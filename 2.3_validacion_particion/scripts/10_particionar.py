"""Partición inicial y reserva del conjunto de prueba (actividad 2.3, script 10).

Parte de data/processed/grd_etiquetado.parquet y reparte a los pacientes entre un conjunto de
desarrollo (80 %) y un conjunto de prueba (20 %), que se aparta hasta la evaluación final:

  1. Unidad de reparto. Con agrupar_por_nacimiento = SI, todos los identificadores de paciente
     con la misma fecha de nacimiento y el mismo sexo van juntos al mismo conjunto. Así todos
     los egresos de un identificador quedan en un solo conjunto, y también los de una persona
     que tiene un identificador en cada bloque (2019-2020 y 2021-2024). Con NO, la unidad es
     el identificador.
  2. Estratificación. Dentro de cada año de nacimiento y sexo, las unidades se ordenan por su
     tasa de reingreso a 30 días y se toma una de cada cinco para prueba, con un punto de
     partida al azar fijado por la semilla del proyecto.
  3. Salidas. data/processed/particion.parquet indica el conjunto de cada egreso;
     data/processed/desarrollo.parquet y data/reserva/prueba.parquet contienen los egresos de
     cada conjunto con todas las columnas, más GRUPO_PARTICION.

Los parámetros están en reglas/parametros.csv. El reporte reportes/10_particion.md compara la
composición y las tasas de reingreso de los dos conjuntos.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.3_validacion_particion\\scripts\\10_particionar.py
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
DIR_RESERVA = RAIZ / "data" / "reserva"
DIR_REPORTS = ACTIVIDAD / "reportes"
ORIGEN = DIR_PROCESSED / "grd_etiquetado.parquet"
PARTICION = DIR_PROCESSED / "particion.parquet"
DESARROLLO = DIR_PROCESSED / "desarrollo.parquet"
PRUEBA = DIR_RESERVA / "prueba.parquet"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
ANIOS = list(range(2019, 2025))

CONJUNTOS = ["DESARROLLO", "PRUEBA"]
COLUMNAS = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "ID_PACIENTE", "ID_PERSONA", "SEXO", "FECHA_NACIMIENTO",
            "FECHA_INGRESO", "TIPO_ACTIVIDAD", "TIPO_INGRESO", "CDM", "ES_CASO_ESTUDIO"]
EDADES = [(-1, 0, "Menos de 1 año"), (1, 14, "1 a 14 años"), (15, 44, "15 a 44 años"), (45, 64, "45 a 64 años"),
          (65, 79, "65 a 79 años"), (80, 200, "80 años o más")]


def cargar_parametros() -> dict:
    with open(ARCHIVO_PARAMETROS, encoding="utf-8-sig", newline="") as f:
        filas = {fila["parametro"]: fila for fila in csv.DictReader(f, delimiter=";")}
    agrupar = filas["agrupar_por_nacimiento"]["valor"].strip().upper()
    if agrupar not in ("SI", "NO"):
        raise SystemExit(f"agrupar_por_nacimiento: se esperaba SI o NO y dice '{agrupar}'.")
    par = {"semilla": int(filas["semilla"]["valor"]), "prueba_una_de_cada": int(filas["prueba_una_de_cada"]["valor"]),
           "agrupar_por_nacimiento": agrupar == "SI"}
    if par["prueba_una_de_cada"] < 2:
        raise SystemExit("prueba_una_de_cada debe ser 2 o más.")
    par["descripcion"] = {nombre: (fila["valor"].strip(), fila["descripcion"]) for nombre, fila in filas.items()}
    return par


def moda(df: pd.DataFrame, col: str) -> pd.Series:
    """Valor más frecuente de una columna en cada identificador; si empatan, el menor."""
    n = df.groupby(["ID_PACIENTE", col], sort=True).size().reset_index(name="n")
    n = n.sort_values(["ID_PACIENTE", "n", col], ascending=[True, False, True])
    return n.drop_duplicates("ID_PACIENTE").set_index("ID_PACIENTE")[col]


def conteo(valores: pd.Series) -> dict:
    return {k: int(v) for k, v in valores.value_counts(dropna=False).items()}


# ------------------------------------------------------------------ partición
def particionar(par: dict) -> tuple[pd.DataFrame, dict]:
    """Devuelve el conjunto de cada egreso con persona (en el orden de la tabla etiquetada) y las cifras del reporte."""
    objetivos = [c for c in pq.read_schema(ORIGEN).names if c.startswith("REING_")]
    # Se estratifica por el reingreso por cualquier causa de la ventana más larga.
    estratifica = max((c for c in objetivos if not c.endswith("_CDM")), key=lambda c: int(c.split("_")[1][:-1]))
    d = pq.read_table(ORIGEN, columns=COLUMNAS + objetivos).to_pandas()
    p = d[d["ID_PERSONA"].notna()].copy()
    p["ID_PACIENTE"] = p["ID_PACIENTE"].astype("int64")

    # 1. Unidad de reparto de cada identificador: su sexo y su fecha de nacimiento más frecuentes.
    por_id = pd.DataFrame(index=pd.Index(np.sort(p["ID_PACIENTE"].unique()), name="ID_PACIENTE"))
    por_id["SEXO"] = moda(p, "SEXO").reindex(por_id.index).fillna("?")
    por_id["FNAC"] = moda(p, "FECHA_NACIMIENTO").reindex(por_id.index)
    con_fecha = por_id["FNAC"].notna()
    if par["agrupar_por_nacimiento"]:
        unidad = por_id[con_fecha].groupby(["SEXO", "FNAC"], sort=True).ngroup()
        resto = pd.Series(np.arange((~con_fecha).sum()) + (unidad.max() + 1 if len(unidad) else 0), index=por_id.index[~con_fecha])
        por_id["UNIDAD"] = pd.concat([unidad, resto]).reindex(por_id.index).astype("int64")   # sin fecha: una unidad por identificador
    else:
        por_id["UNIDAD"] = np.arange(len(por_id))
    por_id["ANIO_NAC"] = por_id["FNAC"].dt.year.fillna(0).astype("int64")
    p["UNIDAD"] = por_id["UNIDAD"].reindex(p["ID_PACIENTE"]).to_numpy()

    # 2. Estratos y tasa de reingreso de cada unidad.
    casos = p[p["ES_CASO_ESTUDIO"]]
    u = por_id.groupby("UNIDAD").agg(SEXO=("SEXO", "first"), ANIO_NAC=("ANIO_NAC", "first"), identificadores=("SEXO", "size"))
    u["casos"] = casos.groupby("UNIDAD").size().reindex(u.index, fill_value=0)
    u["positivos"] = casos.groupby("UNIDAD")[estratifica].sum().reindex(u.index, fill_value=0).astype("int64")
    u["tasa"] = (u["positivos"] / u["casos"]).fillna(0.0)
    u["estrato"] = u.groupby(["SEXO", "ANIO_NAC"], sort=True).ngroup()

    # 3. Dentro de cada estrato, una de cada N unidades va a prueba, en el orden de su tasa de reingreso.
    rng = np.random.default_rng(par["semilla"])
    u["azar"] = rng.random(len(u))                                   # desempate entre unidades con la misma tasa
    partida = rng.integers(0, par["prueba_una_de_cada"], u["estrato"].max() + 1)
    u = u.sort_values(["estrato", "tasa", "azar"])
    lugar = u.groupby("estrato").cumcount().to_numpy()
    u["PRUEBA"] = (lugar + partida[u["estrato"].to_numpy()]) % par["prueba_una_de_cada"] == 0
    p["CONJUNTO"] = np.where(u["PRUEBA"].reindex(p["UNIDAD"]).to_numpy(), "PRUEBA", "DESARROLLO")

    salida = p[["ID_EGRESO", "ID_PACIENTE", "ID_PERSONA", "UNIDAD", "CONJUNTO"]].rename(columns={"UNIDAD": "GRUPO_PARTICION"})
    salida["GRUPO_PARTICION"] = salida["GRUPO_PARTICION"].astype("int32")

    # ---------------------------------------------------------------- cifras del reporte
    casos = p[p["ES_CASO_ESTUDIO"]]
    edad = (casos["FECHA_INGRESO"] - casos["FECHA_NACIMIENTO"]).dt.days // 365.25
    grupo_edad = pd.Series("(sin dato)", index=casos.index)
    for desde, hasta, nombre in EDADES:
        grupo_edad[(edad >= desde) & (edad <= hasta)] = nombre
    describe = {"Año del alta": casos["ANIO_ARCHIVO"].astype(str), "Bloque de identificador": casos["BLOQUE_ID"],
                "Sexo": casos["SEXO"].fillna("(sin dato)"), "Edad al ingreso": grupo_edad,
                "Tipo de actividad": casos["TIPO_ACTIVIDAD"].fillna("(sin dato)"),
                "Tipo de ingreso": casos["TIPO_INGRESO"].fillna("(sin dato)"), "CDM": casos["CDM"].fillna("(sin dato)")}
    orden_edad = [nombre for _, _, nombre in EDADES] + ["(sin dato)"]
    info = {
        "objetivos": objetivos, "estratifica": estratifica,
        "egresos_tabla": len(d), "egresos": len(p), "sin_persona": len(d) - len(p),
        "unidades": conteo(u["PRUEBA"].map({True: "PRUEBA", False: "DESARROLLO"})),
        "estratos": int(u["estrato"].nunique()),
        "unidades_con_casos": int((u["casos"] > 0).sum()),
        "casos_por_unidad": (float(u["casos"].median()), int(u["casos"].max())),
        "identificadores": {c: int(p.loc[p["CONJUNTO"] == c, "ID_PACIENTE"].nunique()) for c in CONJUNTOS},
        "personas": {c: int(p.loc[p["CONJUNTO"] == c, "ID_PERSONA"].nunique()) for c in CONJUNTOS},
        "egresos_conjunto": conteo(p["CONJUNTO"]),
        "casos": conteo(casos["CONJUNTO"]),
        "positivos": {o: {c: int(casos.loc[casos["CONJUNTO"] == c, o].sum()) for c in CONJUNTOS} for o in objetivos},
        "positivos_anio": {c: conteo(casos.loc[(casos["CONJUNTO"] == c) & (casos[estratifica] == 1), "ANIO_ARCHIVO"]) for c in CONJUNTOS},
        "casos_anio": {c: conteo(casos.loc[casos["CONJUNTO"] == c, "ANIO_ARCHIVO"]) for c in CONJUNTOS},
        "composicion": {}, "sin_fecha": int((~con_fecha).sum()),
    }
    for nombre, valores in describe.items():
        tabla = pd.crosstab(valores, casos["CONJUNTO"]).reindex(columns=CONJUNTOS, fill_value=0)
        if nombre == "Edad al ingreso":
            tabla = tabla.reindex([e for e in orden_edad if e in tabla.index])
        info["composicion"][nombre] = tabla

    n_por = {col: p.groupby(col)["CONJUNTO"].nunique().max() for col in ("ID_PACIENTE", "ID_PERSONA", "UNIDAD")}
    total_casos = sum(info["casos"].values())
    parte = info["casos"]["PRUEBA"] / total_casos
    esperado = 1 / par["prueba_una_de_cada"]
    dif = max(abs(info["positivos"][o]["PRUEBA"] / info["casos"]["PRUEBA"] - info["positivos"][o]["DESARROLLO"] / info["casos"]["DESARROLLO"])
              for o in objetivos)
    info["diferencia_maxima"] = dif
    info["verificaciones"] = [
        ("Todos los egresos de un identificador de paciente están en un solo conjunto", n_por["ID_PACIENTE"] == 1),
        ("Todos los egresos de una persona están en un solo conjunto", n_por["ID_PERSONA"] == 1),
        ("Cada unidad de reparto está en un solo conjunto", n_por["UNIDAD"] == 1),
        ("Todos los casos de estudio quedaron asignados a un conjunto", int(d["ES_CASO_ESTUDIO"].sum()) == total_casos),
        (f"El conjunto de prueba tiene cerca del {100 * esperado:.0f} % de los casos de estudio (entre {100 * esperado - 1:.0f} % y {100 * esperado + 1:.0f} %)",
         abs(parte - esperado) < 0.01),
        ("La tasa de cada variable objetivo difiere en menos de 0,1 puntos porcentuales entre los dos conjuntos", dif < 0.001),
    ]
    if par["agrupar_por_nacimiento"]:
        canon = por_id.loc[con_fecha].assign(P=u["PRUEBA"].reindex(por_id.loc[con_fecha, "UNIDAD"]).to_numpy())
        info["verificaciones"].insert(3, (
            "Los identificadores con la misma fecha de nacimiento y el mismo sexo están en un solo conjunto",
            int(canon.groupby(["SEXO", "FNAC"])["P"].nunique().max()) == 1))
    return salida, info


# ------------------------------------------------------------------ escritura
def escribir(salida: pd.DataFrame) -> list[tuple[str, bool]]:
    """Escribe la llave de la partición y los dos conjuntos, copiando la tabla etiquetada por grupos de filas."""
    DIR_RESERVA.mkdir(parents=True, exist_ok=True)
    esquema_llave = pa.schema([("ID_EGRESO", pa.int64()), ("ID_PACIENTE", pa.int64()), ("ID_PERSONA", pa.int64()),
                               ("GRUPO_PARTICION", pa.int32()), ("CONJUNTO", pa.string())])
    pq.write_table(pa.Table.from_pandas(salida, schema=esquema_llave, preserve_index=False), PARTICION, compression="zstd")

    origen = pq.ParquetFile(ORIGEN)
    esquema = pa.schema([*origen.schema_arrow, pa.field("GRUPO_PARTICION", pa.int32())])
    grupo = salida.set_index("ID_EGRESO")["GRUPO_PARTICION"]
    conjunto = salida.set_index("ID_EGRESO")["CONJUNTO"]
    destinos = {"DESARROLLO": DESARROLLO, "PRUEBA": PRUEBA}
    temporales = {c: ruta.with_suffix(".parquet.tmp") for c, ruta in destinos.items()}
    escritores, escritas = {}, dict.fromkeys(destinos, 0)
    try:
        for g in range(origen.num_row_groups):
            bloque = origen.read_row_group(g).to_pandas()
            bloque["GRUPO_PARTICION"] = grupo.reindex(bloque["ID_EGRESO"]).astype("Int32").array
            destino = conjunto.reindex(bloque["ID_EGRESO"]).to_numpy()
            for c in destinos:
                parte = pa.Table.from_pandas(bloque[destino == c], schema=esquema, preserve_index=False)
                if c not in escritores:
                    escritores[c] = pq.ParquetWriter(temporales[c], parte.schema, compression="zstd")
                escritores[c].write_table(parte)
                escritas[c] += parte.num_rows
            print(f"  grupo {g + 1} de {origen.num_row_groups}", flush=True)
            del bloque
    finally:
        for escritor in escritores.values():
            escritor.close()
    for c, ruta in destinos.items():
        temporales[c].replace(ruta)

    filas = {c: pq.ParquetFile(ruta).metadata.num_rows for c, ruta in destinos.items()}
    ids = {c: pq.read_table(ruta, columns=["ID_EGRESO"]).column(0).to_numpy() for c, ruta in destinos.items()}
    esperados = {c: np.sort(salida.loc[salida["CONJUNTO"] == c, "ID_EGRESO"].to_numpy()) for c in destinos}
    columnas = [f.name for f in origen.schema_arrow] + ["GRUPO_PARTICION"]
    return [
        ("Los dos archivos contienen exactamente los egresos asignados a cada conjunto",
         all((np.sort(ids[c]) == esperados[c]).all() if len(ids[c]) == len(esperados[c]) else False for c in destinos)),
        ("Ningún egreso está en los dos archivos", len(np.intersect1d(ids["DESARROLLO"], ids["PRUEBA"])) == 0),
        ("Los dos archivos tienen las columnas de la tabla etiquetada más `GRUPO_PARTICION`",
         all(pq.read_schema(ruta).names == columnas for ruta in destinos.values())),
        ("La suma de filas de los dos archivos es el número de egresos con persona", sum(filas.values()) == len(salida) == sum(escritas.values())),
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
    ruta = ACTIVIDAD.name
    casos, pos = info["casos"], info["positivos"]
    total = sum(casos.values())
    n = par["prueba_una_de_cada"]

    def fila_total(nombre: str, valores: dict) -> list:
        suma = sum(valores.values())
        return [nombre, fmt(valores["DESARROLLO"]), fmt(valores["PRUEBA"]), fmt(suma), pct(valores["PRUEBA"], suma, 1)]

    def definicion(col: str) -> str:
        return f"{col.split('_')[1][:-1]} días, " + ("relacionado (misma CDM)" if col.endswith("_CDM") else "por cualquier causa")

    partes = [
        "# Partición inicial y reserva del conjunto de prueba (actividad 2.3, script 10)",
        f"Generado por `{ruta}/scripts/10_particionar.py`. Entrada: `data/processed/{ORIGEN.name}`. Salidas: "
        f"`data/processed/{PARTICION.name}`, `data/processed/{DESARROLLO.name}` y `data/reserva/{PRUEBA.name}`. Parámetros: "
        f"`{ruta}/reglas/{ARCHIVO_PARAMETROS.name}`. Las decisiones están en `{ruta}/bitacora.md`.",
        "El conjunto de prueba se aparta aquí y no se vuelve a abrir hasta la evaluación final: todo lo que sigue "
        "(ingeniería de variables, filtro, entrenamiento y ajuste) se hace solo con `desarrollo.parquet`.",

        "## 1. Cómo se reparte",
        ("**Unidad de reparto:** todos los identificadores de paciente con la misma fecha de nacimiento y el mismo sexo van juntos "
         "al mismo conjunto. Con eso, todos los egresos de un identificador quedan en un solo conjunto, y también los de una "
         "persona que tiene un identificador en el bloque A (2019–2020) y otro en el bloque B (2021–2024), que no se pueden "
         "vincular de otra forma. A cada identificador se le asigna su fecha de nacimiento y su sexo más frecuentes."
         if par["agrupar_por_nacimiento"] else
         "**Unidad de reparto:** el identificador de paciente. Todos los egresos de un identificador quedan en un solo conjunto. "
         "Una persona con un identificador en cada bloque puede quedar repartida entre los dos conjuntos."),
        f"**Estratificación:** las unidades se separan en {fmt(info['estratos'])} estratos por año de nacimiento y sexo. Dentro de "
        f"cada estrato se ordenan por su tasa de `{info['estratifica']}` y se toma una de cada {n} para prueba, con un punto de "
        f"partida al azar fijado por la semilla del proyecto ({par['semilla']}). Así los dos conjuntos quedan equilibrados en edad, "
        "sexo y tasa de reingreso, y la partición es la misma cada vez que se ejecuta el script.",

        "## 2. Tamaño de los conjuntos",
        tabla_md(["", "Desarrollo", "Prueba", "Total", "% en prueba"], [
            fila_total("Unidades de reparto", info["unidades"]),
            fila_total("Identificadores de paciente", info["identificadores"]),
            fila_total("Personas", info["personas"]),
            fila_total("Egresos", info["egresos_conjunto"]),
            fila_total("**Casos de estudio**", casos),
        ]),
        f"Los egresos que no son caso de estudio acompañan a su persona, porque sirven para calcular su historia de "
        f"hospitalizaciones. Quedan fuera de los dos conjuntos los {fmt(info['sin_persona'])} egresos sin persona asignada "
        f"(sin identificador o con identificador genérico), que no son casos de estudio. De las {fmt(sum(info['unidades'].values()))} "
        f"unidades, {fmt(info['unidades_con_casos'])} tienen casos de estudio (mediana de {fmt(info['casos_por_unidad'][0])} casos; "
        f"máximo, {fmt(info['casos_por_unidad'][1])})."
        + (f" {fmt(info['sin_fecha'])} identificadores sin fecha de nacimiento forman cada uno su propia unidad." if info["sin_fecha"] else ""),

        "## 3. Tasas de reingreso en cada conjunto",
        "Porcentaje de los casos de estudio de cada conjunto. La diferencia está en puntos porcentuales.",
        tabla_md(["Variable", "Definición", "Desarrollo", "Prueba", "Diferencia"],
                 [[f"`{o}`", definicion(o), pct(pos[o]["DESARROLLO"], casos["DESARROLLO"], 3), pct(pos[o]["PRUEBA"], casos["PRUEBA"], 3),
                   f"{100 * (pos[o]['PRUEBA'] / casos['PRUEBA'] - pos[o]['DESARROLLO'] / casos['DESARROLLO']):+.3f}".replace(".", ",")]
                  for o in info["objetivos"]]),
        f"`{info['estratifica']}` por año del alta (% de los casos de estudio del año en cada conjunto):",
        tabla_md(["Conjunto", *[str(a) for a in ANIOS]],
                 [[c.capitalize(), *[pct(info["positivos_anio"][c].get(a, 0), info["casos_anio"][c].get(a, 0)) for a in ANIOS]] for c in CONJUNTOS]),

        "## 4. Composición de los casos de estudio",
        "Porcentaje dentro de cada conjunto. Las dos columnas deben ser casi iguales.",
    ]
    for nombre, tabla in info["composicion"].items():
        partes.append(tabla_md([nombre, "Desarrollo", "Prueba", "Diferencia"],
                               [[g, pct(f["DESARROLLO"], casos["DESARROLLO"]), pct(f["PRUEBA"], casos["PRUEBA"]),
                                 f"{100 * (f['PRUEBA'] / casos['PRUEBA'] - f['DESARROLLO'] / casos['DESARROLLO']):+.2f}".replace(".", ",")]
                                for g, f in tabla.iterrows()]))
    partes += [
        "## 5. Parámetros",
        tabla_md(["Parámetro", "Valor", "Descripción"], [[f"`{k}`", f"`{v}`", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 6. Archivos",
        tabla_md(["Archivo", "Contenido"], [
            [f"`data/processed/{PARTICION.name}`", "Una fila por egreso con persona: `ID_EGRESO`, `ID_PACIENTE`, `ID_PERSONA`, "
                                                    "`GRUPO_PARTICION` (unidad de reparto) y `CONJUNTO` (`DESARROLLO` o `PRUEBA`)."],
            [f"`data/processed/{DESARROLLO.name}`", "Egresos del conjunto de desarrollo, con todas las columnas de la tabla etiquetada "
                                                     "más `GRUPO_PARTICION`. Es el único archivo que usan las etapas siguientes."],
            [f"`data/reserva/{PRUEBA.name}`", "Egresos del conjunto de prueba, con las mismas columnas. No se abre hasta la evaluación final."],
        ]),
        "`GRUPO_PARTICION` es también el grupo que debe usar la validación cruzada agrupada dentro del conjunto de desarrollo.",

        "## 7. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),
    ]
    salida = DIR_REPORTS / "10_particion.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par = cargar_parametros()
    print("Particionando...", flush=True)
    salida, info = particionar(par)
    print(f"  casos de estudio: {info['casos']['DESARROLLO']:,} en desarrollo y {info['casos']['PRUEBA']:,} en prueba "
          f"({time.time() - inicio:.0f} s)", flush=True)
    print("Escribiendo...", flush=True)
    info["verificaciones"] += escribir(salida)
    escribir_reporte(info, par)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
