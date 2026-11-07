"""Prueba independiente de las tablas para los modelos (actividad 3.1, script 16).

Vuelve a armar, sin usar ninguna función de los scripts 14 ni 16 y por otro camino, lo que el script 16 dejó en
data/processed/modelos_casos.parquet y data/processed/modelos_codigos.parquet:

  1. Versión y columnas. El conjunto de desarrollo es el registrado. Las dos tablas tienen las columnas esperadas, con el
     papel de una segunda transcripción escrita en este programa, y ninguna de las que nunca pueden estar.
  2. Tabla de casos. Tiene exactamente los casos de estudio de desarrollo, y cada columna es igual, caso por caso, a la de
     su origen (desarrollo.parquet, validacion_temporal.parquet o variables_casos.parquet). Los casos se emparejan por su
     ID_EGRESO, no por su posición. El período se recalcula con los años de la validación temporal.
  3. Tabla de códigos. Vuelve a sacar los códigos de las 65 columnas con pyarrow (el script usa pandas), con la categoría
     calculada con una expresión regular, y compara los pares uno por uno.
  4. Matrices. Para cada variable y cada código de alguna lista, los casos con dato que tienen el código son los CASOS de
     filtro_codigos.parquet; en las listas de cada pliegue, todo código tiene al menos el mínimo de casos en el
     entrenamiento del pliegue. Además ejecuta la receta del diccionario (sin la línea de scipy, que no está en el entorno)
     y comprueba que sus columnas sumen lo mismo.
  5. Documentos. El diccionario tiene cada columna con su papel; el registro de versión, los hashes de los archivos
     actuales, y la tabla de matrices del reporte 16, las cifras del recálculo.

Solo lee el conjunto de desarrollo; con las rutas por defecto deja reportes/pruebas_tablas_modelos.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\pruebas\\verificar_16_tablas_modelos.py

Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
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
DATOS = RAIZ / "data" / "processed"
DESARROLLO = DATOS / "desarrollo.parquet"
GRUPOS = DATOS / "validacion_temporal.parquet"
VARIABLES = DATOS / "variables_casos.parquet"
LISTAS = DATOS / "listas_codigos.parquet"
FILTRO = DATOS / "filtro_codigos.parquet"
CASOS = DATOS / "modelos_casos.parquet"
CODIGOS = DATOS / "modelos_codigos.parquet"
REGISTRO_PARTICION = RAIZ / "docs" / "version_particion.csv"
REGISTRO = RAIZ / "docs" / "version_tablas_modelos.csv"
DICCIONARIO = RAIZ / "docs" / "diccionario_tablas_modelos.md"
REPORTE_16 = ACTIVIDAD / "reportes" / "16_tablas_modelos.md"
ARCHIVO_COLUMNAS = ACTIVIDAD / "reglas" / "columnas_modelos.csv"
PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
PARAMETROS_23 = RAIZ / "2.3_validacion_particion" / "reglas" / "parametros.csv"
SCRIPT_16 = ACTIVIDAD / "scripts" / "16_tablas_modelos.py"
SALIDA = ACTIVIDAD / "reportes" / "pruebas_tablas_modelos.md"
DIAGNOSTICOS = [f"DIAGNOSTICO{i}" for i in range(1, 36)]
PROCEDIMIENTOS = [f"PROCEDIMIENTO{i}" for i in range(1, 31)]

# ---------------------------------------------------------------- segunda transcripción de las columnas
OBJETIVOS = ["REING_7D", "REING_7D_CDM", "REING_30D", "REING_30D_CDM"]
PREDICTORAS = ["EDAD", "SEXO", "PREVISION_GRUPO", "REGION", "TIPO_INGRESO", "ESTADIA", "CDM", "PESO_GRD", "HOSP_PREVIAS",
               "HOSP_PREVIAS_NO_PLANIF", "DIAS_ULTIMA_HOSP", "CMA_PREVIAS", "SESIONES_PREVIAS", "VENTANA_CORTADA",
               "INDICE_COMORBILIDAD", "TIPO_ALTA", "SEVERIDAD", "RIESGO_MORTALIDAD", "ESPECIALIDAD_INTERVENCION", "UCI_UTI",
               "TRASLADO", "N_DIAGNOSTICOS", "N_PROCEDIMIENTOS", "ESPECIALIDAD", "TIPO_PROCEDENCIA", "SERVICIO_INGRESO",
               "SERVICIO_ALTA", "PUEBLO_ORIGINARIO", "NACIONALIDAD_EXTRANJERA", "HOSPITAL"]
COLUMNAS_CASOS = [("ID_EGRESO", "IDENTIFICADOR"), ("ID_PACIENTE", "IDENTIFICADOR"), ("ANIO_ALTA", "VALIDACION"),
                  ("PERIODO", "VALIDACION"), ("PACIENTE_VISTO", "VALIDACION"), ("PLIEGUE", "VALIDACION"),
                  *[(c, "PREDICTORA") for c in PREDICTORAS], *[(k, "OBJETIVO") for k in OBJETIVOS]]
COLUMNAS_CODIGOS = [("ID_EGRESO", "IDENTIFICADOR"), ("BLOQUE", "CODIGO"), ("NIVEL", "CODIGO"), ("CODIGO", "CODIGO")]
PROHIBIDAS = ["DIAS_REING", "ID_EGRESO_REING", "IDENTIDAD_AMBIGUA", "ID_PERSONA", "ID_EPISODIO", "BLOQUE_ID", "ANIO_ARCHIVO",
              "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO", "MOTIVO_EXCLUSION", "FECHAALTA", "FECHA_INGRESO"]
LISTA_DEL_REPORTE = {"A": "A", "C": "C", "Agrupada": "AGRUPADA", "Sin filtro": "SIN_FILTRO"}
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


def numeros(texto: str) -> int:
    return int(texto.replace(".", "").replace("`", "").strip())


def indices_y_diccionario(col: pa.ChunkedArray) -> tuple[np.ndarray, list]:
    """Posición de cada fila en un único diccionario de valores, para una columna guardada como categoría."""
    col = col.unify_dictionaries()
    diccionario = col.chunk(0).dictionary.to_pylist() if col.num_chunks else []
    indices = np.concatenate([c.indices.to_numpy(zero_copy_only=False) for c in col.chunks]) if col.num_chunks else np.array([], int)
    return indices.astype(np.int64), diccionario


def main() -> None:
    inicio = time.time()
    registro = leer_csv(REGISTRO_PARTICION)[-1]
    par = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS)}
    par23 = {f["parametro"]: f["valor"].strip() for f in leer_csv(PARAMETROS_23)}
    minimo = int(par["casos_minimos"])
    n_pliegues = int(par23["pliegues_validacion_cruzada"])
    anios_entrenamiento = [int(a) for a in par23["anios_entrenamiento_temporal"].split("|")]
    anios_evaluacion = [int(a) for a in par23["anios_evaluacion_temporal"].split("|")]

    # ---------------------------------------------------------------- 1. versión y columnas
    comprobar(f"El conjunto de desarrollo tiene el hash de la versión {registro['version']} registrada de la partición",
              sha256(DESARROLLO) == registro["sha256_desarrollo"])
    casos = pq.read_table(CASOS)
    codigos = pq.read_table(CODIGOS)
    comprobar("modelos_casos.parquet tiene las 40 columnas esperadas, en orden", casos.column_names == [c for c, _ in COLUMNAS_CASOS])
    comprobar("modelos_codigos.parquet tiene las 4 columnas esperadas, en orden", codigos.column_names == [c for c, _ in COLUMNAS_CODIGOS])
    todas = set(casos.column_names) | set(codigos.column_names)
    comprobar("Ninguna de las dos tablas tiene columnas que nunca pueden estar (después del alta, identidad o armado de la cohorte)",
              not todas & set(PROHIBIDAS) and not any(c.startswith(("EXC_", "DUP_")) for c in todas))
    reglas = {(f["tabla"], f["columna"]): f["rol"] for f in leer_csv(ARCHIVO_COLUMNAS)}
    esperado = {("modelos_casos", c): r for c, r in COLUMNAS_CASOS} | {("modelos_codigos", c): r for c, r in COLUMNAS_CODIGOS}
    comprobar(f"{ARCHIVO_COLUMNAS.name} da a cada columna el papel de la segunda transcripción", reglas == esperado)

    # ---------------------------------------------------------------- 2. tabla de casos
    d = pq.read_table(DESARROLLO, columns=["ID_EGRESO", "ID_PACIENTE", "ANIO_ARCHIVO", "FECHAALTA", "ES_CASO_ESTUDIO", *OBJETIVOS])
    d = d.filter(d["ES_CASO_ESTUDIO"])
    g, v = pq.read_table(GRUPOS), pq.read_table(VARIABLES)
    id_d = d["ID_EGRESO"].to_numpy()
    posicion = pd.Index(casos["ID_EGRESO"].to_numpy()).get_indexer(id_d)   # dónde está cada caso de desarrollo en la tabla
    comprobar("La tabla de casos tiene exactamente los casos de estudio de desarrollo, una vez cada uno",
              casos.num_rows == len(id_d) == int(registro["casos_desarrollo"]) and (posicion >= 0).all()
              and len(np.unique(posicion)) == len(id_d), f"({fmt(casos.num_rows)} casos)")
    pos = pa.array(posicion)
    distintas, revisadas = [], set()
    for nombre, origen, columnas_origen in [("desarrollo.parquet", d, {"ID_PACIENTE": "ID_PACIENTE", **{k: k for k in OBJETIVOS}}),
                                           ("validacion_temporal.parquet", g, {c: c for c in ["ID_PACIENTE", "PERIODO", "PACIENTE_VISTO", "PLIEGUE"]}),
                                           ("variables_casos.parquet", v, {c: c for c in PREDICTORAS})]:
        id_origen = origen["ID_EGRESO"].to_numpy()
        pos_origen = pa.array(pd.Index(casos["ID_EGRESO"].to_numpy()).get_indexer(id_origen))
        if (pos_origen.to_numpy() < 0).any():
            distintas.append(f"{nombre}: casos que no están")
            continue
        for destino, fuente in columnas_origen.items():
            revisadas.add(destino)
            if not casos[destino].take(pos_origen).equals(origen[fuente]):
                distintas.append(f"{destino} ({nombre})")
    comprobar("Cada columna de la tabla de casos es igual, caso por caso, a la de su origen (buscando cada caso por su ID_EGRESO)",
              not distintas, f"({len(revisadas)} columnas; ANIO_ALTA se revisa abajo" +
              (f"; distintas: {', '.join(distintas)}" if distintas else "") + ")")
    anio = casos["ANIO_ALTA"].take(pos).to_numpy()
    anio_alta = pc.year(d["FECHAALTA"]).to_numpy()
    periodo = np.where(np.isin(anio_alta, anios_entrenamiento), "ENTRENAMIENTO", np.where(np.isin(anio_alta, anios_evaluacion), "EVALUACION", ""))
    comprobar("ANIO_ALTA es el año de la fecha de alta, y PERIODO, el que dan los años de la validación temporal",
              (anio == anio_alta).all() and (casos["PERIODO"].take(pos).to_numpy(zero_copy_only=False) == periodo).all())
    tabla_pp = pd.DataFrame({"p": casos["ID_PACIENTE"].to_numpy(), "f": casos["PLIEGUE"].to_numpy()})
    comprobar(f"PLIEGUE va de 1 a {n_pliegues} y ningún paciente está en dos pliegues",
              tabla_pp["f"].between(1, n_pliegues).all() and (tabla_pp.groupby("p")["f"].nunique() == 1).all())

    # ---------------------------------------------------------------- 3. tabla de códigos
    print("Sacando de nuevo los códigos de cada caso...", flush=True)
    listas = pq.read_table(LISTAS).to_pandas()
    union = (listas[["BLOQUE", "NIVEL", "CODIGO"]].astype(str).drop_duplicates()
             .sort_values(["NIVEL", "BLOQUE", "CODIGO"], ascending=[False, True, True]).reset_index(drop=True))
    K = len(union)
    t = pq.read_table(DESARROLLO, columns=["ES_CASO_ESTUDIO", *DIAGNOSTICOS, *PROCEDIMIENTOS])
    t = t.filter(t["ES_CASO_ESTUDIO"])
    filas, ids = [], []
    for (bloque, nivel), grupo in union.groupby(["BLOQUE", "NIVEL"]):
        conjunto = pa.array(grupo["CODIGO"].tolist())
        for col in (DIAGNOSTICOS if bloque == "DIAGNOSTICO" else PROCEDIMIENTOS):
            arreglo = t[col].combine_chunks()
            validos = pc.is_valid(arreglo)
            fila_col = np.flatnonzero(validos.to_numpy(zero_copy_only=False))
            valores = arreglo.filter(validos)
            if nivel == "CATEGORIA":   # lo que va antes del primer punto, con una expresión regular
                valores = pc.extract_regex(valores, r"^(?P<cat>[^.]*)").field("cat")
            posicion_codigo = pc.fill_null(pc.index_in(valores, value_set=conjunto), -1).to_numpy(zero_copy_only=False)
            esta = posicion_codigo >= 0
            filas.append(fila_col[esta])
            ids.append(grupo.index.to_numpy()[posicion_codigo[esta]])
    del t
    clave = np.unique(np.concatenate(filas).astype(np.int64) * K + np.concatenate(ids).astype(np.int64))
    del filas, ids
    fila_rec, id_rec = clave // K, clave % K

    # La tabla del script, en los mismos números: fila del caso en desarrollo y código de la tabla de arriba
    fila_script = pd.Index(id_d).get_indexer(codigos["ID_EGRESO"].to_numpy())
    b_idx, b_dic = indices_y_diccionario(codigos["BLOQUE"])
    n_idx, n_dic = indices_y_diccionario(codigos["NIVEL"])
    c_idx, c_dic = indices_y_diccionario(codigos["CODIGO"])
    traduccion = np.full(len(b_dic) * len(n_dic) * len(c_dic), -1, dtype=np.int64)
    pos_c = {c: i for i, c in enumerate(c_dic)}
    for i, r in union.iterrows():
        if r["BLOQUE"] in b_dic and r["NIVEL"] in n_dic and r["CODIGO"] in pos_c:
            traduccion[(b_dic.index(r["BLOQUE"]) * len(n_dic) + n_dic.index(r["NIVEL"])) * len(c_dic) + pos_c[r["CODIGO"]]] = i
    id_script = traduccion[(b_idx * len(n_dic) + n_idx) * len(c_dic) + c_idx]
    del b_idx, n_idx, c_idx
    clave_script = fila_script.astype(np.int64) * K + id_script
    comprobar("Todos los pares de la tabla de códigos son de casos de desarrollo y de códigos de alguna lista",
              bool((fila_script >= 0).all() and (id_script >= 0).all()))
    comprobar("La tabla de códigos está ordenada por caso y no repite un código en un caso",
              bool((np.diff(codigos["ID_EGRESO"].to_numpy()) >= 0).all() and len(np.unique(clave_script)) == len(clave_script)))
    comprobar("Los pares caso–código son exactamente los recalculados con pyarrow, uno por uno",
              len(clave_script) == len(clave) and np.array_equal(np.sort(clave_script), clave),
              f"({fmt(len(clave))} recalculados y {fmt(len(clave_script))} en la tabla)")
    del clave_script, fila_script, id_script

    # ---------------------------------------------------------------- 4. matrices
    y = {k: d[k].to_numpy(zero_copy_only=False).astype("float64") for k in OBJETIVOS}
    pliegue_d = g["PLIEGUE"].take(pa.array(pd.Index(g["ID_EGRESO"].to_numpy()).get_indexer(id_d))).to_numpy().astype(np.int64)
    filtro = pd.read_parquet(FILTRO, columns=["VARIABLE", "BLOQUE", "NIVEL", "CODIGO", "CASOS"]).astype(
        {"VARIABLE": str, "BLOQUE": str, "NIVEL": str, "CODIGO": str})
    cuenta, cuenta_pliegue, malas = {}, {}, {}
    for k in OBJETIVOS:
        con = ~np.isnan(y[k][fila_rec])
        cuenta[k] = np.bincount(id_rec[con], minlength=K)
        cuenta_pliegue[k] = np.bincount(id_rec[con] * n_pliegues + pliegue_d[fila_rec[con]] - 1,
                                        minlength=K * n_pliegues).reshape(K, n_pliegues)
        casos_filtro = union.merge(filtro[filtro["VARIABLE"] == k], on=["BLOQUE", "NIVEL", "CODIGO"], how="left")["CASOS"]
        malas[k] = int((casos_filtro.isna() | (casos_filtro.to_numpy() != cuenta[k])).sum())
    comprobar("Para cada variable y cada código de alguna lista, los casos con dato que lo tienen son los CASOS de filtro_codigos.parquet",
              not any(malas.values()), "(" + "; ".join(f"{k}: {v} distintos" for k, v in malas.items() if v) + ")" if any(malas.values()) else
              f"({fmt(K)} códigos × {len(OBJETIVOS)} variables)")
    listas_id = listas.astype({"BLOQUE": str, "NIVEL": str, "CODIGO": str}).merge(union.reset_index(names="ID"),
                                                                                 on=["BLOQUE", "NIVEL", "CODIGO"])
    bajo_minimo = 0
    for (k, lista, f), grupo in listas_id.groupby(["VARIABLE", "LISTA", "PLIEGUE"]):
        ids_l = grupo["ID"].to_numpy()
        entrenamiento = cuenta[k][ids_l] - (cuenta_pliegue[k][ids_l, int(f) - 1] if int(f) > 0 else 0)
        bajo_minimo += int((entrenamiento < minimo).sum())
    comprobar(f"En cada lista, todo código tiene al menos {minimo} casos con dato en su entrenamiento (todo desarrollo en "
              "PLIEGUE 0; sin los casos del pliegue en los demás)", bajo_minimo == 0,
              f"({fmt(len(listas_id))} filas de listas revisadas; {bajo_minimo} bajo el mínimo)")

    # La receta del diccionario, tal como está escrita (sin la línea de scipy)
    texto = DICCIONARIO.read_text(encoding="utf-8")
    bloque = re.search(r"```python\n(.*?)```", texto, flags=re.S)
    receta_ok, detalle = False, "(no se encontró la receta)"
    if bloque:
        codigo = "\n".join(linea for linea in bloque.group(1).splitlines() if "scipy" not in linea and "sp.csr_matrix" not in linea)
        for archivo, ruta in [("modelos_casos.parquet", CASOS), ("modelos_codigos.parquet", CODIGOS), ("listas_codigos.parquet", LISTAS)]:
            codigo = codigo.replace(f'"data/processed/{archivo}"', repr(str(ruta)))
        print("Ejecutando la receta del diccionario...", flush=True)
        t0 = time.time()
        espacio = {}
        exec(codigo, espacio)
        p_rec, columnas_rec, variable = espacio["pares"], espacio["columnas"], espacio["variable"]
        suma = np.bincount(p_rec["j"].to_numpy(), minlength=len(columnas_rec))
        esperado_rec = columnas_rec.astype(str).merge(filtro[filtro["VARIABLE"] == variable], on=["BLOQUE", "NIVEL", "CODIGO"],
                                                      how="left")["CASOS"].to_numpy()
        receta_ok = bool(len(espacio["filas"]) == int((~np.isnan(y[variable])).sum()) and (suma == esperado_rec).all()
                         and p_rec["i"].between(0, len(espacio["filas"]) - 1).all())
        detalle = (f"({variable}, lista {espacio['lista']}, pliegue {espacio['pliegue']}: {fmt(len(espacio['filas']))} filas, "
                   f"{fmt(len(columnas_rec))} columnas y {fmt(len(p_rec))} unos, en {time.time() - t0:.0f} s)")
        del espacio, p_rec
    comprobar("La receta del diccionario arma columnas que suman los CASOS de filtro_codigos.parquet", receta_ok, detalle)

    # ---------------------------------------------------------------- 5. documentos
    ultima = leer_csv(REGISTRO)[-1] if REGISTRO.exists() else {}
    comprobar("La última versión del registro tiene el hash de las dos tablas y de sus entradas actuales",
              bool(ultima) and ultima["sha256_casos"] == sha256(CASOS) and ultima["sha256_codigos"] == sha256(CODIGOS)
              and ultima["sha256_desarrollo"] == registro["sha256_desarrollo"] and ultima["sha256_validacion_temporal"] == sha256(GRUPOS)
              and ultima["sha256_variables_casos"] == sha256(VARIABLES) and ultima["sha256_listas_codigos"] == sha256(LISTAS)
              and ultima["sha256_columnas"] == sha256(ARCHIVO_COLUMNAS) and ultima["sha256_script_16"] == sha256(SCRIPT_16)
              and ultima["version_particion"] == registro["version"] and int(ultima["casos"]) == casos.num_rows
              and int(ultima["pares_codigos"]) == codigos.num_rows,
              f"(versión {ultima.get('version', '—')})")
    secciones = re.split(r"\n## ", texto)
    seccion = {s.split("\n", 1)[0]: s for s in secciones}
    sec_casos = next((s for titulo, s in seccion.items() if titulo.startswith("1.")), "")
    sec_codigos = next((s for titulo, s in seccion.items() if titulo.startswith("2.")), "")
    faltan = [c for c, r in COLUMNAS_CASOS if sec_casos.count(f"| `{c}` | {r} |") != 1]
    faltan += [c for c, r in COLUMNAS_CODIGOS if sec_codigos.count(f"| `{c}` | {r} |") != 1]
    comprobar("El diccionario describe cada columna una vez, con su papel, y muestra la versión registrada",
              not faltan and bool(ultima) and f"`{ultima.get('sha256_casos')}`" in texto and f"`{ultima.get('sha256_codigos')}`" in texto,
              f"(faltan o están mal: {', '.join(faltan)})" if faltan else "")

    reporte = REPORTE_16.read_text(encoding="utf-8")
    filas_reporte = re.findall(r"^\| `(REING_\w+)` \| (A|C|Agrupada|Sin filtro) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", reporte, flags=re.M)
    malas_rep = 0
    for k, nombre_lista, n_filas, n_columnas, unos in filas_reporte:
        ids_l = listas_id[(listas_id["VARIABLE"] == k) & (listas_id["LISTA"] == LISTA_DEL_REPORTE[nombre_lista])
                          & (listas_id["PLIEGUE"] == 0)]["ID"].to_numpy()
        calculado = (int((~np.isnan(y[k])).sum()), len(ids_l), int(cuenta[k][ids_l].sum()))
        malas_rep += calculado != (numeros(n_filas), numeros(n_columnas), numeros(unos))
    comprobar("La tabla de matrices del reporte 16 coincide con el recálculo (filas, columnas y celdas con 1)",
              len(filas_reporte) == len(OBJETIVOS) * listas.drop_duplicates(["LISTA"]).shape[0] and malas_rep == 0,
              f"({len(filas_reporte)} filas; {malas_rep} distintas)")

    # ---------------------------------------------------------------- reporte
    todo_bien = all(ok for _, ok in resultados)
    print(f"\nRESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'} ({time.time() - inicio:.0f} s)")
    ruta = ACTIVIDAD.name
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n\n".join([
        "# Prueba independiente de las tablas para los modelos",
        f"Generado por `{ruta}/pruebas/verificar_16_tablas_modelos.py` el {date.today():%d-%m-%Y}. El programa vuelve a armar, sin "
        "usar ninguna función de los scripts 14 ni 16, lo que el script 16 dejó en `data/processed/modelos_casos.parquet` y "
        "`data/processed/modelos_codigos.parquet`. Compara las columnas con una segunda transcripción de sus papeles; empareja "
        "cada caso con su origen por su `ID_EGRESO`; vuelve a sacar los códigos de las 65 columnas con pyarrow (la categoría, con "
        "una expresión regular) y compara los pares uno por uno; comprueba que las columnas de las matrices sumen los casos de "
        "`filtro_codigos.parquet` y que la receta del diccionario funcione, y revisa el diccionario, el registro de versión y el "
        "reporte 16. Solo lee el conjunto de desarrollo.",
        f"Partición probada: versión {registro['version']}, registrada el {registro['fecha']} en `docs/{REGISTRO_PARTICION.name}`. "
        f"Tablas probadas: versión {ultima.get('version', '—')} de `docs/{REGISTRO.name}`.",
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}** ({len(resultados)} comprobaciones, "
        f"{sum(not ok for _, ok in resultados)} fallas).",
        "\n".join(f"- {texto_r}: **{'sí' if ok else 'NO'}**." for texto_r, ok in resultados),
    ]) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
