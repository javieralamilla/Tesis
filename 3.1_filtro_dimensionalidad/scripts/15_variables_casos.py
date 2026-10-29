"""Variables de los casos de estudio (actividad 3.1, script 15).

Etapa 3 de la propuesta, paso 2. Para cada caso de estudio del conjunto de desarrollo arma las variables que no
pasan por el filtro de códigos: las administrativas y demográficas de la propuesta, la historia de 12 meses con su
marca de ventana cortada (D42 y D44 de la bitácora de la 2.3), el índice de comorbilidad y las demás columnas del
CMBD que describen al paciente o su hospitalización. Ninguna se elige ni se descarta por su relación con el
reingreso: la propuesta deja la selección a los modelos (bitácora de la 3.1, D46 a D49).

  1. Parámetros y reglas. Los umbrales están en reglas/parametros.csv; los grupos de previsión, las regiones y los
     códigos de comorbilidad, en tablas aparte de reglas/. La regla de «no planificado» se lee de los parámetros de
     la 2.2, para que sea la misma del etiquetado (D20 y D33).
  2. Versión. Comprueba que el conjunto de desarrollo sea el de la última versión registrada de la partición. No
     abre el conjunto de prueba.
  3. Episodios. Reúne los egresos de cada episodio asistencial (D19): su ingreso índice, su alta final, cuántos
     hospitales tiene, si pasó por una UCI o UTI, su intervención y si empezó con un ingreso no planificado.
  4. Variables del caso. Las que salen del egreso del caso de estudio y las que describen todo el episodio.
  5. Historia de 12 meses. Cuenta lo que terminó en los 365 días antes del ingreso índice, sin el propio episodio
     (D42), y marca los casos cuya ventana empieza antes del inicio de su bloque de identificador (D44).
  6. Índice de comorbilidad. Elixhauser con los códigos de Quan et al. (2005); Charlson con los pesos de Quan et al.
     (2011) se calcula siempre, como comparación.
  7. Valores poco frecuentes. En las columnas del CMBD tomadas tal cual, los valores con menos de 100 casos pasan a
     OTRO.
  8. Salida. data/processed/variables_casos.parquet (una fila por caso de estudio) y reportes/15_variables_casos.md.

Las tasas de reingreso del reporte son solo descriptivas: ninguna variable se construye con las variables objetivo.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\scripts\\15_variables_casos.py
"""

import csv
import hashlib
import re
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
DESTINO = RAIZ / "data" / "processed" / "variables_casos.parquet"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
DIR_REGLAS = ACTIVIDAD / "reglas"
ARCHIVO_PARAMETROS = DIR_REGLAS / "parametros.csv"
ARCHIVO_COMORBILIDAD = DIR_REGLAS / "comorbilidad_quan2005.csv"
ARCHIVO_PREVISION = DIR_REGLAS / "prevision_grupos.csv"
ARCHIVO_REGIONES = DIR_REGLAS / "provincia_region.csv"
PARAMETROS_22 = RAIZ / "2.2_depuracion_etiquetado" / "reglas" / "parametros.csv"
REPORTE = ACTIVIDAD / "reportes" / "15_variables_casos.md"

PARAMETROS = ["ventana_historia_dias", "inicio_bloques", "dias_sin_hospitalizacion", "indice_comorbilidad",
              "casos_minimos_categoria", "servicios_criticos", "servicios_criticos_excluidos", "etnia_sin_pueblo",
              "nacionalidad_local"]
PARAMETROS_REGLA_22 = ["ingresos_no_planificados", "grd_parto", "diagnosticos_sesion"]  # regla de D20 y D33
INDICES = {"ELIXHAUSER": "número de condiciones de Elixhauser presentes (códigos de Quan et al., 2005)",
           "CHARLSON": "puntaje de Charlson con los pesos de Quan et al. (2011)"}
DIAGNOSTICOS = [f"DIAGNOSTICO{i}" for i in range(1, 36)]
PROCEDIMIENTOS = [f"PROCEDIMIENTO{i}" for i in range(1, 31)]
SERVICIOS = ["SERVICIOINGRESO", *[f"SERVICIOTRASLADO{i}" for i in range(1, 10)], "SERVICIOALTA"]
SIN_DATO, OTRO, SIN_INTERVENCION = "SIN DATO", "OTRO", "SIN INTERVENCIÓN"
BASE = 1 << 20  # más que cualquier fecha contada en días desde 1970 (unos 20.000): permite ordenar por persona y día

# Las 30 variables, en el orden de la tabla de salida: columna, decisión de la bitácora y qué contiene
VARIABLES = [
    ("EDAD", "D46", "Edad en años, con decimales, al ingreso del propio egreso"),
    ("SEXO", "D46", "Sexo, tal cual"),
    ("PREVISION_GRUPO", "D46", "Previsión en 8 grupos (reglas/prevision_grupos.csv)"),
    ("REGION", "D46", "Región de residencia, desde la provincia (reglas/provincia_region.csv)"),
    ("TIPO_INGRESO", "D46", "Tipo de ingreso del propio egreso, tal cual"),
    ("ESTADIA", "D46", "Días desde el ingreso índice (el que abre el episodio) hasta el alta del caso"),
    ("CDM", "D46", "Categoría diagnóstica mayor, tal cual"),
    ("PESO_GRD", "D46", "Peso del GRD; el peso 0 queda sin dato"),
    ("HOSP_PREVIAS", "D47", "Hospitalizaciones de la misma persona (episodios) terminadas en la ventana"),
    ("HOSP_PREVIAS_NO_PLANIF", "D47", "De ellas, las que empezaron con un ingreso no planificado (D20 y D33)"),
    ("DIAS_ULTIMA_HOSP", "D47", "Días desde el alta de la última hospitalización de la ventana hasta el ingreso índice"),
    ("CMA_PREVIAS", "D47", "Cirugías mayores ambulatorias terminadas en la ventana"),
    ("SESIONES_PREVIAS", "D47", "Sesiones de tratamiento (diagnóstico principal Z51) terminadas en la ventana"),
    ("VENTANA_CORTADA", "D47", "1 si la ventana empieza antes del inicio del bloque del identificador (D42 y D44)"),
    ("INDICE_COMORBILIDAD", "D48", "Índice de comorbilidad con todos los diagnósticos del egreso"),
    ("TIPO_ALTA", "D49", "Destino al alta, tal cual"),
    ("SEVERIDAD", "D49", "Nivel de severidad del GRD (1 a 3; es el último dígito del código)"),
    ("RIESGO_MORTALIDAD", "D49", "Nivel de riesgo de mortalidad del GRD (1 a 3)"),
    ("ESPECIALIDAD_INTERVENCION", "D49", "Especialidad de la intervención del episodio, o SIN INTERVENCIÓN"),
    ("UCI_UTI", "D49", "1 si algún egreso del episodio pasó por una unidad de cuidados intensivos o intermedios"),
    ("TRASLADO", "D49", "1 si el episodio pasó por más de un hospital (D19)"),
    ("N_DIAGNOSTICOS", "D49", "Diagnósticos distintos del egreso"),
    ("N_PROCEDIMIENTOS", "D49", "Procedimientos distintos del egreso"),
    ("ESPECIALIDAD", "D49", "Especialidad médica del episodio, tal cual"),
    ("TIPO_PROCEDENCIA", "D49", "De dónde llega el paciente, tal cual"),
    ("SERVICIO_INGRESO", "D49", "Servicio clínico de ingreso, tal cual"),
    ("SERVICIO_ALTA", "D49", "Servicio clínico de alta, tal cual"),
    ("PUEBLO_ORIGINARIO", "D49", "SÍ si la etnia nombra un pueblo originario; NO si dice NINGUNO u OTRO"),
    ("NACIONALIDAD_EXTRANJERA", "D49", "SÍ si la nacionalidad no es chilena"),
    ("HOSPITAL", "D49", "Código del hospital del egreso; su uso como predictora lo decide la revisión del profesor guía"),
]
AGRUPADAS = ["TIPO_ALTA", "ESPECIALIDAD_INTERVENCION", "ESPECIALIDAD", "TIPO_PROCEDENCIA", "SERVICIO_INGRESO",
             "SERVICIO_ALTA", "HOSPITAL"]                                  # columnas del CMBD tomadas tal cual (paso 7)
CATEGORIAS_D46 = ["SEXO", "PREVISION_GRUPO", "REGION", "TIPO_INGRESO", "CDM"]  # se revisa que no tengan valores raros


# ------------------------------------------------------------------ 1. parámetros y reglas, 2. versión
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
    regla = {fila["parametro"]: fila["valor"].strip() for fila in leer_csv(PARAMETROS_22)}

    def lista(texto: str) -> list[str]:
        return [v.strip() for v in texto.split("|") if v.strip()]

    par = {"ventana": int(valor["ventana_historia_dias"]), "sin_hosp": int(valor["dias_sin_hospitalizacion"]),
           "indice": valor["indice_comorbilidad"].upper(), "minimo": int(valor["casos_minimos_categoria"]),
           "criticos": lista(valor["servicios_criticos"]), "criticos_excluidos": lista(valor["servicios_criticos_excluidos"]),
           "sin_pueblo": lista(valor["etnia_sin_pueblo"]), "local": valor["nacionalidad_local"],
           "inicio_bloques": {b.split("=")[0].strip(): date.fromisoformat(b.split("=")[1].strip())
                              for b in lista(valor["inicio_bloques"])},
           "no_planificados": lista(regla["ingresos_no_planificados"]), "grd_parto": lista(regla["grd_parto"]),
           "sesiones": lista(regla["diagnosticos_sesion"])}
    if par["indice"] not in INDICES:
        raise SystemExit(f"indice_comorbilidad: se esperaba {' o '.join(INDICES)} y dice '{valor['indice_comorbilidad']}'.")
    if par["sin_hosp"] <= par["ventana"]:
        raise SystemExit("dias_sin_hospitalizacion debe ser mayor que ventana_historia_dias: si no, se confunde con una hospitalización.")
    par["descripcion"] = {nombre: (valor[nombre], filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    par["descripcion_22"] = {nombre: regla[nombre] for nombre in PARAMETROS_REGLA_22}
    return par


def cargar_reglas() -> dict:
    """Las tres tablas de reglas: grupos de previsión, región de cada provincia y códigos de comorbilidad."""
    comorbilidad = pd.DataFrame(leer_csv(ARCHIVO_COMORBILIDAD))
    comorbilidad["peso"] = comorbilidad["peso"].astype(int)
    return {"prevision": {f["prevision"]: f["grupo"] for f in leer_csv(ARCHIVO_PREVISION)},
            "region": {f["provincia"]: f["region"] for f in leer_csv(ARCHIVO_REGIONES)},
            "comorbilidad": comorbilidad}


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


def a_dias(fechas: pd.Series) -> np.ndarray:
    """Cada fecha como número de días desde el 1 de enero de 1970: así se resta y se compara rápido."""
    return fechas.to_numpy(dtype="datetime64[ms]").astype("datetime64[D]").astype("int64")


# ------------------------------------------------------------------ 3. episodios
def leer_egresos() -> pd.DataFrame:
    """Todos los egresos de desarrollo que forman parte de un episodio asistencial (D19), sean o no casos de estudio.
    Los que no tienen episodio no se pueden seguir (sin identificador o sin fechas) o son los E04 de 2019, que la
    decisión 2 deja fuera de la historia."""
    columnas = ["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "EXC_ACTIVIDAD_2019", "EXC_CMA", "EXC_SESION",
                "COD_HOSPITAL", "FECHA_INGRESO", "FECHAALTA", "TIPO_INGRESO", "IR_29301_COD_GRD", "DIAGNOSTICO1",
                "ESPECIALIDADINTERVENCION", *SERVICIOS]
    e = pd.read_parquet(DESARROLLO, columns=columnas)
    e = e[e["ID_EPISODIO"].notna()].reset_index(drop=True)
    e["ID_EPISODIO"] = e["ID_EPISODIO"].astype("int64")
    e["ID_PERSONA"] = e["ID_PERSONA"].astype("int64")
    e["INICIO"], e["FIN"] = a_dias(e["FECHA_INGRESO"]), a_dias(e["FECHAALTA"])
    return e


def unidad_critica(e: pd.DataFrame, par: dict) -> np.ndarray:
    """Verdadero si el servicio de ingreso, alguno de los traslados internos o el de alta es una UCI o una UTI."""
    incluir = "|".join(re.escape(t) for t in par["criticos"])
    excluir = "|".join(re.escape(t) for t in par["criticos_excluidos"])
    marca = np.zeros(len(e), dtype=bool)
    for columna in SERVICIOS:
        texto = e[columna].str.upper()
        es = texto.str.contains(incluir, regex=True) & ~texto.str.contains(excluir, regex=True)
        marca |= es.fillna(False).to_numpy(dtype=bool)
    return marca


def armar_episodios(e: pd.DataFrame, par: dict) -> pd.DataFrame:
    """Una fila por episodio asistencial, con lo que describe a toda la hospitalización."""
    e["CRITICA"] = unidad_critica(e, par)
    e["HOSPITALIZACION"] = ~(e["EXC_CMA"] | e["EXC_SESION"])  # ni cirugía mayor ambulatoria ni sesión Z51
    g = e.groupby("ID_EPISODIO", sort=True)
    epi = pd.DataFrame({"ID_PERSONA": g["ID_PERSONA"].first(), "PERSONAS": g["ID_PERSONA"].nunique(),
                        "INICIO": g["INICIO"].min(), "FIN": g["FIN"].max(), "EGRESOS": g.size(),
                        "HOSPITALES": g["COD_HOSPITAL"].nunique(), "CRITICA": g["CRITICA"].any(),
                        "HOSPITALIZACION": g["HOSPITALIZACION"].any()})

    # El ingreso que abre el episodio (el egreso cuyo ID_EGRESO es el ID_EPISODIO) dice si fue no planificado, con la
    # misma regla y en el mismo orden que el etiquetado (D20 y D33): un parto o una sesión no cuentan, aunque hayan
    # entrado por urgencia; cuentan los ingresos por urgencia u obstétricos.
    abre = e[e["ID_EGRESO"] == e["ID_EPISODIO"]].set_index("ID_EPISODIO")
    parto = abre["IR_29301_COD_GRD"].str.startswith(tuple(par["grd_parto"])).fillna(False).astype(bool)
    sesion = abre["DIAGNOSTICO1"].str.startswith(tuple(par["sesiones"])).fillna(False).astype(bool)
    no_planificado = abre["TIPO_INGRESO"].isin(par["no_planificados"]) & ~parto & ~sesion
    epi["NO_PLANIFICADO"] = no_planificado.reindex(epi.index, fill_value=False).astype(bool)
    epi["TIENE_APERTURA"] = epi.index.isin(abre.index)

    # La intervención del episodio: la del egreso del caso; si no tiene, la del último tramo anterior que la tenga.
    con = e.loc[e["ESPECIALIDADINTERVENCION"].notna(), ["ID_EPISODIO", "FIN", "ES_CASO_ESTUDIO", "ESPECIALIDADINTERVENCION"]]
    con = con.sort_values(["ID_EPISODIO", "FIN", "ES_CASO_ESTUDIO"])  # a igual fecha de alta, el caso queda al final
    epi["INTERVENCION"] = con.groupby("ID_EPISODIO")["ESPECIALIDADINTERVENCION"].last().reindex(epi.index)
    return epi


# ------------------------------------------------------------------ 4. variables del caso
def leer_casos() -> pd.DataFrame:
    columnas = ["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "BLOQUE_ID", "ANIO_ARCHIVO", "COD_HOSPITAL", "SEXO",
                "FECHA_NACIMIENTO", "FECHA_INGRESO", "FECHAALTA", "ETNIA", "NACIONALIDAD", "PREVISION", "PROVINCIA",
                "TIPO_PROCEDENCIA", "TIPO_INGRESO", "ESPECIALIDAD_MEDICA", "SERVICIOINGRESO", "SERVICIOALTA", "TIPOALTA",
                "ESPECIALIDADINTERVENCION", "CDM", "IR_29301_PESO", "IR_29301_SEVERIDAD", "IR_29301_MORTALIDAD", "REING_30D",
                *DIAGNOSTICOS, *PROCEDIMIENTOS]
    c = pd.read_parquet(DESARROLLO, columns=columnas, filters=[("ES_CASO_ESTUDIO", "==", True)]).reset_index(drop=True)
    c["ID_EPISODIO"] = c["ID_EPISODIO"].astype("int64")
    c["ID_PERSONA"] = c["ID_PERSONA"].astype("int64")
    return c


def tabla_larga(c: pd.DataFrame, columnas: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Fila del caso y código sin punto (E11.9 → E119) de cada código del caso, sin repetir un código en un caso."""
    partes = [pd.DataFrame({"FILA": c[col].dropna().index, "CODIGO": c[col].dropna().str.replace(".", "", regex=False)})
              for col in columnas]
    largo = pd.concat(partes, ignore_index=True).drop_duplicates()
    return largo["FILA"].to_numpy(), largo["CODIGO"].to_numpy(dtype=object)


def contar_por_caso(filas: np.ndarray, n: int) -> np.ndarray:
    return np.bincount(filas, minlength=n).astype("int16")


def variables_caso(c: pd.DataFrame, epi: pd.DataFrame, par: dict, reglas: dict) -> tuple[pd.DataFrame, dict]:
    ep = epi.loc[c["ID_EPISODIO"].to_numpy()]   # el episodio de cada caso, en el orden de los casos
    v = pd.DataFrame({"ID_EGRESO": c["ID_EGRESO"].to_numpy()})
    info = {}

    # Decisión 1 (D46): las variables administrativas y demográficas de la propuesta
    v["EDAD"] = ((c["FECHA_INGRESO"] - c["FECHA_NACIMIENTO"]).dt.days / 365.25).to_numpy()
    v["SEXO"] = c["SEXO"].fillna(SIN_DATO).to_numpy()
    v["PREVISION_GRUPO"] = c["PREVISION"].map(reglas["prevision"]).where(c["PREVISION"].notna(), SIN_DATO).to_numpy()
    v["REGION"] = c["PROVINCIA"].map(reglas["region"]).where(c["PROVINCIA"].notna(), SIN_DATO).to_numpy()
    v["TIPO_INGRESO"] = c["TIPO_INGRESO"].fillna(SIN_DATO).to_numpy()
    v["ESTADIA"] = (a_dias(c["FECHAALTA"]) - ep["INICIO"].to_numpy()).astype("int32")
    v["CDM"] = c["CDM"].to_numpy()
    v["PESO_GRD"] = c["IR_29301_PESO"].where(c["IR_29301_PESO"] > 0).to_numpy()
    info["sin_mapa"] = {"previsión": sorted(set(c.loc[c["PREVISION"].notna() & v["PREVISION_GRUPO"].isna().to_numpy(), "PREVISION"])),
                        "provincia": sorted(set(c.loc[c["PROVINCIA"].notna() & v["REGION"].isna().to_numpy(), "PROVINCIA"]))}
    info["estadia_propia"] = (a_dias(c["FECHAALTA"]) - a_dias(c["FECHA_INGRESO"])).astype("int32")
    info["peso_cero"] = int((c["IR_29301_PESO"] <= 0).sum())

    # Decisión 4 (D49): las demás columnas del CMBD, del egreso del caso o de todo el episodio
    v["TIPO_ALTA"] = c["TIPOALTA"].fillna(SIN_DATO).to_numpy()
    v["SEVERIDAD"] = c["IR_29301_SEVERIDAD"].to_numpy(dtype="int8")
    v["RIESGO_MORTALIDAD"] = c["IR_29301_MORTALIDAD"].to_numpy(dtype="int8")
    v["ESPECIALIDAD_INTERVENCION"] = ep["INTERVENCION"].fillna(SIN_INTERVENCION).to_numpy()
    v["UCI_UTI"] = ep["CRITICA"].to_numpy(dtype="int8")
    v["TRASLADO"] = (ep["HOSPITALES"].to_numpy() > 1).astype("int8")
    filas_dx, codigos_dx = tabla_larga(c, DIAGNOSTICOS)
    filas_px, _ = tabla_larga(c, PROCEDIMIENTOS)
    v["N_DIAGNOSTICOS"] = contar_por_caso(filas_dx, len(c))
    v["N_PROCEDIMIENTOS"] = contar_por_caso(filas_px, len(c))
    v["ESPECIALIDAD"] = c["ESPECIALIDAD_MEDICA"].fillna(SIN_DATO).to_numpy()
    v["TIPO_PROCEDENCIA"] = c["TIPO_PROCEDENCIA"].fillna(SIN_DATO).to_numpy()
    v["SERVICIO_INGRESO"] = c["SERVICIOINGRESO"].fillna(SIN_DATO).to_numpy()
    v["SERVICIO_ALTA"] = c["SERVICIOALTA"].fillna(SIN_DATO).to_numpy()
    v["PUEBLO_ORIGINARIO"] = np.where(c["ETNIA"].isna(), SIN_DATO, np.where(c["ETNIA"].isin(par["sin_pueblo"]), "NO", "SÍ"))
    v["NACIONALIDAD_EXTRANJERA"] = np.where(c["NACIONALIDAD"].isna(), SIN_DATO,
                                            np.where(c["NACIONALIDAD"] == par["local"], "NO", "SÍ"))
    v["HOSPITAL"] = c["COD_HOSPITAL"].to_numpy()
    info["intervencion_de_tramo"] = int((c["ESPECIALIDADINTERVENCION"].isna() & ep["INTERVENCION"].notna().to_numpy()).sum())
    info["uci_de_tramo"] = None  # se completa en main con los egresos
    return v, {**info, "filas_dx": filas_dx, "codigos_dx": codigos_dx}


# ------------------------------------------------------------------ 5. historia de 12 meses
def contar_en_ventana(p_eventos, dia_eventos, p_casos, desde, hasta) -> np.ndarray:
    """Cuántos eventos de la misma persona terminaron entre «desde» y «hasta», ambos días incluidos.
    Cada evento se resume en un número (persona · BASE + día) y se ordenan: los de una persona quedan juntos y por
    fecha, así que basta buscar dónde caerían el primer y el último día de la ventana."""
    clave = np.sort(p_eventos * BASE + dia_eventos)
    return (np.searchsorted(clave, p_casos * BASE + hasta, side="right")
            - np.searchsorted(clave, p_casos * BASE + desde, side="left"))


def ultimo_hasta(p_eventos, dia_eventos, id_eventos, p_casos, hasta, propio) -> np.ndarray:
    """Día del último evento de la misma persona terminado hasta «hasta», sin contar el propio episodio; -1 si no hay."""
    orden = np.lexsort((id_eventos, dia_eventos, p_eventos))
    clave = (p_eventos * BASE + dia_eventos)[orden]
    persona, dia, ident = p_eventos[orden], dia_eventos[orden], id_eventos[orden]
    j = np.searchsorted(clave, p_casos * BASE + hasta, side="right") - 1
    j = np.where((j >= 0) & (ident[np.maximum(j, 0)] == propio), j - 1, j)  # el propio episodio se salta
    hay = (j >= 0) & (persona[np.maximum(j, 0)] == p_casos)
    return np.where(hay, dia[np.maximum(j, 0)], -1)


def historia(c: pd.DataFrame, e: pd.DataFrame, epi: pd.DataFrame, par: dict) -> tuple[dict, dict]:
    """Variables de la historia de 12 meses (D42 y D44 de la bitácora de la 2.3; decisión 2 del paso 2)."""
    # Las personas se numeran 0, 1, 2… para que persona · BASE + día no se desborde.
    personas = np.unique(epi["ID_PERSONA"].to_numpy())
    numero = lambda p: np.searchsorted(personas, p)
    propio = c["ID_EPISODIO"].to_numpy()
    p_caso = numero(c["ID_PERSONA"].to_numpy())
    ingreso = epi.loc[propio, "INICIO"].to_numpy()      # ingreso índice del caso
    fin_propio = epi.loc[propio, "FIN"].to_numpy()       # alta final del propio episodio
    desde, hasta = ingreso - par["ventana"], ingreso

    # Hospitalizaciones: episodios con al menos un egreso que no es cirugía mayor ambulatoria ni sesión. El propio
    # episodio terminaría dentro de la ventana solo si dura 0 días (ingresa y egresa el mismo día del ingreso índice).
    h = epi[epi["HOSPITALIZACION"]]
    p_h, fin_h, id_h = numero(h["ID_PERSONA"].to_numpy()), h["FIN"].to_numpy(), h.index.to_numpy()
    propio_dentro = fin_propio <= hasta
    previas = contar_en_ventana(p_h, fin_h, p_caso, desde, hasta) - propio_dentro
    hnp = h[h["NO_PLANIFICADO"]]
    no_planif = (contar_en_ventana(numero(hnp["ID_PERSONA"].to_numpy()), hnp["FIN"].to_numpy(), p_caso, desde, hasta)
                 - (propio_dentro & epi.loc[propio, "NO_PLANIFICADO"].to_numpy()))
    ultimo = ultimo_hasta(p_h, fin_h, id_h, p_caso, hasta, propio)
    dias = np.where((ultimo >= 0) & (ultimo >= desde), hasta - ultimo, par["sin_hosp"])

    # Cirugías mayores ambulatorias y sesiones: se cuentan egresos, sin los del propio episodio (D42). Un egreso del
    # propio episodio solo cae en la ventana si termina el mismo día del ingreso índice.
    eventos = {"CMA_PREVIAS": e["EXC_CMA"].to_numpy(), "SESIONES_PREVIAS": (e["EXC_SESION"] & ~e["EXC_CMA"]).to_numpy()}
    salida = {"HOSP_PREVIAS": previas, "HOSP_PREVIAS_NO_PLANIF": no_planif, "DIAS_ULTIMA_HOSP": dias}
    for nombre, es in eventos.items():
        ev = e[es]
        total = contar_en_ventana(numero(ev["ID_PERSONA"].to_numpy()), ev["FIN"].to_numpy(), p_caso, desde, hasta)
        mismo_dia = ev["FIN"].to_numpy() <= epi.loc[ev["ID_EPISODIO"].to_numpy(), "INICIO"].to_numpy()
        del_propio = ev.loc[mismo_dia, "ID_EPISODIO"].value_counts().reindex(propio, fill_value=0).to_numpy()
        salida[nombre] = total - del_propio

    # Marca de ventana cortada: la ventana empieza antes del primer día del bloque del identificador (D42 y D44).
    inicio_bloque = c["BLOQUE_ID"].map({b: (np.datetime64(f) - np.datetime64("1970-01-01")).astype(int)
                                        for b, f in par["inicio_bloques"].items()}).to_numpy()
    salida["VENTANA_CORTADA"] = (desde < inicio_bloque).astype("int8")
    for k in ["HOSP_PREVIAS", "HOSP_PREVIAS_NO_PLANIF", "CMA_PREVIAS", "SESIONES_PREVIAS"]:
        salida[k] = salida[k].astype("int16")
    salida["DIAS_ULTIMA_HOSP"] = salida["DIAS_ULTIMA_HOSP"].astype("int16")
    return salida, {"ingreso_indice": ingreso, "propio_dentro": int(propio_dentro.sum())}


# ------------------------------------------------------------------ 6. índice de comorbilidad
def comorbilidad(filas: np.ndarray, codigos: np.ndarray, n: int, tabla: pd.DataFrame) -> tuple[dict, dict]:
    """Marca cada condición en los casos que tienen alguno de sus códigos, en cualquier posición, aplica las
    jerarquías (una condición más grave reemplaza a su versión leve) y suma los pesos."""
    ident, distintos = pd.factorize(codigos)
    distintos = pd.Series(distintos, dtype="str")
    marcas = {}
    for r in tabla.itertuples():
        prefijos = tuple(x.replace(".", "") for x in r.codigos.split("|"))
        es = distintos.str.startswith(prefijos).to_numpy(dtype=bool)   # qué códigos distintos empiezan así
        tiene = np.zeros(n, dtype=bool)
        tiene[filas[es[ident]]] = True
        marcas[(r.indice, r.condicion)] = tiene
    antes = {k: v.copy() for k, v in marcas.items()}
    for r in tabla[tabla["reemplaza_a"] != ""].itertuples():
        marcas[(r.indice, r.reemplaza_a)] &= ~marcas[(r.indice, r.condicion)]
    puntaje = {i: sum(r.peso * marcas[(i, r.condicion)].astype("int16") for r in tabla[tabla["indice"] == i].itertuples())
               for i in INDICES}
    return {i: p.astype("int8") for i, p in puntaje.items()}, {"marcas": marcas, "antes": antes}


# ------------------------------------------------------------------ 7. valores poco frecuentes
def agrupar_raros(v: pd.DataFrame, minimo: int) -> dict:
    """En las columnas del CMBD tomadas tal cual, los valores con menos de «minimo» casos se juntan en OTRO."""
    juntados = {}
    for col in AGRUPADAS:
        n = v[col].value_counts()
        raros = n[n < minimo]
        v[col] = v[col].where(~v[col].isin(raros.index), OTRO)
        juntados[col] = raros
    return juntados


# ------------------------------------------------------------------ verificaciones y 8. salida
def verificar(v: pd.DataFrame, c: pd.DataFrame, e: pd.DataFrame, epi: pd.DataFrame, info: dict, version: dict,
              par: dict) -> list[tuple[str, bool]]:
    cortada = []  # la marca, calculada de nuevo con fechas de calendario
    for b, f in par["inicio_bloques"].items():
        cortada.append((c["BLOQUE_ID"] == b).to_numpy()
                       & (info["ingreso_indice"] < (np.datetime64(f.replace(year=f.year + 1)) - np.datetime64("1970-01-01")).astype(int)))
    sin_hosp = v["HOSP_PREVIAS"] == 0
    categoricas = [col for col, _, _ in VARIABLES if v[col].dtype == object or str(v[col].dtype) in ("str", "string")]
    return [
        ("Se leyeron todos los casos de estudio del conjunto de desarrollo registrado", len(c) == int(version["casos_desarrollo"])),
        ("Hay una fila por caso de estudio, sin repetir ID_EGRESO", bool(v["ID_EGRESO"].is_unique)),
        ("Cada caso de estudio tiene su episodio y cada episodio, su egreso de apertura",
         bool(c["ID_EPISODIO"].isin(epi.index).all() and epi["TIENE_APERTURA"].all())),
        ("Todos los egresos de un episodio son de la misma persona", bool((epi["PERSONAS"] == 1).all())),
        ("Ningún egreso E04 de 2019 forma parte de un episodio, así que no entra en la historia",
         not bool(e["EXC_ACTIVIDAD_2019"].any())),
        ("Todas las previsiones y provincias con dato tienen grupo y región en las tablas de reglas",
         not info["sin_mapa"]["previsión"] and not info["sin_mapa"]["provincia"]),
        ("Ninguna variable de categorías queda vacía", all(v[col].notna().all() for col in categoricas)),
        ("La edad está entre 0 y 110 años", bool(v["EDAD"].between(0, 110).all())),
        ("La estadía del episodio es mayor o igual que la del propio egreso, y esta, que cero",
         bool((v["ESTADIA"].to_numpy() >= info["estadia_propia"]).all() and (info["estadia_propia"] >= 0).all())),
        ("Las hospitalizaciones no planificadas no superan a las hospitalizaciones previas",
         bool((v["HOSP_PREVIAS_NO_PLANIF"] <= v["HOSP_PREVIAS"]).all() and (v["HOSP_PREVIAS_NO_PLANIF"] >= 0).all())),
        (f"DIAS_ULTIMA_HOSP vale {par['sin_hosp']} justo cuando no hay hospitalizaciones previas, y si no, entre 0 y {par['ventana']}",
         bool((v.loc[sin_hosp, "DIAS_ULTIMA_HOSP"] == par["sin_hosp"]).all()
              and v.loc[~sin_hosp, "DIAS_ULTIMA_HOSP"].between(0, par["ventana"]).all())),
        ("Ninguna cuenta de la historia es negativa",
         bool(all((v[k] >= 0).all() for k in ["HOSP_PREVIAS", "CMA_PREVIAS", "SESIONES_PREVIAS"]))),
        ("La marca de ventana cortada coincide con la regla de D42 calculada con fechas de calendario",
         bool((v["VENTANA_CORTADA"].to_numpy() == np.logical_or.reduce(cortada)).all())),
        ("El índice de Elixhauser está entre 0 y 28 condiciones y el de Charlson entre 0 y 24 puntos",
         bool(info["puntaje"]["ELIXHAUSER"].min() >= 0 and info["puntaje"]["ELIXHAUSER"].max() <= 28
              and info["puntaje"]["CHARLSON"].min() >= 0 and info["puntaje"]["CHARLSON"].max() <= 24)),
        ("Después de las jerarquías, ningún caso tiene a la vez una condición y la versión que esta reemplaza",
         all(not (info["comorb"]["marcas"][(r.indice, r.condicion)] & info["comorb"]["marcas"][(r.indice, r.reemplaza_a)]).any()
             for r in info["tabla_comorbilidad"].itertuples() if r.reemplaza_a)),
        ("En las columnas agrupadas no queda ningún valor propio con menos del mínimo de casos (OTRO puede tener menos)",
         all((v.loc[v[col] != OTRO, col].value_counts() >= par["minimo"]).all() for col in AGRUPADAS)),
    ]


def escribir(v: pd.DataFrame) -> list[tuple[str, bool]]:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    temporal = DESTINO.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(v, preserve_index=False), temporal, compression="zstd")
    temporal.replace(DESTINO)
    releido = pd.read_parquet(DESTINO)
    try:
        pd.testing.assert_frame_equal(releido, v, check_dtype=False)
        igual = True
    except AssertionError:
        igual = False
    return [("Lo releído de variables_casos.parquet es igual a lo calculado", igual)]


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def dec(x, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(lineas)


def auroc(puntaje: np.ndarray, y: np.ndarray) -> float:
    """Área bajo la curva ROC del puntaje solo: la probabilidad de que un caso que reingresa tenga un puntaje más
    alto que uno que no (los empates cuentan la mitad)."""
    ok = ~np.isnan(y)
    rango = pd.Series(puntaje[ok]).rank(method="average").to_numpy()
    positivo = y[ok] == 1
    n1, n0 = positivo.sum(), (~positivo).sum()
    return (rango[positivo].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def por_grupo(grupo, y: np.ndarray, orden=None) -> list[tuple]:
    """Casos y tasa de reingreso a 30 días (con dato) de cada valor de «grupo»."""
    t = pd.DataFrame({"g": grupo, "y": y}).groupby("g", observed=True)["y"].agg(["size", "count", "sum"])
    if orden is not None:
        t = t.reindex(orden).dropna(how="all")
    return [(k, int(r["size"]), 100 * r["sum"] / r["count"] if r["count"] else float("nan")) for k, r in t.iterrows()]


def tramos(x: pd.Series, cortes: list[int], etiquetas: list[str]) -> pd.Series:
    return pd.cut(x, [-1, *cortes], labels=etiquetas).astype(str)


def escribir_reporte(v: pd.DataFrame, c: pd.DataFrame, info: dict, par: dict, version: dict, verificaciones: list) -> None:
    ruta = ACTIVIDAD.name
    n = len(v)
    y = c["REING_30D"].to_numpy(dtype="float64", na_value=np.nan)
    tasa = lambda m: pct(np.nansum(y[m]), (~np.isnan(y[m])).sum())

    # 1. Lista de variables
    def valores(col: str) -> str:
        s = v[col]
        if s.dtype.kind in "fiu":
            return f"de {dec(s.min(), 1) if s.dtype.kind == 'f' else fmt(s.min())} a {dec(s.max(), 1) if s.dtype.kind == 'f' else fmt(s.max())}"
        return f"{fmt(s.nunique())} valores"

    def sin_dato(col: str) -> str:
        s = v[col]
        k = int(s.isna().sum()) if s.dtype.kind in "fiu" else int((s == SIN_DATO).sum())
        return fmt(k) if k else "—"

    filas_var = [[f"`{col}`", dcs, desc, valores(col), sin_dato(col)] for col, dcs, desc in VARIABLES]

    # 2. Episodio e historia
    traslado = info["ingreso_indice"] < a_dias(c["FECHA_INGRESO"])
    marca = v["VENTANA_CORTADA"].to_numpy() == 1
    hp = tramos(v["HOSP_PREVIAS"], [0, 1, 2, 3, 4, 10_000], ["0", "1", "2", "3", "4", "5 o más"])
    filas_hist = []
    for k in ["0", "1", "2", "3", "4", "5 o más"]:
        m = (hp == k).to_numpy()
        filas_hist.append([k, fmt((m & ~marca).sum()), tasa(m & ~marca), fmt((m & marca).sum()), tasa(m & marca)])
    anios = sorted(c["ANIO_ARCHIVO"].unique())
    filas_marca = [[str(a), fmt((c["ANIO_ARCHIVO"] == a).sum()), fmt((marca & (c["ANIO_ARCHIVO"] == a).to_numpy()).sum()),
                    pct((marca & (c["ANIO_ARCHIVO"] == a).to_numpy()).sum(), (c["ANIO_ARCHIVO"] == a).sum(), 1)] for a in anios]
    dias = tramos(v["DIAS_ULTIMA_HOSP"], [7, 30, 90, 180, par["ventana"], par["sin_hosp"]],
                  ["0 a 7", "8 a 30", "31 a 90", "91 a 180", f"181 a {par['ventana']}", "sin hospitalización previa"])
    filas_dias = [[k, fmt((dias == k).sum()), tasa((dias == k).to_numpy() & ~marca)] for k in
                  ["0 a 7", "8 a 30", "31 a 90", "91 a 180", f"181 a {par['ventana']}", "sin hospitalización previa"]]
    filas_otras = []
    for col in ["CMA_PREVIAS", "SESIONES_PREVIAS"]:
        t = tramos(v[col], [0, 1, 10_000], ["0", "1", "2 o más"])
        filas_otras.append([f"`{col}`", *[f"{fmt((t == k).sum())} ({tasa((t == k).to_numpy() & ~marca)})" for k in ["0", "1", "2 o más"]]])

    # 3. Comorbilidad
    tabla = info["tabla_comorbilidad"]
    marcas = info["comorb"]["marcas"]
    elix = tabla[tabla["indice"] == "ELIXHAUSER"]
    filas_cond = [[r.orden, r.descripcion, fmt(marcas[("ELIXHAUSER", r.condicion)].sum()),
                   pct(marcas[("ELIXHAUSER", r.condicion)].sum(), n), tasa(marcas[("ELIXHAUSER", r.condicion)])]
                  for r in elix.itertuples()]
    pe, pc = info["puntaje"]["ELIXHAUSER"], info["puntaje"]["CHARLSON"]
    alguna = {i: np.logical_or.reduce([marcas[(i, r.condicion)] for r in tabla[tabla["indice"] == i].itertuples()]) for i in INDICES}
    te = tramos(pd.Series(pe), [0, 1, 2, 3, 4, 100], ["0", "1", "2", "3", "4", "5 o más"])
    filas_cuenta = [[k, fmt((te == k).sum()), pct((te == k).sum(), n, 1), tasa((te == k).to_numpy())]
                    for k in ["0", "1", "2", "3", "4", "5 o más"]]
    filas_comp = [["Elixhauser (número de condiciones)", pct(alguna["ELIXHAUSER"].sum(), n, 1), dec(pe.mean()), dec(auroc(pe.astype(float), y), 3)],
                  ["Charlson (pesos de Quan 2011)", pct(alguna["CHARLSON"].sum(), n, 1), dec(pc.mean()), dec(auroc(pc.astype(float), y), 3)],
                  ["Número de diagnósticos (para comparar)", "—", dec(v["N_DIAGNOSTICOS"].mean()),
                   dec(auroc(v["N_DIAGNOSTICOS"].to_numpy(dtype=float), y), 3)]]
    ceros = ", ".join(r.descripcion.lower() for r in tabla[(tabla["indice"] == "CHARLSON") & (tabla["peso"] == 0)].itertuples())
    filas_anio_comorb = [[str(a), pct(alguna["ELIXHAUSER"][(c["ANIO_ARCHIVO"] == a).to_numpy()].sum(), (c["ANIO_ARCHIVO"] == a).sum(), 1),
                          pct(alguna["CHARLSON"][(c["ANIO_ARCHIVO"] == a).to_numpy()].sum(), (c["ANIO_ARCHIVO"] == a).sum(), 1)] for a in anios]

    # 4. Otras variables del CMBD
    filas_cmbd = []
    for col in ["TIPO_ALTA", "ESPECIALIDAD_INTERVENCION", "ESPECIALIDAD", "TIPO_PROCEDENCIA", "SERVICIO_INGRESO",
                "SERVICIO_ALTA", "HOSPITAL", "PUEBLO_ORIGINARIO", "NACIONALIDAD_EXTRANJERA"]:
        grupos = [g for g in por_grupo(v[col].to_numpy(), y) if g[1] >= 1000]
        baja, alta = min(grupos, key=lambda g: g[2]), max(grupos, key=lambda g: g[2])
        raros = info["juntados"].get(col)
        otro = f"{fmt(len(raros))} ({fmt(raros.sum())} casos)" if raros is not None and len(raros) else "—"
        filas_cmbd.append([f"`{col}`", fmt(v[col].nunique()), otro, f"{baja[0]}: {dec(baja[2])} %", f"{alta[0]}: {dec(alta[2])} %"])
    filas_num = []
    for col, cortes, etiquetas in [("SEVERIDAD", [1, 2, 3], ["1", "2", "3"]), ("RIESGO_MORTALIDAD", [1, 2, 3], ["1", "2", "3"]),
                                   ("UCI_UTI", [0, 1], ["0", "1"]), ("TRASLADO", [0, 1], ["0", "1"])]:
        t = tramos(v[col], cortes, etiquetas)
        filas_num.append([f"`{col}`", " · ".join(f"{k}: {fmt((t == k).sum())} casos ({tasa((t == k).to_numpy())})" for k in etiquetas)])
    nd = tramos(v["N_DIAGNOSTICOS"], [1, 3, 5, 7, 9, 12, 100], ["0 a 1", "2 a 3", "4 a 5", "6 a 7", "8 a 9", "10 a 12", "13 o más"])
    npx = tramos(v["N_PROCEDIMIENTOS"], [0, 4, 9, 14, 20, 1000], ["0", "1 a 4", "5 a 9", "10 a 14", "15 a 20", "21 o más"])
    filas_conteo = [["`N_DIAGNOSTICOS`", " · ".join(f"{k}: {tasa((nd == k).to_numpy())}" for k in
                                                     ["0 a 1", "2 a 3", "4 a 5", "6 a 7", "8 a 9", "10 a 12", "13 o más"])],
                    ["`N_PROCEDIMIENTOS`", " · ".join(f"{k}: {tasa((npx == k).to_numpy())}" for k in
                                                       ["0", "1 a 4", "5 a 9", "10 a 14", "15 a 20", "21 o más"])]]
    filas_juntados = []
    for col, raros in info["juntados"].items():
        for valor, casos in raros.sort_values(ascending=False).items():
            filas_juntados.append([f"`{col}`", valor, fmt(casos)])
    raros_d46 = {col: v[col].value_counts()[lambda s: s < par["minimo"]] for col in CATEGORIAS_D46}

    partes = [
        "# Variables de los casos de estudio (actividad 3.1, script 15)",
        f"Generado por `{ruta}/scripts/15_variables_casos.py`. Entrada: `data/processed/{DESARROLLO.name}`, de la versión "
        f"{version['version']} de la partición (SHA-256 `{version['sha256_desarrollo']}`), y la regla de «no planificado» de "
        "`2.2_depuracion_etiquetado/reglas/parametros.csv`. Salida: `data/processed/" + DESTINO.name + "`, con una fila por caso "
        "de estudio. No se abre el conjunto de prueba. Las decisiones están en `" + ruta + "/bitacora.md` (D46 a D49).",
        f"**Variables:** las {len(VARIABLES)} de la tabla siguiente, para los {fmt(n)} casos de estudio de desarrollo. Ninguna se "
        "elige ni se descarta por su relación con el reingreso; las tasas de este reporte son solo descriptivas.",

        "## 1. Las variables",
        "«Sin dato» cuenta los casos con el valor SIN DATO (en las de categorías) o sin valor (en las numéricas).",
        tabla_md(["Variable", "Decisión", "Contenido", "Valores", "Sin dato"], filas_var),
        f"Índice de comorbilidad en uso: **{par['indice']}**, {INDICES[par['indice']]}.",

        "## 2. Episodio e historia",
        f"**Ingreso índice.** En {fmt(traslado.sum())} casos el episodio empezó antes del ingreso a este hospital (traslados). "
        f"En ellos la mediana de la estadía es de {fmt(np.median(v['ESTADIA'].to_numpy()[traslado]))} días contando todo el episodio "
        f"y de {fmt(np.median(info['estadia_propia'][traslado]))} en el último hospital.",
        f"**Ventana.** Cuenta lo que terminó entre el ingreso índice menos {par['ventana']} días y el ingreso índice, ambos días "
        "incluidos, sin el propio episodio: una hospitalización que terminó el mismo día del ingreso índice cuenta, igual que el "
        "etiquetado cuenta el día 0 como reingreso (D20). En "
        f"{fmt(info['historia']['propio_dentro'])} casos el propio episodio dura 0 días: como termina el mismo día del ingreso "
        "índice, se descuenta para no contarlo como hospitalización previa.",
        f"**Valores extremos.** `HOSP_PREVIAS` llega a {fmt(v['HOSP_PREVIAS'].max())}. {fmt(info['extremos']['casos'])} casos, de "
        f"{fmt(info['extremos']['personas'])} personas, tienen 50 o más; de los egresos de esas personas, el "
        f"{pct(info['extremos']['cero_dias'], info['extremos']['egresos'], 1)} dura 0 días y el "
        f"{pct(info['extremos']['programados'], info['extremos']['egresos'], 1)} es programado.",
        "Hospitalizaciones previas y reingreso a 30 días, sin y con la marca de ventana cortada:",
        tabla_md(["Hospitalizaciones previas", "Casos sin marca", "Reingreso a 30 días", "Casos con marca", "Reingreso a 30 días"], filas_hist),
        "Casos con la ventana cortada, por año del alta:",
        tabla_md(["Año", "Casos de estudio", "Con la ventana cortada", "%"], filas_marca),
        "Días desde la última hospitalización (reingreso a 30 días de los casos sin marca):",
        tabla_md(["Días", "Casos", "Reingreso a 30 días sin marca"], filas_dias),
        "Cirugías mayores ambulatorias y sesiones previas (casos y reingreso a 30 días sin marca):",
        tabla_md(["Variable", "0", "1", "2 o más"], filas_otras),

        "## 3. Índice de comorbilidad",
        "Las 31 condiciones de Elixhauser con los códigos de Quan et al. (2005), buscadas en todos los diagnósticos del egreso. Las "
        "jerarquías ya están aplicadas: la diabetes con complicaciones reemplaza a la sin complicaciones, el cáncer metastásico al "
        "tumor sólido y la hipertensión con complicaciones a la sin complicaciones. Los códigos están en "
        f"`{ruta}/reglas/{ARCHIVO_COMORBILIDAD.name}`.",
        tabla_md(["N.º", "Condición", "Casos", "% de los casos", "Reingreso a 30 días"], filas_cond),
        "Número de condiciones de Elixhauser:",
        tabla_md(["Condiciones", "Casos", "%", "Reingreso a 30 días"], filas_cuenta),
        "Comparación con Charlson (sensibilidad). El área bajo la curva ROC mide qué tan bien el índice, solo, ordena a los casos "
        "que reingresan a 30 días por sobre los que no (0,5 es el azar):",
        tabla_md(["Índice", "Casos con al menos una condición", "Promedio", "Área bajo la curva ROC"], filas_comp),
        f"Con los pesos de Quan et al. (2011) cinco condiciones de Charlson valen 0 puntos ({ceros}): por eso solo el "
        f"{pct((pc > 0).sum(), n, 1)} de los casos tiene un puntaje de Charlson mayor que 0.",
        "Casos con al menos una condición, por año del alta:",
        tabla_md(["Año", "Elixhauser", "Charlson"], filas_anio_comorb),

        "## 4. Otras variables del CMBD",
        f"En las columnas tomadas tal cual, los valores con menos de {fmt(par['minimo'])} casos de estudio pasan a {OTRO} (D45). "
        "Reingreso a 30 días menor y mayor entre los valores con 1.000 casos o más:",
        tabla_md(["Variable", "Valores", "Juntados en OTRO", "Menor reingreso", "Mayor reingreso"], filas_cmbd),
        tabla_md(["Variable", "Casos y reingreso a 30 días por valor"], filas_num),
        "Reingreso a 30 días según el número de diagnósticos y de procedimientos:",
        tabla_md(["Variable", "Reingreso a 30 días por tramo"], filas_conteo),
        "Valores juntados en OTRO:",
        tabla_md(["Variable", "Valor", "Casos"], filas_juntados),
        "En las variables de categorías de la decisión 1 no se junta ningún valor; tienen menos de "
        f"{fmt(par['minimo'])} casos: " + ("; ".join(f"`{k}` {', '.join(f'{i} ({fmt(x)})' for i, x in s.items())}"
                                             for k, s in raros_d46.items() if len(s)) or "ninguno") + ".",

        "## 5. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{val.replace('|', ' / ')}`", desc] for k, (val, desc) in par["descripcion"].items()]),
        "De `2.2_depuracion_etiquetado/reglas/parametros.csv` (regla de «no planificado», D20 y D33): " +
        "; ".join(f"`{k}` = `{val.replace('|', ' / ')}`" for k, val in par["descripcion_22"].items()) + ".",

        "## 6. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in verificaciones),
    ]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {REPORTE}")


def main() -> None:
    inicio = time.time()
    par = cargar_parametros()
    reglas = cargar_reglas()
    version = comprobar_version()
    print(f"Partición: versión {version['version']}. Leyendo los egresos y armando los episodios...", flush=True)
    e = leer_egresos()
    epi = armar_episodios(e, par)
    print(f"{fmt(len(e))} egresos en {fmt(len(epi))} episodios ({time.time() - inicio:.0f} s). Leyendo los casos...", flush=True)
    c = leer_casos()
    v, info = variables_caso(c, epi, par, reglas)
    print(f"{fmt(len(c))} casos de estudio. Historia de 12 meses...", flush=True)
    hist, info["historia"] = historia(c, e, epi, par)
    for k, valor in hist.items():
        v[k] = valor
    info["ingreso_indice"] = info["historia"]["ingreso_indice"]
    muchas = c.loc[v["HOSP_PREVIAS"].to_numpy() >= 50, "ID_PERSONA"].unique()   # para el reporte: valores extremos
    de_ellas = e[e["ID_PERSONA"].isin(muchas)]
    info["extremos"] = {"casos": int((v["HOSP_PREVIAS"] >= 50).sum()), "personas": len(muchas), "egresos": len(de_ellas),
                        "cero_dias": int((de_ellas["FIN"] == de_ellas["INICIO"]).sum()),
                        "programados": int((de_ellas["TIPO_INGRESO"] == "PROGRAMADA").sum())}
    print(f"Índice de comorbilidad ({time.time() - inicio:.0f} s)...", flush=True)
    tabla = reglas["comorbilidad"]
    info["puntaje"], info["comorb"] = comorbilidad(info.pop("filas_dx"), info.pop("codigos_dx"), len(c), tabla)
    info["tabla_comorbilidad"] = tabla
    v["INDICE_COMORBILIDAD"] = info["puntaje"][par["indice"]]
    info["juntados"] = agrupar_raros(v, par["minimo"])
    v = v[["ID_EGRESO", *[col for col, _, _ in VARIABLES]]]
    verificaciones = [(f"El conjunto de desarrollo es el de la versión {version['version']} registrada de la partición", True)]
    verificaciones += verificar(v, c, e, epi, info, version, par)
    verificaciones += escribir(v)
    escribir_reporte(v, c, info, par, version, verificaciones)
    fallidas = [texto for texto, ok in verificaciones if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
