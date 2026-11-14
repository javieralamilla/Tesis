# Análisis de reingresos hospitalarios sobre datos GRD — Código

Los datos originales del DEIS están fuera de esta carpeta, en `..\Datos\` (`txt\`, `Zip\` y `Tablas auxiliares\`), y nunca se modifican.

## Estructura

El trabajo se organiza en una carpeta por actividad de la Carta Gantt. Cada carpeta de actividad contiene sus `scripts\`, sus `reportes\` y, si corresponde, sus `reglas\`.

| Carpeta | Contenido | En Git |
|---|---|---|
| `1.2_exploracion_calidad/` | Scripts que examinan los datos sin modificarlos, y sus reportes: identificador de paciente, cobertura de catálogos y perfil de columnas. | Sí |
| `2.1_integracion_homogenizacion/` | Scripts que transforman los datos (conversión, homogenización, integración y diccionario), sus reportes y las tablas de reglas revisables en Excel. | Sí |
| `2.2_depuracion_etiquetado/` | Depuración y etiquetado del reingreso: scripts, reportes, su propia `bitacora.md`, las tablas `reglas/criterios_exclusion.csv` (qué exclusiones están activas, con su justificación) y `reglas/parametros.csv` (umbrales), y `pruebas/`, con los programas que contrastan los resultados con otro método. | Sí |
| `2.3_validacion_particion/` | Partición inicial en desarrollo (80 %) y prueba (20 %), reserva del conjunto de prueba y grupos de la validación temporal: scripts, reportes, su propia `bitacora.md`, `reglas/parametros.csv` (semilla del proyecto, tamaño de la prueba, variable principal y años de la validación temporal) y `pruebas/`, con los programas que contrastan la partición y los grupos. | Sí |
| `3.1_filtro_dimensionalidad/` | Ingeniería de variables y filtro de dimensionalidad (Etapa 3 de la propuesta): deja, para cada variable de reingreso, los códigos de diagnósticos y procedimientos con un tamaño de efecto (V de Cramér) mayor o igual a 0,01 y al menos 100 casos (lista A), más tres listas para comparar y las listas de cada pliegue de la validación cruzada, arma las demás variables de cada caso de estudio (las de la propuesta, la historia de 12 meses, el índice de comorbilidad y las demás columnas del CMBD) y junta todo en las tablas para los modelos. Scripts, reportes (entre ellos la lista fija de códigos retenidos, `reportes/14_codigos_retenidos.csv`), su propia `bitacora.md`, `reglas/` (`parametros.csv`, con los umbrales de los dos scripts; `prevision_grupos.csv`, `provincia_region.csv`, `comorbilidad_quan2005.csv`, con los códigos de Quan et al., 2005, `pesos_elixhauser.csv`, con los pesos de Moore et al., 2017, y de van Walraven et al., 2009, y `columnas_modelos.csv`, con el papel y la descripción de cada columna de las tablas para los modelos) y `pruebas/`, con los programas que contrastan el filtro, las variables y las tablas. | Sí |
| `3.2_entrenamiento_modelos/` | Entrenamiento de la regresión logística con multa L1, Random Forest y XGBoost con la validación cruzada de cinco pliegues (Etapas 4 y 5 de la propuesta), sobre las tablas para los modelos de la actividad 3.1, y comparación de las listas de códigos y del modelo sin hospital. Se ejecuta en el servidor del laboratorio (D58 y D65). Scripts, reportes, su propia `bitacora.md` (decisiones D58 a D67 y hallazgos H35 y H36), `reglas/parametros.csv` (las variables, los modelos, las listas, los valores de cada modelo, los procesadores, la ponderación, los sorteos de las métricas, la regla de los 0 y los márgenes de las comparaciones) y `pruebas/`, con los programas que contrastan el entrenamiento y las métricas. | Sí |
| `data/interim/` | Parquet intermedios generados por los scripts (`crudo_<año>`, `homog_<año>`, `ids_<año>`). Compartida por todas las actividades. | No |
| `data/processed/` | Tabla integrada 2019–2024 (`grd_2019_2024.parquet`), tabla depurada (`grd_depurado.parquet`), tabla etiquetada con las variables objetivo (`grd_etiquetado.parquet`), conjunto de cada egreso (`particion.parquet`) y de cada identificador de paciente (`particion_identificadores.parquet`), conjunto de desarrollo (`desarrollo.parquet`), que es el único que usan las etapas de modelado, grupos de la validación temporal y pliegues de la validación cruzada de sus casos de estudio (`validacion_temporal.parquet`), asociación de cada código de diagnóstico o procedimiento con cada variable de reingreso, pase o no el filtro (`filtro_codigos.parquet`), códigos de cada lista, de todo desarrollo y de cada pliegue (`listas_codigos.parquet`), las 30 variables de cada caso de estudio de desarrollo (`variables_casos.parquet`) y las tablas que leen los modelos: una fila por caso de estudio de desarrollo (`modelos_casos.parquet`) y una por caso y código (`modelos_codigos.parquet`). En `predicciones_3.2/`, las predicciones fuera de pliegue de la validación cruzada, una tabla por combinación de variable, modelo, lista, hospital y ponderación (script 17, en el servidor). En `metricas_3.2/`, las métricas de cada combinación, sin sorteo y en cada uno de los 1.000 sorteos de pacientes (script 18, en el servidor). | No |
| `data/reserva/` | Conjunto de prueba (`prueba.parquet`). Está apartado, como archivo de solo lectura: no se abre hasta la evaluación final. Su hash está registrado en `docs/version_particion.csv`. | No |
| `docs/` | Documentación transversal: `bitacora.md` (hallazgos y decisiones de las actividades 1.2 y 2.1) y su versión Word; `diccionario_datos.md` (las 136 columnas de la tabla integrada); `diccionario_conjunto_analitico.md` (las 163 columnas de la tabla etiquetada, que es la que usan las etapas siguientes); `version_conjunto_analitico.csv` (versiones registradas de esa tabla, con su hash) `version_particion.csv` (versiones registradas de la partición, con el hash del conjunto de prueba); `diccionario_tablas_modelos.md` (las columnas de las tablas para los modelos y cómo se usan) y `version_tablas_modelos.csv` (versiones registradas de esas tablas, con su hash). | Sí |
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
| 08 | 2.2 | `2.2_depuracion_etiquetado/scripts/08_depurar.py` | Elimina los duplicados, asigna la persona (y marca la identidad ambigua) y el episodio asistencial (traslados) y marca los criterios de exclusión de `reglas/criterios_exclusion.csv`, entre ellos los tratamientos periódicos (E15). | `data/processed/grd_depurado.parquet`, `reportes/08_depuracion.md`, `reportes/08_derivaciones_por_hospital.csv` |
| 09 | 2.2 | `2.2_depuracion_etiquetado/scripts/09_etiquetar.py` | Calcula las cuatro variables objetivo de reingreso no planificado (7 y 30 días; por cualquier causa y misma CDM) de cada caso de estudio. | `data/processed/grd_etiquetado.parquet`, `reportes/09_etiquetado.md`, `reportes/09_tasas_por_hospital.csv` |
| 10 | 2.3 | `2.3_validacion_particion/scripts/10_particionar.py` | Reparte los identificadores de paciente entre desarrollo (80 %) y prueba (20 %), estratificando por bloque y por las cuatro variables objetivo, y aparta el conjunto de prueba. Desde la versión 3 conserva el reparto registrado (`reparto` = REGISTRADO): cada identificador queda en el conjunto que ya tenía. Se ejecuta después del script 12: solo reparte la versión registrada de la tabla etiquetada. | `data/processed/particion.parquet`, `data/processed/particion_identificadores.parquet`, `data/processed/desarrollo.parquet`, `data/reserva/prueba.parquet`, `reportes/10_particion.md`, `docs/version_particion.csv` |
| 11 | 2.2 | `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py` | Análisis de sensibilidad: vuelve a calcular las cuatro variables cambiando una decisión cada vez (actividades de 2019, cirugía mayor ambulatoria, sesiones Z51, partos con valor 0 en las variables relacionadas, CDM 13 y 14, censura sin margen, solo traslados con marca, derivados como casos de estudio, tratamientos periódicos, identidad ambigua). En los escenarios de traslados y derivados desglosa las cifras que pidió explicar la revisión del profesor guía del 24 de octubre de 2026. Usa las funciones de los scripts 08 y 09 y no modifica las tablas de datos; no depende del script 10. | `reportes/11_sensibilidad.md` |
| 12 | 2.2 | `2.2_depuracion_etiquetado/scripts/12_diccionario_version.py` | Describe las columnas de la tabla etiquetada y registra su versión: el hash SHA-256 del archivo y de lo que lo produce. Hay que ejecutarlo de nuevo cada vez que la tabla cambia; no depende del script 10. | `docs/diccionario_conjunto_analitico.md`, `docs/version_conjunto_analitico.csv` |
| 13 | 2.3 | `2.3_validacion_particion/scripts/13_validacion_temporal.py` | Marca los grupos de la validación temporal interna: cada caso de estudio de desarrollo es de entrenamiento (2019–2022) o de evaluación (2023–2024), y en la evaluación se separan los pacientes nuevos de los ya vistos en 2021–2022. Asigna además el pliegue de la validación cruzada (1 a 5), con todos los casos de un paciente en el mismo pliegue. Lee solo el conjunto de desarrollo y se ejecuta después del script 10. | `data/processed/validacion_temporal.parquet`, `reportes/13_validacion_temporal.md` |
| 14 | 3.1 | `3.1_filtro_dimensionalidad/scripts/14_filtro_codigos.py` | Filtro de dimensionalidad: para cada código de diagnóstico (CIE-10) o de procedimiento (CIE-9-MC) de los casos de estudio de desarrollo, arma la tabla de 2×2 con cada variable de reingreso y calcula el chi-cuadrado, su valor p y la V de Cramér. Deja la lista fija de los códigos que pasan los umbrales de `reglas/parametros.csv` (lista A), las listas para comparar (C, agrupada y sin filtro) y las listas A, C y agrupada de cada pliegue, y cuenta cuántos pasarían con los umbrales de la sensibilidad. Lee solo el conjunto de desarrollo y se ejecuta después del script 13. | `data/processed/filtro_codigos.parquet`, `data/processed/listas_codigos.parquet`, `reportes/14_codigos_retenidos.csv`, `reportes/14_filtro_codigos.md` |
| 15 | 3.1 | `3.1_filtro_dimensionalidad/scripts/15_variables_casos.py` | Variables de los casos de estudio de desarrollo, que no pasan por el filtro: las administrativas y demográficas de la propuesta, la historia de 12 meses con la marca de ventana cortada, el índice de reingreso de Moore con las condiciones de Elixhauser de los diagnósticos secundarios (con el conteo, van Walraven y Charlson como comparación en el reporte) y las demás columnas del CMBD, con las tablas de `reglas/`. Lee solo el conjunto de desarrollo y se ejecuta después del script 10. | `data/processed/variables_casos.parquet`, `reportes/15_variables_casos.md` |
| 16 | 3.1 | `3.1_filtro_dimensionalidad/scripts/16_tablas_modelos.py` | Cierre de la actividad 3.1: junta lo que dejaron los scripts 13, 14 y 15 en las tablas que leen los modelos de la actividad 3.2. Una fila por caso de estudio de desarrollo, con los identificadores, las columnas de la validación, las 30 variables y las cuatro variables objetivo, y una fila por caso y código de alguna lista. Comprueba que cada código tenga los mismos casos que en el filtro, describe las columnas y registra la versión. Lee solo el conjunto de desarrollo y se ejecuta después del script 15. | `data/processed/modelos_casos.parquet`, `data/processed/modelos_codigos.parquet`, `docs/diccionario_tablas_modelos.md`, `docs/version_tablas_modelos.csv`, `reportes/16_tablas_modelos.md` |
| 17 | 3.2 | `3.2_entrenamiento_modelos/scripts/17_entrenar_modelos.py` | Entrena la regresión logística con multa L1, Random Forest y XGBoost con la validación cruzada de cinco pliegues y guarda la probabilidad que le da a cada caso el modelo que no lo vio (la predicción fuera de pliegue). Se ejecuta por etapas, en el orden de D64 (`tiempos`, `ensayo`, `base`, `sin_filtro`, `agrupada`, `sin_hospital` y `c`), con `--etapa`; antes comprueba la versión de las tablas para los modelos, y no repite lo ya guardado. Usa los valores de `reglas/parametros.csv`. Se ejecuta en el servidor del laboratorio, con el entorno de D65 y dentro de tmux, después del script 16. | `data/processed/predicciones_3.2/`, `reportes/17_registro.csv`, `reportes/17_entrenamiento.md` |
| 18 | 3.2 | `3.2_entrenamiento_modelos/scripts/18_metricas.py` | Calcula, con las predicciones fuera de pliegue del script 17, las métricas de cada combinación: AUPRC (precisión promedio), AUROC, Brier, prevalencia e intercepto y pendiente de calibración, en general y por año del alta, con intervalos de 1.000 sorteos de pacientes, los mismos en todas las combinaciones. Con esos sorteos da el veredicto del ensayo de la ponderación y los de la lista A frente a las otras listas y sin hospital. Calcula solo lo que falta, con varias combinaciones a la vez. Se ejecuta en el servidor, después de cada etapa del script 17. | `data/processed/metricas_3.2/`, `reportes/18_metricas.csv`, `reportes/18_comparaciones.csv`, `reportes/18_metricas.md` |

Los reportes y las reglas de cada script están en la carpeta de su actividad. Para ejecutar un script, desde `Codigo`:

```
.venv\Scripts\python.exe 2.1_integracion_homogenizacion\scripts\05_homogenizar.py
```

Los scripts 17 y 18 y sus pruebas no se ejecutan en el portátil, sino en la Terminal del servidor, dentro de tmux, desde `~/Tesis_Javiera/Codigo` y con el Python del entorno de D65 (bitácora de la 3.2):

```
"$HOME/Tesis_Javiera/entorno/bin/python" 3.2_entrenamiento_modelos/scripts/17_entrenar_modelos.py --etapa tiempos
```

```
"$HOME/Tesis_Javiera/entorno/bin/python" 3.2_entrenamiento_modelos/scripts/18_metricas.py
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

Los grupos de la validación temporal (script 13) se contrastan con otro programa, que también reconstruye los pliegues, y deja `2.3_validacion_particion/reportes/pruebas_validacion_temporal.md`:

```
.venv\Scripts\python.exe 2.3_validacion_particion\pruebas\verificar_13_validacion_temporal.py
```

El filtro de la actividad 3.1 (script 14) se contrasta con otro programa, que vuelve a calcular por otro camino una muestra de códigos y revisa la tabla completa y las listas, también las de una muestra de pliegues. Tarda unos 3 minutos y deja `3.1_filtro_dimensionalidad/reportes/pruebas_filtro_codigos.md`:

```
.venv\Scripts\python.exe 3.1_filtro_dimensionalidad\pruebas\verificar_14_filtro_codigos.py
```

Las variables de los casos de estudio (script 15) se contrastan con otro programa, que compara las tablas de reglas con una segunda transcripción, recalcula con otro método las variables de todos los casos y arma la historia de 12 meses egreso por egreso en una muestra. Tarda unos 2 minutos y deja `3.1_filtro_dimensionalidad/reportes/pruebas_variables_casos.md`:

```
.venv\Scripts\python.exe 3.1_filtro_dimensionalidad\pruebas\verificar_15_variables_casos.py
```

Las tablas para los modelos (script 16) se contrastan con otro programa, que vuelve a sacar los códigos de cada caso por otro camino y compara los pares uno por uno, compara cada columna con su origen, ejecuta la receta del diccionario y revisa el registro de versión. Tarda unos 3 minutos y deja `3.1_filtro_dimensionalidad/reportes/pruebas_tablas_modelos.md`:

```
.venv\Scripts\python.exe 3.1_filtro_dimensionalidad\pruebas\verificar_16_tablas_modelos.py
```

El entrenamiento (script 17) se contrasta con otro programa, que revisa cada tabla de predicciones y el registro, vuelve a armar por otro camino la matriz de una muestra de casos de cada vuelta y entrena otra vez una vuelta de XGBoost, también con las respuestas de los casos de validación desordenadas. Se ejecuta en el servidor, después del script 17, y deja `3.2_entrenamiento_modelos/reportes/pruebas_entrenamiento.md`:

```
"$HOME/Tesis_Javiera/entorno/bin/python" 3.2_entrenamiento_modelos/pruebas/verificar_17_entrenamiento.py
```

Las métricas (script 18) se contrastan con otro programa, que recalcula con scikit-learn las áreas y el Brier y con scipy la calibración, rehace desde cero el primer y el último sorteo de cada combinación y vuelve a calcular las comparaciones y sus veredictos con una segunda transcripción de las reglas. Se ejecuta en el servidor, después del script 18, y deja `3.2_entrenamiento_modelos/reportes/pruebas_metricas.md`:

```
"$HOME/Tesis_Javiera/entorno/bin/python" 3.2_entrenamiento_modelos/pruebas/verificar_18_metricas.py
```

## Orden para regenerar todo desde la tabla integrada

Los scripts 08 y 09 generan la tabla etiquetada; el 11, el análisis de sensibilidad; el 12 registra la versión; las pruebas de la 2.2 la contrastan; el 10 hace la partición sobre la versión registrada, y su prueba la contrasta; el 13 marca los grupos de la validación temporal y los pliegues en el conjunto de desarrollo, y su prueba los contrasta; el 14 calcula el filtro de códigos y las listas sobre el conjunto de desarrollo, con los pliegues del 13, y su prueba lo contrasta; el 15 arma las variables de los casos de estudio de desarrollo, y su prueba las contrasta; el 16 junta las tablas para los modelos y registra su versión, y su prueba las contrasta; el 17 entrena los modelos en el servidor, por etapas, y su prueba contrasta las predicciones; el 18 calcula las métricas y los veredictos con esas predicciones, y su prueba los contrasta.

## Entorno

Desde esta carpeta (`Codigo`):

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Bitácoras

`docs/bitacora.md` registra los hallazgos y decisiones de las actividades 1.2 y 2.1. Desde la actividad 2.2, cada actividad lleva su propia bitácora dentro de su carpeta (`2.2_depuracion_etiquetado/bitacora.md`, `2.3_validacion_particion/bitacora.md`, `3.1_filtro_dimensionalidad/bitacora.md` y `3.2_entrenamiento_modelos/bitacora.md`), con códigos que continúan la numeración.

La versión Word se regenera cada vez que una bitácora cambia (requiere Node.js):

```
cd herramientas\bitacora_word
npm install
npm run generar
npm run generar:2.2
npm run generar:2.3
npm run generar:3.1
npm run generar:3.2
```

`npm run generar` actualiza `docs/bitacora.docx`; `npm run generar:2.2`, `npm run generar:2.3`, `npm run generar:3.1` y `npm run generar:3.2` actualizan el `bitacora.docx` de la carpeta de cada actividad.

## Semilla del proyecto

Todo componente aleatorio usa la semilla declarada en `2.3_validacion_particion/reglas/parametros.csv` (2026): la partición inicial y, en las etapas siguientes, la validación cruzada y los modelos.
