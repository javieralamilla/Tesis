# Etiquetado del reingreso (actividad 2.2, script 09)

Generado por `2.2_depuracion_etiquetado/scripts/09_etiquetar.py`. Entrada: `data/processed/grd_depurado.parquet`. Salida: `data/processed/grd_etiquetado.parquet`. Umbrales: `2.2_depuracion_etiquetado/reglas/parametros.csv`. Las decisiones están en `2.2_depuracion_etiquetado/bitacora.md`.

Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un episodio asistencial nuevo, y se cuentan los días entre el alta del caso y ese ingreso. El día 0 (ingreso el mismo día del alta) cuenta. Un ingreso que continúa un traslado no cuenta.

**Qué ingreso cuenta como reingreso:** solo el no planificado (regla completa en la sección 4).

**Reingreso relacionado:** se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio. Un ingreso con CDM 99 nunca cuenta como relacionado. La comparación es literal: no se agrupa ninguna CDM.

**Censura:** un reingreso solo aparece en la base si termina antes del cierre del bloque. Por eso cada ventana exige un margen de 30 días además de sus propios días (7 días: alta al menos 37 días antes del cierre; 30 días: alta al menos 60 días antes del cierre). Un caso de estudio que no alcanza el seguimiento de una ventana queda sin dato en las variables de esa ventana (sección 6).

## 1. Las cuatro variables objetivo

Hay 4.192.410 casos de estudio. Cada variable se calcula sobre los que tienen seguimiento suficiente para su ventana.

| Variable | Definición | Casos con seguimiento | Casos con reingreso | % |
|---|---|---|---|---|
| `REING_7D` | 7 días, por cualquier causa | 4.192.410 | 86.609 | 2,07 % |
| `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 4.192.410 | 45.195 | 1,08 % |
| `REING_30D` | 30 días, por cualquier causa | 4.101.883 | 241.953 | 5,90 % |
| `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 4.101.883 | 124.256 | 3,03 % |

Las cuatro están contenidas unas en otras: la ventana de 30 días incluye los primeros 7, y «por cualquier causa» incluye a los relacionados. Combinaciones de las cuatro variables en los 4.101.883 casos de estudio que tienen dato en todas:

| `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` | Casos de estudio | % |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 44.246 | 1,08 % |
| 1 | 0 | 1 | 1 | 916 | 0,02 % |
| 1 | 0 | 1 | 0 | 39.567 | 0,96 % |
| 0 | 0 | 1 | 1 | 79.094 | 1,93 % |
| 0 | 0 | 1 | 0 | 78.130 | 1,90 % |
| 0 | 0 | 0 | 0 | 3.859.930 | 94,10 % |

## 2. Tasas por año del alta

Porcentaje de los casos de estudio de cada año con seguimiento suficiente para la ventana.

| Definición | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| 7 días, por cualquier causa | 2,05 % | 2,09 % | 1,94 % | 1,94 % | 2,13 % | 2,24 % | 2,07 % |
| 7 días, relacionado (misma CDM) | 1,05 % | 1,05 % | 1,01 % | 1,03 % | 1,13 % | 1,18 % | 1,08 % |
| 30 días, por cualquier causa | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,14 % | 6,45 % | 5,90 % |
| 30 días, relacionado (misma CDM) | 2,96 % | 2,81 % | 2,86 % | 2,96 % | 3,19 % | 3,34 % | 3,03 % |
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

Comparación de las cuatro variables según la forma de contar. La tabla de datos contiene solo la forma en uso; para cambiarla basta modificar `reingreso_solo_no_planificado` y volver a ejecutar este script.

| Definición | Solo ingresos no planificados (en uso) | % | Todo ingreso | % |
|---|---|---|---|---|
| 7 días, por cualquier causa | 86.609 | 2,07 % | 150.521 | 3,59 % |
| 7 días, relacionado (misma CDM) | 45.195 | 1,08 % | 76.586 | 1,83 % |
| 30 días, por cualquier causa | 241.953 | 5,90 % | 398.660 | 9,72 % |
| 30 días, relacionado (misma CDM) | 124.256 | 3,03 % | 193.442 | 4,72 % |

## 5. Reingreso relacionado: definición en uso y análisis de sensibilidad

Como análisis de sensibilidad, la tabla compara el reingreso relacionado según la definición en uso con otra forma de comparar las CDM (parámetros `cdm_agrupadas` y `cdm_sensibilidad`; bitácora H17 y D31).

| Variable | Misma CDM, literal (en uso) | % | Con las CDM 13 y 14 como una sola | % | Diferencia |
|---|---|---|---|---|---|
| `REING_7D_CDM` | 45.195 | 1,08 % | 49.087 | 1,17 % | +3.892 |
| `REING_30D_CDM` | 124.256 | 3,03 % | 130.654 | 3,19 % | +6.398 |

Detalle de la ventana de 30 días en los casos de estudio de las CDM que la comparación agrupa:

| CDM del caso de estudio | Casos con seguimiento | Con reingreso por cualquier causa | % | Relacionado: misma CDM, literal (en uso) | % | Relacionado: con las CDM 13 y 14 como una sola | % |
|---|---|---|---|---|---|---|---|
| 13 | 425.312 | 31.061 | 7,30 % | 26.156 | 6,15 % | 26.156 | 6,15 % |
| 14 | 603.423 | 8.686 | 1,44 % | 0 | 0,00 % | 6.398 | 1,06 % |

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
| OBSTETRICA | 879.251 | 1,61 % | 0,98 % | 3,97 % | 2,73 % |
| PROGRAMADA | 850.539 | 1,37 % | 0,52 % | 3,80 % | 1,45 % |
| (sin dato) | 379 | 2,37 % | 0,79 % | 6,91 % | 2,93 % |

| Tipo de alta | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| DOMICILIO | 3.973.075 | 1,91 % | 0,98 % | 5,57 % | 2,84 % |
| HOSPITALIZACIÓN DOMICILIARIA | 129.823 | 3,52 % | 1,74 % | 10,98 % | 5,08 % |
| ALTA VOLUNTARIA | 52.562 | 6,38 % | 4,23 % | 12,69 % | 8,04 % |
| DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE | 20.216 | 3,40 % | 1,87 % | 9,51 % | 4,94 % |
| FUGA DEL PACIENTE | 16.734 | 12,47 % | 8,72 % | 20,08 % | 13,64 % |

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
| 14 | 615.167 | 0,77 % | 0,00 % | 1,44 % | 0,00 % |
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
| `REING_7D_CDM` | 0,50 % | 0,89 % | 1,10 % | 1,33 % | 3,92 % |
| `REING_30D` | 3,01 % | 5,27 % | 5,95 % | 6,73 % | 14,28 % |
| `REING_30D_CDM` | 1,81 % | 2,64 % | 3,06 % | 3,49 % | 8,12 % |

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

Cierre de cada bloque de identificador: A, 31-12-2020; B, 31-12-2024.

## 9. Columnas nuevas

| Columna | Contenido |
|---|---|
| `REING_7D` | Reingreso dentro de 7 días, por cualquier causa. 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 37 días del cierre del bloque. |
| `REING_7D_CDM` | Reingreso dentro de 7 días, relacionado (misma CDM). 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 37 días del cierre del bloque. |
| `REING_30D` | Reingreso dentro de 30 días, por cualquier causa. 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 60 días del cierre del bloque. |
| `REING_30D_CDM` | Reingreso dentro de 30 días, relacionado (misma CDM). 1 = sí, 0 = no. Sin dato si el alta ocurre a menos de 60 días del cierre del bloque. |
| `DIAS_REING` | Días entre el alta y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia dentro del bloque. Sin dato si no hay ninguno. |
| `ID_EGRESO_REING` | `ID_EGRESO` de ese ingreso, para poder revisar cada par. |

Todas quedan sin dato en los egresos que no son caso de estudio. Describen lo que ocurre después del alta: son variables objetivo o de trazabilidad y **no deben usarse como variables predictoras**.

## 10. Verificaciones

- Cada variable tiene dato en los casos de estudio con seguimiento suficiente para su ventana, y solo en ellos: **sí**.
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
| 101100 Hospital Dr. Juan Noé Crevanni (Arica) | Todos | 84.035 | 2,08 % | 1,08 % | 5,62 % | 2,85 % |
| 102100 Hospital Dr. Ernesto Torres Galdames (Iquique) | Todos | 88.960 | 2,34 % | 1,32 % | 5,97 % | 3,29 % |
| 103100 Hospital Dr. Leonardo Guzmán (Antofagasta) | Todos | 96.250 | 1,82 % | 0,89 % | 5,26 % | 2,53 % |
| 103101 Hospital Dr. Carlos Cisternas (Calama) | Todos | 49.240 | 2,21 % | 1,15 % | 6,28 % | 3,29 % |
| 104100 Hospital San José del Carmen (Copiapó) | Todos | 61.918 | 1,95 % | 1,02 % | 5,40 % | 2,66 % |
| 104103 Hospital Provincial del Huasco Monseñor Fernando Ariztía Ruiz (Vallenar) | Todos | 26.517 | 2,24 % | 1,18 % | 5,93 % | 2,97 % |
| 105100 Hospital San Juan de Dios (La Serena) | Todos | 66.796 | 1,69 % | 0,83 % | 5,17 % | 2,51 % |
| 105101 Hospital San Pablo (Coquimbo) | Todos | 72.329 | 1,61 % | 0,79 % | 4,96 % | 2,46 % |
| 105102 Hospital Dr. Antonio Tirado Lanas (Ovalle) | Todos | 43.659 | 1,64 % | 0,83 % | 4,72 % | 2,47 % |
| 106100 Hospital Carlos Van Buren (Valparaíso) | Todos | 77.757 | 1,94 % | 1,06 % | 5,99 % | 3,21 % |
| 106102 Hospital Dr. Eduardo Pereira Ramírez (Valparaíso) | Todos | 22.023 | 1,48 % | 0,61 % | 5,27 % | 2,19 % |
| 106103 Hospital Claudio Vicuña (San Antonio) | Todos | 34.351 | 2,03 % | 1,11 % | 5,65 % | 3,08 % |
| 107100 Hospital Dr. Gustavo Fricke (Viña del Mar) | Todos | 97.986 | 1,83 % | 0,96 % | 5,34 % | 2,60 % |
| 107101 Hospital San Martín (Quillota) | Todos | 45.266 | 1,58 % | 0,85 % | 4,74 % | 2,63 % |
| 107102 Hospital de Quilpué | Todos | 34.146 | 1,64 % | 0,99 % | 4,92 % | 2,92 % |
| 108100 Hospital de San Camilo (San Felipe) | Todos | 50.282 | 2,07 % | 1,06 % | 5,69 % | 2,90 % |
| 108101 Hospital San Juan de Dios (Los Andes) | Todos | 41.010 | 2,24 % | 1,17 % | 5,86 % | 2,99 % |
| 109100 Complejo Hospitalario San José (Santiago, Independencia) | Todos | 117.007 | 1,52 % | 0,81 % | 4,44 % | 2,20 % |
| 109101 Hospital Clínico de Niños Dr. Roberto del Río (Santiago, Independencia) | Todos | 38.191 | 2,53 % | 1,35 % | 6,47 % | 3,34 % |
| 110100 Hospital San Juan de Dios (Santiago, Santiago) | Todos | 99.777 | 2,02 % | 1,04 % | 6,07 % | 3,05 % |
| 110110 Instituto Traumatológico Dr. Teodoro Gebauer | 2023 a 2024 | 5.752 | 0,99 % | 0,50 % | 3,01 % | 1,81 % |
| 110120 Hospital Dr. Félix Bulnes Cerda (Santiago, Quinta Normal) | Todos | 101.715 | 1,85 % | 0,96 % | 5,76 % | 3,02 % |
| 110130 Hospital Adalberto Steeger (Talagante) | Todos | 31.007 | 1,58 % | 0,78 % | 4,57 % | 2,22 % |
| 110150 Hospital San José (Melipilla) | Todos | 36.039 | 1,71 % | 0,90 % | 4,21 % | 2,08 % |
| 111100 Hospital Clínico San Borja-Arriarán (Santiago, Santiago) | Todos | 85.276 | 1,39 % | 0,68 % | 4,01 % | 2,08 % |
| 111101 Hospital Clínico Metropolitano El Carmen Doctor Luis Valentín Ferrada | Todos | 85.003 | 1,83 % | 0,85 % | 6,15 % | 2,93 % |
| 111195 Hospital de Urgencia Asistencia Pública Dr. Alejandro del Río | Todos | 49.361 | 2,29 % | 1,15 % | 7,39 % | 3,46 % |
| 112100 Hospital Del Salvador (Santiago, Providencia) | Todos | 51.670 | 2,08 % | 0,94 % | 7,12 % | 3,23 % |
| 112101 Hospital Dr. Luis Tisné B. (Santiago, Peñalolén) | Todos | 76.897 | 2,25 % | 1,17 % | 5,73 % | 2,87 % |
| 112102 Hospital de Niños Dr. Luis Calvo Mackenna (Santiago, Providencia) | Todos | 35.794 | 3,06 % | 1,43 % | 8,52 % | 3,96 % |
| 112103 Instituto Nacional de Enfermedades Respiratorias y Cirugía Torácica | Todos | 18.132 | 1,38 % | 0,71 % | 4,36 % | 2,39 % |
| 112104 Instituto de Neurocirugía Dr. Alfonso Asenjo | Todos | 17.911 | 2,47 % | 1,25 % | 6,62 % | 3,29 % |
| 113100 Hospital Barros Luco Trudeau (Santiago, San Miguel) | Todos | 132.552 | 2,18 % | 1,17 % | 6,09 % | 3,05 % |
| 113130 Hospital Dr. Exequiel González Cortés (Santiago, San Miguel) | Todos | 37.340 | 2,37 % | 1,33 % | 5,97 % | 3,47 % |
| 113150 Hospital San Luis (Buin) | Todos | 24.851 | 2,63 % | 1,46 % | 6,70 % | 3,69 % |
| 113180 Hospital El Pino (Santiago, San Bernardo) | Todos | 65.847 | 2,49 % | 1,34 % | 6,26 % | 3,26 % |
| 114101 Complejo Hospitalario Dr. Sótero del Río (Santiago, Puente Alto) | Todos | 191.028 | 2,95 % | 1,50 % | 7,61 % | 3,76 % |
| 114103 Hospital Padre Alberto Hurtado (San Ramón) | Todos | 82.319 | 2,38 % | 1,38 % | 6,43 % | 3,63 % |
| 114105 Hospital Clínico Metropolitano La Florida Dra. Eloisa Díaz Inzunza | Todos | 79.216 | 1,92 % | 0,91 % | 5,88 % | 2,86 % |
| 115100 Hospital Regional de Rancagua | Todos | 108.715 | 2,08 % | 1,03 % | 6,00 % | 3,01 % |
| 115107 Hospital San Juan de Dios (San Fernando) | Todos | 38.334 | 1,92 % | 0,89 % | 5,38 % | 2,54 % |
| 115110 Hospital de Santa Cruz | Todos | 26.298 | 2,16 % | 1,36 % | 5,43 % | 3,17 % |
| 116100 Hospital San Juan de Dios (Curicó) | Todos | 69.244 | 1,71 % | 0,89 % | 5,19 % | 2,71 % |
| 116105 Hospital Dr. César Garavagno Burotto (Talca) | Todos | 135.155 | 1,51 % | 0,71 % | 4,72 % | 2,25 % |
| 116107 Hospital de Constitución | 2024 | 2.168 | 6,69 % | 3,92 % | 14,28 % | 8,12 % |
| 116108 Hospital Presidente Carlos Ibáñez del Campo (Linares) | Todos | 58.805 | 1,93 % | 0,98 % | 5,18 % | 2,64 % |
| 116110 Hospital San José (Parral) | Todos | 21.507 | 4,05 % | 2,14 % | 11,14 % | 5,83 % |
| 116111 Hospital San Juan de Dios (Cauquenes) | 2024 | 3.335 | 4,14 % | 2,43 % | 10,82 % | 5,87 % |
| 117101 Hospital Clínico Herminda Martín (Chillán) | Todos | 93.528 | 2,07 % | 1,07 % | 6,17 % | 3,15 % |
| 117102 Hospital de San Carlos | Todos | 34.876 | 2,31 % | 1,15 % | 6,75 % | 3,35 % |
| 118100 Hospital Clínico Regional Dr. Guillermo Grant Benavente (Concepción) | Todos | 145.527 | 2,07 % | 1,07 % | 6,19 % | 3,20 % |
| 118105 Hospital San José (Coronel) | Todos | 30.288 | 3,29 % | 1,78 % | 9,41 % | 5,16 % |
| 118106 Hospital de Lota | 2023 a 2024 | 6.223 | 3,58 % | 1,94 % | 10,63 % | 5,61 % |
| 119100 Hospital Las Higueras (Talcahuano) | Todos | 101.752 | 2,27 % | 1,21 % | 6,79 % | 3,52 % |
| 119101 Hospital de Tomé | 2023 a 2024 | 5.275 | 4,02 % | 2,20 % | 12,33 % | 6,29 % |
| 119102 Hospital Penco - Lirquén | 2024 | 2.228 | 2,92 % | 1,66 % | 9,36 % | 5,02 % |
| 120101 Complejo Asistencial Dr. Víctor Ríos Ruiz (Los Ángeles) | Todos | 128.882 | 1,83 % | 0,87 % | 5,40 % | 2,73 % |
| 121109 Hospital Dr. Hernán Henríquez Aravena (Temuco) | Todos | 122.433 | 1,61 % | 0,81 % | 4,54 % | 2,35 % |
| 121110 Hospital Dr. Abraham Godoy (Lautaro) | Todos | 13.346 | 2,47 % | 1,55 % | 8,55 % | 5,45 % |
| 121114 Hospital Intercultural de Nueva Imperial | Todos | 21.467 | 2,21 % | 1,29 % | 7,33 % | 4,28 % |
| 121117 Hospital de Pitrufquén | Todos | 12.805 | 2,20 % | 1,27 % | 7,58 % | 4,38 % |
| 121121 Hospital de Villarrica | Todos | 20.267 | 2,61 % | 1,39 % | 6,84 % | 3,80 % |
| 122100 Hospital Clínico Regional (Valdivia) | Todos | 92.292 | 1,96 % | 1,15 % | 5,51 % | 3,12 % |
| 123100 Hospital Base San José de Osorno | Todos | 85.347 | 1,69 % | 0,87 % | 5,22 % | 2,56 % |
| 124105 Hospital de Puerto Montt | Todos | 118.847 | 2,61 % | 1,62 % | 7,05 % | 3,97 % |
| 125100 Hospital Regional (Coihaique) | Todos | 43.933 | 2,36 % | 1,25 % | 6,12 % | 3,20 % |
| 126100 Hospital Clínico de Magallanes Dr. Lautaro Navarro Avaria | Todos | 54.581 | 2,23 % | 1,15 % | 6,52 % | 3,37 % |
| 128109 Hospital Provincial Dr. Rafael Avaría (Curanilahue) | Todos | 26.588 | 1,99 % | 1,22 % | 5,72 % | 3,57 % |
| 129100 Hospital Dr. Mauricio Heyermann (Angol) | Todos | 41.390 | 2,46 % | 1,23 % | 6,72 % | 3,38 % |
| 129106 Hospital San José (Victoria) | Todos | 32.962 | 1,75 % | 0,83 % | 4,89 % | 2,46 % |
| 133150 Hospital de Castro | Todos | 33.662 | 2,16 % | 1,09 % | 5,60 % | 2,86 % |
| 200717 (sin nombre en la tabla maestra) | 2024 | 5.140 | 1,77 % | 0,93 % | 5,73 % | 3,02 % |
