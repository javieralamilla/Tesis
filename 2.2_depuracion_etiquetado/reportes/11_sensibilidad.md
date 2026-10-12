# Análisis de sensibilidad (actividad 2.2, script 11)

Generado por `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py`. Cada escenario vuelve a calcular las cuatro variables objetivo cambiando una sola decisión respecto del análisis principal, con las mismas funciones de los scripts 08 y 09. El cambio se aplica solo en memoria: no se modifican las tablas de reglas ni las tablas de datos. El análisis principal es el de `data/processed/grd_etiquetado.parquet`.

## 1. Tabla de sensibilidad

Cada tasa usa los casos de estudio con seguimiento suficiente para su ventana. Entre paréntesis, la diferencia con el análisis principal en puntos porcentuales.

| Escenario | Qué cambia | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| Análisis principal | Ninguno | 4.192.410 | 2,07 % | 1,08 % | 5,90 % | 3,03 % |
| Con las actividades que solo existen en 2019 | E04 desactivado | 4.275.385 | 2,11 % (+0,04) | 1,10 % (+0,02) | 5,99 % (+0,09) | 3,07 % (+0,04) |
| Con la cirugía mayor ambulatoria | E13 desactivado | 5.036.703 | 1,79 % (-0,28) | 0,92 % (-0,16) | 5,10 % (-0,80) | 2,58 % (-0,45) |
| Con las sesiones de tratamiento | E14 desactivado | 4.274.335 | 2,08 % (+0,01) | 1,06 % (-0,02) | 5,94 % (+0,04) | 2,99 % (-0,04) |
| Con las CDM 13 y 14 como una sola | `cdm_agrupadas` = 13+14 | 4.192.410 | 2,07 % (+0,00) | 1,17 % (+0,09) | 5,90 % (+0,00) | 3,19 % (+0,16) |
| Censura sin margen: solo los días de la ventana | `censura_margen_dias` = 0 | 4.313.289 | 2,06 % (-0,01) | 1,07 % (-0,01) | 5,89 % (-0,01) | 3,02 % (-0,01) |
| Sin los casos con identidad ambigua | Se quitan los casos con `IDENTIDAD_AMBIGUA` | 4.129.132 | 2,03 % (-0,04) | 1,06 % (-0,02) | 5,79 % (-0,11) | 2,97 % (-0,06) |

Casos de estudio que cada escenario agrega o quita, y casos comunes que cambian en alguna de las variables:

| Escenario | Casos que se agregan | Casos que dejan de serlo | Casos comunes con alguna variable distinta |
|---|---|---|---|
| Con las actividades que solo existen en 2019 | 83.073 | 98 | 3.083 |
| Con la cirugía mayor ambulatoria | 844.293 | 0 | 0 |
| Con las sesiones de tratamiento | 81.925 | 0 | 0 |
| Con las CDM 13 y 14 como una sola | 0 | 0 | 6.489 |
| Censura sin margen: solo los días de la ventana | 120.879 | 0 | 0 |
| Sin los casos con identidad ambigua | 0 | 63.278 | 0 |

## 2. Con las actividades que solo existen en 2019

Criterio E04: Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019.

El criterio deja fuera, en los dos papeles, los tipos de actividad que solo se registraron en 2019. Al incluirlos cambian los casos de estudio y también los reingresos de las demás altas de ese año. Casos de estudio de 2019:

|  | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| Análisis principal | 807.143 | 2,05 % | 1,05 % | 5,70 % | 2,96 % |
| Con esas actividades | 890.118 | 2,27 % | 1,17 % | 6,15 % | 3,15 % |

Composición de los casos de estudio de 2019 en el escenario, por tipo de actividad:

| Tipo de actividad | Casos de estudio | % | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| HOSPITALIZACIÓN | 807.046 | 90,7 % | 2,18 % | 1,11 % | 6,05 % | 3,11 % |
| HOSPITALIZACIÓN EN URGENCIA | 43.217 | 4,9 % | 4,75 % | 2,84 % | 10,06 % | 5,59 % |
| HOSPITALIZACIÓN DIURNA | 39.855 | 4,5 % | 1,43 % | 0,53 % | 4,02 % | 1,32 % |

Composición clínica: las CDM cuya participación entre los casos de estudio de 2019 cambia más al incluir esas actividades.

| CDM | Análisis principal | Con esas actividades | Diferencia (puntos) |
|---|---|---|---|
| 14 | 15,4 % | 14,0 % | -1,44 |
| 11 | 4,8 % | 5,9 % | +1,11 |
| 13 | 11,0 % | 10,2 % | -0,82 |
| 02 | 0,8 % | 1,4 % | +0,60 |
| 03 | 2,7 % | 3,1 % | +0,42 |
| 08 | 9,5 % | 9,2 % | -0,34 |

## 3. Con la cirugía mayor ambulatoria

Criterio E13: Cirugía mayor ambulatoria.

Casos de estudio del escenario por tipo de actividad:

| Tipo de actividad | Casos de estudio | % | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| HOSPITALIZACIÓN | 4.192.410 | 83,2 % | 2,07 % | 1,08 % | 5,90 % | 3,03 % |
| CIRUGÍA MAYOR AMBULATORIA (CMA) | 844.293 | 16,8 % | 0,41 % | 0,14 % | 1,14 % | 0,33 % |

## 4. Con las sesiones de tratamiento

Criterio E14: Sesión de tratamiento: diagnóstico principal Z51.

Caracterización de los egresos que el criterio deja fuera como caso de estudio (los que el escenario agrega):

|  | Cantidad |
|---|---|
| Casos de estudio que se agregan | 81.925 |
| Personas | 28.428 |
| Personas con 20 casos de estudio o más | 229 (suman 9.264 casos, 11,3 %) |
| Tipo de ingreso PROGRAMADA | 80.345 (98,1 %) |
| Tipo de ingreso URGENCIA | 1.322 (1,6 %) |
| Tipo de ingreso OBSTETRICA | 235 (0,3 %) |
| Tipo de ingreso (sin dato) | 23 (0,0 %) |
| Diagnóstico principal Z51.1 | 49.492 (60,4 %) |
| Diagnóstico principal Z51.8 | 21.402 (26,1 %) |
| Diagnóstico principal Z51.2 | 5.686 (6,9 %) |
| Diagnóstico principal Z51.4 | 2.743 (3,3 %) |
| Diagnóstico principal Z51.0 | 2.333 (2,8 %) |
| Estadía de 0 días (ingreso y alta el mismo día) | 23.927 (29,2 %) |
| Estadía: mediana y percentil 90, en días | 2 y 5 |
| Seguidos de cualquier ingreso dentro de 30 días, también programado | 47.555 (59,3 %) |
| Con reingreso no planificado, `REING_7D` | 2.410 (2,94 %) |
| Con reingreso no planificado, `REING_7D_CDM` | 268 (0,33 %) |
| Con reingreso no planificado, `REING_30D` | 6.534 (8,15 %) |
| Con reingreso no planificado, `REING_30D_CDM` | 819 (1,02 %) |

En cualquier escenario, un ingreso con diagnóstico principal de sesión no cuenta como reingreso no planificado.

## 5. Con las CDM 13 y 14 como una sola

Cambia solo el reingreso relacionado: los casos de estudio y el reingreso por cualquier causa son los mismos.

| Variable | Análisis principal | % | Con esas CDM como una sola | % | Diferencia |
|---|---|---|---|---|---|
| `REING_7D_CDM` | 45.195 | 1,08 % | 49.087 | 1,17 % | +3.892 |
| `REING_30D_CDM` | 124.256 | 3,03 % | 130.654 | 3,19 % | +6.398 |

El detalle por CDM del caso de estudio está en la sección 5 del reporte 09.

## 6. Censura sin margen: solo los días de la ventana

Sin el margen, una ventana se considera observada si cabe entera antes del cierre del bloque. Los casos que así ganan dato son las altas más cercanas al cierre, y parte de sus reingresos no se ve porque termina después del cierre (reporte 09, sección 6). La tabla compara su tasa observada con la del análisis principal:

| Variable | Casos que ganan dato | Con reingreso observado | % | Tasa del análisis principal |
|---|---|---|---|---|
| `REING_7D` | 120.879 | 2.093 | 1,73 % | 2,07 % |
| `REING_7D_CDM` | 120.879 | 1.080 | 0,89 % | 1,08 % |
| `REING_30D` | 118.298 | 6.623 | 5,60 % | 5,90 % |
| `REING_30D_CDM` | 118.298 | 3.302 | 2,79 % | 3,03 % |

## 7. Sin los casos con identidad ambigua

Casos de estudio del análisis principal según la columna `IDENTIDAD_AMBIGUA` (reporte 08, sección 3):

| Identidad | Casos de estudio | % | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| Ambigua | 63.278 | 1,5 % | 4,18 % | 2,17 % | 12,88 % | 6,61 % |
| Sin inconsistencias | 4.129.132 | 98,5 % | 2,03 % | 1,06 % | 5,79 % | 2,97 % |

Una diferencia entre los dos grupos no prueba por sí sola que haya reingresos falsos: un identificador con más egresos tiene más oportunidades de registrar un dato distinto, y también más reingresos. El efecto de dejar fuera estos casos es el de la última fila de la tabla de la sección 1.

## 8. Verificaciones

- El escenario principal reproduce exactamente las columnas de `grd_etiquetado.parquet` (caso de estudio, episodio y las variables objetivo): **sí**.
- Las verificaciones del etiquetado (script 09) se cumplen en todos los escenarios: **sí**.
- Al desactivar un criterio que solo afecta al papel de caso de estudio, los casos comunes conservan sus variables: **sí**.
