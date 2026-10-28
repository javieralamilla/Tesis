"""Filtro de dimensionalidad (actividad 3.1, script 14).

Etapa 3 de la propuesta. Los diagnósticos (CIE-10) y los procedimientos (CIE-9-MC) de cada caso de estudio
se usan como indicadores sí/no y suman miles de códigos, así que se filtran según su asociación con cada
variable de reingreso. Sobre millones de casos casi cualquier código sale significativo, por lo que el
umbral no se pone en el valor p sino en el tamaño de efecto, la V de Cramér (bitácora D45).

  1. Parámetros. Los umbrales están en reglas/parametros.csv.
  2. Versión. Comprueba que el conjunto de desarrollo sea el de la última versión registrada de la
     partición (docs/version_particion.csv). No abre el conjunto de prueba.
  3. Códigos. Arma una tabla con una fila por caso de estudio y código. Un código cuenta una vez por
     caso, esté en la posición que esté.
  4. Asociación. Para cada variable de reingreso, con los casos que tienen dato en ella, arma la tabla
     de 2×2 de cada código (tiene o no el código × reingresa o no) y calcula el chi-cuadrado, su valor
     p y la V de Cramér.
  5. Filtro. Pasan los códigos con V mayor o igual a v_minima que tengan al menos casos_minimos casos.
     Además cuenta cuántos pasarían con los otros umbrales de la sensibilidad.
  6. Salida. data/processed/filtro_codigos.parquet tiene todos los códigos, pasen o no; la lista fija
     con los que pasan queda en reportes/14_codigos_retenidos.csv, y el resumen, en
     reportes/14_filtro_codigos.md.

El filtro se calcula una sola vez, con todo el conjunto de desarrollo, y la lista queda fija: las etapas
siguientes la aplican sin recalcularla, también al conjunto de prueba en la evaluación final.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 3.1_filtro_dimensionalidad\\scripts\\14_filtro_codigos.py
"""

import csv
import hashlib
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DESARROLLO = RAIZ / "data" / "processed" / "desarrollo.parquet"
DESTINO = RAIZ / "data" / "processed" / "filtro_codigos.parquet"
REGISTRO = RAIZ / "docs" / "version_particion.csv"
DIR_TABLAS = RAIZ.parent / "Datos" / "Tablas auxiliares"  # tablas del DEIS con la descripción de cada código
ARCHIVO_PARAMETROS = ACTIVIDAD / "reglas" / "parametros.csv"
DIR_REPORTS = ACTIVIDAD / "reportes"
LISTA = DIR_REPORTS / "14_codigos_retenidos.csv"
REPORTE = DIR_REPORTS / "14_filtro_codigos.md"
PARAMETROS = ["variables_objetivo", "nivel_codigo", "v_minima", "casos_minimos", "v_sensibilidad", "casos_sensibilidad"]
BLOQUES = {  # bloque: columnas del conjunto de desarrollo y tabla del DEIS con sus descripciones
    "DIAGNOSTICO": ([f"DIAGNOSTICO{i}" for i in range(1, 36)], "CIE-10.xlsx"),
    "PROCEDIMIENTO": ([f"PROCEDIMIENTO{i}" for i in range(1, 31)], "CIE-9.xlsx"),
}
NOMBRE_BLOQUE = {"DIAGNOSTICO": "Diagnósticos (CIE-10)", "PROCEDIMIENTO": "Procedimientos (CIE-9-MC)"}
NIVELES = {"COMPLETO": "el código tal como viene (por ejemplo, E11.9)",
           "CATEGORIA": "solo la categoría del código, lo que va antes del punto (E11 en los diagnósticos y 99 en los procedimientos)"}
COLUMNAS_LISTA = ["VARIABLE", "BLOQUE", "CODIGO", "DESCRIPCION", "CASOS", "REINGRESOS", "TASA_CON_CODIGO",
                  "TASA_SIN_CODIGO", "V", "DIRECCION"]


# ------------------------------------------------------------------ 1. parámetros y 2. versión
def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cargar_parametros() -> dict:
    filas = {fila["parametro"]: fila for fila in leer_csv(ARCHIVO_PARAMETROS)}
    faltan = sorted(set(PARAMETROS) - set(filas))
    if faltan:
        raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: faltan los parámetros {faltan}.")
    for nombre, fila in filas.items():
        if None in fila:  # una columna de más: hay un «;» dentro de un texto y cortaría la descripción
            raise SystemExit(f"{ARCHIVO_PARAMETROS.name}: la fila de '{nombre}' tiene un «;» de más.")
    valor = {nombre: filas[nombre]["valor"].strip() for nombre in PARAMETROS}

    def numeros(nombre: str, tipo) -> list:
        # "0,005|0,01|0,02" se convierte en [0.005, 0.01, 0.02]: en Python el decimal se escribe con punto
        return [tipo(v.strip().replace(",", ".")) for v in valor[nombre].split("|") if v.strip()]

    par = {"objetivos": [v.strip() for v in valor["variables_objetivo"].split("|") if v.strip()],
           "nivel": valor["nivel_codigo"].upper(),
           "v_minima": numeros("v_minima", float)[0], "casos_minimos": numeros("casos_minimos", int)[0],
           "v_sensibilidad": numeros("v_sensibilidad", float), "casos_sensibilidad": numeros("casos_sensibilidad", int)}
    if par["nivel"] not in NIVELES:
        raise SystemExit(f"nivel_codigo: se esperaba {' o '.join(NIVELES)} y dice '{valor['nivel_codigo']}'.")
    if par["v_minima"] not in par["v_sensibilidad"] or par["casos_minimos"] not in par["casos_sensibilidad"]:
        raise SystemExit("Los umbrales principales deben estar también entre los de la sensibilidad.")
    par["descripcion"] = {nombre: (valor[nombre], filas[nombre]["descripcion"]) for nombre in PARAMETROS}
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


# ------------------------------------------------------------------ 3. códigos de cada caso de estudio
def leer_casos(par: dict) -> pd.DataFrame:
    """Los casos de estudio de desarrollo, con su año, las variables de reingreso y las columnas de códigos."""
    columnas_codigos = [c for columnas, _ in BLOQUES.values() for c in columnas]
    casos = pd.read_parquet(DESARROLLO, columns=["ID_EGRESO", "ANIO_ARCHIVO", *par["objetivos"], *columnas_codigos],
                            filters=[("ES_CASO_ESTUDIO", "==", True)])
    return casos.reset_index(drop=True)  # las filas quedan numeradas 0, 1, 2, ...


def tabla_larga(casos: pd.DataFrame, columnas: list[str], nivel: str) -> pd.DataFrame:
    """Una fila por caso de estudio y código (FILA es la fila del caso en la tabla de casos).
    Un código que aparece en dos posiciones del mismo caso queda una sola vez."""
    partes = []
    for columna in columnas:
        codigos = casos[columna].dropna()  # solo los casos que tienen un código en esta posición
        partes.append(pd.DataFrame({"FILA": codigos.index, "CODIGO": codigos}))
    largo = pd.concat(partes, ignore_index=True)
    if nivel == "CATEGORIA":
        largo["CODIGO"] = largo["CODIGO"].str.split(".").str[0]
    largo["CODIGO"] = largo["CODIGO"].astype("category")  # cada código distinto se guarda una sola vez: ahorra memoria
    return largo.drop_duplicates(ignore_index=True)


# ------------------------------------------------------------------ 4. asociación con una variable de reingreso
def asociacion(largo: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
    """Tabla de 2×2 de cada código con una variable de reingreso, y sus medidas de asociación.

    y tiene una posición por caso de estudio: 1 si reingresa, 0 si no y NaN si no tiene dato (por ejemplo,
    un caso sin los 60 días de seguimiento en las variables de 30 días). Los casos sin dato no se cuentan."""
    N = int((~np.isnan(y)).sum())  # casos con dato en la variable
    R = int((y == 1).sum())        # de ellos, los que reingresan
    y_par = y[largo["FILA"].to_numpy()]  # el valor de la variable en el caso de cada par caso-código
    con_dato = ~np.isnan(y_par)
    pares = pd.DataFrame({"CODIGO": largo["CODIGO"][con_dato], "REINGRESA": y_par[con_dato] == 1})
    cuenta = pares.groupby("CODIGO", observed=False)["REINGRESA"].agg(["size", "sum"])

    # Las cuatro celdas de la tabla de 2×2 de cada código
    a = cuenta["sum"].to_numpy(dtype=float)       # tiene el código y reingresa
    b = cuenta["size"].to_numpy(dtype=float) - a  # tiene el código y no reingresa
    c = R - a                                     # no tiene el código y reingresa
    d = (N - R) - b                               # no tiene el código y no reingresa
    con, sin = a + b, c + d                       # casos con el código y sin él

    # Chi-cuadrado de Pearson: suma, en las cuatro celdas, de (observado - esperado)² / esperado. El esperado
    # es lo que habría si el código no tuviera relación con el reingreso: la misma tasa con el código y sin él.
    chi2 = np.zeros(len(cuenta))
    for observado, total_fila, total_columna in [(a, con, R), (b, con, N - R), (c, sin, R), (d, sin, N - R)]:
        esperado = total_fila * total_columna / N
        chi2 += np.divide((observado - esperado) ** 2, esperado, out=np.zeros(len(cuenta)), where=esperado > 0)

    with np.errstate(invalid="ignore", divide="ignore"):
        tasa_con = np.where(con > 0, 100 * a / con, np.nan)
        tasa_sin = np.where(sin > 0, 100 * c / sin, np.nan)
    return pd.DataFrame({
        "CODIGO": cuenta.index.astype(str),
        "CASOS": con.astype(np.int64),
        "REINGRESOS": a.astype(np.int64),
        "TASA_CON_CODIGO": tasa_con,
        "TASA_SIN_CODIGO": tasa_sin,
        "CHI2": chi2,
        "VALOR_P": [math.erfc(math.sqrt(x / 2)) for x in chi2],  # valor p del chi-cuadrado con 1 grado de libertad
        "V": np.sqrt(chi2 / N),                                  # V de Cramér: en una tabla de 2×2 es raíz(chi² / N)
        "DIRECCION": np.select([con == 0, tasa_con > tasa_sin, tasa_con < tasa_sin], ["sin casos", "sube", "baja"],
                               default="igual"),
    })


# ------------------------------------------------------------------ 5. filtro y sensibilidad
def filtrar(par: dict, casos: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Calcula la asociación de todos los códigos con cada variable de reingreso y marca los que pasan."""
    y = {k: casos[k].to_numpy(dtype="float64", na_value=np.nan) for k in par["objetivos"]}
    anio = casos["ANIO_ARCHIVO"].to_numpy()
    info = {"casos": len(casos), "casos_anio": casos["ANIO_ARCHIVO"].value_counts().sort_index(),
            "totales": {k: (int((~np.isnan(v)).sum()), int((v == 1).sum())) for k, v in y.items()},
            "bloques": {}, "pares_con_dato": {}, "frecuencia_anual": {}}
    resultados = []
    for bloque, (columnas, _) in BLOQUES.items():
        largo = tabla_larga(casos, columnas, par["nivel"])
        info["bloques"][bloque] = {"codigos": int(largo["CODIGO"].nunique()), "pares": len(largo)}
        # casos de cada año del alta que tienen cada código (para ver si un código cambia con los años)
        info["frecuencia_anual"][bloque] = (pd.DataFrame({"CODIGO": largo["CODIGO"], "ANIO": anio[largo["FILA"].to_numpy()]})
                                            .groupby(["CODIGO", "ANIO"], observed=True).size())
        for k in par["objetivos"]:
            tabla = asociacion(largo, y[k])
            tabla.insert(0, "BLOQUE", bloque)
            tabla.insert(0, "VARIABLE", k)
            resultados.append(tabla)
            info["pares_con_dato"][(bloque, k)] = int((~np.isnan(y[k][largo["FILA"].to_numpy()])).sum())
        del largo

    todo = pd.concat(resultados, ignore_index=True)
    todo["PASA"] = (todo["CASOS"] >= par["casos_minimos"]) & (todo["V"] >= par["v_minima"])
    todo["VARIABLE"] = pd.Categorical(todo["VARIABLE"], categories=par["objetivos"], ordered=True)
    todo = todo.sort_values(["VARIABLE", "BLOQUE", "V"], ascending=[True, True, False], ignore_index=True)
    todo["VARIABLE"] = todo["VARIABLE"].astype(str)

    # Sensibilidad: cuántos códigos pasarían con cada combinación de umbrales (solo se cuentan)
    info["sensibilidad"] = {}
    for v in par["v_sensibilidad"]:
        for n in par["casos_sensibilidad"]:
            pasaria = (todo["CASOS"] >= n) & (todo["V"] >= v)
            info["sensibilidad"][(v, n)] = {
                k: {b: int((pasaria & (todo["VARIABLE"] == k) & (todo["BLOQUE"] == b)).sum()) for b in BLOQUES}
                for k in par["objetivos"]}
    return todo, info


def agregar_descripciones(todo: pd.DataFrame) -> None:
    """Agrega la descripción de cada código según las tablas del DEIS (CIE-10 y CIE-9)."""
    descripcion = pd.Series("", index=todo.index)
    for bloque, (_, archivo) in BLOQUES.items():
        tabla = pd.read_excel(DIR_TABLAS / archivo, dtype=str)
        texto = dict(zip(tabla["Código"].str.strip(), tabla["Descripción"].str.split().str.join(" ")))
        filas = todo["BLOQUE"] == bloque
        descripcion[filas] = todo.loc[filas, "CODIGO"].map(texto).fillna("")
    todo.insert(3, "DESCRIPCION", descripcion)


# ------------------------------------------------------------------ verificaciones y 6. salida
def verificar(todo: pd.DataFrame, info: dict, par: dict, version: dict) -> list[tuple[str, bool]]:
    pasan = todo[todo["PASA"]]
    abreviada_igual, celdas_ok, filas_ok, suma_ok = True, True, True, True
    for k, (N, R) in info["totales"].items():
        for bloque in BLOQUES:
            t = todo[(todo["VARIABLE"] == k) & (todo["BLOQUE"] == bloque)]
            a = t["REINGRESOS"].to_numpy(dtype=float)
            b = t["CASOS"].to_numpy(dtype=float) - a
            c, d = R - a, (N - R) - b
            celdas_ok &= bool((a >= 0).all() and (b >= 0).all() and (c >= 0).all() and (d >= 0).all())
            # El chi-cuadrado de una tabla de 2×2 también es N·(ad − bc)² / (con · sin · R · (N − R))
            den = (a + b) * (c + d) * R * (N - R)
            abreviada = np.divide(N * (a * d - b * c) ** 2, den, out=np.zeros(len(t)), where=den > 0)
            abreviada_igual &= bool(np.allclose(abreviada, t["CHI2"].to_numpy(), rtol=1e-9, atol=1e-9))
            filas_ok &= len(t) == info["bloques"][bloque]["codigos"] and t["CODIGO"].is_unique
            suma_ok &= int(t["CASOS"].sum()) == info["pares_con_dato"][(bloque, k)]
    principal = info["sensibilidad"][(par["v_minima"], par["casos_minimos"])]
    return [
        ("Se leyeron todos los casos de estudio del conjunto de desarrollo registrado",
         info["casos"] == int(version["casos_desarrollo"])),
        ("Cada variable tiene una fila por código distinto de cada bloque, sin repetir códigos", filas_ok),
        ("En cada variable, los casos de todos los códigos suman los pares caso–código con dato", suma_ok),
        ("Las cuatro celdas de la tabla de 2×2 de cada código son mayores o iguales a cero", celdas_ok),
        ("El chi-cuadrado coincide con el de la fórmula abreviada N·(ad − bc)² / (con · sin · R · (N − R))", abreviada_igual),
        ("La V está entre 0 y 1 en todos los códigos", bool(todo["V"].between(0, 1).all())),
        ("El valor p es 0,05 cuando el chi-cuadrado es 3,841459 (control de la fórmula)",
         abs(math.erfc(math.sqrt(3.841459 / 2)) - 0.05) < 1e-6),
        ("Todos los códigos que pasan tienen descripción en las tablas del DEIS", bool((pasan["DESCRIPCION"] != "").all())),
        ("Con los umbrales principales, la sensibilidad cuenta los mismos códigos que la lista",
         sum(sum(x.values()) for x in principal.values()) == len(pasan)),
    ]


def escribir(todo: pd.DataFrame) -> list[tuple[str, bool]]:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    LISTA.parent.mkdir(parents=True, exist_ok=True)
    temporal = DESTINO.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(todo, preserve_index=False), temporal, compression="zstd")
    temporal.replace(DESTINO)
    lista = todo.loc[todo["PASA"], COLUMNAS_LISTA]
    lista.to_csv(LISTA, sep=";", decimal=",", index=False, encoding="utf-8-sig", float_format="%.6f")

    releido = pd.read_parquet(DESTINO)
    releida = pd.read_csv(LISTA, sep=";", decimal=",", encoding="utf-8-sig", dtype={"CODIGO": str})
    try:
        pd.testing.assert_frame_equal(releido, todo, check_dtype=False)
        parquet_igual = True
    except AssertionError:
        parquet_igual = False
    clave = ["VARIABLE", "BLOQUE", "CODIGO", "CASOS", "REINGRESOS"]
    lista_igual = (len(releida) == len(lista)
                   and (releida[clave].astype(str).to_numpy() == lista[clave].astype(str).to_numpy()).all())
    return [
        ("Lo releído de filtro_codigos.parquet es igual a lo calculado", parquet_igual),
        ("La lista releída tiene los mismos códigos, casos y reingresos que los que pasan el filtro", bool(lista_igual)),
    ]


# ------------------------------------------------------------------ reporte
def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def dec(x, decimales: int = 4) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def contar(n, singular: str, plural: str) -> str:
    return f"{fmt(n)} {singular if n == 1 else plural}"


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def tasa_necesaria(n: int, N: int, R: int, v: float) -> float:
    """Tasa de reingreso (%) que necesita un código con n casos para llegar a V = v subiendo el riesgo.
    Sale de despejar los reingresos del código en la fórmula de la V: a = (n·R + v·raíz(n·(N − n)·R·(N − R))) / N."""
    a = (n * R + v * math.sqrt(n * (N - n) * R * (N - R))) / N
    return 100 * a / n


def casos_para_bajar(N: int, R: int, v: float) -> int:
    """Casos mínimos para que un código que baja el riesgo llegue a V = v aunque ninguno de sus casos reingrese:
    n ≥ v²·N·(N − R) / (R + v²·(N − R))."""
    return math.ceil(v * v * N * (N - R) / (R + v * v * (N - R)))


def escribir_reporte(todo: pd.DataFrame, info: dict, par: dict, version: dict, verificaciones: list) -> None:
    ruta = ACTIVIDAD.name
    objetivos, v_min = par["objetivos"], par["v_minima"]
    pasan = todo[todo["PASA"]]

    filas_pasan = []
    for k in objetivos:
        N, R = info["totales"][k]
        celdas = []
        for b in BLOQUES:
            p = pasan[(pasan["VARIABLE"] == k) & (pasan["BLOQUE"] == b)]
            celdas.append(f"{fmt(len(p))} ({contar((p['DIRECCION'] == 'sube').sum(), 'sube', 'suben')} y "
                          f"{contar((p['DIRECCION'] == 'baja').sum(), 'baja', 'bajan')})")
        filas_pasan.append([f"`{k}`", fmt(N), f"{fmt(R)} ({pct(R, N)})", *celdas, fmt((pasan["VARIABLE"] == k).sum())])

    filas_sens = []
    for (v, n), conteo in info["sensibilidad"].items():
        marca = " (principal)" if (v, n) == (v_min, par["casos_minimos"]) else ""
        filas_sens.append([dec(v, 3) + marca, fmt(n),
                           *[f"{fmt(sum(conteo[k].values()))} ({fmt(conteo[k]['DIAGNOSTICO'])} + {fmt(conteo[k]['PROCEDIMIENTO'])})"
                             for k in objetivos]])

    tamanos = [100, 250, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 100_000]
    filas_tasa = [[fmt(n), *[dec(tasa_necesaria(n, *info["totales"][k], v_min), 1) + " %" for k in objetivos]] for n in tamanos]
    filas_tasa.append(["Tasa de toda la variable", *[pct(info["totales"][k][1], info["totales"][k][0]) for k in objetivos]])
    filas_tasa.append(["Casos que necesita un código que baja el riesgo", *[fmt(casos_para_bajar(*info["totales"][k], v_min))
                                                                           for k in objetivos]])

    mayores = []
    for k in objetivos:
        for direccion, verbo in [("sube", "suben"), ("baja", "bajan")]:
            p = pasan[(pasan["VARIABLE"] == k) & (pasan["DIRECCION"] == direccion)].nlargest(10, "V")
            if len(p):
                mayores += [f"**`{k}`, los que más {verbo} el riesgo:**",
                            tabla_md(["Código", "Descripción", "Casos", "Reingreso con el código", "Sin el código", "V"],
                                     [[f"`{r.CODIGO}`", r.DESCRIPCION, fmt(r.CASOS), dec(r.TASA_CON_CODIGO, 2) + " %",
                                       dec(r.TASA_SIN_CODIGO, 2) + " %", dec(r.V)] for r in p.itertuples()])]

    filas_listas = []
    for b in BLOQUES:
        n_listas = pasan[pasan["BLOQUE"] == b].groupby("CODIGO")["VARIABLE"].nunique()
        filas_listas.append([NOMBRE_BLOQUE[b], fmt(len(n_listas)),
                             *[fmt((n_listas == i).sum()) for i in range(len(objetivos), 0, -1)]])

    # Códigos que pasan y cambian con los años: % de los casos de estudio de cada año que tienen el código
    casos_anio = info["casos_anio"]
    anios = [int(a) for a in casos_anio.index]
    prevalencia = {}
    for b in BLOQUES:
        frec = info["frecuencia_anual"][b].unstack(fill_value=0).reindex(columns=casos_anio.index, fill_value=0)
        frec.index = frec.index.astype(str)
        prevalencia[b] = 100 * frec / casos_anio.to_numpy()
    filas_cambio = []
    for k in objetivos:
        celdas = []
        for b in BLOQUES:
            p = prevalencia[b].loc[pasan.loc[(pasan["VARIABLE"] == k) & (pasan["BLOQUE"] == b), "CODIGO"]]
            falta = (p == 0).any(axis=1)
            razon = p.max(axis=1) / p.min(axis=1).where(~falta)
            celdas.append(f"{fmt((razon > 3).sum())} de {fmt(len(p))}" + (f" (faltan en algún año: {fmt(falta.sum())})" if falta.any() else ""))
        filas_cambio.append([f"`{k}`", *celdas])
    # Entre los que varían más del triple, los que tienen la mayor diferencia (en puntos) entre su año de mayor
    # y su año de menor frecuencia: son los que más casos afectan.
    donde = pasan.groupby(["BLOQUE", "CODIGO"])["VARIABLE"].agg(lambda s: ", ".join(f"`{x}`" for x in s))
    candidatos = []
    for (b, codigo), variables in donde.items():
        p = prevalencia[b].loc[codigo]
        if p.min() == 0 or p.max() / p.min() > 3:
            descripcion = pasan.loc[(pasan["BLOQUE"] == b) & (pasan["CODIGO"] == codigo), "DESCRIPCION"].iloc[0]
            candidatos.append((p.max() - p.min(), codigo, descripcion, p, variables))
    candidatos.sort(key=lambda x: -x[0])
    filas_top = [[f"`{codigo}`", descripcion, *[dec(x, 3) + " %" for x in p.to_numpy()], variables]
                 for _, codigo, descripcion, p, variables in candidatos[:12]]

    partes = [
        "# Filtro de dimensionalidad (actividad 3.1, script 14)",
        f"Generado por `{ruta}/scripts/14_filtro_codigos.py`. Entrada: `data/processed/{DESARROLLO.name}`, de la versión "
        f"{version['version']} de la partición (SHA-256 `{version['sha256_desarrollo']}`). Salidas: `data/processed/{DESTINO.name}` "
        f"(todos los códigos) y `{ruta}/reportes/{LISTA.name}` (la lista fija). No se abre el conjunto de prueba. Las "
        f"decisiones están en `{ruta}/bitacora.md` (D45, H30 y H31).",
        f"**Filtro:** para cada variable de reingreso, pasa un código si su V de Cramér es mayor o igual a {dec(v_min, 3)} y lo "
        f"tienen al menos {fmt(par['casos_minimos'])} casos de estudio con dato en esa variable. Se usa {NIVELES[par['nivel']]}, "
        "en cualquier posición y una vez por caso. El filtro se calcula una sola vez, con todo el conjunto de desarrollo, y la "
        "lista queda fija: las etapas siguientes la aplican sin recalcularla (propuesta, Etapa 3).",

        "## 1. Códigos de los casos de estudio",
        tabla_md(["Bloque", "Códigos distintos", "Pares caso–código", "Promedio por caso"],
                 [[NOMBRE_BLOQUE[b], fmt(r["codigos"]), fmt(r["pares"]), dec(r["pares"] / info["casos"], 2)]
                  for b, r in info["bloques"].items()]),
        f"Casos de estudio de desarrollo: {fmt(info['casos'])}.",

        "## 2. Códigos que pasan el filtro",
        "Cada variable usa los casos de estudio con dato en ella: las variables de 30 días no incluyen los casos sin 60 días "
        "de seguimiento (D30), y las de misma CDM no incluyen los partos (D38).",
        tabla_md(["Variable", "Casos con dato", "Reingresos", "Diagnósticos que pasan", "Procedimientos que pasan", "Total"],
                 filas_pasan),

        "## 3. Sensibilidad de los umbrales",
        "Cuántos códigos pasarían con cada combinación de umbrales: total (diagnósticos + procedimientos). Solo se cuentan; "
        "la lista fija es la de los umbrales principales.",
        tabla_md(["V mínima", "Casos mínimos", *[f"`{k}`" for k in objetivos]], filas_sens),

        "## 4. Cuánto reingreso necesita un código para pasar",
        f"La V mide cuánto explica el código del reingreso de todos los casos, así que un código con pocos casos necesita una "
        f"diferencia muy grande para llegar a {dec(v_min, 3)} (H30). La tabla da la tasa de reingreso mínima con que pasaría un "
        "código que sube el riesgo, según cuántos casos lo tienen. Un código que baja el riesgo necesita muchos casos para "
        "pasar, aunque ninguno de ellos reingrese (última fila).",
        tabla_md(["Casos con el código", *[f"`{k}`" for k in objetivos]], filas_tasa),

        "## 5. Los códigos con mayor V",
        *mayores,

        "## 6. Códigos que pasan en varias variables",
        tabla_md(["Bloque", "Pasan en alguna variable", *[f"En {i}" for i in range(len(objetivos), 0, -1)]], filas_listas),

        "## 7. Códigos que pasan y cambian con los años",
        "Códigos que pasan cuya frecuencia (porcentaje de los casos de estudio del año que tienen el código) varía más del "
        "triple entre el año de menor y el de mayor frecuencia (H31). El filtro no cambia, pero ayuda a interpretar la "
        "validación temporal.",
        tabla_md(["Variable", *[NOMBRE_BLOQUE[b] for b in BLOQUES]], filas_cambio),
        f"De esos {fmt(len(candidatos))} códigos (contando una vez los que pasan en varias variables), los doce con la "
        "mayor diferencia entre su año de mayor y su año de menor frecuencia:",
        tabla_md(["Código", "Descripción", *[str(a) for a in anios], "Pasa en"], filas_top),

        "## 8. Parámetros usados por este script",
        tabla_md(["Parámetro", "Valor", "Descripción"],
                 [[f"`{k}`", f"`{v.replace('|', ' / ')}`", desc] for k, (v, desc) in par["descripcion"].items()]),

        "## 9. Archivos de salida",
        f"`data/processed/{DESTINO.name}` tiene una fila por variable de reingreso y código, pase o no el filtro. "
        f"`{ruta}/reportes/{LISTA.name}` tiene solo los que pasan, sin las columnas `CHI2`, `VALOR_P` y `PASA`; se lee con "
        "`sep=\";\"`, `decimal=\",\"` y la columna `CODIGO` como texto (los procedimientos pueden empezar con cero, como `00.14`).",
        tabla_md(["Columna", "Contenido"], [
            ["`VARIABLE`", "Variable de reingreso."],
            ["`BLOQUE`", "`DIAGNOSTICO` (CIE-10) o `PROCEDIMIENTO` (CIE-9-MC)."],
            ["`CODIGO`", "El código."],
            ["`DESCRIPCION`", "Descripción según las tablas del DEIS (`Datos/Tablas auxiliares`)."],
            ["`CASOS`", "Casos de estudio con dato en la variable que tienen el código."],
            ["`REINGRESOS`", "De ellos, los que reingresan."],
            ["`TASA_CON_CODIGO` y `TASA_SIN_CODIGO`", "Porcentaje de reingreso de los casos con el código y sin él."],
            ["`CHI2` y `VALOR_P`", "Chi-cuadrado de Pearson de la tabla de 2×2 y su valor p (1 grado de libertad)."],
            ["`V`", "V de Cramér: raíz(chi-cuadrado / casos con dato). Va de 0 (sin relación) a 1."],
            ["`DIRECCION`", "`sube` si el reingreso es mayor con el código, `baja` si es menor."],
            ["`PASA`", "Verdadero si el código pasa los dos umbrales."],
        ]),

        "## 10. Verificaciones",
        "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in verificaciones),
    ]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {REPORTE}")


def main() -> None:
    inicio = time.time()
    par = cargar_parametros()
    version = comprobar_version()
    print(f"Partición: versión {version['version']}. Leyendo los casos de estudio...", flush=True)
    casos = leer_casos(par)
    print(f"{fmt(len(casos))} casos de estudio. Calculando la asociación de cada código...", flush=True)
    todo, info = filtrar(par, casos)
    del casos
    agregar_descripciones(todo)
    verificaciones = [(f"El conjunto de desarrollo es el de la versión {version['version']} registrada de la partición", True)]
    verificaciones += verificar(todo, info, par, version)
    verificaciones += escribir(todo)
    escribir_reporte(todo, info, par, version, verificaciones)
    fallidas = [texto for texto, ok in verificaciones if not ok]
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(fallidas)}")
    for texto in fallidas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
