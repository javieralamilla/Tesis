# Análisis de reingresos hospitalarios sobre datos GRD — Código

Los datos originales del DEIS están fuera de esta carpeta, en `..\Datos\` (`txt\`, `Zip\` y `Tablas auxiliares\`), y nunca se modifican.

## Estructura

El trabajo se organiza en una carpeta por actividad de la Carta Gantt. Cada carpeta de actividad contiene sus `scripts\`, sus `reportes\` y, si corresponde, sus `reglas\`.

| Carpeta | Contenido | En Git |
|---|---|---|
| `1.2_exploracion_calidad/` | Scripts que examinan los datos sin modificarlos, y sus reportes: identificador de paciente, cobertura de catálogos y perfil de columnas. | Sí |
| `2.1_integracion_homogenizacion/` | Scripts que transforman los datos (conversión, homogenización, integración y diccionario), sus reportes y las tablas de reglas revisables en Excel. | Sí |
| `2.2_depuracion_etiquetado/` | Depuración y etiquetado del reingreso: scripts, reportes, su propia `bitacora.md`, las tablas `reglas/criterios_exclusion.csv` (qué exclusiones están activas, con su justificación) y `reglas/parametros.csv` (umbrales), y `pruebas/`, con los programas que contrastan los resultados con otro método. | Sí |
| `2.3_validacion_particion/` | Partición inicial en desarrollo (80 %) y prueba (20 %) y reserva del conjunto de prueba: script, reporte, su propia `bitacora.md`, `reglas/parametros.csv` (semilla del proyecto, tamaño de la prueba y variable principal) y `pruebas/`, con el programa que contrasta la partición. | Sí |
| `data/interim/` | Parquet intermedios generados por los scripts (`crudo_<año>`, `homog_<año>`, `ids_<año>`). Compartida por todas las actividades. | No |
| `data/processed/` | Tabla integrada 2019–2024 (`grd_2019_2024.parquet`), tabla depurada (`grd_depurado.parquet`), tabla etiquetada con las variables objetivo (`grd_etiquetado.parquet`), conjunto de cada egreso (`particion.parquet`) y de cada identificador de paciente (`particion_identificadores.parquet`), y conjunto de desarrollo (`desarrollo.parquet`), que es el único que usan las etapas de modelado. | No |
| `data/reserva/` | Conjunto de prueba (`prueba.parquet`). Está apartado, como archivo de solo lectura: no se abre hasta la evaluación final. Su hash está registrado en `docs/version_particion.csv`. | No |
| `docs/` | Documentación transversal: `bitacora.md` (hallazgos y decisiones de las actividades 1.2 y 2.1) y su versión Word; `diccionario_datos.md` (las 136 columnas de la tabla integrada); `diccionario_conjunto_analitico.md` (las 163 columnas de la tabla etiquetada, que es la que usan las etapas siguientes); `version_conjunto_analitico.csv` (versiones registradas de esa tabla, con su hash) y `version_particion.csv` (versiones registradas de la partición, con el hash del conjunto de prueba). | Sí |
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
| 08 | 2.2 | `2.2_depuracion_etiquetado/scripts/08_depurar.py` | Elimina los duplicados, asigna la persona (y marca la identidad ambigua) y el episodio asistencial (traslados) y marca los criterios de exclusión de `reglas/criterios_exclusion.csv`. | `data/processed/grd_depurado.parquet`, `reportes/08_depuracion.md`, `reportes/08_derivaciones_por_hospital.csv` |
| 09 | 2.2 | `2.2_depuracion_etiquetado/scripts/09_etiquetar.py` | Calcula las cuatro variables objetivo de reingreso no planificado (7 y 30 días; por cualquier causa y misma CDM) de cada caso de estudio. | `data/processed/grd_etiquetado.parquet`, `reportes/09_etiquetado.md`, `reportes/09_tasas_por_hospital.csv` |
| 10 | 2.3 | `2.3_validacion_particion/scripts/10_particionar.py` | Reparte los identificadores de paciente entre desarrollo (80 %) y prueba (20 %), estratificando por bloque y por las cuatro variables objetivo, y aparta el conjunto de prueba. Se ejecuta después del script 12: solo reparte la versión registrada de la tabla etiquetada. | `data/processed/particion.parquet`, `data/processed/particion_identificadores.parquet`, `data/processed/desarrollo.parquet`, `data/reserva/prueba.parquet`, `reportes/10_particion.md`, `docs/version_particion.csv` |
| 11 | 2.2 | `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py` | Análisis de sensibilidad: vuelve a calcular las cuatro variables cambiando una decisión cada vez (actividades de 2019, cirugía mayor ambulatoria, sesiones Z51, CDM 13 y 14, censura sin margen, identidad ambigua). Usa las funciones de los scripts 08 y 09 y no modifica las tablas de datos; no depende del script 10. | `reportes/11_sensibilidad.md` |
| 12 | 2.2 | `2.2_depuracion_etiquetado/scripts/12_diccionario_version.py` | Describe las columnas de la tabla etiquetada y registra su versión: el hash SHA-256 del archivo y de lo que lo produce. Hay que ejecutarlo de nuevo cada vez que la tabla cambia; no depende del script 10. | `docs/diccionario_conjunto_analitico.md`, `docs/version_conjunto_analitico.csv` |

Los reportes y las reglas de cada script están en la carpeta de su actividad. Para ejecutar un script, desde `Codigo`:

```
.venv\Scripts\python.exe 2.1_integracion_homogenizacion\scripts\05_homogenizar.py
```

## Pruebas independientes

Los resultados de la actividad 2.2 se contrastan con programas que los vuelven a calcular con otro método, sin usar las funciones de los scripts 08, 09 y 11. Están en `2.2_depuracion_etiquetado/pruebas/` y se ejecutan con un solo comando, que tarda unos 8 minutos y deja `2.2_depuracion_etiquetado/reportes/pruebas_independientes.md`:

```
.venv\Scripts\python.exe 2.2_depuracion_etiquetado\pruebas\ejecutar_pruebas.py
```

Hay que ejecutarlas después de volver a generar las tablas (scripts 08, 09 y 11) y de registrar la versión (script 12).

La partición de la actividad 2.3 tiene su propio contraste, que tarda cerca de un minuto y deja `2.3_validacion_particion/reportes/pruebas_independientes.md`. Sirve también para comprobar, antes de la evaluación final, que el conjunto de prueba conserva el hash registrado:

```
.venv\Scripts\python.exe 2.3_validacion_particion\pruebas\verificar_10_particion.py
```

## Orden para regenerar todo desde la tabla integrada

Los scripts 08 y 09 generan la tabla etiquetada; el 11, el análisis de sensibilidad; el 12 registra la versión; las pruebas de la 2.2 la contrastan; el 10 hace la partición sobre la versión registrada, y su prueba la contrasta.

## Entorno

Desde esta carpeta (`Codigo`):

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Bitácoras

`docs/bitacora.md` registra los hallazgos y decisiones de las actividades 1.2 y 2.1. Desde la actividad 2.2, cada actividad lleva su propia bitácora dentro de su carpeta (`2.2_depuracion_etiquetado/bitacora.md` y `2.3_validacion_particion/bitacora.md`), con códigos que continúan la numeración.

La versión Word se regenera cada vez que una bitácora cambia (requiere Node.js):

```
cd herramientas\bitacora_word
npm install
npm run generar
npm run generar:2.2
npm run generar:2.3
```

`npm run generar` actualiza `docs/bitacora.docx`; `npm run generar:2.2` y `npm run generar:2.3` actualizan el `bitacora.docx` de la carpeta de cada actividad.

## Semilla del proyecto

Todo componente aleatorio usa la semilla declarada en `2.3_validacion_particion/reglas/parametros.csv` (2026): la partición inicial y, en las etapas siguientes, la validación cruzada y los modelos.
