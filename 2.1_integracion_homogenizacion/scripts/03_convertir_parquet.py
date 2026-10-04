"""Paso 2: conversión de los seis archivos GRD de texto a Parquet, sin transformar.

Cada archivo se lee con su codificación, en bloques, con todas las columnas como
texto tal como vienen. Se agregan tres columnas de trazabilidad (ANIO_ARCHIVO,
ARCHIVO_ORIGEN, FILA_ORIGEN) y se verifica que no se pierda ningún registro.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.1_integracion_homogenizacion\\scripts\\03_convertir_parquet.py
"""

import csv
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_TXT = RAIZ.parent / "Datos" / "txt"
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_REPORTS = ACTIVIDAD / "reportes"

ARCHIVOS = {
    2019: ("GRD_PUBLICO_2019.txt", "utf-8"),
    2020: ("GRD_PUBLICO_2020.txt", "utf-8"),
    2021: ("GRD_PUBLICO_2021.txt", "utf-8-sig"),
    2022: ("GRD_PUBLICO_EXTERNO_2022.txt", "utf-16"),
    2023: ("GRD_PUBLICO_2023.txt", "utf-16"),
    2024: ("GRD_PUBLICO_2024.txt", "cp1252"),
}

N_COLUMNAS = 129
TAM_BLOQUE = 200_000
def inspeccionar_txt(ruta: Path, encoding: str) -> tuple[int, dict[int, int]]:
    """Cuenta los registros (líneas menos el encabezado) y devuelve las líneas cuyo
    número de campos difiere de N_COLUMNAS, como {número de línea: campos}."""
    anomalas, n_lineas = {}, 0
    with open(ruta, encoding=encoding, newline="\n") as f:
        for n_lineas, linea in enumerate(f, start=1):
            campos = linea.count("|") + 1
            if campos != N_COLUMNAS:
                anomalas[n_lineas] = campos
    return n_lineas - 1, anomalas


def unir_campos_sobrantes(campos: list[str]) -> list[str]:
    """Línea con un "|" de más dentro del último valor (HOSPPROCEDENCIA): se vuelve a
    unir el sobrante con "|" para conservar el texto original."""
    return campos[: N_COLUMNAS - 1] + ["|".join(campos[N_COLUMNAS - 1:])]


def convertir(anio: int) -> dict:
    nombre, encoding = ARCHIVOS[anio]
    origen = DIR_TXT / nombre
    destino = DIR_INTERIM / f"crudo_{anio}.parquet"
    temporal = destino.with_suffix(".parquet.tmp")
    inicio = time.time()

    filas_txt, anomalas = inspeccionar_txt(origen, encoding)
    if 1 in anomalas:
        raise ValueError(f"{nombre}: el encabezado tiene {anomalas[1]} columnas")
    if any(campos < N_COLUMNAS for campos in anomalas.values()):
        raise ValueError(f"{nombre}: hay líneas con menos campos de lo esperado: {anomalas}")

    opciones = dict(sep="|", encoding=encoding, dtype=str, keep_default_na=False,
                    quoting=csv.QUOTE_NONE, chunksize=TAM_BLOQUE)
    if anomalas:
        # El lector en Python es más lento, pero permite reparar las líneas con campos de más.
        opciones.update(engine="python", on_bad_lines=unir_campos_sobrantes)
    lector = pd.read_csv(origen, **opciones)

    escritor, filas, celdas_faltantes, fila_inicio = None, 0, 0, 2  # la línea 1 es el encabezado
    try:
        for bloque in lector:
            if bloque.shape[1] != N_COLUMNAS:
                raise ValueError(f"{nombre}: se esperaban {N_COLUMNAS} columnas y hay {bloque.shape[1]}")
            # Con keep_default_na=False solo quedan nulos si una línea trae menos campos.
            celdas_faltantes += int(bloque.isna().sum().sum())
            n = len(bloque)
            bloque["ANIO_ARCHIVO"] = pd.Series([anio] * n, index=bloque.index, dtype="int16")
            bloque["ARCHIVO_ORIGEN"] = nombre
            bloque["FILA_ORIGEN"] = pd.RangeIndex(fila_inicio, fila_inicio + n).astype("int32")
            tabla = pa.Table.from_pandas(bloque, preserve_index=False)
            if escritor is None:
                escritor = pq.ParquetWriter(temporal, tabla.schema, compression="zstd")
            escritor.write_table(tabla)
            filas += n
            fila_inicio += n
            print(f"  {anio}: {filas:,} filas", end="\r", flush=True)
    finally:
        if escritor is not None:
            escritor.close()
    temporal.replace(destino)

    # Las líneas reparadas deben aparecer en el Parquet con un "|" en HOSPPROCEDENCIA.
    ultima = pq.read_table(destino, columns=["HOSPPROCEDENCIA", "FILA_ORIGEN"]).to_pandas()
    reparadas = sorted(ultima.loc[ultima["HOSPPROCEDENCIA"].str.contains("|", regex=False),
                                  "FILA_ORIGEN"].tolist())

    filas_parquet = pq.ParquetFile(destino).metadata.num_rows
    ok = (filas_txt == filas == filas_parquet and celdas_faltantes == 0
          and reparadas == sorted(anomalas))
    print(f"  {anio}: {filas_parquet:,} filas en Parquet, {filas_txt:,} en txt -> {'OK' if ok else 'REVISAR'}")
    return {
        "archivo": nombre,
        "codificación": encoding,
        "registros txt": f"{filas_txt:,}",
        "registros Parquet": f"{filas_parquet:,}",
        "celdas faltantes": celdas_faltantes,
        "líneas con '|' extra (reparadas)": ", ".join(map(str, reparadas)) or "ninguna",
        "verificación": "OK" if ok else "REVISAR",
        "MB txt": f"{origen.stat().st_size / 1e6:,.0f}",
        "MB Parquet": f"{destino.stat().st_size / 1e6:,.0f}",
        "segundos": round(time.time() - inicio),
    }


def main() -> None:
    DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    resultados = {}
    for anio in ARCHIVOS:
        print(f"Convirtiendo {anio}...", flush=True)
        resultados[anio] = convertir(anio)

    df = pd.DataFrame(resultados).T
    df.index.name = "año"
    cols = [str(c) for c in df.columns]
    lineas = ["| año | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    lineas += [f"| {a} | " + " | ".join(str(v) for v in fila) + " |" for a, fila in df.iterrows()]
    total_txt = sum(int(r["registros txt"].replace(",", "")) for r in resultados.values())
    total_pq = sum(int(r["registros Parquet"].replace(",", "")) for r in resultados.values())
    informe = "\n\n".join([
        "# Conversión de los archivos GRD a Parquet (Paso 2)",
        "Generado por `2.1_integracion_homogenizacion/scripts/03_convertir_parquet.py`. Todas las columnas se guardan como texto, "
        "sin transformar. Se agregan `ANIO_ARCHIVO`, `ARCHIVO_ORIGEN` y `FILA_ORIGEN` "
        "(número de línea en el txt original; la línea 1 es el encabezado). "
        "'Celdas faltantes' cuenta campos ausentes por líneas con menos columnas de lo esperado. "
        "Las líneas con un campo de más (un '|' dentro de `HOSPPROCEDENCIA`) se reparan uniendo "
        "ese campo al valor de `HOSPPROCEDENCIA` con '|', lo que reproduce el texto original.",
        "\n".join(lineas),
        f"**Total:** {total_txt:,} registros en los txt y {total_pq:,} en Parquet.",
    ]) + "\n"
    salida = DIR_REPORTS / "03_conversion_parquet.md"
    salida.write_text(informe, encoding="utf-8")
    print(informe)
    print(f"Reporte guardado en {salida}")


if __name__ == "__main__":
    main()
