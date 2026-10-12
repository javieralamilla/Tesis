"""Contraste independiente del script 10 (partición y reserva del conjunto de prueba).

Comprueba, sin usar ninguna función del script 10, que la partición cumple lo que se exige de ella:
ningún paciente está en los dos conjuntos, los dos archivos contienen exactamente los egresos del
conjunto analítico sin cambiar ninguna celda, la partición se puede reproducir a partir de la
semilla (se vuelve a calcular con un programa escrito de otra forma), los archivos tienen el hash
registrado y las cifras del reporte 10 coinciden con el recálculo. Solo lee los datos; con las
rutas por defecto deja reportes/pruebas_independientes.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.3_validacion_particion\\pruebas\\verificar_10_particion.py

Para contrastar una prueba en seco se indica la carpeta que tiene sus salidas:
    ... verificar_10_particion.py <carpeta>

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import os
import re
import sys
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
CONJUNTO = RAIZ / "data" / "processed" / "grd_etiquetado.parquet"
VERSION_CONJUNTO = RAIZ / "docs" / "version_conjunto_analitico.csv"
if len(sys.argv) > 1:                            # salidas de una prueba en seco, todas en una carpeta
    BASE = Path(sys.argv[1])
    PARTICION, IDENTIFICADORES, DESARROLLO = BASE / "particion.parquet", BASE / "particion_identificadores.parquet", BASE / "desarrollo.parquet"
    PRUEBA, REPORTE_10, REGISTRO, SALIDA = BASE / "reserva" / "prueba.parquet", BASE / "10_particion.md", BASE / "version_particion.csv", None
else:
    PARTICION = RAIZ / "data" / "processed" / "particion.parquet"
    IDENTIFICADORES = RAIZ / "data" / "processed" / "particion_identificadores.parquet"
    DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
    PRUEBA = RAIZ / "data" / "reserva" / "prueba.parquet"
    REPORTE_10 = ACTIVIDAD / "reportes" / "10_particion.md"
    REGISTRO = RAIZ / "docs" / "version_particion.csv"
    SALIDA = ACTIVIDAD / "reportes" / "pruebas_independientes.md"
ARCHIVOS = {"DESARROLLO": DESARROLLO, "PRUEBA": PRUEBA}
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
inicio = time.time()
resultados = []


def comprobar(nombre: str, cumple, detalle: str = "") -> None:
    resultados.append((f"{nombre} {detalle}".rstrip(), bool(cumple)))
    print(f"[{'OK' if cumple else 'FALLA'}] {nombre} {detalle}".rstrip(), flush=True)


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


par = {r["parametro"]: r["valor"].strip() for r in leer_csv(ACTIVIDAD / "reglas" / "parametros.csv")}
SEMILLA, UNA_DE_CADA, PRINCIPAL = int(par["semilla"]), int(par["prueba_una_de_cada"]), par["variable_principal"]

# ------------------------------------------------------------------ 1. versiones y sello
version = leer_csv(VERSION_CONJUNTO)[-1]
registro = leer_csv(REGISTRO)[-1]
hash_conjunto = sha256(CONJUNTO)
comprobar("El conjunto analítico es el de la última versión registrada", hash_conjunto == version["sha256"], f"(versión {version['version']})")
comprobar("La partición se hizo sobre esa versión del conjunto analítico", registro["sha256_conjunto"] == hash_conjunto)
comprobar("El conjunto de prueba tiene el hash registrado: no cambió desde que se apartó", sha256(PRUEBA) == registro["sha256_prueba"])
comprobar("El conjunto de desarrollo y la lista de identificadores tienen el hash registrado",
          sha256(DESARROLLO) == registro["sha256_desarrollo"] and sha256(IDENTIFICADORES) == registro["sha256_identificadores"])
comprobar("El archivo del conjunto de prueba es de solo lectura", not os.access(PRUEBA, os.W_OK))

# ------------------------------------------------------------------ 2. ningún paciente en los dos conjuntos
columnas = ["ID_EGRESO", "ID_PACIENTE", "ID_PERSONA", "BLOQUE_ID", "ES_CASO_ESTUDIO", *VARIABLES]
d = pq.read_table(CONJUNTO, columns=columnas).to_pandas()
partes = {c: pq.read_table(ruta, columns=columnas).to_pandas() for c, ruta in ARCHIVOS.items()}
des, pru = partes["DESARROLLO"], partes["PRUEBA"]
for columna, nombre in (("ID_PACIENTE", "Ningún identificador de paciente"), ("ID_PERSONA", "Ninguna persona"), ("ID_EGRESO", "Ningún egreso")):
    comunes = np.intersect1d(des[columna].dropna().unique(), pru[columna].dropna().unique())
    comprobar(f"{nombre} está en los dos conjuntos", len(comunes) == 0,
              f"({des[columna].nunique()} en desarrollo y {pru[columna].nunique()} en prueba)")
con_persona = d[d["ID_PERSONA"].notna()]
comprobar("Ningún identificador de paciente aparece en los dos bloques", int(con_persona.groupby("ID_PACIENTE")["BLOQUE_ID"].nunique().max()) == 1)

# ------------------------------------------------------------------ 3. los dos archivos son el conjunto analítico, repartido
ids = pq.read_table(CONJUNTO, columns=["ID_EGRESO"]).column(0)
en = {c: pc.is_in(ids, value_set=pa.array(partes[c]["ID_EGRESO"].to_numpy())) for c in ARCHIVOS}
comprobar("Los dos conjuntos reúnen exactamente los egresos con persona del conjunto analítico",
          np.array_equal(np.sort(np.concatenate([des["ID_EGRESO"].to_numpy(), pru["ID_EGRESO"].to_numpy()])), np.sort(con_persona["ID_EGRESO"].to_numpy())),
          f"({len(des)} + {len(pru)} = {len(con_persona)}; quedan fuera {len(d) - len(con_persona)} sin persona)")
comprobar("Todos los casos de estudio están en uno de los dos conjuntos",
          int(des["ES_CASO_ESTUDIO"].sum()) + int(pru["ES_CASO_ESTUDIO"].sum()) == int(d["ES_CASO_ESTUDIO"].sum()))
nombres = pq.read_schema(CONJUNTO).names
comprobar("Los dos archivos tienen las mismas columnas que el conjunto analítico, en el mismo orden",
          all(pq.read_schema(ruta).names == nombres for ruta in ARCHIVOS.values()), f"({len(nombres)} columnas)")
distintas = []
for columna in nombres:
    original = pq.read_table(CONJUNTO, columns=[columna]).column(0)
    for c, ruta in ARCHIVOS.items():
        if not original.filter(en[c]).equals(pq.read_table(ruta, columns=[columna]).column(0)):
            distintas.append((c, columna))
comprobar(f"Las {len(nombres)} columnas de cada archivo son idénticas, celda a celda, a las del conjunto analítico", not distintas, str(distintas[:5]) if distintas else "")

# ------------------------------------------------------------------ 4. lista de identificadores y conjunto de cada egreso
lista = pq.read_table(IDENTIFICADORES).to_pandas()
comprobar("La lista tiene una fila por identificador de paciente con persona", lista["ID_PACIENTE"].is_unique and len(lista) == con_persona["ID_PACIENTE"].nunique(),
          f"({len(lista)} identificadores)")
comprobar("La lista de identificadores coincide con los identificadores de cada archivo",
          all(set(lista.loc[lista["CONJUNTO"] == c, "ID_PACIENTE"]) == set(partes[c]["ID_PACIENTE"].astype("int64")) for c in ARCHIVOS))
comprobar("La lista solo tiene el identificador, su bloque y su conjunto (nada que dependa de las variables objetivo)",
          list(lista.columns) == ["ID_PACIENTE", "BLOQUE_ID", "CONJUNTO"])
llave = pq.read_table(PARTICION).to_pandas()
comprobar("particion.parquet indica el mismo conjunto que los archivos para cada egreso",
          all(set(llave.loc[llave["CONJUNTO"] == c, "ID_EGRESO"]) == set(partes[c]["ID_EGRESO"]) for c in ARCHIVOS) and len(llave) == len(con_persona))

# ------------------------------------------------------------------ 5. la partición se reproduce a partir de la semilla
# Se vuelve a calcular con otra implementación: conteos con bincount y un recorrido estrato por estrato.
codigo, identificador = pd.factorize(con_persona["ID_PACIENTE"].astype("int64"), sort=True)          # identificadores en orden creciente
n_id = len(identificador)
caso = con_persona["ES_CASO_ESTUDIO"].to_numpy()
casos_id = np.bincount(codigo[caso], minlength=n_id)
reingresos = {k: np.bincount(codigo[caso], weights=con_persona.loc[caso, k].fillna(0).to_numpy(), minlength=n_id).astype("int64") for k in VARIABLES}
bloque_id = np.empty(n_id, dtype=object)
bloque_id[codigo] = con_persona["BLOQUE_ID"].to_numpy()
tiene = {k: reingresos[k] > 0 for k in VARIABLES}
tiene["REING_30D"] |= tiene["REING_7D"]                    # un reingreso a 7 días también lo es a 30
tiene["REING_30D_CDM"] |= tiene["REING_7D_CDM"]
patron = ["sin casos" if casos_id[i] == 0 else "".join("1" if tiene[k][i] else "0" for k in ("REING_30D", "REING_30D_CDM", "REING_7D", "REING_7D_CDM"))
          for i in range(n_id)]
rng = np.random.default_rng(SEMILLA)
azar = rng.random(n_id)
estratos = sorted(set(zip(bloque_id.tolist(), patron)))
partida = rng.integers(0, UNA_DE_CADA, len(estratos))
miembros = {e: [] for e in estratos}
for i, clave in enumerate(zip(bloque_id.tolist(), patron)):
    miembros[clave].append(i)
a_prueba = np.zeros(n_id, dtype=bool)
for numero, e in enumerate(estratos):
    fila = np.array(miembros[e])
    orden = fila[np.lexsort((azar[fila], casos_id[fila], reingresos[PRINCIPAL][fila]))]      # por reingresos, luego casos, luego azar
    a_prueba[orden[(np.arange(len(orden)) + partida[numero]) % UNA_DE_CADA == 0]] = True
recalculado = pd.Series(np.where(a_prueba, "PRUEBA", "DESARROLLO"), index=identificador)
comprobar(f"La partición se reproduce con la semilla {SEMILLA}: el recálculo asigna cada identificador al mismo conjunto",
          (recalculado.reindex(lista["ID_PACIENTE"]).to_numpy() == lista["CONJUNTO"].to_numpy()).all(),
          f"({len(estratos)} estratos; {int(a_prueba.sum())} identificadores a prueba)")

# ------------------------------------------------------------------ 6. tamaño, tasas y reporte
casos = {c: partes[c][partes[c]["ES_CASO_ESTUDIO"]] for c in ARCHIVOS}
total = sum(len(v) for v in casos.values())
parte_prueba = 100 * len(casos["PRUEBA"]) / total
comprobar(f"El conjunto de prueba tiene cerca del {100 / UNA_DE_CADA:.0f} % de los casos de estudio", abs(parte_prueba - 100 / UNA_DE_CADA) < 0.5,
          f"({len(casos['DESARROLLO'])} en desarrollo y {len(casos['PRUEBA'])} en prueba: {parte_prueba:.3f} %)".replace(".", ","))
tasas = {k: {c: (int(casos[c][k].notna().sum()), int((casos[c][k] == 1).sum())) for c in ARCHIVOS} for k in VARIABLES}
diferencias = {k: 100 * t["PRUEBA"][1] / t["PRUEBA"][0] - 100 * t["DESARROLLO"][1] / t["DESARROLLO"][0] for k, t in tasas.items()}
comprobar("La tasa de cada variable objetivo difiere en menos de 0,05 puntos porcentuales entre los dos conjuntos", max(abs(v) for v in diferencias.values()) < 0.05,
          "(" + "; ".join(f"{k} {v:+.3f}".replace(".", ",") for k, v in diferencias.items()) + ")")
if REPORTE_10.exists():
    del_reporte = {}
    for linea in REPORTE_10.read_text(encoding="utf-8").split("## 3.")[1].split("## 4.")[0].splitlines():
        m = re.match(r"\| `(REING_\w+)` \| .* \| ([\d.]+) \| ([\d,]+) % \| ([\d.]+) \| ([\d,]+) % \|", linea)
        if m:
            del_reporte[m[1]] = (int(m[2].replace(".", "")), float(m[3].replace(",", ".")), int(m[4].replace(".", "")), float(m[5].replace(",", ".")))
    esperado = {k: (t["DESARROLLO"][0], round(100 * t["DESARROLLO"][1] / t["DESARROLLO"][0], 3), t["PRUEBA"][0], round(100 * t["PRUEBA"][1] / t["PRUEBA"][0], 3))
                for k, t in tasas.items()}
    comprobar(f"La tabla de tasas de {REPORTE_10.name} coincide con el recálculo", del_reporte == esperado,
              f"(reporte {del_reporte}; recalculado {esperado})" if del_reporte != esperado else "")

todo_bien = all(ok for _, ok in resultados)
print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
if SALIDA is not None:
    ruta = ACTIVIDAD.name
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente de la actividad 2.3",
        f"Generado por `{ruta}/pruebas/verificar_10_particion.py` el {date.today():%d-%m-%Y}. El programa comprueba la partición sin usar "
        "ninguna función del script 10: que ningún paciente esté en los dos conjuntos, que los archivos sean el conjunto analítico "
        "repartido sin cambios, que la partición se reproduzca a partir de la semilla y que los archivos tengan el hash registrado.",
        f"Partición probada: versión {registro['version']}, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`, sobre la versión "
        f"{version['version']} del conjunto analítico. SHA-256 del conjunto de prueba: `{registro['sha256_prueba']}`.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
sys.exit(0 if todo_bien else 1)
