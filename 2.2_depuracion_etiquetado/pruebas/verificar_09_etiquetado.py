"""Contraste independiente del script 09 (etiquetado del reingreso).

Vuelve a calcular las cuatro variables objetivo de data/processed/grd_etiquetado.parquet de dos formas
que no usan ninguna función del script 09: (a) un recorrido caso por caso sobre todos los casos de
estudio y (b) la unión literal de cada alta con los ingresos posteriores de la misma persona, en una
muestra de personas. También recalcula la verificación de la censura, comprueba que los casos sin
dato en las variables relacionadas (CDM de `cdm_sin_relacionado`, D38) habrían tenido 0 y compara las
cifras con las tablas del reporte 09. Solo lee.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\pruebas\\verificar_09_etiquetado.py

Para contrastar otros archivos se indican sus rutas y, si se quiere comparar, la del reporte:
    ... verificar_09_etiquetado.py <grd_etiquetado.parquet> <grd_depurado.parquet> [<09_etiquetado.md>]

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
ETIQUETADA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "data" / "processed" / "grd_etiquetado.parquet"
DEPURADA = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "data" / "processed" / "grd_depurado.parquet"
REPORTE = Path(sys.argv[3]) if len(sys.argv) > 3 else (None if len(sys.argv) > 1 else ACTIVIDAD / "reportes" / "09_etiquetado.md")
CIERRE = {"A": pd.Timestamp("2020-12-31"), "B": pd.Timestamp("2024-12-31")}
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
VENTANA = {"REING_7D": 7, "REING_7D_CDM": 7, "REING_30D": 30, "REING_30D_CDM": 30}
TRAMOS_CIERRE = [(7, 13), (14, 20), (21, 29), (30, 36), (37, 59), (60, 89), (90, 120)]     # los de la sección 6 del reporte
MUESTRA = 25                                     # la unión literal se hace en 1 de cada 25 identificadores
inicio = time.time()
todo_bien = True


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    global todo_bien
    todo_bien &= bool(cumple)
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


def lista(valor: str) -> tuple:
    return tuple(v.strip() for v in valor.split("|") if v.strip())


with open(ACTIVIDAD / "reglas" / "parametros.csv", encoding="utf-8-sig", newline="") as f:
    par = {r["parametro"]: r["valor"] for r in csv.DictReader(f, delimiter=";")}
# CDM agrupadas: cada CDM de un grupo se reemplaza por la primera del grupo antes de comparar.
agrupadas = {c: g.split("+")[0] for g in lista(par["cdm_agrupadas"]) for c in g.split("+")}
solo_no_planificado = par["reingreso_solo_no_planificado"].strip().upper() == "SI"
# CDM cuyos casos quedan sin dato en las variables relacionadas (D38), salvo que cdm_agrupadas las una con otra
# o que cuente todo ingreso (entonces un parto también es reingreso).
sin_relacionado = [x for x in lista(par["cdm_sin_relacionado"]) if x not in agrupadas] if solo_no_planificado else []
margen = int(par["censura_margen_dias"])
sesiones, no_planificados, partos = lista(par["diagnosticos_sesion"]), lista(par["ingresos_no_planificados"]), lista(par["grd_parto"])
print(f"Archivo: {ETIQUETADA}", flush=True)

# ------------------------------------------------------------------ 1. columnas de la tabla depurada
de_depurada, de_etiquetada = pq.read_schema(DEPURADA).names, pq.read_schema(ETIQUETADA).names
comprobar("Las columnas de la tabla depurada están al comienzo y en el mismo orden", de_etiquetada[:len(de_depurada)] == de_depurada,
          f"({len(de_depurada)} + {len(de_etiquetada) - len(de_depurada)} nuevas)")
distintas = [c for c in de_depurada if not pq.read_table(DEPURADA, columns=[c]).column(0).equals(pq.read_table(ETIQUETADA, columns=[c]).column(0))]
comprobar(f"Las {len(de_depurada)} columnas de la tabla depurada son idénticas celda a celda", not distintas, str(distintas[:5]) if distintas else "")
nuevas = de_etiquetada[len(de_depurada):]
comprobar("Las columnas nuevas son las esperadas", nuevas == VARIABLES + ["DIAS_REING", "ID_EGRESO_REING"], str(nuevas))

columnas = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO", "TIPO_INGRESO",
            "FECHA_INGRESO", "FECHAALTA", "IR_29301_COD_GRD", "CDM", "DIAGNOSTICO1"]
d = pd.read_parquet(ETIQUETADA, columns=columnas + nuevas)
caso = d["ES_CASO_ESTUDIO"].to_numpy()
al_cierre = (d["BLOQUE_ID"].map(CIERRE) - d["FECHAALTA"]).dt.days
for k in VARIABLES:
    esperado = caso & (al_cierre >= VENTANA[k] + margen).to_numpy()
    if k.endswith("_CDM"):
        esperado &= ~d["CDM"].isin(sin_relacionado).to_numpy()
    comprobar(f"{k}: con dato solo en los casos de estudio con al menos {VENTANA[k] + margen} días antes del cierre"
              + (f", sin los de la CDM {' y '.join(sin_relacionado)}" if k.endswith("_CDM") and sin_relacionado else "") + "; valores 0 o 1",
              (d[k].notna().to_numpy() == esperado).all() and d[k].dropna().isin([0, 1]).all(), f"(con dato {int(esperado.sum())})")
comprobar("DIAS_REING e ID_EGRESO_REING: sin dato fuera de los casos de estudio", d.loc[~caso, ["DIAS_REING", "ID_EGRESO_REING"]].isna().all().all())

# ------------------------------------------------------------------ 2. recorrido caso por caso
ingresos = d[d["PUEDE_SER_REINGRESO"]].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
persona = ingresos["ID_PERSONA"].to_numpy(dtype="int64").tolist()
dia_ingreso = ingresos["FECHA_INGRESO"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
egreso = ingresos["ID_EGRESO"].to_numpy().tolist()
cdm = [agrupadas.get(x, x) for x in ingresos["CDM"].fillna("").tolist()]
# No planificado: tipo de ingreso no programado, que no sea parto (por GRD) ni sesión de tratamiento (por diagnóstico principal).
cuenta = [(t in no_planificados and not g.startswith(partos) and not (bool(sesiones) and x.startswith(sesiones))) if solo_no_planificado else True
          for t, g, x in zip(ingresos["TIPO_INGRESO"].fillna("").tolist(), ingresos["IR_29301_COD_GRD"].fillna("").tolist(),
                             ingresos["DIAGNOSTICO1"].fillna("").tolist())]
posicion = {e: i for i, e in enumerate(egreso)}
n = len(egreso)
c = d[caso]
episodio_caso = c["ID_EPISODIO"].to_numpy(dtype="int64").tolist()
alta_caso = c["FECHAALTA"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
cdm_caso = [agrupadas.get(x, x) for x in c["CDM"].fillna("").tolist()]
nc = len(c)
calculado = np.zeros((nc, 4), dtype="int8")      # en el orden de VARIABLES
dias_primero, id_primero = np.full(nc, -1, dtype="int64"), np.zeros(nc, dtype="int64")
for i in range(nc):
    p = posicion[episodio_caso[i]]
    j = p + 1
    while j < n and persona[j] == persona[p]:
        dias = dia_ingreso[j] - alta_caso[i]
        if cuenta[j]:
            if dias_primero[i] < 0:
                dias_primero[i], id_primero[i] = dias, egreso[j]
            if dias <= 30:
                relacionado = cdm[j] == cdm_caso[i] and cdm[j] not in ("", "99")
                calculado[i, 2] = 1
                if relacionado:
                    calculado[i, 3] = 1
                if dias <= 7:
                    calculado[i, 0] = 1
                    if relacionado:
                        calculado[i, 1] = 1
        if dias > 30 and dias_primero[i] >= 0:
            break
        j += 1
con_dato = {k: c[k].notna().to_numpy() for k in VARIABLES}
cifras = {}
for i, k in enumerate(VARIABLES):
    v = con_dato[k]
    real = c[k].to_numpy(dtype="float64", na_value=np.nan)[v].astype("int8")
    cifras[k] = (int(v.sum()), int(calculado[v, i].sum()))
    comprobar(f"Recorrido caso por caso: {k}", (real == calculado[v, i]).all(),
              f"(casos {cifras[k][0]}; con reingreso {cifras[k][1]}; diferencias {int((real != calculado[v, i]).sum())})")
if sin_relacionado:
    excluido = c["CDM"].isin(sin_relacionado).to_numpy()
    comprobar(f"Recorrido caso por caso: los casos de la CDM {' y '.join(sin_relacionado)}, sin dato en las relacionadas, no tienen "
              "ningún reingreso de su misma CDM (el 0 era obligatorio)", int(calculado[excluido][:, [1, 3]].sum()) == 0,
              f"(casos {int(excluido.sum())})")
comprobar("Recorrido caso por caso: DIAS_REING e ID_EGRESO_REING",
          (c["DIAS_REING"].fillna(-1).to_numpy(dtype="int64") == dias_primero).all() and (c["ID_EGRESO_REING"].fillna(0).to_numpy(dtype="int64") == id_primero).all(),
          f"(casos con algún reingreso posterior: {int((dias_primero >= 0).sum())})")

# ------------------------------------------------------------------ 3. unión literal, en una muestra de personas
en_muestra = ((d["ID_PERSONA"] // 100) % MUESTRA == 3).fillna(False).to_numpy()
casos_m = d[en_muestra & caso][["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "FECHAALTA", "CDM"] + VARIABLES]
ingresos_m = d[en_muestra & d["PUEDE_SER_REINGRESO"].to_numpy()][["ID_PERSONA", "ID_EPISODIO", "FECHA_INGRESO", "CDM", "TIPO_INGRESO", "IR_29301_COD_GRD", "DIAGNOSTICO1"]]
pares = casos_m[["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "FECHAALTA", "CDM"]].merge(ingresos_m, on="ID_PERSONA", suffixes=("_C", "_I"))
pares = pares[(pares["ID_EPISODIO_C"] != pares["ID_EPISODIO_I"]) & (pares["FECHA_INGRESO"] >= pares["FECHAALTA"])]
pares["DIAS"] = (pares["FECHA_INGRESO"] - pares["FECHAALTA"]).dt.days
no_planificado = (pares["TIPO_INGRESO"].isin(list(no_planificados))
                  & ~pares["IR_29301_COD_GRD"].fillna("").str.match("(?:" + "|".join(partos) + ")" if partos else "(?!)")
                  & ~pares["DIAGNOSTICO1"].fillna("").str.match("(?:" + "|".join(sesiones) + ")" if sesiones else "(?!)"))
vale = no_planificado if solo_no_planificado else pd.Series(True, index=pares.index)
misma_cdm = (pares["CDM_C"].replace(agrupadas) == pares["CDM_I"].replace(agrupadas)) & (pares["CDM_I"] != "99")
union = {}
for v in (7, 30):
    dentro = vale & (pares["DIAS"] <= v)
    union[f"REING_{v}D"] = set(pares.loc[dentro, "ID_EGRESO"])
    union[f"REING_{v}D_CDM"] = set(pares.loc[dentro & misma_cdm, "ID_EGRESO"])
for k in VARIABLES:
    con = set(casos_m.loc[casos_m[k].notna(), "ID_EGRESO"])
    real, esperado = set(casos_m.loc[casos_m[k] == 1, "ID_EGRESO"]), union[k] & con
    comprobar(f"Unión literal en la muestra: {k}", real == esperado,
              f"(casos {len(con)}; con reingreso {len(real)}; solo en el archivo {len(real - esperado)}; solo en la unión {len(esperado - real)})")

# ------------------------------------------------------------------ 4. verificación de la censura
# En los años cuyo año siguiente está en la base con el mismo identificador: reingresos que terminan después del 31 de diciembre.
anio_alta = c["FECHAALTA"].dt.year.to_numpy()
interior = anio_alta < c["BLOQUE_ID"].map({b: f.year for b, f in CIERRE.items()}).to_numpy()
fin_anio = pd.to_datetime(pd.DataFrame({"year": anio_alta, "month": 12, "day": 31})).to_numpy()
al_fin = (fin_anio - c["FECHAALTA"].to_numpy()) / np.timedelta64(1, "D")
alta_reingreso = pd.Series(id_primero).map(d.set_index("ID_EGRESO")["FECHAALTA"]).to_numpy()
termina_despues = (dias_primero >= 0) & (alta_reingreso > fin_anio)
censura = {}
for a, b in TRAMOS_CIERRE:
    tramo = interior & (al_fin >= a) & (al_fin <= b)
    fila = [int(tramo.sum())]
    for v in (7, 30):
        reingresa = tramo & (dias_primero >= 0) & (dias_primero <= v)
        fila += [int(reingresa.sum()), round(100 * (reingresa & termina_despues).sum() / max(int(reingresa.sum()), 1), 1)] if a >= v else [None, None]
    censura[f"{a} a {b}"] = fila

# ------------------------------------------------------------------ 5. comparación con las tablas del reporte
if REPORTE is not None and REPORTE.exists():
    texto = REPORTE.read_text(encoding="utf-8")

    def entero(celda: str):
        return None if celda == "—" else int(celda.replace(".", ""))

    def porcentaje(celda: str):
        return None if celda == "—" else float(celda.replace(" %", "").replace(",", "."))

    del_reporte = {}
    for linea in texto.split("## 1.")[1].split("## 2.")[0].splitlines():
        m = re.match(r"\| `(REING_\w+)` \| .* \| ([\d.]+) \| ([\d.]+) \| [\d,]+ % \|$", linea)
        if m:
            del_reporte[m[1]] = (entero(m[2]), entero(m[3]))
    comprobar(f"La tabla de las cuatro variables de {REPORTE.name} coincide con el recorrido caso por caso", del_reporte == cifras,
              f"(reporte {del_reporte}; recalculado {cifras})" if del_reporte != cifras else "")
    censura_reporte = {}
    for linea in texto.split("## 6.")[1].split("## 7.")[0].splitlines():
        celdas = [x.strip() for x in linea.strip().strip("|").split("|")]
        if len(celdas) == 6 and re.fullmatch(r"\d+ a \d+", celdas[0]):
            censura_reporte[celdas[0]] = [entero(celdas[1]), entero(celdas[2]), porcentaje(celdas[3]), entero(celdas[4]), porcentaje(celdas[5])]
    comprobar(f"La tabla de verificación de la censura de {REPORTE.name} coincide con el recálculo", censura_reporte == censura,
              f"(reporte {censura_reporte}; recalculado {censura})" if censura_reporte != censura else f"({len(censura)} tramos)")

print("\nVariable: casos con dato, con reingreso, tasa")
for k in VARIABLES:
    print(f"  {k:14} {cifras[k][0]:>9} {cifras[k][1]:>8} {100 * cifras[k][1] / cifras[k][0]:.3f} %")
print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
sys.exit(0 if todo_bien else 1)
