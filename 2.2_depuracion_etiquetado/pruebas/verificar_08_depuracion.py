"""Contraste independiente del script 08 (depuración).

Vuelve a calcular, con otro método, lo que el script 08 dejó en data/processed/grd_depurado.parquet:
duplicados, personas, identidad ambigua, criterios de exclusión, episodios asistenciales y los dos
papeles de cada egreso. No usa ninguna función del script 08: los criterios se evalúan con pyarrow
en vez de pandas y los episodios se arman con un recorrido egreso por egreso. Al final compara el
resultado con la tabla «paso a paso» del reporte 08. Solo lee.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\pruebas\\verificar_08_depuracion.py

Para contrastar otro archivo se indican su ruta y, si se quiere comparar, la de su reporte:
    ... verificar_08_depuracion.py <grd_depurado.parquet> [<08_depuracion.md>]

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
INTEGRADA = RAIZ / "data" / "processed" / "grd_2019_2024.parquet"
DEPURADA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "data" / "processed" / "grd_depurado.parquet"
REPORTE = Path(sys.argv[2]) if len(sys.argv) > 2 else (None if len(sys.argv) > 1 else ACTIVIDAD / "reportes" / "08_depuracion.md")
REGLAS = ACTIVIDAD / "reglas"
CIERRE = {"A": pd.Timestamp("2020-12-31"), "B": pd.Timestamp("2024-12-31")}
inicio = time.time()
todo_bien = True


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    global todo_bien
    todo_bien &= bool(cumple)
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


with open(REGLAS / "criterios_exclusion.csv", encoding="utf-8-sig", newline="") as f:
    criterios = list(csv.DictReader(f, delimiter=";"))
with open(REGLAS / "parametros.csv", encoding="utf-8-sig", newline="") as f:
    par = {r["parametro"]: r["valor"] for r in csv.DictReader(f, delimiter=";")}
activo = {c["codigo"]: c["activo"].strip().upper() == "SI" for c in criterios}
columna = {c["codigo"]: c["columna"] for c in criterios}
print(f"Archivo: {DEPURADA}", flush=True)

# ------------------------------------------------------------------ 1. columnas de la tabla integrada
ids_integrada = pq.read_table(INTEGRADA, columns=["ID_EGRESO"]).column(0)
ids_depurada = pq.read_table(DEPURADA, columns=["ID_EGRESO"]).column(0)
conservada = pc.is_in(ids_integrada, value_set=ids_depurada.combine_chunks())
comprobar("Las filas de la tabla depurada son filas de la tabla integrada", len(ids_depurada) == pc.sum(conservada).as_py(),
          f"({len(ids_integrada)} -> {len(ids_depurada)}; eliminadas {len(ids_integrada) - len(ids_depurada)})")
comprobar("Las filas conservan el orden de la tabla integrada", ids_integrada.filter(conservada).equals(ids_depurada))
originales = [n for n in pq.read_schema(INTEGRADA).names if n not in ("DUP_EXACTO", "DUP_CLAVE")]
nombres = pq.read_schema(DEPURADA).names
comprobar("Las columnas originales están al comienzo y en el mismo orden", nombres[:len(originales)] == originales,
          f"({len(originales)} originales + {len(nombres) - len(originales)} nuevas)")
distintas = [c for c in originales
             if not pq.read_table(INTEGRADA, columns=[c]).column(0).filter(conservada).equals(pq.read_table(DEPURADA, columns=[c]).column(0))]
comprobar(f"Las {len(originales)} columnas originales son idénticas celda a celda", not distintas, str(distintas[:5]) if distintas else "")

# ------------------------------------------------------------------ carga
nuevas = nombres[len(originales):]
base = ["ID_EGRESO", "ANIO_ARCHIVO", "ID_PACIENTE", "BLOQUE_ID", "SEXO", "FECHA_NACIMIENTO", "COD_HOSPITAL", "TIPO_ACTIVIDAD", "TIPO_INGRESO",
        "TIPO_PROCEDENCIA", "FECHA_INGRESO", "FECHAALTA", "TIPOALTA", "DIAGNOSTICO1", "IR_29301_COD_GRD", "CDM", "IR_29301_PESO"]
tabla = pq.read_table(DEPURADA, columns=base + nuevas)
d = tabla.to_pandas()

# ------------------------------------------------------------------ 2. duplicados
eliminados = pq.read_table(INTEGRADA, columns=["ID_EGRESO", "DUP_EXACTO", "ID_PACIENTE", "COD_HOSPITAL", "FECHA_INGRESO", "FECHAALTA", "SEXO",
                                               "FECHA_NACIMIENTO", "IR_29301_PESO"]).filter(pc.invert(conservada)).to_pandas()
CLAVE = ["ID_PACIENTE", "COD_HOSPITAL", "FECHA_INGRESO", "FECHAALTA", "SEXO", "FECHA_NACIMIENTO"]
completa = d[CLAVE[:4]].notna().all(axis=1)
comprobar("No quedan dos registros con igual paciente, hospital, fechas, sexo y fecha de nacimiento", not d[completa].duplicated(CLAVE).any())
repetidos = eliminados[~eliminados["DUP_EXACTO"]]
comprobar("Todo registro repetido eliminado tenía la clave completa", repetidos[CLAVE[:4]].notna().all(axis=1).all(),
          f"(copias exactas {int(eliminados['DUP_EXACTO'].sum())}; registros repetidos {len(repetidos)})")
conservados = d[completa].merge(repetidos[CLAVE].drop_duplicates(), on=CLAVE, how="inner")[["ID_EGRESO"] + CLAVE + ["IR_29301_PESO"]]
comprobar("Cada registro repetido eliminado tiene exactamente un registro conservado con la misma clave",
          len(conservados) == len(repetidos[CLAVE].drop_duplicates()) and not conservados.duplicated(CLAVE).any())
# Número de diagnósticos y de procedimientos de los registros involucrados, contados con pandas.
involucrados = np.concatenate([repetidos["ID_EGRESO"].to_numpy(), conservados["ID_EGRESO"].to_numpy()]).tolist()
diagnosticos, procedimientos = [f"DIAGNOSTICO{i}" for i in range(1, 36)], [f"PROCEDIMIENTO{i}" for i in range(1, 31)]
detalle = pq.read_table(INTEGRADA, columns=["ID_EGRESO"] + diagnosticos + procedimientos,
                        filters=[("ID_EGRESO", "in", involucrados)]).to_pandas().set_index("ID_EGRESO")
n_diag, n_proc = detalle[diagnosticos].notna().sum(axis=1), detalle[procedimientos].notna().sum(axis=1)
pares = repetidos.merge(conservados, on=CLAVE, suffixes=("_Q", "_C"))      # Q: eliminado; C: conservado


def completitud(sufijo: str) -> pd.DataFrame:
    ids = pares[f"ID_EGRESO{sufijo}"]
    return pd.DataFrame({"diag": n_diag.reindex(ids).to_numpy(), "proc": n_proc.reindex(ids).to_numpy(),
                         "peso": pares[f"IR_29301_PESO{sufijo}"].fillna(-1).to_numpy(), "id": ids.to_numpy()})


q, c = completitud("_Q"), completitud("_C")
mejor = ((c["diag"] > q["diag"]) | ((c["diag"] == q["diag"]) & ((c["proc"] > q["proc"]) | ((c["proc"] == q["proc"]) & (
    (c["peso"] > q["peso"]) | ((c["peso"] == q["peso"]) & (c["id"] < q["id"])))))))
comprobar("El registro conservado es el más completo (diagnósticos, procedimientos, peso GRD, primero del archivo)", mejor.all(),
          f"({int((~mejor).sum())} excepciones en {len(pares)})")

# ------------------------------------------------------------------ 3. personas e identidad ambigua
p = d.dropna(subset=["ID_PACIENTE"])
con_persona = p["ID_PERSONA"].notna()
comprobar("ID_PERSONA = ID_PACIENTE x 100 + número de persona",
          ((p.loc[con_persona, "ID_PERSONA"] // 100) == p.loc[con_persona, "ID_PACIENTE"]).all() and p.loc[con_persona, "ID_PERSONA"].mod(100).between(1, 99).all())
combinaciones = (p["SEXO"].fillna("?") + "|" + p["FECHA_NACIMIENTO"].astype("string").fillna("NA")).groupby(p["ID_PACIENTE"]).nunique()
genericos = set(combinaciones.index[combinaciones >= int(par["id_generico_min_personas"])])
es_generico = d["ID_PACIENTE"].isin(genericos)
comprobar("Identificadores genéricos (contados con otro método)", (es_generico == d["EXC_ID_GENERICO"]).all(),
          f"({len(genericos)} identificadores; {int(es_generico.sum())} egresos)")
if activo["E02"]:
    comprobar("Los identificadores genéricos no tienen persona", d.loc[es_generico, "ID_PERSONA"].isna().all())
resto = p[~p["ID_PACIENTE"].isin(genericos)] if activo["E02"] else p
comprobar("Todo egreso con identificador no genérico y con fecha de nacimiento tiene persona",
          resto.loc[resto["FECHA_NACIMIENTO"].notna(), "ID_PERSONA"].notna().all(), f"(sin persona: {int(resto['ID_PERSONA'].isna().sum())})")
fechas = resto.dropna(subset=["FECHA_NACIMIENTO"]).drop_duplicates(["ID_PACIENTE", "FECHA_NACIMIENTO", "ID_PERSONA"])[["ID_PACIENTE", "FECHA_NACIMIENTO", "ID_PERSONA"]]
comprobar("Una fecha de nacimiento de un identificador pertenece a una sola persona", not fechas.duplicated(["ID_PACIENTE", "FECHA_NACIMIENTO"]).any())
n_fechas = fechas.groupby("ID_PACIENTE")["FECHA_NACIMIENTO"].transform("size")
una = fechas[n_fechas == 1]
comprobar("Identificador con una sola fecha de nacimiento: persona 1", (una["ID_PERSONA"] % 100 == 1).all(), f"({len(una)} identificadores)")
dias_max, mismo_dia_mes = int(par["persona_dias_fnac"]), par["persona_mismo_dia_mes"].strip().upper() == "SI"
dos = fechas[n_fechas == 2].sort_values(["ID_PACIENTE", "FECHA_NACIMIENTO"])
a, b = dos.iloc[0::2].reset_index(drop=True), dos.iloc[1::2].reset_index(drop=True)
diferencia = (b["FECHA_NACIMIENTO"] - a["FECHA_NACIMIENTO"]).dt.days
igual_dia_mes = (a["FECHA_NACIMIENTO"].dt.day == b["FECHA_NACIMIENTO"].dt.day) & (a["FECHA_NACIMIENTO"].dt.month == b["FECHA_NACIMIENTO"].dt.month)
misma = (diferencia <= dias_max) | (igual_dia_mes & mismo_dia_mes)
comprobar("Identificadores con dos fechas de nacimiento: una persona si y solo si lo indica la regla", ((a["ID_PERSONA"] == b["ID_PERSONA"]) == misma).all(),
          f"({len(a)} identificadores: {int(misma.sum())} con una persona y {int((~misma).sum())} con dos)")
comprobar("Con dos personas, la 1 es la de más edad", ((a["ID_PERSONA"] % 100 == 1) & ((b["ID_PERSONA"] % 100 == 2) | misma)).all())
tres = fechas[n_fechas >= 3].sort_values(["ID_PACIENTE", "FECHA_NACIMIENTO"])
errores = 0
for _, g in tres.groupby("ID_PACIENTE"):
    fe, pe = g["FECHA_NACIMIENTO"].tolist(), g["ID_PERSONA"].tolist()
    grupo = [-1] * len(fe)                         # componentes conexas de la relación «compatibles», por búsqueda en anchura
    for i in range(len(fe)):
        if grupo[i] >= 0:
            continue
        grupo[i], cola = i, [i]
        while cola:
            x = cola.pop()
            for y in range(len(fe)):
                if grupo[y] < 0 and (abs((fe[x] - fe[y]).days) <= dias_max or (mismo_dia_mes and (fe[x].day, fe[x].month) == (fe[y].day, fe[y].month))):
                    grupo[y] = i
                    cola.append(y)
    errores += any((grupo[i] == grupo[j]) != (pe[i] == pe[j]) for i in range(len(fe)) for j in range(i))
comprobar("Identificadores con tres o más fechas de nacimiento: las personas son los grupos de fechas compatibles", errores == 0,
          f"({tres['ID_PACIENTE'].nunique()} identificadores)")
n_sexos, n_nacimientos = p.groupby("ID_PACIENTE")["SEXO"].nunique(), p.groupby("ID_PACIENTE")["FECHA_NACIMIENTO"].nunique()
ambiguos = set(n_sexos.index[(n_sexos > 1) | (n_nacimientos > 1)])
ambigua = d["ID_PACIENTE"].isin(ambiguos)
comprobar("IDENTIDAD_AMBIGUA: identificador con más de un sexo o más de una fecha de nacimiento", (ambigua == d["IDENTIDAD_AMBIGUA"]).all(),
          f"({len(ambiguos)} identificadores; {int(ambigua.sum())} egresos; {int((ambigua & d['ES_CASO_ESTUDIO']).sum())} casos de estudio)")
comprobar("Todo identificador con más de una persona tiene identidad ambigua",
          d.loc[d["ID_PACIENTE"].isin(set(p.loc[p["ID_PERSONA"] % 100 >= 2, "ID_PACIENTE"])), "IDENTIDAD_AMBIGUA"].all())

# ------------------------------------------------------------------ 4. criterios, con pyarrow
col = {n: tabla.column(n) for n in base}
ingreso, alta, nacimiento, tipoalta = col["FECHA_INGRESO"], col["FECHAALTA"], col["FECHA_NACIMIENTO"], col["TIPOALTA"]


def falso_si_nulo(x):
    return pc.fill_null(x, False)


def fecha(texto: str, dias: int) -> pa.Scalar:
    return pa.scalar((pd.Timestamp(texto) - pd.Timedelta(days=dias)).to_pydatetime(), type=tabla.schema.field("FECHAALTA").type)


seguimiento_minimo = min(int(v) for v in par["ventanas_dias"].split("|")) + int(par["censura_margen_dias"])
sesiones = [v.strip() for v in par["diagnosticos_sesion"].split("|") if v.strip()]
edad_dias = pc.divide(pc.cast(pc.subtract(pc.cast(ingreso, pa.timestamp("s")), pc.cast(nacimiento, pa.timestamp("s"))), pa.int64()), 86400)
sesion = pa.chunked_array([pa.array(np.zeros(len(d), dtype=bool))])
for prefijo in sesiones:
    sesion = pc.or_(sesion, falso_si_nulo(pc.starts_with(col["DIAGNOSTICO1"], prefijo)))
esperado = {
    "E03": pc.or_(pc.or_(pc.is_null(ingreso), pc.is_null(alta)), falso_si_nulo(pc.less(alta, ingreso))),
    "E04": falso_si_nulo(pc.is_in(col["TIPO_ACTIVIDAD"], value_set=pa.array(["HOSPITALIZACIÓN DIURNA", "HOSPITALIZACIÓN EN URGENCIA"]))),
    "E06": falso_si_nulo(pc.equal(tipoalta, "FALLECIDO")),
    "E07": falso_si_nulo(pc.starts_with(tipoalta, "DERIVACIÓN OTRO HOSPITAL")),
    "E08": falso_si_nulo(pc.starts_with(tipoalta, "DERIVACIÓN INST. PRIVADA")),
    "E09": pc.or_(pc.is_null(col["IR_29301_COD_GRD"]), falso_si_nulo(pc.equal(col["CDM"], "99"))),
    "E10": pc.or_(pc.or_(pc.is_null(nacimiento), pc.is_null(tipoalta)),
                  pc.or_(falso_si_nulo(pc.greater(nacimiento, ingreso)), falso_si_nulo(pc.greater(edad_dias, int(par["edad_maxima"]) * 365.25)))),
    "E11": falso_si_nulo(pc.if_else(pc.equal(col["BLOQUE_ID"], "A"), pc.greater(alta, fecha("2020-12-31", seguimiento_minimo)),
                                    pc.greater(alta, fecha("2024-12-31", seguimiento_minimo)))),
    "E12": falso_si_nulo(pc.is_in(tipoalta, value_set=pa.array(["ALTA VOLUNTARIA", "FUGA DEL PACIENTE"]))),
    "E13": falso_si_nulo(pc.starts_with(col["TIPO_ACTIVIDAD"], "CIRUGÍA MAYOR AMBULATORIA")),
    "E14": sesion,
}
marca = {codigo: valores.to_numpy(zero_copy_only=False) for codigo, valores in esperado.items()}
marca["E01"] = (d["ID_PACIENTE"].isna() | (d["ID_PERSONA"].isna() & ~es_generico)).to_numpy()
marca["E02"] = es_generico.to_numpy()
for codigo in sorted(marca):
    real = d[columna[codigo]].to_numpy()
    comprobar(f"{codigo} ({columna[codigo]})", (marca[codigo] == real).all(), f"(cumplen {int(real.sum())}; diferencias {int((marca[codigo] != real).sum())})")

# ------------------------------------------------------------------ 5. episodios asistenciales, con un recorrido egreso por egreso
seguible = d["ID_PERSONA"].notna().to_numpy() & ~marca["E03"]
for cr in criterios:
    if cr["papel"] == "AMBOS" and activo[cr["codigo"]]:
        seguible &= ~marca[cr["codigo"]]
s = d[seguible].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
personas = s["ID_PERSONA"].to_numpy(dtype="int64").tolist()
ingresos = s["FECHA_INGRESO"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
altas = s["FECHAALTA"].to_numpy().astype("datetime64[D]").astype("int64").tolist()
hospitales = pd.factorize(s["COD_HOSPITAL"])[0].tolist()
egresos = s["ID_EGRESO"].to_numpy().tolist()
derivado = s["TIPOALTA"].fillna("").str.startswith("DERIVACIÓN").tolist()
viene_de_hospital = s["TIPO_PROCEDENCIA"].fillna("").str.startswith("OTROS HOSPITALES").tolist()
dias_traslado, exige_marca = int(par["traslado_dias_max"]), par["traslado_exige_marca"].strip().upper() == "SI"
n = len(s)
episodio, continua, ultimo = np.empty(n, dtype="int64"), np.zeros(n, dtype=bool), {}
persona_anterior = alta_mayor = hospital_ref = ingreso_ref = derivado_ref = episodio_actual = None
for k in range(n):
    persona, ing, alt, hosp = personas[k], ingresos[k], altas[k], hospitales[k]
    sigue = False
    if persona == persona_anterior:
        dias = ing - alta_mayor
        if dias < 0:                                                   # ingresa antes del alta anterior
            sigue = True
        elif dias <= dias_traslado and hosp != hospital_ref and (not exige_marca or derivado_ref or viene_de_hospital[k]):
            sigue = True                                               # otro hospital, el mismo día o los siguientes
        elif dias == 0 and hosp == hospital_ref and ing == ingreso_ref and alt == alta_mayor:
            sigue = True                                               # la misma estadía registrada dos veces
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
comprobar("Episodios: ID_EPISODIO igual al del recorrido", (episodio == s["ID_EPISODIO"].to_numpy(dtype="int64")).all(), f"({len(ultimo)} episodios en {n} egresos)")
comprobar("Episodios: CONTINUA_EPISODIO igual", (continua == s["CONTINUA_EPISODIO"].to_numpy()).all(), f"({int(continua.sum())} continuaciones)")
comprobar("Episodios: ALTA_FINAL_EPISODIO igual", (final == s["ALTA_FINAL_EPISODIO"].to_numpy()).all())
tamano = pd.Series(episodio).map(pd.Series(episodio).value_counts()).to_numpy()
comprobar("Episodios: N_EGRESOS_EPISODIO igual", (tamano == s["N_EGRESOS_EPISODIO"].to_numpy(dtype="int64")).all())
comprobar("Los egresos que no se pueden seguir no tienen episodio",
          d.loc[~seguible, "ID_EPISODIO"].isna().all() and not d.loc[~seguible, "CONTINUA_EPISODIO"].any() and not d.loc[~seguible, "ALTA_FINAL_EPISODIO"].any())
tramo = pd.Series(False, index=d.index)
tramo[s.index] = ~final
marca["E05"] = tramo.to_numpy()
comprobar(f"E05 ({columna['E05']})", (marca["E05"] == d[columna["E05"]].to_numpy()).all(), f"(cumplen {int(marca['E05'].sum())})")

# ------------------------------------------------------------------ 6. paso a paso, motivo y papeles
quedan = np.ones(len(d), dtype=bool)
motivo = np.full(len(d), None, dtype=object)
pasos = {}
for cr in criterios:
    cumple = marca[cr["codigo"]]
    quita = quedan & cumple & activo[cr["codigo"]]
    motivo[quita] = cr["codigo"]
    quedan &= ~quita
    pasos[cr["codigo"]] = (int(cumple.sum()), int(quita.sum()) if activo[cr["codigo"]] else None, int(quedan.sum()))
comprobar("ES_CASO_ESTUDIO", (quedan == d["ES_CASO_ESTUDIO"].to_numpy()).all(), f"({int(quedan.sum())} casos de estudio)")
comprobar("MOTIVO_EXCLUSION", (pd.Series(motivo, index=d.index).fillna("-") == d["MOTIVO_EXCLUSION"].fillna("-")).all())
puede = pd.Series(False, index=d.index)
puede[s.index] = ~continua
comprobar("PUEDE_SER_REINGRESO", (puede.to_numpy() == d["PUEDE_SER_REINGRESO"].to_numpy()).all(), f"({int(puede.sum())} egresos)")
casos = d[quedan]
al_cierre = (casos["BLOQUE_ID"].map(CIERRE) - casos["FECHAALTA"]).dt.days
comprobar("Los casos de estudio están vivos al alta y tienen persona, GRD válido y el seguimiento mínimo",
          casos["ID_PERSONA"].notna().all() and (casos["TIPOALTA"] != "FALLECIDO").all() and casos["IR_29301_COD_GRD"].notna().all()
          and (casos["CDM"] != "99").all() and (al_cierre >= seguimiento_minimo).all(), f"(mínimo de días al cierre: {int(al_cierre.min())})")

if REPORTE is not None and REPORTE.exists():
    filas = {}
    for linea in REPORTE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (E\d\d) \| .* \| ([\d.]+) \| ([\d.]+|—) \| ([\d.]+) \|$", linea)
        if m and m[1] not in filas:
            filas[m[1]] = (int(m[2].replace(".", "")), None if m[3] == "—" else int(m[3].replace(".", "")), int(m[4].replace(".", "")))
    comprobar(f"La tabla «paso a paso» de {REPORTE.name} coincide con el recálculo en los {len(pasos)} criterios", filas == pasos,
              str({k: (filas.get(k), v) for k, v in pasos.items() if filas.get(k) != v}) if filas != pasos else "")

print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
sys.exit(0 if todo_bien else 1)
