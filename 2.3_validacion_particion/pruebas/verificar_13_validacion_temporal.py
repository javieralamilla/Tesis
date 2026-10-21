"""Contraste independiente del script 13 (grupos de la validación temporal).

Vuelve a calcular, sin usar ninguna función del script 13 y con otro camino, el período de cada caso
de estudio de desarrollo y si el paciente ya fue visto: el año se toma de la fecha de alta (no del
año del archivo) y los pacientes ya vistos se obtienen agrupando por identificador con pyarrow.
Compara el resultado con data/processed/validacion_temporal.parquet y con la tabla del reporte 13.
Solo lee el conjunto de desarrollo; con las rutas por defecto deja
reportes/pruebas_validacion_temporal.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.3_validacion_particion\\pruebas\\verificar_13_validacion_temporal.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import re
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
GRUPOS = RAIZ / "data" / "processed" / "validacion_temporal.parquet"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
REPORTE_13 = ACTIVIDAD / "reportes" / "13_validacion_temporal.md"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_validacion_temporal.md"
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
inicio = time.time()
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


par = {r["parametro"]: r["valor"].strip() for r in leer_csv(ACTIVIDAD / "reglas" / "parametros.csv")}
ENTRENA = [int(a) for a in par["anios_entrenamiento_temporal"].split("|")]
EVALUA = [int(a) for a in par["anios_evaluacion_temporal"].split("|")]
SOLO_CASOS = par["paciente_visto_egresos"].upper() == "CASOS"

# ------------------------------------------------------------------ 1. versión y archivo
registro = leer_csv(REGISTRO)[-1]
comprobar(f"El conjunto de desarrollo tiene el hash de la versión {registro['version']} registrada de la partición",
          sha256(DESARROLLO) == registro["sha256_desarrollo"])
grupos = pq.read_table(GRUPOS)
comprobar("El archivo de grupos tiene solo las columnas esperadas, sin nada que dependa de las variables objetivo",
          grupos.column_names == ["ID_EGRESO", "ID_PACIENTE", "PERIODO", "PACIENTE_VISTO"], str(grupos.column_names))

# ------------------------------------------------------------------ 2. recálculo con otro camino
t = pq.read_table(DESARROLLO, columns=["ID_EGRESO", "ID_PACIENTE", "BLOQUE_ID", "FECHAALTA", "ES_CASO_ESTUDIO", *VARIABLES])
anio_alta = pc.year(t["FECHAALTA"])
caso = t["ES_CASO_ESTUDIO"]
evalua = pc.and_(caso, pc.is_in(anio_alta, pa.array(EVALUA, type=anio_alta.type)))
entrena = pc.and_(caso, pc.is_in(anio_alta, pa.array(ENTRENA, type=anio_alta.type)))
bloques_eval = pc.unique(pc.filter(t["BLOQUE_ID"], evalua))
# Egresos de los años de entrenamiento en el bloque de la evaluación (todos o solo casos de estudio, según el parámetro).
previo = pc.and_(pc.is_in(anio_alta, pa.array(ENTRENA, type=anio_alta.type)), pc.is_in(t["BLOQUE_ID"], bloques_eval))
if SOLO_CASOS:
    previo = pc.and_(previo, caso)
pacientes_previos = pa.table({"ID_PACIENTE": pc.filter(t["ID_PACIENTE"], previo)}).group_by("ID_PACIENTE").aggregate([])["ID_PACIENTE"]
visto_todos = pc.is_in(t["ID_PACIENTE"], pacientes_previos)

casos = t.filter(caso)
periodo_calc = np.where(pc.filter(evalua, caso).to_numpy(zero_copy_only=False), "EVALUACION",
                        np.where(pc.filter(entrena, caso).to_numpy(zero_copy_only=False), "ENTRENAMIENTO", ""))
visto_calc = pc.filter(visto_todos, caso).to_numpy(zero_copy_only=False)
ids_calc = casos["ID_EGRESO"].to_numpy()

archivo = {"ID_EGRESO": grupos["ID_EGRESO"].to_numpy(), "PERIODO": np.array(grupos["PERIODO"].to_pylist()),
           "PACIENTE_VISTO": np.array(grupos["PACIENTE_VISTO"].to_pylist(), dtype=object)}
orden = np.argsort(archivo["ID_EGRESO"])
posicion = orden[np.searchsorted(archivo["ID_EGRESO"], ids_calc, sorter=orden)]
comprobar("El archivo tiene exactamente los casos de estudio del conjunto de desarrollo",
          len(archivo["ID_EGRESO"]) == len(ids_calc) and (archivo["ID_EGRESO"][posicion] == ids_calc).all(),
          f"({len(ids_calc)} casos)")
comprobar("Todo caso de estudio tiene período y el del archivo coincide con el recálculo (año de la fecha de alta)",
          bool((periodo_calc != "").all() and (archivo["PERIODO"][posicion] == periodo_calc).all()))
es_eval = periodo_calc == "EVALUACION"
visto_archivo = archivo["PACIENTE_VISTO"][posicion]
comprobar("PACIENTE_VISTO del archivo coincide con el recálculo en los casos de evaluación y no tiene dato en los de entrenamiento",
          bool((visto_archivo[es_eval].astype(bool) == visto_calc[es_eval]).all() and all(v is None for v in visto_archivo[~es_eval])),
          f"({int(es_eval.sum())} casos de evaluación; {int(visto_calc[es_eval].sum())} de pacientes ya vistos)")

# ------------------------------------------------------------------ 3. tabla del reporte
def cifras(mascara: np.ndarray) -> tuple:
    sub = casos.filter(pa.array(mascara))
    tasas = []
    for k in VARIABLES:
        v = sub[k].drop_null()
        tasas.append(round(100 * pc.sum(v).as_py() / len(v), 2) if len(v) else None)
    return len(sub), pc.count_distinct(sub["ID_PACIENTE"]).as_py(), tasas


esperado = {"Entrenamiento": cifras(~es_eval), "Evaluación: todos los casos": cifras(es_eval),
            "Evaluación: pacientes nuevos": cifras(es_eval & ~visto_calc), "Evaluación: pacientes ya vistos": cifras(es_eval & visto_calc)}
del_reporte = {}
for linea in REPORTE_13.read_text(encoding="utf-8").split("## 1.")[1].split("## 2.")[0].splitlines():
    celdas = [x.strip() for x in linea.strip().strip("|").split("|")]
    if len(celdas) == 8 and celdas[0] in esperado:
        del_reporte[celdas[0]] = (int(celdas[1].replace(".", "")), int(celdas[3].replace(".", "")),
                                  [float(x.replace(" %", "").replace(",", ".")) for x in celdas[4:]])
for nombre, (n, pacientes, tasas) in esperado.items():
    fila = del_reporte.get(nombre)
    comprobar(f"Reporte 13, fila «{nombre}»: casos, pacientes y tasas iguales al recálculo",
              fila is not None and fila[0] == n and fila[1] == pacientes and all(abs(a - b) < 0.0051 for a, b in zip(fila[2], tasas)),
              f"({n} casos; {pacientes} pacientes; tasas {tasas})")

todo_bien = all(ok for _, ok in resultados)
print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
ruta = ACTIVIDAD.name
SALIDA.write_text("\n\n".join([
    "# Prueba independiente de los grupos de la validación temporal",
    f"Generado por `{ruta}/pruebas/verificar_13_validacion_temporal.py` el {date.today():%d-%m-%Y}. El programa vuelve a calcular, sin "
    "usar ninguna función del script 13, el período de cada caso de estudio de desarrollo (con el año de la fecha de alta) y si el "
    "paciente ya fue visto (agrupando por identificador con pyarrow), y lo compara con el archivo y con la tabla del reporte 13. "
    "Solo lee el conjunto de desarrollo.",
    f"Partición probada: versión {registro['version']}, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`.",
    f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
    f"{sum(not ok for _, ok in resultados)} fallas).",
    "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
]) + "\n", encoding="utf-8")
print(f"Reporte guardado en {SALIDA}")
sys.exit(0 if todo_bien else 1)
