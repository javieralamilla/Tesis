"""Paso 1: diagnóstico del identificador de paciente entre los seis archivos GRD.

Responde si un mismo paciente conserva su identificador entre años, requisito
para reconstruir reingresos que cruzan de un año a otro.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 1.2_exploracion_calidad\\scripts\\01_diagnostico_ids.py
"""

import csv
from itertools import product
from pathlib import Path

import pandas as pd

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_TXT = RAIZ.parent / "Datos" / "txt"
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_REPORTS = ACTIVIDAD / "reportes"

# Codificación detectada en la inspección inicial de cada archivo.
ARCHIVOS = {
    2019: ("GRD_PUBLICO_2019.txt", "utf-8"),
    2020: ("GRD_PUBLICO_2020.txt", "utf-8"),
    2021: ("GRD_PUBLICO_2021.txt", "utf-8-sig"),
    2022: ("GRD_PUBLICO_EXTERNO_2022.txt", "utf-16"),
    2023: ("GRD_PUBLICO_2023.txt", "utf-16"),
    2024: ("GRD_PUBLICO_2024.txt", "cp1252"),
}

# Columnas por posición, porque el nombre del ID cambia en 2024
# (CIP_ENCRIPTADO -> ID_BENEFICIARIO).
COLUMNAS = {0: "COD_HOSPITAL", 1: "ID", 2: "SEXO", 3: "FECHA_NACIMIENTO",
            14: "FECHA_INGRESO", 34: "FECHAALTA"}

VALORES_NULOS = {"", "DESCONOCIDO", "SIN INFORMACIÓN", "0"}


def leer_extracto(anio: int) -> pd.DataFrame:
    nombre, encoding = ARCHIVOS[anio]
    df = pd.read_csv(
        DIR_TXT / nombre, sep="|", encoding=encoding, usecols=list(COLUMNAS),
        dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE,
    )
    df.columns = [COLUMNAS[i] for i in sorted(COLUMNAS)]
    df = df.apply(lambda s: s.str.strip())
    # Fecha de nacimiento a AAAA-MM-DD, cualquiera sea el formato de origen.
    fnac = df["FECHA_NACIMIENTO"]
    dmy = fnac.str.fullmatch(r"\d{2}-\d{2}-\d{4}")
    df.loc[dmy, "FECHA_NACIMIENTO"] = (fnac[dmy].str[6:10] + "-" + fnac[dmy].str[3:5]
                                       + "-" + fnac[dmy].str[0:2])
    df["ANIO"] = anio
    return df


def describir(df: pd.DataFrame) -> dict:
    ids = df["ID"]
    validos = ids[~ids.isin(VALORES_NULOS)]
    numericos = validos[validos.str.fullmatch(r"\d+")]
    largos = numericos.str.len().value_counts(normalize=True).sort_index()
    return {
        "registros": len(df),
        "pacientes_distintos": validos.nunique(),
        "egresos_por_paciente": round(len(validos) / max(validos.nunique(), 1), 2),
        "pct_id_nulo": round(100 * (1 - len(validos) / len(df)), 3),
        "pct_id_no_numerico": round(100 * (1 - len(numericos) / max(len(validos), 1)), 3),
        "id_min": int(numericos.astype("int64").min()),
        "id_max": int(numericos.astype("int64").max()),
        "largo_id_%": ", ".join(f"{k} dig: {100 * v:.1f}%" for k, v in largos.items() if v >= 0.001),
    }


def perfil_por_paciente(df: pd.DataFrame) -> pd.DataFrame:
    """Un registro por ID con su sexo y fecha de nacimiento más frecuentes."""
    df = df[~df["ID"].isin(VALORES_NULOS)]

    def moda(col: str) -> pd.Series:
        conteo = df.groupby(["ID", col]).size().reset_index(name="n")
        conteo = conteo.sort_values(["ID", "n"], ascending=[True, False])
        return conteo.drop_duplicates("ID").set_index("ID")[col]

    g = df.groupby("ID")
    return pd.DataFrame({
        "SEXO": moda("SEXO"),
        "FNAC": moda("FECHA_NACIMIENTO"),
        "n_sexo": g["SEXO"].nunique(),
        "n_fnac": g["FECHA_NACIMIENTO"].nunique(),
    })


def tabla_md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    filas = ["| " + " | ".join([str(df.index.name or "")] + cols) + " |",
             "|" + "---|" * (len(cols) + 1)]
    for idx, fila in df.iterrows():
        filas.append("| " + " | ".join([str(idx)] + [str(v) for v in fila]) + " |")
    return "\n".join(filas)


def main() -> None:
    DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)

    descripcion, perfiles, consistencia = {}, {}, {}
    for anio in ARCHIVOS:
        print(f"Leyendo {anio}...", flush=True)
        df = leer_extracto(anio)
        df.to_parquet(DIR_INTERIM / f"ids_{anio}.parquet", index=False)
        descripcion[anio] = describir(df)
        p = perfil_por_paciente(df)
        perfiles[anio] = p
        consistencia[anio] = {
            "pacientes": len(p),
            "pct_con_>1_sexo": round(100 * (p["n_sexo"] > 1).mean(), 3),
            "pct_con_>1_fnac": round(100 * (p["n_fnac"] > 1).mean(), 3),
        }

    # Cruce entre años: % de pacientes de A presentes en B, y concordancia
    # de sexo y fecha de nacimiento entre los que coinciden.
    anios = list(ARCHIVOS)
    presencia = pd.DataFrame(index=anios, columns=anios, dtype=object)
    concord = pd.DataFrame(index=anios, columns=anios, dtype=object)
    for a, b in product(anios, anios):
        if a == b:
            presencia.loc[a, b] = concord.loc[a, b] = "—"
            continue
        comun = perfiles[a].join(perfiles[b], how="inner", lsuffix="_a", rsuffix="_b")
        presencia.loc[a, b] = f"{100 * len(comun) / len(perfiles[a]):.1f}%"
        if len(comun):
            igual = (comun["SEXO_a"] == comun["SEXO_b"]) & (comun["FNAC_a"] == comun["FNAC_b"])
            concord.loc[a, b] = f"{100 * igual.mean():.1f}% (n={len(comun):,})"
        else:
            concord.loc[a, b] = "sin coincidencias"
    presencia.index.name = concord.index.name = "desde \\ en"

    desc_df = pd.DataFrame(descripcion).T
    desc_df.index.name = "año"
    cons_df = pd.DataFrame(consistencia).T
    cons_df.index.name = "año"

    informe = "\n\n".join([
        "# Diagnóstico del identificador de paciente (Paso 1)",
        "Generado por `1.2_exploracion_calidad/scripts/01_diagnostico_ids.py`. Nulos: vacío, `DESCONOCIDO`, `SIN INFORMACIÓN` o `0`.",
        "## 1. Descripción del ID por año", tabla_md(desc_df),
        "## 2. Consistencia dentro del año",
        "Porcentaje de pacientes cuyo ID presenta más de un sexo o fecha de nacimiento.",
        tabla_md(cons_df),
        "## 3. Presencia entre años",
        "Porcentaje de pacientes distintos del año de la fila que aparecen en el año de la columna.",
        tabla_md(presencia),
        "## 4. Concordancia entre años",
        "Entre los ID que coinciden, porcentaje con igual sexo y fecha de nacimiento. "
        "Valores cercanos a 100% indican que el ID corresponde a la misma persona; "
        "valores bajos indican coincidencias numéricas entre personas distintas.",
        tabla_md(concord),
    ]) + "\n"
    salida = DIR_REPORTS / "01_diagnostico_ids.md"
    salida.write_text(informe, encoding="utf-8")
    print(informe)
    print(f"Reporte guardado en {salida}")


if __name__ == "__main__":
    main()
