# Análisis de sensibilidad (actividad 2.2, script 11)

Generado por `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py`. Cada escenario vuelve a calcular las cuatro variables objetivo cambiando una sola decisión respecto del análisis principal, con las mismas funciones de los scripts 08 y 09. El cambio se aplica solo en memoria: no se modifican las tablas de reglas ni las tablas de datos. El análisis principal es el de `data/processed/grd_etiquetado.parquet`.

## 1. Tabla de sensibilidad

Cada tasa usa los casos de estudio con seguimiento suficiente para su ventana. Entre paréntesis, la diferencia con el análisis principal en puntos porcentuales. En las dos variables relacionadas, además, los partos (CDM sin reingreso relacionado posible) quedan sin dato (bitácora D38), salvo en las filas que los vuelven a incluir: la de los partos con valor 0 y la de las CDM unidas.

| Escenario | Qué cambia | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| Análisis principal | Ninguno | 4.192.410 | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
| Con las actividades que solo existen en 2019 | E04 desactivado | 4.275.385 | 2,11 % (+0,04) | 1,29 % (+0,03) | 5,99 % (+0,09) | 3,59 % (+0,04) |
| Con la cirugía mayor ambulatoria | E13 desactivado | 5.036.703 | 1,79 % (-0,28) | 1,05 % (-0,21) | 5,10 % (-0,80) | 2,94 % (-0,61) |
| Con las sesiones de tratamiento | E14 desactivado | 4.274.335 | 2,08 % (+0,01) | 1,24 % (-0,02) | 5,94 % (+0,04) | 3,50 % (-0,05) |
| Con los partos en las variables relacionadas, con valor 0 | `cdm_sin_relacionado` vacío | 4.192.410 | 2,07 % (+0,00) | 1,08 % (-0,18) | 5,90 % (+0,00) | 3,03 % (-0,52) |
| Con las CDM 13 y 14 como una sola | `cdm_agrupadas` = 13+14 (la CDM 14 vuelve a tener dato) | 4.192.410 | 2,07 % (+0,00) | 1,17 % (-0,09) | 5,90 % (+0,00) | 3,19 % (-0,36) |
| Censura sin margen: solo los días de la ventana | `censura_margen_dias` = 0 | 4.313.289 | 2,06 % (-0,01) | 1,26 % (+0,00) | 5,89 % (-0,01) | 3,54 % (-0,01) |
| Solo los traslados con marca explícita | `traslado_exige_marca` = SI | 4.195.786 | 2,12 % (+0,05) | 1,30 % (+0,04) | 5,95 % (+0,05) | 3,59 % (+0,04) |
| Con los derivados sin continuación como casos de estudio | E07 y E08 desactivados | 4.286.199 | 2,12 % (+0,05) | 1,30 % (+0,04) | 5,98 % (+0,08) | 3,59 % (+0,04) |
| Sin los casos con identidad ambigua | Se quitan los casos con `IDENTIDAD_AMBIGUA` | 4.129.132 | 2,03 % (-0,04) | 1,25 % (-0,01) | 5,79 % (-0,11) | 3,49 % (-0,06) |

Casos de estudio que cada escenario agrega o quita, y casos comunes que cambian en alguna de las variables:

| Escenario | Casos que se agregan | Casos que dejan de serlo | Casos comunes con alguna variable distinta |
|---|---|---|---|
| Con las actividades que solo existen en 2019 | 83.073 | 98 | 3.083 |
| Con la cirugía mayor ambulatoria | 844.293 | 0 | 0 |
| Con las sesiones de tratamiento | 81.925 | 0 | 0 |
| Con los partos en las variables relacionadas, con valor 0 | 0 | 0 | 0 |
| Con las CDM 13 y 14 como una sola | 0 | 0 | 0 |
| Censura sin margen: solo los días de la ventana | 120.879 | 0 | 0 |
| Solo los traslados con marca explícita | 3.376 | 0 | 75 |
| Con los derivados sin continuación como casos de estudio | 93.789 | 0 | 0 |
| Sin los casos con identidad ambigua | 0 | 63.278 | 0 |

## 2. Con las actividades que solo existen en 2019

Criterio E04: Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019.

El criterio deja fuera, en los dos papeles, los tipos de actividad que solo se registraron en 2019. Al incluirlos cambian los casos de estudio y también los reingresos de las demás altas de ese año. Casos de estudio de 2019:

|  | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| Análisis principal | 807.143 | 2,05 % | 1,25 % | 5,70 % | 3,49 % |
| Con esas actividades | 890.118 | 2,27 % | 1,36 % | 6,15 % | 3,66 % |

Composición de los casos de estudio de 2019 en el escenario, por tipo de actividad:

| Tipo de actividad | Casos de estudio | % | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| HOSPITALIZACIÓN | 807.046 | 90,7 % | 2,18 % | 1,31 % | 6,05 % | 3,68 % |
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
| HOSPITALIZACIÓN | 4.192.410 | 83,2 % | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
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

## 5. Con los partos en las variables relacionadas, con valor 0

Es la forma de cálculo anterior a la revisión del profesor guía del 13 de octubre de 2026: los partos se quedan en las variables relacionadas con valor 0. Ese 0 es obligatorio, porque ningún reingreso puede ser de su CDM (reporte 09, sección 5; bitácora D38). Los casos de estudio y el reingreso por cualquier causa no cambian.

| Variable | Análisis principal: casos con dato | Con reingreso | % | Con los partos, con valor 0: casos con dato | Con reingreso | % |
|---|---|---|---|---|---|---|
| `REING_7D_CDM` | 3.577.243 | 45.195 | 1,26 % | 4.192.410 | 45.195 | 1,08 % |
| `REING_30D_CDM` | 3.498.460 | 124.256 | 3,55 % | 4.101.883 | 124.256 | 3,03 % |

## 6. Con las CDM 13 y 14 como una sola

Cambia solo el reingreso relacionado: los casos de estudio y el reingreso por cualquier causa son los mismos. Al unir las CDM, la que no tenía reingreso relacionado posible (bitácora D38) vuelve a tener dato, así que cada columna tiene sus propios casos con dato.

| Variable | Análisis principal: casos con dato | Con reingreso | % | Con esas CDM como una sola: casos con dato | Con reingreso | % |
|---|---|---|---|---|---|---|
| `REING_7D_CDM` | 3.577.243 | 45.195 | 1,26 % | 4.192.410 | 49.087 | 1,17 % |
| `REING_30D_CDM` | 3.498.460 | 124.256 | 3,55 % | 4.101.883 | 130.654 | 3,19 % |

El detalle por CDM del caso de estudio está en la sección 5 del reporte 09.

## 7. Censura sin margen: solo los días de la ventana

Sin el margen, una ventana se considera observada si cabe entera antes del cierre del bloque. Los casos que así ganan dato son las altas más cercanas al cierre, y parte de sus reingresos no se ve porque termina después del cierre (reporte 09, sección 6). La tabla compara su tasa observada con la del análisis principal:

| Variable | Casos que ganan dato | Con reingreso observado | % | Tasa del análisis principal |
|---|---|---|---|---|
| `REING_7D` | 120.879 | 2.093 | 1,73 % | 2,07 % |
| `REING_7D_CDM` | 105.217 | 1.080 | 1,03 % | 1,26 % |
| `REING_30D` | 118.298 | 6.623 | 5,60 % | 5,90 % |
| `REING_30D_CDM` | 102.840 | 3.302 | 3,21 % | 3,55 % |

## 8. Solo los traslados con marca explícita

La regla del análisis principal (bitácora D19) une al mismo episodio asistencial un ingreso en otro hospital el mismo día del alta o al día siguiente, aunque no conste el traslado. En este escenario solo los une si consta: alta por derivación en el egreso anterior o procedencia desde otro hospital en el ingreso. Los ingresos que comienzan antes del alta anterior (estadías solapadas) siguen unidos, porque la persona todavía no había salido y no pueden ser un reingreso con ninguna regla. Un ingreso que deja de unirse abre un episodio nuevo: el egreso anterior puede pasar a ser caso de estudio, y el ingreso, a contar como su reingreso si no es planificado.

|  | Cantidad |
|---|---|
| Ingresos que dejan de unirse y pasan a abrir un episodio | 3.755 |
| Casos de estudio con `REING_7D` (análisis principal → escenario) | 86.609 → 88.742 (+2.133 casos, 2,5 % más) |
| Casos de estudio con `REING_7D_CDM` (análisis principal → escenario) | 45.195 → 46.496 (+1.301 casos, 2,9 % más) |
| Casos de estudio con `REING_30D` (análisis principal → escenario) | 241.953 → 244.119 (+2.166 casos, 0,9 % más) |
| Casos de estudio con `REING_30D_CDM` (análisis principal → escenario) | 124.256 → 125.606 (+1.350 casos, 1,1 % más) |

### Por qué los casos con `REING_7D` no aumentan tanto como los ingresos que dejan de unirse

Lo pidió explicar la revisión del profesor guía del 24 de octubre de 2026 (observación O3). Cada ingreso que deja de unirse comienza el mismo día del alta anterior o al día siguiente, así que podría darle a esa alta un reingreso a 7 días. No lo hace en dos situaciones: cuando el alta anterior no es caso de estudio por otro criterio de la tabla, y cuando el ingreso separado no cuenta como reingreso no planificado (bitácora D20 y D33). Además, unos pocos casos que ya eran de estudio ganan un reingreso: el ingreso separado cae dentro de su ventana y antes, como continuación de un traslado, no contaba.

|  | Cantidad |
|---|---|
| Ingresos que dejan de unirse (cada uno con su propia alta anterior) | 3.755 |
| Alta anterior que no es caso de estudio por el criterio E13 (cirugía mayor ambulatoria) | −229 |
| Alta anterior que no es caso de estudio por el criterio E11 (seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta) | −101 |
| Alta anterior que no es caso de estudio por el criterio E14 (sesión de tratamiento: diagnóstico principal Z51) | −35 |
| Alta anterior que no es caso de estudio por el criterio E06 (alta por fallecimiento) | −11 |
| Alta anterior que no es caso de estudio por el criterio E09 (sin GRD válido: sin código GRD o con CDM 99) | −3 |
| **Casos de estudio que se agregan** (las altas anteriores) | **3.376** |
| … con `REING_7D` = 1, porque el ingreso separado es un reingreso no planificado | 2.116 |
| … con `REING_7D` = 1 por otro ingreso no planificado dentro de la ventana (el separado no cuenta) | 8 |
| … con `REING_7D` = 0, porque el ingreso separado es de tipo PROGRAMADA | 909 |
| … con `REING_7D` = 0, porque el ingreso separado es un parto o una cesárea (GRD 146 o 147) | 317 |
| … con `REING_7D` = 0, porque el ingreso separado es una sesión de tratamiento | 24 |
| … con `REING_7D` = 0, porque el ingreso separado no tiene tipo de ingreso | 2 |
| Casos que ya eran de estudio y pasan de 0 a 1 en `REING_7D` | 9 |
| **Aumento de casos con `REING_7D`** | **2.124 + 9 = 2.133** |

Las cadenas de más de dos tramos casi no influyen: los 3.755 ingresos separados vienen de 3.719 episodios del análisis principal (3.684 con 1 separación; 34 con 2 separaciones; 1 con 3 separaciones). Cada separación tiene su propia alta anterior, así que una cadena no reduce el aumento.

El mismo desglose en las cuatro variables:

| Variable | Casos agregados con reingreso | Casos comunes de 0 a 1 | Casos comunes de 1 a 0 | Aumento |
|---|---|---|---|---|
| `REING_7D` | 2.124 | 9 | 0 | 2.133 |
| `REING_7D_CDM` | 1.296 | 5 | 0 | 1.301 |
| `REING_30D` | 2.117 | 49 | 0 | 2.166 |
| `REING_30D_CDM` | 1.300 | 50 | 0 | 1.350 |

## 9. Con los derivados sin continuación como casos de estudio

Criterio E07: Alta por derivación a otro hospital.

Criterio E08: Alta por derivación a una institución privada.

En el análisis principal, los egresos con alta por derivación a otro hospital cuya continuación no aparece en la base (E07) y los derivados a una institución privada (E08) no son casos de estudio: la atención siguió donde la base no la ve, así que no se puede saber si hubo reingreso (censura administrativa del seguimiento). No tienen valor en las variables objetivo, y sí pueden contar como reingreso de un alta anterior. Este escenario los deja como casos de estudio y les calcula las variables con lo que la base sí ve: un reingreso ocurrido fuera de la base queda como 0.

Casos de estudio que el escenario agrega (los derivados) y sus tasas:

|  | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| Análisis principal | 4.192.410 | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
| Derivados que se agregan | 93.789 | 4,38 % | 2,66 % | 9,42 % | 5,20 % |

### Derivados que el escenario no agrega

Lo pidió explicar la revisión del profesor guía del 24 de octubre de 2026 (observación O4). En el análisis principal, E07 y E08 dejan fuera 99.573 derivados (E07: 76.605; E08: 22.968). Al desactivar esos criterios, cada derivado pasa al siguiente criterio de la tabla: los que cumplen alguno de los posteriores siguen fuera, por ese criterio.

|  | E07 | E08 | Total |
|---|---|---|---|
| Quedan fuera por E09 (sin GRD válido: sin código GRD o con CDM 99) | 52 | 15 | 67 |
| Quedan fuera por E11 (seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta) | 3.505 | 726 | 4.231 |
| Quedan fuera por E13 (cirugía mayor ambulatoria) | 1.087 | 194 | 1.281 |
| Quedan fuera por E14 (sesión de tratamiento: diagnóstico principal Z51) | 153 | 52 | 205 |
| **Se agregan como casos de estudio** | 71.808 | 21.981 | **93.789** |
| **Derivados excluidos en el análisis principal** | 76.605 | 22.968 | **99.573** |

Por año del archivo, los que quedan fuera por cada criterio: E09, 2019: 10, 2020: 11, 2021: 14, 2022: 12, 2023: 9, 2024: 11; E11, 2020: 1.865, 2024: 2.366; E13, 2019: 257, 2020: 295, 2021: 343, 2022: 127, 2023: 138, 2024: 121; E14, 2019: 58, 2020: 43, 2021: 27, 2022: 18, 2023: 24, 2024: 35.

De los 93.789 derivados que se agregan, 91.594 tienen seguimiento suficiente para las variables de 30 días; los otros 2.195 quedan sin dato en ellas, como cualquier caso de estudio con el alta cerca del cierre del bloque.

## 10. Sin los casos con identidad ambigua

Casos de estudio del análisis principal según la columna `IDENTIDAD_AMBIGUA` (reporte 08, sección 3):

| Identidad | Casos de estudio | % | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| Ambigua | 63.278 | 1,5 % | 4,18 % | 2,34 % | 12,88 % | 7,12 % |
| Sin inconsistencias | 4.129.132 | 98,5 % | 2,03 % | 1,25 % | 5,79 % | 3,49 % |

Una diferencia entre los dos grupos no prueba por sí sola que haya reingresos falsos: un identificador con más egresos tiene más oportunidades de registrar un dato distinto, y también más reingresos. El efecto de dejar fuera estos casos es el de la última fila de la tabla de la sección 1.

## 11. Verificaciones

- El escenario principal reproduce exactamente las columnas de `grd_etiquetado.parquet` (persona, episodio, alta final, motivo de exclusión, caso de estudio y las variables objetivo): **sí**.
- Las verificaciones del etiquetado (script 09) se cumplen en todos los escenarios: **sí**.
- Al desactivar un criterio que solo afecta al papel de caso de estudio, los casos comunes conservan sus variables: **sí**.
- Desglose de traslados: cada ingreso separado tiene su propia alta anterior, y esas altas son exactamente las que pasan a cerrar un episodio: **sí**.
- Desglose de traslados: los casos de estudio que se agregan son exactamente las altas anteriores que no quedan fuera por otro criterio, y ningún caso deja de serlo: **sí**.
- Desglose de traslados: en cada variable, los casos agregados con reingreso más los casos comunes que pasan de 0 a 1, menos los que pasan de 1 a 0, igualan el aumento: **sí**.
- Desglose de derivados: los que quedan fuera por un criterio posterior más los que se agregan suman todos los derivados excluidos por E07 y E08: **sí**.
