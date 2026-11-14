"""Entrenamiento de los modelos con validación cruzada (actividad 3.2, script 17).

Etapas 4 y 5 de la propuesta. Para cada combinación de variable de reingreso, modelo, lista de códigos, con o sin el
hospital y con o sin ponderación, entrena el modelo una vez sin cada pliegue (D52) y guarda la probabilidad que le da a
cada caso el modelo que no lo vio: la predicción fuera de pliegue. No calcula métricas: las calcula el script 18 con
estas predicciones (D63).

  1. Versión. Comprueba que las tablas para los modelos sean la versión registrada (D57).
  2. Matriz de cada vuelta. Las 30 variables predictoras (las categorías como columnas sí/no) y los códigos de la lista
     calculada sin el pliegue que se valida (D53; la lista sin filtro es la misma en todas las vueltas). En la regresión
     logística, logaritmo, estandarización y columnas sí/no divididas por su desviación típica, con estadísticas sacadas
     solo del entrenamiento de la vuelta (D60). Los árboles reciben los valores tal cual.
  3. Modelos. Regresión logística con multa L1, Random Forest y XGBoost con los valores de D62, escritos explícitos en
     reglas/parametros.csv aunque coincidan con los de la biblioteca (H35), la semilla del proyecto y como máximo los
     procesadores de D65. La regresión logística se calcula con liblinear y no con saga, que no llega a la solución con
     las columnas sí/no divididas por su desviación típica (H36).
  4. Verificaciones. Antes de guardar cada combinación (verificar_vuelta y verificar_combinacion). Si alguna falla, la
     combinación no se guarda y el script se detiene.
  5. Salida. Una tabla por combinación en la carpeta de las predicciones (ID_EGRESO, PLIEGUE y PROBABILIDAD), una fila por
     entrenamiento en reportes/17_registro.csv (casos, columnas, segundos, memoria, convergencia y commit del código) y el
     reporte reportes/17_entrenamiento.md.

Se ejecuta por etapas, en el orden de D64: tiempos, ensayo, base, sin_filtro, agrupada, sin_hospital y c. Una combinación
ya guardada no se repite: si la ejecución se corta, el mismo comando sigue con las que faltan. La etapa tiempos entrena
solo la primera vuelta de cada modelo con la lista más pesada, para medir, y no guarda predicciones.

Uso (desde la carpeta Codigo; en el servidor, con el Python del entorno de D65 y dentro de tmux):
    python 3.2_entrenamiento_modelos/scripts/17_entrenar_modelos.py --etapa ensayo
"""

import argparse
import csv
import hashlib
import os
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import scipy
import scipy.sparse as sp
import sklearn
import xgboost
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_DATOS = RAIZ / "data" / "processed"
CASOS = DIR_DATOS / "modelos_casos.parquet"      # una fila por caso de estudio de desarrollo (script 16)
CODIGOS = DIR_DATOS / "modelos_codigos.parquet"  # una fila por caso y código (script 16)
LISTAS = DIR_DATOS / "listas_codigos.parquet"    # los códigos de cada lista, variable y pliegue (script 14)
REGISTRO_TABLAS = RAIZ / "docs" / "version_tablas_modelos.csv"
ARCHIVO_COLUMNAS = RAIZ / "3.1_filtro_dimensionalidad" / "reglas" / "columnas_modelos.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"  # semilla y número de pliegues
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
REGISTRO = ACTIVIDAD / "reportes" / "17_registro.csv"
REPORTE = ACTIVIDAD / "reportes" / "17_entrenamiento.md"

ETAPAS = ["tiempos", "ensayo", "base", "sin_filtro", "agrupada", "sin_hospital", "c"]
MODELOS = {"LR": "regresión logística con multa L1", "RF": "Random Forest", "XGB": "XGBoost"}
CAMPOS_REGISTRO = ["fecha", "etapa", "variable", "modelo", "lista", "hospital", "ponderacion", "pliegue",
                   "casos_entrenamiento", "reingresos_entrenamiento", "casos_validacion", "columnas", "codigos",
                   "peso_reingreso", "segundos", "memoria_gb", "iteraciones", "llego_a_la_solucion", "avisos",
                   "commit", "cambios_sin_confirmar", "version_tablas"]


# ------------------------------------------------------------------ utilidades
def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def separar(valor: str) -> list[str]:
    return [v.strip() for v in valor.split("|") if v.strip()]


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def dec(x, decimales: int = 2) -> str:
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{decimales}f}".replace(".", ",")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(lineas)


def memoria_gb() -> float:
    """Memoria máxima que ha usado el proceso hasta ahora. Solo en Linux (en Windows no hay cómo medirla aquí)."""
    try:
        import resource
    except ImportError:
        return float("nan")
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2  # Linux la entrega en KB


def estado_git() -> tuple[str, str]:
    """El commit del código y si los scripts o las reglas de la actividad tienen cambios sin confirmar."""
    try:
        commit = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "--short", "HEAD"], capture_output=True,
                                text=True, timeout=30).stdout.strip()
        cambios = subprocess.run(["git", "-C", str(RAIZ), "status", "--porcelain", "--",
                                  f"{ACTIVIDAD.name}/scripts", f"{ACTIVIDAD.name}/reglas"], capture_output=True,
                                 text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "sin git", "—"
    return (commit or "sin git"), ("SI" if cambios else "NO")


# ------------------------------------------------------------------ 1. parámetros, columnas y versión
def cargar_parametros() -> dict:
    filas = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS)}
    p23 = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS_23)}

    def leer(nombre: str, tabla: dict = filas, archivo: Path = PARAMETROS) -> str:
        if nombre not in tabla:
            raise SystemExit(f"Falta el parámetro '{nombre}' en {archivo}.")
        return tabla[nombre]

    def num(nombre: str) -> float:
        return float(leer(nombre).replace(",", "."))

    def si_no(nombre: str) -> bool:
        valor = leer(nombre).upper()
        if valor not in ("SI", "NO"):
            raise SystemExit(f"El parámetro '{nombre}' debe ser SI o NO, no '{valor}'.")
        return valor == "SI"

    par = {
        "variables": separar(leer("variables_objetivo")),
        "modelos": separar(leer("modelos")),
        "listas_por_pliegue": separar(leer("listas_por_pliegue")),
        "listas_fijas": separar(leer("listas_fijas")),
        "variable_ensayo": leer("variable_ensayo"),
        "variable_tiempos": leer("variable_tiempos"),
        "lista_tiempos": leer("lista_tiempos"),
        "col_log": separar(leer("columnas_logaritmo")),
        "col_num": separar(leer("columnas_numericas")),
        "col_si_no": separar(leer("columnas_si_no")),
        "col_hospital": leer("columna_hospital"),
        "lr": {"C": num("lr_C"), "l1_ratio": num("lr_l1_ratio"), "solver": leer("lr_solver"),
               "intercept_scaling": num("lr_intercept_scaling"), "max_iter": int(num("lr_max_iter")),
               "tol": num("lr_tol")},
        "rf": {"n_estimators": int(num("rf_n_estimators")), "max_features": leer("rf_max_features"),
               "min_samples_split": int(num("rf_min_samples_split"))},
        "xgb": {"n_estimators": int(num("xgb_n_estimators")), "learning_rate": num("xgb_learning_rate"),
                "max_depth": int(num("xgb_max_depth")), "tree_method": leer("xgb_tree_method"),
                "device": leer("xgb_device")},
        "procesadores": int(num("procesadores")),
        "ponderar": {m: si_no(f"ponderar_{m}") for m in MODELOS},
        "ensayo_resuelto": si_no("ensayo_resuelto"),
        "carpeta_predicciones": RAIZ / leer("carpeta_predicciones"),
        "semilla": int(leer("semilla", p23, PARAMETROS_23)),
        "pliegues": int(leer("pliegues_validacion_cruzada", p23, PARAMETROS_23)),
    }
    if set(par["modelos"]) - set(MODELOS):
        raise SystemExit(f"Modelos desconocidos en {PARAMETROS.name}: {sorted(set(par['modelos']) - set(MODELOS))}.")
    if par["variable_ensayo"] not in par["variables"] or par["variable_tiempos"] not in par["variables"]:
        raise SystemExit("variable_ensayo y variable_tiempos deben estar entre las variables objetivo.")
    if par["lista_tiempos"] not in par["listas_por_pliegue"] + par["listas_fijas"]:
        raise SystemExit("lista_tiempos debe ser una de las listas.")
    return par


def cargar_predictoras(par: dict) -> dict:
    """Las 30 predictoras de reglas/columnas_modelos.csv (D57), separadas según cómo entran a los modelos (D60)."""
    filas = [f for f in leer_csv(ARCHIVO_COLUMNAS) if f["tabla"] == "modelos_casos"]
    predictoras = [f["columna"] for f in filas if f["rol"] == "PREDICTORA"]
    no_predictoras = [f["columna"] for f in filas if f["rol"] != "PREDICTORA"]
    numericas = par["col_log"] + par["col_num"]
    nombradas = numericas + par["col_si_no"] + [par["col_hospital"]]
    if set(nombradas) - set(predictoras):
        raise SystemExit(f"{PARAMETROS.name} nombra columnas que no son predictoras: {sorted(set(nombradas) - set(predictoras))}.")
    if len(set(numericas + par["col_si_no"])) != len(numericas + par["col_si_no"]):
        raise SystemExit(f"{PARAMETROS.name}: hay columnas repetidas entre las numéricas y las sí/no.")
    categorias = [c for c in predictoras if c not in numericas + par["col_si_no"]]
    return {"predictoras": predictoras, "no_predictoras": no_predictoras, "numericas": numericas,
            "si_no": par["col_si_no"], "categorias": categorias}


def comprobar_version() -> dict:
    """Solo se entrena con las tablas para los modelos de la última versión registrada (D57)."""
    if not REGISTRO_TABLAS.exists():
        raise SystemExit(f"No existe {REGISTRO_TABLAS}: falta el registro de versión del script 16.")
    version = leer_csv(REGISTRO_TABLAS)[-1]
    for ruta, campo in [(CASOS, "sha256_casos"), (CODIGOS, "sha256_codigos"), (LISTAS, "sha256_listas_codigos")]:
        if not ruta.exists():
            raise SystemExit(f"No está {ruta}: hay que copiarla desde el portátil (D58).")
        if sha256(ruta) != version[campo]:
            raise SystemExit(f"{ruta.name} no es la de la versión {version['version']} registrada de las tablas: "
                             "vuelva a copiarla o ejecute el script 16.")
    return version


# ------------------------------------------------------------------ 2. datos y matrices
def cargar_datos(par: dict, col: dict) -> dict:
    """Lee las tres tablas una sola vez. Las categorías quedan como números (su posición entre los valores ordenados) y
    cada fila de la tabla de códigos, como la posición de su caso y de su código (BLOQUE, NIVEL y CODIGO juntos)."""
    casos = pd.read_parquet(CASOS, columns=["ID_EGRESO", "ID_PACIENTE", "PLIEGUE"] + col["predictoras"] + par["variables"])
    if casos["ID_EGRESO"].duplicated().any():
        raise SystemExit(f"{CASOS.name} tiene casos repetidos.")
    pliegues_tabla = sorted(casos["PLIEGUE"].unique().tolist())
    if pliegues_tabla != list(range(1, par["pliegues"] + 1)):
        raise SystemExit(f"Los pliegues de {CASOS.name} son {pliegues_tabla}, no 1 a {par['pliegues']} (D52).")
    niveles, cat_codigos = {}, {}
    for c in col["categorias"]:
        if casos[c].isna().any():
            raise SystemExit(f"La categoría {c} tiene datos faltantes: deberían ser SIN DATO (D46).")
        niveles[c] = np.sort(casos[c].astype(str).unique())  # las columnas sí/no salen de los valores, no del reingreso
        cat_codigos[c] = pd.Categorical(casos[c].astype(str), categories=niveles[c]).codes.astype(np.int64)
    for c in col["numericas"] + col["si_no"]:
        if not pd.api.types.is_numeric_dtype(casos[c]):
            raise SystemExit(f"La columna {c} debería ser numérica.")
    for c in col["si_no"]:
        if not set(casos[c].dropna().unique()) <= {0, 1}:
            raise SystemExit(f"La columna {c} debería valer solo 0 o 1.")
    numeros = casos[col["numericas"] + col["si_no"]].to_numpy(dtype=np.float64)

    t = pq.read_table(CODIGOS, columns=["ID_EGRESO", "BLOQUE", "NIVEL", "CODIGO"],
                      read_dictionary=["BLOQUE", "NIVEL", "CODIGO"]).unify_dictionaries().combine_chunks()
    partes, diccionarios = [], []
    for nombre in ["BLOQUE", "NIVEL", "CODIGO"]:
        arr = t[nombre].chunk(0) if t[nombre].num_chunks else pa.array([], pa.dictionary(pa.int32(), pa.string()))
        partes.append(arr.indices.to_numpy(zero_copy_only=False).astype(np.int64))
        diccionarios.append(arr.dictionary.to_pylist())
    nb, nn, nc = (len(d) for d in diccionarios)
    clave = (partes[0] * nn + partes[1]) * nc + partes[2]
    claves, triple = np.unique(clave, return_inverse=True)
    triples = [(diccionarios[0][k // (nn * nc)], diccionarios[1][(k // nc) % nn], diccionarios[2][k % nc]) for k in claves]
    fila = pd.Index(casos["ID_EGRESO"]).get_indexer(t["ID_EGRESO"].to_numpy())
    if (fila < 0).any():
        raise SystemExit(f"{CODIGOS.name} tiene códigos de casos que no están en {CASOS.name}.")

    listas = pd.read_parquet(LISTAS)
    indice = {tr: i for i, tr in enumerate(triples)}
    sin_casos = 0
    posiciones = []
    for tr in zip(listas["BLOQUE"], listas["NIVEL"], listas["CODIGO"]):
        if tr not in indice:  # un código de la lista que ningún caso de la tabla tiene: su columna queda en 0
            indice[tr] = len(triples)
            triples.append(tr)
            sin_casos += 1
        posiciones.append(indice[tr])
    listas["T"] = posiciones
    lista_de = {k: g["T"].to_numpy() for k, g in listas.groupby(["VARIABLE", "LISTA", "PLIEGUE"])}
    return {"casos": casos, "niveles": niveles, "cat_codigos": cat_codigos, "numeros": numeros,
            "fila_codigo": fila, "triple_codigo": triple.astype(np.int64), "triples": triples, "n_triples": len(triples),
            "lista_de": lista_de, "codigos_sin_casos": sin_casos, "pares": len(fila)}


def preparar_variable(datos: dict, variable: str) -> dict:
    """Los casos con dato en la variable (los demás no entran: no son 0) y sus códigos."""
    casos = datos["casos"]
    y = casos[variable].to_numpy(dtype=np.float64)
    idx = np.flatnonzero(~np.isnan(y))
    if not set(np.unique(y[idx])) <= {0.0, 1.0}:
        raise SystemExit(f"{variable} debería valer 0, 1 o no tener dato.")
    posicion = np.full(len(casos), -1, dtype=np.int64)
    posicion[idx] = np.arange(len(idx))
    filas_cod = posicion[datos["fila_codigo"]]
    con_dato = filas_cod >= 0
    return {"variable": variable, "idx": idx, "y": y[idx].astype(np.int8),
            "pliegue": casos["PLIEGUE"].to_numpy()[idx], "paciente": casos["ID_PACIENTE"].to_numpy()[idx],
            "id_egreso": casos["ID_EGRESO"].to_numpy()[idx], "numeros": datos["numeros"][idx],
            "cat": {c: v[idx] for c, v in datos["cat_codigos"].items()},
            "filas_cod": filas_cod[con_dato], "triple_cod": datos["triple_codigo"][con_dato]}


def bloque_categorias(vd: dict, datos: dict, col: dict, hospital: bool, par: dict) -> tuple[sp.csr_matrix, list[str]]:
    """Una columna sí/no por cada valor de cada categoría (D60). Sin hospital, sin sus columnas (D55)."""
    usadas = [c for c in col["categorias"] if hospital or c != par["col_hospital"]]
    n = len(vd["idx"])
    filas, columnas, desplazamiento = [], [], 0
    for c in usadas:
        filas.append(np.arange(n))
        columnas.append(vd["cat"][c] + desplazamiento)
        desplazamiento += len(datos["niveles"][c])
    filas = np.concatenate(filas) if filas else np.array([], dtype=np.int64)
    columnas = np.concatenate(columnas) if columnas else np.array([], dtype=np.int64)
    return sp.csr_matrix((np.ones(len(filas)), (filas, columnas)), shape=(n, desplazamiento)), usadas


def bloque_codigos(vd: dict, datos: dict, lista: str, pliegue: int, par: dict) -> tuple[sp.csr_matrix, int, np.ndarray]:
    """Una columna sí/no por código de la lista de la vuelta: la calculada sin el pliegue que se valida, o la de todo
    desarrollo si la lista no mira el reingreso (D53)."""
    pliegue_lista = pliegue if lista in par["listas_por_pliegue"] else 0
    clave = (vd["variable"], lista, pliegue_lista)
    if clave not in datos["lista_de"]:
        raise SystemExit(f"No hay lista {lista} de {vd['variable']} con PLIEGUE = {pliegue_lista} en {LISTAS.name}.")
    triples = datos["lista_de"][clave]
    columna_de = np.full(datos["n_triples"], -1, dtype=np.int64)
    columna_de[triples] = np.arange(len(triples))
    j = columna_de[vd["triple_cod"]]
    usar = j >= 0
    X = sp.csr_matrix((np.ones(int(usar.sum())), (vd["filas_cod"][usar], j[usar])), shape=(len(vd["idx"]), len(triples)))
    return X, pliegue_lista, triples


def densa_a_csr(X: np.ndarray) -> sp.csr_matrix:
    """Pasa una matriz llena a dispersa guardando también los ceros, para que XGBoost los lea como valor."""
    n, m = X.shape
    return sp.csr_matrix((X.ravel(), np.tile(np.arange(m, dtype=np.int32), n), np.arange(0, n * m + 1, m)), shape=(n, m))


def numeros_de_la_vuelta(numeros: np.ndarray, entren: np.ndarray, n_log: int, n_num: int, para_lr: bool) -> tuple[np.ndarray, dict]:
    """Las 13 numéricas y las 3 sí/no. El dato faltante (un PESO_GRD) recibe la mediana del entrenamiento. En la
    regresión logística: logaritmo, estandarización y división por la desviación típica (D60)."""
    X = numeros.copy()
    mediana = np.nanmedian(X[entren], axis=0)
    faltan = np.isnan(X)
    X[faltan] = mediana[np.nonzero(faltan)[1]]
    est = {"mediana": mediana, "faltantes": int(faltan.sum())}
    if para_lr:
        X[:, :n_log] = np.log1p(X[:, :n_log])
        media = X[entren, :n_num].mean(axis=0)
        desv = X[entren, :n_num].std(axis=0)
        desv[desv == 0] = 1.0
        X[:, :n_num] = (X[:, :n_num] - media) / desv
        p = X[entren, n_num:].mean(axis=0)
        desv_si_no = np.sqrt(p * (1 - p))
        desv_si_no[desv_si_no == 0] = 1.0
        X[:, n_num:] = X[:, n_num:] / desv_si_no
        est.update(media=media, desv=desv, prop_si_no=p)
    return X, est


def escalar_si_no(B: sp.csr_matrix, entren_idx: np.ndarray) -> tuple[sp.csr_matrix, np.ndarray]:
    """Divide cada columna 0/1 por su desviación típica en el entrenamiento, sin restar el promedio (D60)."""
    p = np.asarray(B[entren_idx].mean(axis=0)).ravel()
    desv = np.sqrt(p * (1 - p))
    desv[desv == 0] = 1.0  # una columna sin casos en el entrenamiento queda igual (en 0)
    return (B @ sp.diags(1.0 / desv)).tocsr(), p


# ------------------------------------------------------------------ 3. modelos
def crear_modelo(modelo: str, par: dict, peso: float | None):
    """Los valores de D62, explícitos. peso: lo que pesa cada reingreso si el modelo se pondera (D61)."""
    pesos_clase = {0: 1.0, 1: peso} if peso else None
    if modelo == "LR":
        return LogisticRegression(C=par["lr"]["C"], l1_ratio=par["lr"]["l1_ratio"], solver=par["lr"]["solver"],
                                  intercept_scaling=par["lr"]["intercept_scaling"], max_iter=par["lr"]["max_iter"],
                                  tol=par["lr"]["tol"], random_state=par["semilla"], class_weight=pesos_clase)
    if modelo == "RF":
        return RandomForestClassifier(n_estimators=par["rf"]["n_estimators"], max_features=par["rf"]["max_features"],
                                      min_samples_split=par["rf"]["min_samples_split"], n_jobs=par["procesadores"],
                                      random_state=par["semilla"], class_weight=pesos_clase)
    return xgboost.XGBClassifier(n_estimators=par["xgb"]["n_estimators"], learning_rate=par["xgb"]["learning_rate"],
                                 max_depth=par["xgb"]["max_depth"], tree_method=par["xgb"]["tree_method"],
                                 device=par["xgb"]["device"], n_jobs=par["procesadores"], random_state=par["semilla"],
                                 scale_pos_weight=peso if peso else 1.0, objective="binary:logistic")


def combinaciones(etapa: str, par: dict) -> list[dict]:
    """Las combinaciones de cada etapa de D64."""
    M, V = par["modelos"], par["variables"]

    def comb(variable, modelo, lista, hospital, ponderar):
        return {"variable": variable, "modelo": modelo, "lista": lista, "hospital": hospital, "ponderar": ponderar}

    if etapa == "tiempos":
        return [comb(par["variable_tiempos"], m, par["lista_tiempos"], True, par["ponderar"][m]) for m in M]
    if etapa == "ensayo":
        return [comb(par["variable_ensayo"], m, "A", True, p) for m in M for p in (False, True)]
    if etapa == "base":
        return [comb(v, m, "A", True, par["ponderar"][m]) for v in V if v != par["variable_ensayo"] for m in M]
    lista, hospital = {"sin_filtro": ("SIN_FILTRO", True), "agrupada": ("AGRUPADA", True), "sin_hospital": ("A", False),
                       "c": ("C", True)}[etapa]
    return [comb(v, m, lista, hospital, par["ponderar"][m]) for v in V for m in M]


def nombre_archivo(c: dict) -> str:
    return (f"{c['variable']}__{c['modelo']}__{c['lista']}__{'con' if c['hospital'] else 'sin'}_hospital__"
            f"{'ponderado' if c['ponderar'] else 'sin_ponderar'}.parquet")


# ------------------------------------------------------------------ 4. una combinación y sus verificaciones
def verificar_vuelta(vd: dict, datos: dict, col: dict, par: dict, k: int, lista: str, pliegue_lista: int,
                     triples: np.ndarray, entren_idx: np.ndarray, valid_idx: np.ndarray, X: sp.csr_matrix,
                     cods: sp.csr_matrix, usadas: list[str], est: dict, prop_cat, prop_cod, modelo: str) -> dict[str, bool]:
    """Lo que debe cumplirse en cada vuelta. Las estadísticas se vuelven a calcular por otro camino: desde la tabla de
    casos y desde la tabla de códigos, no desde la matriz."""
    casos = datos["casos"]
    filas_ent = vd["idx"][entren_idx]
    v = {}
    v["lista"] = (pliegue_lista == (k if lista in par["listas_por_pliegue"] else 0)
                  and len(triples) == len(datos["lista_de"][(vd["variable"], lista, pliegue_lista)]))
    v["separados"] = (len(np.intersect1d(entren_idx, valid_idx)) == 0
                      and len(np.intersect1d(vd["paciente"][entren_idx], vd["paciente"][valid_idx])) == 0
                      and bool((vd["pliegue"][valid_idx] == k).all()) and bool((vd["pliegue"][entren_idx] != k).all()))
    n_cat = sum(len(datos["niveles"][c]) for c in usadas)
    v["columnas"] = X.shape[1] == len(col["numericas"]) + len(col["si_no"]) + n_cat + len(triples)
    v["codigos_0_1"] = cods.nnz == 0 or (float(cods.data.min()) == 1.0 and float(cods.data.max()) == 1.0)
    crudos = casos.iloc[filas_ent]
    medianas = crudos[col["numericas"] + col["si_no"]].median().to_numpy()
    v["estadisticas"] = bool(np.allclose(est["mediana"], medianas))
    if modelo == "LR":
        n_log = len(par["col_log"])
        transformadas = np.column_stack([np.log1p(crudos[c].fillna(crudos[c].median())) if i < n_log
                                         else crudos[c].fillna(crudos[c].median())
                                         for i, c in enumerate(col["numericas"])])
        ok = (np.allclose(est["media"], transformadas.mean(axis=0))
              and np.allclose(est["desv"], transformadas.std(axis=0))
              and np.allclose(est["prop_si_no"], crudos[col["si_no"]].mean().to_numpy()))
        partes = []
        for c in usadas:
            conteo = crudos[c].astype(str).value_counts()
            partes.append(conteo.reindex(datos["niveles"][c], fill_value=0).to_numpy() / len(crudos))
        ok = ok and np.allclose(prop_cat, np.concatenate(partes))
        columna_de = np.full(datos["n_triples"], -1, dtype=np.int64)
        columna_de[triples] = np.arange(len(triples))
        en_ent = np.zeros(len(vd["idx"]), dtype=bool)
        en_ent[entren_idx] = True
        j = columna_de[vd["triple_cod"]]
        sel = (j >= 0) & en_ent[vd["filas_cod"]]
        ok = ok and np.allclose(prop_cod, np.bincount(j[sel], minlength=len(triples)) / len(entren_idx))
        v["estadisticas"] = v["estadisticas"] and bool(ok)
    return v


TEXTOS_VUELTA = {
    "lista": "Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)",
    "separados": "Entrenamiento y validación no comparten casos ni pacientes (D52)",
    "columnas": "La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista",
    "codigos_0_1": "Cada código vale 0 o 1 en cada caso",
    "estadisticas": "Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)",
}


def entrenar_combinacion(c: dict, vd: dict, datos: dict, col: dict, par: dict, pliegues: list[int], cache: dict,
                         etapa: str, git: tuple[str, str], version: dict) -> tuple[np.ndarray, list[dict], dict, list[str]]:
    clave_cat = (vd["variable"], c["hospital"])
    if clave_cat not in cache:
        cache[clave_cat] = bloque_categorias(vd, datos, col, c["hospital"], par)
    cats, usadas = cache[clave_cat]
    n = len(vd["idx"])
    prob = np.full(n, np.nan)
    asignadas = np.zeros(n, dtype=np.int64)
    filas, avisos_comb = [], []
    verif = {k: True for k in TEXTOS_VUELTA}
    para_lr = c["modelo"] == "LR"
    for k in pliegues:
        valid = vd["pliegue"] == k
        entren_idx, valid_idx = np.flatnonzero(~valid), np.flatnonzero(valid)
        cods, pliegue_lista, triples = bloque_codigos(vd, datos, c["lista"], k, par)
        numeros, est = numeros_de_la_vuelta(vd["numeros"], ~valid, len(par["col_log"]), len(col["numericas"]), para_lr)
        if para_lr:
            cats_v, prop_cat = escalar_si_no(cats, entren_idx)
            cods_v, prop_cod = escalar_si_no(cods, entren_idx)
        else:
            cats_v, cods_v, prop_cat, prop_cod = cats, cods, None, None
        X = sp.hstack([densa_a_csr(numeros), cats_v, cods_v], format="csr")
        if not para_lr:
            X = X.astype(np.float32)
        y_ent = vd["y"][entren_idx]
        reingresos = int(y_ent.sum())
        peso = (len(y_ent) - reingresos) / reingresos if c["ponderar"] else None
        modelo = crear_modelo(c["modelo"], par, peso)
        inicio = time.perf_counter()
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            modelo.fit(X[entren_idx], y_ent)
            p = modelo.predict_proba(X[valid_idx])[:, 1]
        segundos = time.perf_counter() - inicio
        prob[valid_idx] = p
        asignadas[valid_idx] += 1
        textos = sorted({f"{a.category.__name__}: {str(a.message)[:150]}" for a in avisos})
        avisos_comb += textos
        iteraciones, llego = "—", "—"
        if para_lr:
            iteraciones = int(np.max(modelo.n_iter_))
            llego = "SI" if iteraciones < par["lr"]["max_iter"] and not any(
                issubclass(a.category, ConvergenceWarning) for a in avisos) else "NO"
        v = verificar_vuelta(vd, datos, col, par, k, c["lista"], pliegue_lista, triples, entren_idx, valid_idx, X, cods,
                             usadas, est, prop_cat, prop_cod, c["modelo"])
        verif = {t: verif[t] and v[t] for t in verif}
        filas.append({"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "etapa": etapa, "variable": c["variable"],
                      "modelo": c["modelo"], "lista": c["lista"], "hospital": "CON" if c["hospital"] else "SIN",
                      "ponderacion": "SI" if c["ponderar"] else "NO", "pliegue": k,
                      "casos_entrenamiento": len(entren_idx), "reingresos_entrenamiento": reingresos,
                      "casos_validacion": len(valid_idx), "columnas": X.shape[1], "codigos": len(triples),
                      "peso_reingreso": dec(peso, 3) if peso else "—", "segundos": dec(segundos, 1),
                      "memoria_gb": dec(memoria_gb(), 1), "iteraciones": iteraciones, "llego_a_la_solucion": llego,
                      "avisos": " / ".join(textos) if textos else "—", "commit": git[0],
                      "cambios_sin_confirmar": git[1], "version_tablas": version["version"]})
        print(f"    vuelta {k}: {fmt(len(entren_idx))} casos de entrenamiento, {X.shape[1]} columnas, "
              f"{segundos:.1f} s" + (f", {iteraciones} pasadas" if para_lr else ""), flush=True)
    verif["usadas"] = (set(col["numericas"] + col["si_no"] + usadas)
                       == set(col["predictoras"]) - (set() if c["hospital"] else {par["col_hospital"]})
                       and not set(col["numericas"] + col["si_no"] + usadas) & set(col["no_predictoras"]))
    if etapa != "tiempos":
        verif["una_por_caso"] = bool((asignadas == 1).all()) and not pd.Index(vd["id_egreso"]).duplicated().any()
        verif["probabilidades"] = bool(np.isfinite(prob).all() and (prob >= 0).all() and (prob <= 1).all())
    return prob, filas, verif, avisos_comb


TEXTOS_COMBINACION = {
    "usadas": "Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo",
    "una_por_caso": "Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación",
    "probabilidades": "Las probabilidades están entre 0 y 1, sin valores vacíos",
}


def guardar_predicciones(c: dict, vd: dict, prob: np.ndarray, par: dict, git: tuple[str, str], version: dict) -> Path:
    """Escribe primero un archivo temporal y lo renombra al final: si se corta, no queda una tabla a medias."""
    carpeta = par["carpeta_predicciones"]
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre_archivo(c)
    tabla = pa.table({"ID_EGRESO": vd["id_egreso"], "PLIEGUE": vd["pliegue"].astype(np.int8), "PROBABILIDAD": prob})
    meta = {"variable": c["variable"], "modelo": c["modelo"], "lista": c["lista"],
            "hospital": "CON" if c["hospital"] else "SIN", "ponderacion": "SI" if c["ponderar"] else "NO",
            "semilla": str(par["semilla"]), "commit": git[0], "version_tablas": version["version"],
            "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__}
    tabla = tabla.replace_schema_metadata({k: str(v) for k, v in meta.items()})
    temporal = ruta.with_name(ruta.name + ".tmp")
    pq.write_table(tabla, temporal)
    os.replace(temporal, ruta)
    return ruta


def agregar_registro(filas: list[dict]) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not REGISTRO.exists()
    with open(REGISTRO, "w" if nuevo else "a", encoding="utf-8-sig" if nuevo else "utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_REGISTRO, delimiter=";")
        if nuevo:
            escritor.writeheader()
        escritor.writerows(filas)


# ------------------------------------------------------------------ 5. reporte
def escribir_reporte(par: dict, version: dict, git: tuple[str, str], etapa: str, resultados: list[tuple[str, bool]],
                     datos: dict, duracion: float) -> None:
    registro = pd.read_csv(REGISTRO, sep=";", dtype=str, encoding="utf-8-sig") if REGISTRO.exists() else pd.DataFrame(columns=CAMPOS_REGISTRO)
    num = lambda s: pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
    lineas = ["# Entrenamiento de los modelos con validación cruzada (script 17)", "",
              f"Última ejecución: etapa `{etapa}`, el {datetime.now().strftime('%Y-%m-%d %H:%M')}, en {duracion / 60:.1f} minutos. "
              f"Commit del código: `{git[0]}` (cambios sin confirmar en los scripts o las reglas: {git[1]}). "
              f"Tablas para los modelos: versión {version['version']} del {version['fecha']}. "
              f"Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}, scipy {scipy.__version__}, "
              f"scikit-learn {sklearn.__version__}, XGBoost {xgboost.__version__}. Semilla {par['semilla']}; "
              f"hasta {par['procesadores']} procesadores.", "",
              "## 1. Verificaciones de esta ejecución", ""]
    lineas += [f"- {'✓' if ok else '✗ FALLÓ:'} {texto}" for texto, ok in resultados] or ["- (ninguna combinación nueva)"]
    lineas += ["", f"Códigos de las listas que ningún caso de la tabla tiene (su columna queda en 0): {datos['codigos_sin_casos']}. "
               "Con las tablas completas debe ser 0, porque toda lista exige al menos 100 casos (D45).", ""]
    tiempos = registro[registro["etapa"] == "tiempos"]
    lineas += ["## 2. Prueba de tiempos", ""]
    if len(tiempos):
        ultima = tiempos.groupby("modelo").tail(1)
        filas, total = [], 0.0
        for _, f in ultima.iterrows():
            seg = float(num(pd.Series([f["segundos"]])).iloc[0])
            estimado = seg * par["pliegues"] * 21  # cada modelo tiene 21 combinaciones (63 / 3), de cinco vueltas
            total += estimado
            filas.append([f["modelo"], f"{f['variable']} con la lista {f['lista']}", fmt(int(f["casos_entrenamiento"])),
                          f["columnas"], dec(seg / 60, 1), f["memoria_gb"], dec(estimado / 3600, 1)])
        lineas += [tabla_md(["Modelo", "Entrenamiento medido", "Casos", "Columnas", "Minutos de una vuelta",
                             "Memoria máxima (GB)", "Horas como máximo para sus 105 entrenamientos"], filas), "",
                   f"Como máximo, unas {dec(total / 3600, 1)} horas en total, una combinación tras otra. Es una cota para "
                   "los entrenamientos sin ponderar, porque se midió con la lista más pesada; si un modelo se pondera "
                   "(D61), puede tardar varias veces más.", ""]
    else:
        lineas += ["Todavía no se ejecuta.", ""]
    lineas += ["## 3. Combinaciones guardadas", ""]
    carpeta = par["carpeta_predicciones"]
    archivos = sorted(carpeta.glob("*.parquet")) if carpeta.exists() else []
    reales = registro[registro["etapa"] != "tiempos"]
    filas = []
    for a in archivos:
        partes = a.stem.split("__")
        r = reales[(reales["variable"] == partes[0]) & (reales["modelo"] == partes[1]) & (reales["lista"] == partes[2])
                   & (reales["hospital"] == ("CON" if partes[3] == "con_hospital" else "SIN"))
                   & (reales["ponderacion"] == ("SI" if partes[4] == "ponderado" else "NO"))].tail(par["pliegues"])
        llego = "—" if partes[1] != "LR" or not len(r) else ("SI" if (r["llego_a_la_solucion"] == "SI").all() else "NO")
        filas.append([partes[0], partes[1], partes[2], partes[3].replace("_", " "), partes[4].replace("_", " "),
                      fmt(pq.ParquetFile(a).metadata.num_rows), dec(num(r["segundos"]).sum() / 60, 1) if len(r) else "—", llego])
    lineas += [tabla_md(["Variable", "Modelo", "Lista", "Hospital", "Ponderación", "Casos", "Minutos", "Llegó a la solución"], filas)
               if filas else "Todavía ninguna.", "", f"Combinaciones guardadas: {len(archivos)} de 63 (D64).", ""]
    lineas += ["## 4. Valores completos de cada modelo", "",
               "Los de D62 están escritos explícitos en `reglas/parametros.csv`; el resto son los de la biblioteca.", ""]
    for m in par["modelos"]:
        valores = {k: v for k, v in crear_modelo(m, par, None).get_params().items() if v is not None}
        lineas += [f"- **{MODELOS[m]}:** " + ", ".join(f"`{k}` = {v}" for k, v in sorted(valores.items()))]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ principal
def leer_argumentos(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Entrena los modelos de la actividad 3.2 con validación cruzada (D58 a D65).")
    p.add_argument("--etapa", required=True, choices=ETAPAS, help="Etapa de D64 que se ejecuta")
    p.add_argument("--modelos", help="Solo estos modelos, separados por coma (por ejemplo, LR,XGB)")
    p.add_argument("--variables", help="Solo estas variables, separadas por coma")
    return p.parse_args(argv)


def main(argv=None) -> None:
    args = leer_argumentos(argv)
    inicio = time.time()
    par = cargar_parametros()
    if args.etapa not in ("tiempos", "ensayo") and not par["ensayo_resuelto"]:
        raise SystemExit("Primero va el ensayo de la ponderación (D61): ejecute la etapa ensayo, evalúela con el script 18 "
                         f"y fije ponderar_LR, ponderar_RF, ponderar_XGB y ensayo_resuelto en {PARAMETROS.name}.")
    col = cargar_predictoras(par)
    combos = combinaciones(args.etapa, par)
    if args.modelos:
        combos = [c for c in combos if c["modelo"] in args.modelos.split(",")]
    if args.variables:
        combos = [c for c in combos if c["variable"] in args.variables.split(",")]
    print(f"Etapa {args.etapa}: {len(combos)} combinaciones. Comprobando la versión de las tablas...", flush=True)
    version = comprobar_version()
    git = estado_git()
    datos = cargar_datos(par, col)
    print(f"Tablas leídas: {fmt(len(datos['casos']))} casos y {fmt(datos['pares'])} pares caso–código "
          f"({time.time() - inicio:.0f} s).", flush=True)
    pliegues = [1] if args.etapa == "tiempos" else list(range(1, par["pliegues"] + 1))
    variables, cache, resultados = {}, {}, []
    for i, c in enumerate(combos, 1):
        ruta = par["carpeta_predicciones"] / nombre_archivo(c)
        if args.etapa != "tiempos" and ruta.exists():
            print(f"[{i}/{len(combos)}] {ruta.name}: ya está guardada, se omite.", flush=True)
            continue
        print(f"[{i}/{len(combos)}] {nombre_archivo(c).removesuffix('.parquet')}", flush=True)
        if c["variable"] not in variables:
            variables = {c["variable"]: preparar_variable(datos, c["variable"])}  # una variable a la vez en memoria
            cache = {}
        vd = variables[c["variable"]]
        prob, filas, verif, _ = entrenar_combinacion(c, vd, datos, col, par, pliegues, cache, args.etapa, git, version)
        nombre = nombre_archivo(c).removesuffix(".parquet")
        textos = {**TEXTOS_VUELTA, **TEXTOS_COMBINACION}
        resultados += [(f"{nombre}: {textos[k]}", ok) for k, ok in verif.items()]
        if not all(verif.values()):
            escribir_reporte(par, version, git, args.etapa, resultados, datos, time.time() - inicio)
            raise SystemExit(f"Falló una verificación en {nombre}: no se guardó. Revise {REPORTE}.")
        if args.etapa != "tiempos":
            guardar_predicciones(c, vd, prob, par, git, version)
        agregar_registro(filas)
    escribir_reporte(par, version, git, args.etapa, resultados, datos, time.time() - inicio)
    print(f"Listo en {(time.time() - inicio) / 60:.1f} minutos. Reporte: {REPORTE}", flush=True)


if __name__ == "__main__":
    main()
