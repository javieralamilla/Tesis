"""Grupos de la validación temporal interna (actividad 2.3, script 13).

Parte del conjunto de desarrollo (data/processed/desarrollo.parquet) y marca cada caso de estudio
para la validación temporal interna (bitácora D37 y D40). No abre el conjunto de prueba.

  1. Versión. Comprueba que el conjunto de desarrollo sea el de la última versión registrada de la
     partición (docs/version_particion.csv).
  2. Período. Los casos de estudio con alta en los años de entrenamiento (2019 a 2022) entrenan el
     modelo, y los de los años de evaluación (2023 y 2024) lo evalúan.
  3. Paciente ya visto. Un caso de evaluación es de un paciente ya visto si su identificador de
     paciente tiene algún egreso en un año de entrenamiento de su mismo bloque, es decir, en 2021 o
     2022. Los egresos de 2019 y 2020 tienen otro identificador y no se pueden enlazar (H19): la
     separación vale dentro del bloque 2021-2024, y un paciente «nuevo» pudo estar hospitalizado
     en 2019 o 2020 con el otro identificador.
  4. Salida. data/processed/validacion_temporal.parquet tiene una fila por caso de estudio de
     desarrollo: su período y, en los de evaluación, si el paciente ya fue visto. No contiene nada
     que dependa de las variables objetivo, así que las etapas siguientes pueden usarla para que
     todos los modelos se evalúen con los mismos grupos.

La validación temporal se informa de tres maneras: con todos los casos de evaluación, solo con los
de pacientes nuevos y solo con los de pacientes ya vistos (revisión del profesor guía del 13 de
octubre de 2026, punto 2.2). Los parámetros están en reglas/parametros.csv. El reporte
reportes/13_validacion_temporal.md muestra el tamaño y las tasas de cada grupo.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.3_validacion_particion\\scripts\\13_validacion_temporal.py
"""

import csv
import hashlib
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
DESARROLLO = DIR_PROCESSED / "desarrollo.parquet"
DESTINO = DIR_PROCESSED / "validacion_temporal.parquet"
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
PARAMETROS = ["anios_entrenamiento_temporal", "anios_evaluacion_temporal", "paciente_visto_egresos"]
COLUMNAS = ["ID_EGRESO", "ID_PACIENTE", "BLOQUE_ID", "ANIO_ARCHIVO", "ES_CASO_ESTUDIO"]
ENTRENAMIENTO, EVALUACION = "ENTRENAMIENTO", "EVALUACION"
FORMAS_VISTO = {"TODOS": "cualquier egreso, sea o no caso de estudio", "CASOS": "un caso de estudio"}


# ------------------------------------------------------------------ parámetros y versión
def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cargar_parametros() -> dict:
    filas = {fila["parametro"]: fila for fila in leer_csv(ARCHIVO_PARAMETROS)}
    faltan = sorted(set(PARAMETROS) - set(filas))
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")

    def anios(nombre: str) -> list[int]:
        return sorted(int(v) for v in filas[nombre]["valor"].split("|") if v.strip())
    par = {"entrenamiento": anios("anios_entrenamiento_temporal"), "evaluacion": anios("anios_evaluacion_temporal"),
           "visto": filas["paciente_visto_egresos"]["valor"].strip().upper()}
    if not par["entrenamiento"] or not par["evaluacion"] or max(par["entrenamiento"]) >= min(par["evaluacion"]):
        raise SystemExit("Los años de evaluación deben ser posteriores a todos los de entrenamiento.")
    if par["visto"] not in FORMAS_VISTO:
        raise SystemExit(f"paciente_visto_egresos: se esperaba {' o '.join(FORMAS_VISTO)} y dice '{par['visto']}'.")
    par["descripcion"] = {nombre: (filas[nombre]["valor"].strip(), filas[nombre]["descripcion"]) for nombre in PARAMETROS}
    return par


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


# ------------------------------------------------------------------ grupos
def marcar(par: dict) -> tuple[pd.DataFrame, dict]:
    """Devuelve una fila por caso de estudio de desarrollo, con su período y si el paciente ya fue visto,
    y las cifras del reporte."""
    objetivos = [c for c in pq.read_schema(DESARROLLO).names if c.startswith("REING_")]
    d = pq.read_table(DESARROLLO, columns=COLUMNAS + objetivos).to_pandas()
    casos = d[d["ES_CASO_ESTUDIO"]].copy()
    anio = casos["ANIO_ARCHIVO"]
    casos["PERIODO"] = np.select([anio.isin(par["entrenamiento"]), anio.isin(par["evaluacion"])], [ENTRENAMIENTO, EVALUACION], default="")
    evaluacion = (casos["PERIODO"] == EVALUACION).to_numpy()

    # Egresos que hacen visto a un paciente: en un año de entrenamiento y en el bloque de los casos de evaluación.
    bloques = sorted(casos.loc[evaluacion, "BLOQUE_ID"].unique())
    fuente = d if par["visto"] == "TODOS" else d[d["ES_CASO_ESTUDIO"]]
    previos = fuente[fuente["ANIO_ARCHIVO"].isin(par["entrenamiento"]) & fuente["BLOQUE_ID"].isin(bloques)]
    visto = casos["ID_PACIENTE"].isin(set(previos["ID_PACIENTE"])).to_numpy()
    casos["PACIENTE_VISTO"] = pd.array(np.where(evaluacion, visto, False), dtype="boolean")
    casos.loc[~evaluacion, "PACIENTE_VISTO"] = pd.NA

    salida = casos[["ID_EGRESO", "ID_PACIENTE", "PERIODO", "PACIENTE_VISTO"]].reset_index(drop=True)

    # ---------------------------------------------------------------- cifras del reporte
    def resumen(mascara: np.ndarray) -> dict:
        g = casos[mascara]
        return {"casos": len(g), "pacientes": int(g["ID_PACIENTE"].nunique()),
                **{k: (int(g[k].notna().sum()), int((g[k] == 1).sum())) for k in objetivos}}
    nuevo = evaluacion & ~visto
    ya_visto = evaluacion & visto
    grupos = {"Entrenamiento": resumen(~evaluacion), "Evaluación: todos los casos": resumen(evaluacion),
              "Evaluación: pacientes nuevos": resumen(nuevo), "Evaluación: pacientes ya vistos": resumen(ya_visto)}
    por_anio = {int(a): (int(((anio == a).to_numpy() & evaluacion).sum()), int(((anio == a).to_numpy() & ya_visto).sum()))
                for a in par["evaluacion"]}
    entrenamiento_bloque = {b: int((~evaluacion & (casos["BLOQUE_ID"] == b).to_numpy()).sum()) for b in sorted(casos["BLOQUE_ID"].unique())}
    info = {"objetivos": objetivos, "egresos": len(d), "casos": len(casos), "grupos": grupos, "por_anio": por_anio,
            "bloques_evaluacion": bloques, "anios_previos": sorted(int(a) for a in previos["ANIO_ARCHIVO"].unique()),
            "egresos_previos": len(previos), "pacientes_previos": int(previos["ID_PACIENTE"].nunique()),
            "entrenamiento_bloque": entrenamiento_bloque}

    # ---------------------------------------------------------------- verificaciones
    info["verificaciones"] = [
        ("Todo caso de estudio de desarrollo tiene un período, de entrenamiento o de evaluación", bool((casos["PERIODO"] != "").all())),
        ("Los casos de evaluación son de años posteriores a todos los de entrenamiento",
         int(anio[evaluacion].min()) > int(anio[~evaluacion].max())),
        ("Los pacientes nuevos y los ya vistos suman todos los casos de evaluación, sin repetir ninguno",
         grupos["Evaluación: pacientes nuevos"]["casos"] + grupos["Evaluación: pacientes ya vistos"]["casos"]
         == grupos["Evaluación: todos los casos"]["casos"]),
        ("`PACIENTE_VISTO` tiene dato solo en los casos de evaluación",
         bool((salida["PACIENTE_VISTO"].notna().to_numpy() == evaluacion).all())),
        ("Un paciente ya visto tiene, en un año de entrenamiento de su bloque, un egreso anterior a su caso de evaluación",
         bool((previos.groupby("ID_PACIENTE")["ANIO_ARCHIVO"].max().reindex(casos.loc[ya_visto, "ID_PACIENTE"]).to_numpy()
               < anio[ya_visto].to_numpy()).all())),
    ]
    return salida, info


# ------------------------------------------------------------------ escritura
def escribir(salida: pd.DataFrame, casos_registrados: int) -> list[tuple[str, bool]]:
    tabla = pa.Table.from_pandas(salida, preserve_index=False)
    temporal = DESTINO.with_suffix(".parquet.tmp")
    pq.write_table(tabla, temporal, compression="zstd")
    temporal.replace(DESTINO)
    releido = pq.read_table(DESTINO).to_pandas(types_mapper={pa.bool_(): pd.BooleanDtype()}.get)

    def texto(df: pd.DataFrame, columna: str) -> np.ndarray:
        return df[columna].astype("string").fillna("(sin dato)").to_numpy()
    return [
        ("El archivo tiene una fila por caso de estudio de desarrollo, como los casos registrados de la partición",
         len(releido) == casos_registrados and releido["ID_EGRESO"].is_unique),
        ("Lo releído del archivo es igual a lo calculado",
         len(releido) == len(salida) and list(releido.columns) == list(salida.columns)
         and all((texto(releido, c) == texto(salida, c)).all() for c in salida.columns)),
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


def escribir_reporte(info: dict, par: dict, version: dict) -> None:
    ruta = ACTIVIDAD.name
    objetivos, g = info["objetivos"], info["grupos"]
    evaluacion = g["Evaluación: todos los casos"]["casos"]
    anios_e = " y ".join(str(a) for a in par["evaluacion"])
    anios_t = f"{min(par['entrenamiento'])} a {max(par['entrenamiento'])}"
    previos = " y ".join(str(a) for a in info["anios_previos"])
    partes = [
        "# Grupos de la validación temporal (actividad 2.3, script 13)",
        f"Generado por `{ruta}/scripts/13_validacion_temporal.py`. Entrada: `data/processed/{DESARROLLO.name}`, de la versión "
        f"{version['version']} de la partición (SHA-256 `{version['sha256_desarrollo']}`). Salida: `data/processed/{DESTINO.name}`. "
        "No se abre el conjunto de prueba. Las decisiones están en "
        f"`{ruta}/bitacora.md` (D37 y D40).",
        f"**Validación temporal interna:** el modelo se entrena con los casos de estudio de desarrollo de {anios_t} y se evalúa "
        f"en los de {anios_e}. Como el reingreso depende mucho de cada paciente, el resultado se informa de tres maneras: con "
        "todos los casos de evaluación, solo con los de pacientes nuevos y solo con los de pacientes ya vistos (revisión del "
        "profesor guía del 13 de octubre de 2026, punto 2.2).",
        f"**Paciente ya visto:** su identificador tiene {FORMAS_VISTO[par['visto']]} en un año de entrenamiento de su mismo "
        f"bloque ({previos}). Los egresos de 2019 y 2020 tienen otro identificador y no se pueden enlazar (H19), así que la "
        "separación vale dentro del bloque 2021–2024: un paciente nuevo pudo estar hospitalizado en 2019 o 2020 con el otro "
        "identificador.",

        "## 1. Tamaño y tasas de cada grupo",
        "Cada tasa usa los casos de estudio del grupo con dato en esa variable.",
        tabla_md(["Grupo", "Casos de estudio", "% de la evaluación", "Pacientes", *[f"`{k}`" for k in objetivos]],
                 [[nombre, fmt(r["casos"]), "—" if nombre == "Entrenamiento" else pct(r["casos"], evaluacion, 1), fmt(r["pacientes"]),
                   *[pct(r[k][1], r[k][0]) for k in objetivos]] for nombre, r in g.items()]),
        "Los pacientes ya vistos reingresan más que los nuevos: por eso conviene separarlos. En ellos el modelo puede rendir "
        "mejor por haberlos visto al entrenar, y ese desempeño no se traslada a pacientes nuevos.",
        "Casos de evaluación por año del alta:",
        tabla_md(["Año del alta", "Casos de evaluación", "De pacientes ya vistos", "%"],
                 [[a, fmt(n), fmt(v), pct(v, n, 1)] for a, (n, v) in info["por_anio"].items()]),
        "Casos de entrenamiento por bloque de identificador: "
        + "; ".join(f"bloque {b}, {fmt(n)}" for b, n in info["entrenamiento_bloque"].items()) + ".",
        f"Egresos que hacen visto a un paciente: {fmt(info['egresos_previos'])} egresos de {fmt(info['pacientes_previos'])} "
        f"identificadores, de {previos}, del bloque {' y '.join(info['bloques_evaluacion'])}.",

        "## 2. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{v.replace('|', ' / ')}`", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 3. Archivo de salida",
        tabla_md(["Columna", "Contenido"], [
            ["`ID_EGRESO`", "Caso de estudio de desarrollo."],
            ["`ID_PACIENTE`", "Identificador de paciente: es el grupo de la validación cruzada (D27)."],
            ["`PERIODO`", f"`{ENTRENAMIENTO}` ({anios_t}) o `{EVALUACION}` ({anios_e})."],
            ["`PACIENTE_VISTO`", "En los casos de evaluación, verdadero si el paciente ya fue visto en el entrenamiento. Sin dato "
                                 "en los casos de entrenamiento."],
        ]),
        "El archivo no contiene las variables objetivo ni nada que dependa de ellas.",

        "## 4. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in info["verificaciones"]),
    ]
    salida = DIR_REPORTS / "13_validacion_temporal.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    par = cargar_parametros()
    version = comprobar_version()
    print(f"Partición: versión {version['version']}. Marcando los grupos...", flush=True)
    salida, info = marcar(par)
    info["verificaciones"].insert(0, (f"El conjunto de desarrollo es el de la versión {version['version']} registrada de la partición", True))
    info["verificaciones"] += escribir(salida, int(version["casos_desarrollo"]))
    escribir_reporte(info, par, version)
    fallidas = [texto for texto, ok in info["verificaciones"] if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
