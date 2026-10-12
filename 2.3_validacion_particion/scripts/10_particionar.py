"""Partición inicial y reserva del conjunto de prueba (actividad 2.3, script 10).

Parte del conjunto analítico (data/processed/grd_etiquetado.parquet) y reparte a los pacientes
entre un conjunto de desarrollo (80 %) y un conjunto de prueba (20 %), que queda apartado hasta
la evaluación final (bitácora D27 a D29):

  1. Versión. Comprueba que el archivo sea el de la última versión registrada en
     docs/version_conjunto_analitico.csv.
  2. Unidad de reparto. El identificador de paciente: todos sus egresos van al mismo conjunto.
     Los identificadores de los bloques A (2019-2020) y B (2021-2024) no se enlazan.
  3. Estratos. Los identificadores se separan por bloque y por el patrón de sus variables
     objetivo: qué reingresos tuvo alguno de sus casos de estudio.
  4. Reparto. Dentro de cada estrato se ordenan por su número de reingresos de la variable
     principal y por su número de casos de estudio, y uno de cada cinco va a prueba, con un punto
     de partida al azar fijado por la semilla del proyecto.
  5. Salidas. data/processed/particion.parquet indica el conjunto de cada egreso y
     data/processed/particion_identificadores.parquet, el de cada identificador.
     data/processed/desarrollo.parquet y data/reserva/prueba.parquet contienen los egresos de cada
     conjunto con todas las columnas. El de prueba queda como archivo de solo lectura.
  6. Registro. docs/version_particion.csv guarda el hash SHA-256 de los archivos, para poder
     comprobar más adelante que el conjunto de prueba no cambió.

Los parámetros están en reglas/parametros.csv. El reporte reportes/10_particion.md compara los dos
conjuntos por tasa de reingreso, año, hospital, sexo, edad y CDM.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.3_validacion_particion\\scripts\\10_particionar.py
"""

import csv
import hashlib
import os
import stat
import time
from datetime import date
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
IDENTIFICADORES = DIR_PROCESSED / "particion_identificadores.parquet"
DESARROLLO = DIR_PROCESSED / "desarrollo.parquet"
PRUEBA = DIR_RESERVA / "prueba.parquet"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
VERSION_CONJUNTO = RAIZ / "docs" / "version_conjunto_analitico.csv"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
# Nombres de los hospitales: hoja Hospitales de la tabla maestra del DEIS (solo se usan en el reporte).
TABLA_MAESTRA = RAIZ.parent / "Datos" / "Tablas auxiliares" / "Tablas maestras bases GRD.xlsx"
ANIOS = list(range(2019, 2025))

CONJUNTOS = ["DESARROLLO", "PRUEBA"]
SIN_CASOS = "sin casos"                          # estrato de los identificadores sin ningún caso de estudio
COLUMNAS = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "ID_PACIENTE", "ID_PERSONA", "SEXO", "FECHA_NACIMIENTO", "FECHA_INGRESO",
            "COD_HOSPITAL", "TIPO_INGRESO", "CDM", "ES_CASO_ESTUDIO"]
EDADES = [(-1, 0, "Menos de 1 año"), (1, 14, "1 a 14 años"), (15, 44, "15 a 44 años"), (45, 64, "45 a 64 años"),
          (65, 79, "65 a 79 años"), (80, 200, "80 años o más")]
CAMPOS = ["version", "fecha", "version_conjunto", "sha256_conjunto", "semilla", "prueba_una_de_cada", "variable_principal",
          "identificadores_desarrollo", "identificadores_prueba", "casos_desarrollo", "casos_prueba",
          "sha256_identificadores", "sha256_desarrollo", "sha256_prueba"]
# Límites de las verificaciones, en puntos porcentuales.
MARGEN_TAMANO, MARGEN_TASA, MARGEN_COMPOSICION = 0.5, 0.05, 0.5


# ------------------------------------------------------------------ parámetros y versión
def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cargar_parametros() -> dict:
    filas = {fila["parametro"]: fila for fila in leer_csv(ARCHIVO_PARAMETROS)}
    par = {"semilla": int(filas["semilla"]["valor"]), "prueba_una_de_cada": int(filas["prueba_una_de_cada"]["valor"]),
           "variable_principal": filas["variable_principal"]["valor"].strip()}
    if par["prueba_una_de_cada"] < 2:
        raise SystemExit("prueba_una_de_cada debe ser 2 o más.")
    par["descripcion"] = {nombre: (fila["valor"].strip(), fila["descripcion"]) for nombre, fila in filas.items()}
    return par


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def comprobar_version() -> dict:
    """La partición solo se hace sobre la versión registrada del conjunto analítico (bitácora D36)."""
    if not VERSION_CONJUNTO.exists():
        raise SystemExit(f"No existe {VERSION_CONJUNTO.name}: registre la versión del conjunto con el script 12.")
    version = leer_csv(VERSION_CONJUNTO)[-1]
    if sha256(ORIGEN) != version["sha256"]:
        raise SystemExit(f"{ORIGEN.name} no es la versión {version['version']} registrada: ejecute el script 12 y vuelva a intentar.")
    return version


# ------------------------------------------------------------------ partición
def ventana_de(variable: str) -> int:
    return int(variable.split("_")[1][:-1])


def resumir_identificadores(p: pd.DataFrame, objetivos: list[str], principal: str) -> pd.DataFrame:
    """Una fila por identificador de paciente: bloque, egresos, casos de estudio, reingresos de la variable
    principal y patrón de las variables objetivo. El índice queda ordenado por identificador."""
    casos = p[p["ES_CASO_ESTUDIO"]]
    u = p.groupby("ID_PACIENTE").agg(BLOQUE_ID=("BLOQUE_ID", "first"), EGRESOS=("ID_EGRESO", "size"), PERSONAS=("ID_PERSONA", "nunique"))
    u["CASOS"] = casos.groupby("ID_PACIENTE").size().reindex(u.index, fill_value=0)
    # Casos de estudio con reingreso, en cada variable. Un caso sin dato en una variable no suma.
    reingresos = {k: casos.groupby("ID_PACIENTE")[k].sum().reindex(u.index).fillna(0).astype("int64") for k in objetivos}
    u["REINGRESOS"] = reingresos[principal]
    # Patrón: un dígito por variable (1 = algún caso de estudio con reingreso), de la ventana más larga a la más corta.
    # Un reingreso dentro de una ventana corta también lo es dentro de una más larga, aunque esa variable no tenga dato.
    ventanas = sorted({ventana_de(k) for k in objetivos})
    for sufijo in ("", "_CDM"):
        alguno = np.zeros(len(u), dtype=bool)
        for v in ventanas:                                   # de la ventana más corta a la más larga
            alguno = alguno | (reingresos[f"REING_{v}D{sufijo}"] > 0).to_numpy()
            u[f"REING_{v}D{sufijo}"] = alguno.astype("int8").astype(str)
    patron = pd.Series("", index=u.index)
    for v in reversed(ventanas):
        for sufijo in ("", "_CDM"):
            patron = patron + u[f"REING_{v}D{sufijo}"]
    u["PATRON"] = np.where(u["CASOS"] == 0, SIN_CASOS, patron)
    return u.sort_index()


def repartir(u: pd.DataFrame, par: dict) -> pd.Series:
    """Marca los identificadores que van al conjunto de prueba: uno de cada N dentro de cada estrato.

    El resultado depende solo de los datos y de la semilla: con la misma tabla y la misma semilla, siempre es el mismo.
    """
    n = par["prueba_una_de_cada"]
    rng = np.random.default_rng(par["semilla"])
    u = u.sort_index().copy()                                # orden fijo: por identificador
    u["AZAR"] = rng.random(len(u))                           # desempata a los identificadores iguales
    u["ESTRATO"] = u.groupby(["BLOQUE_ID", "PATRON"], sort=True).ngroup()
    partida = rng.integers(0, n, u["ESTRATO"].max() + 1)     # punto de partida de cada estrato: de 0 a N - 1
    u = u.sort_values(["ESTRATO", "REINGRESOS", "CASOS", "AZAR"])
    lugar = u.groupby("ESTRATO").cumcount().to_numpy()       # 0, 1, 2, ... dentro de cada estrato
    u["PRUEBA"] = (lugar + partida[u["ESTRATO"].to_numpy()]) % n == 0
    return u["PRUEBA"].sort_index()


def conteo(valores: pd.Series) -> dict:
    return {k: int(v) for k, v in valores.value_counts(dropna=False).items()}


def particionar(par: dict) -> tuple[np.ndarray, pd.DataFrame, dict]:
    """Devuelve el conjunto de cada egreso (en el orden del conjunto analítico; vacío si no tiene persona),
    el conjunto de cada identificador y las cifras del reporte."""
    objetivos = [c for c in pq.read_schema(ORIGEN).names if c.startswith("REING_")]
    principal = par["variable_principal"]
    if principal not in objetivos:
        raise SystemExit(f"variable_principal: '{principal}' no es una de las variables objetivo {objetivos}.")
    d = pq.read_table(ORIGEN, columns=COLUMNAS + objetivos).to_pandas()
    con_persona = d["ID_PERSONA"].notna().to_numpy()
    p = d[con_persona].copy()
    p["ID_PACIENTE"] = p["ID_PACIENTE"].astype("int64")

    u = resumir_identificadores(p, objetivos, principal)
    u["PRUEBA"] = repartir(u, par)
    u["CONJUNTO"] = np.where(u["PRUEBA"], "PRUEBA", "DESARROLLO")
    p["CONJUNTO"] = u["CONJUNTO"].reindex(p["ID_PACIENTE"]).to_numpy()
    conjunto = np.full(len(d), None, dtype=object)
    conjunto[con_persona] = p["CONJUNTO"].to_numpy()
    # La lista de identificadores no lleva nada que dependa de las variables objetivo: el conjunto de prueba queda sellado.
    lista = u[["BLOQUE_ID", "CONJUNTO"]].reset_index()

    # ---------------------------------------------------------------- cifras del reporte
    casos = p[p["ES_CASO_ESTUDIO"]]
    edad = (casos["FECHA_INGRESO"] - casos["FECHA_NACIMIENTO"]).dt.days // 365.25
    grupo_edad = pd.Series("(sin dato)", index=casos.index)
    for desde, hasta, nombre in EDADES:
        grupo_edad[(edad >= desde) & (edad <= hasta)] = nombre
    describe = {"Año del alta": casos["ANIO_ARCHIVO"].astype(str), "Bloque de identificador": casos["BLOQUE_ID"],
                "Sexo": casos["SEXO"].fillna("(sin dato)"), "Edad al ingreso": grupo_edad,
                "Tipo de ingreso": casos["TIPO_INGRESO"].fillna("(sin dato)"), "CDM": casos["CDM"].fillna("(sin dato)"),
                "Hospital": casos["COD_HOSPITAL"]}
    orden_edad = [nombre for _, _, nombre in EDADES] + ["(sin dato)"]
    en = {c: (casos["CONJUNTO"] == c).to_numpy() for c in CONJUNTOS}

    def por_anio(c: str) -> dict:
        """Por año del alta: (casos con dato en la variable principal, casos con reingreso) del conjunto c."""
        salida = {}
        for a in ANIOS:
            m = en[c] & (casos["ANIO_ARCHIVO"] == a).to_numpy() & casos[principal].notna().to_numpy()
            salida[a] = (int(m.sum()), int((casos.loc[m, principal] == 1).sum()))
        return salida

    info = {
        "objetivos": objetivos, "principal": principal,
        "egresos_tabla": len(d), "sin_persona": int((~con_persona).sum()),
        "identificadores": conteo(u["CONJUNTO"]), "con_varias_personas": int((u["PERSONAS"] > 1).sum()),
        "identificadores_bloque": {b: conteo(u.loc[u["BLOQUE_ID"] == b, "CONJUNTO"]) for b in sorted(u["BLOQUE_ID"].unique())},
        "personas": {c: int(p.loc[p["CONJUNTO"] == c, "ID_PERSONA"].nunique()) for c in CONJUNTOS},
        "egresos": conteo(p["CONJUNTO"]),
        "casos": conteo(casos["CONJUNTO"]),
        "casos_bloque": {b: conteo(casos.loc[casos["BLOQUE_ID"] == b, "CONJUNTO"]) for b in sorted(u["BLOQUE_ID"].unique())},
        # Por variable y conjunto: (casos con dato, casos con reingreso).
        "tasas": {k: {c: (int(casos.loc[en[c], k].notna().sum()), int((casos.loc[en[c], k] == 1).sum())) for c in CONJUNTOS} for k in objetivos},
        "tasas_anio": {c: por_anio(c) for c in CONJUNTOS},
        "estratos": (u.groupby(["BLOQUE_ID", "PATRON"], sort=True)
                     .agg(identificadores=("PRUEBA", "size"), prueba=("PRUEBA", "sum"), casos=("CASOS", "sum")).reset_index()),
        "composicion": {},
    }
    for nombre, valores in describe.items():
        tabla = pd.crosstab(valores, casos["CONJUNTO"]).reindex(columns=CONJUNTOS, fill_value=0)
        if nombre == "Edad al ingreso":
            tabla = tabla.reindex([e for e in orden_edad if e in tabla.index])
        info["composicion"][nombre] = tabla

    # ---------------------------------------------------------------- verificaciones
    total_casos = sum(info["casos"].values())
    parte = 100 * info["casos"]["PRUEBA"] / total_casos
    esperado = 100 / par["prueba_una_de_cada"]
    info["diferencia_tasas"] = max(abs(100 * t["PRUEBA"][1] / t["PRUEBA"][0] - 100 * t["DESARROLLO"][1] / t["DESARROLLO"][0])
                                   for t in info["tasas"].values())
    info["diferencia_composicion"] = {nombre: float((100 * tabla["PRUEBA"] / tabla["PRUEBA"].sum()
                                                     - 100 * tabla["DESARROLLO"] / tabla["DESARROLLO"].sum()).abs().max())
                                      for nombre, tabla in info["composicion"].items()}
    e = info["estratos"]
    info["verificaciones"] = [
        ("Todos los egresos de un identificador de paciente están en un solo conjunto", int(p.groupby("ID_PACIENTE")["CONJUNTO"].nunique().max()) == 1),
        ("Todos los egresos de una persona están en un solo conjunto", int(p.groupby("ID_PERSONA")["CONJUNTO"].nunique().max()) == 1),
        ("Ningún identificador de paciente aparece en los dos bloques", int(p.groupby("ID_PACIENTE")["BLOQUE_ID"].nunique().max()) == 1),
        ("Todos los casos de estudio quedaron asignados a un conjunto", int(d["ES_CASO_ESTUDIO"].sum()) == total_casos),
        (f"En cada estrato va a prueba uno de cada {par['prueba_una_de_cada']} identificadores (la diferencia con esa proporción es menor que un identificador)",
         bool(((e["prueba"] - e["identificadores"] / par["prueba_una_de_cada"]).abs() < 1).all())),
        (f"El conjunto de prueba tiene entre {esperado - MARGEN_TAMANO:.1f} % y {esperado + MARGEN_TAMANO:.1f} % de los casos de estudio".replace(".", ","),
         abs(parte - esperado) < MARGEN_TAMANO),
        (f"La tasa de cada variable objetivo difiere en menos de {MARGEN_TASA} puntos porcentuales entre los dos conjuntos".replace(".", ","),
         info["diferencia_tasas"] < MARGEN_TASA),
        (f"Ninguna categoría de año, bloque, sexo, edad, tipo de ingreso, CDM u hospital difiere en más de {MARGEN_COMPOSICION} puntos porcentuales".replace(".", ","),
         max(info["diferencia_composicion"].values()) < MARGEN_COMPOSICION),
    ]
    return conjunto, lista, info


# ------------------------------------------------------------------ escritura
def reemplazar(temporal: Path, destino: Path) -> None:
    """Pone el archivo temporal en el lugar del destino, aunque el destino sea de solo lectura."""
    if destino.exists():
        os.chmod(destino, stat.S_IWRITE)
    temporal.replace(destino)


def escribir(conjunto: np.ndarray, lista: pd.DataFrame) -> list[tuple[str, bool]]:
    """Escribe el conjunto de cada egreso, la lista de identificadores y los dos conjuntos, copiando el conjunto
    analítico por grupos de filas sin cambiar ninguna columna."""
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    DIR_RESERVA.mkdir(parents=True, exist_ok=True)
    origen = pq.ParquetFile(ORIGEN)
    destinos = {"DESARROLLO": DESARROLLO, "PRUEBA": PRUEBA}
    temporales = {c: ruta.with_suffix(".parquet.tmp") for c, ruta in destinos.items()}
    escritores = {c: pq.ParquetWriter(temporales[c], origen.schema_arrow, compression="zstd") for c in destinos}
    llaves, leidas = [], 0
    try:
        for g in range(origen.num_row_groups):
            tabla = origen.read_row_group(g)
            de_fila = conjunto[leidas:leidas + tabla.num_rows]           # conjunto de cada fila de este grupo
            leidas += tabla.num_rows
            for c in destinos:
                escritores[c].write_table(tabla.filter(pa.array(de_fila == c)))
            con_conjunto = pa.array(de_fila != None)                     # noqa: E711 (comparación elemento a elemento)
            llaves.append(tabla.select(["ID_EGRESO", "ID_PACIENTE", "BLOQUE_ID"]).filter(con_conjunto)
                          .append_column("CONJUNTO", pa.array(de_fila[de_fila != None], type=pa.string())))      # noqa: E711
            print(f"  grupo {g + 1} de {origen.num_row_groups}", flush=True)
            del tabla
    finally:
        for escritor in escritores.values():
            escritor.close()
    for c, ruta in destinos.items():
        reemplazar(temporales[c], ruta)
    os.chmod(PRUEBA, stat.S_IREAD)                                       # el conjunto de prueba queda como solo lectura
    pq.write_table(pa.concat_tables(llaves), PARTICION, compression="zstd")
    pq.write_table(pa.Table.from_pandas(lista, preserve_index=False), IDENTIFICADORES, compression="zstd")

    # Relectura: cada archivo contiene exactamente los egresos de su conjunto, con las columnas del conjunto analítico.
    todos = pq.read_table(ORIGEN, columns=["ID_EGRESO"]).column(0).to_numpy()
    ids = {c: pq.read_table(ruta, columns=["ID_EGRESO"]).column(0).to_numpy() for c, ruta in destinos.items()}
    pacientes = {c: set(pq.read_table(ruta, columns=["ID_PACIENTE"]).column(0).to_pylist()) for c, ruta in destinos.items()}
    muestra = ["ID_EGRESO", "ID_PERSONA", "FECHAALTA", "DIAGNOSTICO1", "ES_CASO_ESTUDIO", "REING_30D"]
    return [
        ("Cada archivo contiene exactamente los egresos asignados a su conjunto, en el orden del conjunto analítico",
         all(np.array_equal(ids[c], todos[conjunto == c]) for c in destinos)),
        ("Ningún identificador de paciente está en los dos archivos", not (pacientes["DESARROLLO"] & pacientes["PRUEBA"])),
        ("Los dos archivos tienen las mismas columnas que el conjunto analítico, con el mismo tipo de dato",
         all(pq.read_schema(ruta).equals(origen.schema_arrow) for ruta in destinos.values())),
        (f"Contenido idéntico al del conjunto analítico en {len(muestra)} columnas de control",
         all(pq.read_table(ORIGEN, columns=muestra).filter(pa.array(conjunto == c)).equals(pq.read_table(ruta, columns=muestra)) for c, ruta in destinos.items())),
        ("La suma de filas de los dos archivos es el número de egresos con persona",
         len(ids["DESARROLLO"]) + len(ids["PRUEBA"]) == int((conjunto != None).sum())),      # noqa: E711
        ("El archivo del conjunto de prueba quedó como solo lectura", not os.access(PRUEBA, os.W_OK)),
    ]


def registrar(par: dict, version: dict, info: dict) -> tuple[dict, bool]:
    """Registra el hash de los archivos de la partición. Solo agrega una fila si alguno cambió."""
    ficha = {"version_conjunto": version["version"], "sha256_conjunto": version["sha256"], "semilla": str(par["semilla"]),
             "prueba_una_de_cada": str(par["prueba_una_de_cada"]), "variable_principal": par["variable_principal"],
             "identificadores_desarrollo": str(info["identificadores"]["DESARROLLO"]), "identificadores_prueba": str(info["identificadores"]["PRUEBA"]),
             "casos_desarrollo": str(info["casos"]["DESARROLLO"]), "casos_prueba": str(info["casos"]["PRUEBA"]),
             "sha256_identificadores": sha256(IDENTIFICADORES), "sha256_desarrollo": sha256(DESARROLLO), "sha256_prueba": sha256(PRUEBA)}
    filas = leer_csv(REGISTRO) if REGISTRO.exists() else []
    if filas and all(filas[-1][k] == v for k, v in ficha.items()):
        return filas[-1], False
    nueva = {"version": str(int(filas[-1]["version"]) + 1 if filas else 1), "fecha": date.today().isoformat(), **ficha}
    with open(REGISTRO, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";", lineterminator="\r\n")
        escritor.writeheader()
        escritor.writerows([*filas, nueva])
    return nueva, True


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def puntos(valor: float, decimales: int = 2) -> str:
    return f"{valor:+.{decimales}f}".replace(".", ",")


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


def escribir_reporte(info: dict, par: dict, version: dict, registro: dict) -> None:
    ruta = ACTIVIDAD.name
    casos, n, principal, objetivos = info["casos"], par["prueba_una_de_cada"], info["principal"], info["objetivos"]

    def fila_total(nombre: str, valores: dict) -> list:
        suma = sum(valores.values())
        return [nombre, fmt(valores["DESARROLLO"]), fmt(valores["PRUEBA"]), fmt(suma), pct(valores["PRUEBA"], suma, 2)]

    def definicion(col: str) -> str:
        return f"{ventana_de(col)} días, " + ("relacionado (misma CDM)" if col.endswith("_CDM") else "por cualquier causa")

    def tabla_composicion(nombre: str, tabla: pd.DataFrame, etiquetas: dict | None = None) -> str:
        """Porcentaje de los casos de estudio de cada conjunto en cada categoría, y su diferencia en puntos porcentuales."""
        filas = []
        for g, f in tabla.iterrows():
            des, pru = 100 * f["DESARROLLO"] / casos["DESARROLLO"], 100 * f["PRUEBA"] / casos["PRUEBA"]
            filas.append([f"{g} {etiquetas.get(g, '(sin nombre en la tabla maestra)')}" if etiquetas is not None else g,
                          pct(f["DESARROLLO"], casos["DESARROLLO"]), pct(f["PRUEBA"], casos["PRUEBA"]), puntos(pru - des)])
        return tabla_md([nombre, "Desarrollo", "Prueba", "Diferencia"], filas)

    # Estratos: un dígito por variable objetivo, en el orden del patrón (de la ventana más larga a la más corta).
    en_patron = [f"REING_{v}D{s}" for v in sorted({ventana_de(k) for k in objetivos}, reverse=True) for s in ("", "_CDM")]
    filas_estratos = []
    for _, e in info["estratos"].iterrows():
        marcas = ["—"] * len(en_patron) if e["PATRON"] == SIN_CASOS else ["Sí" if x == "1" else "No" for x in e["PATRON"]]
        filas_estratos.append([e["BLOQUE_ID"], "No" if e["PATRON"] == SIN_CASOS else "Sí", *marcas, fmt(e["identificadores"]),
                               fmt(e["prueba"]), pct(e["prueba"], e["identificadores"])])

    partes = [
        "# Partición inicial y reserva del conjunto de prueba (actividad 2.3, script 10)",
        f"Generado por `{ruta}/scripts/10_particionar.py`. Entrada: `data/processed/{ORIGEN.name}`, versión {version['version']} del conjunto "
        f"analítico. Parámetros: `{ruta}/reglas/{ARCHIVO_PARAMETROS.name}`. Las decisiones están en `{ruta}/bitacora.md`.",
        "El conjunto de prueba se aparta aquí y no se vuelve a abrir hasta la evaluación final: todo lo que sigue (ingeniería de "
        f"variables, filtro, entrenamiento y ajuste) se hace solo con `{DESARROLLO.name}`. Las cifras del conjunto de prueba que "
        "aparecen en este reporte son las necesarias para comprobar que la partición quedó equilibrada.",

        "## 1. Cómo se reparte",
        "**Unidad de reparto:** el identificador de paciente. Todos los egresos de un identificador quedan en un solo conjunto, "
        f"también cuando el identificador reúne a más de una persona ({fmt(info['con_varias_personas'])} identificadores). Los "
        "identificadores del bloque A (2019–2020) y del bloque B (2021–2024) no se enlazan: una persona con un identificador en "
        "cada bloque puede quedar en los dos conjuntos.",
        "**Estratos:** los identificadores se separan por bloque y por el patrón de sus variables objetivo, es decir, por las "
        "variables en las que alguno de sus casos de estudio tiene reingreso. Los identificadores sin casos de estudio forman su "
        "propio estrato.",
        f"**Reparto:** dentro de cada estrato, los identificadores se ordenan por su número de casos de estudio con `{principal}` y por "
        f"su número de casos de estudio, y uno de cada {n} va al conjunto de prueba. El punto de partida de cada estrato se sortea "
        f"con la semilla del proyecto ({par['semilla']}), así que la partición es la misma cada vez que se ejecuta el script.",

        "## 2. Tamaño de los conjuntos",
        tabla_md(["", "Desarrollo", "Prueba", "Total", "% en prueba"], [
            fila_total("Identificadores de paciente", info["identificadores"]),
            *[fila_total(f"  del bloque {b}", v) for b, v in info["identificadores_bloque"].items()],
            fila_total("Personas", info["personas"]),
            fila_total("Egresos", info["egresos"]),
            fila_total("**Casos de estudio**", casos),
            *[fila_total(f"  del bloque {b}", v) for b, v in info["casos_bloque"].items()],
        ]),
        "Los egresos que no son caso de estudio acompañan a su identificador, porque sirven para calcular la historia de "
        f"hospitalizaciones de la persona. Quedan fuera de los dos conjuntos los {fmt(info['sin_persona'])} egresos sin persona "
        "asignada (sin identificador o con identificador genérico), que no son casos de estudio.",

        "## 3. Tasas de reingreso en cada conjunto",
        "Porcentaje de los casos de estudio con seguimiento suficiente para cada variable. La diferencia está en puntos porcentuales.",
        tabla_md(["Variable", "Definición", "Casos en desarrollo", "Tasa", "Casos en prueba", "Tasa", "Diferencia"],
                 [[f"`{k}`", definicion(k), fmt(t["DESARROLLO"][0]), pct(t["DESARROLLO"][1], t["DESARROLLO"][0], 3),
                   fmt(t["PRUEBA"][0]), pct(t["PRUEBA"][1], t["PRUEBA"][0], 3),
                   puntos(100 * t["PRUEBA"][1] / t["PRUEBA"][0] - 100 * t["DESARROLLO"][1] / t["DESARROLLO"][0], 3)]
                  for k, t in info["tasas"].items()]),
        f"`{principal}` por año del alta:",
        tabla_md(["Conjunto", *[str(a) for a in ANIOS]],
                 [[c.capitalize(), *[pct(info["tasas_anio"][c][a][1], info["tasas_anio"][c][a][0]) for a in ANIOS]] for c in CONJUNTOS]),

        "## 4. Composición de los casos de estudio",
        "Porcentaje de los casos de estudio de cada conjunto en cada categoría. Las dos columnas deben ser casi iguales. Mayor "
        "diferencia de cada tabla, en puntos porcentuales:",
        tabla_md(["Tabla", "Mayor diferencia entre los dos conjuntos"],
                 [[nombre, f"{valor:.2f}".replace(".", ",")] for nombre, valor in info["diferencia_composicion"].items()]),
    ]
    for nombre, tabla in info["composicion"].items():
        if nombre != "Hospital":
            partes.append(tabla_composicion(nombre, tabla))
    partes += [
        "La tabla por hospital está en el anexo.",

        "## 5. Estratos",
        "Identificadores de cada estrato y cuántos van al conjunto de prueba. Las columnas de las variables indican si alguno de "
        "los casos de estudio del identificador tiene reingreso en esa variable.",
        tabla_md(["Bloque", "Tiene casos de estudio", *[f"`{k}`" for k in en_patron], "Identificadores", "En prueba", "%"], filas_estratos),

        "## 6. Parámetros",
        tabla_md(["Parámetro", "Valor", "Descripción"], [[f"`{k}`", f"`{v}`", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 7. Archivos y versión",
        tabla_md(["Archivo", "Contenido"], [
            [f"`data/processed/{PARTICION.name}`", "Una fila por egreso con persona: `ID_EGRESO`, `ID_PACIENTE`, `BLOQUE_ID` y `CONJUNTO` "
                                                    "(`DESARROLLO` o `PRUEBA`)."],
            [f"`data/processed/{IDENTIFICADORES.name}`", "La lista de identificadores de cada conjunto: `ID_PACIENTE`, `BLOQUE_ID` y `CONJUNTO`."],
            [f"`data/processed/{DESARROLLO.name}`", "Egresos del conjunto de desarrollo, con todas las columnas del conjunto analítico. "
                                                     "Es el único archivo que usan las etapas siguientes."],
            [f"`data/reserva/{PRUEBA.name}`", "Egresos del conjunto de prueba, con las mismas columnas. Es de solo lectura y no se abre "
                                              "hasta la evaluación final."],
        ]),
        f"Versión {registro['version']} de la partición, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`, sobre la versión "
        f"{version['version']} del conjunto analítico.",
        tabla_md(["Archivo", "SHA-256"], [
            [f"`{ORIGEN.name}`", f"`{registro['sha256_conjunto']}`"],
            [f"`{IDENTIFICADORES.name}`", f"`{registro['sha256_identificadores']}`"],
            [f"`{DESARROLLO.name}`", f"`{registro['sha256_desarrollo']}`"],
            [f"`{PRUEBA.name}`", f"`{registro['sha256_prueba']}`"],
        ]),
        "El identificador de paciente (`ID_PACIENTE`) es también el grupo que debe usar la validación cruzada agrupada dentro del "
        "conjunto de desarrollo.",

        "## 8. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),

        "## Anexo. Casos de estudio por hospital",
        "Porcentaje de los casos de estudio de cada conjunto que corresponde a cada hospital. Los nombres son los de la tabla "
        "maestra del DEIS.",
        tabla_composicion("Hospital", info["composicion"]["Hospital"], nombres_hospitales()),
    ]
    salida = DIR_REPORTS / "10_particion.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par = cargar_parametros()
    version = comprobar_version()
    print(f"Conjunto analítico: versión {version['version']}. Particionando...", flush=True)
    conjunto, lista, info = particionar(par)
    print(f"  casos de estudio: {info['casos']['DESARROLLO']:,} en desarrollo y {info['casos']['PRUEBA']:,} en prueba "
          f"({time.time() - inicio:.0f} s)", flush=True)
    print("Escribiendo...", flush=True)
    info["verificaciones"] += escribir(conjunto, lista)
    registro, es_nueva = registrar(par, version, info)
    print(f"Versión {registro['version']} de la partición ({'nueva' if es_nueva else 'ya registrada'})", flush=True)
    escribir_reporte(info, par, version, registro)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
