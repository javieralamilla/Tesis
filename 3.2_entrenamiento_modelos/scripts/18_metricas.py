"""Métricas de la validación cruzada (actividad 3.2, script 18).

Etapa 5 de la propuesta (comparación de los modelos). Lee las predicciones fuera de pliegue que guarda el script 17, una
tabla por combinación de variable, modelo, lista, hospital y ponderación, y calcula para cada una las métricas de D41, con
el intercepto de D43 y la calibración por año de D56, con intervalos hechos con los mismos sorteos de pacientes en todas
las combinaciones (D63). Con esos sorteos da los veredictos del ensayo de la ponderación (D61) y de las comparaciones de
listas y del hospital (D64). No entrena nada.

  1. Entradas. Comprueba que las tablas para los modelos sean la versión registrada (D57) y que cada tabla de
     predicciones sea una de las combinaciones de D64, de esa versión, con exactamente los casos con dato en su variable,
     su pliegue y probabilidades entre 0 y 1.
  2. Sorteos. Los pacientes de desarrollo, ordenados, se sortean con reposición. El sorteo b sale de un generador hecho
     con la semilla del proyecto y el número b, así que es el mismo en todas las combinaciones, se calcule donde se
     calcule. Cada caso cuenta tantas veces como salió su paciente.
  3. Métricas. AUPRC como precisión promedio, AUROC, Brier y prevalencia; intercepto con el logit como offset y pendiente,
     en general y por año del alta. Para el logit, una probabilidad exactamente 0 se cuenta como probabilidad_minima_logit
     y una exactamente 1, como 1 menos ese valor (D67). Todo se calcula sin sorteo y en cada sorteo; el intervalo son los
     percentiles 2,5 y 97,5. Al lado, la AUPRC y el AUROC de cada vuelta.
  4. Comparaciones, de a pares con los mismos sorteos. Ensayo: mejora relativa de la AUPRC al ponderar; se pondera si
     todo el intervalo pasa el margen. Listas: caída de AUROC y caída relativa de AUPRC de la lista A frente a cada otra
     lista, como proporción del valor de la otra (no pierde, no se puede afirmar o pierde). Sin hospital: la misma
     cuenta, solo para informar.
  5. Salida. Una tabla por combinación con el valor sin sorteo y los de cada sorteo en la carpeta de las métricas (fuera
     de Git), reportes/18_metricas.csv, reportes/18_comparaciones.csv y reportes/18_metricas.md.

Calcula solo lo que falta: una combinación cuyas métricas ya están guardadas, hechas con la misma tabla de predicciones
(misma huella), el mismo script y los mismos parámetros, no se repite. Calcula hasta `procesadores` combinaciones a la vez.

Uso (desde la carpeta Codigo; en el servidor, con el Python del entorno de D65 y dentro de tmux), después del script 17:
    python 3.2_entrenamiento_modelos/scripts/18_metricas.py
"""

import hashlib
import importlib.util
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import scipy
import sklearn
from scipy.special import expit
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_DATOS = RAIZ / "data" / "processed"
CASOS = DIR_DATOS / "modelos_casos.parquet"      # una fila por caso de estudio de desarrollo (script 16)
CODIGOS = DIR_DATOS / "modelos_codigos.parquet"  # solo para comprobar la versión
LISTAS = DIR_DATOS / "listas_codigos.parquet"    # solo para comprobar la versión
REGISTRO_TABLAS = RAIZ / "docs" / "version_tablas_modelos.csv"
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"  # semilla y número de pliegues
SCRIPT_17 = ACTIVIDAD / "scripts" / "17_entrenar_modelos.py"
CSV_METRICAS = ACTIVIDAD / "reportes" / "18_metricas.csv"
CSV_COMPARACIONES = ACTIVIDAD / "reportes" / "18_comparaciones.csv"
REPORTE = ACTIVIDAD / "reportes" / "18_metricas.md"

PRINCIPALES = ["prevalencia", "AUPRC", "AUROC", "Brier", "intercepto", "pendiente"]
OTRAS_LISTAS = ["SIN_FILTRO", "AGRUPADA", "C"]  # en el orden de D64
NOMBRE_LISTA = {"A": "A", "SIN_FILTRO": "sin filtro", "AGRUPADA": "agrupada", "C": "C"}
NOMBRE_MODELO = {"LR": "Regresión logística", "RF": "Random Forest", "XGB": "XGBoost"}
TEXTOS_VERIFICACION = {
    "casos": "La tabla de predicciones tiene exactamente los casos con dato en su variable, cada uno con su pliegue, y probabilidades entre 0 y 1, sin vacíos",
    "informacion": "La información guardada en la tabla de predicciones coincide con su nombre, la semilla y la versión de las tablas",
    "sklearn": "Sin sorteo, la AUPRC, el AUROC y el Brier coinciden con las funciones de scikit-learn",
    "calibracion": "La calibración (general y por año) llegó a la solución sin sorteo y en todos los sorteos",
}


# ------------------------------------------------------------------ utilidades
def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def num(x, decimales: int = 3, signo: bool = False) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:{'+' if signo else ''}.{decimales}f}".replace(".", ",").replace("-", "−")


def con_intervalo(v: float, lo: float, hi: float, decimales: int = 3, signo: bool = False) -> str:
    return f"{num(v, decimales, signo)} ({num(lo, decimales, signo)} a {num(hi, decimales, signo)})"


def pct(x, decimales: int = 1) -> str:
    return "—" if x is None or np.isnan(x) else f"{x * 100:.{decimales}f} %".replace(".", ",").replace("-", "−")


def entero(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(lineas)


def decimal_csv(x) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{x:.6f}".replace(".", ",")


# ------------------------------------------------------------------ 1. parámetros y combinaciones
def cargar_script_17():
    """El script 17 da los parámetros de D60 a D65, la versión de las tablas y los nombres de las combinaciones, para que
    los dos scripts lean lo mismo."""
    spec = importlib.util.spec_from_file_location("script_17", SCRIPT_17)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for nombre in ["RAIZ", "CASOS", "CODIGOS", "LISTAS", "REGISTRO_TABLAS", "PARAMETROS", "PARAMETROS_23"]:
        setattr(m, nombre, globals()[nombre])  # el script 17 lee las mismas tablas y parámetros que este
    return m


def cargar_parametros(s17) -> dict:
    par = s17.cargar_parametros()
    filas = {f["parametro"]: f["valor"].strip() for f in s17.leer_csv(PARAMETROS)}

    def leer(nombre: str) -> str:
        if nombre not in filas:
            raise SystemExit(f"Falta el parámetro '{nombre}' en {PARAMETROS}.")
        return filas[nombre]

    def numero(nombre: str) -> float:
        return float(leer(nombre).replace(",", "."))

    par.update(sorteos=int(numero("sorteos")), confianza=numero("confianza"),
               p_min=numero("probabilidad_minima_logit"), margen_auroc=numero("margen_auroc"),
               margen_auprc=numero("margen_auprc"), margen_ponderacion=numero("margen_ponderacion"),
               carpeta_metricas=RAIZ / leer("carpeta_metricas"))
    if par["sorteos"] < 1 or not 0 < par["confianza"] < 100 or not 0 < par["p_min"] < 0.5:
        raise SystemExit(f"Revise sorteos, confianza y probabilidad_minima_logit en {PARAMETROS}.")
    return par


def combinaciones_validas(s17, par: dict) -> dict[str, dict]:
    """Las combinaciones de D64 que pueden tener predicciones: las del ensayo y, si ya se resolvió, las demás con la
    ponderación decidida (D61)."""
    validas = {}
    for etapa in ["ensayo", "base", "sin_filtro", "agrupada", "sin_hospital", "c"]:
        if etapa != "ensayo" and not par["ensayo_resuelto"]:
            continue
        for c in s17.combinaciones(etapa, par):
            validas[s17.nombre_archivo(c)] = {**c, "etapa": etapa}
    return validas


# ------------------------------------------------------------------ 2 y 3. sorteos y métricas (en cada proceso)
def sorteo(semilla: int, b: int, n_pacientes: int) -> np.ndarray:
    """Cuántas veces sale cada paciente en el sorteo b: n_pacientes extracciones con reposición. El generador depende
    solo de la semilla y de b, así que el sorteo b es el mismo en todas las combinaciones (D63)."""
    rng = np.random.default_rng([semilla, b])
    return np.bincount(rng.integers(0, n_pacientes, size=n_pacientes), minlength=n_pacientes)


def areas(y_o: np.ndarray, w_o: np.ndarray, fin: np.ndarray) -> tuple[float, float]:
    """AUPRC como precisión promedio y AUROC, con pesos, con los casos ya ordenados de mayor a menor probabilidad. `fin` es
    la posición del último caso de cada valor distinto: los empates se cuentan juntos, como en scikit-learn."""
    vp = np.cumsum(w_o * y_o)[fin]           # reingresos encontrados hasta cada umbral
    fp = np.cumsum(w_o * (1.0 - y_o))[fin]   # casos sin reingreso marcados hasta cada umbral
    if vp[-1] <= 0 or fp[-1] <= 0:
        return np.nan, np.nan
    exhaustividad = vp / vp[-1]
    marcados = vp + fp
    precision = np.divide(vp, marcados, out=np.zeros_like(vp), where=marcados > 0)
    auprc = float(np.sum(np.diff(exhaustividad, prepend=0.0) * precision))
    tpr, fpr = np.r_[0.0, exhaustividad], np.r_[0.0, fp / fp[-1]]
    auroc = float(np.sum(np.diff(fpr) * (tpr[1:] + tpr[:-1]) / 2))
    return auprc, auroc


def calibrar(y, lp, w, grupo, n_grupos, a, b, pendiente: bool, iter_max: int = 100, tol: float = 1e-9):
    """Regresión logística de la calibración (D43), por Newton, en varios grupos a la vez (todos los casos o cada año).
    Con pendiente: logit P(reingreso) = a + b · logit(p). Sin ella: logit P(reingreso) = a + logit(p), con el logit como
    offset. Cada paso es de a lo más 1, para que no se dispare si parte lejos de la solución."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    for _ in range(iter_max):
        mu = expit(a[grupo] + (b[grupo] * lp if pendiente else lp))
        r, v = w * (y - mu), w * mu * (1.0 - mu)
        g0, h00 = np.bincount(grupo, r, n_grupos), np.bincount(grupo, v, n_grupos)
        if pendiente:
            g1 = np.bincount(grupo, r * lp, n_grupos)
            h01, h11 = np.bincount(grupo, v * lp, n_grupos), np.bincount(grupo, v * lp * lp, n_grupos)
            det = h00 * h11 - h01 * h01
            da, db = (h11 * g0 - h01 * g1) / det, (h00 * g1 - h01 * g0) / det
        else:
            da, db = g0 / h00, np.zeros(n_grupos)
        mayor = np.maximum(np.abs(da), np.abs(db))
        escala = np.minimum(1.0, 1.0 / np.maximum(mayor, 1e-300))
        a, b = a + escala * da, b + escala * db
        if np.all(np.isfinite(mayor)) and mayor.max() < tol:
            return a, b, True
    return a, b, False


def medir(d: dict, w: np.ndarray, inicio: dict | None) -> tuple[dict, bool]:
    """Todas las métricas con los pesos w (1 en todos los casos = sin sorteo). `inicio`: los valores sin sorteo, desde
    donde parte la calibración de cada sorteo."""
    G = len(d["anios"])
    auprc, auroc = areas(d["y_o"], w[d["orden"]], d["fin"])
    total = w.sum()
    r = {"prevalencia": float(np.sum(w * d["y"]) / total), "AUPRC": auprc, "AUROC": auroc,
         "Brier": float(np.sum(w * (d["p"] - d["y"]) ** 2) / total)}
    if inicio is None:
        inicio = {"intercepto": 0.0, "a_pendiente": 0.0, "pendiente": 1.0,
                  **{f"intercepto_{t}": 0.0 for t in d["anios"]}, **{f"a_pendiente_{t}": 0.0 for t in d["anios"]},
                  **{f"pendiente_{t}": 1.0 for t in d["anios"]}}
    y, lp, cero, g = d["y"], d["lp"], d["cero"], d["grupo"]
    a1, _, ok1 = calibrar(y, lp, w, cero, 1, [inicio["intercepto"]], [1.0], False)
    a2, b2, ok2 = calibrar(y, lp, w, cero, 1, [inicio["a_pendiente"]], [inicio["pendiente"]], True)
    a3, _, ok3 = calibrar(y, lp, w, g, G, [inicio[f"intercepto_{t}"] for t in d["anios"]], np.ones(G), False)
    a4, b4, ok4 = calibrar(y, lp, w, g, G, [inicio[f"a_pendiente_{t}"] for t in d["anios"]],
                           [inicio[f"pendiente_{t}"] for t in d["anios"]], True)
    r.update(intercepto=float(a1[0]), a_pendiente=float(a2[0]), pendiente=float(b2[0]))
    for i, t in enumerate(d["anios"]):
        r[f"intercepto_{t}"], r[f"a_pendiente_{t}"], r[f"pendiente_{t}"] = float(a3[i]), float(a4[i]), float(b4[i])
    return r, ok1 and ok2 and ok3 and ok4


def calcular_combinacion(tarea: dict) -> dict:
    """Una combinación: comprueba su tabla de predicciones, calcula las métricas sin sorteo y en cada sorteo y las guarda.
    Se ejecuta en un proceso aparte: todo lo que necesita viene en `tarea`."""
    inicio_reloj = time.perf_counter()
    c, par = tarea["combinacion"], tarea["parametros"]
    v = c["variable"]
    casos = pd.read_parquet(tarea["casos"], columns=["ID_EGRESO", "ID_PACIENTE", "ANIO_ALTA", "PLIEGUE", v])
    pacientes = np.unique(casos["ID_PACIENTE"].to_numpy())  # todos los de desarrollo: los mismos sorteos en las cuatro variables
    anios = [int(t) for t in np.unique(casos["ANIO_ALTA"].to_numpy())]
    con = casos[casos[v].notna()]
    tabla = pq.read_table(tarea["prediccion"])
    meta = {k.decode(): x.decode() for k, x in (tabla.schema.metadata or {}).items()}
    pred = tabla.to_pandas()

    verif = {}
    esperado = {"variable": v, "modelo": c["modelo"], "lista": c["lista"], "hospital": "CON" if c["hospital"] else "SIN",
                "ponderacion": "SI" if c["ponderar"] else "NO", "semilla": str(par["semilla"]),
                "version_tablas": tarea["version"]}
    verif["informacion"] = all(meta.get(k) == x for k, x in esperado.items())
    repetidos = bool(pred["ID_EGRESO"].duplicated().any())
    unidos = con.merge(pred.drop_duplicates("ID_EGRESO"), on="ID_EGRESO", how="inner", suffixes=("", "_pred"))
    pr = unidos["PROBABILIDAD"].to_numpy(dtype=np.float64)
    verif["casos"] = (not repetidos and len(pred) == len(con) == len(unidos)
                      and bool((unidos["PLIEGUE"].astype(int) == unidos["PLIEGUE_pred"].astype(int)).all())
                      and bool(np.isfinite(pr).all() and (pr >= 0).all() and (pr <= 1).all()))
    if not (verif["casos"] and verif["informacion"]):
        return {"nombre": Path(tarea["prediccion"]).name, "verificaciones": verif, "guardada": False, "avisos": []}

    y = unidos[v].to_numpy(dtype=np.float64)
    p_min = par["p_min"]
    q = np.where(pr == 0, p_min, np.where(pr == 1, 1 - p_min, pr))  # D67: solo los 0 y los 1 exactos
    orden = np.argsort(-pr, kind="mergesort")
    d = {"y": y, "p": pr, "lp": np.log(q / (1 - q)), "orden": orden, "y_o": y[orden],
         "fin": np.r_[np.flatnonzero(np.diff(pr[orden])), len(pr) - 1], "anios": anios,
         "grupo": np.searchsorted(anios, unidos["ANIO_ALTA"].to_numpy()).astype(np.int64),
         "cero": np.zeros(len(y), dtype=np.int64)}
    indice = np.searchsorted(pacientes, unidos["ID_PACIENTE"].to_numpy())
    avisos = []
    ceros, unos = pr == 0, pr == 1
    bajo = (pr > 0) & (pr < p_min)
    if ceros.any() and bajo.any():
        avisos.append(f"{int(bajo.sum())} casos tienen probabilidades positivas bajo {p_min}: con el reemplazo de los 0, "
                      "esos casos quedan por debajo de los que tenían 0")

    punto, ok = medir(d, np.ones(len(y)), None)
    convergio = ok
    verif["sklearn"] = (abs(punto["AUPRC"] - average_precision_score(y, pr)) < 1e-9
                        and abs(punto["AUROC"] - roc_auc_score(y, pr)) < 1e-9
                        and abs(punto["Brier"] - brier_score_loss(y, pr)) < 1e-9)
    por_vuelta = {}
    pliegue = unidos["PLIEGUE"].to_numpy()
    for k in sorted(np.unique(pliegue).tolist()):
        por_vuelta[str(k)] = areas(d["y_o"], (pliegue == k).astype(np.float64)[orden], d["fin"])
    por_anio = {str(t): {"casos": int((d["grupo"] == i).sum()), "reingresos": int(y[d["grupo"] == i].sum()),
                         "observado": float(y[d["grupo"] == i].mean()), "predicho": float(pr[d["grupo"] == i].mean())}
                for i, t in enumerate(anios)}

    filas = [{"sorteo": 0, **punto}]
    primero = None
    for b in range(1, par["sorteos"] + 1):
        cuenta = sorteo(par["semilla"], b, len(pacientes))
        if b == 1:
            primero = hashlib.sha256(cuenta.astype(np.int64).tobytes()).hexdigest()
        r, ok = medir(d, cuenta[indice].astype(np.float64), punto)
        convergio = convergio and ok
        filas.append({"sorteo": b, **r})
    verif["calibracion"] = convergio
    resultado = pd.DataFrame(filas)

    datos_meta = {
        "variable": v, "modelo": c["modelo"], "lista": c["lista"], "hospital": esperado["hospital"],
        "ponderacion": esperado["ponderacion"], "etapa": c["etapa"], "huella_predicciones": tarea["huella"],
        "huella_script": tarea["huella_script"], "semilla": str(par["semilla"]), "sorteos": str(par["sorteos"]),
        "probabilidad_minima_logit": repr(p_min), "version_tablas": tarea["version"], "commit": tarea["commit"],
        "huella_pacientes": hashlib.sha256(pacientes.astype(np.int64).tobytes()).hexdigest(), "huella_sorteo_1": primero or "",
        "casos": str(len(y)), "reingresos": str(int(y.sum())), "ceros": str(int(ceros.sum())),
        "reingresos_ceros": str(int(y[ceros].sum())), "unos": str(int(unos.sum())), "anios": json.dumps(anios),
        "por_vuelta": json.dumps(por_vuelta), "por_anio": json.dumps(por_anio), "verificaciones": json.dumps(verif),
        "avisos": json.dumps(avisos, ensure_ascii=False), "numpy": np.__version__, "scikit_learn": sklearn.__version__,
        "segundos": f"{time.perf_counter() - inicio_reloj:.1f}"}
    guardada = all(verif.values())
    if guardada:  # se escribe con otro nombre y se renombra al final: un corte no deja una tabla a medias
        salida = Path(tarea["salida"])
        temporal = salida.with_name(salida.name + ".tmp")
        t = pa.Table.from_pandas(resultado, preserve_index=False)
        pq.write_table(t.replace_schema_metadata({k: str(x) for k, x in datos_meta.items()}), temporal)
        os.replace(temporal, salida)
    return {"nombre": Path(tarea["prediccion"]).name, "verificaciones": verif, "guardada": guardada, "avisos": avisos,
            "segundos": time.perf_counter() - inicio_reloj}


def vigente(salida: Path, huella: str, huella_script: str, par: dict, version: str) -> bool:
    """Las métricas guardadas sirven si salen de la misma tabla de predicciones, del mismo script y con los mismos
    parámetros."""
    if not salida.exists():
        return False
    meta = {k.decode(): x.decode() for k, x in (pq.read_schema(salida).metadata or {}).items()}
    return (meta.get("huella_predicciones") == huella and meta.get("huella_script") == huella_script
            and meta.get("semilla") == str(par["semilla"]) and meta.get("sorteos") == str(par["sorteos"])
            and meta.get("probabilidad_minima_logit") == repr(par["p_min"]) and meta.get("version_tablas") == version)


# ------------------------------------------------------------------ 4. comparaciones
def intervalo(x: np.ndarray, confianza: float) -> tuple[float, float]:
    cola = (100 - confianza) / 2
    lo, hi = np.percentile(x, [cola, 100 - cola])
    return float(lo), float(hi)


def veredicto_lista(c_prc: tuple, c_roc: tuple, par: dict) -> str:
    """D64 con los extremos del intervalo: pierde si alguna caída pasa entera su margen; no pierde si las dos quedan
    enteras dentro; si no, no se puede afirmar."""
    if c_prc[1] > par["margen_auprc"] or c_roc[1] > par["margen_auroc"]:
        return "Pierde"
    if c_prc[2] <= par["margen_auprc"] and c_roc[2] <= par["margen_auroc"]:
        return "No pierde"
    return "No se puede afirmar"


def comparar(base: pd.DataFrame, otra: pd.DataFrame, par: dict) -> dict:
    """Caída de la combinación `base` frente a `otra`, sorteo por sorteo: AUROC en puntos y AUPRC como proporción del
    valor de `otra`. La fila 0 es el valor sin sorteo; las demás, los sorteos (los mismos en las dos tablas)."""
    if not np.array_equal(base["sorteo"].to_numpy(), otra["sorteo"].to_numpy()):
        raise SystemExit("Dos combinaciones que se comparan no tienen los mismos sorteos.")
    s0, o0 = base.iloc[0], otra.iloc[0]
    sb, ob = base.iloc[1:], otra.iloc[1:]
    caida_prc = (ob["AUPRC"].to_numpy() - sb["AUPRC"].to_numpy()) / ob["AUPRC"].to_numpy()
    caida_roc = ob["AUROC"].to_numpy() - sb["AUROC"].to_numpy()
    return {"auprc": ((o0["AUPRC"] - s0["AUPRC"]) / o0["AUPRC"], *intervalo(caida_prc, par["confianza"])),
            "auroc": (o0["AUROC"] - s0["AUROC"], *intervalo(caida_roc, par["confianza"])),
            "auprc_base": s0["AUPRC"], "auprc_otra": o0["AUPRC"], "auroc_base": s0["AUROC"], "auroc_otra": o0["AUROC"]}


def comparaciones(s17, par: dict, res: dict) -> tuple[list[dict], dict]:
    """El ensayo (D61), las listas y el hospital (D64), con lo que ya esté calculado."""
    filas, ensayo = [], {}
    nombre = lambda v, m, l, h, p: s17.nombre_archivo({"variable": v, "modelo": m, "lista": l, "hospital": h, "ponderar": p})
    for m in par["modelos"]:
        sin, con = (nombre(par["variable_ensayo"], m, "A", True, p) for p in (False, True))
        if sin in res and con in res:
            s, c = res[sin][0], res[con][0]
            mejora = (c["AUPRC"].to_numpy()[1:] - s["AUPRC"].to_numpy()[1:]) / s["AUPRC"].to_numpy()[1:]
            lo, hi = intervalo(mejora, par["confianza"])
            valor = c["AUPRC"].iloc[0] / s["AUPRC"].iloc[0] - 1
            ver = "Ponderar" if lo > par["margen_ponderacion"] else "No ponderar"
            ensayo[m] = {"sin": s["AUPRC"].iloc[0], "con": c["AUPRC"].iloc[0], "mejora": (valor, lo, hi), "veredicto": ver,
                         "pares": (sin, con)}
            filas.append({"tipo": "ENSAYO", "variable": par["variable_ensayo"], "modelo": m, "frente_a": "ponderado",
                          "ponderacion": "—", "medida": "mejora relativa de la AUPRC", "valor": valor, "inferior": lo,
                          "superior": hi, "margen": par["margen_ponderacion"], "veredicto": ver, "pares": (sin, con)})
    if not par["ensayo_resuelto"]:
        return filas, ensayo
    for v in par["variables"]:
        for m in par["modelos"]:
            pond = par["ponderar"][m]
            a = nombre(v, m, "A", True, pond)
            if a not in res:
                continue
            for lista in OTRAS_LISTAS:
                o = nombre(v, m, lista, True, pond)
                if o not in res:
                    continue
                r = comparar(res[a][0], res[o][0], par)
                ver = veredicto_lista(r["auprc"], r["auroc"], par)
                for medida, clave, margen in [("caída relativa de la AUPRC", "auprc", par["margen_auprc"]),
                                              ("caída del AUROC", "auroc", par["margen_auroc"])]:
                    filas.append({"tipo": "LISTA", "variable": v, "modelo": m, "frente_a": lista,
                                  "ponderacion": "SI" if pond else "NO", "medida": medida, "valor": r[clave][0],
                                  "inferior": r[clave][1], "superior": r[clave][2], "margen": margen, "veredicto": ver,
                                  "pares": (a, o), "detalle": r})
            s = nombre(v, m, "A", False, pond)
            if s in res:
                r = comparar(res[s][0], res[a][0], par)  # la caída de la A sin hospital frente a la A con hospital
                ver = veredicto_lista(r["auprc"], r["auroc"], par)
                for medida, clave, margen in [("caída relativa de la AUPRC", "auprc", par["margen_auprc"]),
                                              ("caída del AUROC", "auroc", par["margen_auroc"])]:
                    filas.append({"tipo": "SIN_HOSPITAL", "variable": v, "modelo": m, "frente_a": "con hospital",
                                  "ponderacion": "SI" if pond else "NO", "medida": medida, "valor": r[clave][0],
                                  "inferior": r[clave][1], "superior": r[clave][2], "margen": margen,
                                  "veredicto": f"{ver} (solo informa)", "pares": (s, a), "detalle": r})
    return filas, ensayo


# ------------------------------------------------------------------ 5. salidas
def en_orden(res: dict, par: dict) -> list:
    """Las combinaciones por variable, modelo, lista (A, sin filtro, agrupada, C), con hospital antes y sin ponderar antes."""
    def clave(item):
        meta = item[1][1]
        return (par["variables"].index(meta["variable"]), par["modelos"].index(meta["modelo"]),
                (["A"] + OTRAS_LISTAS).index(meta["lista"]), meta["hospital"] != "CON", meta["ponderacion"] == "SI")
    return sorted(res.items(), key=clave)


def escribir_csv(res: dict, filas_comp: list[dict], par: dict) -> None:
    lineas = [";".join(["variable", "modelo", "lista", "hospital", "ponderacion", "grupo", "metrica", "valor", "inferior",
                        "superior"])]
    for nombre_tabla, (df, meta) in en_orden(res, par):
        clave = [meta["variable"], meta["modelo"], meta["lista"], meta["hospital"], meta["ponderacion"]]
        cero = df.iloc[0]
        for k in PRINCIPALES:
            lo, hi = intervalo(df[k].to_numpy()[1:], par["confianza"])
            lineas.append(";".join(clave + ["TODOS", k, decimal_csv(cero[k]), decimal_csv(lo), decimal_csv(hi)]))
        lineas.append(";".join(clave + ["TODOS", "cociente_AUPRC_prevalencia", decimal_csv(cero["AUPRC"] / cero["prevalencia"]), "", ""]))
        lineas.append(";".join(clave + ["TODOS", "Brier_referencia", decimal_csv(cero["prevalencia"] * (1 - cero["prevalencia"])), "", ""]))
        lineas.append(";".join(clave + ["TODOS", "casos_con_0", meta["ceros"], "", ""]))
        lineas.append(";".join(clave + ["TODOS", "reingresos_con_0", meta["reingresos_ceros"], "", ""]))
        por_anio = json.loads(meta["por_anio"])
        for t in json.loads(meta["anios"]):
            for k in ["intercepto", "pendiente"]:
                lo, hi = intervalo(df[f"{k}_{t}"].to_numpy()[1:], par["confianza"])
                lineas.append(";".join(clave + [str(t), k, decimal_csv(cero[f"{k}_{t}"]), decimal_csv(lo), decimal_csv(hi)]))
            for k in ["observado", "predicho"]:
                lineas.append(";".join(clave + [str(t), k, decimal_csv(por_anio[str(t)][k]), "", ""]))
        for k, (prc, roc) in json.loads(meta["por_vuelta"]).items():
            lineas.append(";".join(clave + [f"VUELTA_{k}", "AUPRC", decimal_csv(prc), "", ""]))
            lineas.append(";".join(clave + [f"VUELTA_{k}", "AUROC", decimal_csv(roc), "", ""]))
    CSV_METRICAS.parent.mkdir(parents=True, exist_ok=True)
    CSV_METRICAS.write_text("﻿" + "\n".join(lineas) + "\n", encoding="utf-8")
    campos = ["tipo", "variable", "modelo", "frente_a", "ponderacion", "medida", "valor", "inferior", "superior", "margen",
              "veredicto"]
    lineas = [";".join(campos)]
    for f in filas_comp:
        lineas.append(";".join(decimal_csv(f[k]) if k in ("valor", "inferior", "superior", "margen") else str(f[k]) for k in campos))
    CSV_COMPARACIONES.write_text("﻿" + "\n".join(lineas) + "\n", encoding="utf-8")


def escribir_reporte(s17, par, version, git, res, verificaciones, filas_comp, ensayo, validas, duracion) -> None:
    lineas = ["# Métricas de la validación cruzada (script 18)", "",
              f"Última ejecución: el {datetime.now().strftime('%Y-%m-%d %H:%M')}, en {num(duracion / 60, 1)} minutos. "
              f"Commit del código: `{git[0]}` (cambios sin confirmar en los scripts o las reglas: {git[1]}). "
              f"Tablas para los modelos: versión {version['version']} del {version['fecha']}. "
              f"Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}, scipy {scipy.__version__}, "
              f"scikit-learn {sklearn.__version__}. Semilla {par['semilla']}; {entero(par['sorteos'])} sorteos de pacientes, "
              f"intervalos al {num(par['confianza'], 0)} %; para el logit de la calibración, un 0 exacto se cuenta como "
              f"{str(par['p_min']).replace('.', ',')} (D67).", "",
              "Ninguna cifra de este reporte sale del conjunto de prueba: todas son predicciones fuera de pliegue del conjunto de desarrollo.", "",
              "## 1. Verificaciones", ""]
    lineas += [f"- {'✓' if ok else '✗ FALLÓ:'} {texto}" for texto, ok in verificaciones]
    avisos = [(n, a) for n, (_, meta) in en_orden(res, par) for a in json.loads(meta["avisos"])]
    if avisos:
        lineas += ["", "Avisos:"] + [f"- {n.removesuffix('.parquet')}: {a}" for n, a in avisos]

    lineas += ["", "## 2. Ensayo de la ponderación (D61)", "",
               f"Con `{par['variable_ensayo']}` y la lista A. Un modelo se entrena ponderado solo si su AUPRC con ponderación "
               f"supera en más de {pct(par['margen_ponderacion'], 0)} a la sin ponderar en todo el intervalo pareado.", ""]
    if ensayo:
        lineas += [tabla_md(["Modelo", "AUPRC sin ponderar", "AUPRC ponderada", "Cambio relativo (intervalo)", "Veredicto"],
                            [[NOMBRE_MODELO[m], num(e["sin"]), num(e["con"]),
                              f"{pct(e['mejora'][0])} ({pct(e['mejora'][1])} a {pct(e['mejora'][2])})", e["veredicto"]]
                             for m, e in ensayo.items()]), ""]
        if len(ensayo) == len(par["modelos"]):
            fijar = ", ".join(f"`ponderar_{m}` = {'SI' if e['veredicto'] == 'Ponderar' else 'NO'}" for m, e in ensayo.items())
            if par["ensayo_resuelto"]:
                distintos = [m for m, e in ensayo.items() if (e["veredicto"] == "Ponderar") != par["ponderar"][m]]
                lineas += [f"El ensayo ya está resuelto en `reglas/parametros.csv`. "
                           + (f"**Atención:** la ponderación fijada no coincide con el veredicto en {', '.join(distintos)}."
                              if distintos else "La ponderación fijada coincide con el veredicto."), ""]
            else:
                lineas += [f"Para seguir: en el portátil, fijar en `reglas/parametros.csv` {fijar} y `ensayo_resuelto` = SI, "
                           "con el visto bueno de la persona a cargo; commit y push, y `git pull` en el servidor antes de la etapa base.", ""]
            if any(e["veredicto"] == "Ponderar" for e in ensayo.values()):
                lineas += ["**Algún modelo se pondera:** antes de seguir hay que decidir la recalibración de Platt (D61).", ""]
    else:
        lineas += ["Todavía faltan las predicciones del ensayo.", ""]

    filas_a, filas_b = [], []
    for n, (df, meta) in en_orden(res, par):
        cero = df.iloc[0]
        iv = {k: intervalo(df[k].to_numpy()[1:], par["confianza"]) for k in PRINCIPALES}
        clave = [meta["variable"], meta["modelo"], NOMBRE_LISTA[meta["lista"]], meta["hospital"].lower(), meta["ponderacion"]]
        filas_a.append(clave + [entero(meta["casos"]), pct(cero["prevalencia"], 2), con_intervalo(cero["AUPRC"], *iv["AUPRC"]),
                                num(cero["AUPRC"] / cero["prevalencia"], 2), con_intervalo(cero["AUROC"], *iv["AUROC"])])
        filas_b.append(clave + [con_intervalo(cero["Brier"], *iv["Brier"], decimales=4),
                                num(cero["prevalencia"] * (1 - cero["prevalencia"]), 4),
                                con_intervalo(cero["intercepto"], *iv["intercepto"], signo=True),
                                con_intervalo(cero["pendiente"], *iv["pendiente"], decimales=2),
                                f"{entero(meta['ceros'])} ({entero(meta['reingresos_ceros'])})"])
    encabezado = ["Variable", "Modelo", "Lista", "Hospital", "Ponderado"]
    lineas += ["## 3. Discriminación de cada combinación", "",
               "La AUPRC de un modelo al azar es la prevalencia; el cociente dice cuántas veces la supera (D41). Entre paréntesis, "
               "el intervalo de los sorteos.", "",
               tabla_md(encabezado + ["Casos", "Prevalencia", "AUPRC", "Cociente", "AUROC"], filas_a), "",
               "## 4. Brier y calibración de cada combinación", "",
               "Brier de referencia: el de dar a todos la prevalencia, p(1 − p). Intercepto con el logit como offset (ideal 0; "
               "positivo, el modelo subestima el riesgo) y pendiente (ideal 1; menor que 1, predicciones demasiado extremas) (D43). "
               "La última columna dice cuántos casos tienen probabilidad 0 y, entre paréntesis, cuántos de ellos reingresaron (D67).", "",
               tabla_md(encabezado + ["Brier", "Brier de referencia", "Intercepto", "Pendiente", "Casos con 0 (reingresan)"], filas_b), ""]

    filas_anio, filas_vuelta = [], []
    for n, (df, meta) in en_orden(res, par):
        if meta["lista"] != "A" or meta["hospital"] != "CON" or meta["etapa"] not in ("ensayo", "base"):
            continue
        if meta["etapa"] == "ensayo" and (meta["ponderacion"] == "SI") != (par["ensayo_resuelto"] and par["ponderar"][meta["modelo"]]):
            continue  # del ensayo, solo la versión que queda como principal
        cero, por_anio = df.iloc[0], json.loads(meta["por_anio"])
        for t in json.loads(meta["anios"]):
            pa_ = por_anio[str(t)]
            filas_anio.append([meta["variable"], meta["modelo"], t, entero(pa_["casos"]), pct(pa_["observado"], 2), pct(pa_["predicho"], 2),
                               con_intervalo(cero[f"intercepto_{t}"], *intervalo(df[f"intercepto_{t}"].to_numpy()[1:], par["confianza"]), signo=True),
                               con_intervalo(cero[f"pendiente_{t}"], *intervalo(df[f"pendiente_{t}"].to_numpy()[1:], par["confianza"]), decimales=2)])
        vueltas = json.loads(meta["por_vuelta"])
        filas_vuelta.append([meta["variable"], meta["modelo"]] + [f"{num(prc)} / {num(roc)}" for prc, roc in vueltas.values()])
    lineas += ["## 5. Calibración por año del alta (lista A con hospital, D56)", "",
               tabla_md(["Variable", "Modelo", "Año", "Casos", "Observado", "Predicho", "Intercepto", "Pendiente"], filas_anio)
               if filas_anio else "Todavía no hay combinaciones principales.", "",
               "## 6. AUPRC / AUROC de cada vuelta (lista A con hospital, D63)", "",
               tabla_md(["Variable", "Modelo"] + [f"Vuelta {k}" for k in range(1, par["pliegues"] + 1)], filas_vuelta)
               if filas_vuelta else "Todavía no hay combinaciones principales.", ""]

    def tabla_comparacion(tipo):
        filas = {}
        for f in filas_comp:
            if f["tipo"] == tipo:
                clave = (f["variable"], f["modelo"], f["frente_a"])
                filas.setdefault(clave, {})[f["medida"]] = f
        salida = []
        for (v, m, frente), medidas in filas.items():
            prc, roc = medidas["caída relativa de la AUPRC"], medidas["caída del AUROC"]
            salida.append([v, m, NOMBRE_LISTA.get(frente, frente), f"{pct(prc['valor'])} ({pct(prc['inferior'])} a {pct(prc['superior'])})",
                           con_intervalo(roc["valor"], roc["inferior"], roc["superior"], signo=True), prc["veredicto"]])
        return salida

    listas = tabla_comparacion("LISTA")
    conteo = pd.Series([f[-1] for f in listas]).value_counts().to_dict() if listas else {}
    lineas += ["## 7. La lista A frente a las otras listas (D64)", "",
               f"Caída de la lista A frente a cada otra lista, sorteo por sorteo con los mismos pacientes: el AUROC en puntos y la "
               f"AUPRC como proporción del valor de la otra lista. Márgenes del objetivo específico 3: {num(par['margen_auroc'], 2)} "
               f"y {pct(par['margen_auprc'], 0)}. **Pierde** si alguna caída pasa entera su margen; **no pierde** si las dos quedan "
               "enteras dentro; si no, **no se puede afirmar**. Si la A pierde, se lleva al profesor guía antes de la actividad 3.3.", ""]
    lineas += [tabla_md(["Variable", "Modelo", "Frente a", "Caída de la AUPRC", "Caída del AUROC", "Veredicto"], listas),
               "", "Veredictos: " + ", ".join(f"{k}: {x}" for k, x in conteo.items()) + ".", ""] if listas else \
        ["Todavía no hay comparaciones: faltan las predicciones de alguna de las dos listas.", ""]
    hospital = tabla_comparacion("SIN_HOSPITAL")
    lineas += ["## 8. La lista A sin hospital (D64, solo informa)", "",
               "Cuánto pierde el modelo sin `HOSPITAL`, con la misma cuenta: la caída sin hospital frente a con hospital.", ""]
    lineas += [tabla_md(["Variable", "Modelo", "Frente a", "Caída de la AUPRC", "Caída del AUROC", "Veredicto"], hospital), ""] \
        if hospital else ["Todavía no hay comparaciones sin hospital.", ""]

    por_etapa = {}
    for n, c in validas.items():
        e = por_etapa.setdefault(c["etapa"], [0, 0, []])
        e[0] += 1
        if n in res:
            e[1] += 1
        else:
            e[2].append(n.removesuffix(".parquet"))
    faltan = [n for _, _, lista in por_etapa.values() for n in lista]
    lineas += ["## 9. Combinaciones", "",
               f"Con métricas: {len(res)} de {len(validas)}"
               + ("." if par["ensayo_resuelto"] else " (mientras el ensayo no esté resuelto, solo cuentan las 6 del ensayo; "
                  "las otras 57 se entrenan después)."), "",
               tabla_md(["Etapa del script 17", "Combinaciones", "Con métricas", "Faltan"],
                        [[f"`{etapa}`", total, hechas, total - hechas] for etapa, (total, hechas, _) in por_etapa.items()]), ""]
    if 0 < len(faltan) <= 12:
        lineas += ["Faltan: " + ", ".join(f"`{n}`" for n in faltan) + ".", ""]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ principal
def main() -> None:
    inicio = time.time()
    s17 = cargar_script_17()
    par = cargar_parametros(s17)
    print("Comprobando la versión de las tablas...", flush=True)
    version = s17.comprobar_version()
    git = s17.estado_git()
    validas = combinaciones_validas(s17, par)
    carpeta = par["carpeta_predicciones"]
    archivos = sorted(carpeta.glob("*.parquet")) if carpeta.exists() else []
    if not archivos:
        raise SystemExit(f"No hay predicciones en {carpeta}: primero va el script 17.")
    ajenas = [a.name for a in archivos if a.name not in validas]
    if ajenas:
        raise SystemExit(f"Hay tablas de predicciones que no son combinaciones de D64 con la ponderación decidida: {ajenas}.")
    par["carpeta_metricas"].mkdir(parents=True, exist_ok=True)
    huella_script = sha256(Path(__file__))
    tareas = []
    parametros = {k: par[k] for k in ["semilla", "sorteos", "p_min"]}
    for a in archivos:
        salida = par["carpeta_metricas"] / a.name
        huella = sha256(a)
        if not vigente(salida, huella, huella_script, par, version["version"]):
            tareas.append({"prediccion": str(a), "salida": str(salida), "huella": huella, "huella_script": huella_script,
                           "combinacion": validas[a.name], "casos": str(CASOS), "parametros": parametros,
                           "version": version["version"], "commit": git[0]})
    print(f"{len(archivos)} tablas de predicciones; {len(tareas)} sin métricas al día. Hasta {par['procesadores']} a la vez.",
          flush=True)
    fallidas = []
    if tareas:
        with ProcessPoolExecutor(max_workers=min(par["procesadores"], len(tareas))) as procesos:
            futuros = [procesos.submit(calcular_combinacion, t) for t in tareas]
            for i, f in enumerate(as_completed(futuros), 1):
                r = f.result()
                estado = "guardada" if r["guardada"] else "NO SE GUARDÓ (falló una verificación)"
                print(f"[{i}/{len(tareas)}] {r['nombre'].removesuffix('.parquet')}: {estado}", flush=True)
                if not r["guardada"]:
                    fallidas.append(r)

    res = {}
    for a in archivos:
        salida = par["carpeta_metricas"] / a.name
        if salida.exists() and vigente(salida, sha256(a), huella_script, par, version["version"]):
            t = pq.read_table(salida)
            res[a.name] = (t.to_pandas().sort_values("sorteo").reset_index(drop=True),
                           {k.decode(): x.decode() for k, x in t.schema.metadata.items()})
    filas_comp, ensayo = comparaciones(s17, par, res)

    verificaciones = [("Todas las tablas de predicciones son combinaciones de D64 con la ponderación decidida", True)]
    for clave, texto in TEXTOS_VERIFICACION.items():
        malas = [n for n, (_, meta) in res.items() if not json.loads(meta["verificaciones"]).get(clave, False)]
        malas += [r["nombre"] for r in fallidas if not r["verificaciones"].get(clave, True)]
        verificaciones.append((f"{texto} ({len(res)} combinaciones" + (f"; fallan: {', '.join(sorted(set(malas)))})" if malas else ")"),
                               not malas))
    huellas = {(meta["huella_pacientes"], meta["huella_sorteo_1"], meta["semilla"], meta["sorteos"]) for _, meta in res.values()}
    verificaciones.append(("Todas las combinaciones usan los mismos pacientes y los mismos sorteos (huella de la lista de pacientes y del primer sorteo)",
                           len(huellas) <= 1))
    malos_pares = [f"{f['pares'][0]} y {f['pares'][1]}" for f in filas_comp
                   if res[f["pares"][0]][1]["casos"] != res[f["pares"][1]][1]["casos"]]
    verificaciones.append(("Cada comparación junta dos combinaciones con los mismos casos", not malos_pares))
    if par["ensayo_resuelto"] and len(ensayo) == len(par["modelos"]):
        distintos = [m for m, e in ensayo.items() if (e["veredicto"] == "Ponderar") != par["ponderar"][m]]
        verificaciones.append(("La ponderación fijada en reglas/parametros.csv coincide con el veredicto del ensayo (D61)"
                               + (f" (no coincide en {', '.join(distintos)})" if distintos else ""), not distintos))
    if fallidas:
        verificaciones.append((f"Combinaciones que no se guardaron por fallar una verificación: "
                               f"{', '.join(r['nombre'].removesuffix('.parquet') for r in fallidas)}", False))
    escribir_csv(res, filas_comp, par)
    escribir_reporte(s17, par, version, git, res, verificaciones, filas_comp, ensayo, validas, time.time() - inicio)
    if not all(ok for _, ok in verificaciones):
        raise SystemExit(f"Falló una verificación: revise {REPORTE}.")
    print(f"Listo en {(time.time() - inicio) / 60:.1f} minutos. Reporte: {REPORTE}", flush=True)


if __name__ == "__main__":
    main()
