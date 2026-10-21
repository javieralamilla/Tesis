# Etiquetado del reingreso (actividad 2.2, script 09)

Generado por `2.2_depuracion_etiquetado/scripts/09_etiquetar.py`. Entrada: `data/processed/grd_depurado.parquet`. Salida: `data/processed/grd_etiquetado.parquet`. Umbrales: `2.2_depuracion_etiquetado/reglas/parametros.csv`. Las decisiones están en `2.2_depuracion_etiquetado/bitacora.md`.

Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un episodio asistencial nuevo, y se cuentan los días entre el alta del caso y ese ingreso. El día 0 (ingreso el mismo día del alta) cuenta. Un ingreso que continúa un traslado no cuenta.

**Qué ingreso cuenta como reingreso:** solo el no planificado (regla completa en la sección 4).

**Reingreso relacionado:** se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio. Un ingreso con CDM 99 nunca cuenta como relacionado. La comparación es literal: no se agrupa ninguna CDM.

**Censura:** un reingreso solo aparece en la base si termina antes del cierre del bloque. Por eso cada ventana exige un margen de 30 días además de sus propios días (7 días: alta al menos 37 días antes del cierre; 30 días: alta al menos 60 días antes del cierre). Un caso de estudio que no alcanza el seguimiento de una ventana queda sin dato en las variables de esa ventana (sección 6).

## 1. Las cuatro variables objetivo

Hay 4.192.410 casos de estudio. Cada variable se calcula sobre los que tienen seguimiento suficiente para su ventana. En las dos variables relacionadas, además, los casos de estudio de la CDM 14 quedan sin dato: con la comparación en uso no pueden tener un reingreso de su misma CDM (sección 5; bitácora D38). Por eso tienen menos casos que las variables por cualquier causa.

| Variable | Definición | Casos con dato | Casos con reingreso | % |
|---|---|---|---|---|
| `REING_7D` | 7 días, por cualquier causa | 4.192.410 | 86.609 | 2,07 % |
| `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 3.577.243 | 45.195 | 1,26 % |
| `REING_30D` | 30 días, por cualquier causa | 4.101.883 | 241.953 | 5,90 % |
| `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 3.498.460 | 124.256 | 3,55 % |

Las cuatro están contenidas unas en otras: la ventana de 30 días incluye los primeros 7, y «por cualquier causa» incluye a los relacionados. Combinaciones de las cuatro variables en los 3.498.460 casos de estudio que tienen dato en todas:

| `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` | Casos de estudio | % |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 44.246 | 1,26 % |
| 1 | 0 | 1 | 1 | 916 | 0,03 % |
| 1 | 0 | 1 | 0 | 34.925 | 1,00 % |
| 0 | 0 | 1 | 1 | 79.094 | 2,26 % |
| 0 | 0 | 1 | 0 | 74.086 | 2,12 % |
| 0 | 0 | 0 | 0 | 3.265.193 | 93,33 % |

## 2. Tasas por año del alta

Porcentaje de los casos de estudio de cada año con seguimiento suficiente para la ventana.

| Definición | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| 7 días, por cualquier causa | 2,05 % | 2,09 % | 1,94 % | 1,94 % | 2,13 % | 2,24 % | 2,07 % |
| 7 días, relacionado (misma CDM) | 1,25 % | 1,27 % | 1,19 % | 1,22 % | 1,30 % | 1,34 % | 1,26 % |
| 30 días, por cualquier causa | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,14 % | 6,45 % | 5,90 % |
| 30 días, relacionado (misma CDM) | 3,49 % | 3,40 % | 3,36 % | 3,50 % | 3,69 % | 3,81 % | 3,55 % |
| Casos con seguimiento de 7 días | 807.143 | 559.915 | 636.039 | 707.310 | 771.272 | 710.731 | 4.192.410 |
| Casos con seguimiento de 30 días | 807.143 | 517.790 | 636.039 | 707.310 | 771.272 | 662.329 | 4.101.883 |

2019 y 2020 forman el bloque A de identificadores y 2021 a 2024, el bloque B (D03). En 2020 y 2024 faltan las altas de las últimas semanas del año, por la censura.

**Hospitales incorporados.** 65 hospitales están presentes todos los años y 7 se incorporan después (H05). Un reingreso en un hospital que todavía no informaba a la base no se ve, así que la incorporación de hospitales puede subir la tasa medida. La tabla lo revisa para la variable de 30 días por cualquier causa:

| Hospital del caso de estudio | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Todos los hospitales | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,14 % | 6,45 % | 5,90 % |
| Hospitales presentes todos los años | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,13 % | 6,36 % | 5,88 % |
| Los mismos, sin contar los reingresos que ocurren en un hospital incorporado después | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,11 % | 6,31 % | 5,87 % |
| Hospitales incorporados después | — | — | — | — | 7,71 % | 9,31 % | 8,81 % |

La tercera fila es una cota inferior: descuenta todo caso cuyo primer reingreso ocurre en un hospital incorporado después, aunque tenga otro reingreso dentro de la ventana.

**Calidad del identificador.** Si el identificador hubiera mejorado en 2023 y 2024, con menos egresos sin identificador o con identidad ambigua, se verían más reingresos aunque no hubiera más (revisión del profesor guía del 13 de octubre de 2026, punto 2.3). La tabla lo revisa por año del alta. Los egresos sin identificador o con identificador genérico no pueden ser caso de estudio ni contar como reingreso (E01 y E02); los de identidad ambigua sí, con su marca (D34).

|  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Egresos de la tabla depurada | 1.150.536 | 778.635 | 816.285 | 932.204 | 1.038.670 | 1.084.643 | 5.800.973 |
| Sin identificador de paciente (E01) | 0,72 % | 0,24 % | 0,25 % | 0,32 % | 0,16 % | 0,10 % | 0,31 % |
| Con identificador genérico (E02) | 0,02 % | 0,10 % | 0,04 % | 0,07 % | 0,04 % | 0,01 % | 0,04 % |
| Con identidad ambigua | 1,61 % | 1,53 % | 1,65 % | 1,84 % | 1,67 % | 1,69 % | 1,67 % |
| Casos de estudio con identidad ambigua | 1,32 % | 1,27 % | 1,52 % | 1,70 % | 1,59 % | 1,63 % | 1,51 % |
| `REING_30D`, todos los casos de estudio | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,14 % | 6,45 % | 5,90 % |
| `REING_30D`, sin los casos con identidad ambigua | 5,58 % | 5,52 % | 5,53 % | 5,67 % | 6,05 % | 6,35 % | 5,79 % |
| `REING_30D`, solo los casos con identidad ambigua | 15,18 % | 16,35 % | 11,71 % | 11,50 % | 11,75 % | 12,35 % | 12,88 % |

## 3. Días entre el alta y el primer reingreso (hasta 30 días)

| Días | Casos | % |
|---|---|---|
| El mismo día | 1.907 | 0,8 % |
| 1 día | 8.622 | 3,6 % |
| 2 a 3 días | 25.477 | 10,5 % |
| 4 a 7 días | 48.723 | 20,1 % |
| 8 a 14 días | 63.350 | 26,2 % |
| 15 a 30 días | 93.874 | 38,8 % |

El primer reingreso ocurre en un hospital distinto del que dio el alta en el 9,8 % de los casos.

## 4. Ingresos que cuentan y que no cuentan

Regla del reingreso no planificado, en orden de precedencia. Las primeras condiciones prevalecen sobre las siguientes cuando un ingreso tiene señales contradictorias:

1. El ingreso debe abrir un episodio asistencial nuevo (`PUEDE_SER_REINGRESO`): la continuación de un traslado no cuenta.
2. Si su código GRD (`IR_29301_COD_GRD`) comienza con 146 o 147, es un parto o una cesárea y no cuenta, cualquiera sea su tipo de ingreso.
3. Si su diagnóstico principal (`DIAGNOSTICO1`) comienza con Z51, es una sesión de tratamiento y no cuenta, cualquiera sea su tipo de ingreso.
4. Cuenta si su tipo de ingreso (`TIPO_INGRESO`) es `URGENCIA` u `OBSTETRICA`.
5. No cuenta si su tipo de ingreso es otro (ingreso programado) o si no tiene tipo de ingreso.

Clasificación de los 5.565.982 ingresos que abren un episodio:

| Clase del ingreso | Ingresos | % | ¿Cuenta como no planificado? |
|---|---|---|---|
| URGENCIA (no es parto ni sesión) | 2.839.563 | 51,0 % | Sí |
| PROGRAMADA | 1.725.645 | 31,0 % | No |
| PARTO O CESÁREA | 631.645 | 11,3 % | No |
| OBSTETRICA (no es parto ni sesión) | 282.329 | 5,1 % | Sí |
| SESIÓN DE TRATAMIENTO | 86.461 | 1,6 % | No |
| (sin tipo de ingreso) | 339 | 0,0 % | No |

Ingresos con señales contradictorias o sin dato, resueltos por la precedencia anterior: parto o cesárea (por GRD) con tipo de ingreso distinto de obstétrico, 2.493; sesión de tratamiento (por diagnóstico) con tipo de ingreso no programado, 1.649; sin tipo de ingreso y sin ser parto ni sesión, 339.

Casos de estudio seguidos de algún ingreso dentro de 30 días, según la clase del primero de esos ingresos:

| Primer ingreso posterior | Casos | % | ¿Cuenta como no planificado? |
|---|---|---|---|
| URGENCIA (no es parto ni sesión) | 204.000 | 51,2 % | Sí |
| PROGRAMADA | 95.991 | 24,1 % | No |
| PARTO O CESÁREA | 53.789 | 13,5 % | No |
| OBSTETRICA (no es parto ni sesión) | 32.035 | 8,0 % | Sí |
| SESIÓN DE TRATAMIENTO | 12.793 | 3,2 % | No |
| (sin tipo de ingreso) | 52 | 0,0 % | No |

Comparación de las cuatro variables según la forma de contar. La tabla de datos contiene solo la forma en uso; para cambiarla basta modificar `reingreso_solo_no_planificado` y volver a ejecutar este script. Al contar todo ingreso, un parto también es reingreso, así que en esa forma los partos tienen dato en las variables relacionadas (D38): cada columna usa sus propios casos con dato.

| Definición | Solo ingresos no planificados (en uso) | % | Todo ingreso | % |
|---|---|---|---|---|
| 7 días, por cualquier causa | 86.609 | 2,07 % | 150.521 | 3,59 % |
| 7 días, relacionado (misma CDM) | 45.195 | 1,26 % | 76.586 | 1,83 % |
| 30 días, por cualquier causa | 241.953 | 5,90 % | 398.660 | 9,72 % |
| 30 días, relacionado (misma CDM) | 124.256 | 3,55 % | 193.442 | 4,72 % |

## 5. Reingreso relacionado: CDM sin reingreso relacionado posible y análisis de sensibilidad

**CDM sin reingreso relacionado posible (bitácora H17 y D38).** La CDM 14 contiene solo estos GRD (descripciones de la hoja IR - GRD de la tabla maestra del DEIS):

| GRD | Descripción | Egresos | Casos de estudio |
|---|---|---|---|
| `146101` | PH CESÁREA | 180.258 | 173.452 |
| `146102` | PH CESÁREA W/CC | 78.971 | 75.910 |
| `146103` | PH CESÁREA W/MCC | 24.683 | 23.600 |
| `146111` | PH PARTO VAGINAL CON ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO | 19.055 | 18.315 |
| `146112` | PH PARTO VAGINAL CON ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO W/CC | 7.623 | 7.286 |
| `146113` | PH PARTO VAGINAL CON ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO W/MCC | 2.371 | 2.272 |
| `146121` | PH PARTO VAGINAL CON PROCED., EXCEPTO ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO | 134.270 | 129.127 |
| `146122` | PH PARTO VAGINAL CON PROCED., EXCEPTO ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO W/CC | 23.796 | 22.825 |
| `146123` | PH PARTO VAGINAL CON PROCED., EXCEPTO ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO W/MCC | 7.893 | 7.608 |
| `146131` | PH PARTO VAGINAL | 133.765 | 128.364 |
| `146132` | PH PARTO VAGINAL W/CC | 20.121 | 19.322 |
| `146133` | PH PARTO VAGINAL W/MCC | 7.393 | 7.086 |
| `147100` | PA CESÁREA | 34 | 0 |
| `147120` | PA PARTO VAGINAL CON PROCEDIMIENTO, EXCEPTO ESTERILIZACIÓN Y/O DILATACIÓN Y LEGRADO | 11 | 0 |
| `147130` | PA PARTO VAGINAL | 1 | 0 |

Todos comienzan con 146 o 147: son partos o cesáreas, y un parto no cuenta como reingreso (sección 4). Así, ningún reingreso puede ser de la CDM 14, y con la comparación literal sus casos de estudio tendrían 0 por construcción en las variables relacionadas: un modelo acertaría en todos ellos sin aprender nada sobre el reingreso. Por eso quedan sin dato en esas dos variables (parámetro `cdm_sin_relacionado`) y conservan las dos por cualquier causa. Las complicaciones del embarazo y del puerperio pertenecen a otras CDM, sobre todo a la 13. De los 603.423 casos de estudio de la CDM 14 con seguimiento de 30 días, 8.686 (1,44 %) tienen un reingreso no planificado dentro de 30 días. CDM de su primer reingreso:

| CDM del primer reingreso | Casos | % |
|---|---|---|
| 13 | 6.379 | 73,4 % |
| 06 | 644 | 7,4 % |
| 07 | 612 | 7,0 % |
| 09 | 273 | 3,1 % |
| 22 | 234 | 2,7 % |
| 04 | 143 | 1,6 % |
| Otras | 401 | 4,6 % |

GRD y diagnósticos principales más frecuentes de esos primeros reingresos:

| GRD | Descripción | Casos | % |
|---|---|---|---|
| `134171` | MH TRASTORNOS DEL POSTPARTO | 2.914 | 33,5 % |
| `134172` | MH TRASTORNOS DEL POSTPARTO W/CC | 863 | 9,9 % |
| `134161` | MH TRASTORNOS DEL ANTEPARTO | 793 | 9,1 % |
| `131111` | PH PROCEDIMIENTOS SOBRE ÚTERO Y CUELLO, DILATACIÓN Y LEGRADO | 405 | 4,7 % |
| `134162` | MH TRASTORNOS DEL ANTEPARTO W/CC | 299 | 3,4 % |

| Diagnóstico principal (3 caracteres) | Casos | % |
|---|---|---|
| `O86` | 1.651 | 19,0 % |
| `O90` | 1.249 | 14,4 % |
| `O85` | 1.086 | 12,5 % |
| `O99` | 818 | 9,4 % |
| `O72` | 504 | 5,8 % |

**Análisis de sensibilidad.** La tabla compara el reingreso relacionado según la definición en uso con otra forma de comparar las CDM (parámetros `cdm_agrupadas` y `cdm_sensibilidad`; bitácora H17, D31 y D38). Una CDM sin reingreso relacionado posible vuelve a tener dato cuando la comparación la une con otra, así que cada forma de comparar tiene sus propios casos con dato.

| Variable | Misma CDM, literal (en uso): casos con dato | Con reingreso | % | Con las CDM 13 y 14 como una sola: casos con dato | Con reingreso | % |
|---|---|---|---|---|---|---|
| `REING_7D_CDM` | 3.577.243 | 45.195 | 1,26 % | 4.192.410 | 49.087 | 1,17 % |
| `REING_30D_CDM` | 3.498.460 | 124.256 | 3,55 % | 4.101.883 | 130.654 | 3,19 % |

Detalle de la ventana de 30 días en los casos de estudio de las CDM que la comparación agrupa:

| CDM del caso de estudio | Casos con seguimiento | Con reingreso por cualquier causa | % | Relacionado: misma CDM, literal (en uso) | % | Relacionado: con las CDM 13 y 14 como una sola | % |
|---|---|---|---|---|---|---|---|
| 13 | 425.312 | 31.061 | 7,30 % | 26.156 | 6,15 % | 26.156 | 6,15 % |
| 14 | 603.423 | 8.686 | 1,44 % | sin dato | — | 6.398 | 1,06 % |

## 6. Verificación de la censura

Los archivos están organizados por año de alta: un reingreso que comienza dentro de la ventana pero termina después del cierre del bloque queda en un archivo que no se tiene, y el caso parece no haber reingresado. Para medirlo se usan los años cuyo año siguiente sí está en la base con el mismo identificador (2019, 2021, 2022, 2023): se cuenta qué parte de los reingresos reales no se vería si la base terminara el 31 de diciembre del año del alta.

| Días entre el alta y el 31 de diciembre | Casos de estudio | Reingresos a 7 días | No se verían | Reingresos a 30 días | No se verían |
|---|---|---|---|---|---|
| 7 a 13 | 63.351 | 1.489 | 40,2 % | — | — |
| 14 a 20 | 57.606 | 1.149 | 17,1 % | — | — |
| 21 a 29 | 70.071 | 1.411 | 9,5 % | — | — |
| 30 a 36 | 56.928 | 1.192 | 4,9 % | 3.335 | 16,4 % |
| 37 a 59 | 187.307 | 3.907 | 2,4 % | 11.081 | 5,3 % |
| 60 a 89 | 241.011 | 4.968 | 0,9 % | 14.300 | 1,5 % |
| 90 a 120 | 249.690 | 5.085 | 0,2 % | 14.723 | 0,5 % |

Con el margen de 30 días, las variables de 7 y 30 días exigen 37 y 60 días entre el alta y el cierre del bloque, respectivamente. La tabla permite ver cuánto se perdería con un margen menor (`censura_margen_dias`).

## 7. Tasas según las características del caso de estudio

Descriptivo, para revisar que las variables se comportan de forma razonable. Cada porcentaje usa los casos con seguimiento suficiente para esa variable.

| Tipo de ingreso | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| URGENCIA | 2.462.241 | 2,47 % | 1,31 % | 7,31 % | 3,68 % |
| OBSTETRICA | 879.251 | 1,61 % | 3,23 % | 3,97 % | 9,01 % |
| PROGRAMADA | 850.539 | 1,37 % | 0,52 % | 3,80 % | 1,46 % |
| (sin dato) | 379 | 2,37 % | 0,82 % | 6,91 % | 3,01 % |

| Tipo de alta | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| DOMICILIO | 3.973.075 | 1,91 % | 1,16 % | 5,57 % | 3,36 % |
| HOSPITALIZACIÓN DOMICILIARIA | 129.823 | 3,52 % | 1,75 % | 10,98 % | 5,11 % |
| ALTA VOLUNTARIA | 52.562 | 6,38 % | 4,53 % | 12,69 % | 8,61 % |
| DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE | 20.216 | 3,40 % | 1,91 % | 9,51 % | 5,04 % |
| FUGA DEL PACIENTE | 16.734 | 12,47 % | 9,17 % | 20,08 % | 14,34 % |

| CDM | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| 01 | 233.977 | 2,07 % | 1,05 % | 6,08 % | 2,76 % |
| 02 | 23.143 | 1,01 % | 0,47 % | 2,83 % | 1,22 % |
| 03 | 85.511 | 1,38 % | 0,39 % | 3,32 % | 0,83 % |
| 04 | 433.120 | 2,73 % | 1,80 % | 8,10 % | 5,16 % |
| 05 | 323.811 | 2,54 % | 1,27 % | 8,51 % | 4,22 % |
| 06 | 468.370 | 2,23 % | 1,18 % | 5,78 % | 2,87 % |
| 07 | 271.604 | 2,24 % | 1,29 % | 6,37 % | 3,73 % |
| 08 | 397.060 | 1,34 % | 0,65 % | 4,64 % | 2,30 % |
| 09 | 135.678 | 1,56 % | 0,48 % | 5,39 % | 1,61 % |
| 10 | 64.221 | 2,06 % | 0,81 % | 6,40 % | 2,37 % |
| 11 | 210.446 | 2,52 % | 1,15 % | 8,23 % | 3,92 % |
| 12 | 63.658 | 1,55 % | 0,36 % | 3,97 % | 1,00 % |
| 13 | 434.222 | 2,71 % | 2,21 % | 7,30 % | 6,15 % |
| 14 | 615.167 | 0,77 % | — | 1,44 % | — |
| 15 | 123.932 | 3,18 % | 1,62 % | 6,22 % | 1,63 % |
| 16 | 57.760 | 2,63 % | 0,82 % | 8,97 % | 3,07 % |
| 17 | 22.724 | 5,08 % | 1,82 % | 15,83 % | 6,11 % |
| 18 | 40.359 | 2,82 % | 0,65 % | 9,04 % | 2,00 % |
| 19 | 69.904 | 2,90 % | 2,15 % | 7,99 % | 5,69 % |
| 20 | 11.666 | 3,22 % | 1,88 % | 8,16 % | 4,30 % |
| 21 | 62.648 | 1,85 % | 0,56 % | 4,95 % | 1,26 % |
| 22 | 43.429 | 2,11 % | 0,35 % | 6,01 % | 0,82 % |

Por hospital: cómo se reparte la tasa de cada variable entre los 72 hospitales. El detalle está en el anexo y, por hospital y año, en `2.2_depuracion_etiquetado/reportes/09_tasas_por_hospital.csv`.

| Variable | Mínimo | Percentil 25 | Mediana | Percentil 75 | Máximo |
|---|---|---|---|---|---|
| `REING_7D` | 0,99 % | 1,80 % | 2,08 % | 2,37 % | 6,69 % |
| `REING_7D_CDM` | 0,50 % | 1,06 % | 1,26 % | 1,46 % | 4,08 % |
| `REING_30D` | 3,01 % | 5,27 % | 5,95 % | 6,73 % | 14,28 % |
| `REING_30D_CDM` | 1,81 % | 3,11 % | 3,54 % | 4,05 % | 8,47 % |

## 8. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `ventanas_dias` | `7 / 30` | Ventanas de reingreso, en días, separadas por una barra vertical (D20) |
| `censura_margen_dias` | `30` | Días que se suman a cada ventana para la censura. Un caso de estudio tiene las variables de una ventana solo si su alta ocurre al menos ventana + margen días antes del cierre del bloque, porque un reingreso solo aparece en la base si termina antes del cierre. 0 = solo la ventana (H20, D30) |
| `reingreso_solo_no_planificado` | `SI` | SI = solo cuentan como reingreso los ingresos no planificados, como indica el resumen de la propuesta; NO = cuenta todo ingreso, también los programados y los partos (D20, D26) |
| `ingresos_no_planificados` | `URGENCIA / OBSTETRICA` | Tipos de ingreso que cuentan como reingreso no planificado, separados por una barra vertical. Un ingreso sin tipo no cuenta (D20) |
| `grd_parto` | `146 / 147` | Comienzo de los códigos GRD de parto o cesárea: un ingreso con uno de estos GRD no cuenta como reingreso no planificado, cualquiera sea su tipo de ingreso (D20) |
| `diagnosticos_sesion` | `Z51` | Comienzo del diagnóstico principal de las sesiones de tratamiento, separados por una barra vertical si son varios. Esos egresos no son caso de estudio (criterio E14) ni cuentan como reingreso no planificado (D33) |
| `cdm_agrupadas` | (vacío) | CDM que se consideran una sola al comparar la CDM del reingreso con la del caso de estudio. Las CDM de un grupo se unen con + y los grupos se separan con una barra vertical. Vacío = ninguna: la comparación es literal (D31) |
| `cdm_sensibilidad` | `13+14` | Agrupación de CDM que se informa solo como análisis de sensibilidad en el reporte, con el mismo formato que cdm_agrupadas (H17, D31) |
| `cdm_sin_relacionado` | `14` | CDM cuyos casos de estudio quedan sin dato en las dos variables de reingreso relacionado, porque con la comparación en uso no pueden tener un reingreso de su misma CDM: la CDM 14 solo contiene partos y un parto no cuenta como reingreso (H17, D38). Solo se aplica si reingreso_solo_no_planificado = SI: si cuenta todo ingreso, un parto también es reingreso. Si cdm_agrupadas une una de estas CDM con otra, esa CDM vuelve a tener dato. Varias se separan con una barra vertical. Vacío = ninguna |

Cierre de cada bloque de identificador: A, 31-12-2020; B, 31-12-2024.

## 9. Columnas nuevas

| Columna | Contenido |
|---|---|
| `REING_7D` | Reingreso dentro de 7 días, por cualquier causa. 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 37 días del cierre del bloque. |
| `REING_7D_CDM` | Reingreso dentro de 7 días, relacionado (misma CDM). 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 37 días del cierre del bloque. También sin dato en los casos de estudio de la CDM 14, que no pueden tener un reingreso relacionado (D38). |
| `REING_30D` | Reingreso dentro de 30 días, por cualquier causa. 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 60 días del cierre del bloque. |
| `REING_30D_CDM` | Reingreso dentro de 30 días, relacionado (misma CDM). 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 60 días del cierre del bloque. También sin dato en los casos de estudio de la CDM 14, que no pueden tener un reingreso relacionado (D38). |
| `DIAS_REING` | Días entre el alta y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia dentro del bloque. Sin dato si no hay ninguno. |
| `ID_EGRESO_REING` | `ID_EGRESO` de ese ingreso, para poder revisar cada par. |

Todas quedan sin dato en los egresos que no son caso de estudio. Describen lo que ocurre después del alta: son variables objetivo o de trazabilidad y **no deben usarse como variables predictoras**.

## 10. Verificaciones

- Cada variable tiene dato en los casos de estudio con seguimiento suficiente para su ventana, y solo en ellos (en las relacionadas, salvo las CDM de `cdm_sin_relacionado`): **sí**.
- Los casos que quedan sin dato en las variables relacionadas no tienen ningún reingreso de su misma CDM: el 0 era obligatorio: **sí**.
- Todo caso de estudio tiene seguimiento suficiente para la ventana más corta: **sí**.
- Las dos rutas de cálculo dan el mismo resultado en las variables por cualquier causa: **sí**.
- Todo reingreso de una ventana corta lo es también de la más larga: **sí**.
- Todo reingreso relacionado lo es también por cualquier causa: **sí**.
- Todo reingreso no planificado lo es también al contar todo ingreso: **sí**.
- El ingreso señalado como reingreso es de la misma persona, abre otro episodio y ocurre el día del alta o después: **sí**.
- El archivo escrito tiene las mismas filas que la tabla depurada: **sí**.
- Las columnas de la tabla depurada conservan su nombre, orden y tipo de dato: **sí**.
- Contenido idéntico al de la tabla depurada en 7 columnas de control: **sí**.
- Las columnas nuevas releídas del archivo son iguales a las calculadas: **sí**.

El recorrido de la ruta 2 necesitó 37 pasos: ningún caso de estudio tiene más de 36 ingresos posteriores dentro de 30 días.

## Anexo. Tasas por hospital

Casos de estudio según el hospital que dio el alta. Cada porcentaje usa los casos con seguimiento suficiente para esa variable. Los nombres son los de la tabla maestra del DEIS.

| Hospital | Años | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|
| 101100 Hospital Dr. Juan Noé Crevanni (Arica) | Todos | 84.035 | 2,08 % | 1,26 % | 5,62 % | 3,32 % |
| 102100 Hospital Dr. Ernesto Torres Galdames (Iquique) | Todos | 88.960 | 2,34 % | 1,64 % | 5,97 % | 4,09 % |
| 103100 Hospital Dr. Leonardo Guzmán (Antofagasta) | Todos | 96.250 | 1,82 % | 1,04 % | 5,26 % | 2,96 % |
| 103101 Hospital Dr. Carlos Cisternas (Calama) | Todos | 49.240 | 2,21 % | 1,41 % | 6,28 % | 4,03 % |
| 104100 Hospital San José del Carmen (Copiapó) | Todos | 61.918 | 1,95 % | 1,19 % | 5,40 % | 3,10 % |
| 104103 Hospital Provincial del Huasco Monseñor Fernando Ariztía Ruiz (Vallenar) | Todos | 26.517 | 2,24 % | 1,40 % | 5,93 % | 3,51 % |
| 105100 Hospital San Juan de Dios (La Serena) | Todos | 66.796 | 1,69 % | 0,99 % | 5,17 % | 2,99 % |
| 105101 Hospital San Pablo (Coquimbo) | Todos | 72.329 | 1,61 % | 0,95 % | 4,96 % | 2,96 % |
| 105102 Hospital Dr. Antonio Tirado Lanas (Ovalle) | Todos | 43.659 | 1,64 % | 1,05 % | 4,72 % | 3,10 % |
| 106100 Hospital Carlos Van Buren (Valparaíso) | Todos | 77.757 | 1,94 % | 1,22 % | 5,99 % | 3,71 % |
| 106102 Hospital Dr. Eduardo Pereira Ramírez (Valparaíso) | Todos | 22.023 | 1,48 % | 0,61 % | 5,27 % | 2,19 % |
| 106103 Hospital Claudio Vicuña (San Antonio) | Todos | 34.351 | 2,03 % | 1,35 % | 5,65 % | 3,76 % |
| 107100 Hospital Dr. Gustavo Fricke (Viña del Mar) | Todos | 97.986 | 1,83 % | 1,10 % | 5,34 % | 2,99 % |
| 107101 Hospital San Martín (Quillota) | Todos | 45.266 | 1,58 % | 1,02 % | 4,74 % | 3,17 % |
| 107102 Hospital de Quilpué | Todos | 34.146 | 1,64 % | 1,23 % | 4,92 % | 3,63 % |
| 108100 Hospital de San Camilo (San Felipe) | Todos | 50.282 | 2,07 % | 1,30 % | 5,69 % | 3,55 % |
| 108101 Hospital San Juan de Dios (Los Andes) | Todos | 41.010 | 2,24 % | 1,32 % | 5,86 % | 3,39 % |
| 109100 Complejo Hospitalario San José (Santiago, Independencia) | Todos | 117.007 | 1,52 % | 1,16 % | 4,44 % | 3,14 % |
| 109101 Hospital Clínico de Niños Dr. Roberto del Río (Santiago, Independencia) | Todos | 38.191 | 2,53 % | 1,35 % | 6,47 % | 3,34 % |
| 110100 Hospital San Juan de Dios (Santiago, Santiago) | Todos | 99.777 | 2,02 % | 1,23 % | 6,07 % | 3,63 % |
| 110110 Instituto Traumatológico Dr. Teodoro Gebauer | 2023 a 2024 | 5.752 | 0,99 % | 0,50 % | 3,01 % | 1,81 % |
| 110120 Hospital Dr. Félix Bulnes Cerda (Santiago, Quinta Normal) | Todos | 101.715 | 1,85 % | 1,17 % | 5,76 % | 3,67 % |
| 110130 Hospital Adalberto Steeger (Talagante) | Todos | 31.007 | 1,58 % | 1,01 % | 4,57 % | 2,86 % |
| 110150 Hospital San José (Melipilla) | Todos | 36.039 | 1,71 % | 1,21 % | 4,21 % | 2,79 % |
| 111100 Hospital Clínico San Borja-Arriarán (Santiago, Santiago) | Todos | 85.276 | 1,39 % | 0,90 % | 4,01 % | 2,75 % |
| 111101 Hospital Clínico Metropolitano El Carmen Doctor Luis Valentín Ferrada | Todos | 85.003 | 1,83 % | 1,04 % | 6,15 % | 3,58 % |
| 111195 Hospital de Urgencia Asistencia Pública Dr. Alejandro del Río | Todos | 49.361 | 2,29 % | 1,15 % | 7,39 % | 3,46 % |
| 112100 Hospital Del Salvador (Santiago, Providencia) | Todos | 51.670 | 2,08 % | 0,94 % | 7,12 % | 3,23 % |
| 112101 Hospital Dr. Luis Tisné B. (Santiago, Peñalolén) | Todos | 76.897 | 2,25 % | 1,59 % | 5,73 % | 3,93 % |
| 112102 Hospital de Niños Dr. Luis Calvo Mackenna (Santiago, Providencia) | Todos | 35.794 | 3,06 % | 1,43 % | 8,52 % | 3,96 % |
| 112103 Instituto Nacional de Enfermedades Respiratorias y Cirugía Torácica | Todos | 18.132 | 1,38 % | 0,71 % | 4,36 % | 2,39 % |
| 112104 Instituto de Neurocirugía Dr. Alfonso Asenjo | Todos | 17.911 | 2,47 % | 1,25 % | 6,62 % | 3,29 % |
| 113100 Hospital Barros Luco Trudeau (Santiago, San Miguel) | Todos | 132.552 | 2,18 % | 1,37 % | 6,09 % | 3,57 % |
| 113130 Hospital Dr. Exequiel González Cortés (Santiago, San Miguel) | Todos | 37.340 | 2,37 % | 1,33 % | 5,97 % | 3,47 % |
| 113150 Hospital San Luis (Buin) | Todos | 24.851 | 2,63 % | 1,79 % | 6,70 % | 4,53 % |
| 113180 Hospital El Pino (Santiago, San Bernardo) | Todos | 65.847 | 2,49 % | 1,73 % | 6,26 % | 4,21 % |
| 114101 Complejo Hospitalario Dr. Sótero del Río (Santiago, Puente Alto) | Todos | 191.028 | 2,95 % | 1,67 % | 7,61 % | 4,20 % |
| 114103 Hospital Padre Alberto Hurtado (San Ramón) | Todos | 82.319 | 2,38 % | 1,67 % | 6,43 % | 4,40 % |
| 114105 Hospital Clínico Metropolitano La Florida Dra. Eloisa Díaz Inzunza | Todos | 79.216 | 1,92 % | 1,10 % | 5,88 % | 3,48 % |
| 115100 Hospital Regional de Rancagua | Todos | 108.715 | 2,08 % | 1,19 % | 6,00 % | 3,49 % |
| 115107 Hospital San Juan de Dios (San Fernando) | Todos | 38.334 | 1,92 % | 1,06 % | 5,38 % | 3,04 % |
| 115110 Hospital de Santa Cruz | Todos | 26.298 | 2,16 % | 1,68 % | 5,43 % | 3,91 % |
| 116100 Hospital San Juan de Dios (Curicó) | Todos | 69.244 | 1,71 % | 1,09 % | 5,19 % | 3,33 % |
| 116105 Hospital Dr. César Garavagno Burotto (Talca) | Todos | 135.155 | 1,51 % | 0,84 % | 4,72 % | 2,66 % |
| 116107 Hospital de Constitución | 2024 | 2.168 | 6,69 % | 4,08 % | 14,28 % | 8,47 % |
| 116108 Hospital Presidente Carlos Ibáñez del Campo (Linares) | Todos | 58.805 | 1,93 % | 1,18 % | 5,18 % | 3,20 % |
| 116110 Hospital San José (Parral) | Todos | 21.507 | 4,05 % | 2,32 % | 11,14 % | 6,33 % |
| 116111 Hospital San Juan de Dios (Cauquenes) | 2024 | 3.335 | 4,14 % | 2,58 % | 10,82 % | 6,25 % |
| 117101 Hospital Clínico Herminda Martín (Chillán) | Todos | 93.528 | 2,07 % | 1,24 % | 6,17 % | 3,66 % |
| 117102 Hospital de San Carlos | Todos | 34.876 | 2,31 % | 1,28 % | 6,75 % | 3,75 % |
| 118100 Hospital Clínico Regional Dr. Guillermo Grant Benavente (Concepción) | Todos | 145.527 | 2,07 % | 1,18 % | 6,19 % | 3,53 % |
| 118105 Hospital San José (Coronel) | Todos | 30.288 | 3,29 % | 2,04 % | 9,41 % | 5,92 % |
| 118106 Hospital de Lota | 2023 a 2024 | 6.223 | 3,58 % | 2,01 % | 10,63 % | 5,82 % |
| 119100 Hospital Las Higueras (Talcahuano) | Todos | 101.752 | 2,27 % | 1,34 % | 6,79 % | 3,89 % |
| 119101 Hospital de Tomé | 2023 a 2024 | 5.275 | 4,02 % | 2,21 % | 12,33 % | 6,32 % |
| 119102 Hospital Penco - Lirquén | 2024 | 2.228 | 2,92 % | 1,66 % | 9,36 % | 5,03 % |
| 120101 Complejo Asistencial Dr. Víctor Ríos Ruiz (Los Ángeles) | Todos | 128.882 | 1,83 % | 1,00 % | 5,40 % | 3,11 % |
| 121109 Hospital Dr. Hernán Henríquez Aravena (Temuco) | Todos | 122.433 | 1,61 % | 1,01 % | 4,54 % | 2,94 % |
| 121110 Hospital Dr. Abraham Godoy (Lautaro) | Todos | 13.346 | 2,47 % | 1,68 % | 8,55 % | 5,89 % |
| 121114 Hospital Intercultural de Nueva Imperial | Todos | 21.467 | 2,21 % | 1,34 % | 7,33 % | 4,46 % |
| 121117 Hospital de Pitrufquén | Todos | 12.805 | 2,20 % | 1,33 % | 7,58 % | 4,62 % |
| 121121 Hospital de Villarrica | Todos | 20.267 | 2,61 % | 1,72 % | 6,84 % | 4,72 % |
| 122100 Hospital Clínico Regional (Valdivia) | Todos | 92.292 | 1,96 % | 1,30 % | 5,51 % | 3,54 % |
| 123100 Hospital Base San José de Osorno | Todos | 85.347 | 1,69 % | 0,97 % | 5,22 % | 2,87 % |
| 124105 Hospital de Puerto Montt | Todos | 118.847 | 2,61 % | 1,90 % | 7,05 % | 4,66 % |
| 125100 Hospital Regional (Coihaique) | Todos | 43.933 | 2,36 % | 1,41 % | 6,12 % | 3,62 % |
| 126100 Hospital Clínico de Magallanes Dr. Lautaro Navarro Avaria | Todos | 54.581 | 2,23 % | 1,25 % | 6,52 % | 3,69 % |
| 128109 Hospital Provincial Dr. Rafael Avaría (Curanilahue) | Todos | 26.588 | 1,99 % | 1,54 % | 5,72 % | 4,51 % |
| 129100 Hospital Dr. Mauricio Heyermann (Angol) | Todos | 41.390 | 2,46 % | 1,42 % | 6,72 % | 3,90 % |
| 129106 Hospital San José (Victoria) | Todos | 32.962 | 1,75 % | 0,97 % | 4,89 % | 2,87 % |
| 133150 Hospital de Castro | Todos | 33.662 | 2,16 % | 1,32 % | 5,60 % | 3,45 % |
| 200717 (sin nombre en la tabla maestra) | 2024 | 5.140 | 1,77 % | 0,93 % | 5,73 % | 3,02 % |
