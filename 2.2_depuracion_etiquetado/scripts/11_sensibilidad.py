"""Análisis de sensibilidad de la depuración y el etiquetado (actividad 2.2, script 11).

Vuelve a calcular las cuatro variables objetivo cambiando una sola decisión cada vez (un criterio
de exclusión o un parámetro) y compara el resultado con el análisis principal. Usa las mismas
funciones de los scripts 08 y 09, con el cambio aplicado solo en memoria: no modifica las tablas
de reglas ni las tablas de datos. El análisis principal sigue siendo el de grd_etiquetado.parquet.

Escenarios: con las actividades que solo existen en 2019 (E04), con la cirugía mayor ambulatoria
(E13), con las sesiones de tratamiento (E14), con los partos en las variables relacionadas (valor 0),
con las CDM de `cdm_sensibilidad` como una sola, con la censura sin margen, solo con los traslados
que tienen marca explícita, con los derivados sin continuación como casos de estudio (E07 y E08) y
sin los casos de identidad ambigua.

En los escenarios de traslados y derivados, además, desglosa las cifras que la revisión del profesor
guía del 24 de octubre de 2026 pidió explicar: por qué separar episodios suma menos reingresos que
episodios separados (O3) y qué criterio deja fuera a los derivados que no se agregan (O4).

Deja reportes/11_sensibilidad.md.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\scripts\\11_sensibilidad.py
"""

import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_REPORTS = ACTIVIDAD / "reportes"
ETIQUETADO = RAIZ / "data" / "processed" / "grd_etiquetado.parquet"

# Columnas de la tabla integrada que necesita el etiquetado o que describen a los casos de estudio.
ORIGINALES = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "COD_HOSPITAL", "TIPO_ACTIVIDAD", "TIPO_INGRESO", "FECHA_INGRESO",
              "FECHAALTA", "TIPOALTA", "DIAGNOSTICO1", "IR_29301_COD_GRD", "CDM"]
# Columnas que agrega el script 08 y que usa este script.
DEPURACION = ["ID_PERSONA", "IDENTIDAD_AMBIGUA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO"]
ATRIBUTOS = ["ID_EGRESO", "ANIO_ARCHIVO", "BLOQUE_ID", "TIPO_ACTIVIDAD", "TIPO_INGRESO", "FECHA_INGRESO", "FECHAALTA",
             "DIAGNOSTICO1", "CDM", "ID_PERSONA", "IDENTIDAD_AMBIGUA"]
PRINCIPAL = "principal"
MUCHAS_SESIONES = 20                              # casos de estudio de una persona para considerarla de tratamiento reiterado


def cargar_script(nombre: str):
    """Importa otro script de esta carpeta. Su nombre empieza con un número, así que no sirve `import`."""
    ruta = Path(__file__).with_name(nombre)
    spec = importlib.util.spec_from_file_location("script_" + ruta.stem, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def definir_escenarios(m08, m09) -> list[dict]:
    """Cada escenario cambia una decisión, como si se editara una celda de las tablas de reglas.

    criterios: código -> SI o NO. parametros: nombre -> valor. sin: columna que marca los casos que se dejan fuera.
    """
    lista_criterios = m08.cargar_criterios()
    criterio = {c["codigo"]: c["criterio"] for c in lista_criterios}
    activo = {c["codigo"]: c["activo"] for c in lista_criterios}
    par8, par9 = m08.cargar_parametros(), m09.cargar_parametros()
    escenarios = [
        {"clave": PRINCIPAL, "nombre": "Análisis principal", "cambio": "Ninguno"},
        {"clave": "actividad_2019", "nombre": "Con las actividades que solo existen en 2019", "cambio": "E04 desactivado", "criterios": {"E04": "NO"}},
        {"clave": "cma", "nombre": "Con la cirugía mayor ambulatoria", "cambio": "E13 desactivado", "criterios": {"E13": "NO"}},
        {"clave": "sesiones", "nombre": "Con las sesiones de tratamiento", "cambio": "E14 desactivado", "criterios": {"E14": "NO"}},
    ]
    if par9["cdm_sin_relacionado"]:
        escenarios.append({"clave": "partos", "nombre": "Con los partos en las variables relacionadas, con valor 0",
                           "cambio": "`cdm_sin_relacionado` vacío", "parametros": {"cdm_sin_relacionado": ""}})
    if par9["grupos_sensibilidad"] and not par9["grupos_cdm"]:
        valor = par9["descripcion"]["cdm_sensibilidad"][0]
        vuelven = [x for x in par9["cdm_sin_relacionado"] if x in par9["cdm_sensibilidad"]]
        escenarios.append({"clave": "cdm", "nombre": "Con las CDM " + "; ".join(par9["grupos_sensibilidad"]) + " como una sola",
                           "cambio": f"`cdm_agrupadas` = {valor}" + (f" (la CDM {' y '.join(vuelven)} vuelve a tener dato)" if vuelven else ""),
                           "parametros": {"cdm_agrupadas": valor}})
    if par9["margen"] > 0:
        escenarios.append({"clave": "censura", "nombre": "Censura sin margen: solo los días de la ventana",
                           "cambio": "`censura_margen_dias` = 0", "parametros": {"censura_margen_dias": "0"}})
    if not par8["traslado_exige_marca"]:
        escenarios.append({"clave": "traslados", "nombre": "Solo los traslados con marca explícita",
                           "cambio": "`traslado_exige_marca` = SI", "parametros": {"traslado_exige_marca": "SI"}})
    if activo["E07"] and activo["E08"]:
        escenarios.append({"clave": "derivados", "nombre": "Con los derivados sin continuación como casos de estudio",
                           "cambio": "E07 y E08 desactivados", "criterios": {"E07": "NO", "E08": "NO"}})
    escenarios.append({"clave": "identidad", "nombre": "Sin los casos con identidad ambigua",
                       "cambio": "Se quitan los casos con `IDENTIDAD_AMBIGUA`", "sin": "IDENTIDAD_AMBIGUA"})
    for e in escenarios:
        e["criterio"] = {cod: criterio[cod] for cod in e.get("criterios", {})}
    return escenarios


def calcular(m08, m09, originales: pd.DataFrame, df: pd.DataFrame, genericos: np.ndarray, base: dict, esc: dict,
             otros: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Aplica la depuración y el etiquetado con los cambios del escenario.

    Devuelve los casos de estudio (atributos y variables objetivo), las columnas de todos los egresos que
    permiten comparar con los archivos, y las verificaciones del etiquetado que no se cumplen.
    """
    parametros = {**esc.get("parametros", {}), **(otros or {})}
    nuevo, _ = m08.aplicar_criterios(df, genericos, m08.cargar_parametros(parametros), m08.cargar_criterios(esc.get("criterios")), base)
    d = pd.concat([originales, nuevo[DEPURACION].reset_index(drop=True)], axis=1)
    etiquetas, info = m09.etiquetar(m09.cargar_parametros(parametros), d[m09.COLUMNAS])
    variables = etiquetas.drop(columns="ID_EGRESO")
    caso = d["ES_CASO_ESTUDIO"].to_numpy()
    casos = pd.concat([d.loc[caso, ATRIBUTOS], variables.loc[caso]], axis=1).reset_index(drop=True)
    todos = pd.concat([d[["ID_EGRESO", "ID_PERSONA", "ID_EPISODIO", "ES_CASO_ESTUDIO", "PUEDE_SER_REINGRESO"]],
                       nuevo[["ALTA_FINAL_EPISODIO", "MOTIVO_EXCLUSION"]].reset_index(drop=True), variables], axis=1)
    return casos, todos, [texto for texto, ok in info["verificaciones"] if not ok]


def resumen(casos: pd.DataFrame, variables: list[str], mascara=None) -> dict:
    """Casos de estudio y, por variable, (casos con dato, casos con reingreso)."""
    c = casos if mascara is None else casos[np.asarray(mascara)]
    return {"casos": len(c), **{k: (int(c[k].notna().sum()), int((c[k] == 1).sum())) for k in variables}}


def comparar(principal: pd.DataFrame, casos: pd.DataFrame, variables: list[str]) -> dict:
    """Casos que el escenario agrega o quita respecto del análisis principal, y casos comunes con alguna variable distinta."""
    m = principal[["ID_EGRESO", *variables]].merge(casos[["ID_EGRESO", *variables]], on="ID_EGRESO", how="outer",
                                                  suffixes=("_P", "_E"), indicator=True)
    ambos = m[m["_merge"] == "both"]
    distinto = np.zeros(len(ambos), dtype=bool)
    for k in variables:
        p = ambos[f"{k}_P"].to_numpy(dtype="float64", na_value=np.nan)
        e = ambos[f"{k}_E"].to_numpy(dtype="float64", na_value=np.nan)
        distinto |= ~np.isnan(p) & ~np.isnan(e) & (p != e)
    return {"agregados": int((m["_merge"] == "right_only").sum()), "quitados": int((m["_merge"] == "left_only").sum()),
            "distintos": int(distinto.sum())}


# ------------------------------------------------------------------ detalle de cada escenario
def detalle_actividad_2019(principal: pd.DataFrame, casos: pd.DataFrame, variables: list[str]) -> dict:
    """Prevalencia y composición de los años en que el escenario agrega casos de estudio."""
    agregados = casos[~casos["ID_EGRESO"].isin(principal["ID_EGRESO"])]
    anios = sorted(int(a) for a in agregados["ANIO_ARCHIVO"].unique())
    p, e = principal[principal["ANIO_ARCHIVO"].isin(anios)], casos[casos["ANIO_ARCHIVO"].isin(anios)]
    cdm = pd.DataFrame({"p": p["CDM"].value_counts(normalize=True), "e": e["CDM"].value_counts(normalize=True)}).fillna(0) * 100
    cdm["dif"] = cdm["e"] - cdm["p"]
    cdm = cdm.reindex(cdm["dif"].abs().sort_values(ascending=False).index).head(6)
    return {"anios": anios, "principal": resumen(p, variables), "escenario": resumen(e, variables),
            "actividad": {a: resumen(e, variables, e["TIPO_ACTIVIDAD"] == a) for a in e["TIPO_ACTIVIDAD"].value_counts().index},
            "cdm": [(k, f["p"], f["e"], f["dif"]) for k, f in cdm.iterrows()]}


def detalle_por_actividad(casos: pd.DataFrame, variables: list[str]) -> dict:
    return {a: resumen(casos, variables, casos["TIPO_ACTIVIDAD"] == a) for a in casos["TIPO_ACTIVIDAD"].value_counts().index}


def detalle_sesiones(principal: pd.DataFrame, casos: pd.DataFrame, todo_ingreso: pd.DataFrame, variables: list[str], larga: int) -> dict:
    """Caracterización de los casos de estudio que el escenario agrega (sesiones de tratamiento)."""
    s = casos[~casos["ID_EGRESO"].isin(principal["ID_EGRESO"])]
    por_persona = s.groupby("ID_PERSONA").size()
    reiteradas = por_persona[por_persona >= MUCHAS_SESIONES]
    estadia = (s["FECHAALTA"] - s["FECHA_INGRESO"]).dt.days
    k = f"REING_{larga}D"
    t = todo_ingreso.loc[todo_ingreso["ID_EGRESO"].isin(s["ID_EGRESO"]), k]
    return {"casos": len(s), "personas": int(len(por_persona)), "reiteradas": (int(len(reiteradas)), int(reiteradas.sum())),
            "ingreso": {str(a): int(n) for a, n in s["TIPO_INGRESO"].fillna("(sin dato)").value_counts().items()},
            "diagnostico": [(str(a), int(n)) for a, n in s["DIAGNOSTICO1"].value_counts().head(5).items()],
            "estadia": (int((estadia == 0).sum()), float(estadia.median()), float(estadia.quantile(0.9))),
            "resumen": resumen(s, variables), "todo_ingreso": (int(t.notna().sum()), int((t == 1).sum()))}


def detalle_censura(principal: pd.DataFrame, casos: pd.DataFrame, variables: list[str]) -> dict:
    """Por variable: los casos que ganan dato al quitar el margen, y cuántos de ellos tienen reingreso observado."""
    m = casos[["ID_EGRESO", *variables]].merge(principal[["ID_EGRESO", *variables]], on="ID_EGRESO", how="left", suffixes=("", "_P"))
    salida = {}
    for k in variables:
        nuevo = m[k].notna() & m[f"{k}_P"].isna()
        salida[k] = (int(nuevo.sum()), int((nuevo & (m[k] == 1)).sum()))
    return salida


# ------------------------------------------------------------------ reporte
def detalle_traslados(originales: pd.DataFrame, p: pd.DataFrame, e: pd.DataFrame, variables: list[str], par9: dict) -> dict:
    """Desglose de los ingresos que dejan de unirse al exigir la marca de traslado (revisión del 24-10-2026, O3).

    p y e: columnas de todos los egresos en el análisis principal y en el escenario, en el mismo orden.
    Cada ingreso que deja de unirse abre un episodio; el egreso que cierra el episodio anterior (el «alta anterior»)
    pasa a ser alta final y puede volverse caso de estudio, con el ingreso separado como su reingreso.
    """
    separado = e["PUEDE_SER_REINGRESO"].to_numpy() & ~p["PUEDE_SER_REINGRESO"].to_numpy()
    nueva_alta = e["ALTA_FINAL_EPISODIO"].to_numpy() & ~p["ALTA_FINAL_EPISODIO"].to_numpy()
    filas_b = np.flatnonzero(separado)
    # Separaciones por episodio del análisis principal: una cadena de varios tramos puede separarse más de una vez.
    por_episodio = pd.Series(p["ID_EPISODIO"].to_numpy()[filas_b]).value_counts().value_counts().sort_index()

    # Alta anterior de cada ingreso separado: el alta final del episodio que lo precede, en el orden del script 08.
    s = pd.DataFrame({"ID_PERSONA": e["ID_PERSONA"], "ID_EPISODIO": e["ID_EPISODIO"], "FECHA_INGRESO": originales["FECHA_INGRESO"],
                      "FECHAALTA": originales["FECHAALTA"], "ID_EGRESO": originales["ID_EGRESO"]})
    s = s[s["ID_EPISODIO"].notna()].sort_values(["ID_PERSONA", "FECHA_INGRESO", "FECHAALTA", "ID_EGRESO"])
    misma_persona = s["ID_PERSONA"].shift(1).eq(s["ID_PERSONA"]).to_numpy(dtype=bool, na_value=False)
    previo = pd.Series(np.where(misma_persona, s["ID_EPISODIO"].shift(1).to_numpy(dtype="float64", na_value=np.nan), np.nan), index=s.index)
    episodio_previo = previo.reindex(filas_b).to_numpy()
    final = e["ALTA_FINAL_EPISODIO"].to_numpy()
    fila_de_final = pd.Series(np.flatnonzero(final), index=e["ID_EPISODIO"].to_numpy(dtype="float64", na_value=np.nan)[final])
    filas_a = fila_de_final.reindex(episodio_previo).to_numpy()
    emparejados = not np.isnan(filas_a).any()
    filas_a = np.nan_to_num(filas_a, nan=0).astype("int64")

    # El ingreso separado, ¿cuenta como reingreso no planificado? Misma regla y precedencia que el script 09 (D20, D33).
    b = originales.iloc[filas_b]
    parto = (b["IR_29301_COD_GRD"].str.startswith(tuple(par9["grd_parto"]), na=False).to_numpy() if par9["grd_parto"]
             else np.zeros(len(b), dtype=bool))
    sesion = (b["DIAGNOSTICO1"].str.startswith(tuple(par9["sesiones"]), na=False).to_numpy() if par9["sesiones"]
              else np.zeros(len(b), dtype=bool))
    tipo = b["TIPO_INGRESO"]
    cuenta = tipo.isin(par9["ingresos_no_planificados"]).to_numpy() & ~parto & ~sesion
    clase = np.select([parto, sesion, tipo.isna().to_numpy()],
                      ["es un parto o una cesárea (GRD " + " o ".join(par9["grd_parto"]) + ")", "es una sesión de tratamiento",
                       "no tiene tipo de ingreso"], default="es de tipo " + tipo.fillna("").astype(str).to_numpy())

    corta = variables[0]                                   # la variable de la ventana más corta por cualquier causa
    a_caso = e["ES_CASO_ESTUDIO"].to_numpy()[filas_a]
    motivo_a = e["MOTIVO_EXCLUSION"].astype("object").to_numpy()[filas_a]
    valor_a = e[corta].to_numpy(dtype="float64", na_value=np.nan)[filas_a]
    con_uno = a_caso & (valor_a == 1)
    con_cero = a_caso & (valor_a == 0)

    p_caso, e_caso = p["ES_CASO_ESTUDIO"].to_numpy(), e["ES_CASO_ESTUDIO"].to_numpy()
    agregado, comun = e_caso & ~p_caso, e_caso & p_caso
    por_variable = {}
    for k in variables:
        vp = p[k].to_numpy(dtype="float64", na_value=np.nan)
        ve = e[k].to_numpy(dtype="float64", na_value=np.nan)
        por_variable[k] = {"agregados": int((agregado & (ve == 1)).sum()), "sube": int((comun & (vp == 0) & (ve == 1)).sum()),
                           "baja": int((comun & (vp == 1) & (ve == 0)).sum()),
                           "aumento": int((e_caso & (ve == 1)).sum()) - int((p_caso & (vp == 1)).sum())}
    motivos = pd.Series(motivo_a[~a_caso]).value_counts()
    return {
        "separados": int(separado.sum()), "por_episodio": {int(k): int(v) for k, v in por_episodio.items()},
        "excluidas": {str(k): int(v) for k, v in motivos.items()}, "agregados": int(a_caso.sum()), "corta": corta,
        "uno_por_separado": int((con_uno & cuenta).sum()), "uno_por_otro": int((con_uno & ~cuenta).sum()),
        "cero": {str(k): int(v) for k, v in pd.Series(clase[con_cero]).value_counts().items()},
        "cero_cuenta": int((con_cero & cuenta).sum()), "sin_dato": int((a_caso & np.isnan(valor_a)).sum()),
        "por_variable": por_variable,
        "verificaciones": [
            ("Desglose de traslados: cada ingreso separado tiene su propia alta anterior, y esas altas son exactamente las que "
             "pasan a cerrar un episodio", emparejados and len(set(filas_a.tolist())) == len(filas_a)
             and set(filas_a.tolist()) == set(np.flatnonzero(nueva_alta).tolist())),
            ("Desglose de traslados: los casos de estudio que se agregan son exactamente las altas anteriores que no quedan "
             "fuera por otro criterio, y ningún caso deja de serlo", int(agregado.sum()) == int(a_caso.sum())
             and bool(agregado[filas_a[a_caso]].all()) and not (p_caso & ~e_caso).any()),
            ("Desglose de traslados: en cada variable, los casos agregados con reingreso más los casos comunes que pasan de 0 a 1, "
             "menos los que pasan de 1 a 0, igualan el aumento", all(v["agregados"] + v["sube"] - v["baja"] == v["aumento"]
                                                                     for v in por_variable.values())),
        ],
    }


def detalle_derivados(originales: pd.DataFrame, p: pd.DataFrame, e: pd.DataFrame, codigos: list[str], nombres: dict) -> dict:
    """Qué criterio posterior deja fuera a los derivados que el escenario no agrega (revisión del 24-10-2026, O4).

    En el escenario E07 y E08 están desactivados, así que el motivo de exclusión de cada derivado es el primer criterio
    posterior de la tabla que cumple; los que no cumplen ninguno se agregan como casos de estudio.
    """
    motivo_p = p["MOTIVO_EXCLUSION"].astype("object")
    derivado = motivo_p.isin(codigos).to_numpy()
    motivo_e = e["MOTIVO_EXCLUSION"].astype("object")[derivado]
    caso_e = e["ES_CASO_ESTUDIO"].to_numpy()[derivado]
    anio = originales["ANIO_ARCHIVO"].to_numpy()[derivado]
    fuera = {}
    for cod in sorted(set(motivo_e.dropna())):
        m = (motivo_e == cod).to_numpy()
        fuera[cod] = {"nombre": nombres[cod], "total": int(m.sum()),
                      "por_codigo": {c: int((m & (motivo_p[derivado] == c).to_numpy()).sum()) for c in codigos},
                      "por_anio": {int(a): int(v) for a, v in pd.Series(anio[m]).value_counts().sort_index().items()}}
    return {"derivados": int(derivado.sum()), "por_codigo": {c: int((motivo_p == c).sum()) for c in codigos},
            "fuera": fuera, "agregados": int(caso_e.sum()),
            "agregados_por_codigo": {c: int((caso_e & (motivo_p[derivado] == c).to_numpy()).sum()) for c in codigos},
            "verificaciones": [("Desglose de derivados: los que quedan fuera por un criterio posterior más los que se agregan suman "
                                "todos los derivados excluidos por " + " y ".join(codigos),
                                sum(f["total"] for f in fuera.values()) + int(caso_e.sum()) == int(derivado.sum())
                                and bool(motivo_e[caso_e].isna().all()) and bool(motivo_e[~caso_e].notna().all()))]}


def inicial_minuscula(texto: str) -> str:
    """Nombre de un criterio dentro de una frase: solo la primera letra en minúscula, para conservar siglas como GRD o Z51."""
    return texto[:1].lower() + texto[1:]


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def pct(parte, total, decimales: int = 2) -> str:
    return f"{100 * parte / total:.{decimales}f}".replace(".", ",") + " %" if total else "—"


def puntos(valor: float) -> str:
    return f"{valor:+.2f}".replace(".", ",")


def tabla_md(encabezados: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def tasas(r: dict, variables: list[str]) -> list[str]:
    return [pct(r[k][1], r[k][0]) for k in variables]


def escribir_reporte(escenarios: list[dict], res: dict, variables: list[str], larga: int, verificaciones: list[tuple[str, bool]],
                     nombre_criterio: dict) -> None:
    ruta = ACTIVIDAD.name
    principal = res[PRINCIPAL]["resumen"]

    def con_diferencia(r: dict, k: str) -> str:
        """Tasa del escenario y, entre paréntesis, su diferencia con el análisis principal en puntos porcentuales."""
        if not r[k][0]:
            return "—"
        # Diferencia entre las tasas ya redondeadas, para que coincida con las cifras que muestra la tabla.
        diferencia = round(100 * r[k][1] / r[k][0], 2) - round(100 * principal[k][1] / principal[k][0], 2)
        return f"{pct(r[k][1], r[k][0])} ({puntos(diferencia)})"

    def tabla_relacionadas(r: dict, columnas: list[str], nombre: str) -> str:
        """Variables relacionadas: casos con dato, con reingreso y tasa, en el análisis principal y en el escenario."""
        return tabla_md(["Variable", "Análisis principal: casos con dato", "Con reingreso", "%", f"{nombre}: casos con dato",
                         "Con reingreso", "%"],
                        [[f"`{k}`", fmt(principal[k][0]), fmt(principal[k][1]), pct(principal[k][1], principal[k][0]),
                          fmt(r[k][0]), fmt(r[k][1]), pct(r[k][1], r[k][0])] for k in columnas])

    def tabla_grupos(titulo: str, grupos: dict) -> str:
        total = sum(r["casos"] for r in grupos.values())
        return tabla_md([titulo, "Casos de estudio", "%", *[f"`{k}`" for k in variables]],
                        [[g, fmt(r["casos"]), pct(r["casos"], total, 1), *tasas(r, variables)] for g, r in grupos.items()])

    partes = [
        "# Análisis de sensibilidad (actividad 2.2, script 11)",
        f"Generado por `{ruta}/scripts/11_sensibilidad.py`. Cada escenario vuelve a calcular las cuatro variables objetivo cambiando "
        "una sola decisión respecto del análisis principal, con las mismas funciones de los scripts 08 y 09. El cambio se aplica "
        "solo en memoria: no se modifican las tablas de reglas ni las tablas de datos. El análisis principal es el de "
        f"`data/processed/{ETIQUETADO.name}`.",

        "## 1. Tabla de sensibilidad",
        "Cada tasa usa los casos de estudio con seguimiento suficiente para su ventana. Entre paréntesis, la diferencia con el "
        "análisis principal en puntos porcentuales."
        + (" En las dos variables relacionadas, además, los partos (CDM sin reingreso relacionado posible) quedan sin dato "
           "(bitácora D38), salvo en las filas que los vuelven a incluir: la de los partos con valor 0 y la de las CDM unidas."
           if any(e["clave"] == "partos" for e in escenarios) else ""),
        tabla_md(["Escenario", "Qué cambia", "Casos de estudio", *[f"`{k}`" for k in variables]],
                 [[e["nombre"], e["cambio"], fmt(res[e["clave"]]["resumen"]["casos"]),
                   *[pct(principal[k][1], principal[k][0]) if e["clave"] == PRINCIPAL else con_diferencia(res[e["clave"]]["resumen"], k)
                     for k in variables]] for e in escenarios]),
        "Casos de estudio que cada escenario agrega o quita, y casos comunes que cambian en alguna de las variables:",
        tabla_md(["Escenario", "Casos que se agregan", "Casos que dejan de serlo", "Casos comunes con alguna variable distinta"],
                 [[e["nombre"], fmt(res[e["clave"]]["comparacion"]["agregados"]), fmt(res[e["clave"]]["comparacion"]["quitados"]),
                   fmt(res[e["clave"]]["comparacion"]["distintos"])] for e in escenarios if e["clave"] != PRINCIPAL]),
    ]
    numero = 1
    for e in escenarios:
        d = res[e["clave"]].get("detalle")
        if d is None:
            continue
        numero += 1
        partes.append(f"## {numero}. {e['nombre']}")
        partes += [f"Criterio {cod}: {texto}." for cod, texto in e["criterio"].items()]
        if e["clave"] == "actividad_2019":
            anios = " y ".join(str(a) for a in d["anios"])
            partes += [
                f"El criterio deja fuera, en los dos papeles, los tipos de actividad que solo se registraron en {anios}. Al incluirlos "
                f"cambian los casos de estudio y también los reingresos de las demás altas de ese año. Casos de estudio de {anios}:",
                tabla_md(["", "Casos de estudio", *[f"`{k}`" for k in variables]], [
                    ["Análisis principal", fmt(d["principal"]["casos"]), *tasas(d["principal"], variables)],
                    ["Con esas actividades", fmt(d["escenario"]["casos"]), *tasas(d["escenario"], variables)],
                ]),
                f"Composición de los casos de estudio de {anios} en el escenario, por tipo de actividad:",
                tabla_grupos("Tipo de actividad", d["actividad"]),
                f"Composición clínica: las CDM cuya participación entre los casos de estudio de {anios} cambia más al incluir esas actividades.",
                tabla_md(["CDM", "Análisis principal", "Con esas actividades", "Diferencia (puntos)"],
                         [[k, pct(p, 100, 1), pct(x, 100, 1), puntos(dif)] for k, p, x, dif in d["cdm"]]),
            ]
        elif e["clave"] == "cma":
            partes += ["Casos de estudio del escenario por tipo de actividad:", tabla_grupos("Tipo de actividad", d)]
        elif e["clave"] == "sesiones":
            r, n = d["resumen"], d["casos"]
            partes += [
                "Caracterización de los egresos que el criterio deja fuera como caso de estudio (los que el escenario agrega):",
                tabla_md(["", "Cantidad"], [
                    ["Casos de estudio que se agregan", fmt(n)],
                    ["Personas", fmt(d["personas"])],
                    [f"Personas con {MUCHAS_SESIONES} casos de estudio o más", f"{fmt(d['reiteradas'][0])} (suman {fmt(d['reiteradas'][1])} casos, {pct(d['reiteradas'][1], n, 1)})"],
                    *[[f"Tipo de ingreso {a}", f"{fmt(v)} ({pct(v, n, 1)})"] for a, v in d["ingreso"].items()],
                    *[[f"Diagnóstico principal {a}", f"{fmt(v)} ({pct(v, n, 1)})"] for a, v in d["diagnostico"]],
                    ["Estadía de 0 días (ingreso y alta el mismo día)", f"{fmt(d['estadia'][0])} ({pct(d['estadia'][0], n, 1)})"],
                    ["Estadía: mediana y percentil 90, en días", f"{d['estadia'][1]:.0f} y {d['estadia'][2]:.0f}"],
                    [f"Seguidos de cualquier ingreso dentro de {larga} días, también programado",
                     f"{fmt(d['todo_ingreso'][1])} ({pct(d['todo_ingreso'][1], d['todo_ingreso'][0], 1)})"],
                    *[[f"Con reingreso no planificado, `{k}`", f"{fmt(r[k][1])} ({pct(r[k][1], r[k][0])})"] for k in variables],
                ]),
                "En cualquier escenario, un ingreso con diagnóstico principal de sesión no cuenta como reingreso no planificado.",
            ]
        elif e["clave"] == "cdm":
            r = res[e["clave"]]["resumen"]
            partes += [
                "Cambia solo el reingreso relacionado: los casos de estudio y el reingreso por cualquier causa son los mismos. Al "
                "unir las CDM, la que no tenía reingreso relacionado posible (bitácora D38) vuelve a tener dato, así que cada "
                "columna tiene sus propios casos con dato.",
                tabla_relacionadas(r, d, "Con esas CDM como una sola"),
                "El detalle por CDM del caso de estudio está en la sección 5 del reporte 09.",
            ]
        elif e["clave"] == "partos":
            r = res[e["clave"]]["resumen"]
            partes += [
                "Es la forma de cálculo anterior a la revisión del profesor guía del 13 de octubre de 2026: los partos se quedan en "
                "las variables relacionadas con valor 0. Ese 0 es obligatorio, porque ningún reingreso puede ser de su CDM "
                "(reporte 09, sección 5; bitácora D38). Los casos de estudio y el reingreso por cualquier causa no cambian.",
                tabla_relacionadas(r, d, "Con los partos, con valor 0"),
            ]
        elif e["clave"] == "traslados":
            r = res[e["clave"]]["resumen"]

            def cambio(k: str) -> str:
                dif = r[k][1] - principal[k][1]
                return (f"{fmt(principal[k][1])} → {fmt(r[k][1])} ({'+' if dif >= 0 else '−'}{fmt(abs(dif))} casos, "
                        f"{pct(abs(dif), principal[k][1], 1)} {'más' if dif >= 0 else 'menos'})")
            partes += [
                "La regla del análisis principal (bitácora D19) une al mismo episodio asistencial un ingreso en otro hospital el "
                "mismo día del alta o al día siguiente, aunque no conste el traslado. En este escenario solo los une si consta: alta "
                "por derivación en el egreso anterior o procedencia desde otro hospital en el ingreso. Los ingresos que comienzan "
                "antes del alta anterior (estadías solapadas) siguen unidos, porque la persona todavía no había salido y no pueden "
                "ser un reingreso con ninguna regla. Un ingreso que deja de unirse abre un episodio nuevo: el egreso anterior "
                "puede pasar a ser caso de estudio, y el ingreso, a contar como su reingreso si no es planificado.",
                tabla_md(["", "Cantidad"], [
                    ["Ingresos que dejan de unirse y pasan a abrir un episodio", fmt(d["nuevos_episodios"])],
                    *[[f"Casos de estudio con `{k}` (análisis principal → escenario)", cambio(k)] for k in variables],
                ]),
            ]
            g = d["desglose"]
            k = g["corta"]
            v = g["por_variable"][k]
            suma = f"{fmt(v['agregados'])} + {fmt(v['sube'])}" + (f" − {fmt(v['baja'])}" if v["baja"] else "")
            cadenas = "; ".join(f"{fmt(n)} con {x} {'separación' if x == 1 else 'separaciones'}" for x, n in g["por_episodio"].items())
            partes += [
                f"### Por qué los casos con `{k}` no aumentan tanto como los ingresos que dejan de unirse",
                "Lo pidió explicar la revisión del profesor guía del 24 de octubre de 2026 (observación O3). Cada ingreso que deja de "
                "unirse comienza el mismo día del alta anterior o al día siguiente, así que podría darle a esa alta un reingreso a "
                f"{k.split('_')[1].rstrip('D')} días. No lo hace en dos situaciones: cuando el alta anterior no es caso de estudio por "
                "otro criterio de la tabla, y cuando el ingreso separado no cuenta como reingreso no planificado (bitácora D20 y D33). "
                "Además, unos pocos casos que ya eran de estudio ganan un reingreso: el ingreso separado cae dentro de su ventana y "
                "antes, como continuación de un traslado, no contaba.",
                tabla_md(["", "Cantidad"], [
                    ["Ingresos que dejan de unirse (cada uno con su propia alta anterior)", fmt(g["separados"])],
                    *[[f"Alta anterior que no es caso de estudio por el criterio {cod} ({inicial_minuscula(nombre_criterio[cod])})", f"−{fmt(n)}"]
                      for cod, n in g["excluidas"].items()],
                    ["**Casos de estudio que se agregan** (las altas anteriores)", f"**{fmt(g['agregados'])}**"],
                    [f"… con `{k}` = 1, porque el ingreso separado es un reingreso no planificado", fmt(g["uno_por_separado"])],
                    [f"… con `{k}` = 1 por otro ingreso no planificado dentro de la ventana (el separado no cuenta)", fmt(g["uno_por_otro"])],
                    *[[f"… con `{k}` = 0, porque el ingreso separado {clase}", fmt(n)] for clase, n in g["cero"].items()],
                    *([[f"… sin dato en `{k}`", fmt(g["sin_dato"])]] if g["sin_dato"] else []),
                    [f"Casos que ya eran de estudio y pasan de 0 a 1 en `{k}`", fmt(v["sube"])],
                    *([[f"Casos que ya eran de estudio y pasan de 1 a 0 en `{k}`", f"−{fmt(v['baja'])}"]] if v["baja"] else []),
                    [f"**Aumento de casos con `{k}`**", f"**{suma} = {fmt(v['aumento'])}**"],
                ]),
                f"Las cadenas de más de dos tramos casi no influyen: los {fmt(g['separados'])} ingresos separados vienen de "
                f"{fmt(sum(g['por_episodio'].values()))} episodios del análisis principal ({cadenas}). Cada separación tiene su propia "
                "alta anterior, así que una cadena no reduce el aumento.",
                "El mismo desglose en las cuatro variables:",
                tabla_md(["Variable", "Casos agregados con reingreso", "Casos comunes de 0 a 1", "Casos comunes de 1 a 0", "Aumento"],
                         [[f"`{x}`", fmt(w["agregados"]), fmt(w["sube"]), fmt(w["baja"]), fmt(w["aumento"])]
                          for x, w in g["por_variable"].items()]),
            ]
        elif e["clave"] == "derivados":
            a = d["agregados"]
            partes += [
                "En el análisis principal, los egresos con alta por derivación a otro hospital cuya continuación no aparece en la "
                "base (E07) y los derivados a una institución privada (E08) no son casos de estudio: la atención siguió donde la "
                "base no la ve, así que no se puede saber si hubo reingreso (censura administrativa del seguimiento). No tienen "
                "valor en las variables objetivo, y sí pueden contar como reingreso de un alta anterior. Este escenario los deja "
                "como casos de estudio y les calcula las variables con lo que la base sí ve: un reingreso ocurrido fuera de la base "
                "queda como 0.",
                "Casos de estudio que el escenario agrega (los derivados) y sus tasas:",
                tabla_md(["", "Casos de estudio", *[f"`{k}`" for k in variables]],
                         [["Análisis principal", fmt(principal["casos"]), *tasas(principal, variables)],
                          ["Derivados que se agregan", fmt(a["casos"]), *tasas(a, variables)]]),
            ]
            g = d["desglose"]
            codigos = list(g["por_codigo"])
            larga_k = next(k for k in variables if k.startswith(f"REING_{larga}D"))
            partes += [
                "### Derivados que el escenario no agrega",
                "Lo pidió explicar la revisión del profesor guía del 24 de octubre de 2026 (observación O4). En el análisis principal, "
                f"{' y '.join(codigos)} dejan fuera {fmt(g['derivados'])} derivados ("
                + "; ".join(f"{c}: {fmt(n)}" for c, n in g["por_codigo"].items()) + "). Al desactivar esos criterios, cada derivado "
                "pasa al siguiente criterio de la tabla: los que cumplen alguno de los posteriores siguen fuera, por ese criterio.",
                tabla_md(["", *codigos, "Total"], [
                    *[[f"Quedan fuera por {cod} ({inicial_minuscula(f['nombre'])})", *[fmt(f["por_codigo"][c]) for c in codigos], fmt(f["total"])]
                      for cod, f in g["fuera"].items()],
                    ["**Se agregan como casos de estudio**", *[fmt(g["agregados_por_codigo"][c]) for c in codigos], f"**{fmt(g['agregados'])}**"],
                    ["**Derivados excluidos en el análisis principal**", *[fmt(g["por_codigo"][c]) for c in codigos], f"**{fmt(g['derivados'])}**"],
                ]),
                "Por año del archivo, los que quedan fuera por cada criterio: "
                + "; ".join(f"{cod}, " + ", ".join(f"{a}: {fmt(n)}" for a, n in f["por_anio"].items()) for cod, f in g["fuera"].items()) + ".",
                f"De los {fmt(a['casos'])} derivados que se agregan, {fmt(a[larga_k][0])} tienen seguimiento suficiente para las "
                f"variables de {larga} días; los otros {fmt(a['casos'] - a[larga_k][0])} quedan sin dato en ellas, como cualquier "
                "caso de estudio con el alta cerca del cierre del bloque.",
            ]
        elif e["clave"] == "censura":
            partes += [
                "Sin el margen, una ventana se considera observada si cabe entera antes del cierre del bloque. Los casos que así "
                "ganan dato son las altas más cercanas al cierre, y parte de sus reingresos no se ve porque termina después del "
                "cierre (reporte 09, sección 6). La tabla compara su tasa observada con la del análisis principal:",
                tabla_md(["Variable", "Casos que ganan dato", "Con reingreso observado", "%", "Tasa del análisis principal"],
                         [[f"`{k}`", fmt(d[k][0]), fmt(d[k][1]), pct(d[k][1], d[k][0]), pct(principal[k][1], principal[k][0])] for k in variables]),
            ]
        elif e["clave"] == "identidad":
            partes += [
                "Casos de estudio del análisis principal según la columna `IDENTIDAD_AMBIGUA` (reporte 08, sección 3):",
                tabla_grupos("Identidad", d),
                "Una diferencia entre los dos grupos no prueba por sí sola que haya reingresos falsos: un identificador con más "
                "egresos tiene más oportunidades de registrar un dato distinto, y también más reingresos. El efecto de dejar fuera "
                "estos casos es el de la última fila de la tabla de la sección 1.",
            ]
    numero += 1
    partes += [f"## {numero}. Verificaciones", "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in verificaciones)]
    salida = DIR_REPORTS / "11_sensibilidad.md"
    salida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {salida}")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    m08, m09 = cargar_script("08_depurar.py"), cargar_script("09_etiquetar.py")
    escenarios = definir_escenarios(m08, m09)
    larga = max(m09.cargar_parametros()["ventanas_dias"])
    print("Preparando la tabla (duplicados y personas)...", flush=True)
    df, _, genericos, base = m08.preparar(m08.cargar_parametros(), m08.cargar_criterios())
    originales = df[ORIGINALES].reset_index(drop=True)

    res, fallidas, solo_caso, desgloses = {}, [], [], []
    nombres = {c["codigo"]: c["criterio"] for c in m08.cargar_criterios()}
    principal = variables = todos_principal = None
    for e in escenarios:
        if "sin" in e:
            continue
        print(f"{e['nombre']} ({time.time() - inicio:.0f} s)", flush=True)
        casos, todos, mal = calcular(m08, m09, originales, df, genericos, base, e)
        fallidas += [f"{e['nombre']}: {texto}" for texto in mal]
        if e["clave"] == PRINCIPAL:
            principal, todos_principal = casos, todos
            variables = [c for c in casos.columns if c.startswith("REING_")]
            res[PRINCIPAL] = {"resumen": resumen(casos, variables)}
            continue
        r = {"resumen": resumen(casos, variables), "comparacion": comparar(principal, casos, variables)}
        if e["clave"] == "actividad_2019":
            r["detalle"] = detalle_actividad_2019(principal, casos, variables)
        elif e["clave"] == "cma":
            r["detalle"] = detalle_por_actividad(casos, variables)
        elif e["clave"] == "sesiones":
            # Otra pasada contando todo ingreso, para saber cuántas sesiones van seguidas de un ingreso programado.
            todo_ingreso, _, mal = calcular(m08, m09, originales, df, genericos, base, e, {"reingreso_solo_no_planificado": "NO"})
            fallidas += [f"{e['nombre']} (todo ingreso): {texto}" for texto in mal]
            r["detalle"] = detalle_sesiones(principal, casos, todo_ingreso, variables, larga)
            del todo_ingreso
        elif e["clave"] in ("cdm", "partos"):
            r["detalle"] = [k for k in variables if k.endswith("_CDM")]      # las variables que cambian
        elif e["clave"] == "censura":
            r["detalle"] = detalle_censura(principal, casos, variables)
        elif e["clave"] == "traslados":
            # Exigir la marca solo separa episodios: los ingresos que dejan de continuar uno pasan a abrir otro.
            r["detalle"] = {"nuevos_episodios": int((todos["PUEDE_SER_REINGRESO"].to_numpy()
                                                     & ~todos_principal["PUEDE_SER_REINGRESO"].to_numpy()).sum()),
                            "desglose": detalle_traslados(originales, todos_principal, todos, variables, m09.cargar_parametros())}
            desgloses += r["detalle"]["desglose"]["verificaciones"]
        elif e["clave"] == "derivados":
            r["detalle"] = {"agregados": resumen(casos[~casos["ID_EGRESO"].isin(principal["ID_EGRESO"])], variables),
                            "desglose": detalle_derivados(originales, todos_principal, todos, list(e["criterios"]), nombres)}
            desgloses += r["detalle"]["desglose"]["verificaciones"]
        if e.get("criterios") and not e.get("parametros"):
            # Un criterio que solo afecta al papel de caso de estudio no puede cambiar las variables de los demás casos.
            papel = {c["codigo"]: c["papel"] for c in m08.cargar_criterios()}
            if all(papel[cod] == "CASO" for cod in e["criterios"]):
                solo_caso.append(r["comparacion"]["quitados"] == 0 and r["comparacion"]["distintos"] == 0
                                 and todos["PUEDE_SER_REINGRESO"].equals(todos_principal["PUEDE_SER_REINGRESO"]))
        res[e["clave"]] = r
        del casos, todos

    for e in escenarios:
        if "sin" in e:
            marcado = principal[e["sin"]].to_numpy()
            resto = principal[~marcado]
            res[e["clave"]] = {"resumen": resumen(resto, variables),
                               "comparacion": {"agregados": 0, "quitados": int(marcado.sum()), "distintos": 0},
                               "detalle": {"Ambigua": resumen(principal, variables, marcado), "Sin inconsistencias": resumen(resto, variables)}}

    # El escenario principal debe reproducir exactamente los archivos que dejaron los scripts 08 y 09.
    archivo = pq.read_table(ETIQUETADO, columns=list(todos_principal.columns)).to_pandas()
    texto = ["MOTIVO_EXCLUSION"]                                   # columnas de texto: se comparan como texto
    iguales = (len(archivo) == len(todos_principal)
               and all((archivo[c].isna().to_numpy() == todos_principal[c].isna().to_numpy()).all()
                       and (archivo[c].to_numpy(dtype="float64", na_value=np.nan)[archivo[c].notna().to_numpy()]
                            == todos_principal[c].to_numpy(dtype="float64", na_value=np.nan)[todos_principal[c].notna().to_numpy()]).all()
                       for c in todos_principal.columns if c not in texto)
               and all((archivo[c].astype("object").fillna("").astype(str).to_numpy()
                        == todos_principal[c].astype("object").fillna("").astype(str).to_numpy()).all() for c in texto))
    verificaciones = [
        (f"El escenario principal reproduce exactamente las columnas de `{ETIQUETADO.name}` (persona, episodio, alta final, motivo de "
         "exclusión, caso de estudio y las variables objetivo)", bool(iguales)),
        ("Las verificaciones del etiquetado (script 09) se cumplen en todos los escenarios", not fallidas),
        ("Al desactivar un criterio que solo afecta al papel de caso de estudio, los casos comunes conservan sus variables", all(solo_caso)),
        *[(t, bool(ok)) for t, ok in desgloses],
    ]
    escribir_reporte(escenarios, res, variables, larga, verificaciones, nombres)
    malas = [texto for texto, ok in verificaciones if not ok] + fallidas
    print(f"Listo en {time.time() - inicio:.0f} s. Verificaciones fallidas: {len(malas)}")
    for texto in malas:
        print(f"  REVISAR: {texto}")


if __name__ == "__main__":
    main()
