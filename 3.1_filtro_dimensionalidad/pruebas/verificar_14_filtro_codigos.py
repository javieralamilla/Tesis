"""Prueba independiente del filtro de dimensionalidad (actividad 3.1, script 14).

Vuelve a calcular, sin usar ninguna función del script 14 y por otro camino, lo que el script dejó en
data/processed/filtro_codigos.parquet y en reportes/14_codigos_retenidos.csv:

  1. Versión y archivos. El conjunto de desarrollo es el registrado y los archivos del script tienen las
     columnas esperadas, sin identificadores de egresos ni de pacientes.
  2. Totales. Los casos de estudio, los casos con dato y los reingresos de cada variable, y los códigos
     distintos de cada bloque, contados directamente con pyarrow.
  3. Muestra de códigos. Para 300 códigos al azar, los que quedaron justo en el límite de los umbrales
     y cinco ejemplos conocidos, marca los casos que tienen el código revisando columna por columna
     (sin la tabla larga del script) y calcula la V como la correlación entre dos columnas de ceros y
     unos. Compara casos, reingresos, tasas, chi-cuadrado, V, valor p (con la distribución normal),
     dirección, decisión y descripción (leída con openpyxl).
  4. Tabla completa y lista. En todos los códigos: la tasa sin el código cuadra con los totales, la V
     con el chi-cuadrado y la decisión con los umbrales; la lista tiene exactamente los que pasan.
  5. Listas (D53). La regla de la lista C en toda la tabla; las cuatro listas de todo desarrollo; para
     una muestra de categorías de diagnóstico, sus casos y reingresos marcando los casos que tienen
     algún código de la categoría, columna por columna; y para una muestra de códigos (sobre todo los
     que cambian entre pliegues), las listas de cada pliegue, contando directamente los casos de
     entrenamiento de ese pliegue (todos los casos con dato menos los del pliegue).

Solo lee el conjunto de desarrollo; con las rutas por defecto deja reportes/pruebas_filtro_codigos.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\pruebas\\verificar_14_filtro_codigos.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import math
import sys
import time
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
from openpyxl import load_workbook

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
RESULTADO = RAIZ / "data" / "processed" / "filtro_codigos.parquet"
LISTAS = RAIZ / "data" / "processed" / "listas_codigos.parquet"
GRUPOS = RAIZ / "data" / "processed" / "validacion_temporal.parquet"
REPORTE_14 = ACTIVIDAD / "reportes" / "14_filtro_codigos.md"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
DIR_TABLAS = RAIZ.parent / "Datos" / "Tablas auxiliares"
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
LISTA = ACTIVIDAD / "reportes" / "14_codigos_retenidos.csv"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_filtro_codigos.md"
COLUMNAS = {"DIAGNOSTICO": [f"DIAGNOSTICO{i}" for i in range(1, 36)],
            "PROCEDIMIENTO": [f"PROCEDIMIENTO{i}" for i in range(1, 31)]}
TABLAS = {"DIAGNOSTICO": "CIE-10.xlsx", "PROCEDIMIENTO": "CIE-9.xlsx"}
COLUMNAS_RESULTADO = ["VARIABLE", "BLOQUE", "NIVEL", "CODIGO", "DESCRIPCION", "CASOS", "REINGRESOS", "TASA_CON_CODIGO",
                      "TASA_SIN_CODIGO", "CHI2", "VALOR_P", "V", "DIRECCION", "RIESGO_RELATIVO", "PASA", "PASA_C"]
COLUMNAS_LISTA = ["VARIABLE", "BLOQUE", "CODIGO", "DESCRIPCION", "CASOS", "REINGRESOS", "TASA_CON_CODIGO", "TASA_SIN_CODIGO",
                  "V", "DIRECCION"]
COLUMNAS_LISTAS = ["VARIABLE", "LISTA", "PLIEGUE", "BLOQUE", "NIVEL", "CODIGO"]
CATEGORIAS_EJEMPLO = ["R57", "C79", "J84", "D61"]
TAMANO_MUESTRA_CATEGORIAS = 20
TAMANO_MUESTRA_PLIEGUES = 60
EJEMPLOS = ["N18.5", "K80.2", "U07.1", "Z37.0", "D61.3"]
TAMANO_MUESTRA = 300
SEMILLA = 2026
resultados = []


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


def dec(x, decimales: int = 6) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def iguales(a, b, rtol: float = 1e-9, atol: float = 1e-12) -> bool:
    """Compara dos listas de números con una tolerancia mínima (los decimales del computador no son exactos)."""
    return bool(np.allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float), rtol=rtol, atol=atol, equal_nan=True))


def main() -> None:
    inicio = time.time()
    par = {fila["parametro"]: fila["valor"].strip() for fila in leer_csv(PARAMETROS)}
    variables = [v for v in par["variables_objetivo"].split("|") if v]
    v_min = float(par["v_minima"].replace(",", "."))
    n_min = int(par["casos_minimos"])

    # ---------------------------------------------------------------- 1. versión y archivos
    registro = leer_csv(REGISTRO)[-1]
    comprobar(f"El conjunto de desarrollo tiene el hash de la versión {registro['version']} registrada de la partición",
              sha256(DESARROLLO) == registro["sha256_desarrollo"])
    todo_niveles = pd.read_parquet(RESULTADO)
    lista = pd.read_csv(LISTA, sep=";", decimal=",", encoding="utf-8-sig", dtype={"CODIGO": str})
    listas = pd.read_parquet(LISTAS)
    comprobar("filtro_codigos.parquet tiene las columnas esperadas, sin identificadores de egresos ni de pacientes",
              list(todo_niveles.columns) == COLUMNAS_RESULTADO)
    comprobar("La lista fija (A) y listas_codigos.parquet tienen las columnas esperadas",
              list(lista.columns) == COLUMNAS_LISTA and list(listas.columns) == COLUMNAS_LISTAS)
    todo = todo_niveles[todo_niveles["NIVEL"] == "COMPLETO"].reset_index(drop=True)   # códigos completos

    # ---------------------------------------------------------------- 2. totales contados directamente
    t = pq.read_table(DESARROLLO, columns=["ID_EGRESO", *variables, *COLUMNAS["DIAGNOSTICO"], *COLUMNAS["PROCEDIMIENTO"]],
                      filters=[("ES_CASO_ESTUDIO", "==", True)])
    comprobar("Se leen tantos casos de estudio como los registrados en la partición",
              t.num_rows == int(registro["casos_desarrollo"]), f"({fmt(t.num_rows)} casos)")
    con_dato = {k: pc.is_valid(t[k]).to_numpy(zero_copy_only=False) for k in variables}
    reingresa = {k: pc.fill_null(pc.equal(t[k], 1), False).to_numpy(zero_copy_only=False) for k in variables}
    N = {k: int(con_dato[k].sum()) for k in variables}    # casos con dato en cada variable
    R = {k: int(reingresa[k].sum()) for k in variables}   # reingresos de cada variable
    distintos = {b: set().union(*(pc.unique(t[c]).drop_null().to_pylist() for c in columnas))
                 for b, columnas in COLUMNAS.items()}
    filas_ok = all(((todo["VARIABLE"] == k) & (todo["BLOQUE"] == b)).sum() == len(distintos[b])
                   and set(todo.loc[(todo["VARIABLE"] == k) & (todo["BLOQUE"] == b), "CODIGO"]) == distintos[b]
                   for k in variables for b in COLUMNAS)
    comprobar("Cada variable tiene una fila por código distinto de cada bloque, contados columna por columna", filas_ok,
              f"({fmt(len(distintos['DIAGNOSTICO']))} diagnósticos y {fmt(len(distintos['PROCEDIMIENTO']))} procedimientos)")

    # ---------------------------------------------------------------- 3. muestra de códigos, por otro camino
    rng = np.random.default_rng(SEMILLA)
    todos = [(b, c) for b in COLUMNAS for c in sorted(distintos[b])]
    muestra = {todos[i] for i in rng.choice(len(todos), TAMANO_MUESTRA, replace=False)}
    muestra |= {("DIAGNOSTICO", c) for c in EJEMPLOS}
    for k in variables:  # los que quedaron justo en el límite de alguno de los dos umbrales, a cada lado
        sub = todo[todo["VARIABLE"] == k]
        con_n, con_v = sub[sub["CASOS"] >= n_min], sub[sub["V"] >= v_min]
        for parte in (con_n[con_n["V"] >= v_min].nsmallest(5, "V"), con_n[con_n["V"] < v_min].nlargest(5, "V"),
                      con_v[con_v["CASOS"] >= n_min].nsmallest(5, "CASOS"), con_v[con_v["CASOS"] < n_min].nlargest(5, "CASOS")):
            muestra |= set(zip(parte["BLOQUE"], parte["CODIGO"]))
    print(f"Recalculando {len(muestra)} códigos...", flush=True)

    # De cada columna se guardan solo las filas que tienen un código, y el código: así cada comparación
    # recorre menos datos (la columna DIAGNOSTICO30, por ejemplo, está casi siempre vacía).
    no_vacias = {b: [(np.flatnonzero(pc.is_valid(t[c]).to_numpy(zero_copy_only=False)), t[c].drop_null()) for c in columnas]
                 for b, columnas in COLUMNAS.items()}
    filas = []
    for i, (b, codigo) in enumerate(sorted(muestra), start=1):
        tiene = np.zeros(t.num_rows, dtype=bool)  # casos que tienen el código en alguna de sus columnas
        for filas_columna, codigos_columna in no_vacias[b]:
            tiene[filas_columna[pc.equal(codigos_columna, codigo).to_numpy(zero_copy_only=False)]] = True
        if i % 50 == 0:
            print(f"  {i} de {len(muestra)} códigos ({time.time() - inicio:.0f} s)", flush=True)
        for k in variables:
            x = tiene[con_dato[k]].astype(float)          # 1 si el caso tiene el código
            y = reingresa[k][con_dato[k]].astype(float)   # 1 si el caso reingresa
            n1, a = int(x.sum()), int(x @ y)
            v = abs(np.corrcoef(x, y)[0, 1]) if 0 < n1 < len(x) else 0.0  # en una tabla de 2×2, V = |correlación|
            filas.append({"VARIABLE": k, "BLOQUE": b, "CODIGO": codigo, "CASOS": n1, "REINGRESOS": a, "V": v,
                          "TASA_CON_CODIGO": 100 * a / n1 if n1 else np.nan,
                          "TASA_SIN_CODIGO": 100 * (R[k] - a) / (N[k] - n1), "CHI2": N[k] * v * v})
    calc = pd.DataFrame(filas)
    ref = todo.set_index(["VARIABLE", "BLOQUE", "CODIGO"]).loc[pd.MultiIndex.from_frame(calc[["VARIABLE", "BLOQUE", "CODIGO"]])]

    detalle = f"({len(muestra)} códigos × {len(variables)} variables)"
    comprobar("Muestra: casos y reingresos iguales a los del script",
              (ref["CASOS"].to_numpy() == calc["CASOS"].to_numpy()).all()
              and (ref["REINGRESOS"].to_numpy() == calc["REINGRESOS"].to_numpy()).all(), detalle)
    comprobar("Muestra: tasas de reingreso con el código y sin él iguales",
              iguales(ref["TASA_CON_CODIGO"], calc["TASA_CON_CODIGO"]) and iguales(ref["TASA_SIN_CODIGO"], calc["TASA_SIN_CODIGO"]))
    comprobar("Muestra: V igual a la correlación entre «tiene el código» y «reingresa»", iguales(ref["V"], calc["V"], rtol=1e-8))
    comprobar("Muestra: chi-cuadrado igual a N · V²", iguales(ref["CHI2"], calc["CHI2"], rtol=1e-8, atol=1e-9))
    # Un chi-cuadrado con 1 grado de libertad es el cuadrado de una normal estándar: p = 2 · (1 − Φ(raíz(chi²))).
    # Con chi-cuadrados grandes el valor p es tan chico que la resta pierde precisión; se comparan los menores que 40.
    chicos = calc["CHI2"].to_numpy() < 40
    p_normal = [2 * (1 - NormalDist().cdf(math.sqrt(x))) for x in calc["CHI2"].to_numpy()[chicos]]
    comprobar("Muestra: valor p igual al calculado con la distribución normal (chi-cuadrado menor que 40)",
              iguales(ref["VALOR_P"].to_numpy()[chicos], p_normal, rtol=1e-6), f"({int(chicos.sum())} filas)")
    direccion = np.select([calc["CASOS"] == 0, calc["TASA_CON_CODIGO"] > calc["TASA_SIN_CODIGO"],
                           calc["TASA_CON_CODIGO"] < calc["TASA_SIN_CODIGO"]], ["sin casos", "sube", "baja"], default="igual")
    pasa = ((calc["CASOS"] >= n_min) & (calc["V"] >= v_min)).to_numpy()
    comprobar("Muestra: dirección (sube o baja) y decisión (pasa o no) iguales",
              (ref["DIRECCION"].to_numpy() == direccion).all() and (ref["PASA"].to_numpy() == pasa).all(),
              f"({int(pasa.sum())} filas pasan)")
    descripciones = {}
    for b, archivo in TABLAS.items():
        libro = load_workbook(DIR_TABLAS / archivo, read_only=True)
        filas_xl = libro.active.iter_rows(values_only=True)
        encabezado = list(next(filas_xl))
        i_cod, i_desc = encabezado.index("Código"), encabezado.index("Descripción")
        descripciones[b] = {str(f[i_cod]).strip(): " ".join(str(f[i_desc] or "").split()) for f in filas_xl if f[i_cod] is not None}
        libro.close()
    esperada = np.array([descripciones[b].get(c, "") for b, c in zip(calc["BLOQUE"], calc["CODIGO"])])
    comprobar("Muestra: descripciones iguales a las de las tablas del DEIS (leídas con openpyxl)",
              (ref["DESCRIPCION"].to_numpy() == esperada).all())

    # ---------------------------------------------------------------- 4. tabla completa y lista
    cuadra, v_ok = True, True
    for k in variables:
        sub = todo[todo["VARIABLE"] == k]
        cuadra &= iguales(sub["TASA_SIN_CODIGO"], 100 * (R[k] - sub["REINGRESOS"]) / (N[k] - sub["CASOS"]))
        v_ok &= iguales(sub["V"], np.sqrt(sub["CHI2"] / N[k]), rtol=1e-12) and bool(sub["V"].between(0, 1).all())
    comprobar("Todos los códigos: la tasa sin el código cuadra con los casos con dato y los reingresos de cada variable", cuadra,
              "(" + "; ".join(f"{k}: {fmt(N[k])} casos con dato y {fmt(R[k])} reingresos" for k in variables) + ")")
    comprobar("Todos los códigos: la V es raíz(chi-cuadrado / N) y está entre 0 y 1", v_ok)
    pasa_todo = (todo["CASOS"] >= n_min) & (todo["V"] >= v_min)
    comprobar("Todos los códigos: pasan exactamente los que cumplen los dos umbrales",
              bool((todo["PASA"] == pasa_todo).all()), f"({int(pasa_todo.sum())} filas)")
    clave = ["VARIABLE", "BLOQUE", "CODIGO", "CASOS", "REINGRESOS"]
    de_lista = set(map(tuple, lista[clave].astype(str).to_numpy()))
    de_tabla = set(map(tuple, todo.loc[pasa_todo, clave].astype(str).to_numpy()))
    por_variable = lista["VARIABLE"].value_counts().reindex(variables, fill_value=0)
    comprobar("La lista tiene exactamente los códigos que pasan, con los mismos casos y reingresos",
              len(lista) == len(de_lista) and de_lista == de_tabla,
              f"({fmt(len(lista))} filas: " + ", ".join(f"{k} {fmt(n)}" for k, n in por_variable.items()) + ")")
    procedimientos = lista.loc[lista["BLOQUE"] == "PROCEDIMIENTO", "CODIGO"]
    comprobar("En la lista, los códigos de procedimiento conservan el cero inicial (dos dígitos antes del punto)",
              bool(procedimientos.str.fullmatch(r"\d\d(\.\d{1,2})?").all()))

    # ---------------------------------------------------------------- 5. listas de todo desarrollo y de cada pliegue (D53)
    riesgo = float(par["efecto_grande_riesgo"].replace(",", "."))
    p_max = float(par["efecto_grande_p"].replace(",", "."))
    pedidas = ["A", *[x.strip().upper() for x in par["listas_comparacion"].split("|") if x.strip()]]

    def regla_c(casos, chi2, tasa_con, tasa_sin, pasa_a):
        """Regla de la lista C, con el valor p de la distribución normal y el riesgo como cociente de las tasas."""
        p = np.array([2 * (1 - NormalDist().cdf(math.sqrt(x))) for x in np.asarray(chi2, dtype=float)])
        rr = np.where(np.asarray(tasa_sin) > 0, np.asarray(tasa_con, dtype=float) / np.where(np.asarray(tasa_sin) > 0, tasa_sin, 1), np.nan)
        grande = ((rr >= riesgo) | (rr <= 1 / riesgo)) & (p < p_max)
        return (np.asarray(casos) >= n_min) & (np.asarray(pasa_a) | grande)

    tn = todo_niveles
    pasa_a_tn = (tn["CASOS"] >= n_min) & (tn["V"] >= v_min)
    pasa_c_tn = regla_c(tn["CASOS"], tn["CHI2"], tn["TASA_CON_CODIGO"], tn["TASA_SIN_CODIGO"], pasa_a_tn)
    comprobar(f"Toda la tabla: PASA_C es la regla de la lista C (la A, o riesgo {dec(riesgo, 1)} veces mayor o menor con valor p menor "
              f"que {dec(p_max, 3)}, con al menos {n_min} casos)", bool((tn["PASA_C"].to_numpy() == pasa_c_tn).all()),
              f"({int(pasa_c_tn[tn['NIVEL'] == 'COMPLETO'].sum())} filas de códigos completos)")
    clave_l = ["VARIABLE", "BLOQUE", "NIVEL", "CODIGO"]

    def claves(df: pd.DataFrame) -> set:
        return set(map(tuple, df[clave_l].astype(str).to_numpy().tolist()))
    completo, categoria = tn["NIVEL"] == "COMPLETO", tn["NIVEL"] == "CATEGORIA"
    esperado0 = {"A": tn[completo & pasa_a_tn], "C": tn[completo & pasa_c_tn],
                 "AGRUPADA": tn[((categoria & (tn["BLOQUE"] == "DIAGNOSTICO")) | (completo & (tn["BLOQUE"] == "PROCEDIMIENTO"))) & pasa_a_tn],
                 "SIN_FILTRO": tn[completo & (tn["CASOS"] >= n_min)]}
    malas0 = [x for x in pedidas if claves(listas[(listas["LISTA"] == x) & (listas["PLIEGUE"] == 0)]) != claves(esperado0[x])]
    comprobar("Listas de todo desarrollo: cada una tiene exactamente los códigos de su regla", not malas0,
              "(" + "; ".join(f"{x}: {fmt(len(esperado0[x]))} filas" for x in pedidas) + (f"; distintas: {malas0}" if malas0 else "") + ")")

    # Categorías de diagnóstico: casos que tienen algún código que empieza con la categoría, columna por columna.
    cats = sorted(set(tn.loc[categoria, "CODIGO"]))
    muestra_cat = set(CATEGORIAS_EJEMPLO) & set(cats)
    muestra_cat |= {cats[i] for i in rng.choice(len(cats), min(TAMANO_MUESTRA_CATEGORIAS, len(cats)), replace=False)}
    ref_cat = tn[categoria].set_index(["VARIABLE", "CODIGO"])
    malas_cat = 0
    for cat in sorted(muestra_cat):
        tiene = np.zeros(t.num_rows, dtype=bool)
        for filas_columna, codigos_columna in no_vacias["DIAGNOSTICO"]:
            tiene[filas_columna[pc.starts_with(codigos_columna, cat).to_numpy(zero_copy_only=False)]] = True
        for k in variables:
            n1, a = int((tiene & con_dato[k]).sum()), int((tiene & reingresa[k]).sum())
            malas_cat += int((ref_cat.loc[(k, cat), "CASOS"], ref_cat.loc[(k, cat), "REINGRESOS"]) != (n1, a))
    comprobar("Muestra de categorías de diagnóstico: casos y reingresos iguales, marcando columna por columna", malas_cat == 0,
              f"({len(muestra_cat)} categorías × {len(variables)} variables, entre ellas {', '.join(sorted(set(CATEGORIAS_EJEMPLO) & muestra_cat))})")

    # Listas de cada pliegue: para una muestra de códigos se cuentan directamente los casos de entrenamiento (con dato y fuera
    # del pliegue), y se decide si pasan las reglas de la A y de la C.
    pliegue_de = pd.read_parquet(GRUPOS, columns=["ID_EGRESO", "PLIEGUE"]).set_index("ID_EGRESO")["PLIEGUE"]
    pliegue = pliegue_de.reindex(t["ID_EGRESO"].to_numpy()).to_numpy()
    comprobar("Todo caso de estudio tiene su pliegue en validacion_temporal.parquet", not np.isnan(pliegue.astype(float)).any())
    pliegues = sorted(int(f) for f in np.unique(pliegue))
    miembros = {g: set(map(tuple, d[["BLOQUE", "NIVEL", "CODIGO"]].to_numpy().tolist()))
                for g, d in listas[listas["PLIEGUE"] > 0].groupby(["VARIABLE", "LISTA", "PLIEGUE"])}
    # Los códigos que cambian entre pliegues (los más difíciles) y otros al azar con el mínimo de casos.
    inestables = set()
    for (k, nombre, f), cods in miembros.items():
        base = set(map(tuple, listas.loc[(listas["VARIABLE"] == k) & (listas["LISTA"] == nombre) & (listas["PLIEGUE"] == 0),
                                         ["BLOQUE", "NIVEL", "CODIGO"]].to_numpy().tolist()))
        inestables |= set(sorted(base ^ cods)[:3])
    candidatos = sorted(set(map(tuple, tn.loc[tn["CASOS"] >= n_min, ["BLOQUE", "NIVEL", "CODIGO"]].to_numpy().tolist())))
    muestra_pl = inestables | {candidatos[i] for i in rng.choice(len(candidatos), TAMANO_MUESTRA_PLIEGUES, replace=False)}
    print(f"Recalculando las listas de cada pliegue para {len(muestra_pl)} códigos...", flush=True)
    malas_pl, revisadas = [], 0
    for b, nivel, codigo in sorted(muestra_pl):
        tiene = np.zeros(t.num_rows, dtype=bool)
        for filas_columna, codigos_columna in no_vacias[b]:
            iguala = pc.starts_with(codigos_columna, codigo) if nivel == "CATEGORIA" else pc.equal(codigos_columna, codigo)
            tiene[filas_columna[iguala.to_numpy(zero_copy_only=False)]] = True
        for k in variables:
            for f in pliegues:
                entrena = con_dato[k] & (pliegue != f)
                n_e, r_e = int(entrena.sum()), int((entrena & reingresa[k]).sum())
                n1, a = int((tiene & entrena).sum()), int((tiene & entrena & reingresa[k]).sum())
                bb, c, d = n1 - a, r_e - a, (n_e - r_e) - (n1 - a)
                den = n1 * (n_e - n1) * r_e * (n_e - r_e)
                chi2 = n_e * (a * d - bb * c) ** 2 / den if den > 0 else 0.0
                pasa_a = n1 >= n_min and math.sqrt(chi2 / n_e) >= v_min
                pasa_c = bool(regla_c([n1], [chi2], [100 * a / n1 if n1 else np.nan], [100 * c / (n_e - n1)], [pasa_a])[0])
                esperado = {"A": pasa_a and nivel == "COMPLETO", "C": pasa_c and nivel == "COMPLETO",
                            "AGRUPADA": pasa_a and ((b == "DIAGNOSTICO") == (nivel == "CATEGORIA"))}
                for nombre in [x for x in ("A", "C", "AGRUPADA") if x in pedidas]:
                    revisadas += 1
                    if ((b, nivel, codigo) in miembros.get((k, nombre, f), set())) != esperado[nombre]:
                        malas_pl.append(f"{k} {nombre} pliegue {f} {codigo}")
    comprobar("Muestra de códigos: las listas de cada pliegue coinciden con el recálculo con los casos de entrenamiento", not malas_pl,
              f"({len(muestra_pl)} códigos, {fmt(revisadas)} decisiones revisadas, {len(inestables)} de ellos cambian entre pliegues"
              + (f"; distintas: {', '.join(malas_pl[:5])}" if malas_pl else "") + ")")
    if REPORTE_14.exists():
        del_reporte = {}
        for linea in REPORTE_14.read_text(encoding="utf-8").split("## 3.")[1].split("## 4.")[0].splitlines():
            celdas = [x.strip().strip("`") for x in linea.strip().strip("|").split("|")]
            if len(celdas) == len(variables) + 1 and celdas[0] in pedidas:
                del_reporte[celdas[0]] = [int(x.replace(".", "")) for x in celdas[1:]]
        conteo0 = {x: [len(listas[(listas["LISTA"] == x) & (listas["PLIEGUE"] == 0) & (listas["VARIABLE"] == k)]) for k in variables]
                   for x in pedidas}
        comprobar(f"La tabla de listas de {REPORTE_14.name} coincide con listas_codigos.parquet", del_reporte == conteo0,
                  "(" + "; ".join(f"{x}: {' / '.join(fmt(n) for n in v)}" for x, v in conteo0.items()) + ")")

    # ---------------------------------------------------------------- reporte
    todo_bien = all(ok for _, ok in resultados)
    print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
    k_ej = "REING_30D" if "REING_30D" in variables else variables[0]
    ej = calc[(calc["VARIABLE"] == k_ej) & calc["CODIGO"].isin(EJEMPLOS)].set_index("CODIGO").reindex(EJEMPLOS)
    ej_ref = ref.reset_index().query("VARIABLE == @k_ej").set_index("CODIGO").reindex(EJEMPLOS)
    filas_ej = [f"| `{c}` | {fmt(ej_ref.loc[c, 'CASOS'])} / {fmt(ej.loc[c, 'CASOS'])} | "
                f"{fmt(ej_ref.loc[c, 'REINGRESOS'])} / {fmt(ej.loc[c, 'REINGRESOS'])} | "
                f"{dec(ej_ref.loc[c, 'V'])} / {dec(ej.loc[c, 'V'])} |" for c in EJEMPLOS]
    ruta = ACTIVIDAD.name
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente del filtro de dimensionalidad",
        f"Generado por `{ruta}/pruebas/verificar_14_filtro_codigos.py` el {date.today():%d-%m-%Y}. El programa vuelve a calcular, "
        "sin usar ninguna función del script 14, lo que el script dejó en `data/processed/filtro_codigos.parquet` y en "
        f"`{ruta}/reportes/14_codigos_retenidos.csv`. Para una muestra de códigos ({len(muestra)}: {TAMANO_MUESTRA} al azar con la "
        f"semilla {SEMILLA}, los que quedaron justo en el límite de los umbrales y cinco ejemplos conocidos) marca los casos que "
        "tienen el código revisando columna por columna y calcula la V como la correlación entre dos columnas de ceros y unos. "
        "Solo lee el conjunto de desarrollo.",
        f"Partición probada: versión {registro['version']}, registrada el {registro['fecha']} en `docs/{REGISTRO.name}`.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
        f"Los cinco ejemplos con `{k_ej}` (script / recálculo):",
        "\n".join(["| Código | Casos | Reingresos | V |", "|---|---|---|---|", *filas_ej]),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
