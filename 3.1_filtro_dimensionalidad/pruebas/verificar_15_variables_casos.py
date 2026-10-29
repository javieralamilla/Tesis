"""Prueba independiente de las variables de los casos de estudio (actividad 3.1, script 15).

Vuelve a calcular, sin usar ninguna función del script 15 y por otro camino, lo que el script dejó en
data/processed/variables_casos.parquet:

  1. Versión y archivo. El conjunto de desarrollo es el registrado; la tabla tiene las 31 columnas esperadas, sin
     identificadores de pacientes ni variables objetivo, y exactamente una fila por caso de estudio.
  2. Tablas de reglas. Los grupos de previsión, las regiones y los códigos de comorbilidad coinciden con una
     segunda transcripción escrita en este programa (los códigos, con los rangos tal como los imprime Quan et al.,
     2005, por ejemplo I42.5–I42.9).
  3. Tabla completa. Para todos los casos, recalcula con pyarrow (el script usa pandas) las variables que no
     dependen de la historia: las de la decisión 1, el episodio (estadía, traslado, UCI o UTI, intervención), la
     marca de ventana cortada, el número de diagnósticos y de procedimientos (que además debe sumar los pares
     caso–código del script 14), el índice de Elixhauser con expresiones regulares y los valores juntados en OTRO.
  4. Muestra de casos. Para 2.000 casos al azar (semilla 2026), los ejemplos del reporte y casos en los bordes
     (episodios de 0 días, hospitalizaciones que terminan el mismo día del ingreso índice o 365 días antes, los
     valores más altos, traslados), arma la historia de 12 meses recorriendo uno por uno los egresos de cada
     persona, sin ordenar ni buscar como lo hace el script.

Solo lee el conjunto de desarrollo; con las rutas por defecto deja reportes/pruebas_variables_casos.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\pruebas\\verificar_15_variables_casos.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
RESULTADO = RAIZ / "data" / "processed" / "variables_casos.parquet"
FILTRO = RAIZ / "data" / "processed" / "filtro_codigos.parquet"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
REGLAS = ACTIVIDAD / "reglas"
PARAMETROS_22 = RAIZ / "2.2_depuracion_etiquetado" / "reglas" / "parametros.csv"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_variables_casos.md"
DIAGNOSTICOS = [f"DIAGNOSTICO{i}" for i in range(1, 36)]
PROCEDIMIENTOS = [f"PROCEDIMIENTO{i}" for i in range(1, 31)]
SERVICIOS = ["SERVICIOINGRESO", *[f"SERVICIOTRASLADO{i}" for i in range(1, 10)], "SERVICIOALTA"]
COLUMNAS = ["ID_EGRESO", "EDAD", "SEXO", "PREVISION_GRUPO", "REGION", "TIPO_INGRESO", "ESTADIA", "CDM", "PESO_GRD",
            "HOSP_PREVIAS", "HOSP_PREVIAS_NO_PLANIF", "DIAS_ULTIMA_HOSP", "CMA_PREVIAS", "SESIONES_PREVIAS",
            "VENTANA_CORTADA", "INDICE_COMORBILIDAD", "TIPO_ALTA", "SEVERIDAD", "RIESGO_MORTALIDAD",
            "ESPECIALIDAD_INTERVENCION", "UCI_UTI", "TRASLADO", "N_DIAGNOSTICOS", "N_PROCEDIMIENTOS", "ESPECIALIDAD",
            "TIPO_PROCEDENCIA", "SERVICIO_INGRESO", "SERVICIO_ALTA", "PUEBLO_ORIGINARIO", "NACIONALIDAD_EXTRANJERA",
            "HOSPITAL"]
PROHIBIDAS = ["ID_PACIENTE", "ID_PERSONA", "ID_EPISODIO", "REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM",
              "DIAS_REING", "ID_EGRESO_REING", "IDENTIDAD_AMBIGUA", "BLOQUE_ID", "ANIO_ARCHIVO"]
HISTORIA = ["HOSP_PREVIAS", "HOSP_PREVIAS_NO_PLANIF", "DIAS_ULTIMA_HOSP", "CMA_PREVIAS", "SESIONES_PREVIAS", "VENTANA_CORTADA"]
EJEMPLOS = [20230001746, 20230000956, 20230120079]  # traslado, historia y jerarquías del reporte
TAMANO_MUESTRA = 2000
SEMILLA = 2026
SIN_DATO, OTRO, SIN_INTERVENCION = "SIN DATO", "OTRO", "SIN INTERVENCIÓN"
resultados = []

# ---------------------------------------------------------------- segunda transcripción de las reglas
PREVISION_ESPERADA = {  # decisión 1: de 12 valores a 8 grupos
    "FONASA INSTITUCIONAL - (MAI) A": "FONASA A", "FONASA INSTITUCIONAL - (MAI) B": "FONASA B",
    "FONASA INSTITUCIONAL - (MAI) C": "FONASA C", "FONASA INSTITUCIONAL - (MAI) D": "FONASA D",
    "FONASA LIBRE ELECCIÓN (FMLE_B)": "FONASA LIBRE ELECCIÓN", "FONASA LIBRE ELECCIÓN (FMLE_C)": "FONASA LIBRE ELECCIÓN",
    "FONASA LIBRE ELECCIÓN (FMLE_D)": "FONASA LIBRE ELECCIÓN", "ISAPRE": "ISAPRE", "PARTICULAR": "PARTICULAR",
    "DIPRECA": "DIPRECA, CAPREDENA Y SISA", "CAPREDENA": "DIPRECA, CAPREDENA Y SISA",
    "CAJA DE PREVISIÓN FFAA (SISA)": "DIPRECA, CAPREDENA Y SISA",
}
REGION_ESPERADA = {  # decisión 1: las 57 provincias de la base, en orden alfabético, con su región
    "AISEN": "AYSÉN", "ANTOFAGASTA": "ANTOFAGASTA", "ANTÁRTICA CHILENA": "MAGALLANES", "ARAUCO": "BIOBÍO",
    "ARICA": "ARICA Y PARINACOTA", "BIO-BIO": "BIOBÍO", "CACHAPOAL": "O'HIGGINS", "CAPITAN PRAT": "AYSÉN",
    "CARDENAL CARO": "O'HIGGINS", "CAUQUENES": "MAULE", "CAUTIN": "LA ARAUCANÍA", "CHACABUCO": "METROPOLITANA",
    "CHAÑARAL": "ATACAMA", "CHILOE": "LOS LAGOS", "CHOAPA": "COQUIMBO", "COIHAIQUE": "AYSÉN", "COLCHAGUA": "O'HIGGINS",
    "CONCEPCION": "BIOBÍO", "COPIAPO": "ATACAMA", "CORDILLERA": "METROPOLITANA", "CURICO": "MAULE", "DIGUILLÍN": "ÑUBLE",
    "EL LOA": "ANTOFAGASTA", "ELQUI": "COQUIMBO", "GENERAL CARRERA": "AYSÉN", "HUASCO": "ATACAMA", "IQUIQUE": "TARAPACÁ",
    "ISLA DE PASCUA": "VALPARAÍSO", "ITATA": "ÑUBLE", "LIMARI": "COQUIMBO", "LINARES": "MAULE", "LLANQUIHUE": "LOS LAGOS",
    "LOS ANDES": "VALPARAÍSO", "MAGALLANES": "MAGALLANES", "MAIPO": "METROPOLITANA", "MALLECO": "LA ARAUCANÍA",
    "MARGA MARGA": "VALPARAÍSO", "MELIPILLA": "METROPOLITANA", "OSORNO": "LOS LAGOS", "PALENA": "LOS LAGOS",
    "PARINACOTA": "ARICA Y PARINACOTA", "PETORCA": "VALPARAÍSO", "PUNILLA": "ÑUBLE", "QUILLOTA": "VALPARAÍSO",
    "RANCO": "LOS RÍOS", "SAN ANTONIO": "VALPARAÍSO", "SAN FELIPE": "VALPARAÍSO", "SANTIAGO": "METROPOLITANA",
    "TALAGANTE": "METROPOLITANA", "TALCA": "MAULE", "TAMARUGAL": "TARAPACÁ", "TIERRA DEL FUEGO": "MAGALLANES",
    "TOCOPILLA": "ANTOFAGASTA", "ULTIMA ESPERANZA": "MAGALLANES", "VALDIVIA": "LOS RÍOS", "VALPARAISO": "VALPARAÍSO",
    "ÑUBLE": "ÑUBLE",
}
# Códigos CIE-10 de Quan et al. (2005), escritos como en su tabla: «.x» es toda la categoría y «–» un rango.
ELIXHAUSER_QUAN = {
    "ICC": "I09.9, I11.0, I13.0, I13.2, I25.5, I42.0, I42.5–I42.9, I43.x, I50.x, P29.0",
    "ARRITMIA": "I44.1–I44.3, I45.6, I45.9, I47.x–I49.x, R00.0, R00.1, R00.8, T82.1, Z45.0, Z95.0",
    "VALVULAR": "A52.0, I05.x–I08.x, I09.1, I09.8, I34.x–I39.x, Q23.0–Q23.3, Z95.2–Z95.4",
    "CIRCULACION_PULMONAR": "I26.x, I27.x, I28.0, I28.8, I28.9",
    "VASCULAR_PERIFERICA": "I70.x, I71.x, I73.1, I73.8, I73.9, I77.1, I79.0, I79.2, K55.1, K55.8, K55.9, Z95.8, Z95.9",
    "HTA_SIN_COMPLICACIONES": "I10.x",
    "HTA_CON_COMPLICACIONES": "I11.x–I13.x, I15.x",
    "PARALISIS": "G04.1, G11.4, G80.1, G80.2, G81.x, G82.x, G83.0–G83.4, G83.9",
    "OTRA_NEUROLOGICA": "G10.x–G13.x, G20.x–G22.x, G25.4, G25.5, G31.2, G31.8, G31.9, G32.x, G35.x–G37.x, G40.x, G41.x, "
                        "G93.1, G93.4, R47.0, R56.x",
    "PULMONAR_CRONICA": "I27.8, I27.9, J40.x–J47.x, J60.x–J67.x, J68.4, J70.1, J70.3",
    "DIABETES_SIN_COMPLICACIONES": "E10.0, E10.1, E10.9, E11.0, E11.1, E11.9, E12.0, E12.1, E12.9, E13.0, E13.1, E13.9, "
                                   "E14.0, E14.1, E14.9",
    "DIABETES_CON_COMPLICACIONES": "E10.2–E10.8, E11.2–E11.8, E12.2–E12.8, E13.2–E13.8, E14.2–E14.8",
    "HIPOTIROIDISMO": "E00.x–E03.x, E89.0",
    "INSUFICIENCIA_RENAL": "I12.0, I13.1, N18.x, N19.x, N25.0, Z49.0–Z49.2, Z94.0, Z99.2",
    "HEPATICA": "B18.x, I85.x, I86.4, I98.2, K70.x, K71.1, K71.3–K71.5, K71.7, K72.x–K74.x, K76.0, K76.2–K76.9, Z94.4",
    "ULCERA_PEPTICA": "K25.7, K25.9, K26.7, K26.9, K27.7, K27.9, K28.7, K28.9",
    "VIH": "B20.x–B22.x, B24.x",
    "LINFOMA": "C81.x–C85.x, C88.x, C96.x, C90.0, C90.2",
    "METASTASIS": "C77.x–C80.x",
    "TUMOR_SOLIDO": "C00.x–C26.x, C30.x–C34.x, C37.x–C41.x, C43.x, C45.x–C58.x, C60.x–C76.x, C97.x",
    "REUMATICA": "L94.0, L94.1, L94.3, M05.x, M06.x, M08.x, M12.0, M12.3, M30.x, M31.0–M31.3, M32.x–M35.x, M45.x, M46.1, "
                 "M46.8, M46.9",
    "COAGULOPATIA": "D65–D68.x, D69.1, D69.3–D69.6",
    "OBESIDAD": "E66.x",
    "PERDIDA_DE_PESO": "E40.x–E46.x, R63.4, R64",
    "LIQUIDOS_ELECTROLITOS": "E22.2, E86.x, E87.x",
    "ANEMIA_POR_PERDIDA": "D50.0",
    "ANEMIA_POR_DEFICIENCIA": "D50.8, D50.9, D51.x–D53.x",
    "ALCOHOL": "F10, E52, G62.1, I42.6, K29.2, K70.0, K70.3, K70.9, T51.x, Z50.2, Z71.4, Z72.1",
    "DROGAS": "F11.x–F16.x, F18.x, F19.x, Z71.5, Z72.2",
    "PSICOSIS": "F20.x, F22.x–F25.x, F28.x, F29.x, F30.2, F31.2, F31.5",
    "DEPRESION": "F20.4, F31.3–F31.5, F32.x, F33.x, F34.1, F41.2, F43.2",
}
CHARLSON_QUAN = {
    "INFARTO": "I21.x, I22.x, I25.2",
    "ICC": "I09.9, I11.0, I13.0, I13.2, I25.5, I42.0, I42.5–I42.9, I43.x, I50.x, P29.0",
    "VASCULAR_PERIFERICA": "I70.x, I71.x, I73.1, I73.8, I73.9, I77.1, I79.0, I79.2, K55.1, K55.8, K55.9, Z95.8, Z95.9",
    "CEREBROVASCULAR": "G45.x, G46.x, H34.0, I60.x–I69.x",
    "DEMENCIA": "F00.x–F03.x, F05.1, G30.x, G31.1",
    "PULMONAR_CRONICA": "I27.8, I27.9, J40.x–J47.x, J60.x–J67.x, J68.4, J70.1, J70.3",
    "REUMATICA": "M05.x, M06.x, M31.5, M32.x–M34.x, M35.1, M35.3, M36.0",
    "ULCERA_PEPTICA": "K25.x–K28.x",
    "HEPATICA_LEVE": "B18.x, K70.0–K70.3, K70.9, K71.3–K71.5, K71.7, K73.x, K74.x, K76.0, K76.2–K76.4, K76.8, K76.9, Z94.4",
    "DIABETES_SIN_COMPLICACIONES": "E10.0, E10.1, E10.6, E10.8, E10.9, E11.0, E11.1, E11.6, E11.8, E11.9, E12.0, E12.1, "
                                   "E12.6, E12.8, E12.9, E13.0, E13.1, E13.6, E13.8, E13.9, E14.0, E14.1, E14.6, E14.8, E14.9",
    "DIABETES_CON_COMPLICACIONES": "E10.2–E10.5, E10.7, E11.2–E11.5, E11.7, E12.2–E12.5, E12.7, E13.2–E13.5, E13.7, "
                                   "E14.2–E14.5, E14.7",
    "HEMIPLEJIA": "G04.1, G11.4, G80.1, G80.2, G81.x, G82.x, G83.0–G83.4, G83.9",
    "RENAL": "I12.0, I13.1, N03.2–N03.7, N05.2–N05.7, N18.x, N19.x, N25.0, Z49.0–Z49.2, Z94.0, Z99.2",
    "CANCER": "C00.x–C26.x, C30.x–C34.x, C37.x–C41.x, C43.x, C45.x–C58.x, C60.x–C76.x, C81.x–C85.x, C88.x, C90.x–C97.x",
    "HEPATICA_GRAVE": "I85.0, I85.9, I86.4, I98.2, K70.4, K71.1, K72.1, K72.9, K76.5, K76.6, K76.7",
    "METASTASIS": "C77.x–C80.x",
    "VIH": "B20.x–B22.x, B24.x",
}
PESOS_QUAN_2011 = {"INFARTO": 0, "ICC": 2, "VASCULAR_PERIFERICA": 0, "CEREBROVASCULAR": 0, "DEMENCIA": 2,
                   "PULMONAR_CRONICA": 1, "REUMATICA": 1, "ULCERA_PEPTICA": 0, "HEPATICA_LEVE": 2,
                   "DIABETES_SIN_COMPLICACIONES": 0, "DIABETES_CON_COMPLICACIONES": 1, "HEMIPLEJIA": 2, "RENAL": 1,
                   "CANCER": 2, "HEPATICA_GRAVE": 4, "METASTASIS": 6, "VIH": 4}
JERARQUIAS = {  # la condición más grave (clave) reemplaza a su versión leve (valor)
    "ELIXHAUSER": {"DIABETES_CON_COMPLICACIONES": "DIABETES_SIN_COMPLICACIONES", "METASTASIS": "TUMOR_SOLIDO",
                   "HTA_CON_COMPLICACIONES": "HTA_SIN_COMPLICACIONES"},
    "CHARLSON": {"DIABETES_CON_COMPLICACIONES": "DIABETES_SIN_COMPLICACIONES", "HEPATICA_GRAVE": "HEPATICA_LEVE",
                 "METASTASIS": "CANCER"},
}


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    resultados.append((f"{nombre} {detalle}".rstrip(), bool(cumple)))
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


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


def expandir(texto: str) -> set[str]:
    """«I42.5–I42.9, I43.x» → {I425, I426, I427, I428, I429, I43}: los códigos sin punto, como prefijos."""
    codigos = set()
    for item in texto.replace(" ", "").split(","):
        item = item.replace(".x", "")
        if "–" not in item:
            codigos.add(item.replace(".", ""))
            continue
        a, b = item.split("–")
        if len(a) == 3:  # rango de categorías: I05–I08
            codigos |= {f"{a[0]}{n:02d}" for n in range(int(a[1:3]), int(b[1:3]) + 1)}
        else:            # rango dentro de una categoría: I42.5–I42.9
            codigos |= {f"{a[:3]}{n}" for n in range(int(a[4:]), int(b[4:]) + 1)}
    return codigos


def a_numpy(arreglo) -> np.ndarray:
    return arreglo.to_numpy(zero_copy_only=False)


def sin_dato(arreglo, valor: str = SIN_DATO) -> np.ndarray:
    return a_numpy(pc.fill_null(arreglo, valor)).astype(object)


def juntar_raros(valores: np.ndarray, minimo: int) -> np.ndarray:
    """Los valores con menos de «minimo» casos pasan a OTRO (contados aquí con un diccionario de Python)."""
    cuenta = {}
    for x in valores:
        cuenta[x] = cuenta.get(x, 0) + 1
    raros = {x for x, k in cuenta.items() if k < minimo}
    return np.array([OTRO if x in raros else x for x in valores], dtype=object)


def distintos_por_caso(tabla: pa.Table, columnas: list[str]) -> np.ndarray:
    """Códigos distintos de cada caso: cada par (fila, código) se vuelve un número y se cuentan los distintos."""
    filas, valores = [], []
    for col in columnas:
        filas.append(np.flatnonzero(a_numpy(pc.is_valid(tabla[col]))))
        valores.extend(tabla[col].drop_null().chunks)
    filas = np.concatenate(filas).astype("int64")
    indices = a_numpy(pa.concat_arrays(valores).dictionary_encode().indices).astype("int64")
    k = int(indices.max()) + 1
    pares = np.unique(filas * k + indices)
    return np.bincount(pares // k, minlength=tabla.num_rows)


def main() -> None:
    inicio = time.time()
    registro = leer_csv(REGISTRO)[-1]
    par = {f["parametro"]: f["valor"].strip() for f in leer_csv(REGLAS / "parametros.csv")}
    regla = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS_22)}
    lista = lambda t: [x.strip() for x in t.split("|") if x.strip()]
    ventana, sin_hosp, minimo = int(par["ventana_historia_dias"]), int(par["dias_sin_hospitalizacion"]), int(par["casos_minimos_categoria"])
    inicio_bloques = {b.split("=")[0]: date.fromisoformat(b.split("=")[1]) for b in lista(par["inicio_bloques"])}
    no_planificados, partos, sesiones = lista(regla["ingresos_no_planificados"]), lista(regla["grd_parto"]), lista(regla["diagnosticos_sesion"])

    # ---------------------------------------------------------------- 1. versión y archivo
    comprobar(f"El conjunto de desarrollo tiene el hash de la versión {registro['version']} registrada de la partición",
              sha256(DESARROLLO) == registro["sha256_desarrollo"])
    res = pd.read_parquet(RESULTADO)
    comprobar("variables_casos.parquet tiene las 31 columnas esperadas, en orden", list(res.columns) == COLUMNAS)
    comprobar("No contiene identificadores de pacientes, variables objetivo ni el año",
              not set(PROHIBIDAS) & set(res.columns))

    # ---------------------------------------------------------------- 2. tablas de reglas
    prevision = {f["prevision"]: f["grupo"] for f in leer_csv(REGLAS / "prevision_grupos.csv")}
    comprobar("La tabla de previsión coincide con la decisión 1 (12 valores en 8 grupos)",
              prevision == PREVISION_ESPERADA and len(set(prevision.values())) == 8)
    region = {f["provincia"]: f["region"] for f in leer_csv(REGLAS / "provincia_region.csv")}
    comprobar("La tabla de regiones coincide con la segunda transcripción (57 provincias en 16 regiones)",
              region == REGION_ESPERADA and len(set(region.values())) == 16)
    tabla = pd.DataFrame(leer_csv(REGLAS / "comorbilidad_quan2005.csv"))
    esperado = {("ELIXHAUSER", k): expandir(v) for k, v in ELIXHAUSER_QUAN.items()}
    esperado |= {("CHARLSON", k): expandir(v) for k, v in CHARLSON_QUAN.items()}
    en_tabla = {(r.indice, r.condicion): {c.replace(".", "") for c in r.codigos.split("|")} for r in tabla.itertuples()}
    distintas = sorted(f"{i} {c}" for (i, c) in set(esperado) | set(en_tabla) if esperado.get((i, c)) != en_tabla.get((i, c)))
    comprobar("Los códigos de comorbilidad coinciden con los rangos de Quan et al. (2005), condición por condición",
              not distintas, f"({len(esperado)} condiciones, {sum(len(v) for v in esperado.values())} códigos"
                             + (f"; distintas: {', '.join(distintas[:5])}" if distintas else "") + ")")
    pesos_ok = all(int(r.peso) == (1 if r.indice == "ELIXHAUSER" else PESOS_QUAN_2011[r.condicion]) for r in tabla.itertuples())
    jerarquia_ok = all((r.reemplaza_a or None) == JERARQUIAS[r.indice].get(r.condicion) for r in tabla.itertuples())
    comprobar("Los pesos (1 en Elixhauser; Quan et al. 2011 en Charlson) y las jerarquías de la tabla son los esperados",
              pesos_ok and jerarquia_ok)

    # ---------------------------------------------------------------- 3. tabla completa, con pyarrow
    columnas_casos = ["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "BLOQUE_ID", "COD_HOSPITAL", "SEXO", "FECHA_NACIMIENTO",
                      "FECHA_INGRESO", "FECHAALTA", "ETNIA", "NACIONALIDAD", "PREVISION", "PROVINCIA", "TIPO_PROCEDENCIA",
                      "TIPO_INGRESO", "ESPECIALIDAD_MEDICA", "SERVICIOINGRESO", "SERVICIOALTA", "TIPOALTA",
                      "ESPECIALIDADINTERVENCION", "CDM", "IR_29301_PESO", "IR_29301_SEVERIDAD", "IR_29301_MORTALIDAD",
                      *DIAGNOSTICOS, *PROCEDIMIENTOS]
    t = pq.read_table(DESARROLLO, columns=columnas_casos, filters=[("ES_CASO_ESTUDIO", "==", True)])
    n = t.num_rows
    ids = a_numpy(t["ID_EGRESO"])
    comprobar("Hay exactamente una fila por caso de estudio de desarrollo", len(res) == n == int(registro["casos_desarrollo"])
              and res["ID_EGRESO"].is_unique and set(res["ID_EGRESO"]) == set(ids), f"({fmt(n)} casos)")
    r = res.set_index("ID_EGRESO").loc[ids]  # en el orden de los casos de desarrollo

    def iguales(col: str, calculado: np.ndarray) -> int:
        """Cuántos casos difieren entre el script y el recálculo (los vacíos numéricos cuentan como iguales)."""
        a = r[col].to_numpy()
        if a.dtype.kind == "f" or np.asarray(calculado).dtype.kind == "f":
            a, b = a.astype(float), np.asarray(calculado, dtype=float)
            return int((~(np.isclose(a, b, rtol=0, atol=1e-9) | (np.isnan(a) & np.isnan(b)))).sum())
        return int((a.astype(object) != np.asarray(calculado).astype(object)).sum())

    def comparar_columnas(nombre: str, calculadas: dict) -> None:
        malas = {col: iguales(col, valores) for col, valores in calculadas.items()}
        comprobar(nombre, not any(malas.values()),
                  "(" + "; ".join(f"{col}: {fmt(k)} casos distintos" for col, k in malas.items() if k) + ")" if any(malas.values()) else "")

    # Decisión 1
    dias = lambda col: a_numpy(t[col]).astype("datetime64[D]")
    edad = (dias("FECHA_INGRESO") - dias("FECHA_NACIMIENTO")).astype("int64") / 365.25
    prov = sin_dato(t["PREVISION"])
    reg = sin_dato(t["PROVINCIA"])
    peso = a_numpy(t["IR_29301_PESO"]).astype(float)
    sin = {"SEXO": int(a_numpy(pc.is_null(t["SEXO"])).sum()), "PREVISION": int(a_numpy(pc.is_null(t["PREVISION"])).sum()),
           "PROVINCIA": int(a_numpy(pc.is_null(t["PROVINCIA"])).sum()), "TIPO_INGRESO": int(a_numpy(pc.is_null(t["TIPO_INGRESO"])).sum()),
           "peso 0": int((peso <= 0).sum())}
    comparar_columnas("Decisión 1: edad, sexo, previsión, región, tipo de ingreso, CDM y peso iguales en todos los casos", {
        "EDAD": edad, "SEXO": sin_dato(t["SEXO"]),
        "PREVISION_GRUPO": np.array([SIN_DATO if x == SIN_DATO else PREVISION_ESPERADA.get(x, "?") for x in prov], dtype=object),
        "REGION": np.array([SIN_DATO if x == SIN_DATO else REGION_ESPERADA.get(x, "?") for x in reg], dtype=object),
        "TIPO_INGRESO": sin_dato(t["TIPO_INGRESO"]), "CDM": a_numpy(t["CDM"]).astype(object),
        "PESO_GRD": np.where(peso > 0, peso, np.nan)})
    print("  sin dato:", sin, flush=True)

    # Episodios, con el group_by de pyarrow sobre todos los egresos que tienen episodio
    columnas_egresos = ["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "COD_HOSPITAL", "FECHA_INGRESO",
                        "FECHAALTA", "TIPO_INGRESO", "IR_29301_COD_GRD", "DIAGNOSTICO1", "EXC_CMA", "EXC_SESION",
                        "EXC_ACTIVIDAD_2019", "ESPECIALIDADINTERVENCION", *SERVICIOS]
    eg = pq.read_table(DESARROLLO, columns=columnas_egresos)
    eg = eg.filter(pc.is_valid(eg["ID_EPISODIO"]))
    critico = np.zeros(eg.num_rows, dtype=bool)
    for col in SERVICIOS:
        texto = pc.utf8_upper(eg[col])
        incluye = np.zeros(eg.num_rows, dtype=bool)
        for patron in lista(par["servicios_criticos"]):
            incluye |= a_numpy(pc.fill_null(pc.match_substring(texto, patron), False))
        for patron in lista(par["servicios_criticos_excluidos"]):
            incluye &= ~a_numpy(pc.fill_null(pc.match_substring(texto, patron), False))
        critico |= incluye
    eg = eg.append_column("CRITICO", pa.array(critico))
    epi = eg.group_by("ID_EPISODIO").aggregate([("FECHA_INGRESO", "min"), ("COD_HOSPITAL", "count_distinct"), ("CRITICO", "any")])
    epi = epi.to_pandas().set_index("ID_EPISODIO")
    ep = epi.loc[a_numpy(t["ID_EPISODIO"]).astype("int64")]
    ingreso_indice = ep["FECHA_INGRESO_min"].to_numpy().astype("datetime64[D]")
    cortada = np.zeros(n, dtype=bool)
    for bloque, primer_dia in inicio_bloques.items():  # D42: la ventana empieza antes del primer día del bloque
        limite = np.datetime64(primer_dia.replace(year=primer_dia.year + 1))
        cortada |= (a_numpy(t["BLOQUE_ID"]) == bloque) & (ingreso_indice < limite)
    # Intervención: la del propio egreso; si no tiene, la del último otro egreso del episodio que la tenga
    otros = eg.filter(pc.and_(pc.is_valid(eg["ESPECIALIDADINTERVENCION"]), pc.invert(eg["ES_CASO_ESTUDIO"])))
    otros = otros.select(["ID_EPISODIO", "FECHAALTA", "ESPECIALIDADINTERVENCION"]).to_pandas()
    otros = otros.sort_values(["ID_EPISODIO", "FECHAALTA"]).drop_duplicates("ID_EPISODIO", keep="last").set_index("ID_EPISODIO")
    propia = a_numpy(t["ESPECIALIDADINTERVENCION"]).astype(object)
    de_tramo = otros["ESPECIALIDADINTERVENCION"].reindex(a_numpy(t["ID_EPISODIO"]).astype("int64")).to_numpy()
    intervencion = np.array([p if isinstance(p, str) else (o if isinstance(o, str) else SIN_INTERVENCION)
                             for p, o in zip(propia, de_tramo)], dtype=object)
    comparar_columnas("Episodio: estadía, traslado, UCI o UTI, marca de ventana cortada e intervención iguales en todos los casos", {
        "ESTADIA": (dias("FECHAALTA") - ingreso_indice).astype("int64"),
        "TRASLADO": (ep["COD_HOSPITAL_count_distinct"].to_numpy() > 1).astype(int),
        "UCI_UTI": ep["CRITICO_any"].to_numpy().astype(int), "VENTANA_CORTADA": cortada.astype(int),
        "ESPECIALIDAD_INTERVENCION": juntar_raros(intervencion, minimo)})
    comprobar("Ningún egreso E04 de 2019 tiene episodio", not a_numpy(eg["EXC_ACTIVIDAD_2019"]).any())

    # Número de diagnósticos y de procedimientos, y su suma frente a los pares caso–código del script 14
    n_dx, n_px = distintos_por_caso(t, DIAGNOSTICOS), distintos_por_caso(t, PROCEDIMIENTOS)
    comparar_columnas("Número de diagnósticos y de procedimientos distintos iguales en todos los casos",
                      {"N_DIAGNOSTICOS": n_dx, "N_PROCEDIMIENTOS": n_px})
    filtro = pd.read_parquet(FILTRO, columns=["VARIABLE", "BLOQUE", "CASOS"])
    pares = filtro[filtro["VARIABLE"] == "REING_7D"].groupby("BLOQUE")["CASOS"].sum()  # REING_7D tiene dato en todos
    comprobar("Las sumas coinciden con los pares caso–código del filtro del script 14",
              int(n_dx.sum()) == int(pares["DIAGNOSTICO"]) and int(n_px.sum()) == int(pares["PROCEDIMIENTO"]),
              f"({fmt(n_dx.sum())} diagnósticos y {fmt(n_px.sum())} procedimientos)")

    # Índice de comorbilidad con expresiones regulares de pyarrow, columna por columna
    marcas = {k: np.zeros(n, dtype=bool) for k in esperado}
    patrones = {k: "^(" + "|".join(sorted(v)) + ")" for k, v in esperado.items()}
    for col in DIAGNOSTICOS:
        filas = np.flatnonzero(a_numpy(pc.is_valid(t[col])))
        if not len(filas):
            continue
        sin_punto = pc.replace_substring(t[col].drop_null(), ".", "")
        for k, patron in patrones.items():
            marcas[k][filas[a_numpy(pc.match_substring_regex(sin_punto, patron))]] = True
    for indice, reglas in JERARQUIAS.items():
        for grave, leve in reglas.items():
            marcas[(indice, leve)] = marcas[(indice, leve)] & ~marcas[(indice, grave)]
    elix = sum(marcas[("ELIXHAUSER", k)].astype(int) for k in ELIXHAUSER_QUAN)
    charlson = sum(PESOS_QUAN_2011[k] * marcas[("CHARLSON", k)].astype(int) for k in CHARLSON_QUAN)
    alguna_charlson = np.logical_or.reduce([marcas[("CHARLSON", k)] for k in CHARLSON_QUAN])
    en_uso = elix if par["indice_comorbilidad"].upper() == "ELIXHAUSER" else charlson
    comparar_columnas(f"Índice de comorbilidad ({par['indice_comorbilidad']}) igual en todos los casos", {"INDICE_COMORBILIDAD": en_uso})
    print(f"  Elixhauser con alguna condición: {100 * (elix > 0).mean():.1f} %; Charlson con alguna: {100 * alguna_charlson.mean():.1f} %"
          f" ({time.time() - inicio:.0f} s)", flush=True)

    # Las demás columnas del CMBD, con los valores raros juntados en OTRO
    etnia, nacion = a_numpy(t["ETNIA"]).astype(object), a_numpy(t["NACIONALIDAD"]).astype(object)
    sin_pueblo, local = set(lista(par["etnia_sin_pueblo"])), par["nacionalidad_local"]
    comparar_columnas("Demás columnas del CMBD y valores juntados en OTRO iguales en todos los casos", {
        "TIPO_ALTA": juntar_raros(sin_dato(t["TIPOALTA"]), minimo),
        "SEVERIDAD": a_numpy(t["IR_29301_SEVERIDAD"]).astype(int), "RIESGO_MORTALIDAD": a_numpy(t["IR_29301_MORTALIDAD"]).astype(int),
        "ESPECIALIDAD": juntar_raros(sin_dato(t["ESPECIALIDAD_MEDICA"]), minimo),
        "TIPO_PROCEDENCIA": juntar_raros(sin_dato(t["TIPO_PROCEDENCIA"]), minimo),
        "SERVICIO_INGRESO": juntar_raros(sin_dato(t["SERVICIOINGRESO"]), minimo),
        "SERVICIO_ALTA": juntar_raros(sin_dato(t["SERVICIOALTA"]), minimo),
        "PUEBLO_ORIGINARIO": np.array([SIN_DATO if not isinstance(x, str) else ("NO" if x in sin_pueblo else "SÍ") for x in etnia], dtype=object),
        "NACIONALIDAD_EXTRANJERA": np.array([SIN_DATO if not isinstance(x, str) else ("NO" if x == local else "SÍ") for x in nacion], dtype=object),
        "HOSPITAL": juntar_raros(a_numpy(t["COD_HOSPITAL"]).astype(object), minimo)})

    # ---------------------------------------------------------------- 4. muestra: la historia, egreso por egreso
    rng = np.random.default_rng(SEMILLA)
    muestra = set(rng.choice(ids, TAMANO_MUESTRA, replace=False).tolist()) | set(EJEMPLOS)
    anio = res["ID_EGRESO"] // 10_000_000
    bordes = {"episodio propio de 0 días": res["ESTADIA"] == 0, "hospitalización el mismo día del ingreso índice": res["DIAS_ULTIMA_HOSP"] == 0,
              "hospitalización justo 365 días antes": res["DIAS_ULTIMA_HOSP"] == ventana,
              "marca en 2020 o 2022": (res["VENTANA_CORTADA"] == 1) & anio.isin([2020, 2022]),
              "cirugía ambulatoria previa": res["CMA_PREVIAS"] > 0, "sesión previa": res["SESIONES_PREVIAS"] > 0,
              "traslado": res["TRASLADO"] == 1}
    for nombre, filtro_borde in bordes.items():
        candidatos = res.loc[filtro_borde, "ID_EGRESO"].to_numpy()
        muestra |= set(rng.choice(candidatos, min(150, len(candidatos)), replace=False).tolist())
    muestra |= set(res.nlargest(10, "HOSP_PREVIAS")["ID_EGRESO"])
    muestra = sorted(muestra)
    casos_m = t.select(["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "BLOQUE_ID"]).to_pandas().set_index("ID_EGRESO").loc[muestra]
    personas = set(casos_m["ID_PERSONA"].astype("int64"))
    egm = eg.select(["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "FECHA_INGRESO", "FECHAALTA", "TIPO_INGRESO", "IR_29301_COD_GRD",
                     "DIAGNOSTICO1", "EXC_CMA", "EXC_SESION"]).to_pandas()
    egm = egm[egm["ID_PERSONA"].isin(personas)]
    print(f"Recalculando la historia de {fmt(len(muestra))} casos ({fmt(len(personas))} personas, {fmt(len(egm))} egresos)...", flush=True)
    por_persona = {p: list(g.itertuples(index=False)) for p, g in egm.groupby("ID_PERSONA")}
    calculado = {}
    for id_caso, caso in casos_m.iterrows():
        egresos = por_persona[int(caso["ID_PERSONA"])]
        propio = int(caso["ID_EPISODIO"])
        ingreso = min(x.FECHA_INGRESO for x in egresos if x.ID_EPISODIO == propio).date()
        desde = ingreso - timedelta(days=ventana)
        episodios = {}
        for x in egresos:  # cada episodio: su alta final, si es hospitalización y si empezó con un ingreso no planificado
            e = episodios.setdefault(x.ID_EPISODIO, {"alta": None, "hosp": False, "no_planif": False})
            alta = x.FECHAALTA.date()
            e["alta"] = alta if e["alta"] is None or alta > e["alta"] else e["alta"]
            e["hosp"] = e["hosp"] or not (x.EXC_CMA or x.EXC_SESION)
            if x.ID_EGRESO == x.ID_EPISODIO:
                parto = isinstance(x.IR_29301_COD_GRD, str) and any(x.IR_29301_COD_GRD.startswith(g) for g in partos)
                sesion = isinstance(x.DIAGNOSTICO1, str) and any(x.DIAGNOSTICO1.startswith(s) for s in sesiones)
                e["no_planif"] = x.TIPO_INGRESO in no_planificados and not parto and not sesion
        previas = [e for k, e in episodios.items() if k != propio and e["hosp"] and desde <= e["alta"] <= ingreso]
        cma = sum(1 for x in egresos if x.ID_EPISODIO != propio and x.EXC_CMA and desde <= x.FECHAALTA.date() <= ingreso)
        ses = sum(1 for x in egresos if x.ID_EPISODIO != propio and x.EXC_SESION and not x.EXC_CMA
                  and desde <= x.FECHAALTA.date() <= ingreso)
        primer_dia = inicio_bloques[caso["BLOQUE_ID"]]
        calculado[id_caso] = {
            "HOSP_PREVIAS": len(previas), "HOSP_PREVIAS_NO_PLANIF": sum(e["no_planif"] for e in previas),
            "DIAS_ULTIMA_HOSP": (ingreso - max(e["alta"] for e in previas)).days if previas else sin_hosp,
            "CMA_PREVIAS": cma, "SESIONES_PREVIAS": ses,
            "VENTANA_CORTADA": int(ingreso < primer_dia.replace(year=primer_dia.year + 1))}
    calc = pd.DataFrame.from_dict(calculado, orient="index").loc[muestra]
    ref = res.set_index("ID_EGRESO").loc[muestra, HISTORIA]
    malas = {col: int((ref[col].to_numpy() != calc[col].to_numpy()).sum()) for col in HISTORIA}
    comprobar("Muestra: las seis variables de la historia iguales, recorriendo egreso por egreso", not any(malas.values()),
              f"({fmt(len(muestra))} casos" + "".join(f"; {col}: {k} distintos" for col, k in malas.items() if k) + ")")
    bordes_ok = {nombre: int(filtro_borde[res["ID_EGRESO"].isin(muestra)].sum()) for nombre, filtro_borde in bordes.items()}
    print("  casos de borde en la muestra:", bordes_ok, flush=True)

    # Coherencia de la historia en toda la tabla
    sin_previas = res["HOSP_PREVIAS"] == 0
    comprobar(f"Toda la tabla: DIAS_ULTIMA_HOSP vale {sin_hosp} solo sin hospitalizaciones previas, y las no planificadas no superan al total",
              bool((res.loc[sin_previas, "DIAS_ULTIMA_HOSP"] == sin_hosp).all() and res.loc[~sin_previas, "DIAS_ULTIMA_HOSP"].between(0, ventana).all()
                   and (res["HOSP_PREVIAS_NO_PLANIF"] <= res["HOSP_PREVIAS"]).all()))

    # ---------------------------------------------------------------- reporte
    todo_bien = all(ok for _, ok in resultados)
    print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
    filas_ej = []
    for id_caso in EJEMPLOS:
        a, b = res.set_index("ID_EGRESO").loc[id_caso], calc.loc[id_caso]
        filas_ej.append(f"| `{id_caso}` | " + " | ".join(f"{fmt(a[c])} / {fmt(b[c])}" for c in ["HOSP_PREVIAS", "HOSP_PREVIAS_NO_PLANIF",
                                                                                                "DIAS_ULTIMA_HOSP", "CMA_PREVIAS"]) + " |")
    ruta = ACTIVIDAD.name
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente de las variables de los casos de estudio",
        f"Generado por `{ruta}/pruebas/verificar_15_variables_casos.py` el {date.today():%d-%m-%Y}. El programa vuelve a calcular, "
        "sin usar ninguna función del script 15, lo que el script dejó en `data/processed/variables_casos.parquet`. Compara las tablas "
        "de reglas con una segunda transcripción (los códigos de comorbilidad, con los rangos de Quan et al., 2005); recalcula con "
        "pyarrow, para todos los casos, las variables que no dependen de la historia, y arma la historia de 12 meses recorriendo uno "
        f"por uno los egresos de cada persona en una muestra de {fmt(len(muestra))} casos ({TAMANO_MUESTRA} al azar con la semilla "
        f"{SEMILLA}, los ejemplos del reporte 15 y casos en los bordes de la ventana). Solo lee el conjunto de desarrollo.",
        f"Partición probada: versión {registro['version']}, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
        "Casos de borde incluidos en la muestra: " + "; ".join(f"{k}: {fmt(v)}" for k, v in bordes_ok.items()) + ".",
        "Los ejemplos del reporte 15 (script / recálculo):",
        "\n".join(["| Caso | Hospitalizaciones previas | No planificadas | Días desde la última | Cirugías ambulatorias |",
                   "|---|---|---|---|---|", *filas_ej]),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
