"""Filtro de dimensionalidad (actividad 3.1, script 14).

Etapa 3 de la propuesta. Los diagnósticos (CIE-10) y los procedimientos (CIE-9-MC) de cada caso de estudio
se usan como indicadores sí/no y suman miles de códigos, así que se filtran según su asociación con cada
variable de reingreso. Sobre millones de casos casi cualquier código sale significativo, por lo que el
umbral no se pone en el valor p sino en el tamaño de efecto, la V de Cramér (bitácora D45).

  1. Parámetros. Los umbrales están en reglas/parametros.csv.
  2. Versión. Comprueba que el conjunto de desarrollo sea el de la última versión registrada de la
     partición (docs/version_particion.csv). No abre el conjunto de prueba.
  3. Códigos. Arma una tabla con una fila por caso de estudio y código. Un código cuenta una vez por
     caso, esté en la posición que esté.
  4. Asociación. Para cada variable de reingreso, con los casos que tienen dato en ella, arma la tabla
     de 2×2 de cada código (tiene o no el código × reingresa o no) y calcula el chi-cuadrado, su valor
     p y la V de Cramér.
  5. Filtro. Pasan los códigos con V mayor o igual a v_minima que tengan al menos casos_minimos casos
     (lista A, la principal). Además cuenta cuántos pasarían con los otros umbrales de la sensibilidad.
  6. Listas para comparar en la actividad 3.2 (D53, observación O7 del profesor guía): la lista C (los de
     la A más los de efecto grande: riesgo al menos efecto_grande_riesgo veces mayor o menor, con valor p
     menor que efecto_grande_p), la lista agrupada (la regla de la A con los diagnósticos en su categoría
     de tres caracteres y los procedimientos completos) y la lista sin filtro (todos los códigos con al
     menos casos_minimos casos).
  7. Listas por pliegue (D53, observación O5): las listas que miran el reingreso (A, C y agrupada) se
     calculan además con el entrenamiento de cada pliegue de la validación cruzada, sin los casos de ese
     pliegue (data/processed/validacion_temporal.parquet, script 13).
  8. Salida. data/processed/filtro_codigos.parquet tiene todos los códigos, pasen o no;
     data/processed/listas_codigos.parquet, los códigos de cada lista, de todo desarrollo y de cada pliegue;
     la lista fija A queda en reportes/14_codigos_retenidos.csv, y el resumen, en reportes/14_filtro_codigos.md.

La lista calculada con todo el conjunto de desarrollo queda fija para el modelo final: se aplica sin
recalcularla al conjunto de prueba en la evaluación final (propuesta, Etapa 3). Dentro de la validación
cruzada de la actividad 3.2, cada pliegue usa la lista de su entrenamiento (D53).

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\scripts\\14_filtro_codigos.py
"""

import csv
import hashlib
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
DESTINO = RAIZ / "data" / "processed" / "filtro_codigos.parquet"
LISTAS = RAIZ / "data" / "processed" / "listas_codigos.parquet"
GRUPOS = RAIZ / "data" / "processed" / "validacion_temporal.parquet"   # pliegue de cada caso de estudio (script 13)
REGISTRO = RAIZ / "docs" / "version_particion.csv"
DIR_TABLAS = RAIZ.parent / "Datos" / "Tablas auxiliares"  # tablas del DEIS con la descripción de cada código
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
DIR_REPORTS = ACTIVIDAD / "reportes"
LISTA = DIR_REPORTS / "14_codigos_retenidos.csv"
REPORTE = DIR_REPORTS / "14_filtro_codigos.md"
PARAMETROS = ["variables_objetivo", "nivel_codigo", "v_minima", "casos_minimos", "v_sensibilidad", "casos_sensibilidad",
              "listas_comparacion", "efecto_grande_riesgo", "efecto_grande_p"]
LISTAS_POSIBLES = {
    "A": "la principal: V ≥ v_minima y al menos casos_minimos casos (D45)",
    "C": "los de la A más los de efecto grande: riesgo al menos efecto_grande_riesgo veces mayor o menor que sin el código, "
         "con valor p menor que efecto_grande_p, y al menos casos_minimos casos (H30)",
    "AGRUPADA": "la regla de la A con los diagnósticos en su categoría de tres caracteres (R57.0 → R57) y los procedimientos completos",
    "SIN_FILTRO": "todos los códigos completos con al menos casos_minimos casos, sin mirar el reingreso",
}
LISTAS_POR_PLIEGUE = ["A", "C", "AGRUPADA"]       # las que miran el reingreso
EJEMPLO_AGRUPADA = ("R57.0", "choque cardiogénico")   # el ejemplo de la revisión del profesor guía (O7)
BLOQUES = {  # bloque: columnas del conjunto de desarrollo y tabla del DEIS con sus descripciones
    "DIAGNOSTICO": ([f"DIAGNOSTICO{i}" for i in range(1, 36)], "CIE-10.xlsx"),
    "PROCEDIMIENTO": ([f"PROCEDIMIENTO{i}" for i in range(1, 31)], "CIE-9.xlsx"),
}
NOMBRE_BLOQUE = {"DIAGNOSTICO": "Diagnósticos (CIE-10)", "PROCEDIMIENTO": "Procedimientos (CIE-9-MC)"}
NIVELES = {"COMPLETO": "el código tal como viene (por ejemplo, E11.9)",
           "CATEGORIA": "solo la categoría del código, lo que va antes del punto (E11 en los diagnósticos y 99 en los procedimientos)"}
COLUMNAS_LISTA = ["VARIABLE", "BLOQUE", "CODIGO", "DESCRIPCION", "CASOS", "REINGRESOS", "TASA_CON_CODIGO",
                  "TASA_SIN_CODIGO", "V", "DIRECCION"]


# ------------------------------------------------------------------ 1. parámetros y 2. versión
def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cargar_parametros() -> dict:
    filas = {fila["parametro"]: fila for fila in leer_csv(ARCHIVO_PARAMETROS)}
    faltan = sorted(set(PARAMETROS) - set(filas))
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")
    for nombre, fila in filas.items():
        if None in fila:  # una columna de más: hay un «;» dentro de un texto y cortaría la descripción
            raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: la fila de '{nombre}' tiene un «;» de más.")
    valor = {nombre: filas[nombre]["valor"].strip() for nombre in PARAMETROS}

    def numeros(nombre: str, tipo) -> list:
        # "0,005|0,01|0,02" se convierte en [0.005, 0.01, 0.02]: en Python el decimal se escribe con punto
        return [tipo(v.strip().replace(",", ".")) for v in valor[nombre].split("|") if v.strip()]

    par = {"objetivos": [v.strip() for v in valor["variables_objetivo"].split("|") if v.strip()],
           "nivel": valor["nivel_codigo"].upper(),
           "v_minima": numeros("v_minima", float)[0], "casos_minimos": numeros("casos_minimos", int)[0],
           "v_sensibilidad": numeros("v_sensibilidad", float), "casos_sensibilidad": numeros("casos_sensibilidad", int),
           "listas": ["A", *[v.strip().upper() for v in valor["listas_comparacion"].split("|") if v.strip()]],
           "riesgo": numeros("efecto_grande_riesgo", float)[0], "p_maximo": numeros("efecto_grande_p", float)[0]}
    if par["nivel"] not in NIVELES:
        raise SystemExit(f"nivel_codigo: se esperaba {' o '.join(NIVELES)} y dice '{valor['nivel_codigo']}'.")
    if set(par["listas"]) - set(LISTAS_POSIBLES) or len(set(par["listas"])) != len(par["listas"]):
        raise SystemExit(f"listas_comparacion: se esperaban valores distintos entre {', '.join(list(LISTAS_POSIBLES)[1:])}.")
    if par["riesgo"] <= 1 or not 0 < par["p_maximo"] < 1:
        raise SystemExit("efecto_grande_riesgo debe ser mayor que 1 y efecto_grande_p, un valor entre 0 y 1.")
    if par["v_minima"] not in par["v_sensibilidad"] or par["casos_minimos"] not in par["casos_sensibilidad"]:
        raise SystemExit("Los umbrales principales deben estar también entre los de la sensibilidad.")
    par["descripcion"] = {nombre: (valor[nombre], filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    return par


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def comprobar_version() -> dict:
    """Solo se trabaja sobre el conjunto de desarrollo de la última versión registrada de la partición (D29)."""
    if not REGISTRO.exists():
        raise SystemExit(f"No existe {REGISTRO.name}: ejecute antes el script 10.")
    version = leer_csv(REGISTRO)[-1]
    if sha256(DESARROLLO) != version["sha256_desarrollo"]:
        raise SystemExit(f"{DESARROLLO.name} no es el de la versión {version['version']} de la partición: ejecute el script 10.")
    return version


# ------------------------------------------------------------------ 3. códigos de cada caso de estudio
def leer_casos(par: dict) -> pd.DataFrame:
    """Los casos de estudio de desarrollo, con su año, las variables de reingreso y las columnas de códigos."""
    columnas_codigos = [c for columnas, _ in BLOQUES.values() for c in columnas]
    casos = pd.read_parquet(DESARROLLO, columns=["ID_EGRESO", "ANIO_ARCHIVO", *par["objetivos"], *columnas_codigos],
                            filters=[("ES_CASO_ESTUDIO", "==", True)])
    casos = casos.reset_index(drop=True)  # las filas quedan numeradas 0, 1, 2, ...
    # Pliegue de la validación cruzada de cada caso (script 13, D52): todos los casos de un paciente en el mismo.
    if not GRUPOS.exists():
        raise SystemExit(f"No existe {GRUPOS.name}: ejecute antes el script 13.")
    grupos = pd.read_parquet(GRUPOS, columns=["ID_EGRESO", "PLIEGUE"]).set_index("ID_EGRESO")["PLIEGUE"]
    casos["PLIEGUE"] = grupos.reindex(casos["ID_EGRESO"]).to_numpy()
    if casos["PLIEGUE"].isna().any() or len(grupos) != len(casos):
        raise SystemExit(f"{GRUPOS.name} no tiene un pliegue para cada caso de estudio de desarrollo: ejecute el script 13.")
    casos["PLIEGUE"] = casos["PLIEGUE"].astype("int64")
    return casos


def tabla_larga(casos: pd.DataFrame, columnas: list[str], nivel: str) -> pd.DataFrame:
    """Una fila por caso de estudio y código (FILA es la fila del caso en la tabla de casos).
    Un código que aparece en dos posiciones del mismo caso queda una sola vez."""
    partes = []
    for columna in columnas:
        codigos = casos[columna].dropna()  # solo los casos que tienen un código en esta posición
        partes.append(pd.DataFrame({"FILA": codigos.index, "CODIGO": codigos}))
    largo = pd.concat(partes, ignore_index=True)
    if nivel == "CATEGORIA":
        largo["CODIGO"] = largo["CODIGO"].str.split(".").str[0]
    largo["CODIGO"] = largo["CODIGO"].astype("category")  # cada código distinto se guarda una sola vez: ahorra memoria
    return largo.drop_duplicates(ignore_index=True)


# ------------------------------------------------------------------ 4. asociación con una variable de reingreso
def asociacion(largo: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
    """Tabla de 2×2 de cada código con una variable de reingreso, y sus medidas de asociación.

    y tiene una posición por caso de estudio: 1 si reingresa, 0 si no y NaN si no tiene dato (por ejemplo,
    un caso sin los 60 días de seguimiento en las variables de 30 días). Los casos sin dato no se cuentan."""
    N = int((~np.isnan(y)).sum())  # casos con dato en la variable
    R = int((y == 1).sum())        # de ellos, los que reingresan
    y_par = y[largo["FILA"].to_numpy()]  # el valor de la variable en el caso de cada par caso-código
    con_dato = ~np.isnan(y_par)
    pares = pd.DataFrame({"CODIGO": largo["CODIGO"][con_dato], "REINGRESA": y_par[con_dato] == 1})
    cuenta = pares.groupby("CODIGO", observed=False)["REINGRESA"].agg(["size", "sum"])

    # Las cuatro celdas de la tabla de 2×2 de cada código
    a = cuenta["sum"].to_numpy(dtype=float)       # tiene el código y reingresa
    b = cuenta["size"].to_numpy(dtype=float) - a  # tiene el código y no reingresa
    c = R - a                                     # no tiene el código y reingresa
    d = (N - R) - b                               # no tiene el código y no reingresa
    con, sin = a + b, c + d                       # casos con el código y sin él

    # Chi-cuadrado de Pearson: suma, en las cuatro celdas, de (observado - esperado)² / esperado. El esperado
    # es lo que habría si el código no tuviera relación con el reingreso: la misma tasa con el código y sin él.
    chi2 = np.zeros(len(cuenta))
    for observado, total_fila, total_columna in [(a, con, R), (b, con, N - R), (c, sin, R), (d, sin, N - R)]:
        esperado = total_fila * total_columna / N
        chi2 += np.divide((observado - esperado) ** 2, esperado, out=np.zeros(len(cuenta)), where=esperado > 0)

    with np.errstate(invalid="ignore", divide="ignore"):
        tasa_con = np.where(con > 0, 100 * a / con, np.nan)
        tasa_sin = np.where(sin > 0, 100 * c / sin, np.nan)
    return pd.DataFrame({
        "CODIGO": cuenta.index.astype(str),
        "CASOS": con.astype(np.int64),
        "REINGRESOS": a.astype(np.int64),
        "TASA_CON_CODIGO": tasa_con,
        "TASA_SIN_CODIGO": tasa_sin,
        "CHI2": chi2,
        "VALOR_P": [math.erfc(math.sqrt(x / 2)) for x in chi2],  # valor p del chi-cuadrado con 1 grado de libertad
        "V": np.sqrt(chi2 / N),                                  # V de Cramér: en una tabla de 2×2 es raíz(chi² / N)
        "DIRECCION": np.select([con == 0, tasa_con > tasa_sin, tasa_con < tasa_sin], ["sin casos", "sube", "baja"],
                               default="igual"),
    })


# ------------------------------------------------------------------ listas por pliegue
def conteo_pliegues(largo: pd.DataFrame, y: np.ndarray, pliegue: np.ndarray, n_pliegues: int) -> tuple[np.ndarray, np.ndarray]:
    """Casos con el código y, de ellos, los que reingresan, por código (filas, en el orden de las categorías del código) y
    pliegue (columnas). Solo cuentan los casos con dato en la variable."""
    codigo = largo["CODIGO"].cat.codes.to_numpy().astype(np.int64)
    filas = largo["FILA"].to_numpy()
    y_par = y[filas]
    con_dato = ~np.isnan(y_par)
    clave = codigo[con_dato] * n_pliegues + (pliegue[filas][con_dato] - 1)
    n_codigos = len(largo["CODIGO"].cat.categories)
    casos = np.bincount(clave, minlength=n_codigos * n_pliegues).reshape(n_codigos, n_pliegues)
    reingresos = np.bincount(clave, weights=(y_par[con_dato] == 1).astype(float),
                             minlength=n_codigos * n_pliegues).reshape(n_codigos, n_pliegues).astype(np.int64)
    return casos, reingresos


def reglas_lista(a: np.ndarray, n: np.ndarray, R: int, N: int, par: dict) -> dict[str, np.ndarray]:
    """Qué códigos pasan las reglas de las listas A y C con a reingresos entre n casos con el código, de N casos con dato
    y R reingresos (todo desarrollo o el entrenamiento de un pliegue). Usa la fórmula abreviada del chi-cuadrado."""
    a, n = a.astype(float), n.astype(float)
    b, c = n - a, R - a
    d = (N - R) - b
    den = n * (N - n) * R * (N - R)
    chi2 = np.divide(N * (a * d - b * c) ** 2, den, out=np.zeros(len(n)), where=den > 0)
    v = np.sqrt(chi2 / N)
    with np.errstate(divide="ignore", invalid="ignore"):
        rr = np.where((n > 0) & (c > 0), (a / np.where(n > 0, n, 1)) / (c / (N - n)), np.nan)
    p = np.array([math.erfc(math.sqrt(x / 2)) for x in chi2])
    suficiente = n >= par["casos_minimos"]
    lista_a = suficiente & (v >= par["v_minima"])
    grande = ((rr >= par["riesgo"]) | (rr <= 1 / par["riesgo"])) & (p < par["p_maximo"])
    return {"A": lista_a, "C": suficiente & (lista_a | grande), "RR": rr}


# ------------------------------------------------------------------ 5. filtro y sensibilidad
def filtrar(par: dict, casos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Calcula la asociación de todos los códigos con cada variable de reingreso, marca los que pasan y arma las listas
    de todo desarrollo (PLIEGUE 0) y del entrenamiento de cada pliegue (PLIEGUE 1 a N)."""
    y = {k: casos[k].to_numpy(dtype="float64", na_value=np.nan) for k in par["objetivos"]}
    anio = casos["ANIO_ARCHIVO"].to_numpy()
    pliegue = casos["PLIEGUE"].to_numpy()
    pliegues = sorted(int(f) for f in np.unique(pliegue))
    n_pl = max(pliegues)
    info = {"casos": len(casos), "casos_anio": casos["ANIO_ARCHIVO"].value_counts().sort_index(),
            "totales": {k: (int((~np.isnan(v)).sum()), int((v == 1).sum())) for k, v in y.items()},
            "totales_pliegue": {k: {f: (int((~np.isnan(v[pliegue == f])).sum()), int((v[pliegue == f] == 1).sum())) for f in pliegues}
                                for k, v in y.items()},
            "pliegues": pliegues, "bloques": {}, "pares_con_dato": {}, "frecuencia_anual": {}, "conteos_cuadran": True}
    # El nivel principal de los códigos para todas las listas y, para la lista agrupada, los diagnósticos en su categoría.
    combinaciones = [(b, par["nivel"]) for b in BLOQUES]
    if "AGRUPADA" in par["listas"]:
        if par["nivel"] != "COMPLETO":
            raise SystemExit("La lista agrupada ya agrupa los diagnósticos: use nivel_codigo = COMPLETO.")
        combinaciones.append(("DIAGNOSTICO", "CATEGORIA"))
    resultados, listas = [], []
    for bloque, nivel in combinaciones:
        principal = nivel == par["nivel"]
        largo = tabla_larga(casos, BLOQUES[bloque][0], nivel)
        if principal:
            info["bloques"][bloque] = {"codigos": int(largo["CODIGO"].nunique()), "pares": len(largo)}
            # casos de cada año del alta que tienen cada código (para ver si un código cambia con los años)
            info["frecuencia_anual"][bloque] = (pd.DataFrame({"CODIGO": largo["CODIGO"], "ANIO": anio[largo["FILA"].to_numpy()]})
                                                .groupby(["CODIGO", "ANIO"], observed=True).size())
        else:
            info["categorias"] = {"codigos": int(largo["CODIGO"].nunique()), "pares": len(largo)}
        categorias = np.asarray(largo["CODIGO"].cat.categories.astype(str))
        for k in par["objetivos"]:
            tabla = asociacion(largo, y[k])
            N, R = info["totales"][k]
            casos_pl, reingresos_pl = conteo_pliegues(largo, y[k], pliegue, n_pl)
            info["conteos_cuadran"] &= bool((casos_pl.sum(axis=1) == tabla["CASOS"].to_numpy()).all()
                                            and (reingresos_pl.sum(axis=1) == tabla["REINGRESOS"].to_numpy()).all())
            reglas = reglas_lista(reingresos_pl.sum(axis=1), casos_pl.sum(axis=1), R, N, par)
            tabla.insert(0, "NIVEL", nivel)
            tabla.insert(0, "BLOQUE", bloque)
            tabla.insert(0, "VARIABLE", k)
            tabla["RIESGO_RELATIVO"] = reglas["RR"]
            tabla["PASA_C"] = reglas["C"]
            resultados.append(tabla)
            if principal:
                info["pares_con_dato"][(bloque, k)] = int((~np.isnan(y[k][largo["FILA"].to_numpy()])).sum())
            # Listas de cada pliegue: las mismas reglas con el entrenamiento, es decir, sin los casos del pliegue.
            for f in pliegues:
                Nf, Rf = info["totales_pliegue"][k][f]
                r = reglas_lista(reingresos_pl.sum(axis=1) - reingresos_pl[:, f - 1], casos_pl.sum(axis=1) - casos_pl[:, f - 1],
                                 R - Rf, N - Nf, par)
                for lista in LISTAS_POR_PLIEGUE:
                    if lista not in par["listas"]:
                        continue
                    if lista == "AGRUPADA":   # diagnósticos por categoría y procedimientos completos, con la regla de la A
                        usar, regla = (bloque == "DIAGNOSTICO") != principal, "A"
                    else:
                        usar, regla = principal, lista
                    if usar:
                        listas.append(pd.DataFrame({"VARIABLE": k, "LISTA": lista, "PLIEGUE": f, "BLOQUE": bloque, "NIVEL": nivel,
                                                    "CODIGO": categorias[r[regla]]}))
        del largo

    todo = pd.concat(resultados, ignore_index=True)
    todo["PASA"] = (todo["CASOS"] >= par["casos_minimos"]) & (todo["V"] >= par["v_minima"])
    todo = todo[["VARIABLE", "BLOQUE", "NIVEL", "CODIGO", "CASOS", "REINGRESOS", "TASA_CON_CODIGO", "TASA_SIN_CODIGO", "CHI2",
                 "VALOR_P", "V", "DIRECCION", "RIESGO_RELATIVO", "PASA", "PASA_C"]]
    todo["VARIABLE"] = pd.Categorical(todo["VARIABLE"], categories=par["objetivos"], ordered=True)
    todo["NIVEL"] = pd.Categorical(todo["NIVEL"], categories=list(dict.fromkeys([par["nivel"], "CATEGORIA"])), ordered=True)
    todo = todo.sort_values(["VARIABLE", "NIVEL", "BLOQUE", "V"], ascending=[True, True, True, False], ignore_index=True)
    todo["VARIABLE"], todo["NIVEL"] = todo["VARIABLE"].astype(str), todo["NIVEL"].astype(str)

    # Listas de todo desarrollo (PLIEGUE 0)
    es_principal = todo["NIVEL"] == par["nivel"]
    seleccion = {"A": es_principal & todo["PASA"], "C": es_principal & todo["PASA_C"],
                 "AGRUPADA": (((todo["NIVEL"] == "CATEGORIA") & (todo["BLOQUE"] == "DIAGNOSTICO"))
                              | (es_principal & (todo["BLOQUE"] == "PROCEDIMIENTO"))) & todo["PASA"],
                 "SIN_FILTRO": es_principal & (todo["CASOS"] >= par["casos_minimos"])}
    for lista in par["listas"]:
        listas.append(todo.loc[seleccion[lista], ["VARIABLE", "BLOQUE", "NIVEL", "CODIGO"]].assign(LISTA=lista, PLIEGUE=0))
    listas = pd.concat(listas, ignore_index=True)[["VARIABLE", "LISTA", "PLIEGUE", "BLOQUE", "NIVEL", "CODIGO"]]
    listas["LISTA"] = pd.Categorical(listas["LISTA"], categories=par["listas"], ordered=True)
    listas["VARIABLE"] = pd.Categorical(listas["VARIABLE"], categories=par["objetivos"], ordered=True)
    listas = listas.sort_values(["VARIABLE", "LISTA", "PLIEGUE", "BLOQUE", "NIVEL", "CODIGO"], ignore_index=True)
    listas["LISTA"], listas["VARIABLE"] = listas["LISTA"].astype(str), listas["VARIABLE"].astype(str)
    listas["PLIEGUE"] = listas["PLIEGUE"].astype("int8")

    # Sensibilidad: cuántos códigos pasarían con cada combinación de umbrales (solo se cuentan, en el nivel principal)
    info["sensibilidad"] = {}
    for v in par["v_sensibilidad"]:
        for n in par["casos_sensibilidad"]:
            pasaria = es_principal & (todo["CASOS"] >= n) & (todo["V"] >= v)
            info["sensibilidad"][(v, n)] = {
                k: {b: int((pasaria & (todo["VARIABLE"] == k) & (todo["BLOQUE"] == b)).sum()) for b in BLOQUES}
                for k in par["objetivos"]}
    return todo, listas, info


def agregar_descripciones(todo: pd.DataFrame) -> None:
    """Agrega la descripción de cada código según las tablas del DEIS (CIE-10 y CIE-9)."""
    descripcion = pd.Series("", index=todo.index)
    for bloque, (_, archivo) in BLOQUES.items():
        tabla = pd.read_excel(DIR_TABLAS / archivo, dtype=str)
        texto = dict(zip(tabla["Código"].str.strip(), tabla["Descripción"].str.split().str.join(" ")))
        filas = todo["BLOQUE"] == bloque
        descripcion[filas] = todo.loc[filas, "CODIGO"].map(texto).fillna("")
    todo.insert(todo.columns.get_loc("CODIGO") + 1, "DESCRIPCION", descripcion)


# ------------------------------------------------------------------ verificaciones y 6. salida
def verificar(todo: pd.DataFrame, listas: pd.DataFrame, info: dict, par: dict, version: dict) -> list[tuple[str, bool]]:
    principal = todo[todo["NIVEL"] == par["nivel"]]
    pasan = principal[principal["PASA"]]
    abreviada_igual, celdas_ok, filas_ok, suma_ok = True, True, True, True
    for k, (N, R) in info["totales"].items():
        for bloque in BLOQUES:
            t = principal[(principal["VARIABLE"] == k) & (principal["BLOQUE"] == bloque)]
            a = t["REINGRESOS"].to_numpy(dtype=float)
            b = t["CASOS"].to_numpy(dtype=float) - a
            c, d = R - a, (N - R) - b
            celdas_ok &= bool((a >= 0).all() and (b >= 0).all() and (c >= 0).all() and (d >= 0).all())
            # El chi-cuadrado de una tabla de 2×2 también es N·(ad − bc)² / (con · sin · R · (N − R))
            den = (a + b) * (c + d) * R * (N - R)
            abreviada = np.divide(N * (a * d - b * c) ** 2, den, out=np.zeros(len(t)), where=den > 0)
            abreviada_igual &= bool(np.allclose(abreviada, t["CHI2"].to_numpy(), rtol=1e-9, atol=1e-9))
            filas_ok &= len(t) == info["bloques"][bloque]["codigos"] and t["CODIGO"].is_unique
            suma_ok &= int(t["CASOS"].sum()) == info["pares_con_dato"][(bloque, k)]
    sensibilidad = info["sensibilidad"][(par["v_minima"], par["casos_minimos"])]
    # Las listas: todo código de una lista tiene el mínimo de casos en todo desarrollo; la A está dentro de la C; cada lista
    # que mira el reingreso tiene una versión por pliegue.
    con_fila = listas.merge(todo[["VARIABLE", "BLOQUE", "NIVEL", "CODIGO", "CASOS"]], on=["VARIABLE", "BLOQUE", "NIVEL", "CODIGO"], how="left")
    clave = ["VARIABLE", "PLIEGUE", "BLOQUE", "NIVEL", "CODIGO"]
    a = set(map(tuple, listas.loc[listas["LISTA"] == "A", clave].to_numpy().tolist()))
    c = set(map(tuple, listas.loc[listas["LISTA"] == "C", clave].to_numpy().tolist())) if "C" in par["listas"] else a
    grupos = listas.groupby(["VARIABLE", "LISTA", "PLIEGUE"]).size()
    esperados = {(k, lista, f) for k in par["objetivos"] for lista in par["listas"]
                 for f in ([0, *info["pliegues"]] if lista in LISTAS_POR_PLIEGUE else [0])}
    return [
        ("Se leyeron todos los casos de estudio del conjunto de desarrollo registrado",
         info["casos"] == int(version["casos_desarrollo"])),
        ("Cada variable tiene una fila por código distinto de cada bloque, sin repetir códigos", filas_ok),
        ("En cada variable, los casos de todos los códigos suman los pares caso–código con dato", suma_ok),
        ("Las cuatro celdas de la tabla de 2×2 de cada código son mayores o iguales a cero", celdas_ok),
        ("El chi-cuadrado coincide con el de la fórmula abreviada N·(ad − bc)² / (con · sin · R · (N − R))", abreviada_igual),
        ("La V está entre 0 y 1 en todos los códigos", bool(todo["V"].between(0, 1).all())),
        ("El valor p es 0,05 cuando el chi-cuadrado es 3,841459 (control de la fórmula)",
         abs(math.erfc(math.sqrt(3.841459 / 2)) - 0.05) < 1e-6),
        ("Todos los códigos que pasan tienen descripción en las tablas del DEIS", bool((pasan["DESCRIPCION"] != "").all())),
        ("Con los umbrales principales, la sensibilidad cuenta los mismos códigos que la lista",
         sum(sum(x.values()) for x in sensibilidad.values()) == len(pasan)),
        ("Los casos y reingresos por pliegue suman los de todo desarrollo en cada código y variable", info["conteos_cuadran"]),
        ("Cada lista tiene una versión de todo desarrollo y, las que miran el reingreso, una por pliegue",
         set(grupos.index) == esperados),
        (f"Todo código de una lista tiene al menos {fmt(par['casos_minimos'])} casos en todo desarrollo",
         bool(con_fila["CASOS"].notna().all() and (con_fila["CASOS"] >= par["casos_minimos"]).all())),
        ("La lista A está contenida en la C, en todo desarrollo y en cada pliegue", a <= c),
        ("La lista A de todo desarrollo es la de los códigos que pasan el filtro",
         len(listas[(listas["LISTA"] == "A") & (listas["PLIEGUE"] == 0)]) == len(pasan)),
    ]


def escribir(todo: pd.DataFrame, listas: pd.DataFrame, nivel: str) -> list[tuple[str, bool]]:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    LISTA.parent.mkdir(parents=True, exist_ok=True)
    for tabla, ruta in ((todo, DESTINO), (listas, LISTAS)):
        temporal = ruta.with_suffix(".parquet.tmp")
        pq.write_table(pa.Table.from_pandas(tabla, preserve_index=False), temporal, compression="zstd")
        temporal.replace(ruta)
    lista = todo.loc[todo["PASA"] & (todo["NIVEL"] == nivel), COLUMNAS_LISTA]
    lista.to_csv(LISTA, sep=";", decimal=",", index=False, encoding="utf-8-sig", float_format="%.6f")

    releido = pd.read_parquet(DESTINO)
    releida = pd.read_csv(LISTA, sep=";", decimal=",", encoding="utf-8-sig", dtype={"CODIGO": str})
    try:
        pd.testing.assert_frame_equal(releido, todo, check_dtype=False)
        pd.testing.assert_frame_equal(pd.read_parquet(LISTAS), listas, check_dtype=False)
        parquet_igual = True
    except AssertionError:
        parquet_igual = False
    clave = ["VARIABLE", "BLOQUE", "CODIGO", "CASOS", "REINGRESOS"]
    lista_igual = (len(releida) == len(lista)
                   and (releida[clave].astype(str).to_numpy() == lista[clave].astype(str).to_numpy()).all())
    return [
        ("Lo releído de filtro_codigos.parquet y de listas_codigos.parquet es igual a lo calculado", parquet_igual),
        ("La lista releída tiene los mismos códigos, casos y reingresos que los que pasan el filtro", bool(lista_igual)),
    ]


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def dec(x, decimales: int = 4) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def contar(n, singular: str, plural: str) -> str:
    return f"{fmt(n)} {singular if n == 1 else plural}"


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def tasa_necesaria(n: int, N: int, R: int, v: float) -> float:
    """Tasa de reingreso (%) que necesita un código con n casos para llegar a V = v subiendo el riesgo.
    Sale de despejar los reingresos del código en la fórmula de la V: a = (n·R + v·raíz(n·(N − n)·R·(N − R))) / N."""
    a = (n * R + v * math.sqrt(n * (N - n) * R * (N - R))) / N
    return 100 * a / n


def casos_para_bajar(N: int, R: int, v: float) -> int:
    """Casos mínimos para que un código que baja el riesgo llegue a V = v aunque ninguno de sus casos reingrese:
    n ≥ v²·N·(N − R) / (R + v²·(N − R))."""
    return math.ceil(v * v * N * (N - R) / (R + v * v * (N - R)))


def escribir_reporte(todo: pd.DataFrame, listas: pd.DataFrame, info: dict, par: dict, version: dict, verificaciones: list) -> None:
    ruta = ACTIVIDAD.name
    objetivos, v_min = par["objetivos"], par["v_minima"]
    pasan = todo[todo["PASA"] & (todo["NIVEL"] == par["nivel"])]

    # Listas: tamaño de cada una en todo desarrollo y estabilidad entre pliegues (índice de Jaccard frente a la de todo
    # desarrollo: de los códigos que están en alguna de las dos, la parte que está en las dos).
    clave = ["BLOQUE", "NIVEL", "CODIGO"]
    conjuntos = {g: set(map(tuple, t[clave].to_numpy().tolist())) for g, t in listas.groupby(["VARIABLE", "LISTA", "PLIEGUE"])}
    filas_tamano = [[f"`{lista}`", *[fmt(len(conjuntos.get((k, lista, 0), set()))) for k in objetivos]] for lista in par["listas"]]
    filas_estable = []
    for lista in [x for x in LISTAS_POR_PLIEGUE if x in par["listas"]]:
        for k in objetivos:
            base = conjuntos.get((k, lista, 0), set())
            otras = [conjuntos.get((k, lista, f), set()) for f in info["pliegues"]]
            jaccard = [len(base & o) / len(base | o) if base | o else 1.0 for o in otras]
            en_todos = len(base.intersection(*otras))
            filas_estable.append([f"`{lista}`", f"`{k}`", fmt(len(base)), f"{fmt(en_todos)} ({pct(en_todos, len(base), 1)})",
                                  f"{dec(min(jaccard), 3)} a {dec(max(jaccard), 3)}",
                                  f"{fmt(min(len(base - o) for o in otras))} a {fmt(max(len(base - o) for o in otras))}",
                                  f"{fmt(min(len(o - base) for o in otras))} a {fmt(max(len(o - base) for o in otras))}"])
    filas_agrupada, ejemplo_agrupada = [], ""
    if "AGRUPADA" in par["listas"]:
        dx = todo[(todo["BLOQUE"] == "DIAGNOSTICO") & (todo["NIVEL"] == par["nivel"])]
        for k in objetivos:
            categorias = sorted(c for b, n, c in conjuntos.get((k, "AGRUPADA", 0), set()) if b == "DIAGNOSTICO")
            completos = {c for b, n, c in conjuntos.get((k, "A", 0), set()) if b == "DIAGNOSTICO"}
            solas = [c for c in categorias if not any(x.startswith(c) for x in completos)]
            # Diagnósticos completos que no pasan por sí solos, pero cuya categoría sí pasa en la lista agrupada.
            fuera = dx.loc[(dx["VARIABLE"] == k) & ~dx["CODIGO"].isin(completos), "CODIGO"]
            recuperados = int(fuera.str.split(".").str[0].isin(set(categorias)).sum())
            filas_agrupada.append([f"`{k}`", fmt(len(categorias)), fmt(recuperados), fmt(len(solas)),
                                   ", ".join(f"`{c}`" for c in solas[:8]) or "—"])
        # El ejemplo de la revisión del profesor guía (O7), si se cumple con estos datos.
        codigo, nombre = EJEMPLO_AGRUPADA
        for k in objetivos:
            en_a = (k, "A", 0) in conjuntos and any(c == codigo for _, _, c in conjuntos[(k, "A", 0)])
            categoria = todo[(todo["VARIABLE"] == k) & (todo["NIVEL"] == "CATEGORIA") & (todo["CODIGO"] == codigo.split(".")[0])]
            if not en_a and len(categoria) and bool(categoria["PASA"].iloc[0]):
                ejemplo_agrupada = (f" Por ejemplo, con `{k}`, {codigo} ({nombre}) no pasa por sí solo, pero su categoría "
                                    f"{codigo.split('.')[0]} sí (V {dec(categoria['V'].iloc[0])}).")
                break

    filas_pasan = []
    for k in objetivos:
        N, R = info["totales"][k]
        celdas = []
        for b in BLOQUES:
            p = pasan[(pasan["VARIABLE"] == k) & (pasan["BLOQUE"] == b)]
            celdas.append(f"{fmt(len(p))} ({contar((p['DIRECCION'] == 'sube').sum(), 'sube', 'suben')} y "
                          f"{contar((p['DIRECCION'] == 'baja').sum(), 'baja', 'bajan')})")
        filas_pasan.append([f"`{k}`", fmt(N), f"{fmt(R)} ({pct(R, N)})", *celdas, fmt((pasan["VARIABLE"] == k).sum())])

    filas_sens = []
    for (v, n), conteo in info["sensibilidad"].items():
        marca = " (principal)" if (v, n) == (v_min, par["casos_minimos"]) else ""
        filas_sens.append([dec(v, 3) + marca, fmt(n),
                           *[f"{fmt(sum(conteo[k].values()))} ({fmt(conteo[k]['DIAGNOSTICO'])} + {fmt(conteo[k]['PROCEDIMIENTO'])})"
                             for k in objetivos]])

    tamanos = [100, 250, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 100_000]
    filas_tasa = [[fmt(n), *[dec(tasa_necesaria(n, *info["totales"][k], v_min), 1) + " %" for k in objetivos]] for n in tamanos]
    filas_tasa.append(["Tasa de toda la variable", *[pct(info["totales"][k][1], info["totales"][k][0]) for k in objetivos]])
    filas_tasa.append(["Casos que necesita un código que baja el riesgo", *[fmt(casos_para_bajar(*info["totales"][k], v_min))
                                                                           for k in objetivos]])

    mayores = []
    for k in objetivos:
        for direccion, verbo in [("sube", "suben"), ("baja", "bajan")]:
            p = pasan[(pasan["VARIABLE"] == k) & (pasan["DIRECCION"] == direccion)].nlargest(10, "V")
            if len(p):
                mayores += [f"**`{k}`, los que más {verbo} el riesgo:**",
                            tabla_md(["Código", "Descripción", "Casos", "Reingreso con el código", "Sin el código", "V"],
                                     [[f"`{r.CODIGO}`", r.DESCRIPCION, fmt(r.CASOS), dec(r.TASA_CON_CODIGO, 2) + " %",
                                       dec(r.TASA_SIN_CODIGO, 2) + " %", dec(r.V)] for r in p.itertuples()])]

    filas_listas = []
    for b in BLOQUES:
        n_listas = pasan[pasan["BLOQUE"] == b].groupby("CODIGO")["VARIABLE"].nunique()
        filas_listas.append([NOMBRE_BLOQUE[b], fmt(len(n_listas)),
                             *[fmt((n_listas == i).sum()) for i in range(len(objetivos), 0, -1)]])

    # Códigos que pasan y cambian con los años: % de los casos de estudio de cada año que tienen el código
    casos_anio = info["casos_anio"]
    anios = [int(a) for a in casos_anio.index]
    prevalencia = {}
    for b in BLOQUES:
        frec = info["frecuencia_anual"][b].unstack(fill_value=0).reindex(columns=casos_anio.index, fill_value=0)
        frec.index = frec.index.astype(str)
        prevalencia[b] = 100 * frec / casos_anio.to_numpy()
    filas_cambio = []
    for k in objetivos:
        celdas = []
        for b in BLOQUES:
            p = prevalencia[b].loc[pasan.loc[(pasan["VARIABLE"] == k) & (pasan["BLOQUE"] == b), "CODIGO"]]
            falta = (p == 0).any(axis=1)
            razon = p.max(axis=1) / p.min(axis=1).where(~falta)
            celdas.append(f"{fmt((razon > 3).sum())} de {fmt(len(p))}" + (f" (faltan en algún año: {fmt(falta.sum())})" if falta.any() else ""))
        filas_cambio.append([f"`{k}`", *celdas])
    # Entre los que varían más del triple, los que tienen la mayor diferencia (en puntos) entre su año de mayor
    # y su año de menor frecuencia: son los que más casos afectan.
    donde = pasan.groupby(["BLOQUE", "CODIGO"])["VARIABLE"].agg(lambda s: ", ".join(f"`{x}`" for x in s))
    candidatos = []
    for (b, codigo), variables in donde.items():
        p = prevalencia[b].loc[codigo]
        if p.min() == 0 or p.max() / p.min() > 3:
            descripcion = pasan.loc[(pasan["BLOQUE"] == b) & (pasan["CODIGO"] == codigo), "DESCRIPCION"].iloc[0]
            candidatos.append((p.max() - p.min(), codigo, descripcion, p, variables))
    candidatos.sort(key=lambda x: -x[0])
    filas_top = [[f"`{codigo}`", descripcion, *[dec(x, 3) + " %" for x in p.to_numpy()], variables]
                 for _, codigo, descripcion, p, variables in candidatos[:12]]

    partes = [
        "# Filtro de dimensionalidad (actividad 3.1, script 14)",
        f"Generado por `{ruta}/scripts/14_filtro_codigos.py`. Entrada: `data/processed/{DESARROLLO.name}`, de la versión "
        f"{version['version']} de la partición (SHA-256 `{version['sha256_desarrollo']}`), y el pliegue de cada caso de "
        f"`data/processed/{GRUPOS.name}` (script 13). Salidas: `data/processed/{DESTINO.name}` (todos los códigos), "
        f"`data/processed/{LISTAS.name}` (las listas de todo desarrollo y de cada pliegue) y `{ruta}/reportes/{LISTA.name}` (la "
        f"lista fija). No se abre el conjunto de prueba. Las decisiones están en `{ruta}/bitacora.md` (D45, H30, H31 y D53).",
        f"**Filtro:** para cada variable de reingreso, pasa un código si su V de Cramér es mayor o igual a {dec(v_min, 3)} y lo "
        f"tienen al menos {fmt(par['casos_minimos'])} casos de estudio con dato en esa variable. Se usa {NIVELES[par['nivel']]}, "
        "en cualquier posición y una vez por caso. La lista calculada con todo el conjunto de desarrollo queda fija para el modelo "
        "final y se aplica sin recalcularla al conjunto de prueba (propuesta, Etapa 3). Dentro de la validación cruzada de la "
        "actividad 3.2, cada pliegue usa la lista calculada sin sus casos (D53).",

        "## 1. Códigos de los casos de estudio",
        tabla_md(["Bloque", "Códigos distintos", "Pares caso–código", "Promedio por caso"],
                 [[NOMBRE_BLOQUE[b], fmt(r["codigos"]), fmt(r["pares"]), dec(r["pares"] / info["casos"], 2)]
                  for b, r in info["bloques"].items()]),
        f"Casos de estudio de desarrollo: {fmt(info['casos'])}.",

        "## 2. Códigos que pasan el filtro",
        "Cada variable usa los casos de estudio con dato en ella: las variables de 30 días no incluyen los casos sin 60 días "
        "de seguimiento (D30), y las de misma CDM no incluyen los partos (D38).",
        tabla_md(["Variable", "Casos con dato", "Reingresos", "Diagnósticos que pasan", "Procedimientos que pasan", "Total"],
                 filas_pasan),

        "## 3. Listas para comparar en la actividad 3.2",
        "La lista A es la principal. En la actividad 3.2 los modelos se entrenan también con las demás, con la misma validación "
        "cruzada, para medir qué se pierde con el filtro (revisión del profesor guía, O7; D53):",
        "\n".join(f"- **{lista}**: {LISTAS_POSIBLES[lista]}." for lista in par["listas"]),
        f"Códigos de cada lista, calculada con todo el conjunto de desarrollo (en la C, efecto grande = riesgo al menos "
        f"{dec(par['riesgo'], 1)} veces mayor o menor, con valor p menor que {dec(par['p_maximo'], 3)}):",
        tabla_md(["Lista", *[f"`{k}`" for k in objetivos]], filas_tamano),
        *(["En la lista agrupada, una categoría de diagnóstico pasa cuando sus subcódigos, sumados, llegan al umbral, aunque por "
           "separado no lleguen." + ejemplo_agrupada + " La tabla cuenta los diagnósticos completos que no pasan por sí solos y "
           "cuya categoría sí pasa, y las categorías que pasan sin que pase ninguno de sus códigos completos:",
           tabla_md(["Variable", "Categorías de diagnóstico que pasan", "Diagnósticos que no pasan solos y cuya categoría sí",
                     "Categorías sin ningún código completo en la A", "Ejemplos"], filas_agrupada)]
          if filas_agrupada else []),

        "## 4. Listas por pliegue",
        "Las listas que miran el reingreso se calculan también con el entrenamiento de cada pliegue de la validación cruzada, es "
        "decir, sin los casos del pliegue que se evalúa (revisión del profesor guía, O5). Así, en la actividad 3.2 los casos de "
        "validación no ayudan a elegir los códigos. El índice de Jaccard compara la lista de cada pliegue con la de todo "
        "desarrollo: de los códigos que están en alguna de las dos, la parte que está en las dos (1 = iguales).",
        tabla_md(["Lista", "Variable", "Códigos (todo desarrollo)", f"En los {len(info['pliegues'])} pliegues", "Jaccard",
                  "Salen en un pliegue", "Entran en un pliegue"], filas_estable),

        "## 5. Sensibilidad de los umbrales",
        "Cuántos códigos pasarían con cada combinación de umbrales: total (diagnósticos + procedimientos). Solo se cuentan; "
        "la lista fija es la de los umbrales principales.",
        tabla_md(["V mínima", "Casos mínimos", *[f"`{k}`" for k in objetivos]], filas_sens),

        "## 6. Cuánto reingreso necesita un código para pasar",
        f"La V mide cuánto explica el código del reingreso de todos los casos, así que un código con pocos casos necesita una "
        f"diferencia muy grande para llegar a {dec(v_min, 3)} (H30). La tabla da la tasa de reingreso mínima con que pasaría un "
        "código que sube el riesgo, según cuántos casos lo tienen. Un código que baja el riesgo necesita muchos casos para "
        "pasar, aunque ninguno de ellos reingrese (última fila).",
        tabla_md(["Casos con el código", *[f"`{k}`" for k in objetivos]], filas_tasa),

        "## 7. Los códigos con mayor V",
        *mayores,

        "## 8. Códigos que pasan en varias variables",
        tabla_md(["Bloque", "Pasan en alguna variable", *[f"En {i}" for i in range(len(objetivos), 0, -1)]], filas_listas),

        "## 9. Códigos que pasan y cambian con los años",
        "Códigos que pasan cuya frecuencia (porcentaje de los casos de estudio del año que tienen el código) varía más del "
        "triple entre el año de menor y el de mayor frecuencia (H31). El filtro no cambia, pero ayuda a interpretar la "
        "validación temporal.",
        tabla_md(["Variable", *[NOMBRE_BLOQUE[b] for b in BLOQUES]], filas_cambio),
        f"De esos {fmt(len(candidatos))} códigos (contando una vez los que pasan en varias variables), los doce con la "
        "mayor diferencia entre su año de mayor y su año de menor frecuencia:",
        tabla_md(["Código", "Descripción", *[str(a) for a in anios], "Pasa en"], filas_top),

        "## 10. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{v.replace('|', ' / ')}`", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 11. Archivos de salida",
        f"`data/processed/{DESTINO.name}` tiene una fila por variable de reingreso y código, pase o no el filtro, con el código "
        "completo y, para la lista agrupada, también con la categoría de los diagnósticos (columna `NIVEL`), calculado con todo "
        f"el conjunto de desarrollo. `{ruta}/reportes/{LISTA.name}` tiene solo los códigos de la lista A, sin las columnas `NIVEL`, "
        "`CHI2`, `VALOR_P`, `RIESGO_RELATIVO`, `PASA` y `PASA_C`; se lee con `sep=\";\"`, `decimal=\",\"` y la columna `CODIGO` "
        "como texto (los procedimientos pueden empezar con cero, como `00.14`).",
        tabla_md(["Columna", "Contenido"], [
            ["`VARIABLE`", "Variable de reingreso."],
            ["`BLOQUE`", "`DIAGNOSTICO` (CIE-10) o `PROCEDIMIENTO` (CIE-9-MC)."],
            ["`NIVEL`", "`COMPLETO` (el código tal como viene) o `CATEGORIA` (la categoría del diagnóstico, para la lista agrupada)."],
            ["`CODIGO`", "El código."],
            ["`DESCRIPCION`", "Descripción según las tablas del DEIS (`Datos/Tablas auxiliares`)."],
            ["`CASOS`", "Casos de estudio con dato en la variable que tienen el código."],
            ["`REINGRESOS`", "De ellos, los que reingresan."],
            ["`TASA_CON_CODIGO` y `TASA_SIN_CODIGO`", "Porcentaje de reingreso de los casos con el código y sin él."],
            ["`CHI2` y `VALOR_P`", "Chi-cuadrado de Pearson de la tabla de 2×2 y su valor p (1 grado de libertad)."],
            ["`V`", "V de Cramér: raíz(chi-cuadrado / casos con dato). Va de 0 (sin relación) a 1."],
            ["`DIRECCION`", "`sube` si el reingreso es mayor con el código, `baja` si es menor."],
            ["`RIESGO_RELATIVO`", "Tasa de reingreso con el código dividida por la tasa sin él."],
            ["`PASA`", "Verdadero si el código pasa los dos umbrales (la regla de la lista A)."],
            ["`PASA_C`", "Verdadero si el código pasa la regla de la lista C."],
        ]),
        f"`data/processed/{LISTAS.name}` tiene una fila por código de cada lista: `VARIABLE`, `LISTA` "
        f"({', '.join(par['listas'])}), `PLIEGUE` (0 = calculada con todo desarrollo, la del modelo final; 1 a "
        f"{len(info['pliegues'])} = calculada sin los casos de ese pliegue, la que usa ese pliegue en la validación cruzada), "
        "`BLOQUE`, `NIVEL` y `CODIGO`. La lista sin filtro no mira el reingreso, así que solo tiene la versión 0.",

        "## 12. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in verificaciones),
    ]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {REPORTE}")


def main() -> None:
    inicio = time.time()
    par = cargar_parametros()
    version = comprobar_version()
    print(f"Partición: versión {version['version']}. Leyendo los casos de estudio...", flush=True)
    casos = leer_casos(par)
    print(f"{fmt(len(casos))} casos de estudio. Calculando la asociación de cada código...", flush=True)
    todo, listas, info = filtrar(par, casos)
    del casos
    agregar_descripciones(todo)
    verificaciones = [(f"El conjunto de desarrollo es el de la versión {version['version']} registrada de la partición", True)]
    verificaciones += verificar(todo, listas, info, par, version)
    verificaciones += escribir(todo, listas, par["nivel"])
    escribir_reporte(todo, listas, info, par, version, verificaciones)
    fallidas = [texto for texto, ok in verificaciones if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
