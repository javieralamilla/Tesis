"""Paso 3: homogenización de los seis años (un Parquet homogenizado por año).

Aplica las mismas reglas a todos los años, sin eliminar ni agregar filas:
  1. Nombres: CIP_ENCRIPTADO / ID_BENEFICIARIO -> ID_PACIENTE; se agregan BLOQUE_ID y CDM.
  2. "Sin dato" unificado: las celdas vacías y los valores como DESCONOCIDO pasan a nulo.
  3. Textos: sin espacios sobrantes y en mayúsculas.
  4. Fechas: AAAA-MM-DD y DD-MM-AAAA -> fecha.
  5. Números: decimal con coma -> número; enteros como enteros.
  6. Códigos (GRD, CIE-10, CIE-9, hospital) como texto.
  7. Categorías renombradas entre años: reglas/equivalencias_categorias.csv.
  8. Se elimina FECHAPROCEDIMIENTO1 (vacía salvo valores con forma de RUT).
  9. Un tipo de dato por columna, igual en los seis años.

Cada cambio se cuenta y se informa en reportes/05_homogenizacion.md. De los valores que no
se pudieron convertir el reporte muestra solo el formato (9 = dígito, A = letra), nunca el valor.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.1_integracion_homogenizacion\\scripts\\05_homogenizar.py
"""

import csv
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_REPORTS = ACTIVIDAD / "reportes"
ARCHIVO_EQUIVALENCIAS = ACTIVIDAD / "reglas" / "equivalencias_categorias.csv"
ANIOS = list(range(2019, 2025))

# Regla 2: valores que significan "sin dato" (se comparan ya sin espacios y en mayúsculas).
NULOS = {"DESCONOCIDO", "DESCONOCIDA", "SIN INFORMACIÓN", "NO APLICA", "NO IDENTIFICADA",
         "NO IDENTIFICADO", "NO CONSIGNADO", "IGNORADO", "NO RESPONDE", "NO ESPECIFICADO",
         "SERVICIO NO DEFINIDO"}
# El 0 es un valor válido en varias columnas; solo se trata como "sin dato" donde no es un código.
NULOS_POR_GRUPO = {"PROCEDIMIENTO1-30": {"0"}, "SERVICIOTRASLADO1-9": {"0"}}

DIAG = [f"DIAGNOSTICO{i}" for i in range(1, 36)]
PROC = [f"PROCEDIMIENTO{i}" for i in range(1, 31)]
COLS_ID = {"CIP_ENCRIPTADO", "ID_BENEFICIARIO"}
COLS_FECHA = {"FECHA_NACIMIENTO", "FECHA_INGRESO", "FECHAALTA", "FECHAINTERV1",
              *(f"FECHATRASLADO{i}" for i in range(1, 10))}
# Enteros: formato aceptado y tipo. USOSPABELLON admite hasta 3 dígitos para que ningún
# valor con forma de RUT quede guardado como número.
COLS_ENTERO = {
    "ID_PACIENTE": (r"\d{1,10}", "Int64"),
    "MEDICOINTERV1_ENCRIPTADO": (r"\d{1,10}", "Int64"),
    "MEDICOALTA_ENCRIPTADO": (r"\d{1,10}", "Int64"),
    "USOSPABELLON": (r"\d{1,3}", "Int16"),
    "IR_29301_SEVERIDAD": (r"\d", "Int8"),
    "IR_29301_MORTALIDAD": (r"\d", "Int8"),
    **{f"PESORN{i}": (r"\d{1,4}", "Int16") for i in range(1, 5)},
    **{f"RN{i}ESTADO": (r"-?\d{1,2}", "Int8") for i in range(1, 5)},
}
COLS_DECIMAL = {"IR_29301_PESO"}
COLS_CODIGO = {"COD_HOSPITAL", "IR_29301_COD_GRD", *DIAG, *PROC}
COLS_ELIMINAR = {"FECHAPROCEDIMIENTO1"}
TRAZABILIDAD = ["ANIO_ARCHIVO", "ARCHIVO_ORIGEN", "FILA_ORIGEN"]
TIPO_ARROW = {"Int64": pa.int64(), "Int16": pa.int16(), "Int8": pa.int8()}

# Columnas repetidas que se informan como un solo grupo.
GRUPOS = [
    (r"DIAGNOSTICO\d+", "DIAGNOSTICO1-35"), (r"PROCEDIMIENTO\d+", "PROCEDIMIENTO1-30"),
    (r"FECHATRASLADO\d", "FECHATRASLADO1-9"), (r"SERVICIOTRASLADO\d", "SERVICIOTRASLADO1-9"),
    (r"CONDICIONDEALTANEONATO\d", "CONDICIONDEALTANEONATO1-4"), (r"PESORN\d", "PESORN1-4"),
    (r"SEXORN\d", "SEXORN1-4"), (r"RN\dESTADO", "RN1-4ESTADO"),
]
FORMA_RUT = r"\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]"

REGISTRO = Counter()                                  # (sección, grupo, detalle, año) -> celdas
CONTEO_ANTES = defaultdict(lambda: defaultdict(Counter))    # grupo -> año -> valor -> celdas
CONTEO_DESPUES = defaultdict(lambda: defaultdict(Counter))
ORDEN_GRUPOS = []


def grupo_de(col: str) -> str:
    for patron, nombre in GRUPOS:
        if re.fullmatch(patron, col):
            return nombre
    return col


def anotar(seccion: str, grupo: str, detalle: str, anio: int, n) -> None:
    if int(n):
        REGISTRO[(seccion, grupo, detalle, anio)] += int(n)


def mascara(v: str) -> str:
    return "".join("9" if ch.isdigit() else "A" if ch.isalpha() else ch for ch in v)


def sin_tildes(v: str) -> str:
    v = unicodedata.normalize("NFKD", v)
    return "".join(ch for ch in v if not unicodedata.combining(ch))


def cargar_equivalencias() -> dict[str, dict[str, str]]:
    mapa = defaultdict(dict)
    with open(ARCHIVO_EQUIVALENCIAS, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            mapa[fila["columna"]][fila["valor_original"]] = fila["valor_homogenizado"]
    return mapa


def limpiar(s: pd.Series) -> pd.Series:
    """Regla 3: sin espacios sobrantes y en mayúsculas."""
    return s.str.strip().str.replace(r"\s+", " ", regex=True).str.upper()


def anotar_nulos(t: pd.Series, vacia: pd.Series, token: pd.Series, invalido: pd.Series,
                 grupo: str, anio: int) -> None:
    anotar("vacias", grupo, "", anio, vacia.sum())
    for valor, n in t[token].str.upper().value_counts().items():
        anotar("sin_dato", grupo, valor, anio, n)
    no_convertible = invalido & ~vacia & ~token
    for formato, n in t[no_convertible].map(mascara).value_counts().items():
        anotar("no_convertible", grupo, formato, anio, n)


def a_texto(s: pd.Series, col: str, grupo: str, anio: int, equivalencias: dict, contar: bool) -> pd.Series:
    t = limpiar(s)
    vacia = t == ""
    anotar("texto", grupo, "", anio, ((t != s) & ~vacia).sum())
    if contar:
        CONTEO_ANTES[grupo][anio].update(s[~vacia].value_counts().to_dict())
    mapa = equivalencias.get(col)
    if mapa:
        nuevo = t.map(mapa)
        cambia = nuevo.notna()
        for original, n in t[cambia].value_counts().items():
            anotar("equivalencia", col, f"{original}\x1f{mapa[original]}", anio, n)
        t = t.where(~cambia, nuevo)
    token = t.isin(NULOS | NULOS_POR_GRUPO.get(grupo, set()))
    anotar_nulos(t, vacia, token, pd.Series(False, index=t.index), grupo, anio)
    resultado = t.mask(vacia | token)
    if contar:
        CONTEO_DESPUES[grupo][anio].update(resultado.dropna().value_counts().to_dict())
    return resultado


def a_fecha(s: pd.Series, grupo: str, anio: int) -> pd.Series:
    """Regla 4: acepta AAAA-MM-DD y DD-MM-AAAA; lo demás queda como sin dato."""
    t = s.str.strip()
    vacia = t == ""
    token = t.str.upper().isin(NULOS)
    iso = t.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    dmy = t.str.fullmatch(r"\d{2}-\d{2}-\d{4}")
    f_iso = pd.to_datetime(t.where(iso), format="%Y-%m-%d", errors="coerce").astype("datetime64[ms]")
    f_dmy = pd.to_datetime(t.where(dmy), format="%d-%m-%Y", errors="coerce").astype("datetime64[ms]")
    fecha = f_iso.fillna(f_dmy)
    anotar("fecha", grupo, "AAAA-MM-DD", anio, (iso & fecha.notna()).sum())
    anotar("fecha", grupo, "DD-MM-AAAA", anio, (dmy & fecha.notna()).sum())
    anotar_nulos(t, vacia, token, fecha.isna(), grupo, anio)
    return fecha


def a_entero(s: pd.Series, grupo: str, anio: int, patron: str, tipo: str) -> pd.Series:
    t = s.str.strip()
    vacia = t == ""
    token = t.str.upper().isin(NULOS)
    valido = t.str.fullmatch(patron)
    anotar_nulos(t, vacia, token, ~valido, grupo, anio)
    return pd.to_numeric(t.where(valido), errors="coerce").astype(tipo)


def a_decimal(s: pd.Series, grupo: str, anio: int) -> pd.Series:
    """Regla 5: '0,5744' -> 0.5744 y ',3045' -> 0.3045."""
    t = s.str.strip()
    vacia = t == ""
    token = t.str.upper().isin(NULOS)
    u = t.str.replace(",", ".", regex=False)
    sin_cero = u.str.startswith(".")
    u = u.where(~sin_cero, "0" + u)
    valido = u.str.fullmatch(r"\d+(\.\d+)?")
    anotar("numero", grupo, "Coma decimal convertida a punto", anio, (t.str.contains(",", regex=False) & valido).sum())
    anotar("numero", grupo, "Cero inicial agregado (,3045 -> 0.3045)", anio, (sin_cero & valido).sum())
    anotar_nulos(t, vacia, token, ~valido, grupo, anio)
    return pd.to_numeric(u.where(valido), errors="coerce").astype("float64")


def tipo_arrow(col: str) -> pa.DataType:
    if col in COLS_FECHA:
        return pa.timestamp("ms")
    if col in COLS_ENTERO:
        return TIPO_ARROW[COLS_ENTERO[col][1]]
    if col in COLS_DECIMAL:
        return pa.float64()
    return {"ANIO_ARCHIVO": pa.int16(), "FILA_ORIGEN": pa.int32()}.get(col, pa.string())


def alertas_fechas(df: pd.DataFrame, anio: int) -> dict[str, int]:
    """Coherencia entre fechas: se informa, no se corrige (corresponde a la actividad 2.2)."""
    ing, alta, nac = df["FECHA_INGRESO"], df["FECHAALTA"], df["FECHA_NACIMIENTO"]
    return {
        "Sin fecha de ingreso": int(ing.isna().sum()),
        "Sin fecha de alta": int(alta.isna().sum()),
        "Sin fecha de nacimiento": int(nac.isna().sum()),
        "Alta anterior al ingreso": int((alta < ing).sum()),
        "Nacimiento posterior al ingreso": int((nac > ing).sum()),
        "Edad al ingreso mayor de 110 años": int(((ing - nac).dt.days > 110 * 365.25).sum()),
        "Alta fuera del año del archivo": int((alta.notna() & (alta.dt.year != anio)).sum()),
        "Ingreso anterior al año previo al archivo": int((ing.dt.year < anio - 1).sum()),
    }


def homogenizar(anio: int, equivalencias: dict) -> dict:
    inicio = time.time()
    crudo = pq.read_table(DIR_INTERIM / f"crudo_{anio}.parquet").to_pandas()
    n = len(crudo)
    salida = {}
    for col in [c for c in crudo.columns if c not in TRAZABILIDAD]:
        s = crudo.pop(col)
        nombre = "ID_PACIENTE" if col in COLS_ID else col          # regla 1
        grupo = grupo_de(nombre)
        if grupo not in ORDEN_GRUPOS:
            ORDEN_GRUPOS.append(grupo)
        if nombre in COLS_ELIMINAR:                                   # regla 8
            anotar("eliminada", grupo, "", anio, (s.str.strip() != "").sum())
        elif nombre in COLS_FECHA:
            salida[nombre] = a_fecha(s, grupo, anio)
        elif nombre in COLS_ENTERO:
            salida[nombre] = a_entero(s, grupo, anio, *COLS_ENTERO[nombre])
        elif nombre in COLS_DECIMAL:
            salida[nombre] = a_decimal(s, grupo, anio)
        elif nombre in COLS_CODIGO:                                   # regla 6
            salida[nombre] = a_texto(s, nombre, grupo, anio, {}, contar=False)
        else:
            salida[nombre] = a_texto(s, nombre, grupo, anio, equivalencias, contar=True)
        if nombre == "ID_PACIENTE":
            salida["BLOQUE_ID"] = pd.Series("A" if anio <= 2020 else "B", index=s.index, dtype="str")
        elif nombre == "IR_29301_COD_GRD":
            salida[nombre] = salida[nombre].str.zfill(6)
            salida["CDM"] = salida[nombre].str[:2]
    for col in TRAZABILIDAD:
        salida[col] = crudo[col]
    df = pd.DataFrame(salida)
    del crudo, salida

    # Verificaciones antes de guardar
    textos = [c for c in df.columns if tipo_arrow(c) == pa.string()]
    forma_rut = sum(int(df[c].str.fullmatch(FORMA_RUT).sum()) for c in textos)
    filas_ok = bool((df["FILA_ORIGEN"].to_numpy() == pd.RangeIndex(2, n + 2).to_numpy()).all())
    alertas = alertas_fechas(df, anio)
    uso_max = df["USOSPABELLON"].max()

    esquema = pa.schema([(c, tipo_arrow(c)) for c in df.columns])
    destino = DIR_INTERIM / f"homog_{anio}.parquet"
    temporal = destino.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=esquema, preserve_index=False), temporal, compression="zstd")
    temporal.replace(destino)
    filas_parquet = pq.ParquetFile(destino).metadata.num_rows
    print(f"  {anio}: {filas_parquet:,} filas, {len(df.columns)} columnas, {time.time() - inicio:.0f} s", flush=True)
    return {
        "filas_crudo": n, "filas_homog": filas_parquet, "columnas": len(df.columns),
        "mb": destino.stat().st_size / 1e6, "segundos": round(time.time() - inicio),
        "filas_ok": filas_ok and filas_parquet == n, "forma_rut": forma_rut,
        "uso_max": None if pd.isna(uso_max) else int(uso_max), "alertas": alertas, "esquema": esquema,
    }


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def por_anio(d: dict) -> list[str]:
    return [fmt(d[a]) if d.get(a) else "—" for a in ANIOS] + [fmt(sum(d.values()))]


def tabla(encabezados: list[str], filas: list[list[str]]) -> str:
    if not filas:
        return "Sin casos."
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join(lineas)


def seccion(nombre: str) -> dict:
    """(grupo, detalle) -> {año: celdas}, en el orden de las columnas."""
    out = defaultdict(dict)
    for (sec, grupo, detalle, anio), n in REGISTRO.items():
        if sec == nombre:
            out[(grupo, detalle)][anio] = n
    orden = {g: i for i, g in enumerate(ORDEN_GRUPOS)}
    return dict(sorted(out.items(), key=lambda kv: (orden.get(kv[0][0], 999), -sum(kv[1].values()))))


def escribir_reporte(resultados: dict, equivalencias: dict) -> None:
    anios_txt = [str(a) for a in ANIOS]
    esquemas_iguales = all(r["esquema"].equals(resultados[ANIOS[0]]["esquema"]) for r in resultados.values())
    partes = [
        "# Homogenización de los seis años (Paso 3)",
        "Generado por `2.1_integracion_homogenizacion/scripts/05_homogenizar.py` desde `data/interim/crudo_<año>.parquet` hacia "
        "`data/interim/homog_<año>.parquet`. No se elimina ni agrega ninguna fila. Las cifras son "
        "celdas (un registro tiene varias celdas en los grupos de columnas repetidas).",
        "## 1. Resultado",
        tabla(["Año", "Registros crudo", "Registros homogenizado", "Columnas", "MB", "Segundos", "Verificación"],
              [[str(a), fmt(r["filas_crudo"]), fmt(r["filas_homog"]), str(r["columnas"]), f"{r['mb']:.0f}",
                str(r["segundos"]), "OK" if r["filas_ok"] else "REVISAR"] for a, r in resultados.items()]),
        f"**Total:** {fmt(sum(r['filas_crudo'] for r in resultados.values()))} registros crudos y "
        f"{fmt(sum(r['filas_homog'] for r in resultados.values()))} homogenizados. "
        f"Esquema idéntico en los seis años: **{'sí' if esquemas_iguales else 'NO'}**. "
        "Columnas: las 129 originales, menos `FECHAPROCEDIMIENTO1`, más `BLOQUE_ID`, `CDM` y las 3 de trazabilidad.",
    ]

    # 2. Sin dato
    sd = seccion("sin_dato")
    por_valor = defaultdict(lambda: defaultdict(int))
    por_grupo = defaultdict(lambda: defaultdict(int))
    for (grupo, valor), d in sd.items():
        for a, n in d.items():
            por_valor[valor][a] += n
        por_grupo[grupo][valor] += sum(d.values())
    partes += [
        "## 2. \"Sin dato\" unificado",
        "Valores que representaban ausencia de información y pasaron a nulo (además de las celdas vacías).",
        tabla(["Valor original", *anios_txt, "Total"],
              [[f"`{v}`", *por_anio(d)] for v, d in sorted(por_valor.items(), key=lambda kv: -sum(kv[1].values()))]),
        "Detalle por columna (total de los seis años):",
        tabla(["Columna", "Valores convertidos a nulo"],
              [[g, "; ".join(f"`{v}` {fmt(n)}" for v, n in sorted(d.items(), key=lambda kv: -kv[1]))]
               for g, d in por_grupo.items()]),
    ]

    # 3. Textos
    partes += [
        "## 3. Textos: espacios sobrantes y mayúsculas",
        "Celdas cuyo texto cambió al quitar espacios sobrantes o pasar a mayúsculas.",
        tabla(["Columna", *anios_txt, "Total"], [[g, *por_anio(d)] for (g, _), d in seccion("texto").items()]),
    ]

    # 4. Equivalencias
    eq = seccion("equivalencia")
    partes += [
        "## 4. Equivalencias aplicadas",
        "Reglas de `2.1_integracion_homogenizacion/reglas/equivalencias_categorias.csv`.",
        tabla(["Columna", "Valor original", "Valor homogenizado", *anios_txt, "Total"],
              [[g, f"`{det.split(chr(31))[0]}`", f"`{det.split(chr(31))[1]}`", *por_anio(d)] for (g, det), d in eq.items()]),
    ]
    for col in ("ESPECIALIDAD_MEDICA", "ESPECIALIDADINTERVENCION"):
        destinos = sorted(set(equivalencias.get(col, {}).values()))
        conteo = CONTEO_DESPUES[col]
        partes += [
            f"### Continuidad en `{col}` después de homogenizar",
            "Celdas por año del valor homogenizado. 2019 incluye tipos de actividad que no existen "
            "desde 2020 (bitácora H09), por lo que su volumen puede ser mayor.",
            tabla(["Valor homogenizado", *anios_txt],
                  [[f"`{v}`", *[fmt(conteo[a][v]) if conteo[a][v] else "—" for a in ANIOS]] for v in destinos]),
        ]
        solo_un_anio = [(v, a, conteo[a][v]) for v in set().union(*[set(c) for c in conteo.values()])
                        for a in ANIOS if conteo[a][v] and sum(1 for b in ANIOS if conteo[b][v]) == 1 and a == 2019]
        partes += [
            f"Nombres de `{col}` que siguen existiendo solo en 2019 (sin equivalente claro; no se modificaron):",
            tabla(["Valor", "Celdas en 2019"], [[f"`{v}`", fmt(n)] for v, _, n in sorted(solo_un_anio, key=lambda x: -x[2])]),
        ]

    # 5 y 6. Fechas y números
    partes += [
        "## 5. Fechas convertidas",
        tabla(["Columna", "Formato de origen", *anios_txt, "Total"],
              [[g, det, *por_anio(d)] for (g, det), d in seccion("fecha").items()]),
        "## 6. Números",
        tabla(["Columna", "Cambio", *anios_txt, "Total"],
              [[g, det, *por_anio(d)] for (g, det), d in seccion("numero").items()]),
    ]

    # 7. No convertibles
    partes += [
        "## 7. Valores que no se pudieron convertir",
        "Quedaron como \"sin dato\". Se muestra solo su formato (9 = dígito, A = letra), no el valor.",
        tabla(["Columna", "Formato del valor", *anios_txt, "Total"],
              [[g, f"`{det}`", *por_anio(d)] for (g, det), d in seccion("no_convertible").items()]),
    ]

    # 8. Eliminada
    partes += [
        "## 8. Columna eliminada",
        tabla(["Columna", *anios_txt, "Total de celdas no vacías descartadas"],
              [[g, *por_anio(d)] for (g, _), d in seccion("eliminada").items()]),
    ]

    # 9. Alertas
    nombres_alerta = list(next(iter(resultados.values()))["alertas"])
    partes += [
        "## 9. Alertas de coherencia de fechas",
        "Se informan para la actividad 2.2; en este paso no se corrigen ni se excluyen registros.",
        tabla(["Alerta", *anios_txt, "Total"],
              [[nombre, *por_anio({a: r["alertas"][nombre] for a, r in resultados.items()})] for nombre in nombres_alerta]),
    ]

    # 10. Verificaciones
    variantes = []
    filas_cat = []
    for g in ORDEN_GRUPOS:
        if g not in CONTEO_DESPUES:
            continue
        antes = set().union(*[set(c) for c in CONTEO_ANTES[g].values()])
        despues = set().union(*[set(c) for c in CONTEO_DESPUES[g].values()])
        filas_cat.append([g, fmt(len(antes)), fmt(len(despues))])
        claves = defaultdict(set)
        for v in despues:
            claves[sin_tildes(v)].add(v)
        variantes += [f"`{g}`: " + " · ".join(f"`{v}`" for v in sorted(s)) for s in claves.values() if len(s) > 1]
    partes += [
        "## 10. Verificaciones",
        "\n".join([
            f"- Registros conservados y en el mismo orden en los seis años: **{'sí' if all(r['filas_ok'] for r in resultados.values()) else 'NO'}**.",
            f"- Celdas con forma de RUT en la base homogenizada: **{sum(r['forma_rut'] for r in resultados.values())}**.",
            "- Valor máximo de `USOSPABELLON` por año: "
            + ", ".join(f"{a}: {r['uso_max']}" for a, r in resultados.items()) + ".",
            f"- Variantes de un mismo valor que difieren solo en tildes: **{len(variantes)}**.",
        ] + [f"  - {v}" for v in variantes]),
        "Valores distintos por columna de texto, antes y después (seis años):",
        tabla(["Columna", "Antes", "Después"], filas_cat),
    ]

    salida = DIR_REPORTS / "05_homogenizacion.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    equivalencias = cargar_equivalencias()
    resultados = {}
    for anio in ANIOS:
        print(f"Homogenizando {anio}...", flush=True)
        resultados[anio] = homogenizar(anio, equivalencias)
    escribir_reporte(resultados, equivalencias)


if __name__ == "__main__":
    main()
