"""Paso 5: diccionario de datos de la tabla integrada.

Combina las descripciones de reglas/descripciones_columnas.csv con estadísticas calculadas
desde data/processed/grd_2019_2024.parquet (tipo, porcentaje con dato y valores) y escribe
docs/diccionario_datos.md. Las columnas repetidas (DIAGNOSTICO2 a DIAGNOSTICO35, etc.) se
describen como un solo grupo.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.1_integracion_homogenizacion\\scripts\\07_diccionario_datos.py
"""

import csv
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
RUTA = RAIZ / "data" / "processed" / "grd_2019_2024.parquet"
DESCRIPCIONES = ACTIVIDAD / "reglas" / "descripciones_columnas.csv"
SALIDA = RAIZ / "docs" / "diccionario_datos.md"
ANIO_BASE, N_ANIOS = 2019, 6
MAX_LISTA = 12  # hasta esta cantidad de valores distintos se listan todos


def expandir(spec: str) -> list[str]:
    """'DIAGNOSTICO{2-35}' -> ['DIAGNOSTICO2', ..., 'DIAGNOSTICO35']."""
    m = re.fullmatch(r"(.*)\{(\d+)-(\d+)\}(.*)", spec)
    return [spec] if not m else [f"{m[1]}{i}{m[4]}" for i in range(int(m[2]), int(m[3]) + 1)]


def tipo_es(t: pa.DataType) -> str:
    if pa.types.is_boolean(t):
        return "Verdadero/falso"
    if pa.types.is_integer(t):
        return "Entero"
    if pa.types.is_floating(t):
        return "Decimal"
    if pa.types.is_timestamp(t):
        return "Fecha"
    return "Texto"


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def num(v) -> str:
    return fmt(v) if float(v).is_integer() else f"{v:g}".replace(".", ",")


def pct(p: float) -> str:
    if p == 100 or p == 0:
        return f"{p:.0f}"
    if p >= 99.995:
        return ">99,99"
    return "<0,01" if p < 0.005 else f"{p:.2f}".replace(".", ",")


def estadisticas(pf: pq.ParquetFile, cols: list[str], modo: str, anio_idx: np.ndarray) -> tuple:
    validos = np.zeros(N_ANIOS)
    conteo, minimo, maximo = Counter(), None, None
    for c in cols:
        col = pf.read(columns=[c]).column(0)
        validos += np.bincount(anio_idx[pc.is_valid(col).to_numpy()], minlength=N_ANIOS)
        if modo == "categorias":
            vc = pc.value_counts(col.combine_chunks())
            for v, n in zip(vc.field("values").to_pylist(), vc.field("counts").to_pylist()):
                if v is not None:
                    conteo[v] += n
        elif modo == "rango":
            mm = pc.min_max(col)
            mn, mx = mm["min"].as_py(), mm["max"].as_py()
            if mn is not None:
                minimo = mn if minimo is None else min(minimo, mn)
                maximo = mx if maximo is None else max(maximo, mx)
    return validos, conteo, minimo, maximo


def texto_valores(tipo: str, modo: str, conteo: Counter, minimo, maximo) -> str:
    if modo == "ninguno":
        return "Identificador"
    if modo == "rango":
        if minimo is None:
            return "—"
        if tipo == "Fecha":
            return f"Del {minimo:%d-%m-%Y} al {maximo:%d-%m-%Y}"
        return f"De {num(minimo)} a {num(maximo)}"
    if tipo == "Verdadero/falso":
        return f"Verdadero en {fmt(conteo.get(True, 0))} registros"
    total = sum(conteo.values())
    if not total:
        return "—"
    if len(conteo) <= MAX_LISTA:
        orden = sorted(conteo.items()) if tipo == "Entero" else conteo.most_common()
        return " · ".join(f"`{v}` {pct(100 * n / total)} %" for v, n in orden)
    return f"{fmt(len(conteo))} valores distintos. Más frecuentes: " + ", ".join(f"`{v}`" for v, _ in conteo.most_common(5))


def main() -> None:
    pf = pq.ParquetFile(RUTA)
    esquema = pf.schema_arrow
    anio = pf.read(columns=["ANIO_ARCHIVO"]).column(0).to_numpy()
    anio_idx = (anio - ANIO_BASE).astype("int64")
    filas_por_anio = np.bincount(anio_idx, minlength=N_ANIOS)
    total = int(filas_por_anio.sum())

    with open(DESCRIPCIONES, encoding="utf-8-sig", newline="") as f:
        entradas = list(csv.DictReader(f, delimiter=";"))
    descritas = [c for e in entradas for c in expandir(e["columnas"])]
    if sorted(descritas) != sorted(esquema.names):
        faltan = set(esquema.names) - set(descritas)
        sobran = set(descritas) - set(esquema.names)
        raise ValueError(f"Las descripciones no coinciden con las columnas. Faltan: {faltan}. Sobran: {sobran}")

    secciones: dict[str, list[str]] = {}
    for e in entradas:
        cols = expandir(e["columnas"])
        print(f"  {e['columnas']}", flush=True)
        tipo = tipo_es(esquema.field(cols[0]).type)
        validos, conteo, minimo, maximo = estadisticas(pf, cols, e["valores"], anio_idx)
        por_anio = 100 * validos / (len(cols) * filas_por_anio)
        general = 100 * validos.sum() / (len(cols) * total)
        con_dato = pct(general)
        if por_anio.max() - por_anio.min() >= 0.05:
            con_dato += f" ({pct(por_anio.min())} a {pct(por_anio.max())} según el año)"
        nombre = f"`{cols[0]}`" if len(cols) == 1 else f"`{cols[0]}` a `{cols[-1]}`"
        fila = [nombre, tipo, e["descripcion"], texto_valores(tipo, e["valores"], conteo, minimo, maximo),
                con_dato, e["origen"]]
        secciones.setdefault(e["seccion"], []).append("| " + " | ".join(fila) + " |")

    partes = [
        "# Diccionario de datos",
        f"Tabla integrada: `data/processed/{RUTA.name}`. Tiene {fmt(total)} registros (un registro por egreso "
        f"hospitalario, de {ANIO_BASE} a {ANIO_BASE + N_ANIOS - 1}) y {len(esquema.names)} columnas. "
        "Generado por `2.1_integracion_homogenizacion/scripts/07_diccionario_datos.py` con las descripciones de `2.1_integracion_homogenizacion/reglas/descripciones_columnas.csv`.",
        "## Cómo leer este diccionario",
        "\n".join([
            "- **Sin dato:** la ausencia de información se guarda como valor nulo en todas las columnas.",
            "- **Valores:** en las columnas con pocas categorías se listan todas, con su porcentaje sobre los "
            "registros con dato; en las demás, las más frecuentes o el rango.",
            "- **% con dato:** porcentaje de registros con valor (de celdas, en las columnas repetidas). Entre "
            "paréntesis, el mínimo y el máximo por año cuando varía.",
            "- **Origen:** *Original* (viene de los archivos del DEIS), *Renombrada*, *Creada* (agregada en el "
            "procesamiento) o *Trazabilidad* (permite volver al archivo original).",
            "- Las descripciones se elaboraron a partir del informe, de las tablas auxiliares del DEIS y del contenido "
            "de cada columna; deben contrastarse con la documentación oficial de la base GRD.",
            "- Las reglas aplicadas a cada columna están en `2.1_integracion_homogenizacion/reportes/05_homogenizacion.md` y las decisiones, en "
            "`docs/bitacora.md`.",
        ]),
    ]
    for seccion, filas in secciones.items():
        partes += [f"## {seccion}",
                   "\n".join(["| Columna | Tipo | Descripción | Valores | % con dato | Origen |", "|---|---|---|---|---|---|", *filas])]
    SALIDA.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Diccionario guardado en {SALIDA}")


if __name__ == "__main__":
    main()
