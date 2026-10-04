"""Paso 3.0: perfil de las columnas por año, insumo para las reglas de homogenización.

Para cada columna (o grupo de columnas repetidas, como DIAGNOSTICO1-35) y cada año
describe: celdas vacías, valores que representan "sin dato", formatos de fechas,
números y códigos, problemas de texto y, en las variables categóricas, los valores
que aparecen solo en algunos años o que son variantes de un mismo valor.

Solo lee los Parquet crudos; no modifica datos.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 1.2_exploracion_calidad\\scripts\\04_perfil_columnas.py
"""

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_REPORTS = ACTIVIDAD / "reportes"
ANIOS = list(range(2019, 2025))
TRAZABILIDAD = {"ANIO_ARCHIVO", "ARCHIVO_ORIGEN", "FILA_ORIGEN"}
MAX_CATEGORIAS = 400
MAX_FILAS_TABLA = 40
CANDIDATOS_NULO = ["DESCONOCIDO", "DESCONOCIDA", "SIN INFORMACIÓN", "SIN INFORMACION",
                   "NO INFORMADO", "NO IDENTIFICADO", "NO IDENTIFICADA", "NO CONSIGNADO",
                   "IGNORADO", "NO RESPONDE", "NO APLICA", "NULL", "NA", "N/A", "-", "."]
# Valores con forma de RUT: nunca se escriben en los reportes.
FORMA_RUT = re.compile(r"\d{1,2}\.?\d{3}\.?\d{3}(-[\dkK])?")

# Columnas repetidas que se analizan como un solo grupo.
GRUPOS = [
    (r"CIP_ENCRIPTADO|ID_BENEFICIARIO", "ID_PACIENTE (CIP_ENCRIPTADO / ID_BENEFICIARIO)"),
    (r"DIAGNOSTICO\d+", "DIAGNOSTICO1-35"),
    (r"PROCEDIMIENTO\d+", "PROCEDIMIENTO1-30"),
    (r"FECHATRASLADO\d", "FECHATRASLADO1-9"),
    (r"SERVICIOTRASLADO\d", "SERVICIOTRASLADO1-9"),
    (r"CONDICIONDEALTANEONATO\d", "CONDICIONDEALTANEONATO1-4"),
    (r"PESORN\d", "PESORN1-4"),
    (r"SEXORN\d", "SEXORN1-4"),
    (r"RN\dESTADO", "RN1-4ESTADO"),
]
# Columnas cuyo tipo no se deduce bien de su contenido.
TIPO_FIJO = {
    "ID_PACIENTE (CIP_ENCRIPTADO / ID_BENEFICIARIO)": "identificador",
    "MEDICOINTERV1_ENCRIPTADO": "identificador",
    "MEDICOALTA_ENCRIPTADO": "identificador",
    "COD_HOSPITAL": "código",
    "IR_29301_COD_GRD": "código",
    "DIAGNOSTICO1-35": "código",
    "PROCEDIMIENTO1-30": "código",
    "FECHAPROCEDIMIENTO1": "fecha",
    "USOSPABELLON": "número",
}

ES_NUMERO = re.compile(r"-?\d*[.,]?\d+")
ES_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}|\d{2}/\d{2}/\d{4}|\d{4}/\d{2}/\d{2}")


def grupo_de(col: str) -> str:
    for patron, nombre in GRUPOS:
        if re.fullmatch(patron, col):
            return nombre
    return col


def mascara(v: str) -> str:
    """Formato de un valor: dígitos -> 9 y letras -> A (p. ej. '12-03-2023' -> '99-99-9999')."""
    return "".join("9" if ch.isdigit() else "A" if ch.isalpha() else ch for ch in v)


def mascara_corta(v: str) -> str:
    """Formato resumido: '0,5744' -> '9,9'; ',3045' -> ',9'; 'J96.09' -> 'A9.9'."""
    return re.sub(r"A+", "A", re.sub(r"9+", "9", mascara(v)))


def mostrar(v: str) -> str:
    """Valor tal como se escribe en el reporte, ocultando los que tienen forma de RUT."""
    return "«valor con forma de RUT, omitido»" if FORMA_RUT.fullmatch(v.strip()) else f"`{v}`"


def normalizar(v: str) -> str:
    """Clave para detectar variantes: sin espacios sobrantes, mayúsculas y sin tildes."""
    v = unicodedata.normalize("NFKD", v.strip().upper())
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", v)


def contar_anio(anio: int) -> tuple[int, list[str], dict[str, Counter]]:
    pf = pq.ParquetFile(DIR_INTERIM / f"crudo_{anio}.parquet")
    conteos, orden = defaultdict(Counter), []
    for col in pf.schema_arrow.names:
        if col in TRAZABILIDAD:
            continue
        g = grupo_de(col)
        if g not in conteos:
            orden.append(g)
        vc = pc.value_counts(pf.read(columns=[col]).column(0).combine_chunks())
        valores = ["" if v is None else v for v in vc.field("values").to_pylist()]
        conteos[g].update(dict(zip(valores, vc.field("counts").to_pylist())))
    return pf.metadata.num_rows, orden, conteos


def resumir(grupo: str, c: Counter) -> dict:
    total = sum(c.values())
    nulos = {t: c[t] for t in CANDIDATOS_NULO if c.get(t)}
    datos = {v: n for v, n in c.items() if v != "" and v not in nulos}
    n_datos = sum(datos.values())
    exacta, corta = Counter(), Counter()
    espacios = minusculas = danado = numero = fecha = 0
    for v, n in datos.items():
        exacta[mascara(v)] += n
        corta[mascara_corta(v)] += n
        if v != v.strip() or "  " in v:
            espacios += n
        if any(ch.islower() for ch in v):
            minusculas += n
        if "�" in v or "Ã" in v or "Â" in v:
            danado += n
        if ES_NUMERO.fullmatch(v):
            numero += n
        if ES_FECHA.fullmatch(v):
            fecha += n
    if grupo in TIPO_FIJO:
        tipo = TIPO_FIJO[grupo]
    elif n_datos and fecha / n_datos > 0.9:
        tipo = "fecha"
    elif n_datos and numero / n_datos > 0.9:
        tipo = "número"
    elif len(datos) <= MAX_CATEGORIAS:
        tipo = "categoría"
    else:
        tipo = "texto"
    return {
        "tipo": tipo, "total": total, "vacias": c.get("", 0), "nulos": nulos,
        "distintos": len(datos), "espacios": espacios, "minusculas": minusculas,
        "danado": danado, "exacta": exacta, "corta": corta, "n_datos": n_datos,
        "valores": c if len(datos) <= MAX_CATEGORIAS else None,
    }


def formatos(r: dict, tipo: str) -> str:
    m = r["exacta"] if tipo == "fecha" else r["corta"]
    if not r["n_datos"]:
        return "(sin datos)"
    partes = []
    for k, n in m.most_common(3):
        p = 100 * n / r["n_datos"]
        if p >= 0.05 or not partes:
            partes.append(f"`{k}`" + ("" if p >= 99.95 else f" {p:.1f}%"))
    return " / ".join(partes)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    DIR_REPORTS.mkdir(parents=True, exist_ok=True)
    perfiles, filas, orden_global = defaultdict(dict), {}, []
    for anio in ANIOS:
        print(f"Perfilando {anio}...", flush=True)
        filas[anio], orden, conteos = contar_anio(anio)
        for g in orden:
            if g not in orden_global:
                orden_global.append(g)
            perfiles[g][anio] = resumir(g, conteos[g])

    # 1. Resumen por columna
    tabla1 = ["| Columna | Tipo | % vacío 2019·20·21·22·23·24 | \"Sin dato\" explícito (6 años) | Distintos (mín–máx) | Alertas |",
              "|---|---|---|---|---|---|"]
    tipos = {}
    for g in orden_global:
        p = perfiles[g]
        tipo = Counter(r["tipo"] for r in p.values()).most_common(1)[0][0]
        tipos[g] = tipo
        vacio = "·".join(f"{100 * p[a]['vacias'] / p[a]['total']:.0f}" if a in p else "—" for a in ANIOS)
        nulos = Counter()
        for r in p.values():
            nulos.update(r["nulos"])
        nulos_txt = "; ".join(f"`{k}` {fmt(v)}" for k, v in nulos.most_common()) or "—"
        dist = [r["distintos"] for r in p.values()]
        alertas = []
        for clave, nombre in [("espacios", "espacios sobrantes"), ("minusculas", "minúsculas"), ("danado", "texto dañado")]:
            n = sum(r[clave] for r in p.values())
            if n:
                alertas.append(f"{nombre} ({fmt(n)})")
        if tipo in ("fecha", "número", "código", "identificador"):
            principales = {(r["exacta"] if tipo == "fecha" else r["corta"]).most_common(1)[0][0]
                           for r in p.values() if r["n_datos"]}
            if len(principales) > 1:
                alertas.append("**formato distinto entre años**")
        tabla1.append(f"| {g} | {tipo} | {vacio} | {nulos_txt} | {fmt(min(dist))}–{fmt(max(dist))} | {', '.join(alertas) or '—'} |")

    # 2. Formatos por año (fechas, números, códigos e identificadores)
    tabla2 = ["| Columna | " + " | ".join(map(str, ANIOS)) + " |", "|---|" + "---|" * len(ANIOS)]
    for g in orden_global:
        if tipos[g] in ("fecha", "número", "código", "identificador"):
            celdas = [formatos(perfiles[g][a], tipos[g]) if a in perfiles[g] else "—" for a in ANIOS]
            tabla2.append(f"| {g} | " + " | ".join(celdas) + " |")

    # 3. Categorías: valores que no están en todos los años y variantes de un mismo valor
    secciones3 = []
    for g in orden_global:
        p = perfiles[g]
        if tipos[g] != "categoría" or any(r["valores"] is None for r in p.values()):
            continue
        por_valor = defaultdict(dict)
        for a, r in p.items():
            for v, n in r["valores"].items():
                if v != "":
                    por_valor[v][a] = n
        anios_g = sorted(p)
        parciales = sorted((v for v, d in por_valor.items() if len(d) < len(anios_g)),
                           key=lambda v: -sum(por_valor[v].values()))
        variantes = defaultdict(set)
        for v in por_valor:
            variantes[normalizar(v)].add(v)
        variantes = [sorted(s) for s in variantes.values() if len(s) > 1]
        if not parciales and not variantes:
            continue
        partes = [f"### {g}", f"{len(por_valor)} valores distintos en total."]
        if variantes:
            partes.append("**Variantes de un mismo valor** (difieren solo en tildes, espacios o mayúsculas):")
            partes.append("\n".join(
                "- " + " · ".join(f"{mostrar(v)} ({fmt(sum(por_valor[v].values()))})" for v in grupo) for grupo in variantes))
        if parciales:
            partes.append(f"**Valores que no aparecen en todos los años** ({len(parciales)}):")
            filas_t = ["| Valor | " + " | ".join(map(str, anios_g)) + " |", "|---|" + "---|" * len(anios_g)]
            for v in parciales[:MAX_FILAS_TABLA]:
                filas_t.append(f"| {mostrar(v)} | " + " | ".join(fmt(por_valor[v][a]) if a in por_valor[v] else "—" for a in anios_g) + " |")
            if len(parciales) > MAX_FILAS_TABLA:
                filas_t.append(f"| … y {len(parciales) - MAX_FILAS_TABLA} más | " + " | ".join("" for _ in anios_g) + " |")
            partes.append("\n".join(filas_t))
        secciones3.append("\n\n".join(partes))

    informe = "\n\n".join([
        "# Perfil de columnas por año (Paso 3.0)",
        "Generado por `1.2_exploracion_calidad/scripts/04_perfil_columnas.py` sobre `data/interim/crudo_<año>.parquet`. "
        "Las columnas repetidas se agrupan (p. ej. `DIAGNOSTICO1-35`); en ellas el % vacío se calcula "
        "sobre todas las celdas del grupo. Registros por año: "
        + ", ".join(f"{a}: {fmt(n)}" for a, n in filas.items()) + ".",
        "## 1. Resumen por columna",
        "Tipo aparente según el contenido. \"Sin dato\" explícito: valores como `DESCONOCIDO` que "
        "representan ausencia de información.",
        "\n".join(tabla1),
        "## 2. Formatos por año",
        "Formato más frecuente de los valores (9 = dígito, A = letra). En fechas se muestra el formato "
        "exacto; en números y códigos, el resumido (`9,9` = decimal con coma; `,9` = decimal sin cero inicial).",
        "\n".join(tabla2),
        "## 3. Categorías que cambian entre años",
        "\n\n".join(secciones3) or "Sin diferencias.",
    ]) + "\n"
    salida = DIR_REPORTS / "04_perfil_columnas.md"
    salida.write_text(informe, encoding="utf-8")
    print(f"Reporte guardado en {salida}")


if __name__ == "__main__":
    main()
