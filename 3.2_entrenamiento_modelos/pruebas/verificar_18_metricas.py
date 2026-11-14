"""Prueba independiente de las métricas (actividad 3.2, script 18).

Revisa por otro camino lo que dejó el script 18: las tablas de métricas (el valor sin sorteo y los de cada sorteo), los
dos CSV y los veredictos. No usa las funciones del script 18: las áreas y el Brier se recalculan con las funciones de
scikit-learn, la calibración con scipy (buscando el máximo de la verosimilitud, no con el método de Newton del script), los
sorteos con la receta de D63 escrita aquí y los veredictos con una segunda transcripción de las reglas de D61 y D64.

  1. Versión y parámetros. Las tablas para los modelos son la versión registrada, y los parámetros del script 18 (sorteos,
     confianza, probabilidad mínima del logit y márgenes) y la semilla coinciden con una segunda transcripción.
  2. Tablas de métricas. Hay una por cada tabla de predicciones, hecha con esa misma tabla (misma huella), con el valor sin
     sorteo y todos los sorteos, sin valores vacíos.
  3. Valores sin sorteo. La AUPRC, el AUROC, el Brier y la prevalencia, recalculados con scikit-learn uniendo las
     predicciones a modelos_casos; el intercepto y la pendiente, en general y por año, recalculados con scipy y la regla de
     los 0 escrita aquí; los casos con 0 y sus reingresos, recontados.
  4. Sorteos. En cada combinación se rehacen desde cero el primer sorteo y el último, y se recalculan con pesos las
     métricas: deben ser las guardadas. Como la receta es la misma para todas, esto muestra además que todas usan los
     mismos sorteos. En una combinación de cada modelo se revisa también la calibración por año de esos sorteos.
  5. CSV de métricas. Cada valor e intervalo de 18_metricas.csv coincide con el recalculado aquí desde las tablas de
     métricas (percentiles 2,5 y 97,5 de los sorteos) o desde las predicciones (cada vuelta y cada año).
  6. Comparaciones. Están todas las comparaciones posibles, y sus valores, intervalos y veredictos coinciden con los
     recalculados aquí sorteo por sorteo.

Solo lee; con las rutas por defecto deja reportes/pruebas_metricas.md.

Uso (desde la carpeta Codigo; en el servidor, con el Python del entorno de D65), después del script 18:
    python 3.2_entrenamiento_modelos/pruebas/verificar_18_metricas.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import brentq, minimize
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DATOS = RAIZ / "data" / "processed"
CASOS = DATOS / "modelos_casos.parquet"
CODIGOS = DATOS / "modelos_codigos.parquet"
LISTAS = DATOS / "listas_codigos.parquet"
REGISTRO_TABLAS = RAIZ / "docs" / "version_tablas_modelos.csv"
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"
CSV_METRICAS = ACTIVIDAD / "reportes" / "18_metricas.csv"
CSV_COMPARACIONES = ACTIVIDAD / "reportes" / "18_comparaciones.csv"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_metricas.md"

# Segunda transcripción de D41, D61, D63, D64 y D67 (no se lee del script)
SEMILLA = 2026
SORTEOS = 1000
VALORES = {"sorteos": "1000", "confianza": "95", "probabilidad_minima_logit": "0,0001", "margen_auroc": "0,02",
           "margen_auprc": "0,1", "margen_ponderacion": "0,1"}
P_MIN = 0.0001
MARGEN_AUROC, MARGEN_AUPRC, MARGEN_PONDERACION = 0.02, 0.10, 0.10
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
MODELOS = ["LR", "RF", "XGB"]
VARIABLE_ENSAYO = "REING_7D_CDM"
OTRAS = ["SIN_FILTRO", "AGRUPADA", "C"]
TOL_AREAS, TOL_CALIBRACION, TOL_CSV = 1e-9, 1e-5, 6e-7
resultados = []


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    resultados.append((f"{nombre} {detalle}".rstrip(), bool(cumple)))
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def resumen(malas: list[str]) -> str:
    malas = sorted(set(malas))
    return "ninguna" if not malas else f"{len(malas)}, por ejemplo {malas[0]}"


def nombre(v, m, lista, hospital, ponderado) -> str:
    return f"{v}__{m}__{lista}__{'con' if hospital else 'sin'}_hospital__{'ponderado' if ponderado else 'sin_ponderar'}.parquet"


def logit_regla(p: np.ndarray) -> np.ndarray:
    """D67, escrito de nuevo: solo los 0 y los 1 exactos cambian."""
    q = p.copy()
    q[p == 0] = P_MIN
    q[p == 1] = 1 - P_MIN
    return np.log(q) - np.log1p(-q)


def intercepto_scipy(y, lp, w) -> float:
    """El a que anula la derivada de la verosimilitud con el logit como offset, buscado con el método de Brent."""
    f = lambda a: np.sum(w * (y - 1 / (1 + np.exp(-(a + lp))))) / np.sum(w)
    return brentq(f, -30, 30, xtol=1e-12)


def pendiente_scipy(y, lp, w) -> tuple[float, float]:
    """a y b que maximizan la verosimilitud de logit P = a + b · lp, con L-BFGS-B."""
    total = np.sum(w)

    def f(t):
        eta = t[0] + t[1] * lp
        vida = np.sum(w * (np.logaddexp(0, eta) - y * eta)) / total
        r = w * (1 / (1 + np.exp(-eta)) - y) / total
        return vida, np.array([r.sum(), (r * lp).sum()])
    s = minimize(f, x0=[0.0, 1.0], jac=True, method="L-BFGS-B", options={"gtol": 1e-12, "ftol": 1e-16, "maxiter": 10000})
    return float(s.x[0]), float(s.x[1])


def pesos_sorteo(b: int, n_pacientes: int, indice: np.ndarray) -> np.ndarray:
    """D63, escrito de nuevo: n_pacientes extracciones con reposición con numpy.random.default_rng([semilla, b])."""
    extraidos = np.random.default_rng([SEMILLA, b]).integers(0, n_pacientes, size=n_pacientes)
    cuenta = np.zeros(n_pacientes, dtype=np.int64)
    np.add.at(cuenta, extraidos, 1)
    return cuenta[indice].astype(np.float64)


def cuantiles(x: pd.Series) -> tuple[float, float]:
    q = x.quantile([0.025, 0.975])
    return float(q.iloc[0]), float(q.iloc[1])


def main() -> None:
    inicio = time.time()
    # ---------------------------------------------------------------- 1. versión y parámetros
    version = leer_csv(REGISTRO_TABLAS)[-1]
    iguales = all(sha256(r) == version[c] for r, c in [(CASOS, "sha256_casos"), (CODIGOS, "sha256_codigos"),
                                                       (LISTAS, "sha256_listas_codigos")])
    comprobar("Las tablas para los modelos son la versión registrada", iguales, f"(versión {version['version']})")
    par = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS)}
    p23 = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS_23)}
    distintos = [k for k, v in VALORES.items() if par.get(k) != v]
    comprobar("Los parámetros del script 18 coinciden con la segunda transcripción y la semilla es 2026", not distintos
              and p23.get("semilla") == str(SEMILLA), f"(distintos: {distintos or 'ninguno'})")
    ponderar = {m: par.get(f"ponderar_{m}") == "SI" for m in MODELOS}
    resuelto = par.get("ensayo_resuelto") == "SI"
    carpeta_pred = RAIZ / par["carpeta_predicciones"]
    carpeta_met = RAIZ / par["carpeta_metricas"]

    # ---------------------------------------------------------------- 2. tablas de métricas
    predicciones = {a.name: a for a in sorted(carpeta_pred.glob("*.parquet"))} if carpeta_pred.exists() else {}
    metricas = {a.name: a for a in sorted(carpeta_met.glob("*.parquet"))} if carpeta_met.exists() else {}
    comprobar("Hay tablas de métricas para revisar", len(metricas) > 0, f"({len(metricas)})")
    comprobar("Hay una tabla de métricas por cada tabla de predicciones, y ninguna de más", set(metricas) == set(predicciones),
              f"(sin métricas: {resumen(list(set(predicciones) - set(metricas)))}; de más: {resumen(list(set(metricas) - set(predicciones)))})")
    tablas, malas_huella, malas_filas = {}, [], []
    for n in sorted(set(metricas) & set(predicciones)):
        t = pq.read_table(metricas[n])
        meta = {k.decode(): x.decode() for k, x in (t.schema.metadata or {}).items()}
        df = t.to_pandas().sort_values("sorteo").reset_index(drop=True)
        tablas[n] = (df, meta)
        if meta.get("huella_predicciones") != sha256(predicciones[n]):
            malas_huella.append(n)
        columnas = [c for c in df.columns if c != "sorteo"]
        if df["sorteo"].tolist() != list(range(SORTEOS + 1)) or df[columnas].isna().any().any():
            malas_filas.append(n)
    comprobar("Cada tabla de métricas se hizo con la tabla de predicciones que hay ahora (misma huella)", not malas_huella,
              f"(distintas: {resumen(malas_huella)})")
    comprobar(f"Cada tabla de métricas tiene el valor sin sorteo y los {SORTEOS} sorteos, sin valores vacíos", not malas_filas,
              f"(distintas: {resumen(malas_filas)})")

    # ---------------------------------------------------------------- 3 y 4. valores sin sorteo y sorteos rehechos
    casos = pd.read_parquet(CASOS, columns=["ID_EGRESO", "ID_PACIENTE", "ANIO_ALTA", "PLIEGUE"] + VARIABLES)
    pacientes = np.sort(casos["ID_PACIENTE"].unique())
    anios = sorted(int(t) for t in casos["ANIO_ALTA"].unique())
    mal_areas, mal_conteo, mal_cal, mal_cal_anio, mal_sorteo, mal_sorteo_anio, recalculado = [], [], [], [], [], [], {}
    revisar_anios_sorteo = {}
    for n in tablas:
        revisar_anios_sorteo.setdefault(n.split("__")[1], n)  # la primera combinación de cada modelo
    for n, (df, meta) in tablas.items():
        v = n.split("__")[0]
        pred = pd.read_parquet(predicciones[n], columns=["ID_EGRESO", "PROBABILIDAD"])
        u = casos[casos[v].notna()].merge(pred, on="ID_EGRESO", how="inner")  # el pliegue y el año salen de modelos_casos
        y, p = u[v].to_numpy(dtype=float), u["PROBABILIDAD"].to_numpy()
        lp, anio = logit_regla(p), u["ANIO_ALTA"].to_numpy()
        cero = df.iloc[0]
        puntos = {"AUPRC": average_precision_score(y, p), "AUROC": roc_auc_score(y, p), "Brier": brier_score_loss(y, p),
                  "prevalencia": y.mean()}
        if any(abs(cero[k] - x) > TOL_AREAS for k, x in puntos.items()):
            mal_areas.append(n)
        if (int(meta["casos"]), int(meta["reingresos"]), int(meta["ceros"]), int(meta["reingresos_ceros"])) != \
                (len(y), int(y.sum()), int((p == 0).sum()), int(y[p == 0].sum())):
            mal_conteo.append(n)
        uno = np.ones(len(y))
        a_pend, b_pend = pendiente_scipy(y, lp, uno)
        if abs(cero["intercepto"] - intercepto_scipy(y, lp, uno)) > TOL_CALIBRACION or abs(cero["pendiente"] - b_pend) > TOL_CALIBRACION:
            mal_cal.append(n)
        for t in anios:
            k = anio == t
            if abs(cero[f"intercepto_{t}"] - intercepto_scipy(y[k], lp[k], uno[k])) > TOL_CALIBRACION or \
                    abs(cero[f"pendiente_{t}"] - pendiente_scipy(y[k], lp[k], uno[k])[1]) > TOL_CALIBRACION:
                mal_cal_anio.append(f"{n} ({t})")
        indice = np.searchsorted(pacientes, u["ID_PACIENTE"].to_numpy())
        for b in [1, SORTEOS]:
            w = pesos_sorteo(b, len(pacientes), indice)
            fila = df.iloc[b]
            esperado = {"AUPRC": average_precision_score(y, p, sample_weight=w), "AUROC": roc_auc_score(y, p, sample_weight=w),
                        "Brier": brier_score_loss(y, p, sample_weight=w), "prevalencia": np.average(y, weights=w)}
            if any(abs(fila[k] - x) > TOL_AREAS for k, x in esperado.items()) or \
                    abs(fila["intercepto"] - intercepto_scipy(y, lp, w)) > TOL_CALIBRACION or \
                    abs(fila["pendiente"] - pendiente_scipy(y, lp, w)[1]) > TOL_CALIBRACION:
                mal_sorteo.append(f"{n} (sorteo {b})")
            if revisar_anios_sorteo.get(n.split("__")[1]) == n:
                for t in anios:
                    k = anio == t
                    if abs(fila[f"intercepto_{t}"] - intercepto_scipy(y[k], lp[k], w[k])) > TOL_CALIBRACION or \
                            abs(fila[f"pendiente_{t}"] - pendiente_scipy(y[k], lp[k], w[k])[1]) > TOL_CALIBRACION:
                        mal_sorteo_anio.append(f"{n} (sorteo {b}, {t})")
        pliegue = u["PLIEGUE"].to_numpy()
        recalculado[n] = {"anio": {t: (y[anio == t].mean(), p[anio == t].mean()) for t in anios},
                          "vuelta": {int(k): (average_precision_score(y[pliegue == k], p[pliegue == k]),
                                              roc_auc_score(y[pliegue == k], p[pliegue == k])) for k in np.unique(pliegue)}}
        print(f"  revisada {n.removesuffix('.parquet')}", flush=True)
    comprobar("Sin sorteo, la AUPRC, el AUROC, el Brier y la prevalencia coinciden con scikit-learn sobre las predicciones unidas a modelos_casos",
              not mal_areas, f"({len(tablas)} combinaciones; distintas: {resumen(mal_areas)})")
    comprobar("Los casos, los reingresos, los casos con probabilidad 0 y sus reingresos coinciden con un recuento", not mal_conteo,
              f"(distintas: {resumen(mal_conteo)})")
    comprobar("Sin sorteo, el intercepto con offset y la pendiente coinciden con los calculados con scipy (y la regla de los 0 escrita aquí)",
              not mal_cal, f"(distintas: {resumen(mal_cal)})")
    comprobar("Sin sorteo, el intercepto y la pendiente de cada año coinciden con los calculados con scipy", not mal_cal_anio,
              f"(distintos: {resumen(mal_cal_anio)})")
    comprobar("El primer y el último sorteo, rehechos desde cero con la receta de D63, dan las métricas guardadas en todas las combinaciones (los mismos sorteos para todas)",
              not mal_sorteo, f"({2 * len(tablas)} sorteos; distintos: {resumen(mal_sorteo)})")
    comprobar("En una combinación de cada modelo, la calibración de cada año de esos sorteos coincide con scipy", not mal_sorteo_anio,
              f"({len(revisar_anios_sorteo)} combinaciones; distintos: {resumen(mal_sorteo_anio)})")

    # ---------------------------------------------------------------- 5. CSV de métricas
    csv_m = pd.read_csv(CSV_METRICAS, sep=";", decimal=",", encoding="utf-8-sig", dtype={"grupo": str})
    mal_csv, filas_esperadas = [], 0
    for n, (df, meta) in tablas.items():
        clave = (csv_m["variable"] == meta["variable"]) & (csv_m["modelo"] == meta["modelo"]) & (csv_m["lista"] == meta["lista"]) \
            & (csv_m["hospital"] == meta["hospital"]) & (csv_m["ponderacion"] == meta["ponderacion"])
        sub = csv_m[clave].set_index(["grupo", "metrica"])
        cero = df.iloc[0]
        esperado = {}
        for k in ["prevalencia", "AUPRC", "AUROC", "Brier", "intercepto", "pendiente"]:
            esperado[("TODOS", k)] = (cero[k], *cuantiles(df[k].iloc[1:]))
        esperado[("TODOS", "cociente_AUPRC_prevalencia")] = (cero["AUPRC"] / cero["prevalencia"], np.nan, np.nan)
        esperado[("TODOS", "Brier_referencia")] = (cero["prevalencia"] * (1 - cero["prevalencia"]), np.nan, np.nan)
        esperado[("TODOS", "casos_con_0")] = (float(meta["ceros"]), np.nan, np.nan)
        esperado[("TODOS", "reingresos_con_0")] = (float(meta["reingresos_ceros"]), np.nan, np.nan)
        for t in anios:
            for k in ["intercepto", "pendiente"]:
                esperado[(str(t), k)] = (cero[f"{k}_{t}"], *cuantiles(df[f"{k}_{t}"].iloc[1:]))
            esperado[(str(t), "observado")] = (recalculado[n]["anio"][t][0], np.nan, np.nan)
            esperado[(str(t), "predicho")] = (recalculado[n]["anio"][t][1], np.nan, np.nan)
        for k, (prc, roc) in recalculado[n]["vuelta"].items():
            esperado[(f"VUELTA_{k}", "AUPRC")] = (prc, np.nan, np.nan)
            esperado[(f"VUELTA_{k}", "AUROC")] = (roc, np.nan, np.nan)
        filas_esperadas += len(esperado)
        for clave_e, (valor, lo, hi) in esperado.items():
            if clave_e not in sub.index:
                mal_csv.append(f"{n} {clave_e}")
                continue
            fila = sub.loc[clave_e]
            for x, z in [(fila["valor"], valor), (fila["inferior"], lo), (fila["superior"], hi)]:
                if (np.isnan(z) and not pd.isna(x)) or (not np.isnan(z) and (pd.isna(x) or abs(x - z) > TOL_CSV)):
                    mal_csv.append(f"{n} {clave_e}")
                    break
    comprobar("Cada valor e intervalo de 18_metricas.csv coincide con el recalculado aquí (percentiles 2,5 y 97,5, cada año y cada vuelta)",
              not mal_csv and len(csv_m) == filas_esperadas, f"({len(csv_m)} filas, se esperaban {filas_esperadas}; distintas: {resumen(mal_csv)})")

    # ---------------------------------------------------------------- 6. comparaciones
    esperadas = {}
    for m in MODELOS:
        a, b = nombre(VARIABLE_ENSAYO, m, "A", True, False), nombre(VARIABLE_ENSAYO, m, "A", True, True)
        if a in tablas and b in tablas:
            sa, sb = tablas[a][0]["AUPRC"], tablas[b][0]["AUPRC"]
            mejora = (sb.iloc[1:] - sa.iloc[1:]) / sa.iloc[1:]
            lo, hi = cuantiles(mejora)
            esperadas[("ENSAYO", VARIABLE_ENSAYO, m, "ponderado", "mejora relativa de la AUPRC")] = (
                sb.iloc[0] / sa.iloc[0] - 1, lo, hi, "Ponderar" if lo > MARGEN_PONDERACION else "No ponderar")
    if resuelto:
        for v in VARIABLES:
            for m in MODELOS:
                a = nombre(v, m, "A", True, ponderar[m])
                pares = [("LISTA", o, nombre(v, m, o, True, ponderar[m]), a) for o in OTRAS] + \
                        [("SIN_HOSPITAL", "con hospital", a, nombre(v, m, "A", False, ponderar[m]))]
                for tipo, frente, grande, chica in pares:
                    if grande not in tablas or chica not in tablas:
                        continue
                    G, C = tablas[grande][0], tablas[chica][0]
                    prc = (G["AUPRC"] - C["AUPRC"]) / G["AUPRC"]
                    roc = G["AUROC"] - C["AUROC"]
                    (lp_, hp_), (lr_, hr_) = cuantiles(prc.iloc[1:]), cuantiles(roc.iloc[1:])
                    if lp_ > MARGEN_AUPRC or lr_ > MARGEN_AUROC:
                        ver = "Pierde"
                    elif hp_ <= MARGEN_AUPRC and hr_ <= MARGEN_AUROC:
                        ver = "No pierde"
                    else:
                        ver = "No se puede afirmar"
                    if tipo == "SIN_HOSPITAL":
                        ver += " (solo informa)"
                    esperadas[(tipo, v, m, frente, "caída relativa de la AUPRC")] = (prc.iloc[0], lp_, hp_, ver)
                    esperadas[(tipo, v, m, frente, "caída del AUROC")] = (roc.iloc[0], lr_, hr_, ver)
    csv_c = pd.read_csv(CSV_COMPARACIONES, sep=";", decimal=",", encoding="utf-8-sig", dtype=str)
    leidas = {}
    for _, f in csv_c.iterrows():
        leidas[(f["tipo"], f["variable"], f["modelo"], f["frente_a"], f["medida"])] = (
            float(f["valor"].replace(",", ".")), float(f["inferior"].replace(",", ".")), float(f["superior"].replace(",", ".")), f["veredicto"])
    comprobar("18_comparaciones.csv tiene exactamente las comparaciones posibles con las tablas de métricas (ensayo, listas y sin hospital)",
              set(leidas) == set(esperadas), f"({len(esperadas)} filas esperadas; faltan {len(set(esperadas) - set(leidas))}, sobran {len(set(leidas) - set(esperadas))})")
    malas_comp = [" / ".join(k[:4]) for k in set(leidas) & set(esperadas)
                  if any(abs(x - z) > TOL_CSV for x, z in zip(leidas[k][:3], esperadas[k][:3])) or leidas[k][3] != esperadas[k][3]]
    comprobar("Las caídas, la mejora del ensayo, sus intervalos y los veredictos coinciden con los recalculados aquí sorteo por sorteo",
              not malas_comp, f"(distintas: {resumen(malas_comp)})")

    # ---------------------------------------------------------------- reporte
    todo_bien = all(ok for _, ok in resultados)
    print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente de las métricas",
        f"Generado por `{ACTIVIDAD.name}/pruebas/verificar_18_metricas.py` el {date.today():%d-%m-%Y}. Revisa por otro camino lo que "
        "dejó el script 18: recalcula con scikit-learn las áreas y el Brier, con scipy la calibración, rehace desde cero el primer y "
        "el último sorteo de cada combinación con la receta de D63 y vuelve a calcular las comparaciones y sus veredictos con una "
        "segunda transcripción de las reglas de D61 y D64.",
        f"Tablas para los modelos: versión {version['version']}. Tablas de métricas revisadas: {len(tablas)}.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
