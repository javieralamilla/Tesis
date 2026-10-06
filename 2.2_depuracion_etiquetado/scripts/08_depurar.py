"""Depuración de la tabla integrada (actividad 2.2, script 08).

Parte de data/processed/grd_2019_2024.parquet y deja data/processed/grd_depurado.parquet:

  1. Duplicados (bitácora D15 y D24): se eliminan las copias exactas y, cuando varios registros
     comparten paciente, hospital, fechas, sexo y fecha de nacimiento, se conserva el más completo.
  2. Persona (D18): ID_PERSONA separa a las personas distintas que comparten un identificador.
  3. Episodio asistencial (D19): ID_EPISODIO une los egresos que son tramos de una misma
     hospitalización (traslados entre hospitales).
  4. Criterios de exclusión (D23): cada criterio de reglas/criterios_exclusion.csv se marca en una
     columna EXC_*, sin borrar filas. ES_CASO_ESTUDIO indica los egresos que pasan todos los
     criterios activos; PUEDE_SER_REINGRESO, los que pueden contar como reingreso de un alta anterior.

Los umbrales están en reglas/parametros.csv. El reporte reportes/08_depuracion.md muestra cuántos
egresos quita cada criterio, paso a paso, desde la tabla integrada hasta los casos de estudio.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\scripts\\08_depurar.py
"""

import csv
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_REPORTS = ACTIVIDAD / "reportes"
ORIGEN = DIR_PROCESSED / "grd_2019_2024.parquet"
DESTINO = DIR_PROCESSED / "grd_depurado.parquet"
ARCHIVO_CRITERIOS = ACTIVIDAD / "reglas" / "criterios_exclusion.csv"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
ANIOS = list(range(2019, 2025))

# Último día observado de cada bloque de identificador (bitácora D03).
CIERRE_BLOQUE = {"A": pd.Timestamp("2020-12-31"), "B": pd.Timestamp("2024-12-31")}
# Dos registros son el mismo episodio si coinciden en estas cuatro columnas (bitácora D15).
CLAVE = ["ID_PACIENTE", "COD_HOSPITAL", "FECHA_INGRESO", "FECHAALTA"]
# ID_PERSONA = ID_PACIENTE * 100 + número de persona dentro del identificador (1, 2, ...).
FACTOR_PERSONA = 100
ACTIVIDAD_2019 = ["HOSPITALIZACIÓN DIURNA", "HOSPITALIZACIÓN EN URGENCIA"]
DERIVACION = "DERIVACIÓN"                        # comienzo de los tipos de alta por derivación
DERIVA_HOSPITAL = "DERIVACIÓN OTRO HOSPITAL"
DERIVA_PRIVADO = "DERIVACIÓN INST. PRIVADA"
VIENE_DE_HOSPITAL = "OTROS HOSPITALES"           # comienzo de las procedencias desde otro hospital
CMA = "CIRUGÍA MAYOR AMBULATORIA"

COLUMNAS = ["ID_EGRESO", "ANIO_ARCHIVO", "DUP_EXACTO", "ID_PACIENTE", "BLOQUE_ID", "SEXO", "FECHA_NACIMIENTO",
            "COD_HOSPITAL", "TIPO_ACTIVIDAD", "TIPO_INGRESO", "TIPO_PROCEDENCIA", "FECHA_INGRESO", "FECHAALTA",
            "TIPOALTA", "IR_29301_COD_GRD", "CDM", "IR_29301_PESO"]
QUITAR = ["DUP_EXACTO", "DUP_CLAVE"]             # describen la tabla integrada, no la depurada
PARAMETROS = {"persona_dias_fnac": int, "persona_mismo_dia_mes": bool, "id_generico_min_personas": int,
              "traslado_dias_max": int, "traslado_exige_marca": bool, "censura_dias": int, "edad_maxima": int}
# Motivo por el que un egreso continúa el episodio anterior.
SOLAPADO, OTRO_MISMO_DIA, OTRO_DIA_SIGUIENTE, MISMA_ESTADIA = 1, 2, 3, 4


# ------------------------------------------------------------------ reglas
def si_no(valor: str, origen: str) -> bool:
    valor = valor.strip().upper()
    if valor not in ("SI", "NO"):
        raise SystemExit(f"{origen}: se esperaba SI o NO y dice '{valor}'.")
    return valor == "SI"


def cargar_parametros() -> dict:
    with open(ARCHIVO_PARAMETROS, encoding="utf-8-sig", newline="") as f:
        filas = {fila["parametro"]: fila for fila in csv.DictReader(f, delimiter=";")}
    faltan = sorted(set(PARAMETROS) - set(filas))      # el archivo también tiene parámetros de otros scripts
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")
    par = {}
    for nombre, tipo in PARAMETROS.items():
        valor = filas[nombre]["valor"]
        par[nombre] = si_no(valor, nombre) if tipo is bool else int(valor)
    par["descripcion"] = {nombre: (filas[nombre]["valor"].strip(), filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    return par


def cargar_criterios() -> list[dict]:
    with open(ARCHIVO_CRITERIOS, encoding="utf-8-sig", newline="") as f:
        criterios = list(csv.DictReader(f, delimiter=";"))
    for c in criterios:
        c["activo"] = si_no(c["activo"], f"{c['codigo']} (activo)")
        c["obligatorio"] = si_no(c["obligatorio"], f"{c['codigo']} (obligatorio)")
        if c["papel"] not in ("AMBOS", "CASO"):
            raise SystemExit(f"{c['codigo']}: el papel debe ser AMBOS o CASO.")
        if c["obligatorio"] and not c["activo"]:
            raise SystemExit(f"{c['codigo']} no se puede desactivar: sin ese dato no se puede calcular el reingreso.")
    return criterios


# ------------------------------------------------------------------ carga
def cargar() -> pd.DataFrame:
    """Columnas necesarias, en el orden de la tabla integrada (el índice es la posición de la fila)."""
    df = pq.read_table(ORIGEN, columns=COLUMNAS).to_pandas()
    # Número de diagnósticos y de procedimientos informados: decide qué registro repetido se conserva.
    for nombre, prefijo, n in (("N_DIAG", "DIAGNOSTICO", 35), ("N_PROC", "PROCEDIMIENTO", 30)):
        total = np.zeros(len(df), dtype="int8")
        for i in range(1, n + 1):
            columna = pq.read_table(ORIGEN, columns=[f"{prefijo}{i}"]).column(0)
            total += np.asarray(columna.is_valid().to_numpy(zero_copy_only=False), dtype="int8")
        df[nombre] = total
    return df


# ------------------------------------------------------------------ 1. duplicados
def marcar_repetidos(df: pd.DataFrame) -> pd.Series:
    """Registros que sobran entre los que comparten clave, sexo y fecha de nacimiento (bitácora D15).

    Se conserva el más completo: más diagnósticos; luego más procedimientos; luego mayor peso GRD;
    luego el primero del archivo.
    """
    completa = df[CLAVE].notna().all(axis=1)
    orden = df[completa].sort_values(["N_DIAG", "N_PROC", "IR_29301_PESO", "ID_EGRESO"],
                                     ascending=[False, False, False, True], na_position="last")
    repetido = orden.duplicated(CLAVE + ["SEXO", "FECHA_NACIMIENTO"], keep="first")
    return repetido.reindex(df.index, fill_value=False)


# ------------------------------------------------------------------ 2. personas
def numerar_personas(fechas: list, dias_max: int, mismo_dia_mes: bool) -> list[int]:
    """Agrupa en personas las fechas de nacimiento de un identificador (bitácora D18).

    Dos fechas son de la misma persona si difieren en hasta dias_max días o, con mismo_dia_mes,
    si coinciden en día y mes. Las fechas llegan ordenadas: la persona 1 es la de más edad.
    """
    grupo = list(range(len(fechas)))
    for j, b in enumerate(fechas):
        for i in range(j):
            a = fechas[i]
            if (b - a).days <= dias_max or (mismo_dia_mes and (a.day, a.month) == (b.day, b.month)):
                viejo, nuevo = grupo[j], grupo[i]
                if viejo != nuevo:
                    grupo = [nuevo if g == viejo else g for g in grupo]
    numeros = {}
    return [numeros.setdefault(g, len(numeros) + 1) for g in grupo]


def asignar_personas(df: pd.DataFrame, par: dict, excluir_genericos: bool) -> tuple[pd.Series, np.ndarray, dict]:
    con_id = df["ID_PACIENTE"].notna()
    base = pd.DataFrame({"ID": df.loc[con_id, "ID_PACIENTE"].astype("int64"),
                         "SEXO": df.loc[con_id, "SEXO"].fillna("?"),
                         "FNAC": df.loc[con_id, "FECHA_NACIMIENTO"]})
    combos = base.drop_duplicates()
    n_combos = combos.groupby("ID").size()
    genericos = n_combos.index[n_combos >= par["id_generico_min_personas"]].to_numpy()
    es_generico = base["ID"].isin(genericos)

    # Identificadores con más de una fecha de nacimiento: se reparten en personas.
    fechas = combos.dropna(subset=["FNAC"]).drop_duplicates(["ID", "FNAC"])[["ID", "FNAC"]]
    varias = fechas[fechas.groupby("ID")["FNAC"].transform("size") > 1]
    if excluir_genericos:
        varias = varias[~varias["ID"].isin(genericos)]
    varias = varias.sort_values(["ID", "FNAC"])
    numeros = []
    for _, f in varias.groupby("ID", sort=False)["FNAC"]:
        numeros += numerar_personas(f.tolist(), par["persona_dias_fnac"], par["persona_mismo_dia_mes"])
    varias = varias.assign(N=numeros)
    if len(varias) and varias["N"].max() >= FACTOR_PERSONA:
        raise SystemExit("Un identificador tiene 100 personas o más: revisar el criterio E02.")
    personas_por_id = varias.groupby("ID")["N"].max()

    afectado = base["ID"].isin(personas_por_id.index)
    sub = base.loc[afectado, ["ID", "FNAC"]].merge(varias, on=["ID", "FNAC"], how="left")
    sub.index = base.index[afectado]
    # Sin fecha de nacimiento: se asigna a la persona del identificador solo si es única.
    unica = sub["N"].isna() & (sub["ID"].map(personas_por_id) == 1)
    sub.loc[unica, "N"] = 1
    # Una sola fecha de nacimiento: una persona. En los demás identificadores, la que corresponde a la fecha.
    n = sub["N"].astype("Int64").reindex(base.index).where(afectado, 1)
    persona = (base["ID"] * FACTOR_PERSONA + n).mask(es_generico & excluir_genericos)
    id_persona = persona.reindex(df.index)

    # Cifras para el reporte.
    dos = varias[varias.groupby("ID")["N"].transform("size") == 2]
    a, b = dos.iloc[0::2], dos.iloc[1::2]
    dias = ((b["FNAC"].to_numpy() - a["FNAC"].to_numpy()) // np.timedelta64(1, "D")).astype("int64")
    cerca = dias <= par["persona_dias_fnac"]
    distintas = b["N"].to_numpy() == 2
    por_persona = (pd.DataFrame({"P": id_persona, "ID": df["ID_PACIENTE"], "FNAC": df["FECHA_NACIMIENTO"],
                                 "ING": df["FECHA_INGRESO"]}).dropna(subset=["P"])
                   .groupby("P").agg(ID=("ID", "first"), FNAC=("FNAC", "min"), ING=("ING", "min")))
    n_por_id = por_persona.groupby("ID").size()
    pares = por_persona[por_persona["ID"].isin(n_por_id.index[n_por_id == 2])].sort_values(["ID", "FNAC"])
    mayor, menor = pares.iloc[0::2], pares.iloc[1::2]
    edad_menor = (menor["ING"].to_numpy() - menor["FNAC"].to_numpy()) / np.timedelta64(1, "D") / 365.25
    diferencia = (menor["FNAC"].to_numpy() - mayor["FNAC"].to_numpy()) / np.timedelta64(1, "D") / 365.25
    n_sexos = combos.dropna(subset=["FNAC"]).groupby(["ID", "FNAC"]).size()
    info = {
        "identificadores": int(len(n_combos)),
        "con_varias_combinaciones": int((n_combos > 1).sum()),
        "egresos_varias_combinaciones": int(base["ID"].isin(n_combos.index[n_combos > 1]).sum()),
        "genericos": int(len(genericos)),
        "egresos_genericos": int(es_generico.sum()),
        "mayor_generico": int(n_combos.max()),
        "ids_mismo_nacimiento_otro_sexo": int(n_sexos[n_sexos > 1].index.get_level_values("ID").nunique()),
        "ids_varias_fechas": int(len(personas_por_id)),
        "ids_dos_fechas": int(len(a)),
        "dos_cerca": int(cerca.sum()),
        "dos_error_anio": int((~cerca & ~distintas).sum()),
        "dos_distintas": int(distintas.sum()),
        "ids_tres_o_mas_fechas": int((varias.groupby("ID").size() > 2).sum()),
        "personas": int(len(por_persona)),
        "ids_por_personas": {int(k): int(v) for k, v in n_por_id.value_counts().sort_index().items()},
        "madre_hijo": int(((edad_menor < 1) & (diferencia > 12)).sum()),
        "con_id_sin_persona": int((con_id & id_persona.isna()).sum() - (es_generico.sum() if excluir_genericos else 0)),
    }
    return id_persona, genericos, info


# ------------------------------------------------------------------ 3. episodios asistenciales
def armar_episodios(s: pd.DataFrame, par: dict) -> tuple[pd.DataFrame, dict]:
    """Une en un episodio asistencial los egresos de una persona que son tramos de una misma
    hospitalización (bitácora D19). Un egreso continúa el episodio anterior cuando:
      - ingresa antes del alta más tardía de los egresos anteriores (están solapados);
      - ingresa en otro hospital el mismo día de esa alta o hasta traslado_dias_max días después;
      - tiene el mismo hospital y las mismas fechas que el egreso anterior (la misma estadía
        registrada dos veces con distinto sexo o fecha de nacimiento, que D15 no fusiona).
    """
    s = s.sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    persona = s["ID_PERSONA"].to_numpy(dtype="int64")
    primero = np.r_[True, persona[1:] != persona[:-1]]     # primer egreso de cada persona
    ingreso, alta = s["FECHA_INGRESO"], s["FECHAALTA"]

    # Alta más tardía entre los egresos anteriores de la persona, y datos del egreso que la tiene.
    alta_previa = alta.groupby(persona, sort=False).cummax().shift(1).mask(primero)
    lidera = primero | (alta >= alta_previa).to_numpy()
    hospital_previo = s["COD_HOSPITAL"].where(lidera).ffill().shift(1)
    ingreso_previo = ingreso.where(lidera).ffill().shift(1)
    tipoalta_previo = s["TIPOALTA"].fillna("").where(lidera).ffill().shift(1).fillna("")

    dias = (ingreso - alta_previa).dt.days                 # sin dato en el primer egreso de cada persona
    otro_hospital = (s["COD_HOSPITAL"] != hospital_previo).to_numpy() & ~primero
    marca = (tipoalta_previo.str.startswith(DERIVACION).to_numpy()
             | s["TIPO_PROCEDENCIA"].str.startswith(VIENE_DE_HOSPITAL, na=False).to_numpy())
    solapado = (dias < 0).to_numpy()
    contiguo = dias.between(0, par["traslado_dias_max"]).to_numpy() & otro_hospital
    contiguo_todos = contiguo.copy()
    if par["traslado_exige_marca"]:
        contiguo &= marca
    misma_estadia = ((dias == 0).to_numpy() & ~otro_hospital & ~primero
                     & (ingreso == ingreso_previo).to_numpy() & (alta == alta_previa).to_numpy())
    motivo = np.select([solapado, contiguo & (dias == 0).to_numpy(), contiguo, misma_estadia],
                       [SOLAPADO, OTRO_MISMO_DIA, OTRO_DIA_SIGUIENTE, MISMA_ESTADIA], default=0)
    continua = motivo > 0

    egreso = s["ID_EGRESO"].to_numpy()
    episodio = pd.Series(egreso).where(~continua).ffill().to_numpy(dtype="int64")
    _, inverso, cuenta = np.unique(episodio, return_inverse=True, return_counts=True)
    # Alta final: el egreso con el alta más tardía del episodio (si empatan, el último ingresado).
    orden = np.lexsort((egreso, ingreso.to_numpy(), alta.to_numpy(), episodio))
    ultimo = np.r_[episodio[orden][1:] != episodio[orden][:-1], True]
    final = np.zeros(len(s), dtype=bool)
    final[orden[ultimo]] = True

    resultado = pd.DataFrame({"ID_EPISODIO": pd.array(episodio, dtype="Int64"),
                              "N_EGRESOS_EPISODIO": pd.array(cuenta[inverso], dtype="Int16"),
                              "CONTINUA_EPISODIO": continua, "ALTA_FINAL_EPISODIO": final}, index=s.index)
    deriva = s["TIPOALTA"].str.startswith(DERIVA_HOSPITAL, na=False).to_numpy()
    anio = s["ANIO_ARCHIVO"].to_numpy()
    tam = np.minimum(cuenta, 5)
    info = {
        "seguibles": int(len(s)),
        "episodios": int(len(cuenta)),
        "tamanos": {int(k): int((tam == k).sum()) for k in range(1, 6)},
        "continuaciones": {int(k): int((motivo == k).sum()) for k in (SOLAPADO, OTRO_MISMO_DIA, OTRO_DIA_SIGUIENTE, MISMA_ESTADIA)},
        "contiguos": {"mismo_dia": int((contiguo_todos & (dias == 0).to_numpy()).sum()),
                      "dia_siguiente": int((contiguo_todos & (dias >= 1).to_numpy()).sum()),
                      "mismo_dia_marca": int((contiguo_todos & (dias == 0).to_numpy() & marca).sum()),
                      "dia_siguiente_marca": int((contiguo_todos & (dias >= 1).to_numpy() & marca).sum())},
        "mismo_hospital_mismo_dia": int(((dias == 0).to_numpy() & ~otro_hospital & ~primero & ~continua).sum()),
        "derivados": {a: int((deriva & (anio == a)).sum()) for a in ANIOS},
        "derivados_con_continuacion": {a: int((deriva & ~final & (anio == a)).sum()) for a in ANIOS},
        "episodios_sin_solape": bool((dias[~continua & ~primero] >= 0).all()),
        "un_final_por_episodio": bool(final.sum() == len(cuenta)),
    }
    return resultado, info


# ------------------------------------------------------------------ 4. criterios de exclusión
def marcar_criterios(df: pd.DataFrame, genericos: np.ndarray, par: dict) -> dict[str, np.ndarray]:
    """Egresos que cumplen cada criterio, sin considerar los demás. E05 se agrega tras armar los episodios."""
    ingreso, alta, nacimiento = df["FECHA_INGRESO"], df["FECHAALTA"], df["FECHA_NACIMIENTO"]
    edad = (ingreso - nacimiento).dt.days / 365.25
    tipoalta = df["TIPOALTA"]
    es_generico = df["ID_PACIENTE"].isin(genericos)
    cierre = df["BLOQUE_ID"].map(CIERRE_BLOQUE)
    marcas = {
        # Sin identificador, o con identificador pero sin persona asignable (sin fecha de nacimiento
        # en un identificador que comparten varias personas).
        "E01": df["ID_PACIENTE"].isna() | (df["ID_PERSONA"].isna() & ~es_generico),
        "E02": es_generico,
        "E03": ingreso.isna() | alta.isna() | (alta < ingreso),
        "E04": df["TIPO_ACTIVIDAD"].isin(ACTIVIDAD_2019),
        "E06": tipoalta == "FALLECIDO",
        "E07": tipoalta.str.startswith(DERIVA_HOSPITAL, na=False),
        "E08": tipoalta.str.startswith(DERIVA_PRIVADO, na=False),
        "E09": df["IR_29301_COD_GRD"].isna() | (df["CDM"] == "99"),
        "E10": nacimiento.isna() | (nacimiento > ingreso) | (edad > par["edad_maxima"]) | tipoalta.isna(),
        "E11": alta + pd.Timedelta(days=par["censura_dias"]) > cierre,
        "E12": tipoalta.isin(["ALTA VOLUNTARIA", "FUGA DEL PACIENTE"]),
        "E13": df["TIPO_ACTIVIDAD"].str.startswith(CMA, na=False),
    }
    return {codigo: np.asarray(m, dtype=bool) for codigo, m in marcas.items()}


def conteo(mascara: np.ndarray, valores: pd.Series) -> dict:
    return {k: int(v) for k, v in valores[mascara].value_counts(dropna=False).items()}


def depurar(par: dict, criterios: list[dict]) -> tuple[pd.DataFrame, np.ndarray, dict]:
    """Devuelve las columnas nuevas (una fila por egreso conservado, en el orden de la tabla
    integrada), la máscara de filas conservadas y las cifras del reporte."""
    activo = {c["codigo"]: c["activo"] for c in criterios}
    df = cargar()
    info = {"entrada": len(df), "entrada_anio": conteo(np.ones(len(df), dtype=bool), df["ANIO_ARCHIVO"])}
    conservar = np.zeros(len(df), dtype=bool)

    # 1. Duplicados
    exacta = df["DUP_EXACTO"].to_numpy()
    info["exactas_anio"] = conteo(exacta, df["ANIO_ARCHIVO"])
    df = df[~exacta]
    repetido = marcar_repetidos(df).to_numpy()
    info["repetidos_anio"] = conteo(repetido, df["ANIO_ARCHIVO"])
    df = df[~repetido].copy()
    conservar[df.index] = True
    info["salida_anio"] = conteo(np.ones(len(df), dtype=bool), df["ANIO_ARCHIVO"])

    # 2. Personas
    df["ID_PERSONA"], genericos, info["personas"] = asignar_personas(df, par, excluir_genericos=activo["E02"])
    completa = df[CLAVE].notna().all(axis=1)
    misma_clave = df[completa & df.duplicated(CLAVE, keep=False)]
    grupos = misma_clave.groupby(CLAVE)["ID_PERSONA"].agg(personas="nunique", sin_persona=lambda p: p.isna().any())
    info["misma_clave"] = {"registros": len(misma_clave), "grupos": len(grupos),
                           "sin_persona": int(grupos["sin_persona"].sum()),
                           "distintas": int((~grupos["sin_persona"] & (grupos["personas"] > 1)).sum()),
                           "misma": int((~grupos["sin_persona"] & (grupos["personas"] == 1)).sum())}

    # 3. Episodios asistenciales, sobre los egresos que se pueden seguir
    marcas = marcar_criterios(df, genericos, par)
    seguible = df["ID_PERSONA"].notna().to_numpy() & ~marcas["E03"]
    for c in criterios:
        if c["papel"] == "AMBOS" and c["activo"]:
            seguible &= ~marcas[c["codigo"]]
    episodios, info["episodios"] = armar_episodios(df[seguible], par)
    df["ID_EPISODIO"] = episodios["ID_EPISODIO"].reindex(df.index)
    df["N_EGRESOS_EPISODIO"] = episodios["N_EGRESOS_EPISODIO"].reindex(df.index)
    for col in ("CONTINUA_EPISODIO", "ALTA_FINAL_EPISODIO"):
        df[col] = episodios[col].reindex(df.index, fill_value=False)
    marcas["E05"] = seguible & ~df["ALTA_FINAL_EPISODIO"].to_numpy()
    if set(marcas) != {c["codigo"] for c in criterios}:
        raise SystemExit(f"{ARCHIVO_CRITERIOS.name}: los códigos deben ser exactamente {sorted(marcas)}.")

    # 4. Criterios en el orden de la tabla: cada uno quita casos de estudio entre los que quedaban
    anio = df["ANIO_ARCHIVO"]
    restante = np.ones(len(df), dtype=bool)
    motivo = np.full(len(df), None, dtype=object)
    pasos = []
    for c in criterios:
        cumple = marcas[c["codigo"]]
        quita = restante & cumple if c["activo"] else np.zeros(len(df), dtype=bool)
        motivo[quita] = c["codigo"]
        restante &= ~quita
        pasos.append({**c, "cumplen": int(cumple.sum()), "quita": int(quita.sum()),
                      "quita_anio": conteo(quita, anio), "quedan": int(restante.sum())})
    for p in pasos:
        p["quitaria"] = int((restante & marcas[p["codigo"]]).sum())      # solo se informa en los desactivados
    reingreso = seguible & ~df["CONTINUA_EPISODIO"].to_numpy()

    nuevo = df[["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "N_EGRESOS_EPISODIO", "CONTINUA_EPISODIO",
                "ALTA_FINAL_EPISODIO"]].copy()
    for c in criterios:
        nuevo[c["columna"]] = marcas[c["codigo"]]
    nuevo["MOTIVO_EXCLUSION"] = pd.Series(motivo, index=df.index, dtype="str")
    nuevo["ES_CASO_ESTUDIO"] = restante
    nuevo["PUEDE_SER_REINGRESO"] = reingreso

    info.update({
        "pasos": pasos,
        "casos": int(restante.sum()),
        "casos_anio": conteo(restante, anio),
        "reingreso": int(reingreso.sum()),
        "reingreso_anio": conteo(reingreso, anio),
        "no_seguibles": int((~seguible).sum()),
        "continuan": int(df["CONTINUA_EPISODIO"].sum()),
        "casos_tipoalta": conteo(restante, df["TIPOALTA"]),
        "casos_actividad": conteo(restante, df["TIPO_ACTIVIDAD"]),
        "casos_ingreso": conteo(restante, df["TIPO_INGRESO"]),
        "faltantes": {"Sin fecha de nacimiento": int(df["FECHA_NACIMIENTO"].isna().sum()),
                      "Fecha de nacimiento posterior al ingreso": int((df["FECHA_NACIMIENTO"] > df["FECHA_INGRESO"]).sum()),
                      f"Edad al ingreso mayor de {par['edad_maxima']} años":
                          int(((df["FECHA_INGRESO"] - df["FECHA_NACIMIENTO"]).dt.days / 365.25 > par["edad_maxima"]).sum()),
                      "Sin tipo de alta": int(df["TIPOALTA"].isna().sum())},
        "sin_grd": {"Sin código GRD": int(df["IR_29301_COD_GRD"].isna().sum()), "CDM 99": int((df["CDM"] == "99").sum())},
    })
    episodio_persona = df.loc[seguible].groupby("ID_EPISODIO")["ID_PERSONA"].nunique()
    info["verificaciones"] = [
        ("Registros de salida = registros de entrada − duplicados eliminados",
         len(df) == info["entrada"] - int(exacta.sum()) - int(repetido.sum())),
        ("`ID_EGRESO` único en la tabla depurada", df["ID_EGRESO"].is_unique),
        ("Ningún identificador de paciente aparece en los dos bloques",
         int((df.dropna(subset=["ID_PACIENTE"]).groupby("ID_PACIENTE")["BLOQUE_ID"].nunique() > 1).sum()) == 0),
        ("La suma de los pasos coincide: egresos depurados − excluidos = casos de estudio",
         len(df) - sum(p["quita"] for p in pasos) == info["casos"]),
        ("Todo egreso que no es caso de estudio tiene un motivo, y ningún caso de estudio lo tiene",
         bool((pd.isna(motivo) == restante).all())),
        ("Cada episodio asistencial tiene exactamente un alta final", info["episodios"]["un_final_por_episodio"]),
        ("Cada episodio asistencial pertenece a una sola persona", bool((episodio_persona == 1).all())),
        ("Los episodios de una persona no se solapan entre sí", info["episodios"]["episodios_sin_solape"]),
        ("Todo caso de estudio tiene persona, episodio y es el alta final de su episodio"
         if activo["E05"] else "Todo caso de estudio tiene persona y episodio",
         bool((df.loc[restante, "ID_EPISODIO"].notna() & (df.loc[restante, "ALTA_FINAL_EPISODIO"] | (not activo["E05"]))).all())),
    ]
    return nuevo, conservar, info


# ------------------------------------------------------------------ escritura
def escribir(nuevo: pd.DataFrame, conservar: np.ndarray) -> list[tuple[str, bool]]:
    """Copia la tabla integrada sin los duplicados y con las columnas nuevas, por grupos de filas."""
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    origen = pq.ParquetFile(ORIGEN)
    tipos = {"ID_PERSONA": pa.int64(), "ID_EPISODIO": pa.int64(), "N_EGRESOS_EPISODIO": pa.int16(),
             "MOTIVO_EXCLUSION": pa.string()}
    esquema = pa.schema([*[f for f in origen.schema_arrow if f.name not in QUITAR],
                         *[pa.field(c, tipos.get(c, pa.bool_())) for c in nuevo.columns[1:]]])
    temporal = DESTINO.with_suffix(".parquet.tmp")
    escritor, leidas, escritas = None, 0, 0
    try:
        for g in range(origen.num_row_groups):
            tabla = origen.read_row_group(g)
            filtro = conservar[leidas:leidas + tabla.num_rows]
            leidas += tabla.num_rows
            bloque = tabla.filter(pa.array(filtro)).drop_columns(QUITAR).to_pandas()
            extra = nuevo.iloc[escritas:escritas + len(bloque)]
            escritas += len(bloque)
            if not (bloque["ID_EGRESO"].to_numpy() == extra["ID_EGRESO"].to_numpy()).all():
                raise SystemExit("Las columnas nuevas no están alineadas con la tabla integrada.")
            bloque = pd.concat([bloque, extra.iloc[:, 1:].reset_index(drop=True)], axis=1)
            salida = pa.Table.from_pandas(bloque, schema=esquema, preserve_index=False)
            if escritor is None:
                escritor = pq.ParquetWriter(temporal, salida.schema, compression="zstd")
            escritor.write_table(salida)
            print(f"  grupo {g + 1} de {origen.num_row_groups}: {len(bloque):,} filas", flush=True)
            del tabla, bloque, salida
    finally:
        if escritor is not None:
            escritor.close()
    temporal.replace(DESTINO)

    # Relectura: filas, columnas originales intactas y columnas nuevas iguales a las calculadas.
    destino = pq.ParquetFile(DESTINO)
    originales = [f.name for f in origen.schema_arrow if f.name not in QUITAR]
    muestra = ["ID_EGRESO", "ID_PACIENTE", "FECHAALTA", "TIPOALTA", "DIAGNOSTICO1", "IR_29301_PESO", "PROCEDIMIENTO30"]
    antes = pq.read_table(ORIGEN, columns=muestra).filter(pa.array(conservar))
    despues = pq.read_table(DESTINO, columns=muestra)
    releido = pq.read_table(DESTINO, columns=list(nuevo.columns)).to_pandas()
    return [
        ("El archivo escrito tiene las filas esperadas", destino.metadata.num_rows == len(nuevo) == escritas),
        ("Las columnas originales conservan su nombre, orden y tipo de dato",
         [(f.name, f.type) for f in destino.schema_arrow][:len(originales)]
         == [(f.name, f.type) for f in origen.schema_arrow if f.name not in QUITAR]),
        (f"Contenido idéntico al de la tabla integrada en {len(muestra)} columnas de control",
         antes.equals(despues)),
        ("Las columnas nuevas releídas del archivo son iguales a las calculadas",
         all(releido[c].equals(nuevo[c].reset_index(drop=True)) for c in nuevo.columns)),
    ]


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 1) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def por_anio(d: dict) -> list[str]:
    return [fmt(d.get(a, 0)) for a in ANIOS] + [f"**{fmt(sum(d.get(a, 0) for a in ANIOS))}**"]


def escribir_reporte(info: dict, par: dict, criterios: list[dict]) -> None:
    anios_txt = [str(a) for a in ANIOS]
    pasos, per, ep = info["pasos"], info["personas"], info["episodios"]
    n_exactas, n_repetidos = sum(info["exactas_anio"].values()), sum(info["repetidos_anio"].values())
    salida = info["entrada"] - n_exactas - n_repetidos
    activos = [p for p in pasos if p["activo"]]
    inactivos = [p for p in pasos if not p["activo"]]
    e02_activo = next(p["activo"] for p in pasos if p["codigo"] == "E02")
    clave = info["misma_clave"]
    plazo = {0: "el mismo día del alta", 1: "el mismo día del alta o al día siguiente"}.get(
        par["traslado_dias_max"], f"el mismo día del alta o hasta {par['traslado_dias_max']} días después")
    cont, contig = ep["continuaciones"], ep["contiguos"]
    con_varios = sum(n for k, n in ep["tamanos"].items() if k > 1)
    derivados = sum(ep["derivados"].values())
    ruta = ACTIVIDAD.name

    partes = [
        "# Depuración de la tabla integrada (actividad 2.2, script 08)",
        f"Generado por `{ruta}/scripts/08_depurar.py`. Entrada: `data/processed/{ORIGEN.name}`. Salida: "
        f"`data/processed/{DESTINO.name}`. Criterios: `{ruta}/reglas/{ARCHIVO_CRITERIOS.name}`; umbrales: "
        f"`{ruta}/reglas/{ARCHIVO_PARAMETROS.name}`. Las decisiones están en `{ruta}/bitacora.md`.",
        "Cada egreso puede cumplir dos papeles: **caso de estudio** (el alta desde la que se cuentan los días hasta un "
        "posible reingreso) y **reingreso** de un alta anterior. Solo se eliminan los duplicados. Las exclusiones son "
        "marcas (columnas `EXC_*`): un egreso que no sirve como caso de estudio, por ejemplo un fallecido, puede seguir "
        "contando como el reingreso de un alta anterior.",
        "## 1. Resultado",
        tabla_md(["", "Egresos"], [
            ["Tabla integrada", fmt(info["entrada"])],
            ["Copias exactas eliminadas", fmt(n_exactas)],
            ["Registros repetidos eliminados", fmt(n_repetidos)],
            ["**Tabla depurada**", f"**{fmt(salida)}**"],
            ["Casos de estudio (`ES_CASO_ESTUDIO`)", f"{fmt(info['casos'])} ({pct(info['casos'], salida)})"],
            ["Pueden contar como reingreso (`PUEDE_SER_REINGRESO`)", f"{fmt(info['reingreso'])} ({pct(info['reingreso'], salida)})"],
        ]),
        f"La tabla depurada tiene {info['columnas']} columnas: las de la tabla integrada, menos `DUP_EXACTO` y `DUP_CLAVE`, "
        "más las columnas nuevas de la sección 9.",

        "## 2. Duplicados eliminados",
        "Se eliminan las copias exactas. Cuando varios registros comparten paciente, hospital, fecha de ingreso, fecha de "
        "alta, sexo y fecha de nacimiento, se conserva el más completo: el que tiene más diagnósticos; si empatan, más "
        "procedimientos; luego mayor peso GRD; luego el primero del archivo (bitácora D15).",
        tabla_md(["", *anios_txt, "Total"], [
            ["Tabla integrada", *por_anio(info["entrada_anio"])],
            ["Copias exactas", *por_anio(info["exactas_anio"])],
            ["Registros repetidos", *por_anio(info["repetidos_anio"])],
            ["Tabla depurada", *por_anio(info["salida_anio"])],
        ]),
        f"No se fusionan {fmt(clave['registros'])} registros, en {fmt(clave['grupos'])} grupos, que comparten paciente, "
        "hospital y fechas pero difieren en el sexo o en la fecha de nacimiento. Según la regla de la sección 3, en "
        f"{fmt(clave['distintas'])} grupos son personas distintas y en {fmt(clave['sin_persona'])} el identificador no tiene "
        f"persona asignada (genérico). En los otros {fmt(clave['misma'])} la regla los considera una misma persona: no se "
        "borran, pero quedan unidos en un mismo episodio asistencial (sección 4), de modo que solo uno es caso de estudio "
        "y ninguno cuenta como reingreso del otro.",

        "## 3. Personas",
        "Un mismo identificador puede corresponder a más de una persona. Dos egresos con el mismo identificador se "
        f"consideran de personas distintas cuando sus fechas de nacimiento difieren en más de {par['persona_dias_fnac']} días"
        + (", salvo que coincidan en el día y el mes (error de digitación en el año)" if par["persona_mismo_dia_mes"] else "")
        + ". El sexo no se usa. `ID_PERSONA` es el identificador seguido de dos dígitos con el número de persona "
        "(01 la de más edad, 02 la siguiente).",
        tabla_md(["", "Cantidad"], [
            ["Identificadores de paciente", fmt(per["identificadores"])],
            ["Con más de una combinación de sexo y fecha de nacimiento",
             f"{fmt(per['con_varias_combinaciones'])} ({pct(per['con_varias_combinaciones'], per['identificadores'], 2)})"],
            ["Egresos de esos identificadores", fmt(per["egresos_varias_combinaciones"])],
            [f"Identificadores genéricos ({par['id_generico_min_personas']} combinaciones o más)", fmt(per["genericos"])],
            ["Egresos con identificador genérico", fmt(per["egresos_genericos"])],
            ["Combinaciones del identificador genérico más usado", fmt(per["mayor_generico"])],
            ["Identificadores con una misma fecha de nacimiento registrada con más de un sexo (no se separan)",
             fmt(per["ids_mismo_nacimiento_otro_sexo"])],
            ["**Personas**", f"**{fmt(per['personas'])}**"],
        ]),
        ("Los identificadores genéricos quedan sin persona asignada (criterio E02). " if e02_activo else "")
        + f"Hay {fmt(per['ids_varias_fechas'])} identificadores{' no genéricos' if e02_activo else ''} con más de una fecha de nacimiento. "
        f"Los {fmt(per['ids_dos_fechas'])} que tienen exactamente dos se resuelven así:",
        tabla_md(["Las dos fechas de nacimiento…", "Identificadores", "Resultado"], [
            [f"difieren en hasta {par['persona_dias_fnac']} días", fmt(per["dos_cerca"]), "Una persona (error de digitación)"],
            ["difieren en más, pero coinciden en día y mes", fmt(per["dos_error_anio"]), "Una persona (error en el año)"],
            ["difieren en más", fmt(per["dos_distintas"]), "Dos personas"],
        ]),
        f"Otros {fmt(per['ids_tres_o_mas_fechas'])} identificadores tienen tres fechas o más. Identificadores según el número "
        "de personas que resultan: "
        + "; ".join(f"{k} persona{'s' if k > 1 else ''}: {fmt(v)}" for k, v in per["ids_por_personas"].items())
        + f". En {fmt(per['madre_hijo'])} de los identificadores con dos personas, la menor tiene menos de un año en su primer "
        "ingreso y la otra le lleva más de 12 años: es el patrón de un recién nacido registrado con el identificador de su madre."
        + (f" Quedan {fmt(per['con_id_sin_persona'])} egresos con identificador y sin persona asignable (sin fecha de nacimiento "
           "en un identificador con varias personas); se cuentan en el criterio E01." if per["con_id_sin_persona"] else ""),

        "## 4. Episodios asistenciales",
        "Un traslado no es un reingreso: es la continuación de la misma hospitalización. Los egresos de una persona se unen "
        "en un mismo episodio asistencial cuando el segundo ingresa antes del alta del primero, o ingresa en otro hospital "
        + plazo
        + (", siempre que el traslado conste en el tipo de alta o en la procedencia" if par["traslado_exige_marca"] else "")
        + ". Solo el alta final del episodio puede ser caso de estudio, y un egreso que continúa un episodio no cuenta como reingreso.",
        tabla_md(["", "Cantidad"], [
            ["Egresos que se pueden seguir (con persona y fechas, sin los criterios que afectan a ambos papeles)", fmt(ep["seguibles"])],
            ["Episodios asistenciales", fmt(ep["episodios"])],
            ["Episodios con más de un egreso", fmt(con_varios)],
            *[[f"  de {k} egresos" if k < 5 else "  de 5 egresos o más", fmt(n)] for k, n in ep["tamanos"].items() if k > 1],
            ["Egresos que continúan un episodio", fmt(sum(cont.values()))],
            ["  porque ingresan antes del alta anterior (solapados)", fmt(cont[SOLAPADO])],
            ["  porque ingresan en otro hospital el mismo día del alta", fmt(cont[OTRO_MISMO_DIA])],
            ["  porque ingresan en otro hospital en los días siguientes", fmt(cont[OTRO_DIA_SIGUIENTE])],
            ["  porque repiten hospital y fechas del egreso anterior", fmt(cont[MISMA_ESTADIA])],
        ]),
        "Respaldo de la regla: proporción de los ingresos en otro hospital que además tienen una marca explícita de traslado "
        "(el alta anterior es una derivación o el ingreso declara que procede de otro hospital).",
        tabla_md(["Ingreso en otro hospital", "Egresos", "Con marca de traslado", "%"], [
            ["El mismo día del alta", fmt(contig["mismo_dia"]), fmt(contig["mismo_dia_marca"]), pct(contig["mismo_dia_marca"], contig["mismo_dia"])],
            ["En los días siguientes", fmt(contig["dia_siguiente"]), fmt(contig["dia_siguiente_marca"]), pct(contig["dia_siguiente_marca"], contig["dia_siguiente"])],
        ]),
        "El tipo de alta no basta para reconocer un traslado. Egresos con alta por derivación a otro hospital y cuántos "
        "tienen la continuación visible en la base (el resto fue a establecimientos que no reportan GRD):",
        tabla_md(["", *anios_txt, "Total"], [
            ["Alta por derivación a otro hospital", *por_anio(ep["derivados"])],
            ["Con continuación visible", *por_anio(ep["derivados_con_continuacion"])],
            ["%", *[pct(ep["derivados_con_continuacion"][a], ep["derivados"][a]) for a in ANIOS],
             pct(sum(ep["derivados_con_continuacion"].values()), derivados)],
        ]),
        f"Un ingreso en el mismo hospital el mismo día del alta no es un traslado: abre un episodio nuevo y puede contar como "
        f"reingreso ({fmt(ep['mismo_hospital_mismo_dia'])} egresos).",

        "## 5. Criterios de exclusión, paso a paso",
        "Los criterios se aplican en el orden de la tabla. **Cumplen el criterio**: egresos de la tabla depurada que lo "
        "cumplen, sin considerar los demás. **Quita en este paso**: los que lo cumplen entre los que quedaban. Los criterios "
        "de papel *Ambos* dejan al egreso fuera como caso de estudio y como reingreso; los de papel *Caso*, solo como caso de estudio.",
        tabla_md(["Paso", "Criterio", "Papel", "Activo", "Cumplen el criterio", "Quita en este paso", "Quedan"], [
            ["", "Tabla integrada", "", "", "", "", fmt(info["entrada"])],
            ["", "Copias exactas (se eliminan)", "", "", fmt(n_exactas), fmt(n_exactas), fmt(info["entrada"] - n_exactas)],
            ["", "Registros repetidos (se eliminan)", "", "", fmt(n_repetidos), fmt(n_repetidos), fmt(salida)],
            *[[p["codigo"], p["criterio"], "Ambos" if p["papel"] == "AMBOS" else "Caso", "Sí" if p["activo"] else "No",
               fmt(p["cumplen"]), fmt(p["quita"]) if p["activo"] else "—", fmt(p["quedan"])] for p in pasos],
            ["", "**Casos de estudio**", "", "", "", "", f"**{fmt(info['casos'])}**"],
        ]),
        "Egresos que quita cada paso, por año del archivo:",
        tabla_md(["Paso", *anios_txt, "Total"], [
            ["Tabla integrada", *por_anio(info["entrada_anio"])],
            ["Copias exactas", *por_anio(info["exactas_anio"])],
            ["Registros repetidos", *por_anio(info["repetidos_anio"])],
            *[[p["codigo"], *por_anio(p["quita_anio"])] for p in activos],
            ["**Casos de estudio**", *por_anio(info["casos_anio"])],
            ["% de la tabla depurada", *[pct(info["casos_anio"].get(a, 0), info["salida_anio"][a]) for a in ANIOS], pct(info["casos"], salida)],
        ]),
    ]
    if inactivos:
        partes += [
            "Criterios desactivados: no quitan ningún egreso. La columna indica cuántos casos de estudio quitaría cada uno "
            "si se activara (cambiando `NO` por `SI` en la tabla de criterios).",
            tabla_md(["Código", "Criterio", "Casos de estudio que quitaría", "%"],
                     [[p["codigo"], p["criterio"], fmt(p["quitaria"]), pct(p["quitaria"], info["casos"])] for p in inactivos]),
        ]
    partes += [
        "E07 y E05 se complementan: los egresos derivados a otro hospital cuya continuación está en la base ya quedan "
        "fuera en E05, porque no son el alta final de su episodio; E07 quita los derivados cuya continuación no se ve. "
        "Detalle de E09: " + "; ".join(f"{k}: {fmt(v)}" for k, v in info["sin_grd"].items())
        + ". Detalle de E10 (un egreso puede cumplir más de una condición): "
        + "; ".join(f"{k.lower()}: {fmt(v)}" for k, v in info["faltantes"].items()) + ".",

        "## 6. Egresos que pueden contar como reingreso",
        "Un egreso puede contar como el reingreso de un alta anterior si se puede seguir (tiene persona y fechas, y no cumple "
        "ningún criterio activo de papel *Ambos*) y además abre un episodio asistencial, es decir, no es la continuación de un traslado.",
        tabla_md(["", "Egresos"], [
            ["Tabla depurada", fmt(salida)],
            ["No se pueden seguir", fmt(info["no_seguibles"])],
            ["Continúan un episodio (traslados)", fmt(info["continuan"])],
            ["**Pueden contar como reingreso**", f"**{fmt(info['reingreso'])}**"],
        ]),
        tabla_md(["", *anios_txt, "Total"], [["Pueden contar como reingreso", *por_anio(info["reingreso_anio"])]]),

        "## 7. Composición de los casos de estudio",
        tabla_md(["Tipo de alta", "Casos de estudio", "%"],
                 [[k if isinstance(k, str) else "(sin dato)", fmt(v), pct(v, info["casos"], 2)] for k, v in info["casos_tipoalta"].items()]),
        tabla_md(["Tipo de actividad", "Casos de estudio", "%"],
                 [[k if isinstance(k, str) else "(sin dato)", fmt(v), pct(v, info["casos"], 2)] for k, v in info["casos_actividad"].items()]),
        tabla_md(["Tipo de ingreso", "Casos de estudio", "%"],
                 [[k if isinstance(k, str) else "(sin dato)", fmt(v), pct(v, info["casos"], 2)] for k, v in info["casos_ingreso"].items()]),

        "## 8. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", v, d] for k, (v, d) in par["descripcion"].items()]),
        "Cierre de cada bloque de identificador: " + "; ".join(f"{b}, {f:%d-%m-%Y}" for b, f in CIERRE_BLOQUE.items()) + ".",

        "## 9. Columnas nuevas",
        tabla_md(["Columna", "Contenido"], [
            ["`ID_PERSONA`", f"Identificador de la persona: `ID_PACIENTE` × {FACTOR_PERSONA} + número de persona. Sin dato en los "
                             "egresos sin identificador o con identificador genérico."],
            ["`ID_EPISODIO`", "Episodio asistencial: `ID_EGRESO` del primer egreso del episodio. Sin dato en los egresos que no se pueden seguir."],
            ["`N_EGRESOS_EPISODIO`", "Número de egresos del episodio asistencial."],
            ["`CONTINUA_EPISODIO`", "Verdadero si el egreso continúa un episodio abierto por un egreso anterior (traslado)."],
            ["`ALTA_FINAL_EPISODIO`", "Verdadero si el egreso es el alta final de su episodio asistencial."],
            *[[f"`{c['columna']}`", f"{c['codigo']}. {c['criterio']}."] for c in criterios],
            ["`MOTIVO_EXCLUSION`", "Código del primer criterio activo que excluye al egreso como caso de estudio. Sin dato en los casos de estudio."],
            ["`ES_CASO_ESTUDIO`", "Verdadero si el egreso no cumple ningún criterio activo."],
            ["`PUEDE_SER_REINGRESO`", "Verdadero si el egreso puede contar como reingreso de un alta anterior (sección 6)."],
        ]),
        "Las columnas `EXC_*` se calculan siempre, también para los criterios desactivados.",

        "## 10. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),
    ]
    salida_md = DIR_REPORTS / "08_depuracion.md"
    salida_md.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida_md}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par, criterios = cargar_parametros(), cargar_criterios()
    print("Depurando...", flush=True)
    nuevo, conservar, info = depurar(par, criterios)
    print(f"  {len(nuevo):,} egresos, {info['casos']:,} casos de estudio ({time.time() - inicio:.0f} s)", flush=True)
    print("Escribiendo...", flush=True)
    info["verificaciones"] += escribir(nuevo, conservar)
    info["columnas"] = pq.ParquetFile(DESTINO).metadata.num_columns
    escribir_reporte(info, par, criterios)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
