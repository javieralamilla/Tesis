"""Ejecuta los contrastes independientes de la actividad 2.2 y deja un reporte.

Cada contraste (verificar_08, verificar_09 y verificar_11) vuelve a calcular con otro método lo que
dejaron los scripts 08, 09 y 11, sin usar sus funciones. Este script los ejecuta uno tras otro sobre
los archivos de data/processed/ y escribe reportes/pruebas_independientes.md con el resultado de
cada comprobación y la versión del conjunto analítico que se probó.

Uso (desde la carpeta Codigo):
    .venv\\Scripts\\python.exe 2.2_depuracion_etiquetado\\pruebas\\ejecutar_pruebas.py

Tarda unos 8 minutos. Termina con código 0 si todas las comprobaciones se cumplen y con 1 si alguna falla.
"""

import csv
import hashlib
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ACTIVIDAD = Path(__file__).resolve().parents[1]  # carpeta de la actividad
RAIZ = ACTIVIDAD.parent                          # carpeta Codigo
CONJUNTO = RAIZ / "data" / "processed" / "grd_etiquetado.parquet"
REGISTRO = RAIZ / "docs" / "version_conjunto_analitico.csv"
REPORTE = ACTIVIDAD / "reportes" / "pruebas_independientes.md"
PRUEBAS = [
    ("verificar_08_depuracion.py", "Depuración (script 08)",
     "Duplicados, personas, identidad ambigua, criterios, episodios y papeles de `grd_depurado.parquet`, y la tabla «paso a paso» del reporte 08."),
    ("verificar_09_etiquetado.py", "Etiquetado (script 09)",
     "Las cuatro variables objetivo de `grd_etiquetado.parquet`, de dos formas distintas, y las tablas del reporte 09."),
    ("verificar_11_sensibilidad.py", "Análisis de sensibilidad (script 11)",
     "Casos de estudio y tasas de cada escenario de la tabla del reporte 11, y los desgloses de traslados y derivados de sus secciones 8 y 9."),
]


def sha256(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def version_registrada() -> dict | None:
    if not REGISTRO.exists():
        return None
    with open(REGISTRO, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    return filas[-1] if filas else None


def ejecutar(archivo: str) -> dict:
    """Ejecuta un contraste y separa sus comprobaciones: (texto, se cumple)."""
    inicio = time.time()
    proceso = subprocess.run([sys.executable, "-X", "utf8", "-B", str(Path(__file__).with_name(archivo))],
                             capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    comprobaciones = [(linea.split("] ", 1)[1], linea.startswith("[OK]")) for linea in proceso.stdout.splitlines()
                      if linea.startswith(("[OK]", "[FALLA]"))]
    return {"comprobaciones": comprobaciones, "codigo": proceso.returncode, "segundos": time.time() - inicio,
            "error": proceso.stderr.strip().splitlines()[-15:] if proceso.returncode not in (0, 1) else []}


def main() -> None:
    hash_actual = sha256(CONJUNTO)
    version = version_registrada()
    coincide = version is not None and version["sha256"] == hash_actual
    resultados = []
    for archivo, titulo, _ in PRUEBAS:
        print(f"{titulo}...", flush=True)
        r = ejecutar(archivo)
        fallas = sum(not ok for _, ok in r["comprobaciones"])
        print(f"  {len(r['comprobaciones'])} comprobaciones, {fallas} fallas ({r['segundos']:.0f} s)", flush=True)
        resultados.append(r)
    # Un contraste que no termina bien cuenta como falla, aunque no haya impreso ninguna.
    todo_bien = coincide and all(r["codigo"] == 0 and r["comprobaciones"] for r in resultados)

    ruta = ACTIVIDAD.name
    partes = [
        "# Pruebas independientes de la actividad 2.2",
        f"Generado por `{ruta}/pruebas/ejecutar_pruebas.py` el {date.today():%d-%m-%Y}. Cada programa vuelve a calcular con otro "
        "método lo que dejaron los scripts 08, 09 y 11, sin usar sus funciones, y compara el resultado con los archivos y con "
        "las tablas de los reportes.",
        (f"Conjunto analítico probado: `data/processed/{CONJUNTO.name}`, SHA-256 `{hash_actual}`. "
         + (f"Coincide con la versión {version['version']} registrada el {version['fecha']} en `docs/{REGISTRO.name}`: **sí**."
            if coincide else f"Coincide con la última versión registrada en `docs/{REGISTRO.name}`: **NO**. Hay que registrar la versión "
                             "con el script 12 antes de usar el conjunto.")),
        f"**Resultado: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}.**",
        "\n".join(["| Programa | Qué contrasta | Comprobaciones | Fallas | Segundos |", "|---|---|---|---|---|",
                   *[f"| `{archivo}` | {que} | {len(r['comprobaciones'])} | {sum(not ok for _, ok in r['comprobaciones'])} | {r['segundos']:.0f} |"
                     for (archivo, _, que), r in zip(PRUEBAS, resultados)]]),
    ]
    for (archivo, titulo, _), r in zip(PRUEBAS, resultados):
        partes += [f"## {titulo}", "\n".join(f"- {texto}: **{'sí' if ok else 'NO'}**." for texto, ok in r["comprobaciones"])]
        if r["codigo"] not in (0, 1) or not r["comprobaciones"]:
            partes.append(f"**El programa `{archivo}` no terminó bien** (código {r['codigo']}):\n\n```\n" + "\n".join(r["error"]) + "\n```")
    REPORTE.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print(f"Reporte guardado en {REPORTE}")
    print(f"RESULTADO: {'todas las comprobaciones se cumplen' if todo_bien else 'HAY FALLAS'}")
    sys.exit(0 if todo_bien else 1)


if __name__ == "__main__":
    main()
