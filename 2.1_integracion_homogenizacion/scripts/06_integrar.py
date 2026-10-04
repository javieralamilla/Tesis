"""Paso 4: integración de los seis años homogenizados en una sola tabla.

  1. Apila data/interim/homog_<año>.parquet (mismo esquema) en data/processed/grd_2019_2024.parquet.
  2. Agrega ID_EGRESO = año del archivo * 10.000.000 + número de línea en el txt original.
  3. Marca los duplicados, sin eliminarlos:
       DUP_EXACTO: copia idéntica, en todas las columnas de datos, de un registro anterior.
       DUP_CLAVE:  comparte paciente, hospital, fecha de ingreso y fecha de alta con otro registro.
  4. Valida la tabla integrada y escribe reportes/06_integracion.md.

No se elimina ningún registro: la depuración corresponde a la actividad 2.2.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.1_integracion_homogenizacion\\scripts\\06_integrar.py
"""

import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_REPORTS = ACTIVIDAD / "reportes"
DESTINO = DIR_PROCESSED / "grd_2019_2024.parquet"
ANIOS = list(range(2019, 2025))

TRAZABILIDAD = ["ANIO_ARCHIVO", "ARCHIVO_ORIGEN", "FILA_ORIGEN"]
# Dos registros son el mismo episodio si coinciden en estas cuatro columnas (bitácora D14).
CLAVE = ["ID_PACIENTE", "COD_HOSPITAL", "FECHA_INGRESO", "FECHAALTA"]
FACTOR_ID = 10_000_000
REPETIDAS = r"(DIAGNOSTICO|PROCEDIMIENTO|FECHATRASLADO|SERVICIOTRASLADO|CONDICIONDEALTANEONATO|PESORN|SEXORN)(\d+)|RN(\d)ESTADO"
GRUPOS_CONTEO = {  # promedio de valores informados por egreso
    "Diagnósticos (de 35)": [f"DIAGNOSTICO{i}" for i in range(1, 36)],
    "Procedimientos (de 30)": [f"PROCEDIMIENTO{i}" for i in range(1, 31)],
    "Traslados internos (de 9)": [f"FECHATRASLADO{i}" for i in range(1, 10)],
    "Recién nacidos con peso (de 4)": [f"PESORN{i}" for i in range(1, 5)],
}


def marcar_duplicados(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    datos = df.drop(columns=TRAZABILIDAD)
    huella = pd.util.hash_pandas_object(datos, index=False)
    candidatos = huella.duplicated(keep=False)
    dup_exacto = pd.Series(False, index=df.index)
    if candidatos.any():
        # La huella solo preselecciona; la igualdad se confirma comparando los valores.
        dup_exacto[candidatos] = datos[candidatos].duplicated(keep="first")
    completa = df[CLAVE].notna().all(axis=1)
    dup_clave = pd.Series(False, index=df.index)
    dup_clave[completa] = df.loc[completa, CLAVE].duplicated(keep=False)
    return dup_exacto, dup_clave


def integrar() -> dict:
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    base = pq.read_schema(DIR_INTERIM / f"homog_{ANIOS[0]}.parquet")
    esquema = pa.schema([pa.field("ID_EGRESO", pa.int64()), *[pa.field(f.name, f.type) for f in base],
                         pa.field("DUP_EXACTO", pa.bool_()), pa.field("DUP_CLAVE", pa.bool_())])
    temporal = DESTINO.with_suffix(".parquet.tmp")
    escritor, info = None, {}
    try:
        for anio in ANIOS:
            inicio = time.time()
            df = pq.read_table(DIR_INTERIM / f"homog_{anio}.parquet").to_pandas()
            dup_exacto, dup_clave = marcar_duplicados(df)
            df.insert(0, "ID_EGRESO", anio * FACTOR_ID + df["FILA_ORIGEN"].astype("int64"))
            df["DUP_EXACTO"], df["DUP_CLAVE"] = dup_exacto, dup_clave

            est = (df["FECHAALTA"] - df["FECHA_INGRESO"]).dt.days
            edad = (df["FECHA_INGRESO"] - df["FECHA_NACIMIENTO"]).dt.days / 365.25
            info[anio] = {
                "filas": len(df),
                "nulos": df.isna().mean() * 100,
                "meses": df["FECHAALTA"].dt.month.value_counts().to_dict(),
                "pacientes": df["ID_PACIENTE"].dropna().unique().to_numpy(dtype="int64"),
                "conteos": {k: float(df[cols].notna().sum(axis=1).mean()) for k, cols in GRUPOS_CONTEO.items()},
                "control": {
                    "Egresos": len(df),
                    "Pacientes distintos": int(df["ID_PACIENTE"].nunique()),
                    "Hospitales": int(df["COD_HOSPITAL"].nunique()),
                    "Egresos por paciente": round(df["ID_PACIENTE"].notna().sum() / df["ID_PACIENTE"].nunique(), 2),
                    "% mujeres": round(100 * (df["SEXO"] == "MUJER").mean(), 1),
                    "Edad media al ingreso (años)": round(edad[(edad >= 0) & (edad <= 110)].mean(), 1),
                    "% ingreso por urgencia": round(100 * (df["TIPO_INGRESO"] == "URGENCIA").mean(), 1),
                    "% cirugía mayor ambulatoria": round(100 * df["TIPO_ACTIVIDAD"].str.startswith("CIRUGÍA", na=False).mean(), 1),
                    "% alta por fallecimiento": round(100 * (df["TIPOALTA"] == "FALLECIDO").mean(), 2),
                    "Estadía mediana (días)": float(est.median()),
                    "Estadía media (días)": round(float(est[est >= 0].mean()), 2),
                    "Peso GRD medio": round(float(df["IR_29301_PESO"].mean()), 4),
                },
                "duplicados": {
                    "exactos": int(dup_exacto.sum()),
                    "clave_registros": int(dup_clave.sum()),
                    "clave_grupos": int(len(df.loc[dup_clave, CLAVE].drop_duplicates())),
                    "sin_clave": int((~df[CLAVE].notna().all(axis=1)).sum()),
                },
            }
            tabla = pa.Table.from_pandas(df, schema=esquema, preserve_index=False)
            if escritor is None:
                escritor = pq.ParquetWriter(temporal, tabla.schema, compression="zstd")
            escritor.write_table(tabla)
            print(f"  {anio}: {len(df):,} filas, {time.time() - inicio:.0f} s", flush=True)
            del df, tabla
    finally:
        if escritor is not None:
            escritor.close()
    temporal.replace(DESTINO)
    return info


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def numero(v) -> str:
    return fmt(v) if isinstance(v, (int, np.integer)) or float(v).is_integer() and abs(v) >= 1000 else f"{v:g}".replace(".", ",")


def escribir_reporte(info: dict) -> None:
    anios_txt = [str(a) for a in ANIOS]
    pf = pq.ParquetFile(DESTINO)
    total, n_cols = pf.metadata.num_rows, pf.metadata.num_columns
    por_anio = pq.read_table(DESTINO, columns=["ANIO_ARCHIVO", "ID_EGRESO"])
    conteo = dict(zip(*[c.to_pylist() for c in pc.value_counts(por_anio["ANIO_ARCHIVO"]).flatten()]))
    ids_unicos = pc.count_distinct(por_anio["ID_EGRESO"]).as_py()
    suma = sum(i["filas"] for i in info.values())
    filas_ok = total == suma and all(conteo.get(a) == info[a]["filas"] for a in ANIOS)

    partes = [
        "# Integración de los seis años (Paso 4)",
        "Generado por `2.1_integracion_homogenizacion/scripts/06_integrar.py`. Entrada: `data/interim/homog_<año>.parquet`. "
        f"Salida: `data/processed/{DESTINO.name}`. No se elimina ningún registro.",
        "## 1. Resultado",
        tabla_md(["", "Valor"], [
            ["Registros en la tabla integrada", fmt(total)],
            ["Suma de los seis archivos homogenizados", fmt(suma)],
            ["Columnas", n_cols],
            ["Tamaño del archivo", f"{DESTINO.stat().st_size / 1e6:.0f} MB"],
            ["`ID_EGRESO` distintos", fmt(ids_unicos)],
        ]),
        tabla_md(["Año", "Registros homogenizados", "Registros integrados"],
                 [[a, fmt(info[a]["filas"]), fmt(conteo.get(a, 0))] for a in ANIOS]),
        f"**Verificación:** registros por año conservados: **{'sí' if filas_ok else 'NO'}**; "
        f"`ID_EGRESO` único: **{'sí' if ids_unicos == total else 'NO'}**.",
        "## 2. Columnas nuevas",
        tabla_md(["Columna", "Contenido"], [
            ["`ID_EGRESO`", "Identificador único del egreso: año del archivo × 10.000.000 + número de línea en el txt "
                            "original. Ejemplo: la línea 2 del archivo 2023 es `20230000002`."],
            ["`DUP_EXACTO`", "Verdadero en los registros que son copia idéntica, en todas las columnas de datos, de un "
                             "registro anterior del mismo archivo. La primera aparición queda en falso."],
            ["`DUP_CLAVE`", "Verdadero en todos los registros que comparten paciente, hospital, fecha de ingreso y fecha "
                            "de alta con otro registro. Solo se evalúa cuando esos cuatro datos existen."],
        ]),
        "## 3. Duplicados marcados",
        "Como cada archivo contiene los egresos de un año de alta, los duplicados solo pueden darse dentro de un mismo año.",
        tabla_md(["Año", "Copias exactas (`DUP_EXACTO`)", "Registros con clave repetida (`DUP_CLAVE`)",
                  "Grupos con clave repetida", "Registros sin clave completa (no evaluables)"],
                 [[a, fmt(d["exactos"]), fmt(d["clave_registros"]), fmt(d["clave_grupos"]), fmt(d["sin_clave"])]
                  for a, d in ((a, info[a]["duplicados"]) for a in ANIOS)]
                 + [["**Total**", *[f"**{fmt(sum(info[a]['duplicados'][k] for a in ANIOS))}**"
                                    for k in ("exactos", "clave_registros", "clave_grupos", "sin_clave")]]]),
        "## 4. Tabla de control por año",
        "Sirve para detectar años que se comporten distinto al resto.",
        tabla_md(["Indicador", *anios_txt],
                 [[k, *[numero(info[a]["control"][k]) for a in ANIOS]] for k in info[ANIOS[0]]["control"]]),
        "Promedio de valores informados por egreso en las columnas repetidas:",
        tabla_md(["Grupo de columnas", *anios_txt],
                 [[k, *[f"{info[a]['conteos'][k]:.2f}".replace(".", ",") for a in ANIOS]] for k in GRUPOS_CONTEO]),
        "## 5. Egresos por mes de alta",
        tabla_md(["Año", *[str(m) for m in range(1, 13)]],
                 [[a, *[fmt(info[a]["meses"].get(m, 0)) for m in range(1, 13)]] for a in ANIOS]),
    ]

    # 6. Sin dato por columna y año (columnas no repetidas, más el primer diagnóstico y procedimiento)
    columnas = [c for c in info[ANIOS[0]]["nulos"].index
                if not re.fullmatch(REPETIDAS, c) or c in ("DIAGNOSTICO1", "PROCEDIMIENTO1")]
    filas = []
    for c in columnas:
        valores = [info[a]["nulos"][c] for a in ANIOS]
        if max(valores) > 0:
            filas.append([f"`{c}`", *[("0" if v == 0 else "<0,01" if v < 0.005 else f"{v:.2f}".replace(".", ",")) for v in valores]])
    partes += [
        "## 6. Porcentaje de registros sin dato, por columna y año",
        "Solo columnas con algún valor faltante. De las columnas repetidas se muestra la primera "
        "(`DIAGNOSTICO1` es el diagnóstico principal).",
        tabla_md(["Columna", *anios_txt], filas),
    ]

    # 7. Trazabilidad de pacientes entre años consecutivos
    filas = []
    for a, b in zip(ANIOS[:-1], ANIOS[1:]):
        comunes = np.intersect1d(info[a]["pacientes"], info[b]["pacientes"]).size
        filas.append([f"{a} → {b}", fmt(len(info[a]["pacientes"])), fmt(comunes),
                      f"{100 * comunes / len(info[a]['pacientes']):.1f}".replace(".", ",") + " %"])
    partes += [
        "## 7. Pacientes que reaparecen al año siguiente",
        "Confirma que la tabla integrada permite seguir a un paciente entre años dentro de cada bloque de "
        "identificador (A: 2019–2020; B: 2021–2024) y que entre bloques no hay vínculo (bitácora H02 y D03).",
        tabla_md(["Años", "Pacientes del primer año", "Reaparecen al año siguiente", "%"], filas),
    ]

    salida = DIR_REPORTS / "06_integracion.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    print("Integrando...", flush=True)
    escribir_reporte(integrar())


if __name__ == "__main__":
    main()
