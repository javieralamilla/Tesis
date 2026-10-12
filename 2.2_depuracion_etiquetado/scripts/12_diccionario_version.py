"""Diccionario del conjunto analítico y registro de su versión (actividad 2.2, script 12).

El conjunto analítico es data/processed/grd_etiquetado.parquet: la tabla que usan la partición y las
etapas siguientes. Este script deja dos documentos en docs/:

  - diccionario_conjunto_analitico.md: una fila por columna o grupo de columnas, con su descripción y
    estadísticas calculadas (tipo, valores y porcentaje con dato). Las descripciones de las columnas de
    la tabla integrada son las de la actividad 2.1; las de las columnas que agregan los scripts 08 y 09
    están en reglas/descripciones_columnas.csv, y las de los criterios salen de criterios_exclusion.csv.
  - version_conjunto_analitico.csv: una fila por versión registrada, con el hash SHA-256 del archivo y
    de lo que lo produce (tabla integrada, tablas de reglas y scripts). Si el archivo no cambió desde la
    última versión registrada, no se agrega ninguna fila.

Usa las funciones del script 07, que genera el diccionario de la tabla integrada.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\scripts\\12_diccionario_version.py
"""

import csv
import hashlib
import importlib.util
import platform
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
INTEGRACION = RAIZ / "2.1_integracion_homogenizacion"
CONJUNTO = RAIZ / "data" / "processed" / "grd_etiquetado.parquet"
TABLA_INTEGRADA = RAIZ / "data" / "processed" / "grd_2019_2024.parquet"
DESCRIPCIONES = [INTEGRACION / "reglas" / "descripciones_columnas.csv", ACTIVIDAD / "reglas" / "descripciones_columnas.csv"]
ARCHIVO_CRITERIOS = ACTIVIDAD / "reglas" / "criterios_exclusion.csv"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
DICCIONARIO = RAIZ / "docs" / "diccionario_conjunto_analitico.md"
REGISTRO = RAIZ / "docs" / "version_conjunto_analitico.csv"
PLANTILLA_CRITERIOS = "EXC_*"                    # fila de descripciones que se reemplaza por una por criterio
# Lo que produce el conjunto: si alguno cambia, el conjunto puede cambiar.
ORIGENES = {"sha256_tabla_integrada": TABLA_INTEGRADA, "sha256_criterios": ARCHIVO_CRITERIOS, "sha256_parametros": ARCHIVO_PARAMETROS,
            "sha256_script_08": ACTIVIDAD / "scripts" / "08_depurar.py", "sha256_script_09": ACTIVIDAD / "scripts" / "09_etiquetar.py"}
CAMPOS = ["version", "fecha", "archivo", "registros", "columnas", "casos_de_estudio", "sha256", *ORIGENES, "python", "pandas", "pyarrow"]


def cargar_script(ruta: Path):
    """Importa otro script por su ruta. Su nombre empieza con un número, así que no sirve `import`."""
    spec = importlib.util.spec_from_file_location("script_" + ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cargar_descripciones(columnas: list[str], m07) -> list[dict]:
    """Una entrada por columna o grupo de columnas del conjunto, en el orden de las tablas de descripciones."""
    entradas = []
    for ruta in DESCRIPCIONES:
        for e in leer_csv(ruta):
            if e["columnas"] == PLANTILLA_CRITERIOS:
                entradas += [{**e, "columnas": c["columna"],
                              "descripcion": e["descripcion"].format(codigo=c["codigo"], criterio=c["criterio"],
                                                                     estado="activo" if c["activo"].strip().upper() == "SI" else "desactivado")}
                             for c in leer_csv(ARCHIVO_CRITERIOS)]
            elif set(m07.expandir(e["columnas"])) & set(columnas):       # las columnas DUP_* ya no están en el conjunto
                entradas.append(e)
    descritas = [c for e in entradas for c in m07.expandir(e["columnas"])]
    if sorted(descritas) != sorted(columnas):
        raise SystemExit(f"Las descripciones no coinciden con las columnas. Faltan: {sorted(set(columnas) - set(descritas))}. "
                         f"Sobran: {sorted(set(descritas) - set(columnas))}.")
    return entradas


def registrar_version(ficha: dict) -> tuple[dict, bool]:
    """Devuelve la versión que corresponde al archivo actual y si es nueva. Solo agrega una fila si el archivo cambió."""
    filas = leer_csv(REGISTRO) if REGISTRO.exists() else []
    if filas and filas[-1]["sha256"] == ficha["sha256"]:
        return filas[-1], False
    nueva = {"version": str(int(filas[-1]["version"]) + 1 if filas else 1), "fecha": date.today().isoformat(), **ficha}
    with open(REGISTRO, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";", lineterminator="\r\n")
        escritor.writeheader()
        escritor.writerows([*filas, nueva])
    return nueva, True


def main() -> None:
    m07 = cargar_script(INTEGRACION / "scripts" / "07_diccionario_datos.py")
    pf = pq.ParquetFile(CONJUNTO)
    esquema = pf.schema_arrow
    anio_idx = (pf.read(columns=["ANIO_ARCHIVO"]).column(0).to_numpy() - m07.ANIO_BASE).astype("int64")
    filas_por_anio = np.bincount(anio_idx, minlength=m07.N_ANIOS)
    total = int(filas_por_anio.sum())
    casos = pc.sum(pf.read(columns=["ES_CASO_ESTUDIO"]).column(0)).as_py()

    print("Calculando los hash...", flush=True)
    ficha = {"archivo": f"data/processed/{CONJUNTO.name}", "registros": str(total), "columnas": str(len(esquema.names)),
             "casos_de_estudio": str(casos), "sha256": sha256(CONJUNTO), **{k: sha256(ruta) for k, ruta in ORIGENES.items()},
             "python": platform.python_version(), "pandas": pd.__version__, "pyarrow": pa.__version__}
    version, es_nueva = registrar_version(ficha)
    print(f"Versión {version['version']} ({'nueva' if es_nueva else 'ya registrada'}): {version['sha256']}", flush=True)

    entradas = cargar_descripciones(esquema.names, m07)
    secciones: dict[str, list[str]] = {}
    for e in entradas:
        cols = m07.expandir(e["columnas"])
        print(f"  {e['columnas']}", flush=True)
        tipo = m07.tipo_es(esquema.field(cols[0]).type)
        validos, conteo, minimo, maximo = m07.estadisticas(pf, cols, e["valores"], anio_idx)
        por_anio = 100 * validos / (len(cols) * filas_por_anio)
        con_dato = m07.pct(100 * validos.sum() / (len(cols) * total))
        if por_anio.max() - por_anio.min() >= 0.05:
            con_dato += f" ({m07.pct(por_anio.min())} a {m07.pct(por_anio.max())} según el año)"
        nombre = f"`{cols[0]}`" if len(cols) == 1 else f"`{cols[0]}` a `{cols[-1]}`"
        fila = [nombre, tipo, e["descripcion"], m07.texto_valores(tipo, e["valores"], conteo, minimo, maximo), con_dato, e["origen"]]
        secciones.setdefault(e["seccion"], []).append("| " + " | ".join(fila) + " |")

    ruta = ACTIVIDAD.name
    partes = [
        "# Diccionario del conjunto analítico",
        f"Conjunto analítico: `{ficha['archivo']}`. Es la tabla que usan la partición y las etapas siguientes. Tiene "
        f"{m07.fmt(total)} registros (un registro por egreso hospitalario, de {m07.ANIO_BASE} a {m07.ANIO_BASE + m07.N_ANIOS - 1}) y "
        f"{len(esquema.names)} columnas; {m07.fmt(casos)} registros son caso de estudio (`ES_CASO_ESTUDIO`). Generado por "
        f"`{ruta}/scripts/12_diccionario_version.py`.",

        "## Versión del conjunto",
        "\n".join([
            "| Dato | Valor |", "|---|---|",
            f"| Versión | {version['version']} |",
            f"| Fecha de registro | {version['fecha']} |",
            f"| Registros, columnas y casos de estudio | {m07.fmt(version['registros'])}, {version['columnas']} y {m07.fmt(version['casos_de_estudio'])} |",
            f"| SHA-256 del archivo | `{version['sha256']}` |",
            f"| SHA-256 de la tabla integrada (`{TABLA_INTEGRADA.name}`) | `{version['sha256_tabla_integrada']}` |",
            f"| SHA-256 de `{ARCHIVO_CRITERIOS.name}` | `{version['sha256_criterios']}` |",
            f"| SHA-256 de `{ARCHIVO_PARAMETROS.name}` | `{version['sha256_parametros']}` |",
            f"| SHA-256 de `08_depurar.py` | `{version['sha256_script_08']}` |",
            f"| SHA-256 de `09_etiquetar.py` | `{version['sha256_script_09']}` |",
            f"| Bibliotecas | Python {version['python']}, pandas {version['pandas']}, pyarrow {version['pyarrow']} |",
        ]),
        f"El historial de versiones está en `docs/{REGISTRO.name}`. El hash identifica el archivo exacto: la partición "
        "(actividad 2.3) debe comprobar que el archivo que lee es el de la última versión registrada. Si se vuelven a "
        "ejecutar los scripts 08 o 09 y el archivo cambia, hay que ejecutar de nuevo este script para registrar la nueva versión. "
        "Con otras versiones de las bibliotecas el archivo puede tener otro hash aunque su contenido sea el mismo.",

        "## Cómo leer este diccionario",
        "\n".join([
            "- **Secciones 1 a 6:** columnas de la tabla integrada (`docs/diccionario_datos.md`), sin `DUP_EXACTO` ni `DUP_CLAVE`, "
            "porque el script 08 elimina los duplicados. **Secciones 7 a 9:** columnas que agregan los scripts 08 y 09.",
            "- **Sin dato:** la ausencia de información se guarda como valor nulo en todas las columnas.",
            "- **Valores:** en las columnas con pocas categorías se listan todas, con su porcentaje sobre los registros con dato; "
            "en las demás, las más frecuentes o el rango.",
            "- **% con dato:** porcentaje de registros con valor (de celdas, en las columnas repetidas). Entre paréntesis, el "
            "mínimo y el máximo por año cuando varía. Las variables objetivo solo tienen dato en los casos de estudio.",
            "- **Origen:** *Original* (viene de los archivos del DEIS), *Renombrada*, *Creada* (agregada en el procesamiento; se "
            "indica el script cuando es de la actividad 2.2) o *Trazabilidad* (permite volver al archivo original).",
            "- **Para el modelado:** las columnas de la sección 9 describen lo que ocurre después del alta. Las cuatro `REING_*` "
            "son las variables objetivo; `DIAS_REING` e `ID_EGRESO_REING` nunca son predictoras. `ID_PERSONA` es la unidad para "
            "agrupar la partición y la validación cruzada.",
            "- Las descripciones de las secciones 1 a 6 se elaboraron a partir del informe, de las tablas auxiliares del DEIS y "
            "del contenido de cada columna; deben contrastarse con la documentación oficial de la base GRD.",
            f"- Los criterios y los umbrales están en `{ruta}/reglas/`, las cifras en `{ruta}/reportes/` y las decisiones en "
            f"`{ruta}/bitacora.md` y `docs/bitacora.md`.",
        ]),
    ]
    for seccion, filas in secciones.items():
        partes += [f"## {seccion}",
                   "\n".join(["| Columna | Tipo | Descripción | Valores | % con dato | Origen |", "|---|---|---|---|---|---|", *filas])]
    DICCIONARIO.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Diccionario guardado en {DICCIONARIO}")
    print(f"Registro de versiones en {REGISTRO}")


if __name__ == "__main__":
    main()
