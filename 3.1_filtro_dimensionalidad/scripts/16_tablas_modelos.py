"""Tablas para los modelos (actividad 3.1, script 16).

Cierre de la Etapa 3 de la propuesta. Junta en dos tablas lo que dejaron los scripts 13, 14 y 15, para que los modelos
de la actividad 3.2 lean solo esto (bitácora de la 3.1, D57). No calcula variables nuevas.

  1. Versión. Comprueba que el conjunto de desarrollo sea el de la última versión registrada de la partición y que
     validacion_temporal.parquet (script 13) y variables_casos.parquet (script 15) tengan exactamente sus casos de
     estudio, en el mismo orden. No abre el conjunto de prueba.
  2. Tabla de casos. Una fila por caso de estudio de desarrollo: los identificadores, las columnas que organizan la
     validación (año del alta, período de la validación temporal, paciente ya visto y pliegue), las 30 variables del
     script 15 y las cuatro variables objetivo. Es una sola tabla para las cuatro: cada modelo usa los casos que tienen
     dato en la suya.
  3. Tabla de códigos. Una fila por caso de estudio y código (formato largo), solo con los códigos que están en alguna
     lista de listas_codigos.parquet (script 14): los códigos completos y, para la lista agrupada, los diagnósticos en
     su categoría. Con ella se arma la matriz de la lista que se use, con una columna sí/no por código. Guardar esa
     matriz con todas sus columnas no cabe en la memoria: con la lista sin filtro serían unos 24 GB por variable.
  4. Verificaciones. Entre otras, que cada código tenga en esta tabla los mismos casos con dato que en
     filtro_codigos.parquet, y que en las listas de cada pliegue todo código tenga el mínimo de casos en su entrenamiento.
  5. Salida. data/processed/modelos_casos.parquet y data/processed/modelos_codigos.parquet; el diccionario
     (docs/diccionario_tablas_modelos.md) y el registro de versión (docs/version_tablas_modelos.csv, que solo agrega una
     fila si cambió alguna tabla o algo de lo que las produce), si todas las verificaciones se cumplen, y el reporte
     reportes/16_tablas_modelos.md.

Las columnas, su papel y su descripción están en reglas/columnas_modelos.csv. Las de papel IDENTIFICADOR, VALIDACION u
OBJETIVO nunca son predictoras. Los códigos se sacan con la misma función del script 14 (tabla_larga), para que sean
exactamente los del filtro.

El conjunto de prueba se arma del mismo modo en la evaluación final, con las listas de todo desarrollo (PLIEGUE 0).

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\scripts\\16_tablas_modelos.py
"""

import csv
import hashlib
import importlib.util
import platform
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_DATOS = RAIZ / "data" / "processed"
DESARROLLO = DIR_DATOS / "desarrollo.parquet"
GRUPOS = DIR_DATOS / "validacion_temporal.parquet"     # período, paciente ya visto y pliegue (script 13)
VARIABLES = DIR_DATOS / "variables_casos.parquet"      # las 30 variables de los casos (script 15)
LISTAS = DIR_DATOS / "listas_codigos.parquet"          # las listas de códigos (script 14)
FILTRO = DIR_DATOS / "filtro_codigos.parquet"          # los casos de cada código (script 14), para comprobar
CASOS = DIR_DATOS / "modelos_casos.parquet"
CODIGOS = DIR_DATOS / "modelos_codigos.parquet"
REGISTRO_PARTICION = RAIZ / "docs" / "version_particion.csv"
REGISTRO = RAIZ / "docs" / "version_tablas_modelos.csv"
DICCIONARIO = RAIZ / "docs" / "diccionario_tablas_modelos.md"
ARCHIVO_COLUMNAS = ACTIVIDAD / "reglas" / "columnas_modelos.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"
SCRIPT_14 = ACTIVIDAD / "scripts" / "14_filtro_codigos.py"
REPORTE = ACTIVIDAD / "reportes" / "16_tablas_modelos.md"

TABLAS = {"modelos_casos": "una fila por caso de estudio de desarrollo", "modelos_codigos": "una fila por caso de estudio y código"}
ROLES = {
    "IDENTIFICADOR": "identifica el caso o el paciente. Nunca es predictora",
    "VALIDACION": "organiza la validación (pliegues, validación temporal y año del alta). Nunca es predictora",
    "PREDICTORA": "variable del modelo (D46 a D49 y D54, script 15)",
    "OBJETIVO": "variable de reingreso que predice el modelo. Nunca es predictora",
    "CODIGO": "describe los códigos de cada caso: los de la lista elegida pasan a ser predictoras sí/no",
}
# Columnas que nunca pueden estar en las tablas para los modelos: describen lo que pasa después del alta, la identidad de
# la persona o cómo se armó la cohorte (D36 y bitácora de la 2.2; D49).
PROHIBIDAS = ["DIAS_REING", "ID_EGRESO_REING", "IDENTIDAD_AMBIGUA", "ID_PERSONA", "ID_EPISODIO", "BLOQUE_ID",
              "ANIO_ARCHIVO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO", "MOTIVO_EXCLUSION", "FECHAALTA", "FECHA_INGRESO"]
BLOQUES = ["DIAGNOSTICO", "PROCEDIMIENTO"]
NIVELES = ["COMPLETO", "CATEGORIA"]
COMBINACIONES = [("DIAGNOSTICO", "COMPLETO"), ("DIAGNOSTICO", "CATEGORIA"), ("PROCEDIMIENTO", "COMPLETO")]
PERIODOS = {"ENTRENAMIENTO": "anios_entrenamiento_temporal", "EVALUACION": "anios_evaluacion_temporal"}
NOMBRE_BLOQUE = {"DIAGNOSTICO": "Diagnóstico", "PROCEDIMIENTO": "Procedimiento"}
NOMBRE_NIVEL = {"COMPLETO": "Completo", "CATEGORIA": "Categoría"}
NOMBRE_LISTA = {"A": "A", "C": "C", "AGRUPADA": "Agrupada", "SIN_FILTRO": "Sin filtro"}
CDM_PARTO = "14"     # los partos no tienen dato en las dos variables relacionadas (D38)
SIN_DATO = "SIN DATO"
EJEMPLO = 20230000956  # el caso del ejemplo de la explicación del cierre (también está en el reporte 15)
CAMPOS = ["version", "fecha", "version_particion", "casos", "columnas_casos", "pares_codigos", "sha256_casos", "sha256_codigos",
          "sha256_desarrollo", "sha256_validacion_temporal", "sha256_variables_casos", "sha256_listas_codigos",
          "sha256_columnas", "sha256_script_16", "python", "pandas", "pyarrow"]


# ------------------------------------------------------------------ utilidades
def cargar_script(ruta: Path):
    """Importa otro script por su ruta. Su nombre empieza con un número, así que no sirve `import`."""
    spec = importlib.util.spec_from_file_location("script_" + ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def entero(x) -> str:
    """Los números de cinco cifras o más llevan punto de miles; los años y los números cortos, no."""
    return fmt(x) if abs(x) >= 10_000 else str(int(x))


def dec(x, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(lineas)


# ------------------------------------------------------------------ 1. reglas y versión
def cargar_columnas() -> dict[str, list[dict]]:
    """Las columnas de cada tabla, en su orden, con su papel, su origen y su descripción."""
    filas = leer_csv(ARCHIVO_COLUMNAS)
    for f in filas:
        if None in f or any(v is None for v in f.values()):
            raise SystemExit(f"{ARCHIVO_COLUMNAS.name}: la fila de '{f.get('columna')}' tiene un «;» de más o le falta un campo.")
        if f["tabla"] not in TABLAS or f["rol"] not in ROLES:
            raise SystemExit(f"{ARCHIVO_COLUMNAS.name}: la fila de '{f['columna']}' tiene una tabla o un papel desconocido.")
    por_tabla = {t: [f for f in filas if f["tabla"] == t] for t in TABLAS}
    for t, fs in por_tabla.items():
        nombres = [f["columna"] for f in fs]
        if len(set(nombres)) != len(nombres):
            raise SystemExit(f"{ARCHIVO_COLUMNAS.name}: hay columnas repetidas en {t}.")
        if set(nombres) & set(PROHIBIDAS):
            raise SystemExit(f"{ARCHIVO_COLUMNAS.name}: {sorted(set(nombres) & set(PROHIBIDAS))} no pueden estar en las tablas.")
    return por_tabla


def cargar_parametros_23() -> tuple[dict[str, list[int]], int]:
    """Los años de cada período de la validación temporal y el número de pliegues (scripts 13 y 10)."""
    filas = {f["parametro"]: f["valor"] for f in leer_csv(PARAMETROS_23)}
    anios = {p: [int(a) for a in filas[nombre].split("|") if a.strip()] for p, nombre in PERIODOS.items()}
    return anios, int(filas["pliegues_validacion_cruzada"])


def comprobar_version() -> dict:
    """Solo se trabaja sobre el conjunto de desarrollo de la última versión registrada de la partición (D29)."""
    if not REGISTRO_PARTICION.exists():
        raise SystemExit(f"No existe {REGISTRO_PARTICION.name}: ejecute antes el script 10.")
    version = leer_csv(REGISTRO_PARTICION)[-1]
    if sha256(DESARROLLO) != version["sha256_desarrollo"]:
        raise SystemExit(f"{DESARROLLO.name} no es el de la versión {version['version']} de la partición: ejecute el script 10.")
    return version


# ------------------------------------------------------------------ 2. tabla de casos
def leer_entradas(objetivos: list[str]) -> tuple[pa.Table, pa.Table, pa.Table]:
    for ruta, script in [(GRUPOS, 13), (VARIABLES, 15), (LISTAS, 14), (FILTRO, 14)]:
        if not ruta.exists():
            raise SystemExit(f"No existe {ruta.name}: ejecute antes el script {script}.")
    d = pq.read_table(DESARROLLO, columns=["ID_EGRESO", "ID_PACIENTE", "ANIO_ARCHIVO", "FECHAALTA", *objetivos],
                      filters=[("ES_CASO_ESTUDIO", "==", True)])
    g = pq.read_table(GRUPOS)
    v = pq.read_table(VARIABLES)
    for ruta, t in [(GRUPOS, g), (VARIABLES, v)]:
        if not t["ID_EGRESO"].equals(d["ID_EGRESO"]):
            raise SystemExit(f"{ruta.name} no tiene exactamente los casos de estudio de {DESARROLLO.name}, en el mismo orden: "
                             "vuelva a ejecutar los scripts 13 a 15.")
    return d, g, v


def armar_casos(d: pa.Table, g: pa.Table, v: pa.Table, columnas: list[dict], objetivos: list[str]) -> pa.Table:
    """Toma cada columna de su origen, sin cambiar su tipo, en el orden de reglas/columnas_modelos.csv."""
    fuentes = {"ID_EGRESO": d["ID_EGRESO"], "ID_PACIENTE": d["ID_PACIENTE"], "ANIO_ALTA": d["ANIO_ARCHIVO"],
               "PERIODO": g["PERIODO"], "PACIENTE_VISTO": g["PACIENTE_VISTO"], "PLIEGUE": g["PLIEGUE"]}
    fuentes |= {c: v[c] for c in v.column_names if c != "ID_EGRESO"}
    fuentes |= {k: d[k] for k in objetivos}
    orden = [f["columna"] for f in columnas]
    if sorted(orden) != sorted(fuentes):
        raise SystemExit(f"{ARCHIVO_COLUMNAS.name} no describe las columnas de la tabla de casos. "
                         f"Faltan: {sorted(set(fuentes) - set(orden))}. Sobran: {sorted(set(orden) - set(fuentes))}.")
    return pa.table({c: fuentes[c].combine_chunks() for c in orden})


# ------------------------------------------------------------------ 3. tabla de códigos
def codigos_de_listas(listas: pd.DataFrame) -> pd.DataFrame:
    """Los códigos distintos de todas las listas (de todas las variables y pliegues), ordenados por bloque, nivel y código.
    Su posición en esta tabla es el número de cada código (ID)."""
    union = listas[["BLOQUE", "NIVEL", "CODIGO"]].drop_duplicates().astype(str)
    desconocidos = set(map(tuple, union[["BLOQUE", "NIVEL"]].drop_duplicates().to_numpy())) - set(COMBINACIONES)
    if desconocidos:
        raise SystemExit(f"{LISTAS.name} tiene bloques o niveles desconocidos: {sorted(desconocidos)}.")
    union["_b"] = union["BLOQUE"].map(BLOQUES.index)
    union["_n"] = union["NIVEL"].map(NIVELES.index)
    return union.sort_values(["_b", "_n", "CODIGO"]).drop(columns=["_b", "_n"]).reset_index(drop=True)


def armar_pares(m14, n: int, union: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict]:
    """Fila del caso e ID del código de cada par caso-código, solo con los códigos de alguna lista, ordenados por caso y
    código. También devuelve, por bloque y nivel, cuántos pares y códigos hay antes y después de quitar los demás."""
    columnas = [c for cols, _ in m14.BLOQUES.values() for c in cols]
    casos = pd.read_parquet(DESARROLLO, columns=columnas, filters=[("ES_CASO_ESTUDIO", "==", True)]).reset_index(drop=True)
    if len(casos) != n:
        raise SystemExit(f"{DESARROLLO.name} cambió mientras se leía.")
    filas, ids, info = [], [], {"todos": {}, "en_listas": {}, "por_caso": {}}
    for bloque, nivel in COMBINACIONES:
        largo = m14.tabla_larga(casos, m14.BLOQUES[bloque][0], nivel)   # la misma función del filtro de códigos
        fila = largo["FILA"].to_numpy().astype(np.int64)
        if nivel == "COMPLETO":
            info["por_caso"][bloque] = np.bincount(fila, minlength=n)
        sub = union[(union["BLOQUE"] == bloque) & (union["NIVEL"] == nivel)]
        categorias = largo["CODIGO"].cat.categories
        posicion = pd.Index(sub["CODIGO"]).get_indexer(categorias)       # -1 si el código no está en ninguna lista
        id_categoria = np.where(posicion >= 0, sub.index.to_numpy()[posicion], -1)
        id_par = id_categoria[largo["CODIGO"].cat.codes.to_numpy()]
        en_lista = id_par >= 0
        info["todos"][(bloque, nivel)] = (len(largo), int(largo["CODIGO"].nunique()))
        info["en_listas"][(bloque, nivel)] = (int(en_lista.sum()), len(sub))
        filas.append(fila[en_lista])
        ids.append(id_par[en_lista].astype(np.int64))
        del largo
    del casos
    fila, ident = np.concatenate(filas), np.concatenate(ids)
    orden = np.argsort(fila * len(union) + ident, kind="stable")
    return fila[orden], ident[orden], info


def tabla_codigos(fila: np.ndarray, ident: np.ndarray, union: pd.DataFrame, id_egreso: np.ndarray) -> pa.Table:
    """BLOQUE, NIVEL y CODIGO se guardan como categorías (cada valor distinto una sola vez): la tabla ocupa mucho menos."""
    textos = sorted(union["CODIGO"].unique())
    pos_codigo = pd.Index(textos).get_indexer(union["CODIGO"]).astype(np.int32)
    pos_bloque = pd.Index(BLOQUES).get_indexer(union["BLOQUE"]).astype(np.int8)
    pos_nivel = pd.Index(NIVELES).get_indexer(union["NIVEL"]).astype(np.int8)
    return pa.table({
        "ID_EGRESO": pa.array(id_egreso[fila]),
        "BLOQUE": pa.DictionaryArray.from_arrays(pa.array(pos_bloque[ident]), pa.array(BLOQUES)),
        "NIVEL": pa.DictionaryArray.from_arrays(pa.array(pos_nivel[ident]), pa.array(NIVELES)),
        "CODIGO": pa.DictionaryArray.from_arrays(pa.array(pos_codigo[ident]), pa.array(textos)),
    })


def ids_listas(listas: pd.DataFrame, union: pd.DataFrame) -> dict[tuple, np.ndarray]:
    """IDs de los códigos de cada lista: (VARIABLE, LISTA, PLIEGUE) → IDs."""
    con_id = listas.astype({"BLOQUE": str, "NIVEL": str, "CODIGO": str}).merge(
        union.reset_index(names="ID"), on=["BLOQUE", "NIVEL", "CODIGO"], how="left")
    return {(k, lista, int(f)): g["ID"].to_numpy(dtype=np.int64)
            for (k, lista, f), g in con_id.groupby(["VARIABLE", "LISTA", "PLIEGUE"], sort=False)}


def conteos(fila: np.ndarray, ident: np.ndarray, y: np.ndarray, pliegue: np.ndarray, n_codigos: int,
            n_pliegues: int) -> np.ndarray:
    """Casos con dato en la variable que tienen cada código (filas), por pliegue (columnas)."""
    con_dato = ~np.isnan(y[fila])
    clave = ident[con_dato] * n_pliegues + (pliegue[fila[con_dato]] - 1)
    return np.bincount(clave, minlength=n_codigos * n_pliegues).reshape(n_codigos, n_pliegues)


# ------------------------------------------------------------------ 4. verificaciones
def verificar(casos: pa.Table, d: pa.Table, g: pa.Table, columnas: dict, fila: np.ndarray, ident: np.ndarray,
              union: pd.DataFrame, listas_id: dict, cuentas: dict, info: dict, par: dict) -> list[tuple[str, bool]]:
    n, K = casos.num_rows, len(union)
    id_egreso = casos["ID_EGRESO"].to_numpy()
    paciente = casos["ID_PACIENTE"].to_numpy()
    pliegue = casos["PLIEGUE"].to_numpy().astype(np.int64)
    periodo = casos["PERIODO"].to_numpy(zero_copy_only=False)
    anio = casos["ANIO_ALTA"].to_numpy()
    visto_nulo = casos["PACIENTE_VISTO"].is_null().to_numpy(zero_copy_only=False)
    y = {k: casos[k].to_numpy(zero_copy_only=False).astype("float64") for k in par["objetivos"]}
    parto = casos["CDM"].to_numpy(zero_copy_only=False) == CDM_PARTO

    # Un paciente en un solo pliegue
    orden = np.lexsort((pliegue, paciente))
    p_ord, f_ord = paciente[orden], pliegue[orden]
    mismo_paciente = p_ord[1:] == p_ord[:-1]
    un_pliegue = not bool((mismo_paciente & (f_ord[1:] != f_ord[:-1])).any())

    # Los mismos casos con dato que filtro_codigos.parquet, para cada variable y cada código de alguna lista
    filtro = pd.read_parquet(FILTRO, columns=["VARIABLE", "BLOQUE", "NIVEL", "CODIGO", "CASOS"]).astype(
        {"VARIABLE": str, "BLOQUE": str, "NIVEL": str, "CODIGO": str})
    igual_filtro = True
    for k in par["objetivos"]:
        esperado = union.merge(filtro[filtro["VARIABLE"] == k], on=["BLOQUE", "NIVEL", "CODIGO"], how="left")["CASOS"]
        igual_filtro &= bool(esperado.notna().all() and (esperado.to_numpy() == cuentas[k].sum(axis=1)).all())

    # En las listas de cada pliegue, el mínimo de casos se cumple en el entrenamiento (sin los casos del pliegue)
    minimo_pliegues = True
    for (k, lista, f), ids in listas_id.items():
        total = cuentas[k].sum(axis=1)
        entrenamiento = total[ids] - (cuentas[k][ids, f - 1] if f > 0 else 0)
        minimo_pliegues &= bool((entrenamiento >= par["casos_minimos"]).all())

    pares_unicos = not bool(((fila[1:] == fila[:-1]) & (ident[1:] == ident[:-1])).any())   # están ordenados por caso y código
    columnas_casos = [f["columna"] for f in columnas["modelos_casos"]]
    anios = par["anios_temporales"]
    return [
        ("La tabla de casos tiene una fila por caso de estudio de desarrollo, sin repetir ID_EGRESO",
         n == int(par["version"]["casos_desarrollo"]) and len(np.unique(id_egreso)) == n),
        (f"Sus columnas son las de {ARCHIVO_COLUMNAS.name}, en su orden, y no tiene ninguna de las que nunca pueden estar",
         casos.column_names == columnas_casos and not set(casos.column_names) & set(PROHIBIDAS)),
        ("ID_PACIENTE de desarrollo es igual al de validacion_temporal.parquet en todos los casos",
         d["ID_PACIENTE"].equals(g["ID_PACIENTE"])),
        ("ANIO_ALTA es el año de la fecha de alta, y PERIODO corresponde a los años de la validación temporal",
         bool((pc.year(d["FECHAALTA"]).to_numpy() == anio).all()
              and all((np.isin(anio, anios[p]) == (periodo == p)).all() for p in PERIODOS))),
        ("PACIENTE_VISTO tiene dato justo en los casos de evaluación",
         bool((visto_nulo == (periodo == "ENTRENAMIENTO")).all())),
        (f"PLIEGUE va de 1 a {par['n_pliegues']} y ningún paciente está en dos pliegues",
         bool(pliegue.min() == 1 and pliegue.max() == par["n_pliegues"]) and un_pliegue),
        ("Las variables objetivo valen 0 o 1, y REING_7D tiene dato en todos los casos",
         all(bool(np.isin(v[~np.isnan(v)], [0, 1]).all()) for v in y.values()) and not np.isnan(y["REING_7D"]).any()),
        ("Las variables relacionadas no tienen dato justo en los partos (CDM 14) y, a 30 días, en los casos sin dato en REING_30D",
         bool((np.isnan(y["REING_7D_CDM"]) == parto).all() and (np.isnan(y["REING_30D_CDM"]) == (parto | np.isnan(y["REING_30D"]))).all())),
        ("Antes de quitar los códigos que no están en ninguna lista, cada caso tiene tantos diagnósticos y procedimientos "
         "distintos como dicen N_DIAGNOSTICOS y N_PROCEDIMIENTOS (script 15)",
         bool((info["por_caso"]["DIAGNOSTICO"] == casos["N_DIAGNOSTICOS"].to_numpy()).all()
              and (info["por_caso"]["PROCEDIMIENTO"] == casos["N_PROCEDIMIENTOS"].to_numpy()).all())),
        ("La tabla de códigos no repite un código en un caso, y está ordenada por caso",
         pares_unicos and bool((np.diff(fila) >= 0).all())),
        ("Todo código de alguna lista aparece en la tabla de códigos, y la tabla no tiene códigos fuera de las listas",
         bool((np.bincount(ident, minlength=K) > 0).all() and ident.max() < K)),
        ("Para cada variable y cada código de alguna lista, la tabla de códigos tiene los mismos casos con dato que "
         "filtro_codigos.parquet (las columnas de la matriz suman lo mismo que el filtro)", igual_filtro),
        (f"En las listas de cada pliegue, todo código tiene al menos {par['casos_minimos']} casos con dato en el entrenamiento "
         "del pliegue, y en las de todo desarrollo, en todo desarrollo", minimo_pliegues),
    ]


# ------------------------------------------------------------------ 5. salida
def escribir(casos: pa.Table, codigos: pa.Table) -> list[tuple[str, bool]]:
    iguales = []
    for tabla, destino in [(casos, CASOS), (codigos, CODIGOS)]:
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(".parquet.tmp")
        pq.write_table(tabla, temporal, compression="zstd")
        temporal.replace(destino)
        releido = pq.read_table(destino)
        igual = releido.column_names == tabla.column_names and releido.num_rows == tabla.num_rows
        for col in tabla.column_names:   # las categorías se comparan por su valor, no por cómo quedó guardado su diccionario
            a, b = releido[col], tabla[col]
            if pa.types.is_dictionary(b.type):
                a, b = a.cast(b.type.value_type), b.cast(b.type.value_type)
            igual = igual and a.equals(b)
            del a, b
        iguales.append(igual)
    return [("Lo releído de modelos_casos.parquet y de modelos_codigos.parquet es igual a lo calculado", all(iguales))]


def registrar_version(ficha: dict) -> tuple[dict, bool]:
    """Devuelve la versión que corresponde a las tablas actuales y si es nueva. Solo agrega una fila si cambió alguna de las
    dos tablas o algo de lo que las produce (sus entradas, la tabla de columnas o este script)."""
    filas = leer_csv(REGISTRO) if REGISTRO.exists() else []
    hashes = [c for c in CAMPOS if c.startswith("sha256_")]
    if filas and all(filas[-1].get(c) == ficha[c] for c in hashes):
        return filas[-1], False
    nueva = {"version": str(int(filas[-1]["version"]) + 1 if filas else 1), "fecha": date.today().isoformat(), **ficha}
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRO, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";", lineterminator="\r\n")
        escritor.writeheader()
        escritor.writerows([*filas, nueva])
    return nueva, True


def describir(col: pa.ChunkedArray, rol: str) -> tuple[str, str, str]:
    """Tipo, valores y casos sin dato de una columna, en palabras."""
    t, n = col.type, len(col)
    nulos = col.null_count
    if rol == "IDENTIFICADOR":
        return "Entero", f"{fmt(pc.count_distinct(col).as_py())} distintos", fmt(nulos) if nulos else "—"
    if pa.types.is_dictionary(t):
        col = col.cast(t.value_type)
        t = col.type
    if pa.types.is_boolean(t):
        return "Verdadero/falso", "verdadero o falso", fmt(nulos) if nulos else "—"
    if pa.types.is_integer(t) or pa.types.is_floating(t):
        minimo, maximo = pc.min_max(col).values()
        minimo, maximo = minimo.as_py(), maximo.as_py()
        if pa.types.is_integer(t):
            valores = "0 o 1" if (minimo, maximo) == (0, 1) else f"de {entero(minimo)} a {entero(maximo)}"
            tipo = "Entero"
        else:
            valores, tipo = f"de {dec(minimo, 1)} a {dec(maximo, 1)}", "Decimal"
        nan = int(pc.sum(pc.is_nan(col)).as_py() or 0) if pa.types.is_floating(t) else 0
        return tipo, valores, fmt(nulos + nan) if nulos + nan else "—"
    cuenta = pc.value_counts(col)
    pares = sorted(((v.as_py(), c.as_py()) for v, c in zip(cuenta.field("values"), cuenta.field("counts"))), key=lambda x: -x[1])
    sin_dato = nulos + sum(c for v, c in pares if v == SIN_DATO)
    if len(pares) <= 6:
        valores = ", ".join(f"{v} ({pct(c, n, 1)})" for v, c in pares if v is not None)
    else:
        valores = f"{fmt(len([v for v, _ in pares if v is not None]))} valores"
    return "Texto", valores, fmt(sin_dato) if sin_dato else "—"


RECETA = '''```python
import numpy as np
import pandas as pd
import scipy.sparse as sp

casos = pd.read_parquet("data/processed/modelos_casos.parquet")
codigos = pd.read_parquet("data/processed/modelos_codigos.parquet")
listas = pd.read_parquet("data/processed/listas_codigos.parquet")

variable, lista, pliegue = "REING_30D", "A", 0   # pliegue 0: todo desarrollo; k: el entrenamiento sin el pliegue k
filas = casos[casos[variable].notna()].reset_index(drop=True)   # solo los casos con dato en la variable
columnas = (listas[(listas["VARIABLE"] == variable) & (listas["LISTA"] == lista) & (listas["PLIEGUE"] == pliegue)]
            [["BLOQUE", "NIVEL", "CODIGO"]].reset_index(drop=True))
pares = (codigos.astype({"BLOQUE": str, "NIVEL": str, "CODIGO": str})
         .merge(columnas.reset_index(names="j"), on=["BLOQUE", "NIVEL", "CODIGO"]))   # j: columna de la matriz
pares["i"] = pd.Index(filas["ID_EGRESO"]).get_indexer(pares["ID_EGRESO"])               # i: fila (-1 si no tiene dato)
pares = pares[pares["i"] >= 0]
X = sp.csr_matrix((np.ones(len(pares), dtype=np.int8), (pares["i"], pares["j"])), shape=(len(filas), len(columnas)))
y = filas[variable].to_numpy()
```'''


def escribir_diccionario(casos: pa.Table, codigos: pa.Table, columnas: dict, version: dict, listas_id: dict,
                         union: pd.DataFrame, par: dict) -> None:
    ruta = ACTIVIDAD.name
    # Un mismo texto puede ser un código completo y una categoría (I10 no tiene subcategorías): se distinguen por el NIVEL.
    repetidos = union[union.duplicated("CODIGO", keep=False)].sort_values(["CODIGO", "NIVEL"])
    ejemplo_repetido = repetidos["CODIGO"].iloc[0] if len(repetidos) else ""
    textos_distintos = union["CODIGO"].nunique()
    secciones = []
    for nombre, tabla in [("modelos_casos", casos), ("modelos_codigos", codigos)]:
        filas = []
        for f in columnas[nombre]:
            tipo, valores, sin_dato = describir(tabla[f["columna"]], f["rol"])
            filas.append([f"`{f['columna']}`", f["rol"], tipo, f["descripcion"], valores, sin_dato, f["origen"]])
        secciones.append(tabla_md(["Columna", "Papel", "Tipo", "Descripción", "Valores", "Sin dato", "Origen"], filas))
    n_pl = par["n_pliegues"]
    filas_listas = []
    for k in par["objetivos"]:
        for lista in par["listas"]:
            por_pliegue = [len(listas_id[(k, lista, f)]) for f in range(1, n_pl + 1) if (k, lista, f) in listas_id]
            rango = f"{fmt(min(por_pliegue))} a {fmt(max(por_pliegue))}" if por_pliegue else "— (no mira el reingreso)"
            filas_listas.append([f"`{k}`", f"`{lista}`", fmt(len(listas_id.get((k, lista, 0), []))), rango])
    partes = [
        "# Diccionario de las tablas para los modelos",
        f"Generado por `{ruta}/scripts/16_tablas_modelos.py`. Son las tablas que leen los modelos de la actividad 3.2: "
        f"`data/processed/{CASOS.name}` ({TABLAS['modelos_casos']}: {fmt(casos.num_rows)} filas y {casos.num_columns} columnas) y "
        f"`data/processed/{CODIGOS.name}` ({TABLAS['modelos_codigos']}: {fmt(codigos.num_rows)} filas), junto con las listas de "
        f"códigos de `data/processed/{LISTAS.name}` (script 14). Solo tienen los casos de estudio del conjunto de desarrollo: el "
        "conjunto de prueba se arma igual en la evaluación final, con las listas de todo desarrollo (`PLIEGUE` = 0).",

        "## Versión de las tablas",
        tabla_md(["Dato", "Valor"], [
            ["Versión", version["version"]],
            ["Fecha de registro", version["fecha"]],
            ["Versión de la partición", f"{version['version_particion']} (`docs/{REGISTRO_PARTICION.name}`)"],
            ["Casos, columnas de la tabla de casos y pares caso–código",
             f"{fmt(version['casos'])}, {version['columnas_casos']} y {fmt(version['pares_codigos'])}"],
            [f"SHA-256 de `{CASOS.name}`", f"`{version['sha256_casos']}`"],
            [f"SHA-256 de `{CODIGOS.name}`", f"`{version['sha256_codigos']}`"],
            [f"SHA-256 de `{DESARROLLO.name}`", f"`{version['sha256_desarrollo']}`"],
            [f"SHA-256 de `{GRUPOS.name}`", f"`{version['sha256_validacion_temporal']}`"],
            [f"SHA-256 de `{VARIABLES.name}`", f"`{version['sha256_variables_casos']}`"],
            [f"SHA-256 de `{LISTAS.name}`", f"`{version['sha256_listas_codigos']}`"],
            [f"SHA-256 de `{ARCHIVO_COLUMNAS.name}`", f"`{version['sha256_columnas']}`"],
            ["SHA-256 de `16_tablas_modelos.py`", f"`{version['sha256_script_16']}`"],
            ["Bibliotecas", f"Python {version['python']}, pandas {version['pandas']}, pyarrow {version['pyarrow']}"],
        ]),
        f"El historial está en `docs/{REGISTRO.name}`: solo se agrega una fila cuando cambia alguna de las dos tablas o algo de lo "
        "que las produce (sus entradas, la tabla de columnas o el script). Antes de entrenar, conviene comprobar que los "
        "archivos tengan el hash de la última versión registrada.",

        "## Cómo se usan",
        "\n".join([
            "1. **Elegir la variable objetivo** y usar solo los casos que tienen dato en ella. Los casos sin dato no son 0: no "
            "tienen el seguimiento necesario (las de 30 días) o son partos (las de misma CDM).",
            f"2. **Elegir la lista de códigos y el pliegue** en `{LISTAS.name}`. En la validación cruzada, al entrenar sin el "
            "pliegue k se usa la lista de `PLIEGUE` = k, calculada con ese entrenamiento, y se evalúa en el pliegue k (D53). El "
            "modelo final y el conjunto de prueba usan la de `PLIEGUE` = 0, calculada con todo desarrollo.",
            f"3. **Armar la matriz de códigos:** una columna sí/no por código de la lista. Un caso tiene 1 en una columna si en "
            f"`{CODIGOS.name}` hay una fila con su `ID_EGRESO` y el `BLOQUE`, el `NIVEL` y el `CODIGO` de esa columna. Como "
            "casi todas las celdas son 0, conviene una matriz dispersa, que guarda solo los 1 (receta al final).",
            "4. **Juntarla con las predictoras** (papel PREDICTORA) de la tabla de casos. Cómo se codifican las categorías y si "
            "se transforman los números se decide con cada modelo en la actividad 3.2.",
            "5. **Evaluar** con `PLIEGUE` (validación cruzada, D52), `PERIODO` y `PACIENTE_VISTO` (validación temporal, D40), "
            "`ANIO_ALTA` (calibración por año, D56) e `ID_PACIENTE` (intervalos con remuestreo de pacientes, D41).",
        ]),

        "## Papeles de las columnas",
        tabla_md(["Papel", "Qué significa"], [[r, d] for r, d in ROLES.items()]),
        "Las columnas de papel IDENTIFICADOR, VALIDACION u OBJETIVO nunca son predictoras. Tampoco están, en ninguna de las dos "
        "tablas, las columnas que describen lo que pasa después del alta (`DIAS_REING` e `ID_EGRESO_REING`), la identidad de la "
        "persona (`ID_PERSONA`, `IDENTIDAD_AMBIGUA`) ni cómo se armó la cohorte.",

        f"## 1. `{CASOS.name}`",
        f"Una fila por caso de estudio de desarrollo, en el orden de `{DESARROLLO.name}` (de menor a mayor `ID_EGRESO`). "
        "**Sin dato:** en las columnas de texto, el valor SIN DATO; en las numéricas, el valor nulo.",
        secciones[0],

        f"## 2. `{CODIGOS.name}`",
        f"Una fila por caso de estudio y código distinto, ordenada por `ID_EGRESO`. Solo tiene los códigos que están en alguna "
        f"lista de `{LISTAS.name}`, de cualquier variable y pliegue: los diagnósticos y procedimientos completos y, para la lista "
        "agrupada, los diagnósticos en su categoría. Un caso puede no tener ninguna fila. `BLOQUE`, `NIVEL` y `CODIGO` se guardan "
        "como categorías (cada valor distinto se guarda una sola vez).",
        secciones[1],
        (f"Hay {fmt(len(union))} códigos distintos pero {fmt(textos_distintos)} textos: {fmt(len(repetidos) // 2)} textos están con los "
         f"dos niveles, como `{ejemplo_repetido}`, que es a la vez un código completo y una categoría. Por eso una columna de la "
         "matriz se identifica con `BLOQUE`, `NIVEL` y `CODIGO` juntos, nunca con el código solo.") if len(repetidos) else
        "Cada texto de `CODIGO` corresponde a un solo bloque y nivel.",

        f"## 3. `{LISTAS.name}` (script 14)",
        "Una fila por código de cada lista: `VARIABLE` (la variable de reingreso), `LISTA` (`A`, la principal, o una de las "
        "de comparación de D53: `C`, `AGRUPADA` y `SIN_FILTRO`), `PLIEGUE` (0 = todo desarrollo; 1 a 5 = el entrenamiento sin "
        "ese pliegue), `BLOQUE`, `NIVEL` y `CODIGO`. La lista sin filtro no mira el reingreso, así que no tiene versión por "
        "pliegue. Códigos de cada lista:",
        tabla_md(["Variable", "Lista", "Todo desarrollo (PLIEGUE 0)", "Pliegues 1 a 5"], filas_listas),

        "## 4. Receta para armar la matriz",
        "Para la actividad 3.2, con scipy (no está en el entorno del proyecto; se instala con las bibliotecas de los modelos). Las "
        "columnas de `X` quedan en el orden de `columnas`, y cada una suma los casos con dato que tienen ese código: los mismos "
        "`CASOS` de `filtro_codigos.parquet` para esa variable.",
        RECETA,
    ]
    DICCIONARIO.parent.mkdir(parents=True, exist_ok=True)
    DICCIONARIO.write_text("\n\n".join(partes) + "\n", encoding="utf-8")


def escribir_reporte(casos: pa.Table, codigos: pa.Table, fila: np.ndarray, ident: np.ndarray, union: pd.DataFrame,
                     listas_id: dict, columnas: dict, info: dict, par: dict, version: dict, registro: dict | None,
                     verificaciones: list) -> dict:
    ruta = ACTIVIDAD.name
    n, K = casos.num_rows, len(union)

    # 1. Tablas
    filas_tablas = [[f"`data/processed/{CASOS.name}`", fmt(casos.num_rows), casos.num_columns, dec(CASOS.stat().st_size / 1e6, 1),
                     TABLAS["modelos_casos"]],
                    [f"`data/processed/{CODIGOS.name}`", fmt(codigos.num_rows), codigos.num_columns,
                     dec(CODIGOS.stat().st_size / 1e6, 1), TABLAS["modelos_codigos"]]]

    # 2. Variables objetivo
    porque = {"REING_7D": "—", "REING_7D_CDM": "partos (CDM 14)", "REING_30D": "alta a menos de 60 días del cierre del bloque",
              "REING_30D_CDM": "partos o sin dato en REING_30D"}
    filas_obj = []
    for k in par["objetivos"]:
        y = casos[k].to_numpy(zero_copy_only=False).astype("float64")
        con = int((~np.isnan(y)).sum())
        filas_obj.append([f"`{k}`", fmt(con), fmt(np.nansum(y)), pct(np.nansum(y), con), fmt(n - con), porque.get(k, "—")])

    # 3. Papeles
    filas_rol = []
    for rol in ROLES:
        cols = [f["columna"] for f in columnas["modelos_casos"] if f["rol"] == rol]
        if cols:
            filas_rol.append([rol, len(cols), ", ".join(f"`{c}`" for c in cols) if len(cols) <= 6 else
                              f"las {len(cols)} variables del script 15 (D46 a D49 y D54)"])

    # 4. Códigos
    nombre = {c: f"{NOMBRE_BLOQUE[c[0]]}s {'completos' if c[1] == 'COMPLETO' else 'en su categoría'}" for c in COMBINACIONES}
    filas_cod = []
    for c in COMBINACIONES:
        pares_todos, codigos_todos = info["todos"][c]
        pares_lista, codigos_lista = info["en_listas"][c]
        filas_cod.append([nombre[c], fmt(codigos_todos), fmt(pares_todos), fmt(codigos_lista), fmt(pares_lista),
                          pct(pares_lista, pares_todos, 1)])
    sin_codigos = int((np.bincount(fila, minlength=n) == 0).sum())
    sin_ningun_codigo = int(((info["por_caso"]["DIAGNOSTICO"] == 0) & (info["por_caso"]["PROCEDIMIENTO"] == 0)).sum())

    # 5. Tamaño de las matrices (todo desarrollo)
    filas_mat, matrices = [], {}
    for k in par["objetivos"]:
        y = casos[k].to_numpy(zero_copy_only=False).astype("float64")
        con_dato = ~np.isnan(y)
        par_con_dato = con_dato[fila]
        for lista in par["listas"]:
            ids = listas_id.get((k, lista, 0), np.array([], dtype=np.int64))
            en_lista = np.zeros(K, dtype=bool)
            en_lista[ids] = True
            m = par_con_dato & en_lista[ident]
            filas_k, columnas_k, unos = int(con_dato.sum()), len(ids), int(m.sum())
            alguno = int((np.bincount(fila[m], minlength=n) > 0).sum())
            matrices[(k, lista)] = (filas_k, columnas_k, unos)
            filas_mat.append([f"`{k}`", NOMBRE_LISTA[lista], fmt(filas_k), fmt(columnas_k), fmt(unos), pct(unos, filas_k * columnas_k, 3),
                              pct(alguno, filas_k, 1), dec(filas_k * columnas_k / 1e9, 2), dec((unos * 5 + (filas_k + 1) * 8) / 1e6, 0)])

    # 6. Ejemplo
    texto_ejemplo = ""
    posicion = np.flatnonzero(casos["ID_EGRESO"].to_numpy() == EJEMPLO)
    if len(posicion):
        p = int(posicion[0])
        sus = ident[fila == p]
        listas_30 = {lista: set(listas_id.get(("REING_30D", lista, 0), np.array([])).tolist()) for lista in par["listas"]}
        filas_ej = [[f"`{union.at[i, 'CODIGO']}`", NOMBRE_BLOQUE[union.at[i, "BLOQUE"]], NOMBRE_NIVEL[union.at[i, "NIVEL"]],
                     *["sí" if i in listas_30[lista] else "—" for lista in par["listas"]]] for i in sus]
        fila_caso = {c: casos[c][p].as_py() for c in ["EDAD", "SEXO", "CDM", "HOSP_PREVIAS", "PLIEGUE", "ANIO_ALTA", "REING_30D"]}
        texto_ejemplo = "\n\n".join([
            f"El caso `{EJEMPLO}` ({fila_caso['SEXO'].lower()} de {int(fila_caso['EDAD'])} años, alta en {fila_caso['ANIO_ALTA']}, "
            f"CDM {fila_caso['CDM']}, {fila_caso['HOSP_PREVIAS']} "
            f"{'hospitalización previa' if fila_caso['HOSP_PREVIAS'] == 1 else 'hospitalizaciones previas'}, pliegue {fila_caso['PLIEGUE']}, "
            f"`REING_30D` = {fila_caso['REING_30D']}) tiene {len(sus)} filas en `{CODIGOS.name}`. Con `REING_30D`, cada «sí» es "
            "un 1 en la columna de ese código en la matriz de esa lista (todo desarrollo):",
            tabla_md(["Código", "Bloque", "Nivel", *[f"Lista {NOMBRE_LISTA[lista].lower() if len(lista) > 1 else lista}"
                                                     for lista in par["listas"]]], filas_ej),
        ])

    # Verificaciones
    lista_ver = "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in verificaciones)
    fallidas = sum(not ok for _, ok in verificaciones)
    if registro is None:
        texto_version = ("**No se registró la versión ni se escribió el diccionario, porque alguna verificación falló.** Revise "
                         "las verificaciones y vuelva a ejecutar el script.")
    else:
        texto_version = (f"Versión {registro['version']} de las tablas, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`. "
                         f"El diccionario está en `docs/{DICCIONARIO.name}`.")
    partes = [
        "# Tablas para los modelos",
        f"Generado por `{ruta}/scripts/16_tablas_modelos.py` el {date.today():%d-%m-%Y}. Cierre de la actividad 3.1 (D57): "
        f"junta en dos tablas lo que dejaron los scripts 13, 14 y 15 para los modelos de la actividad 3.2. Lee el conjunto de "
        f"desarrollo de la versión {version['version']} de la partición (registrada el {version['fecha']}); no abre el conjunto "
        "de prueba.",
        texto_version,

        "## 1. Tablas",
        tabla_md(["Archivo", "Filas", "Columnas", "MB", "Contenido"], filas_tablas),
        f"Los modelos leen estas dos tablas y las listas de códigos (`data/processed/{LISTAS.name}`, del script 14). Juntas ocupan "
        f"{dec((CASOS.stat().st_size + CODIGOS.stat().st_size + LISTAS.stat().st_size) / 1e6, 0)} MB, frente a "
        f"{dec(DESARROLLO.stat().st_size / 1e6, 0)} MB de `{DESARROLLO.name}`.",

        "## 2. Casos de cada variable objetivo",
        "Una sola tabla de casos para las cuatro variables: cada modelo usa los casos con dato en la suya. Los casos sin dato no "
        "son 0.",
        tabla_md(["Variable", "Casos con dato", "Reingresos", "Tasa", "Sin dato", "Por qué no tienen dato"], filas_obj),

        "## 3. Columnas de la tabla de casos, por papel",
        tabla_md(["Papel", "Columnas", "Cuáles"], filas_rol),
        f"La descripción de cada columna está en `docs/{DICCIONARIO.name}` y en `{ruta}/reglas/{ARCHIVO_COLUMNAS.name}`.",

        "## 4. Códigos de los casos",
        "Se guardan en formato largo: una fila por caso y código, solo con los códigos que están en alguna lista de alguna variable "
        f"y pliegue. Ningún modelo usa los demás: los códigos completos que quedan fuera tienen menos de {par['casos_minimos']} "
        "casos en todas las variables, y las categorías que quedan fuera no pasan la regla de la lista agrupada en ninguna "
        "variable ni pliegue.",
        tabla_md(["Códigos", "Distintos en desarrollo", "Pares caso–código", "Distintos en alguna lista", "Pares en la tabla",
                  "% de los pares"], filas_cod),
        f"{fmt(sin_codigos)} casos ({pct(sin_codigos, n, 3)}) no tienen ninguna fila en la tabla de códigos: {fmt(sin_ningun_codigo)} "
        "no tienen ningún diagnóstico ni procedimiento, y los demás solo tienen códigos que no están en ninguna lista. En la "
        "matriz, su fila queda con 0 en todas las columnas.",

        "## 5. Tamaño de las matrices",
        "Para cada variable y lista de todo desarrollo: cuántas filas (casos con dato) y columnas (códigos) tiene la matriz, "
        "cuántas celdas valen 1 y cuánto ocuparía guardada entera (un byte por celda) o como matriz dispersa (solo los 1: unos "
        "5 bytes por cada uno y 8 por fila). Las listas de cada pliegue tienen un número parecido de columnas.",
        tabla_md(["Variable", "Lista", "Filas", "Columnas", "Celdas con 1", "% de celdas con 1", "Casos con algún código",
                  "Entera (GB)", "Dispersa (MB)"], filas_mat),

        "## 6. Ejemplo",
        texto_ejemplo or f"El caso `{EJEMPLO}` no está en esta versión del conjunto de desarrollo.",

        "## 7. Verificaciones",
        f"{len(verificaciones)} verificaciones, {fallidas} fallidas.",
        lista_ver,
    ]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    return matrices


# ------------------------------------------------------------------ principal
def main() -> None:
    inicio = time.time()
    m14 = cargar_script(SCRIPT_14)
    par = m14.cargar_parametros()   # variables objetivo, mínimo de casos y listas: los mismos del filtro (script 14)
    if par["nivel"] != "COMPLETO":
        raise SystemExit("Las tablas para los modelos usan los códigos completos: nivel_codigo debe ser COMPLETO.")
    par["anios_temporales"], par["n_pliegues"] = cargar_parametros_23()
    columnas = cargar_columnas()
    version = comprobar_version()
    par["version"] = version
    print(f"Partición: versión {version['version']}. Leyendo las tablas de los scripts 13 a 15...", flush=True)
    d, g, v = leer_entradas(par["objetivos"])
    casos = armar_casos(d, g, v, columnas["modelos_casos"], par["objetivos"])
    n = casos.num_rows
    print(f"{fmt(n)} casos de estudio. Sacando los códigos de cada caso ({time.time() - inicio:.0f} s)...", flush=True)
    listas = pd.read_parquet(LISTAS)
    union = codigos_de_listas(listas)
    listas_id = ids_listas(listas, union)
    fila, ident, info = armar_pares(m14, n, union)
    codigos = tabla_codigos(fila, ident, union, casos["ID_EGRESO"].to_numpy())
    if [f["columna"] for f in columnas["modelos_codigos"]] != codigos.column_names:
        raise SystemExit(f"{ARCHIVO_COLUMNAS.name} no describe las columnas de la tabla de códigos: {codigos.column_names}.")
    print(f"{fmt(codigos.num_rows)} pares caso–código. Verificando ({time.time() - inicio:.0f} s)...", flush=True)
    pliegue = casos["PLIEGUE"].to_numpy().astype(np.int64)
    cuentas = {k: conteos(fila, ident, casos[k].to_numpy(zero_copy_only=False).astype("float64"), pliegue, len(union),
                          par["n_pliegues"]) for k in par["objetivos"]}
    verificaciones = [(f"El conjunto de desarrollo es el de la versión {version['version']} registrada de la partición, y "
                       f"{GRUPOS.name} y {VARIABLES.name} tienen exactamente sus casos de estudio, en el mismo orden", True)]
    verificaciones += verificar(casos, d, g, columnas, fila, ident, union, listas_id, cuentas, info, par)
    print(f"Escribiendo ({time.time() - inicio:.0f} s)...", flush=True)
    verificaciones += escribir(casos, codigos)
    registro = None
    if all(ok for _, ok in verificaciones):
        ficha = {"version_particion": version["version"], "casos": str(n), "columnas_casos": str(casos.num_columns),
                 "pares_codigos": str(codigos.num_rows), "sha256_casos": sha256(CASOS), "sha256_codigos": sha256(CODIGOS),
                 "sha256_desarrollo": version["sha256_desarrollo"], "sha256_validacion_temporal": sha256(GRUPOS),
                 "sha256_variables_casos": sha256(VARIABLES), "sha256_listas_codigos": sha256(LISTAS),
                 "sha256_columnas": sha256(ARCHIVO_COLUMNAS), "sha256_script_16": sha256(Path(__file__)),
                 "python": platform.python_version(), "pandas": pd.__version__, "pyarrow": pa.__version__}
        registro, es_nueva = registrar_version(ficha)
        print(f"Versión {registro['version']} de las tablas ({'nueva' if es_nueva else 'ya registrada'})", flush=True)
        escribir_diccionario(casos, codigos, columnas, registro, listas_id, union, par)
        print(f"Diccionario guardado en {DICCIONARIO}")
    escribir_reporte(casos, codigos, fila, ident, union, listas_id, columnas, info, par, version, registro, verificaciones)
    print(f"Reporte guardado en {REPORTE}")
    fallidas = [texto for texto, ok in verificaciones if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
