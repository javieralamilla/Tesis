"""Prueba independiente del entrenamiento (actividad 3.2, script 17).

Revisa por otro camino lo que el script 17 dejó: las tablas de predicciones fuera de pliegue, una por combinación, y su
registro. Lo que puede rehacerse sin el script se rehace aquí con pandas, sin sus funciones. Para probar la matriz y el
entrenamiento usa las funciones del script, pero compara lo que entregan con lo calculado aquí o con lo que ya guardó.

  1. Versión y parámetros. Las tablas para los modelos son la versión registrada; los valores de D62 y D65 de
     reglas/parametros.csv y las columnas de cada tipo coinciden con una segunda transcripción escrita en este programa.
  2. Predicciones. Cada tabla corresponde a una de las 63 combinaciones de D64, con la ponderación decidida; tiene
     exactamente los casos con dato en su variable, cada uno con su pliegue, y probabilidades entre 0 y 1.
  3. Registro. Cada combinación guardada tiene sus cinco vueltas en reportes/17_registro.csv, con los casos, los
     reingresos, los códigos y las columnas que se recalculan aquí, y la regresión logística llegó a su solución.
  4. Matriz. Para una combinación de cada lista guardada, y en cada vuelta, rearma por otro camino, para 200 casos al azar,
     sus columnas de categorías, sus códigos (con la receta del diccionario de D57) y sus números transformados, y las
     proporciones de las columnas sí/no en el entrenamiento, y los compara con los del script.
  5. Entrenamiento. Repite la primera vuelta de una combinación de XGBoost: con las mismas respuestas debe dar las mismas
     probabilidades guardadas, y también con las respuestas de los casos de validación desordenadas, lo que muestra que el
     modelo nunca las miró.

Solo lee; con las rutas por defecto deja reportes/pruebas_entrenamiento.md.

Uso (desde la carpeta Codigo; en el servidor, con el Python del entorno de D65):
    python 3.2_entrenamiento_modelos/pruebas/verificar_17_entrenamiento.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import importlib.util
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
DATOS = RAIZ / "data" / "processed"
CASOS = DATOS / "modelos_casos.parquet"
CODIGOS = DATOS / "modelos_codigos.parquet"
LISTAS = DATOS / "listas_codigos.parquet"
REGISTRO_TABLAS = RAIZ / "docs" / "version_tablas_modelos.csv"
ARCHIVO_COLUMNAS = RAIZ / "3.1_filtro_dimensionalidad" / "reglas" / "columnas_modelos.csv"
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"
SCRIPT_17 = ACTIVIDAD / "scripts" / "17_entrenar_modelos.py"
REGISTRO = ACTIVIDAD / "reportes" / "17_registro.csv"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_entrenamiento.md"

# Segunda transcripción de D57, D60, D62, D64 y D65 (no se lee de los archivos del script)
VARIABLES = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
MODELOS = ["LR", "RF", "XGB"]
LISTAS_POR_PLIEGUE = {"A", "C", "AGRUPADA"}
LISTAS_FIJAS = {"SIN_FILTRO"}
VARIABLE_ENSAYO = "REING_7D_CDM"
CATEGORIAS = {"SEXO", "PREVISION_GRUPO", "REGION", "TIPO_INGRESO", "CDM", "TIPO_ALTA", "ESPECIALIDAD_INTERVENCION",
              "ESPECIALIDAD", "TIPO_PROCEDENCIA", "SERVICIO_INGRESO", "SERVICIO_ALTA", "PUEBLO_ORIGINARIO",
              "NACIONALIDAD_EXTRANJERA", "HOSPITAL"}
LOG = ["ESTADIA", "PESO_GRD", "HOSP_PREVIAS", "HOSP_PREVIAS_NO_PLANIF", "CMA_PREVIAS", "SESIONES_PREVIAS"]
NUM = ["EDAD", "INDICE_COMORBILIDAD", "DIAS_ULTIMA_HOSP", "N_DIAGNOSTICOS", "N_PROCEDIMIENTOS", "SEVERIDAD", "RIESGO_MORTALIDAD"]
SI_NO = ["UCI_UTI", "TRASLADO", "VENTANA_CORTADA"]
VALORES = {"lr_C": "1", "lr_l1_ratio": "1", "lr_solver": "liblinear", "lr_intercept_scaling": "100",
           "rf_n_estimators": "100", "rf_max_features": "sqrt", "rf_min_samples_split": "10",
           "xgb_n_estimators": "100", "xgb_learning_rate": "0,3", "xgb_max_depth": "6", "xgb_tree_method": "hist"}
MUESTRA = 200
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


def resumen(malas: list[str]) -> str:
    """Cuántas fallan y un ejemplo, sin repetir."""
    malas = sorted(set(malas))
    return "ninguna" if not malas else f"{len(malas)}, por ejemplo {malas[0]}"


def cargar_script():
    spec = importlib.util.spec_from_file_location("script_17", SCRIPT_17)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for nombre in ["RAIZ", "CASOS", "CODIGOS", "LISTAS", "REGISTRO_TABLAS", "ARCHIVO_COLUMNAS", "PARAMETROS", "PARAMETROS_23"]:
        setattr(m, nombre, globals()[nombre])  # el script lee lo mismo que esta prueba
    return m


def descomponer(nombre: str) -> dict | None:
    """REING_30D__XGB__A__con_hospital__sin_ponderar → sus cinco partes; None si el nombre no tiene esa forma."""
    partes = nombre.split("__")
    if len(partes) != 5 or partes[3] not in ("con_hospital", "sin_hospital") or partes[4] not in ("ponderado", "sin_ponderar"):
        return None
    return {"variable": partes[0], "modelo": partes[1], "lista": partes[2], "hospital": partes[3] == "con_hospital",
            "ponderar": partes[4] == "ponderado"}


def combinacion_valida(c: dict, ponderar: dict) -> bool:
    """Las combinaciones de D64: el ensayo (con y sin ponderación) y las demás con la ponderación decidida (D61)."""
    if c["variable"] not in VARIABLES or c["modelo"] not in MODELOS:
        return False
    if c["variable"] == VARIABLE_ENSAYO and c["lista"] == "A" and c["hospital"]:
        return True
    base = (c["lista"] in LISTAS_POR_PLIEGUE | LISTAS_FIJAS) and (c["hospital"] or c["lista"] == "A")
    return base and c["ponderar"] == ponderar[c["modelo"]]


def main() -> None:
    inicio = time.time()
    m = cargar_script()

    # ---------------------------------------------------------------- 1. versión y parámetros
    version = leer_csv(REGISTRO_TABLAS)[-1]
    iguales = all(sha256(r) == version[c] for r, c in [(CASOS, "sha256_casos"), (CODIGOS, "sha256_codigos"),
                                                       (LISTAS, "sha256_listas_codigos")])
    comprobar("Las tablas para los modelos son la versión registrada", iguales, f"(versión {version['version']})")
    par_texto = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS)}
    distintos = [k for k, v in VALORES.items() if par_texto.get(k) != v]
    comprobar("Los valores de D62 de reglas/parametros.csv coinciden con la segunda transcripción", not distintos,
              f"({len(VALORES)} valores; distintos: {distintos or 'ninguno'})")
    p23 = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS_23)}
    comprobar("La semilla es 2026 y hay 5 pliegues (parámetros de la 2.3)", p23.get("semilla") == "2026"
              and p23.get("pliegues_validacion_cruzada") == "5")
    par = m.cargar_parametros()
    col = m.cargar_predictoras(par)
    comprobar("Las columnas de cada tipo coinciden con la segunda transcripción (14 categorías, 6 con logaritmo, 7 numéricas y 3 sí/no, en ese orden)",
              set(col["categorias"]) == CATEGORIAS and col["numericas"] == LOG + NUM and col["si_no"] == SI_NO)

    # ---------------------------------------------------------------- 2. predicciones
    casos = pd.read_parquet(CASOS)
    listas = pd.read_parquet(LISTAS)
    carpeta = par["carpeta_predicciones"]
    archivos = sorted(carpeta.glob("*.parquet")) if carpeta.exists() else []
    print(f"{len(archivos)} tablas de predicciones en {carpeta}", flush=True)
    comprobar("Hay tablas de predicciones para revisar", len(archivos) > 0, f"({len(archivos)})")
    combos, malos_nombre, malos_casos, malos_pliegue, malas_prob, malos_meta = [], [], [], [], [], []
    for a in archivos:
        c = descomponer(a.stem)
        if c is None or not combinacion_valida(c, par["ponderar"]):
            malos_nombre.append(a.name)
            continue
        combos.append((a, c))
        t = pq.read_table(a)
        meta = {k.decode(): v.decode() for k, v in (t.schema.metadata or {}).items()}
        esperado = {"variable": c["variable"], "modelo": c["modelo"], "lista": c["lista"],
                    "hospital": "CON" if c["hospital"] else "SIN", "ponderacion": "SI" if c["ponderar"] else "NO",
                    "semilla": "2026", "version_tablas": version["version"]}
        if any(meta.get(k) != v for k, v in esperado.items()):
            malos_meta.append(a.name)
        p = t.to_pandas()
        con_dato = casos.loc[casos[c["variable"]].notna(), ["ID_EGRESO", "PLIEGUE"]]
        if len(p) != len(con_dato) or p["ID_EGRESO"].duplicated().any() or set(p["ID_EGRESO"]) != set(con_dato["ID_EGRESO"]):
            malos_casos.append(a.name)
        unidos = p.merge(con_dato, on="ID_EGRESO", how="inner", suffixes=("", "_casos"))
        if not (unidos["PLIEGUE"].astype(int) == unidos["PLIEGUE_casos"].astype(int)).all():
            malos_pliegue.append(a.name)
        pr = p["PROBABILIDAD"].to_numpy()
        if not (np.isfinite(pr).all() and (pr >= 0).all() and (pr <= 1).all()):
            malas_prob.append(a.name)
    comprobar("Cada tabla es una de las 63 combinaciones de D64, con la ponderación decidida", not malos_nombre,
              f"(fuera de lugar: {resumen(malos_nombre)})")
    comprobar("La información guardada en cada tabla coincide con su nombre, la semilla y la versión", not malos_meta,
              f"(distintas: {resumen(malos_meta)})")
    comprobar("Cada tabla tiene exactamente los casos con dato en su variable, sin repetir", not malos_casos,
              f"(distintas: {resumen(malos_casos)})")
    comprobar("Cada caso tiene en la tabla su pliegue de modelos_casos", not malos_pliegue, f"(distintas: {resumen(malos_pliegue)})")
    comprobar("Las probabilidades están entre 0 y 1, sin valores vacíos", not malas_prob, f"(distintas: {resumen(malas_prob)})")

    # ---------------------------------------------------------------- 3. registro
    registro = pd.read_csv(REGISTRO, sep=";", dtype=str, encoding="utf-8-sig") if REGISTRO.exists() else pd.DataFrame()
    niveles = {c: casos[c].nunique() for c in CATEGORIAS}
    n_cat = {True: sum(niveles.values()), False: sum(niveles.values()) - niveles["HOSPITAL"]}
    malos_reg, sin_converger, sin_commit = [], [], []
    for a, c in combos:
        filas = registro[(registro["etapa"] != "tiempos") & (registro["variable"] == c["variable"])
                         & (registro["modelo"] == c["modelo"]) & (registro["lista"] == c["lista"])
                         & (registro["hospital"] == ("CON" if c["hospital"] else "SIN"))
                         & (registro["ponderacion"] == ("SI" if c["ponderar"] else "NO"))].tail(5) if len(registro) else registro
        y = casos[c["variable"]]
        con = casos[y.notna()]
        bien = len(filas) == 5 and sorted(filas["pliegue"].astype(int)) == [1, 2, 3, 4, 5]
        for _, f in filas.iterrows():
            k = int(f["pliegue"])
            pl = k if c["lista"] in LISTAS_POR_PLIEGUE else 0
            n_cod = int(((listas["VARIABLE"] == c["variable"]) & (listas["LISTA"] == c["lista"]) & (listas["PLIEGUE"] == pl)).sum())
            entren = con[con["PLIEGUE"] != k]
            bien = bien and int(f["casos_validacion"]) == int((con["PLIEGUE"] == k).sum()) \
                and int(f["casos_entrenamiento"]) == len(entren) \
                and int(f["reingresos_entrenamiento"]) == int(entren[c["variable"]].sum()) \
                and int(f["codigos"]) == n_cod and int(f["columnas"]) == n_cat[c["hospital"]] + 16 + n_cod
            if c["modelo"] == "LR" and f["llego_a_la_solucion"] != "SI":
                sin_converger.append(f"{a.stem} vuelta {k}")
            if f["commit"] in ("", "sin git"):
                sin_commit.append(a.stem)
        if not bien:
            malos_reg.append(a.stem)
    comprobar("El registro tiene las cinco vueltas de cada combinación, con los casos, reingresos, códigos y columnas recalculados aquí",
              not malos_reg, f"(distintas: {resumen(malos_reg)})")
    comprobar("La regresión logística llegó a su solución en todas sus vueltas", not sin_converger,
              f"(no llegó: {resumen(sin_converger)})")
    comprobar("Cada vuelta registra el commit del código", not sin_commit, f"(sin commit: {resumen(sin_commit)})")

    # ---------------------------------------------------------------- 4. matriz, por otro camino
    representantes = {}
    for a, c in combos:
        representantes.setdefault((c["lista"], c["hospital"]), c)
    if representantes:
        datos = m.cargar_datos(par, col)
        rng = np.random.default_rng(2026)
        muestras, preparadas = {}, {}
        for (lista, hospital), c in representantes.items():
            if c["variable"] not in preparadas:
                preparadas[c["variable"]] = m.preparar_variable(datos, c["variable"])
            vd = preparadas[c["variable"]]
            for k in range(1, 6):
                muestras[(lista, hospital, k)] = rng.choice(len(vd["idx"]), size=min(MUESTRA, len(vd["idx"])), replace=False)
        ids = np.unique(np.concatenate([preparadas[representantes[(l, h)]["variable"]]["id_egreso"][s]
                                        for (l, h, k), s in muestras.items()]))
        t = pq.read_table(CODIGOS, filters=[("ID_EGRESO", "in", ids.tolist())]).to_pandas()
        codigos_de = {i: set(zip(g["BLOQUE"].astype(str), g["NIVEL"].astype(str), g["CODIGO"].astype(str)))
                      for i, g in t.groupby("ID_EGRESO")}
        por_id = casos.set_index("ID_EGRESO")
        mal_cod, mal_cat, mal_num, mal_prop = [], [], [], []
        for (lista, hospital), c in representantes.items():
            vd = preparadas[c["variable"]]
            cats, usadas = m.bloque_categorias(vd, datos, col, hospital, par)
            nombres_cat = [(u, v) for u in usadas for v in datos["niveles"][u]]
            casos_var = casos[casos[c["variable"]].notna()]
            for k in range(1, 6):
                etiqueta = f"{c['variable']}, lista {lista}, {'con' if hospital else 'sin'} hospital, vuelta {k}"
                cods, pl, ts = m.bloque_codigos(vd, datos, lista, k, par)
                pl_esperado = k if lista in LISTAS_POR_PLIEGUE else 0
                receta = listas[(listas["VARIABLE"] == c["variable"]) & (listas["LISTA"] == lista) & (listas["PLIEGUE"] == pl_esperado)]
                lista_receta = set(zip(receta["BLOQUE"], receta["NIVEL"], receta["CODIGO"]))
                nombres_cod = [datos["triples"][i] for i in ts]
                filas = muestras[(lista, hospital, k)]
                if set(nombres_cod) != lista_receta:
                    mal_cod.append(etiqueta)
                for r in filas:
                    i = vd["id_egreso"][r]
                    del_script = {nombres_cod[j] for j in cods[r].indices}
                    if del_script != codigos_de.get(i, set()) & lista_receta:
                        mal_cod.append(etiqueta)
                        break
                for r in filas:
                    i = vd["id_egreso"][r]
                    del_script = {nombres_cat[j] for j in cats[r].indices}
                    esperado = {(u, str(por_id.at[i, u])) for u in CATEGORIAS if hospital or u != "HOSPITAL"}
                    if del_script != esperado:
                        mal_cat.append(etiqueta)
                        break
                entren = casos_var["PLIEGUE"].to_numpy() != k
                numeros = casos_var[LOG + NUM + SI_NO].astype(float)
                medianas = numeros[entren].median()
                llenos = numeros.fillna(medianas)
                transformados = llenos.copy()
                transformados[LOG] = np.log1p(llenos[LOG])
                media, desv = transformados[entren][LOG + NUM].mean(), transformados[entren][LOG + NUM].std(ddof=0)
                transformados[LOG + NUM] = (transformados[LOG + NUM] - media) / desv
                p = llenos[entren][SI_NO].mean()
                transformados[SI_NO] = llenos[SI_NO] / np.sqrt(p * (1 - p))
                arbol, _ = m.numeros_de_la_vuelta(vd["numeros"], vd["pliegue"] != k, len(LOG), len(LOG) + len(NUM), False)
                lr, _ = m.numeros_de_la_vuelta(vd["numeros"], vd["pliegue"] != k, len(LOG), len(LOG) + len(NUM), True)
                if not (np.allclose(arbol[filas], llenos.to_numpy()[filas]) and np.allclose(lr[filas], transformados.to_numpy()[filas])):
                    mal_num.append(etiqueta)
                ent_idx = np.flatnonzero(vd["pliegue"] != k)
                _, p_cat = m.escalar_si_no(cats, ent_idx)
                entrenamiento = casos_var[entren]
                conteos = {u: entrenamiento[u].astype(str).value_counts() for u in usadas}
                prop_cat = np.array([conteos[u].get(v, 0) / len(entrenamiento) for u, v in nombres_cat])
                _, p_cod = m.escalar_si_no(cods, ent_idx)
                elegidas = rng.choice(len(nombres_cod), size=min(50, len(nombres_cod)), replace=False) if nombres_cod else []
                ids_ent = set(entrenamiento["ID_EGRESO"])
                t_c = pq.read_table(CODIGOS, filters=[("CODIGO", "in", sorted({nombres_cod[j][2] for j in elegidas}))]).to_pandas()
                t_c = t_c[t_c["ID_EGRESO"].isin(ids_ent)]
                cuenta = t_c.groupby(["BLOQUE", "NIVEL", "CODIGO"], observed=True).size()
                prop_cod = np.array([cuenta.get(nombres_cod[j], 0) / len(entrenamiento) for j in elegidas])
                if not (np.allclose(p_cat, prop_cat) and np.allclose(p_cod[elegidas], prop_cod)):
                    mal_prop.append(etiqueta)
        n_rev = len(muestras)
        comprobar("La lista de cada vuelta es la de la receta del diccionario (PLIEGUE = k, o 0 en la sin filtro), y cada caso revisado tiene exactamente sus códigos de esa lista",
                  not mal_cod, f"({n_rev} vueltas, {MUESTRA} casos en cada una; distintas: {resumen(mal_cod)})")
        comprobar("Cada caso revisado tiene un 1 justo en el valor de cada una de sus categorías (sin HOSPITAL en los entrenamientos sin hospital)",
                  not mal_cat, f"(distintas: {resumen(mal_cat)})")
        comprobar("Los números transformados (mediana, logaritmo y estandarización del entrenamiento) coinciden con los recalculados aquí",
                  not mal_num, f"(distintas: {resumen(mal_num)})")
        comprobar("Las proporciones de las columnas sí/no en el entrenamiento coinciden con las contadas aquí (todas las categorías y 50 códigos por vuelta)",
                  not mal_prop, f"(distintas: {resumen(mal_prop)})")

        # ------------------------------------------------------------ 5. entrenamiento: la misma vuelta otra vez
        elegido = next(((a, c) for a, c in combos if c["modelo"] == "XGB"), combos[0])
        a, c = elegido
        vd = preparadas.get(c["variable"]) or m.preparar_variable(datos, c["variable"])
        guardadas = pq.read_table(a).to_pandas().set_index("ID_EGRESO")["PROBABILIDAD"]
        valid = vd["pliegue"] == 1
        referencia = guardadas.loc[vd["id_egreso"][valid]].to_numpy()
        print(f"Repitiendo la vuelta 1 de {a.stem}...", flush=True)
        prob, _, _, _ = m.entrenar_combinacion(c, vd, datos, col, par, [1], {}, "prueba", ("prueba", "—"), version)
        igual = float(np.max(np.abs(prob[valid] - referencia)))
        desordenadas = dict(vd)
        y = vd["y"].copy()
        y[valid] = np.random.default_rng(2026).permutation(y[valid])
        desordenadas["y"] = y
        print("Repitiéndola con las respuestas de la validación desordenadas...", flush=True)
        prob2, _, _, _ = m.entrenar_combinacion(c, desordenadas, datos, col, par, [1], {}, "prueba", ("prueba", "—"), version)
        con_desorden = float(np.max(np.abs(prob2[valid] - referencia)))
        comprobar("Repetir la vuelta 1 da las mismas probabilidades guardadas", igual <= 1e-12,
                  f"({a.stem}; {fmt(valid.sum())} casos; diferencia máxima {igual:.1e})")
        comprobar("Con las respuestas de los casos de validación desordenadas, sus probabilidades no cambian: el modelo nunca las miró",
                  con_desorden <= 1e-12, f"(cambiaron {int(np.sum(y[valid] != vd['y'][valid]))} respuestas; diferencia máxima {con_desorden:.1e})")

    # ---------------------------------------------------------------- reporte
    todo_bien = all(ok for _, ok in resultados)
    print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente del entrenamiento",
        f"Generado por `{ACTIVIDAD.name}/pruebas/verificar_17_entrenamiento.py` el {date.today():%d-%m-%Y}. Revisa por otro camino las "
        "tablas de predicciones fuera de pliegue que dejó el script 17 y su registro: rehace con pandas, sin las funciones del script, "
        "los casos, los pliegues, los códigos de cada lista, las columnas de las categorías, los números transformados y las "
        "proporciones del entrenamiento, y los compara con lo del script; además repite una vuelta, también con las respuestas de los "
        "casos de validación desordenadas, para mostrar que el modelo nunca las miró.",
        f"Tablas para los modelos: versión {version['version']}. Tablas de predicciones revisadas: {len(archivos)}.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in resultados),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
