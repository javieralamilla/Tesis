"""Etiquetado del reingreso (actividad 2.2, script 09).

Parte de data/processed/grd_depurado.parquet y deja data/processed/grd_etiquetado.parquet con las
cuatro variables objetivo de cada caso de estudio (bitácora D20, D25 y D26):

  REING_7D        reingreso dentro de 7 días, por cualquier causa
  REING_7D_CDM    reingreso dentro de 7 días, relacionado con el diagnóstico (misma CDM)
  REING_30D       reingreso dentro de 30 días, por cualquier causa
  REING_30D_CDM   reingreso dentro de 30 días, relacionado con el diagnóstico (misma CDM)

Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un
episodio asistencial nuevo (PUEDE_SER_REINGRESO) y se cuentan los días entre el alta del caso y
ese ingreso. Con reingreso_solo_no_planificado = SI solo cuentan los ingresos no planificados
(de un tipo no programado y que no sean un parto); con NO, cuenta todo ingreso. El reingreso
relacionado se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio.
Las variables valen 1 o 0 en los casos de estudio y quedan sin dato en los demás egresos.

Los umbrales están en reglas/parametros.csv. El reporte reportes/09_etiquetado.md muestra las
tasas por definición y por año, y las compara con las de la otra forma de contar.

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
ANIOS = list(range(2019, 2025))

# Las dos formas de contar un ingreso como reingreso. Se calculan ambas; se guarda la elegida.
FORMAS = {"NP": "Solo ingresos no planificados", "TODO": "Todo ingreso"}
PARAMETROS = ["ventanas_dias", "reingreso_solo_no_planificado", "ingresos_no_planificados", "grd_parto",
              "cdm_agrupadas", "censura_dias"]
COLUMNAS = ["ID_EGRESO", "ANIO_ARCHIVO", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO",
            "COD_HOSPITAL", "TIPO_ACTIVIDAD", "TIPO_INGRESO", "FECHA_INGRESO", "FECHAALTA", "TIPOALTA",
            "IR_29301_COD_GRD", "CDM"]
TRAMOS_DIAS = [(0, 0, "El mismo día"), (1, 1, "1 día"), (2, 3, "2 a 3 días"), (4, 7, "4 a 7 días"),
               (8, 14, "8 a 14 días"), (15, 30, "15 a 30 días")]


def cargar_parametros() -> dict:
    with open(ARCHIVO_PARAMETROS, encoding="utf-8-sig", newline="") as f:
        filas = {fila["parametro"]: fila for fila in csv.DictReader(f, delimiter=";")}
    faltan = sorted(set(PARAMETROS) - set(filas))      # el archivo también tiene parámetros de otros scripts
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")

    def lista(nombre: str) -> list[str]:
        return [v.strip().upper() for v in filas[nombre]["valor"].split("|") if v.strip()]

    solo_np = filas["reingreso_solo_no_planificado"]["valor"].strip().upper()
    if solo_np not in ("SI", "NO"):
        raise SystemExit(f"reingreso_solo_no_planificado: se esperaba SI o NO y dice '{solo_np}'.")
    # cdm_agrupadas: grupos separados por |, y las CDM de cada grupo por +. Cada CDM se lleva a la primera de su grupo.
    grupos = [g.split("+") for g in lista("cdm_agrupadas")]
    par = {"ventanas_dias": sorted(int(v) for v in lista("ventanas_dias")),
           "forma": "NP" if solo_np == "SI" else "TODO",
           "ingresos_no_planificados": lista("ingresos_no_planificados"),
           "grd_parto": lista("grd_parto"),
           "cdm_agrupadas": {c.strip(): g[0].strip() for g in grupos for c in g},
           "grupos_cdm": [" y ".join(c.strip() for c in g) for g in grupos],
           "censura_dias": int(filas["censura_dias"]["valor"])}
    if not par["ventanas_dias"] or max(par["ventanas_dias"]) > par["censura_dias"]:
        raise SystemExit("La ventana más larga no puede superar censura_dias: esos casos no tienen seguimiento completo.")
    par["descripcion"] = {nombre: (filas[nombre]["valor"].strip(), filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    return par


def a_dias(fechas: pd.Series) -> np.ndarray:
    return fechas.to_numpy().astype("datetime64[D]").astype("int64")


def conteo(mascara: np.ndarray, valores: pd.Series) -> dict:
    return {k: int(v) for k, v in valores[mascara].value_counts(dropna=False).items()}


# ------------------------------------------------------------------ etiquetado
def etiquetar(par: dict) -> tuple[pd.DataFrame, dict]:
    """Devuelve las columnas nuevas (una fila por egreso, en el orden de la tabla depurada) y las cifras del reporte."""
    d = pq.read_table(ORIGEN, columns=COLUMNAS).to_pandas()
    ventanas, larga, elegida = par["ventanas_dias"], max(par["ventanas_dias"]), par["forma"]

    # Ingresos que abren un episodio asistencial, en orden dentro de cada persona.
    ing = d[d["PUEDE_SER_REINGRESO"]].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    n = len(ing)
    persona = ing["ID_PERSONA"].to_numpy(dtype="int64")
    ultimo = np.r_[persona[1:] != persona[:-1], True]             # último ingreso de cada persona
    inicio = a_dias(ing["FECHA_INGRESO"])
    egreso = ing["ID_EGRESO"].to_numpy()
    hospital = ing["COD_HOSPITAL"].to_numpy()
    cdm_valida = d["CDM"].where(d["CDM"] != "99")                 # la CDM 99 nunca cuenta como relacionada
    categorias = sorted(cdm_valida.dropna().unique())
    literal = pd.Series(pd.Categorical(cdm_valida, categories=categorias).codes, index=d.index)    # -1: sin CDM o CDM 99
    # Para comparar, las CDM agrupadas en los parámetros cuentan como una sola.
    agrupada = pd.Series(pd.Categorical(cdm_valida.replace(par["cdm_agrupadas"]), categories=categorias).codes, index=d.index)
    cdm, cdm_literal = agrupada[ing.index].to_numpy(), literal[ing.index].to_numpy()
    parto = ing["IR_29301_COD_GRD"].str.startswith(tuple(par["grd_parto"]), na=False).to_numpy()
    no_programado = ing["TIPO_INGRESO"].isin(par["ingresos_no_planificados"]).to_numpy()
    cuenta = {"NP": no_programado & ~parto, "TODO": np.ones(n, dtype=bool)}
    clase = np.select([parto, ing["TIPO_INGRESO"].isna().to_numpy()], ["PARTO O CESÁREA", "(sin dato)"],
                      default=ing["TIPO_INGRESO"].fillna("").to_numpy())

    # Casos de estudio y posición de su episodio en la lista de ingresos.
    es_caso = d["ES_CASO_ESTUDIO"].to_numpy()
    c = d[es_caso]
    nc = len(c)
    pos = pd.Series(np.arange(n), index=egreso).reindex(c["ID_EPISODIO"].to_numpy(dtype="int64")).to_numpy()
    if np.isnan(pos).any():
        raise SystemExit("Hay casos de estudio sin episodio asistencial: revisar el script 08.")
    pos = pos.astype("int64")
    c_alta = a_dias(c["FECHAALTA"])
    c_cdm, c_cdm_literal = agrupada[c.index].to_numpy(), literal[c.index].to_numpy()

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
    misma_cdm_literal = {k: np.zeros(nc, dtype=bool) for k in claves}        # sin agrupar CDM, para el reporte
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
        relacionado_literal = activo & (cdm_literal[k] == c_cdm_literal) & (cdm_literal[k] >= 0)
        for forma, vale in cuenta.items():
            for v in ventanas:
                dentro = activo & (distancia <= v) & vale[k]
                alguno[(forma, v)] |= dentro
                misma_cdm[(forma, v)] |= dentro & relacionado
                misma_cdm_literal[(forma, v)] |= dentro & relacionado_literal

    def variables(forma: str, relacion: dict) -> dict[str, np.ndarray]:
        salida = {}
        for v in ventanas:
            salida[f"REING_{v}D"] = hay[forma] & (dias[forma] <= v)
            salida[f"REING_{v}D_CDM"] = relacion[(forma, v)]
        return salida

    etiquetas = variables(elegida, misma_cdm)
    otra = next(f for f in FORMAS if f != elegida)

    # Columnas nuevas: con dato solo en los casos de estudio.
    def columna(valores: np.ndarray, tipo: str, con_dato: np.ndarray | None = None) -> pd.arrays.IntegerArray:
        lleno = np.zeros(len(d), dtype=tipo)
        lleno[es_caso] = valores
        falta = ~es_caso
        if con_dato is not None:
            falta[es_caso] = ~con_dato
        return pd.arrays.IntegerArray(lleno, falta)

    nuevo = pd.DataFrame({"ID_EGRESO": d["ID_EGRESO"]})
    for nombre, valores in etiquetas.items():
        nuevo[nombre] = columna(valores.astype("int8"), "int8")
    nuevo["DIAS_REING"] = columna(dias[elegida].astype("int16"), "int16", hay[elegida])
    nuevo["ID_EGRESO_REING"] = columna(egreso[primero[elegida]], "int64", hay[elegida])

    # ---------------------------------------------------------------- cifras del reporte
    anio = c["ANIO_ARCHIVO"]
    nombres = list(etiquetas)
    en_ventana = hay[elegida] & (dias[elegida] <= larga)
    con_ingreso = hay["TODO"] & (dias["TODO"] <= larga)
    combinaciones = pd.DataFrame({k: v.astype(int) for k, v in etiquetas.items()}).value_counts().sort_index(ascending=False)
    info = {
        "egresos": len(d), "casos": nc, "casos_anio": conteo(np.ones(nc, dtype=bool), anio), "pasos": paso,
        "positivos": {k: int(v.sum()) for k, v in etiquetas.items()},
        "positivos_anio": {k: conteo(v, anio) for k, v in etiquetas.items()},
        "positivos_otra": {k: int(v.sum()) for k, v in variables(otra, misma_cdm).items()},
        "positivos_literal": {k: int(v.sum()) for k, v in variables(elegida, misma_cdm_literal).items()},
        "combinaciones": [(list(k), int(v)) for k, v in combinaciones.items()],
        "dias": {txt: int((en_ventana & (dias[elegida] >= a) & (dias[elegida] <= b)).sum()) for a, b, txt in TRAMOS_DIAS if a <= larga},
        "otro_hospital": (int((en_ventana & (hospital[primero[elegida]] != c["COD_HOSPITAL"].to_numpy())).sum()), int(en_ventana.sum())),
        "clase_primer_ingreso": conteo(con_ingreso, pd.Series(clase[primero["TODO"]])),
        "por_grupo": {},
    }
    for nombre, col in (("Tipo de actividad", "TIPO_ACTIVIDAD"), ("Tipo de ingreso", "TIPO_INGRESO"), ("Tipo de alta", "TIPOALTA"), ("CDM", "CDM")):
        grupo = c[col].fillna("(sin dato)").to_numpy()
        tabla = pd.DataFrame({"n": 1, **etiquetas}).groupby(grupo).sum()
        info["por_grupo"][nombre] = tabla.sort_index() if col == "CDM" else tabla.sort_values("n", ascending=False)

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
    info["verificaciones"] = [
        ("Las variables tienen dato en todos los casos de estudio y solo en ellos",
         all((nuevo[k].notna().to_numpy() == es_caso).all() for k in nombres)),
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


def escribir_reporte(info: dict, par: dict) -> None:
    anios_txt = [str(a) for a in ANIOS]
    ventanas, larga, elegida = par["ventanas_dias"], max(par["ventanas_dias"]), par["forma"]
    otra = next(f for f in FORMAS if f != elegida)
    casos, pos, pos_anio = info["casos"], info["positivos"], info["positivos_anio"]
    nombres = list(pos)
    ruta = ACTIVIDAD.name
    no_planificados = " u ".join(f"`{t}`" for t in par["ingresos_no_planificados"])
    partos = " ni con ".join(par["grd_parto"])

    def definicion(col: str) -> str:
        dias = col.split("_")[1][:-1]
        return f"{dias} días, " + ("relacionado (misma CDM)" if col.endswith("_CDM") else "por cualquier causa")

    partes = [
        "# Etiquetado del reingreso (actividad 2.2, script 09)",
        f"Generado por `{ruta}/scripts/09_etiquetar.py`. Entrada: `data/processed/{ORIGEN.name}`. Salida: "
        f"`data/processed/{DESTINO.name}`. Umbrales: `{ruta}/reglas/{ARCHIVO_PARAMETROS.name}`. Las decisiones están en "
        f"`{ruta}/bitacora.md` (D20, D25 y D26).",
        "Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un episodio asistencial "
        "nuevo, y se cuentan los días entre el alta del caso y ese ingreso. El día 0 (ingreso el mismo día del alta) cuenta. "
        "Un ingreso que continúa un traslado no cuenta.",
        ("**Qué ingreso cuenta como reingreso:** solo el no planificado, es decir, de tipo " + no_planificados
         + f" y cuyo GRD no es de parto ni de cesárea (no comienza con {partos}). Los ingresos programados y los partos no cuentan."
         if elegida == "NP" else "**Qué ingreso cuenta como reingreso:** todo ingreso, también los programados y los partos."),
        "**Reingreso relacionado:** se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio. "
        "Un ingreso con CDM 99 nunca cuenta como relacionado."
        + "".join(f" Para esta comparación, las CDM {g} se consideran una sola." for g in par["grupos_cdm"]),

        "## 1. Las cuatro variables objetivo",
        f"Sobre {fmt(casos)} casos de estudio.",
        tabla_md(["Variable", "Definición", "Casos con reingreso", "%"],
                 [[f"`{k}`", definicion(k), fmt(pos[k]), pct(pos[k], casos)] for k in nombres]),
        "Las cuatro están contenidas unas en otras: la ventana de 30 días incluye los primeros 7, y «por cualquier causa» "
        "incluye a los relacionados. Casos de estudio según la combinación de las cuatro variables:",
        tabla_md([*[f"`{k}`" for k in nombres], "Casos de estudio", "%"],
                 [[*valores, fmt(n), pct(n, casos)] for valores, n in info["combinaciones"]]),

        "## 2. Tasas por año del alta",
        "Porcentaje de los casos de estudio de cada año.",
        tabla_md(["Definición", *anios_txt, "Total"],
                 [[definicion(k), *[pct(pos_anio[k].get(a, 0), info["casos_anio"][a]) for a in ANIOS], pct(pos[k], casos)] for k in nombres]
                 + [["Casos de estudio", *[fmt(info["casos_anio"][a]) for a in ANIOS], fmt(casos)]]),
        "Los años 2020 y 2024 no incluyen las altas de diciembre (censura, D22). 2019 y 2020 forman el bloque A de identificadores "
        "y 2021 a 2024, el bloque B (D03).",

        f"## 3. Días entre el alta y el primer reingreso (hasta {larga} días)",
        tabla_md(["Días", "Casos", "%"], [[txt, fmt(n), pct(n, sum(info["dias"].values()), 1)] for txt, n in info["dias"].items()]),
        f"El primer reingreso ocurre en un hospital distinto del que dio el alta en el {pct(*info['otro_hospital'], 1)} de los casos.",

        "## 4. Ingresos que cuentan y que no cuentan",
        f"Casos de estudio seguidos de algún ingreso dentro de {larga} días, según el tipo del primero de esos ingresos:",
        tabla_md(["Primer ingreso posterior", "Casos", "%", "¿Es no planificado?"],
                 [[f"{k} (no es parto)" if k in par["ingresos_no_planificados"] else k, fmt(v),
                   pct(v, sum(info["clase_primer_ingreso"].values()), 1), "Sí" if k in par["ingresos_no_planificados"] else "No"]
                  for k, v in sorted(info["clase_primer_ingreso"].items(), key=lambda kv: -kv[1])]),
        "Comparación de las cuatro variables según la forma de contar. La tabla de datos contiene solo la forma en uso; "
        "para cambiarla basta modificar `reingreso_solo_no_planificado` y volver a ejecutar este script.",
        tabla_md(["Definición", f"{FORMAS[elegida]} (en uso)", "%", FORMAS[otra], "%"],
                 [[definicion(k), fmt(pos[k]), pct(pos[k], casos), fmt(info["positivos_otra"][k]), pct(info["positivos_otra"][k], casos)]
                  for k in nombres]),
    ]
    partes.append("## 5. Agrupación de CDM en el reingreso relacionado")
    if par["grupos_cdm"]:
        literal = info["positivos_literal"]
        relacionadas = [k for k in nombres if k.endswith("_CDM")]
        partes += [
            "La CDM 14 contiene solo partos y cesáreas, y las complicaciones del posparto pertenecen a la CDM 13: sin agrupar, "
            "un parto nunca podría tener un reingreso relacionado. Variables de reingreso relacionado con las CDM "
            + "; ".join(par["grupos_cdm"]) + " consideradas una sola (en uso) y sin agruparlas:",
            tabla_md(["Variable", "Sin agrupar", "Con la agrupación (en uso)", "Diferencia"],
                     [[f"`{k}`", fmt(literal[k]), fmt(pos[k]), fmt(pos[k] - literal[k])] for k in relacionadas]),
        ]
    else:
        partes.append("No se agrupa ninguna CDM (`cdm_agrupadas` vacío): la CDM del reingreso se compara tal cual con la del caso "
                      "de estudio. Como la CDM 14 contiene solo partos y cesáreas, y las complicaciones del posparto pertenecen "
                      "a la CDM 13, un parto no puede tener un reingreso no planificado relacionado.")
    partes += [
        "## 6. Tasas según las características del caso de estudio",
        "Descriptivo, para revisar que las variables se comportan de forma razonable.",
    ]
    for nombre, tabla in info["por_grupo"].items():
        partes.append(tabla_md([nombre, "Casos de estudio", *[f"`{k}`" for k in nombres]],
                               [[g, fmt(fila["n"]), *[pct(fila[k], fila["n"]) for k in nombres]] for g, fila in tabla.iterrows()]))
    partes += [
        "## 7. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{v.replace('|', ' / ')}`" if v else "(vacío)", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 8. Columnas nuevas",
        tabla_md(["Columna", "Contenido"], [
            *[[f"`{k}`", f"Reingreso dentro de {definicion(k)}. 1 = sí, 0 = no."] for k in nombres],
            ["`DIAS_REING`", "Días entre el alta y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia "
                             "dentro del bloque. Sin dato si no hay ninguno."],
            ["`ID_EGRESO_REING`", "`ID_EGRESO` de ese ingreso, para poder revisar cada par."],
        ]),
        "Todas quedan sin dato en los egresos que no son caso de estudio. Describen lo que ocurre después del alta: son "
        "variables objetivo o de trazabilidad y **no deben usarse como variables predictoras**.",

        "## 9. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),
        f"El recorrido de la ruta 2 necesitó {info['pasos']} pasos: ningún caso de estudio tiene más de {info['pasos'] - 1} ingresos "
        f"posteriores dentro de {larga} días.",
    ]
    salida = DIR_REPORTS / "09_etiquetado.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par = cargar_parametros()
    print("Etiquetando...", flush=True)
    nuevo, info = etiquetar(par)
    larga = max(par["ventanas_dias"])
    print(f"  {info['casos']:,} casos de estudio; {info['positivos'][f'REING_{larga}D']:,} con reingreso a {larga} días "
          f"({FORMAS[par['forma']].lower()}) ({time.time() - inicio:.0f} s)", flush=True)
    print("Escribiendo...", flush=True)
    info["verificaciones"] += escribir(nuevo)
    escribir_reporte(info, par)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
