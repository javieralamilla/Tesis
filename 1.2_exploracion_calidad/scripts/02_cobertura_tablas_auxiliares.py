"""Cobertura de los códigos de la base GRD en las tablas auxiliares del DEIS.

Mide, por año, qué porcentaje de los códigos de diagnóstico (CIE-10),
procedimiento (CIE-9-MC), GRD y hospital de los archivos aparece en los
catálogos oficiales, y lista los códigos no encontrados más frecuentes.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 1.2_exploracion_calidad\\scripts\\02_cobertura_tablas_auxiliares.py
"""

import csv
from collections import Counter
from pathlib import Path

import pandas as pd

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_DATOS = RAIZ.parent / "Datos"
DIR_TXT = DIR_DATOS / "txt"
DIR_AUX = DIR_DATOS / "Tablas auxiliares"
DIR_REPORTS = ACTIVIDAD / "reportes"

ARCHIVOS = {
    2019: ("GRD_PUBLICO_2019.txt", "utf-8"),
    2020: ("GRD_PUBLICO_2020.txt", "utf-8"),
    2021: ("GRD_PUBLICO_2021.txt", "utf-8-sig"),
    2022: ("GRD_PUBLICO_EXTERNO_2022.txt", "utf-16"),
    2023: ("GRD_PUBLICO_2023.txt", "utf-16"),
    2024: ("GRD_PUBLICO_2024.txt", "cp1252"),
}

DIAG = [f"DIAGNOSTICO{i}" for i in range(1, 36)]
PROC = [f"PROCEDIMIENTO{i}" for i in range(1, 31)]
OTRAS = ["COD_HOSPITAL", "IR_29301_COD_GRD", "IR_29301_SEVERIDAD", "IR_29301_MORTALIDAD"]
TAM_BLOQUE = 200_000


def cargar_catalogos() -> dict[str, set[str]]:
    cie10 = pd.read_excel(DIR_AUX / "CIE-10.xlsx", dtype=str)
    cie9 = pd.read_excel(DIR_AUX / "CIE-9.xlsx", dtype=str)
    maestra = DIR_AUX / "Tablas maestras bases GRD.xlsx"
    hosp = pd.read_excel(maestra, sheet_name="Hospitales", dtype=str)
    grd = pd.read_excel(maestra, sheet_name="IR - GRD", dtype=str)
    return {
        "CIE-10": set(cie10["Código"].str.strip().str.upper()),
        "CIE-9": set(cie9["Código"].str.strip()),
        "Hospital": set(hosp.iloc[:, 0].dropna().str.strip()),
        # En el Excel el código GRD perdió el cero inicial (11011 -> 011011).
        "GRD": set(grd.iloc[:, 0].dropna().str.strip().str.zfill(6)),
    }


def contar_codigos(anio: int) -> dict[str, Counter]:
    nombre, encoding = ARCHIVOS[anio]
    conteos = {k: Counter() for k in ["CIE-10", "CIE-10 principal", "CIE-9", "Hospital",
                                       "GRD", "Severidad", "Mortalidad"]}
    lector = pd.read_csv(
        DIR_TXT / nombre, sep="|", encoding=encoding, usecols=DIAG + PROC + OTRAS,
        dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE, chunksize=TAM_BLOQUE,
    )
    for bloque in lector:
        diag = bloque[DIAG].stack().str.strip().str.upper()
        conteos["CIE-10"].update(diag[diag != ""].value_counts().to_dict())
        principal = bloque["DIAGNOSTICO1"].str.strip().str.upper()
        conteos["CIE-10 principal"].update(principal[principal != ""].value_counts().to_dict())
        proc = bloque[PROC].stack().str.strip()
        conteos["CIE-9"].update(proc[proc != ""].value_counts().to_dict())
        conteos["Hospital"].update(bloque["COD_HOSPITAL"].str.strip().value_counts().to_dict())
        grd = bloque["IR_29301_COD_GRD"].str.strip()
        grd = grd.where(grd == "", grd.str.zfill(6))
        conteos["GRD"].update(grd.value_counts().to_dict())
        conteos["Severidad"].update(bloque["IR_29301_SEVERIDAD"].str.strip().value_counts().to_dict())
        conteos["Mortalidad"].update(bloque["IR_29301_MORTALIDAD"].str.strip().value_counts().to_dict())
    return conteos


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    catalogos = cargar_catalogos()
    catalogo_de = {"CIE-10": "CIE-10", "CIE-10 principal": "CIE-10", "CIE-9": "CIE-9",
                   "Hospital": "Hospital", "GRD": "GRD"}

    cobertura = {}
    no_encontrados = {k: Counter() for k in catalogo_de}
    valores = {"Severidad": {}, "Mortalidad": {}}
    for anio in ARCHIVOS:
        print(f"Procesando {anio}...", flush=True)
        conteos = contar_codigos(anio)
        fila = {}
        for tipo, cat in catalogo_de.items():
            c = conteos[tipo]
            total = sum(c.values())
            faltan = {k: v for k, v in c.items() if k not in catalogos[cat]}
            no_encontrados[tipo].update(faltan)
            fila[f"{tipo} (% registros)"] = f"{100 * (1 - sum(faltan.values()) / total):.2f}%"
            fila[f"{tipo} (códigos distintos no encontrados)"] = f"{len(faltan)} de {len(c)}"
        cobertura[anio] = fila
        for tipo in valores:
            valores[tipo][anio] = dict(sorted(conteos[tipo].items()))

    partes = [
        "# Cobertura de códigos en las tablas auxiliares (DEIS)",
        "Generado por `1.2_exploracion_calidad/scripts/02_cobertura_tablas_auxiliares.py`. "
        "'% registros' es el porcentaje de apariciones del código (no de códigos distintos) "
        "que existe en el catálogo oficial.",
        f"Tamaño de los catálogos: CIE-10 {len(catalogos['CIE-10']):,} códigos, "
        f"CIE-9 {len(catalogos['CIE-9']):,}, GRD {len(catalogos['GRD']):,}, "
        f"hospitales {len(catalogos['Hospital']):,}.",
    ]
    for tipo in catalogo_de:
        partes.append(f"## {tipo}")
        partes.append("| año | % registros cubiertos | códigos distintos no encontrados |\n|---|---|---|")
        partes[-1] += "".join(
            f"\n| {a} | {f[f'{tipo} (% registros)']} | {f[f'{tipo} (códigos distintos no encontrados)']} |"
            for a, f in cobertura.items())
        top = no_encontrados[tipo].most_common(20)
        if top:
            partes.append("Códigos no encontrados más frecuentes (todos los años): "
                          + ", ".join(f"`{k or '(vacío)'}` ({v:,})" for k, v in top))
    for tipo, por_anio in valores.items():
        partes.append(f"## Valores de {tipo} por año")
        partes.append("\n".join(f"- {a}: " + ", ".join(f"`{k or '(vacío)'}`: {v:,}" for k, v in d.items())
                                for a, d in por_anio.items()))

    informe = "\n\n".join(partes) + "\n"
    salida = DIR_REPORTS / "02_cobertura_tablas_auxiliares.md"
    salida.write_text(informe, encoding="utf-8")
    print(informe)
    print(f"Reporte guardado en {salida}")


if __name__ == "__main__":
    main()
