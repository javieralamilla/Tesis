# Análisis de reingresos hospitalarios sobre datos GRD — Código

Los datos originales del DEIS están fuera de esta carpeta, en `..\Datos\` (`txt\`, `Zip\` y `Tablas auxiliares\`), y nunca se modifican.

## Estructura

El trabajo se organiza en una carpeta por actividad de la Carta Gantt. Cada carpeta de actividad contiene sus `scripts\`, sus `reportes\` y, si corresponde, sus `reglas\`.

| Carpeta | Contenido | En Git |
|---|---|---|
| `1.2_exploracion_calidad/` | Scripts que examinan los datos sin modificarlos, y sus reportes: identificador de paciente, cobertura de catálogos y perfil de columnas. | Sí |
| `2.1_integracion_homogenizacion/` | Scripts que transforman los datos (conversión, homogenización, integración y diccionario), sus reportes y las tablas de reglas revisables en Excel. | Sí |
| `2.2_depuracion_etiquetado/` | Depuración y etiquetado del reingreso: scripts, reportes, su propia `bitacora.md` y las tablas `reglas/criterios_exclusion.csv` (qué exclusiones están activas) y `reglas/parametros.csv` (umbrales). | Sí |
| `data/interim/` | Parquet intermedios generados por los scripts (`crudo_<año>`, `homog_<año>`, `ids_<año>`). Compartida por todas las actividades. | No |
| `data/processed/` | Tabla integrada 2019–2024 (`grd_2019_2024.parquet`), tabla depurada (`grd_depurado.parquet`) y tabla etiquetada con las variables objetivo (`grd_etiquetado.parquet`). | No |
| `docs/` | Documentación transversal: `bitacora.md` (hallazgos y decisiones de las actividades 1.2 y 2.1), su versión Word y `diccionario_datos.md` (las 136 columnas). | Sí |
| `herramientas/` | Utilidades que no procesan datos, como `bitacora_word/`, que genera la versión Word de la bitácora. | Sí |

Todo lo que está en `data/` se puede regenerar ejecutando los scripts sobre `..\Datos\`.

## Scripts, en orden de ejecución

El número de cada script indica el orden, aunque estén en carpetas distintas.

| N.º | Actividad | Script | Qué hace | Salida |
|---|---|---|---|---|
| 01 | 1.2 | `1.2_exploracion_calidad/scripts/01_diagnostico_ids.py` | Revisa si el identificador de paciente se mantiene entre años. | `reportes/01_diagnostico_ids.md` |
| 02 | 1.2 | `1.2_exploracion_calidad/scripts/02_cobertura_tablas_auxiliares.py` | Cruza los códigos de la base con los catálogos del DEIS. | `reportes/02_cobertura_tablas_auxiliares.md` |
| 03 | 2.1 | `2.1_integracion_homogenizacion/scripts/03_convertir_parquet.py` | Convierte los seis txt a Parquet sin transformar. | `data/interim/crudo_<año>.parquet`, `reportes/03_conversion_parquet.md` |
| 04 | 1.2 | `1.2_exploracion_calidad/scripts/04_perfil_columnas.py` | Describe las 129 columnas por año (formatos, "sin dato", categorías). | `reportes/04_perfil_columnas.md` |
| 05 | 2.1 | `2.1_integracion_homogenizacion/scripts/05_homogenizar.py` | Aplica las reglas de homogenización y `reglas/equivalencias_categorias.csv`. | `data/interim/homog_<año>.parquet`, `reportes/05_homogenizacion.md` |
| 06 | 2.1 | `2.1_integracion_homogenizacion/scripts/06_integrar.py` | Une los seis años, agrega `ID_EGRESO` y marca los duplicados. | `data/processed/grd_2019_2024.parquet`, `reportes/06_integracion.md` |
| 07 | 2.1 | `2.1_integracion_homogenizacion/scripts/07_diccionario_datos.py` | Genera el diccionario de datos con `reglas/descripciones_columnas.csv`. | `docs/diccionario_datos.md` |
| 08 | 2.2 | `2.2_depuracion_etiquetado/scripts/08_depurar.py` | Elimina los duplicados, asigna la persona y el episodio asistencial (traslados) y marca los criterios de exclusión de `reglas/criterios_exclusion.csv`. | `data/processed/grd_depurado.parquet`, `reportes/08_depuracion.md` |
| 09 | 2.2 | `2.2_depuracion_etiquetado/scripts/09_etiquetar.py` | Calcula las cuatro variables objetivo de reingreso no planificado (7 y 30 días; por cualquier causa y misma CDM) de cada caso de estudio. | `data/processed/grd_etiquetado.parquet`, `reportes/09_etiquetado.md` |

Los reportes y las reglas de cada script están en la carpeta de su actividad. Para ejecutar un script, desde `Codigo`:

```
.venv\Scripts\python.exe 2.1_integracion_homogenizacion\scripts\05_homogenizar.py
```

## Entorno

Desde esta carpeta (`Codigo`):

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Bitácoras

`docs/bitacora.md` registra los hallazgos y decisiones de las actividades 1.2 y 2.1. Desde la actividad 2.2, cada actividad lleva su propia bitácora dentro de su carpeta (`2.2_depuracion_etiquetado/bitacora.md`), con códigos que continúan la numeración.

La versión Word se regenera cada vez que una bitácora cambia (requiere Node.js):

```
cd herramientas\bitacora_word
npm install
npm run generar
npm run generar:2.2
```

`npm run generar` actualiza `docs/bitacora.docx` y `npm run generar:2.2`, `2.2_depuracion_etiquetado/bitacora.docx`.
