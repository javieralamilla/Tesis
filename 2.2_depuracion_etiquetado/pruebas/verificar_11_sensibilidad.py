"""Contraste independiente del script 11 (análisis de sensibilidad).

Vuelve a calcular cada escenario de la tabla de sensibilidad a partir de las columnas de
data/processed/grd_etiquetado.parquet, con recorridos simples (uno para armar los episodios y otro
para las variables objetivo) y sin usar ninguna función de los scripts 08, 09 ni 11. Compara los
casos de estudio y las cuatro tasas de cada escenario con la tabla del reporte 11. En las variables
relacionadas no cuentan las CDM de `cdm_sin_relacionado` (D38), salvo en los escenarios que las
vuelven a incluir. Solo lee.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\pruebas\\verificar_11_sensibilidad.py

Para contrastar otros archivos se indican sus rutas:
    ... verificar_11_sensibilidad.py <grd_etiquetado.parquet> <11_sensibilidad.md>

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
ETIQUETADA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "data" / "processed" / "grd_etiquetado.parquet"
REPORTE = Path(sys.argv[2]) if len(sys.argv) > 2 else ACTIVIDAD / "reportes" / "11_sensibilidad.md"
CIERRE = {"A": pd.Timestamp("2020-12-31"), "B": pd.Timestamp("2024-12-31")}
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
VENTANAS = [7, 7, 30, 30]                        # ventana de cada variable
inicio = time.time()
todo_bien = True


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    global todo_bien
    todo_bien &= bool(cumple)
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


def lista(valor: str) -> tuple:
    return tuple(v.strip() for v in valor.split("|") if v.strip())


with open(ACTIVIDAD / "reglas" / "criterios_exclusion.csv", encoding="utf-8-sig", newline="") as f:
    CRITERIOS = list(csv.DictReader(f, delimiter=";"))
with open(ACTIVIDAD / "reglas" / "parametros.csv", encoding="utf-8-sig", newline="") as f:
    par = {r["parametro"]: r["valor"] for r in csv.DictReader(f, delimiter=";")}
MARGEN = int(par["censura_margen_dias"])
SESIONES, NO_PLANIFICADOS, PARTOS = lista(par["diagnosticos_sesion"]), lista(par["ingresos_no_planificados"]), lista(par["grd_parto"])
# CDM de la sensibilidad: cada CDM de un grupo se reemplaza por la primera del grupo antes de comparar.
AGRUPADAS = {c: g.split("+")[0] for g in lista(par["cdm_sensibilidad"]) for c in g.split("+")}
# CDM cuyos casos quedan sin dato en las variables relacionadas (D38), salvo que la comparación las una con otra.
# Solo se aplica cuando cuentan solo los ingresos no planificados, que es lo que recalcula este contraste.
SIN_RELACIONADO = lista(par["cdm_sin_relacionado"]) if par["reingreso_solo_no_planificado"].strip().upper() == "SI" else ()
DIAS_TRASLADO, EXIGE_MARCA = int(par["traslado_dias_max"]), par["traslado_exige_marca"].strip().upper() == "SI"

columnas = ["ID_EGRESO", "BLOQUE_ID", "ID_PERSONA", "COD_HOSPITAL", "TIPO_PROCEDENCIA", "TIPO_INGRESO", "FECHA_INGRESO", "FECHAALTA", "TIPOALTA",
            "IR_29301_COD_GRD", "CDM", "DIAGNOSTICO1", "IDENTIDAD_AMBIGUA"]
d = pd.read_parquet(ETIQUETADA, columns=columnas + [c["columna"] for c in CRITERIOS]).reset_index(drop=True)
N = len(d)
al_cierre = (d["BLOQUE_ID"].map(CIERRE) - d["FECHAALTA"]).dt.days.to_numpy()      # sin dato si falta la fecha de alta
print(f"Archivo: {ETIQUETADA} ({N} egresos)", flush=True)


def armar_episodios(seguible: np.ndarray, exige_marca: bool = EXIGE_MARCA) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Recorrido egreso por egreso: episodio de cada egreso, si continúa el anterior y si es el alta final."""
    s = d[seguible].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    personas = s["ID_PERSONA"].to_numpy(dtype="int64").tolist()
    ingresos = s["FECHA_INGRESO"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
    altas = s["FECHAALTA"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
    hospitales = pd.factorize(s["COD_HOSPITAL"])[0].tolist()
    egresos = s["ID_EGRESO"].to_numpy().tolist()
    derivado = s["TIPOALTA"].fillna("").str.startswith("DERIVACIÓN").tolist()
    viene_de_hospital = s["TIPO_PROCEDENCIA"].fillna("").str.startswith("OTROS HOSPITALES").tolist()
    n = len(s)
    episodio, continua, ultimo = np.empty(n, dtype="int64"), np.zeros(n, dtype=bool), {}
    persona_anterior = alta_mayor = hospital_ref = ingreso_ref = derivado_ref = episodio_actual = None
    for k in range(n):
        persona, ing, alt, hosp = personas[k], ingresos[k], altas[k], hospitales[k]
        sigue = False
        if persona == persona_anterior:
            dias = ing - alta_mayor
            if dias < 0:
                sigue = True
            elif dias <= DIAS_TRASLADO and hosp != hospital_ref and (not exige_marca or derivado_ref or viene_de_hospital[k]):
                sigue = True
            elif dias == 0 and hosp == hospital_ref and ing == ingreso_ref and alt == alta_mayor:
                sigue = True
        if sigue:
            continua[k] = True
        else:
            episodio_actual = egresos[k]
            if persona != persona_anterior:
                alta_mayor = None
        episodio[k] = episodio_actual
        orden = (alt, ing, egresos[k])
        if episodio_actual not in ultimo or orden > ultimo[episodio_actual][0]:
            ultimo[episodio_actual] = (orden, k)
        if alta_mayor is None or alt >= alta_mayor:
            alta_mayor, hospital_ref, ingreso_ref, derivado_ref = alt, hosp, ing, derivado[k]
        persona_anterior = persona
    final = np.zeros(n, dtype=bool)
    final[[v[1] for v in ultimo.values()]] = True
    fila = s.index.to_numpy()
    episodio_t, continua_t, final_t = np.zeros(N, dtype="int64"), np.zeros(N, dtype=bool), np.zeros(N, dtype=bool)
    episodio_t[fila], continua_t[fila], final_t[fila] = episodio, continua, final
    return episodio_t, continua_t, final_t


def etiquetar(caso: np.ndarray, puede: np.ndarray, episodio: np.ndarray, margen: int) -> tuple[np.ndarray, dict]:
    """Recorrido caso por caso. Columnas: las cuatro variables y las dos relacionadas con las CDM agrupadas."""
    ingresos = d[puede].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    persona = ingresos["ID_PERSONA"].to_numpy(dtype="int64").tolist()
    dia_ingreso = ingresos["FECHA_INGRESO"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
    egreso = ingresos["ID_EGRESO"].to_numpy().tolist()
    cdm = ingresos["CDM"].fillna("").tolist()
    cdm_agrupada = [AGRUPADAS.get(x, x) for x in cdm]
    cuenta = [t in NO_PLANIFICADOS and not g.startswith(PARTOS) and not (bool(SESIONES) and x.startswith(SESIONES))
              for t, g, x in zip(ingresos["TIPO_INGRESO"].fillna("").tolist(), ingresos["IR_29301_COD_GRD"].fillna("").tolist(),
                                 ingresos["DIAGNOSTICO1"].fillna("").tolist())]
    posicion = {e: i for i, e in enumerate(egreso)}
    n = len(egreso)
    c = d[caso]
    episodio_caso = episodio[caso].tolist()
    alta_caso = c["FECHAALTA"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
    cdm_caso = c["CDM"].fillna("").tolist()
    cdm_caso_agrupada = [AGRUPADAS.get(x, x) for x in cdm_caso]
    resultado = np.zeros((len(c), 6), dtype="int8")
    for i in range(len(c)):
        p = posicion[episodio_caso[i]]
        j = p + 1
        while j < n and persona[j] == persona[p]:
            dias = dia_ingreso[j] - alta_caso[i]
            if dias > 30:
                break
            if cuenta[j]:
                relacionado = cdm[j] == cdm_caso[i] and cdm[j] not in ("", "99")
                relacionado_agrupada = cdm_agrupada[j] == cdm_caso_agrupada[i] and cdm_agrupada[j] not in ("", "99")
                resultado[i, 2] = 1
                if relacionado:
                    resultado[i, 3] = 1
                if relacionado_agrupada:
                    resultado[i, 5] = 1
                if dias <= 7:
                    resultado[i, 0] = 1
                    if relacionado:
                        resultado[i, 1] = 1
                    if relacionado_agrupada:
                        resultado[i, 4] = 1
            j += 1
    con_dato = {v: al_cierre[caso] >= v + margen for v in (7, 30)}
    return resultado, con_dato


def escenario(nombre: str, cambios: dict | None = None, margen: int = MARGEN, episodios=None, exige_marca: bool = EXIGE_MARCA) -> dict:
    """cambios: código de criterio -> activo. episodios: los del análisis principal, si el escenario no los cambia."""
    activo = {c["codigo"]: c["activo"].strip().upper() == "SI" for c in CRITERIOS}
    activo.update(cambios or {})
    seguible = d["ID_PERSONA"].notna().to_numpy() & ~d["EXC_FECHAS"].to_numpy()
    for c in CRITERIOS:
        if c["papel"] == "AMBOS" and activo[c["codigo"]]:
            seguible &= ~d[c["columna"]].to_numpy()
    episodio, continua, final = episodios if episodios is not None else armar_episodios(seguible, exige_marca)
    caso = np.ones(N, dtype=bool)
    for c in CRITERIOS:
        if not activo[c["codigo"]]:
            continue
        if c["codigo"] == "E05":                                  # tramo de un traslado: depende de los episodios del escenario
            cumple = seguible & ~final
        elif c["codigo"] == "E11":                                # censura: depende del margen del escenario
            cumple = np.nan_to_num(al_cierre, nan=np.inf) < min(VENTANAS) + margen
        else:
            cumple = d[c["columna"]].to_numpy()
        caso &= ~cumple
    resultado, con_dato = etiquetar(caso, seguible & ~continua, episodio, margen)
    print(f"  {nombre}: {int(caso.sum())} casos de estudio ({time.time() - inicio:.0f} s)", flush=True)
    return {"caso": caso, "resultado": resultado, "con_dato": con_dato, "episodios": (episodio, continua, final)}


def cifras(e: dict, columnas_resultado=(0, 1, 2, 3), filtro=None, sin_relacionado=SIN_RELACIONADO) -> tuple[int, list[float]]:
    """Casos de estudio y tasa (en %, con dos decimales) de cada variable. En las relacionadas no cuentan los
    casos de estudio de las CDM de `sin_relacionado`, que quedan sin dato (D38)."""
    filtro = np.ones(int(e["caso"].sum()), dtype=bool) if filtro is None else filtro
    excluido = d.loc[e["caso"], "CDM"].isin(list(sin_relacionado)).to_numpy()
    tasas = []
    for variable, columna, ventana in zip(VARIABLES, columnas_resultado, VENTANAS):
        v = e["con_dato"][ventana] & filtro
        if variable.endswith("_CDM"):
            v = v & ~excluido
        tasas.append(round(100 * int(e["resultado"][v, columna].sum()) / int(v.sum()), 2))
    return int(filtro.sum()), tasas


print("Recalculando los escenarios...", flush=True)
principal = escenario("Análisis principal")
esperado = {"Análisis principal": cifras(principal),
            "Con los partos en las variables relacionadas": cifras(principal, sin_relacionado=()),
            # Al unir las CDM, la que la unión agrupa con otra vuelve a tener dato.
            "Con las CDM": cifras(principal, (0, 4, 2, 5), sin_relacionado=[x for x in SIN_RELACIONADO if x not in AGRUPADAS]),
            "Sin los casos con identidad ambigua": cifras(principal, filtro=~d.loc[principal["caso"], "IDENTIDAD_AMBIGUA"].to_numpy()),
            "Con la cirugía mayor ambulatoria": cifras(escenario("Con la cirugía mayor ambulatoria", {"E13": False}, episodios=principal["episodios"])),
            "Con las sesiones de tratamiento": cifras(escenario("Con las sesiones de tratamiento", {"E14": False}, episodios=principal["episodios"])),
            "Censura sin margen": cifras(escenario("Censura sin margen", margen=0, episodios=principal["episodios"])),
            "Solo los traslados con marca explícita": cifras(escenario("Solo los traslados con marca explícita", exige_marca=True)),
            "Con los derivados sin continuación como casos de estudio": cifras(escenario("Con los derivados", {"E07": False, "E08": False},
                                                                                      episodios=principal["episodios"])),
            "Con las actividades que solo existen en 2019": cifras(escenario("Con las actividades de 2019", {"E04": False}))}

# ------------------------------------------------------------------ comparación con la tabla del reporte
del_reporte = {}
for linea in REPORTE.read_text(encoding="utf-8").split("## 1.")[1].split("## 2.")[0].splitlines():
    celdas = [x.strip() for x in linea.strip().strip("|").split("|")]
    if len(celdas) == 7 and re.fullmatch(r"[\d.]+", celdas[2]):
        del_reporte[celdas[0]] = (int(celdas[2].replace(".", "")), [float(re.match(r"([\d,]+) %", x).group(1).replace(",", ".")) for x in celdas[3:]])
for clave, (casos, tasas) in esperado.items():
    fila = next((v for k, v in del_reporte.items() if k.startswith(clave)), None)
    if fila is None:
        comprobar(f"El escenario «{clave}» está en la tabla de {REPORTE.name}", False)
        continue
    comprobar(f"{clave}: casos de estudio y las cuatro tasas iguales a los de {REPORTE.name}",
              fila[0] == casos and all(abs(x - y) < 0.0051 for x, y in zip(fila[1], tasas)), f"({casos} casos; tasas {tasas})")
comprobar("Todas las filas de la tabla del reporte fueron contrastadas", len(del_reporte) == len(esperado), f"({len(del_reporte)} filas)")

print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
sys.exit(0 if todo_bien else 1)
