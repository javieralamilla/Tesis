"""Etiquetado del reingreso (actividad 2.2, script 09).

Parte de data/processed/grd_depurado.parquet y deja data/processed/grd_etiquetado.parquet con las
cuatro variables objetivo de cada caso de estudio (bitácora D20, D26 y D30 a D33):

  REING_7D        reingreso dentro de 7 días, por cualquier causa
  REING_7D_CDM    reingreso dentro de 7 días, relacionado con el diagnóstico (misma CDM)
  REING_30D       reingreso dentro de 30 días, por cualquier causa
  REING_30D_CDM   reingreso dentro de 30 días, relacionado con el diagnóstico (misma CDM)

Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un
episodio asistencial nuevo (PUEDE_SER_REINGRESO) y se cuentan los días entre el alta del caso y
ese ingreso. Con reingreso_solo_no_planificado = SI solo cuentan los ingresos no planificados:
de un tipo no programado y que no sean un parto ni una sesión de tratamiento. El reingreso
relacionado se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio.
Los casos de estudio de las CDM de cdm_sin_relacionado (la 14, que solo contiene partos) quedan sin
dato en las variables relacionadas: un parto no cuenta como reingreso, así que con la comparación
literal su valor sería 0 por construcción (bitácora D38).

Censura: un reingreso solo aparece en la base si termina antes del cierre del bloque. Por eso
las variables de una ventana tienen dato solo si el alta ocurre al menos ventana + margen días
antes del cierre; si no, quedan sin dato. Tampoco tienen dato los egresos que no son caso de estudio.

Los umbrales están en reglas/parametros.csv. El reporte reportes/09_etiquetado.md muestra las
tasas por definición, por año y por hospital, la calidad del identificador por año, la verificación
de la censura y la comparación de las dos formas de relacionar las CDM. reportes/09_tasas_por_hospital.csv tiene las tasas por
hospital y año.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\scripts\\09_etiquetar.py
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
ORIGEN = DIR_PROCESSED / "grd_depurado.parquet"
DESTINO = DIR_PROCESSED / "grd_etiquetado.parquet"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
# Nombres de los hospitales y de los GRD: hojas Hospitales e IR - GRD de la tabla maestra del DEIS (solo se usan en el reporte).
TABLA_MAESTRA = RAIZ.parent / "Datos" / "Tablas auxiliares" / "Tablas maestras bases GRD.xlsx"
ANIOS = list(range(2019, 2025))

# Último día observado de cada bloque de identificador (bitácora D03).
CIERRE_BLOQUE = {"A": pd.Timestamp("2020-12-31"), "B": pd.Timestamp("2024-12-31")}
# Las dos formas de contar un ingreso como reingreso. Se calculan ambas; se guarda la elegida.
FORMAS = {"NP": "Solo ingresos no planificados", "TODO": "Todo ingreso"}
PARAMETROS = ["ventanas_dias", "censura_margen_dias", "reingreso_solo_no_planificado", "ingresos_no_planificados",
              "grd_parto", "diagnosticos_sesion", "cdm_agrupadas", "cdm_sensibilidad", "cdm_sin_relacionado"]
COLUMNAS = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO",
            "COD_HOSPITAL", "TIPO_INGRESO", "FECHA_INGRESO", "FECHAALTA", "TIPOALTA", "DIAGNOSTICO1", "IR_29301_COD_GRD", "CDM"]
TRAMOS_DIAS = [(0, 0, "El mismo día"), (1, 1, "1 día"), (2, 3, "2 a 3 días"), (4, 7, "4 a 7 días"),
               (8, 14, "8 a 14 días"), (15, 30, "15 a 30 días")]
# Días entre el alta y el 31 de diciembre, para la verificación de la censura.
TRAMOS_CIERRE = [(7, 13), (14, 20), (21, 29), (30, 36), (37, 59), (60, 89), (90, 120)]
PARTO, SESION, SIN_TIPO = "PARTO O CESÁREA", "SESIÓN DE TRATAMIENTO", "(sin tipo de ingreso)"


def cargar_parametros(cambios: dict | None = None) -> dict:
    """Lee los umbrales. `cambios` reemplaza valores del archivo: lo usa el script 11 (análisis de sensibilidad)."""
    with open(ARCHIVO_PARAMETROS, encoding="utf-8-sig", newline="") as f:
        filas = {fila["parametro"]: fila for fila in csv.DictReader(f, delimiter=";")}
    faltan = sorted(set(PARAMETROS) - set(filas))      # el archivo también tiene parámetros de otros scripts
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")
    desconocidos = sorted(set(cambios or {}) - set(filas))
    if desconocidos:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: no existen los parámetros {desconocidos}.")
    for nombre, valor in (cambios or {}).items():
        filas[nombre]["valor"] = valor

    def lista(nombre: str) -> list[str]:
        return [v.strip().upper() for v in filas[nombre]["valor"].split("|") if v.strip()]

    def grupos_cdm(nombre: str) -> tuple[dict, list[str]]:
        # Grupos separados por |, y las CDM de cada grupo por +. Cada CDM se lleva a la primera de su grupo.
        grupos = [[c.strip() for c in g.split("+")] for g in lista(nombre)]
        return {c: g[0] for g in grupos for c in g}, [" y ".join(g) for g in grupos]

    solo_np = filas["reingreso_solo_no_planificado"]["valor"].strip().upper()
    if solo_np not in ("SI", "NO"):
        raise SystemExit(f"reingreso_solo_no_planificado: se esperaba SI o NO y dice '{solo_np}'.")
    agrupadas, grupos = grupos_cdm("cdm_agrupadas")
    sensibilidad, grupos_sensibilidad = grupos_cdm("cdm_sensibilidad")
    sin_relacionado = lista("cdm_sin_relacionado")
    par = {"ventanas_dias": sorted(int(v) for v in lista("ventanas_dias")),
           "margen": int(filas["censura_margen_dias"]["valor"]),
           "forma": "NP" if solo_np == "SI" else "TODO",
           "ingresos_no_planificados": lista("ingresos_no_planificados"),
           "grd_parto": lista("grd_parto"), "sesiones": lista("diagnosticos_sesion"),
           "cdm_agrupadas": agrupadas, "grupos_cdm": grupos,
           "cdm_sensibilidad": sensibilidad, "grupos_sensibilidad": grupos_sensibilidad,
           # Una CDM sin reingreso relacionado posible lo vuelve a tener si cdm_agrupadas la une con otra, o si cuenta
           # todo ingreso: entonces un parto también es reingreso (D38).
           "cdm_sin_relacionado_archivo": sin_relacionado,
           "cdm_sin_relacionado_np": [x for x in sin_relacionado if x not in agrupadas]}
    par["cdm_sin_relacionado"] = par["cdm_sin_relacionado_np"] if par["forma"] == "NP" else []
    if not par["ventanas_dias"] or par["margen"] < 0:
        raise SystemExit("Se necesita al menos una ventana y un margen de censura que no sea negativo.")
    par["descripcion"] = {nombre: (filas[nombre]["valor"].strip(), filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    return par


def a_dias(fechas: pd.Series) -> np.ndarray:
    return fechas.to_numpy().astype("datetime64[D]").astype("int64")


def conteo(mascara: np.ndarray, valores: pd.Series) -> dict:
    return {k: int(v) for k, v in valores[mascara].value_counts(dropna=False).items()}


def ventana_de(columna: str) -> int:
    return int(columna.split("_")[1][:-1])


# ------------------------------------------------------------------ etiquetado
def etiquetar(par: dict, d: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    """Devuelve las columnas nuevas (una fila por egreso, en el orden de la tabla depurada) y las cifras del reporte.

    Sin `d` lee la tabla depurada. El script 11 entrega la suya, con las mismas columnas, para los análisis de sensibilidad.
    """
    if d is None:
        d = pq.read_table(ORIGEN, columns=COLUMNAS).to_pandas()
    ventanas, larga, margen, elegida = par["ventanas_dias"], max(par["ventanas_dias"]), par["margen"], par["forma"]
    otra = next(f for f in FORMAS if f != elegida)

    # Ingresos que abren un episodio asistencial, en orden dentro de cada persona.
    ing = d[d["PUEDE_SER_REINGRESO"]].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    n = len(ing)
    persona = ing["ID_PERSONA"].to_numpy(dtype="int64")
    ultimo = np.r_[persona[1:] != persona[:-1], True]             # último ingreso de cada persona
    inicio, termino = a_dias(ing["FECHA_INGRESO"]), a_dias(ing["FECHAALTA"])
    egreso = ing["ID_EGRESO"].to_numpy()
    hospital = ing["COD_HOSPITAL"].to_numpy()

    # CDM para comparar: la CDM 99 nunca cuenta como relacionada; las CDM agrupadas cuentan como una sola.
    cdm_valida = d["CDM"].where(d["CDM"] != "99")
    categorias = sorted(cdm_valida.dropna().unique())

    def codigos(mapa: dict) -> pd.Series:
        valores = cdm_valida.replace(mapa) if mapa else cdm_valida
        return pd.Series(pd.Categorical(valores, categories=categorias).codes, index=d.index)      # -1: sin CDM o CDM 99

    # Además de la relación en uso se calcula otra para comparar: la de sensibilidad, o la literal si se usa una agrupación.
    if par["cdm_agrupadas"]:
        comparacion = {"nombre": "Sin agrupar CDM", "mapa": {}}
    elif par["cdm_sensibilidad"]:
        comparacion = {"nombre": "Con las CDM " + "; ".join(par["grupos_sensibilidad"]) + " como una sola", "mapa": par["cdm_sensibilidad"]}
    else:
        comparacion = None
    cod_uso = codigos(par["cdm_agrupadas"])
    cod_comp = codigos(comparacion["mapa"]) if comparacion else cod_uso
    cdm, cdm_comp = cod_uso[ing.index].to_numpy(), cod_comp[ing.index].to_numpy()

    # Regla de reingreso no planificado, en orden de precedencia (bitácora D20 y D33).
    parto = ing["IR_29301_COD_GRD"].str.startswith(tuple(par["grd_parto"]), na=False).to_numpy() if par["grd_parto"] else np.zeros(n, dtype=bool)
    sesion = ing["DIAGNOSTICO1"].str.startswith(tuple(par["sesiones"]), na=False).to_numpy() if par["sesiones"] else np.zeros(n, dtype=bool)
    no_programado = ing["TIPO_INGRESO"].isin(par["ingresos_no_planificados"]).to_numpy()
    sin_tipo = ing["TIPO_INGRESO"].isna().to_numpy()
    cuenta = {"NP": no_programado & ~parto & ~sesion, "TODO": np.ones(n, dtype=bool)}
    clase = np.select([parto, sesion, sin_tipo], [PARTO, SESION, SIN_TIPO], default=ing["TIPO_INGRESO"].fillna("").to_numpy())

    # Casos de estudio, posición de su episodio en la lista de ingresos y seguimiento disponible.
    es_caso = d["ES_CASO_ESTUDIO"].to_numpy()
    c = d[es_caso]
    nc = len(c)
    pos = pd.Series(np.arange(n), index=egreso).reindex(c["ID_EPISODIO"].to_numpy(dtype="int64")).to_numpy()
    if np.isnan(pos).any():
        raise SystemExit("Hay casos de estudio sin episodio asistencial: revisar el script 08.")
    pos = pos.astype("int64")
    c_alta = a_dias(c["FECHAALTA"])
    c_cdm, c_cdm_comp = cod_uso[c.index].to_numpy(), cod_comp[c.index].to_numpy()
    al_cierre = a_dias(c["BLOQUE_ID"].map(CIERRE_BLOQUE)) - c_alta
    valido = {v: al_cierre >= v + margen for v in ventanas}       # el alta deja ventana + margen días antes del cierre

    # Ruta 1: primer ingreso posterior de la misma persona que cuenta como reingreso, a cualquier distancia.
    dias, primero, hay = {}, {}, {}
    for forma, vale in cuenta.items():
        propio = pd.Series(np.where(vale, np.arange(n, dtype="float64"), np.nan))
        desde = propio.groupby(persona, sort=False).bfill().to_numpy()       # primer ingreso que cuenta, desde esta posición
        siguiente = np.r_[desde[1:], np.nan]
        siguiente[ultimo] = np.nan                                           # el que sigue es de otra persona
        j = siguiente[pos]
        hay[forma] = ~np.isnan(j)
        primero[forma] = np.where(hay[forma], j, 0).astype("int64")
        dias[forma] = np.where(hay[forma], inicio[primero[forma]] - c_alta, -1)

    # Ruta 2: se recorren uno a uno los ingresos posteriores mientras caigan dentro de la ventana más larga.
    # Entrega las variables de misma CDM (basta que algún ingreso de la ventana la tenga) y repite las demás.
    claves = [(forma, v) for forma in FORMAS for v in ventanas]
    alguno = {k: np.zeros(nc, dtype=bool) for k in claves}
    misma_cdm = {k: np.zeros(nc, dtype=bool) for k in claves}
    misma_cdm_comp = {k: np.zeros(nc, dtype=bool) for k in claves}           # con la relación de comparación
    activo, paso = np.ones(nc, dtype=bool), 0
    while activo.any():
        paso += 1
        j = pos + paso
        activo &= j < n
        activo[activo] = persona[j[activo]] == persona[pos[activo]]
        distancia = np.full(nc, larga + 1, dtype="int64")
        distancia[activo] = inicio[j[activo]] - c_alta[activo]
        activo &= distancia <= larga
        k = np.where(activo, j, 0)
        relacionado = activo & (cdm[k] == c_cdm) & (cdm[k] >= 0)
        relacionado_comp = activo & (cdm_comp[k] == c_cdm_comp) & (cdm_comp[k] >= 0)
        for forma, vale in cuenta.items():
            for v in ventanas:
                dentro = activo & (distancia <= v) & vale[k]
                alguno[(forma, v)] |= dentro
                misma_cdm[(forma, v)] |= dentro & relacionado
                misma_cdm_comp[(forma, v)] |= dentro & relacionado_comp

    def variables(forma: str, relacion: dict) -> dict[str, np.ndarray]:
        """Las variables de una forma de contar, antes de aplicar la censura de cada ventana."""
        salida = {}
        for v in ventanas:
            salida[f"REING_{v}D"] = hay[forma] & (dias[forma] <= v)
            salida[f"REING_{v}D_CDM"] = relacion[(forma, v)]
        return salida

    etiquetas = variables(elegida, misma_cdm)
    nombres = list(etiquetas)
    # CDM sin reingreso relacionado posible (D38): sus casos quedan sin dato en las variables relacionadas.
    # En la relación de comparación vuelve a tener dato la CDM que esa relación une con otra.
    # Al contar todo ingreso, un parto también es reingreso: entonces no se excluye ninguna CDM.
    def excluidas_en(forma: str) -> list[str]:
        return par["cdm_sin_relacionado_np"] if forma == "NP" else []
    excluidas_comp = [x for x in excluidas_en(elegida) if not (comparacion and x in comparacion["mapa"])]
    sin_rel = c["CDM"].isin(par["cdm_sin_relacionado"]).to_numpy()
    sin_rel_comp = c["CDM"].isin(excluidas_comp).to_numpy()
    sin_rel_otra = c["CDM"].isin(excluidas_en(otra)).to_numpy()

    def dato(k: str, excluir: np.ndarray) -> np.ndarray:
        return valido[ventana_de(k)] & ~excluir if k.endswith("_CDM") else valido[ventana_de(k)]
    con_dato = {k: dato(k, sin_rel) for k in nombres}
    con_dato_comp = {k: dato(k, sin_rel_comp) for k in nombres}
    con_dato_otra = {k: dato(k, sin_rel_otra) for k in nombres}

    # Columnas nuevas: con dato solo en los casos de estudio con seguimiento suficiente.
    def columna(valores: np.ndarray, tipo: str, tiene: np.ndarray | None = None) -> pd.arrays.IntegerArray:
        lleno = np.zeros(len(d), dtype=tipo)
        lleno[es_caso] = valores
        falta = ~es_caso
        if tiene is not None:
            falta[es_caso] = ~tiene
        return pd.arrays.IntegerArray(lleno, falta)

    nuevo = pd.DataFrame({"ID_EGRESO": d["ID_EGRESO"]})
    for k in nombres:
        nuevo[k] = columna(etiquetas[k].astype("int8"), "int8", con_dato[k])
    nuevo["DIAS_REING"] = columna(dias[elegida].astype("int16"), "int16", hay[elegida])
    nuevo["ID_EGRESO_REING"] = columna(egreso[primero[elegida]], "int64", hay[elegida])

    # ---------------------------------------------------------------- cifras del reporte
    anio = c["ANIO_ARCHIVO"]
    todas = valido[larga]                                         # casos con seguimiento para la ventana más larga
    cuatro = todas & ~sin_rel                                     # casos con dato en las cuatro variables

    def positivos(valores: dict, dato: dict = con_dato) -> dict:
        return {k: int((valores[k] & dato[k]).sum()) for k in nombres}

    en_ventana = todas & hay[elegida] & (dias[elegida] <= larga)
    con_ingreso = todas & hay["TODO"] & (dias["TODO"] <= larga)
    combinaciones = pd.DataFrame({k: etiquetas[k][cuatro].astype(int) for k in nombres}).value_counts().sort_index(ascending=False)
    tipo = ing["TIPO_INGRESO"]
    info = {
        "egresos": len(d), "casos": nc, "pasos": paso, "comparacion": comparacion["nombre"] if comparacion else None,
        "con_dato": {k: int(con_dato[k].sum()) for k in nombres},
        "con_dato_anio": {k: conteo(con_dato[k], anio) for k in nombres},
        "positivos": positivos(etiquetas),
        "positivos_anio": {k: conteo(etiquetas[k] & con_dato[k], anio) for k in nombres},
        "positivos_otra": positivos(variables(otra, misma_cdm), con_dato_otra),
        "con_dato_otra": {k: int(con_dato_otra[k].sum()) for k in nombres},
        "positivos_comparacion": positivos(variables(elegida, misma_cdm_comp), con_dato_comp),
        "con_dato_comparacion": {k: int(con_dato_comp[k].sum()) for k in nombres},
        "todas": int(cuatro.sum()),
        "combinaciones": [(list(k), int(v)) for k, v in combinaciones.items()],
        "dias": {txt: int((en_ventana & (dias[elegida] >= a) & (dias[elegida] <= b)).sum()) for a, b, txt in TRAMOS_DIAS if a <= larga},
        "otro_hospital": (int((en_ventana & (hospital[primero[elegida]] != c["COD_HOSPITAL"].to_numpy())).sum()), int(en_ventana.sum())),
        "clase_primer_ingreso": conteo(con_ingreso, pd.Series(clase[primero["TODO"]])),
        "ingresos": n,
        "ingresos_clase": conteo(np.ones(n, dtype=bool), pd.Series(clase)),
        "contradictorios": {
            "parto o cesárea (por GRD) con tipo de ingreso distinto de obstétrico": int((parto & (tipo != "OBSTETRICA").to_numpy()).sum()),
            "sesión de tratamiento (por diagnóstico) con tipo de ingreso no programado": int((sesion & no_programado & ~parto).sum()),
            "sin tipo de ingreso y sin ser parto ni sesión": int((sin_tipo & ~parto & ~sesion).sum()),
        },
        "por_grupo": {},
    }
    # Detalle del reingreso relacionado en las CDM que alguna de las dos formas de comparar agrupa.
    k_larga = f"REING_{larga}D_CDM"
    comp_larga = variables(elegida, misma_cdm_comp)[k_larga]
    cdm_caso = c["CDM"].to_numpy()
    info["cdm_involucradas"] = []
    for x in sorted(set(par["cdm_agrupadas"]) | set(par["cdm_sensibilidad"])):
        de_la_cdm = todas & (cdm_caso == x)                       # None: la CDM no tiene dato en esa relación (D38)
        info["cdm_involucradas"].append((x, int(de_la_cdm.sum()), int((de_la_cdm & etiquetas[f"REING_{larga}D"]).sum()),
                                         None if x in par["cdm_sin_relacionado"] else int((de_la_cdm & etiquetas[k_larga]).sum()),
                                         None if x in excluidas_comp else int((de_la_cdm & comp_larga).sum())))

    # CDM sin reingreso relacionado posible (D38): qué GRD contienen y en qué CDM cae el primer reingreso
    # no planificado de sus casos de estudio, para mostrar por qué el 0 es obligatorio.
    excluida = d["CDM"].isin(par["cdm_sin_relacionado_archivo"])
    info["grd_sin_relacionado"] = (d.loc[excluida].groupby("IR_29301_COD_GRD")
                                   .agg(egresos=("ID_EGRESO", "size"), casos=("ES_CASO_ESTUDIO", "sum")).reset_index())
    excluida_caso = c["CDM"].isin(par["cdm_sin_relacionado_archivo"]).to_numpy()
    reingresa = excluida_caso & todas & hay[elegida] & (dias[elegida] <= larga)
    primeros = ing.iloc[primero[elegida][reingresa]]
    info["primer_reingreso_sin_relacionado"] = {
        "casos": int((excluida_caso & todas).sum()), "con_reingreso": int(reingresa.sum()),
        "cdm": primeros["CDM"].fillna("(sin dato)").value_counts(),
        "grd": primeros["IR_29301_COD_GRD"].fillna("(sin dato)").value_counts().head(5),
        "diagnosticos": primeros["DIAGNOSTICO1"].fillna("(sin dato)").str[:3].value_counts().head(5)}
    # Por cada caso de estudio: si tiene dato y si tiene reingreso en cada variable. Se suman por grupo.
    columnas = {"n": np.ones(nc, dtype="int64")}
    for k in nombres:
        columnas[f"pos_{k}"] = (etiquetas[k] & con_dato[k]).astype("int64")
        columnas[f"n_{k}"] = con_dato[k].astype("int64")
    medidas = pd.DataFrame(columnas)
    for nombre, col in (("Tipo de ingreso", "TIPO_INGRESO"), ("Tipo de alta", "TIPOALTA"), ("CDM", "CDM")):
        tabla = medidas.groupby(c[col].fillna("(sin dato)").to_numpy()).sum()
        info["por_grupo"][nombre] = tabla.sort_index() if col == "CDM" else tabla.sort_values("n", ascending=False)

    # Por hospital. Un reingreso en un hospital que todavía no informaba a la base no se ve (bitácora H05):
    # se separan los hospitales presentes todos los años de los que se incorporan después.
    por_hospital = medidas.groupby([c["COD_HOSPITAL"].to_numpy(), anio.to_numpy()]).sum()
    por_hospital.index.names = ["COD_HOSPITAL", "ANIO"]
    presencia = d.groupby("COD_HOSPITAL")["ANIO_ARCHIVO"].agg(DESDE="min", HASTA="max", ANIOS="nunique")
    incorporados = presencia.index[presencia["ANIOS"] < d["ANIO_ARCHIVO"].nunique()]
    caso_incorporado = c["COD_HOSPITAL"].isin(incorporados).to_numpy()
    k_todo = f"REING_{larga}D"
    positivo = etiquetas[k_todo] & con_dato[k_todo]
    # El primer reingreso de la ventana ocurre en un hospital incorporado después.
    en_incorporado = positivo & pd.Series(hospital[primero[elegida]]).isin(incorporados).to_numpy()
    info["hospitales"] = {
        "por_hospital_anio": por_hospital.reset_index(), "presencia": presencia,
        "n_presentes": int(len(presencia) - len(incorporados)), "n_incorporados": int(len(incorporados)),
        "tendencia": [
            ("Todos los hospitales", conteo(con_dato[k_todo], anio), conteo(positivo, anio)),
            ("Hospitales presentes todos los años", conteo(con_dato[k_todo] & ~caso_incorporado, anio), conteo(positivo & ~caso_incorporado, anio)),
            ("Los mismos, sin contar los reingresos que ocurren en un hospital incorporado después",
             conteo(con_dato[k_todo] & ~caso_incorporado, anio), conteo(positivo & ~caso_incorporado & ~en_incorporado, anio)),
            ("Hospitales incorporados después", conteo(con_dato[k_todo] & caso_incorporado, anio), conteo(positivo & caso_incorporado, anio)),
        ],
    }

    # Verificación de la censura: en los años cuyo año siguiente está en la base con el mismo identificador,
    # qué parte de los reingresos no se vería si la base terminara el 31 de diciembre del año del alta.
    anio_alta = c["FECHAALTA"].dt.year
    interior = (anio_alta < c["BLOQUE_ID"].map({b: f.year for b, f in CIERRE_BLOQUE.items()})).to_numpy()
    fin_anio = a_dias(pd.to_datetime(anio_alta.astype(str) + "-12-31"))
    al_fin = fin_anio - c_alta
    termina_despues = hay[elegida] & (termino[primero[elegida]] > fin_anio)   # el reingreso termina después del 31-12
    info["anios_interiores"] = sorted(int(a) for a in anio_alta[interior].unique())
    info["censura"] = []
    for a, b in TRAMOS_CIERRE:
        tramo = interior & (al_fin >= a) & (al_fin <= b)
        fila = {"tramo": f"{a} a {b}", "casos": int(tramo.sum())}
        for v in ventanas:
            reingresa = tramo & hay[elegida] & (dias[elegida] <= v)
            fila[v] = (int(reingresa.sum()), int((reingresa & termina_despues).sum())) if a >= v else None
        info["censura"].append(fila)

    # ---------------------------------------------------------------- verificaciones
    def contenido(a: str, b: str) -> bool:      # todo caso positivo en a lo es también en b
        return bool((~etiquetas[a] | etiquetas[b]).all())

    ref = d.set_index("ID_EGRESO")[["ID_PERSONA", "ID_EPISODIO", "FECHA_INGRESO", "PUEDE_SER_REINGRESO"]]
    r = ref.reindex(egreso[primero[elegida]][hay[elegida]])
    caso = c[hay[elegida]]
    coherente = bool((r["ID_PERSONA"].to_numpy(dtype="int64") == caso["ID_PERSONA"].to_numpy(dtype="int64")).all()
                     and (r["ID_EPISODIO"].to_numpy(dtype="int64") != caso["ID_EPISODIO"].to_numpy(dtype="int64")).all()
                     and r["PUEDE_SER_REINGRESO"].all()
                     and ((r["FECHA_INGRESO"].to_numpy() - caso["FECHAALTA"].to_numpy()) / np.timedelta64(1, "D") == dias[elegida][hay[elegida]]).all()
                     and (dias[elegida][hay[elegida]] >= 0).all())
    esperado = {}
    for k in nombres:
        esperado[k] = np.zeros(len(d), dtype=bool)
        esperado[k][es_caso] = con_dato[k]
    info["verificaciones"] = [
        ("Cada variable tiene dato en los casos de estudio con seguimiento suficiente para su ventana, y solo en ellos "
         "(en las relacionadas, salvo las CDM de `cdm_sin_relacionado`)",
         all((nuevo[k].notna().to_numpy() == esperado[k]).all() for k in nombres)),
        ("Los casos que quedan sin dato en las variables relacionadas no tienen ningún reingreso de su misma CDM: "
         "el 0 era obligatorio", all(not (etiquetas[k] & sin_rel).any() for k in nombres if k.endswith("_CDM"))),
        ("Todo caso de estudio tiene seguimiento suficiente para la ventana más corta", bool(valido[min(ventanas)].all())),
        ("Las dos rutas de cálculo dan el mismo resultado en las variables por cualquier causa",
         all((alguno[(elegida, v)] == etiquetas[f"REING_{v}D"]).all() for v in ventanas)),
        ("Todo reingreso de una ventana corta lo es también de la más larga",
         all(contenido(f"REING_{v}D{s}", f"REING_{larga}D{s}") for v in ventanas for s in ("", "_CDM"))),
        ("Todo reingreso relacionado lo es también por cualquier causa",
         all(contenido(f"REING_{v}D_CDM", f"REING_{v}D") for v in ventanas)),
        ("Todo reingreso no planificado lo es también al contar todo ingreso",
         all(bool((~a | b).all()) for a, b in zip(variables("NP", misma_cdm).values(), variables("TODO", misma_cdm).values()))),
        ("El ingreso señalado como reingreso es de la misma persona, abre otro episodio y ocurre el día del alta o después",
         coherente),
    ]
    return nuevo, info


def calidad_identificador(nuevo: pd.DataFrame, variable: str) -> dict:
    """Calidad del identificador por año del alta: egresos sin identificador, con identificador genérico o con
    identidad ambigua, y la tasa de `variable` con y sin los casos de identidad ambigua. Sirve para revisar si el
    aumento de 2023 y 2024 se debe a una mejora del identificador (revisión del 13 de octubre de 2026, punto 2.3).
    Solo la usa el reporte de este script."""
    t = pq.read_table(ORIGEN, columns=["ID_EGRESO", "ANIO_ARCHIVO", "EXC_SIN_ID", "EXC_ID_GENERICO", "IDENTIDAD_AMBIGUA",
                                       "ES_CASO_ESTUDIO"]).to_pandas()
    if not (t["ID_EGRESO"].to_numpy() == nuevo["ID_EGRESO"].to_numpy()).all():
        raise SystemExit("Las columnas nuevas no están alineadas con la tabla depurada.")
    caso, ambigua = t["ES_CASO_ESTUDIO"].to_numpy(), t["IDENTIDAD_AMBIGUA"].to_numpy()
    valor = nuevo[variable]
    dato, positivo = valor.notna().to_numpy(dtype=bool), (valor == 1).fillna(False).to_numpy(dtype=bool)
    anio = t["ANIO_ARCHIVO"].to_numpy()
    salida = {}
    for a in [*ANIOS, None]:
        en = np.ones(len(t), dtype=bool) if a is None else anio == a
        salida[a] = {"egresos": int(en.sum()), "sin_id": int((en & t["EXC_SIN_ID"].to_numpy()).sum()),
                     "generico": int((en & t["EXC_ID_GENERICO"].to_numpy()).sum()), "ambigua": int((en & ambigua).sum()),
                     "casos": int((en & caso).sum()), "casos_ambigua": int((en & caso & ambigua).sum()),
                     **{nombre: (int((en & dato & m).sum()), int((en & positivo & m).sum()))
                        for nombre, m in (("todos", caso), ("sin_ambigua", caso & ~ambigua), ("solo_ambigua", caso & ambigua))}}
    return {"variable": variable, "por_anio": salida}


# ------------------------------------------------------------------ escritura
def escribir(nuevo: pd.DataFrame) -> list[tuple[str, bool]]:
    """Copia la tabla depurada con las columnas nuevas, por grupos de filas."""
    origen = pq.ParquetFile(ORIGEN)
    tipos = {"int8": pa.int8(), "int16": pa.int16(), "int64": pa.int64()}
    esquema = pa.schema([*origen.schema_arrow,
                         *[pa.field(col, tipos[str(nuevo[col].dtype).lower()]) for col in nuevo.columns[1:]]])
    temporal = DESTINO.with_suffix(".parquet.tmp")
    escritor, escritas = None, 0
    try:
        for g in range(origen.num_row_groups):
            bloque = origen.read_row_group(g).to_pandas()
            extra = nuevo.iloc[escritas:escritas + len(bloque)]
            escritas += len(bloque)
            if not (bloque["ID_EGRESO"].to_numpy() == extra["ID_EGRESO"].to_numpy()).all():
                raise SystemExit("Las columnas nuevas no están alineadas con la tabla depurada.")
            bloque = pd.concat([bloque, extra.iloc[:, 1:].reset_index(drop=True)], axis=1)
            salida = pa.Table.from_pandas(bloque, schema=esquema, preserve_index=False)
            if escritor is None:
                escritor = pq.ParquetWriter(temporal, salida.schema, compression="zstd")
            escritor.write_table(salida)
            print(f"  grupo {g + 1} de {origen.num_row_groups}: {len(bloque):,} filas", flush=True)
            del bloque, salida
    finally:
        if escritor is not None:
            escritor.close()
    temporal.replace(DESTINO)

    destino = pq.ParquetFile(DESTINO)
    muestra = ["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "FECHAALTA", "TIPOALTA", "DIAGNOSTICO1", "ES_CASO_ESTUDIO"]
    releido = pq.read_table(DESTINO, columns=list(nuevo.columns)).to_pandas()
    return [
        ("El archivo escrito tiene las mismas filas que la tabla depurada", destino.metadata.num_rows == origen.metadata.num_rows == escritas),
        ("Las columnas de la tabla depurada conservan su nombre, orden y tipo de dato",
         [(f.name, f.type) for f in destino.schema_arrow][:len(origen.schema_arrow)] == [(f.name, f.type) for f in origen.schema_arrow]),
        (f"Contenido idéntico al de la tabla depurada en {len(muestra)} columnas de control",
         pq.read_table(ORIGEN, columns=muestra).equals(pq.read_table(DESTINO, columns=muestra))),
        ("Las columnas nuevas releídas del archivo son iguales a las calculadas",
         all(releido[col].equals(nuevo[col]) for col in nuevo.columns)),
    ]


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def nombres_hospitales() -> dict:
    """Nombre de cada hospital según la tabla maestra del DEIS. Vacío si el archivo no está."""
    if not TABLA_MAESTRA.exists():
        return {}
    hoja = pd.read_excel(TABLA_MAESTRA, sheet_name="Hospitales", dtype=str).iloc[:, :2].dropna()
    return dict(zip(hoja.iloc[:, 0].str.strip(), hoja.iloc[:, 1].str.strip()))


def descripciones_grd() -> dict:
    """Descripción de cada código GRD (6 dígitos) según la tabla maestra del DEIS. Vacío si el archivo no está."""
    if not TABLA_MAESTRA.exists():
        return {}
    hoja = pd.read_excel(TABLA_MAESTRA, sheet_name="IR - GRD", dtype=str).iloc[:, :2].dropna()
    return dict(zip(hoja.iloc[:, 0].str.strip().str.zfill(6), hoja.iloc[:, 1].str.strip()))


def escribir_reporte(info: dict, par: dict) -> None:
    anios_txt = [str(a) for a in ANIOS]
    ventanas, larga, margen, elegida = par["ventanas_dias"], max(par["ventanas_dias"]), par["margen"], par["forma"]
    otra = next(f for f in FORMAS if f != elegida)
    casos, pos, con_dato = info["casos"], info["positivos"], info["con_dato"]
    nombres = list(pos)
    relacionadas = [k for k in nombres if k.endswith("_CDM")]
    ruta = ACTIVIDAD.name
    # Hospitales: sumas por hospital y tasa de cada variable (en %) en cada uno.
    hosp = info["hospitales"]
    por_hospital = hosp["por_hospital_anio"].drop(columns="ANIO").groupby("COD_HOSPITAL").sum()
    tasa_hospital = pd.DataFrame({k: 100 * por_hospital[f"pos_{k}"] / por_hospital[f"n_{k}"] for k in nombres})
    nombres_h = nombres_hospitales()

    def porcentaje(valor: float) -> str:
        return "—" if pd.isna(valor) else f"{valor:.2f}".replace(".", ",") + " %"
    no_planificados = " u ".join(f"`{t}`" for t in par["ingresos_no_planificados"])
    partos = " o ".join(par["grd_parto"])
    sesiones = " o ".join(par["sesiones"])
    cdm_excluidas = " y ".join(par["cdm_sin_relacionado"])

    def definicion(col: str) -> str:
        return f"{ventana_de(col)} días, " + ("relacionado (misma CDM)" if col.endswith("_CDM") else "por cualquier causa")

    cortes = "; ".join(f"{v} días: alta al menos {v + margen} días antes del cierre" for v in ventanas)

    def tabla_identificadores(q: dict) -> list[str]:
        """Calidad del identificador por año (sección 2)."""
        p = q["por_anio"]
        columnas = [*ANIOS, None]
        return [
            "**Calidad del identificador.** Si el identificador hubiera mejorado en 2023 y 2024, con menos egresos sin "
            "identificador o con identidad ambigua, se verían más reingresos aunque no hubiera más (revisión del profesor guía "
            "del 13 de octubre de 2026, punto 2.3). La tabla lo revisa por año del alta. Los egresos sin identificador o con "
            "identificador genérico no pueden ser caso de estudio ni contar como reingreso (E01 y E02); los de identidad "
            "ambigua sí, con su marca (D34).",
            tabla_md(["", *anios_txt, "Total"], [
                ["Egresos de la tabla depurada", *[fmt(p[a]["egresos"]) for a in columnas]],
                ["Sin identificador de paciente (E01)", *[pct(p[a]["sin_id"], p[a]["egresos"]) for a in columnas]],
                ["Con identificador genérico (E02)", *[pct(p[a]["generico"], p[a]["egresos"]) for a in columnas]],
                ["Con identidad ambigua", *[pct(p[a]["ambigua"], p[a]["egresos"]) for a in columnas]],
                ["Casos de estudio con identidad ambigua", *[pct(p[a]["casos_ambigua"], p[a]["casos"]) for a in columnas]],
                [f"`{q['variable']}`, todos los casos de estudio", *[pct(*p[a]["todos"][::-1]) for a in columnas]],
                [f"`{q['variable']}`, sin los casos con identidad ambigua", *[pct(*p[a]["sin_ambigua"][::-1]) for a in columnas]],
                [f"`{q['variable']}`, solo los casos con identidad ambigua", *[pct(*p[a]["solo_ambigua"][::-1]) for a in columnas]],
            ]),
        ]
    partes = [
        "# Etiquetado del reingreso (actividad 2.2, script 09)",
        f"Generado por `{ruta}/scripts/09_etiquetar.py`. Entrada: `data/processed/{ORIGEN.name}`. Salida: "
        f"`data/processed/{DESTINO.name}`. Umbrales: `{ruta}/reglas/{ARCHIVO_PARAMETROS.name}`. Las decisiones están en "
        f"`{ruta}/bitacora.md`.",
        "Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un episodio asistencial "
        "nuevo, y se cuentan los días entre el alta del caso y ese ingreso. El día 0 (ingreso el mismo día del alta) cuenta. "
        "Un ingreso que continúa un traslado no cuenta.",
        ("**Qué ingreso cuenta como reingreso:** solo el no planificado (regla completa en la sección 4)."
         if elegida == "NP" else "**Qué ingreso cuenta como reingreso:** todo ingreso, también los programados y los partos."),
        "**Reingreso relacionado:** se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio. "
        "Un ingreso con CDM 99 nunca cuenta como relacionado."
        + ("".join(f" Para esta comparación, las CDM {g} se consideran una sola." for g in par["grupos_cdm"])
           if par["grupos_cdm"] else " La comparación es literal: no se agrupa ninguna CDM."),
        f"**Censura:** un reingreso solo aparece en la base si termina antes del cierre del bloque. Por eso cada ventana exige "
        f"un margen de {margen} días además de sus propios días ({cortes}). Un caso de estudio que no alcanza el seguimiento de "
        "una ventana queda sin dato en las variables de esa ventana (sección 6).",

        "## 1. Las cuatro variables objetivo",
        f"Hay {fmt(casos)} casos de estudio. Cada variable se calcula sobre los que tienen seguimiento suficiente para su ventana."
        + (f" En las dos variables relacionadas, además, los casos de estudio de la CDM {cdm_excluidas} quedan sin dato: con la "
           "comparación en uso no pueden tener un reingreso de su misma CDM (sección 5; bitácora D38). Por eso tienen menos casos "
           "que las variables por cualquier causa." if par["cdm_sin_relacionado"] else ""),
        tabla_md(["Variable", "Definición", "Casos con dato", "Casos con reingreso", "%"],
                 [[f"`{k}`", definicion(k), fmt(con_dato[k]), fmt(pos[k]), pct(pos[k], con_dato[k])] for k in nombres]),
        "Las cuatro están contenidas unas en otras: la ventana de 30 días incluye los primeros 7, y «por cualquier causa» "
        f"incluye a los relacionados. Combinaciones de las cuatro variables en los {fmt(info['todas'])} casos de estudio que "
        "tienen dato en todas:",
        tabla_md([*[f"`{k}`" for k in nombres], "Casos de estudio", "%"],
                 [[*valores, fmt(n), pct(n, info["todas"])] for valores, n in info["combinaciones"]]),

        "## 2. Tasas por año del alta",
        "Porcentaje de los casos de estudio de cada año con seguimiento suficiente para la ventana.",
        tabla_md(["Definición", *anios_txt, "Total"],
                 [[definicion(k), *[pct(info["positivos_anio"][k].get(a, 0), info["con_dato_anio"][k].get(a, 0)) for a in ANIOS],
                   pct(pos[k], con_dato[k])] for k in nombres]
                 + [[f"Casos con seguimiento de {v} días", *[fmt(info["con_dato_anio"][f"REING_{v}D"].get(a, 0)) for a in ANIOS],
                     fmt(con_dato[f"REING_{v}D"])] for v in ventanas]),
        "2019 y 2020 forman el bloque A de identificadores y 2021 a 2024, el bloque B (D03). En 2020 y 2024 faltan las altas "
        "de las últimas semanas del año, por la censura.",
        f"**Hospitales incorporados.** {hosp['n_presentes']} hospitales están presentes todos los años y {hosp['n_incorporados']} se "
        "incorporan después (H05). Un reingreso en un hospital que todavía no informaba a la base no se ve, así que la "
        f"incorporación de hospitales puede subir la tasa medida. La tabla lo revisa para la variable de {larga} días por cualquier causa:",
        tabla_md(["Hospital del caso de estudio", *anios_txt, "Total"],
                 [[texto, *[pct(pos_a.get(a, 0), n_a.get(a, 0)) for a in ANIOS], pct(sum(pos_a.values()), sum(n_a.values()))]
                  for texto, n_a, pos_a in hosp["tendencia"]]),
        "La tercera fila es una cota inferior: descuenta todo caso cuyo primer reingreso ocurre en un hospital incorporado "
        "después, aunque tenga otro reingreso dentro de la ventana.",
        *(tabla_identificadores(info["identificadores"]) if "identificadores" in info else []),

        f"## 3. Días entre el alta y el primer reingreso (hasta {larga} días)",
        tabla_md(["Días", "Casos", "%"], [[txt, fmt(n), pct(n, sum(info["dias"].values()), 1)] for txt, n in info["dias"].items()]),
        f"El primer reingreso ocurre en un hospital distinto del que dio el alta en el {pct(*info['otro_hospital'], 1)} de los casos.",

        "## 4. Ingresos que cuentan y que no cuentan",
        "Regla del reingreso no planificado, en orden de precedencia. Las primeras condiciones prevalecen sobre las siguientes "
        "cuando un ingreso tiene señales contradictorias:",
        "\n".join([
            "1. El ingreso debe abrir un episodio asistencial nuevo (`PUEDE_SER_REINGRESO`): la continuación de un traslado no cuenta.",
            f"2. Si su código GRD (`IR_29301_COD_GRD`) comienza con {partos}, es un parto o una cesárea y no cuenta, cualquiera sea su tipo de ingreso.",
            f"3. Si su diagnóstico principal (`DIAGNOSTICO1`) comienza con {sesiones}, es una sesión de tratamiento y no cuenta, cualquiera sea su tipo de ingreso."
            if par["sesiones"] else "3. No se excluye ningún diagnóstico principal.",
            f"4. Cuenta si su tipo de ingreso (`TIPO_INGRESO`) es {no_planificados}.",
            "5. No cuenta si su tipo de ingreso es otro (ingreso programado) o si no tiene tipo de ingreso.",
        ]),
        f"Clasificación de los {fmt(info['ingresos'])} ingresos que abren un episodio:",
        tabla_md(["Clase del ingreso", "Ingresos", "%", "¿Cuenta como no planificado?"],
                 [[f"{k} (no es parto ni sesión)" if k in par["ingresos_no_planificados"] else k, fmt(v), pct(v, info["ingresos"], 1),
                   "Sí" if k in par["ingresos_no_planificados"] else "No"]
                  for k, v in sorted(info["ingresos_clase"].items(), key=lambda kv: -kv[1])]),
        "Ingresos con señales contradictorias o sin dato, resueltos por la precedencia anterior: "
        + "; ".join(f"{k}, {fmt(v)}" for k, v in info["contradictorios"].items()) + ".",
        f"Casos de estudio seguidos de algún ingreso dentro de {larga} días, según la clase del primero de esos ingresos:",
        tabla_md(["Primer ingreso posterior", "Casos", "%", "¿Cuenta como no planificado?"],
                 [[f"{k} (no es parto ni sesión)" if k in par["ingresos_no_planificados"] else k, fmt(v),
                   pct(v, sum(info["clase_primer_ingreso"].values()), 1), "Sí" if k in par["ingresos_no_planificados"] else "No"]
                  for k, v in sorted(info["clase_primer_ingreso"].items(), key=lambda kv: -kv[1])]),
        "Comparación de las cuatro variables según la forma de contar. La tabla de datos contiene solo la forma en uso; "
        "para cambiarla basta modificar `reingreso_solo_no_planificado` y volver a ejecutar este script."
        + (" Al contar todo ingreso, un parto también es reingreso, así que en esa forma los partos tienen dato en las variables "
           "relacionadas (D38): cada columna usa sus propios casos con dato." if par["cdm_sin_relacionado_np"] else ""),
        tabla_md(["Definición", f"{FORMAS[elegida]} (en uso)", "%", FORMAS[otra], "%"],
                 [[definicion(k), fmt(pos[k]), pct(pos[k], con_dato[k]), fmt(info["positivos_otra"][k]),
                   pct(info["positivos_otra"][k], info["con_dato_otra"][k])] for k in nombres]),

        "## 5. Reingreso relacionado: CDM sin reingreso relacionado posible y análisis de sensibilidad",
    ]
    if par["cdm_sin_relacionado_archivo"]:
        grd_txt = descripciones_grd()
        excluidas = " y ".join(par["cdm_sin_relacionado_archivo"])
        g, pr = info["grd_sin_relacionado"], info["primer_reingreso_sin_relacionado"]
        principales_cdm = pr["cdm"].head(6)
        otras_cdm = pr["con_reingreso"] - int(principales_cdm.sum())
        partes += [
            f"**CDM sin reingreso relacionado posible (bitácora H17 y D38).** La CDM {excluidas} contiene solo estos GRD "
            "(descripciones de la hoja IR - GRD de la tabla maestra del DEIS):",
            tabla_md(["GRD", "Descripción", "Egresos", "Casos de estudio"],
                     [[f"`{r.IR_29301_COD_GRD}`", grd_txt.get(r.IR_29301_COD_GRD, "(sin descripción)"), fmt(r.egresos), fmt(r.casos)]
                      for r in g.itertuples()]),
            f"Todos comienzan con {partos}: son partos o cesáreas, y un parto no cuenta como reingreso (sección 4). Así, ningún "
            f"reingreso puede ser de la CDM {excluidas}, y con la comparación literal sus casos de estudio tendrían 0 por construcción "
            "en las variables relacionadas: un modelo acertaría en todos ellos sin aprender nada sobre el reingreso. Por eso quedan "
            "sin dato en esas dos variables (parámetro `cdm_sin_relacionado`) y conservan las dos por cualquier causa"
            + ("." if par["cdm_sin_relacionado"] else ". En esta ejecución, la agrupación de CDM en uso los vuelve a incluir.")
            + " Las complicaciones del embarazo y del puerperio pertenecen a otras CDM"
            + (f", sobre todo a la {principales_cdm.index[0]}" if len(principales_cdm) else "") + ". De los "
            f"{fmt(pr['casos'])} casos de estudio de la CDM {excluidas} con seguimiento de {larga} días, {fmt(pr['con_reingreso'])} "
            f"({pct(pr['con_reingreso'], pr['casos'])}) tienen un reingreso no planificado dentro de {larga} días. CDM de su primer reingreso:",
            tabla_md(["CDM del primer reingreso", "Casos", "%"],
                     [[k, fmt(v), pct(v, pr["con_reingreso"], 1)] for k, v in principales_cdm.items()]
                     + ([["Otras", fmt(otras_cdm), pct(otras_cdm, pr["con_reingreso"], 1)]] if otras_cdm else [])),
            "GRD y diagnósticos principales más frecuentes de esos primeros reingresos:",
            tabla_md(["GRD", "Descripción", "Casos", "%"],
                     [[f"`{k}`", grd_txt.get(k, "(sin descripción)"), fmt(v), pct(v, pr["con_reingreso"], 1)] for k, v in pr["grd"].items()]),
            tabla_md(["Diagnóstico principal (3 caracteres)", "Casos", "%"],
                     [[f"`{k}`", fmt(v), pct(v, pr["con_reingreso"], 1)] for k, v in pr["diagnosticos"].items()]),
        ]
    if info["comparacion"]:
        comp, n_comp = info["positivos_comparacion"], info["con_dato_comparacion"]
        en_uso = ("Con las CDM " + "; ".join(par["grupos_cdm"]) + " como una sola") if par["grupos_cdm"] else "Misma CDM, literal"

        def celdas(valor, n) -> list[str]:
            return ["sin dato", "—"] if valor is None else [fmt(valor), pct(valor, n)]
        partes += [
            "**Análisis de sensibilidad.** La tabla compara el reingreso relacionado según la definición en uso con otra "
            "forma de comparar las CDM (parámetros `cdm_agrupadas` y `cdm_sensibilidad`; bitácora H17, D31 y D38). Una CDM sin "
            "reingreso relacionado posible vuelve a tener dato cuando la comparación la une con otra, así que cada forma de "
            "comparar tiene sus propios casos con dato.",
            tabla_md(["Variable", f"{en_uso} (en uso): casos con dato", "Con reingreso", "%",
                      f"{info['comparacion']}: casos con dato", "Con reingreso", "%"],
                     [[f"`{k}`", fmt(con_dato[k]), fmt(pos[k]), pct(pos[k], con_dato[k]), fmt(n_comp[k]), fmt(comp[k]), pct(comp[k], n_comp[k])]
                      for k in relacionadas]),
            f"Detalle de la ventana de {larga} días en los casos de estudio de las CDM que la comparación agrupa:",
            tabla_md(["CDM del caso de estudio", "Casos con seguimiento", "Con reingreso por cualquier causa", "%",
                      f"Relacionado: {en_uso[0].lower() + en_uso[1:]} (en uso)", "%", f"Relacionado: {info['comparacion'][0].lower() + info['comparacion'][1:]}", "%"],
                     [[x, fmt(n), fmt(todo), pct(todo, n), *celdas(uso, n), *celdas(otro, n)]
                      for x, n, todo, uso, otro in info["cdm_involucradas"]]),
        ]
    else:
        partes.append("La comparación es literal y no se definió ninguna agrupación de CDM para el análisis de sensibilidad.")

    def celda_censura(valor) -> list[str]:
        return ["—", "—"] if valor is None else [fmt(valor[0]), pct(valor[1], valor[0], 1)]

    partes += [
        "## 6. Verificación de la censura",
        "Los archivos están organizados por año de alta: un reingreso que comienza dentro de la ventana pero termina después "
        "del cierre del bloque queda en un archivo que no se tiene, y el caso parece no haber reingresado. Para medirlo se "
        f"usan los años cuyo año siguiente sí está en la base con el mismo identificador ({', '.join(str(a) for a in info['anios_interiores'])}): "
        "se cuenta qué parte de los reingresos reales no se vería si la base terminara el 31 de diciembre del año del alta.",
        tabla_md(["Días entre el alta y el 31 de diciembre", "Casos de estudio",
                  *[t for v in ventanas for t in (f"Reingresos a {v} días", "No se verían")]],
                 [[f["tramo"], fmt(f["casos"]), *[x for v in ventanas for x in celda_censura(f[v])]] for f in info["censura"]]),
        f"Con el margen de {margen} días, las variables de {' y '.join(str(v) for v in ventanas)} días exigen "
        f"{' y '.join(str(v + margen) for v in ventanas)} días entre el alta y el cierre del bloque, respectivamente. "
        "La tabla permite ver cuánto se perdería con un margen menor (`censura_margen_dias`).",

        "## 7. Tasas según las características del caso de estudio",
        "Descriptivo, para revisar que las variables se comportan de forma razonable. Cada porcentaje usa los casos con "
        "seguimiento suficiente para esa variable.",
    ]
    for nombre, tabla in info["por_grupo"].items():
        partes.append(tabla_md([nombre, "Casos de estudio", *[f"`{k}`" for k in nombres]],
                               [[g, fmt(fila["n"]), *[pct(fila[f"pos_{k}"], fila[f"n_{k}"]) for k in nombres]] for g, fila in tabla.iterrows()]))
    partes += [
        f"Por hospital: cómo se reparte la tasa de cada variable entre los {len(tasa_hospital)} hospitales. El detalle está en el "
        f"anexo y, por hospital y año, en `{ruta}/reportes/09_tasas_por_hospital.csv`.",
        tabla_md(["Variable", "Mínimo", "Percentil 25", "Mediana", "Percentil 75", "Máximo"],
                 [[f"`{k}`", *[porcentaje(tasa_hospital[k].quantile(q)) for q in (0, 0.25, 0.5, 0.75, 1)]] for k in nombres]),
        "## 8. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{v.replace('|', ' / ')}`" if v else "(vacío)", desc] for k, (v, desc) in par["descripcion"].items()]),
        "Cierre de cada bloque de identificador: " + "; ".join(f"{b}, {f:%d-%m-%Y}" for b, f in CIERRE_BLOQUE.items()) + ".",

        "## 9. Columnas nuevas",
        tabla_md(["Columna", "Contenido"], [
            *[[f"`{k}`", f"Reingreso dentro de {definicion(k)}. 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de "
               f"{ventana_de(k) + margen} días del cierre del bloque."
               + (f" También sin dato en los casos de estudio de la CDM {cdm_excluidas}, que no pueden tener un reingreso "
                  "relacionado (D38)." if k.endswith("_CDM") and par["cdm_sin_relacionado"] else "")] for k in nombres],
            ["`DIAS_REING`", "Días entre el alta y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia "
                             "dentro del bloque. Sin dato si no hay ninguno."],
            ["`ID_EGRESO_REING`", "`ID_EGRESO` de ese ingreso, para poder revisar cada par."],
        ]),
        "Todas quedan sin dato en los egresos que no son caso de estudio. Describen lo que ocurre después del alta: son "
        "variables objetivo o de trazabilidad y **no deben usarse como variables predictoras**.",

        "## 10. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),
        f"El recorrido de la ruta 2 necesitó {info['pasos']} pasos: ningún caso de estudio tiene más de {info['pasos'] - 1} ingresos "
        f"posteriores dentro de {larga} días.",

        "## Anexo. Tasas por hospital",
        "Casos de estudio según el hospital que dio el alta. Cada porcentaje usa los casos con seguimiento suficiente para esa "
        "variable. Los nombres son los de la tabla maestra del DEIS.",
        tabla_md(["Hospital", "Años", "Casos de estudio", *[f"`{k}`" for k in nombres]],
                 [[f"{cod} {nombres_h.get(cod, '(sin nombre en la tabla maestra)')}",
                   "Todos" if f["ANIOS"] == len(ANIOS) else str(f["DESDE"]) if f["DESDE"] == f["HASTA"] else f"{f['DESDE']} a {f['HASTA']}",
                   fmt(por_hospital.loc[cod, "n"]), *[porcentaje(tasa_hospital.loc[cod, k]) for k in nombres]]
                  for cod, f in hosp["presencia"].loc[por_hospital.index].iterrows()]),
    ]
    salida = DIR_REPORTS / "09_etiquetado.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")

    # Tasas por hospital y año, con el mismo formato que las tablas de reglas (UTF-8 con BOM y punto y coma).
    detalle = hosp["por_hospital_anio"]
    tabla = pd.DataFrame({"COD_HOSPITAL": detalle["COD_HOSPITAL"], "HOSPITAL": detalle["COD_HOSPITAL"].map(nombres_h).fillna(""),
                          "ANIO": detalle["ANIO"], "CASOS_DE_ESTUDIO": detalle["n"]})
    for v in ventanas:
        tabla[f"CASOS_CON_SEGUIMIENTO_{v}D"] = detalle[f"n_REING_{v}D"]
    for k in relacionadas:                     # sin las CDM de cdm_sin_relacionado (D38)
        tabla[f"CASOS_CON_DATO_{k}"] = detalle[f"n_{k}"]
    for k in nombres:
        tabla[f"N_{k}"] = detalle[f"pos_{k}"]
        tabla[f"TASA_{k}"] = (100 * detalle[f"pos_{k}"] / detalle[f"n_{k}"]).round(2)
    salida_csv = DIR_REPORTS / "09_tasas_por_hospital.csv"
    tabla.to_csv(salida_csv, sep=";", index=False, encoding="utf-8-sig", lineterminator="\r\n", decimal=",", float_format="%.2f")
    print(f"Tasas por hospital y año guardadas en {salida_csv}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par = cargar_parametros()
    print("Etiquetando...", flush=True)
    nuevo, info = etiquetar(par)
    larga = max(par["ventanas_dias"])
    print(f"  {info['casos']:,} casos de estudio; {info['positivos'][f'REING_{larga}D']:,} con reingreso a {larga} días "
          f"({FORMAS[par['forma']].lower()}) ({time.time() - inicio:.0f} s)", flush=True)
    info["identificadores"] = calidad_identificador(nuevo, f"REING_{larga}D")
    print("Escribiendo...", flush=True)
    info["verificaciones"] += escribir(nuevo)
    escribir_reporte(info, par)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
