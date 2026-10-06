# Etiquetado del reingreso (actividad 2.2, script 09)

Generado por `2.2_depuracion_etiquetado/scripts/09_etiquetar.py`. Entrada: `data/processed/grd_depurado.parquet`. Salida: `data/processed/grd_etiquetado.parquet`. Umbrales: `2.2_depuracion_etiquetado/reglas/parametros.csv`. Las decisiones están en `2.2_depuracion_etiquetado/bitacora.md` (D20, D25 y D26).

Para cada caso de estudio se buscan los ingresos posteriores de la misma persona que abren un episodio asistencial nuevo, y se cuentan los días entre el alta del caso y ese ingreso. El día 0 (ingreso el mismo día del alta) cuenta. Un ingreso que continúa un traslado no cuenta.

**Qué ingreso cuenta como reingreso:** solo el no planificado, es decir, de tipo `URGENCIA` u `OBSTETRICA` y cuyo GRD no es de parto ni de cesárea (no comienza con 146 ni con 147). Los ingresos programados y los partos no cuentan.

**Reingreso relacionado:** se cumple si algún ingreso de la ventana tiene la misma CDM que el caso de estudio. Un ingreso con CDM 99 nunca cuenta como relacionado. Para esta comparación, las CDM 13 y 14 se consideran una sola.

## 1. Las cuatro variables objetivo

Sobre 5.154.605 casos de estudio.

| Variable | Definición | Casos con reingreso | % |
|---|---|---|---|
| `REING_7D` | 7 días, por cualquier causa | 93.282 | 1,81 % |
| `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 50.896 | 0,99 % |
| `REING_30D` | 30 días, por cualquier causa | 265.874 | 5,16 % |
| `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 138.380 | 2,68 % |

Las cuatro están contenidas unas en otras: la ventana de 30 días incluye los primeros 7, y «por cualquier causa» incluye a los relacionados. Casos de estudio según la combinación de las cuatro variables:

| `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` | Casos de estudio | % |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 50.896 | 0,99 % |
| 1 | 0 | 1 | 1 | 1.038 | 0,02 % |
| 1 | 0 | 1 | 0 | 41.348 | 0,80 % |
| 0 | 0 | 1 | 1 | 86.446 | 1,68 % |
| 0 | 0 | 1 | 0 | 86.146 | 1,67 % |
| 0 | 0 | 0 | 0 | 4.888.731 | 94,84 % |

## 2. Tasas por año del alta

Porcentaje de los casos de estudio de cada año.

| Definición | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| 7 días, por cualquier causa | 1,82 % | 1,92 % | 1,76 % | 1,69 % | 1,81 % | 1,87 % | 1,81 % |
| 7 días, relacionado (misma CDM) | 0,99 % | 1,03 % | 0,96 % | 0,93 % | 1,00 % | 1,02 % | 0,99 % |
| 30 días, por cualquier causa | 5,07 % | 5,20 % | 5,08 % | 5,00 % | 5,22 % | 5,36 % | 5,16 % |
| 30 días, relacionado (misma CDM) | 2,68 % | 2,65 % | 2,62 % | 2,60 % | 2,74 % | 2,80 % | 2,68 % |
| Casos de estudio | 971.438 | 656.043 | 748.059 | 871.460 | 974.925 | 932.680 | 5.154.605 |

Los años 2020 y 2024 no incluyen las altas de diciembre (censura, D22). 2019 y 2020 forman el bloque A de identificadores y 2021 a 2024, el bloque B (D03).

## 3. Días entre el alta y el primer reingreso (hasta 30 días)

| Días | Casos | % |
|---|---|---|
| El mismo día | 2.251 | 0,8 % |
| 1 día | 9.500 | 3,6 % |
| 2 a 3 días | 27.774 | 10,4 % |
| 4 a 7 días | 53.757 | 20,2 % |
| 8 a 14 días | 69.592 | 26,2 % |
| 15 a 30 días | 103.000 | 38,7 % |

El primer reingreso ocurre en un hospital distinto del que dio el alta en el 10,0 % de los casos.

## 4. Ingresos que cuentan y que no cuentan

Casos de estudio seguidos de algún ingreso dentro de 30 días, según el tipo del primero de esos ingresos:

| Primer ingreso posterior | Casos | % | ¿Es no planificado? |
|---|---|---|---|
| URGENCIA (no es parto) | 224.221 | 43,3 % | Sí |
| PROGRAMADA | 205.196 | 39,6 % | No |
| PARTO O CESÁREA | 55.280 | 10,7 % | No |
| OBSTETRICA (no es parto) | 33.054 | 6,4 % | Sí |
| (sin dato) | 64 | 0,0 % | No |

Comparación de las cuatro variables según la forma de contar. La tabla de datos contiene solo la forma en uso; para cambiarla basta modificar `reingreso_solo_no_planificado` y volver a ejecutar este script.

| Definición | Solo ingresos no planificados (en uso) | % | Todo ingreso | % |
|---|---|---|---|---|
| 7 días, por cualquier causa | 93.282 | 1,81 % | 189.094 | 3,67 % |
| 7 días, relacionado (misma CDM) | 50.896 | 0,99 % | 128.439 | 2,49 % |
| 30 días, por cualquier causa | 265.874 | 5,16 % | 517.815 | 10,05 % |
| 30 días, relacionado (misma CDM) | 138.380 | 2,68 % | 347.263 | 6,74 % |

## 5. Agrupación de CDM en el reingreso relacionado

La CDM 14 contiene solo partos y cesáreas, y las complicaciones del posparto pertenecen a la CDM 13: sin agrupar, un parto nunca podría tener un reingreso relacionado. Variables de reingreso relacionado con las CDM 13 y 14 consideradas una sola (en uso) y sin agruparlas:

| Variable | Sin agrupar | Con la agrupación (en uso) | Diferencia |
|---|---|---|---|
| `REING_7D_CDM` | 46.975 | 50.896 | 3.921 |
| `REING_30D_CDM` | 131.795 | 138.380 | 6.585 |

## 6. Tasas según las características del caso de estudio

Descriptivo, para revisar que las variables se comportan de forma razonable.

| Tipo de actividad | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| HOSPITALIZACIÓN | 4.302.657 | 2,09 % | 1,16 % | 5,95 % | 3,15 % |
| CIRUGÍA MAYOR AMBULATORIA (CMA) | 851.948 | 0,41 % | 0,14 % | 1,15 % | 0,33 % |

| Tipo de ingreso | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| URGENCIA | 2.502.556 | 2,46 % | 1,30 % | 7,27 % | 3,66 % |
| PROGRAMADA | 1.766.662 | 0,99 % | 0,33 % | 2,76 % | 0,92 % |
| OBSTETRICA | 884.979 | 1,62 % | 1,42 % | 3,98 % | 3,47 % |
| (sin dato) | 408 | 2,45 % | 0,98 % | 6,86 % | 2,94 % |

| Tipo de alta | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| DOMICILIO | 4.932.337 | 1,67 % | 0,90 % | 4,85 % | 2,52 % |
| HOSPITALIZACIÓN DOMICILIARIA | 131.548 | 3,52 % | 1,74 % | 10,94 % | 5,06 % |
| ALTA VOLUNTARIA | 53.216 | 6,36 % | 4,31 % | 12,66 % | 8,15 % |
| DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE | 20.578 | 3,38 % | 1,88 % | 9,44 % | 4,91 % |
| FUGA DEL PACIENTE | 16.926 | 12,42 % | 8,74 % | 19,91 % | 13,64 % |

| CDM | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| 01 | 256.113 | 1,92 % | 0,97 % | 5,62 % | 2,53 % |
| 02 | 318.364 | 0,26 % | 0,09 % | 0,89 % | 0,21 % |
| 03 | 143.170 | 1,11 % | 0,31 % | 2,49 % | 0,62 % |
| 04 | 437.071 | 2,72 % | 1,79 % | 8,08 % | 5,13 % |
| 05 | 351.459 | 2,39 % | 1,19 % | 8,02 % | 3,96 % |
| 06 | 536.817 | 2,03 % | 1,06 % | 5,24 % | 2,58 % |
| 07 | 346.198 | 1,88 % | 1,05 % | 5,22 % | 3,01 % |
| 08 | 523.082 | 1,08 % | 0,53 % | 3,73 % | 1,83 % |
| 09 | 185.968 | 1,33 % | 0,39 % | 4,57 % | 1,27 % |
| 10 | 65.885 | 2,05 % | 0,81 % | 6,34 % | 2,35 % |
| 11 | 241.587 | 2,42 % | 1,11 % | 7,81 % | 3,69 % |
| 12 | 120.880 | 1,06 % | 0,24 % | 2,57 % | 0,65 % |
| 13 | 487.666 | 2,45 % | 1,99 % | 6,62 % | 5,53 % |
| 14 | 618.882 | 0,77 % | 0,63 % | 1,44 % | 1,06 % |
| 15 | 124.678 | 3,18 % | 1,61 % | 6,20 % | 1,62 % |
| 16 | 60.549 | 2,58 % | 0,79 % | 8,77 % | 2,95 % |
| 17 | 79.369 | 4,12 % | 0,89 % | 11,99 % | 3,22 % |
| 18 | 40.627 | 2,83 % | 0,64 % | 9,00 % | 2,00 % |
| 19 | 70.452 | 2,90 % | 2,15 % | 7,96 % | 5,65 % |
| 20 | 11.754 | 3,20 % | 1,86 % | 8,11 % | 4,24 % |
| 21 | 63.129 | 1,84 % | 0,56 % | 4,94 % | 1,25 % |
| 22 | 67.397 | 1,88 % | 0,30 % | 5,63 % | 0,80 % |
| 23 | 3.508 | 2,68 % | 0,03 % | 7,58 % | 0,03 % |

## 7. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `ventanas_dias` | `7 / 30` | Ventanas de reingreso, en días, separadas por una barra vertical. La más larga no puede superar censura_dias (D20, D22) |
| `reingreso_solo_no_planificado` | `SI` | SI = solo cuentan como reingreso los ingresos no planificados, como indica el resumen de la propuesta; NO = cuenta todo ingreso, también los programados y los partos (D20, D26) |
| `ingresos_no_planificados` | `URGENCIA / OBSTETRICA` | Tipos de ingreso que cuentan como reingreso no planificado, separados por una barra vertical (D20) |
| `grd_parto` | `146 / 147` | Comienzo de los códigos GRD de parto o cesárea: un ingreso con uno de estos GRD no cuenta como reingreso no planificado (D20) |
| `cdm_agrupadas` | `13+14` | CDM que se consideran una sola al comparar la CDM del reingreso con la del caso de estudio. Las CDM de un grupo se unen con + y los grupos se separan con una barra vertical. Vacío = ninguna (H17, D25) |
| `censura_dias` | `30` | Días de seguimiento que deben quedar dentro del bloque después del alta (D22) |

## 8. Columnas nuevas

| Columna | Contenido |
|---|---|
| `REING_7D` | Reingreso dentro de 7 días, por cualquier causa. 1 = sí, 0 = no. |
| `REING_7D_CDM` | Reingreso dentro de 7 días, relacionado (misma CDM). 1 = sí, 0 = no. |
| `REING_30D` | Reingreso dentro de 30 días, por cualquier causa. 1 = sí, 0 = no. |
| `REING_30D_CDM` | Reingreso dentro de 30 días, relacionado (misma CDM). 1 = sí, 0 = no. |
| `DIAS_REING` | Días entre el alta y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia dentro del bloque. Sin dato si no hay ninguno. |
| `ID_EGRESO_REING` | `ID_EGRESO` de ese ingreso, para poder revisar cada par. |

Todas quedan sin dato en los egresos que no son caso de estudio. Describen lo que ocurre después del alta: son variables objetivo o de trazabilidad y **no deben usarse como variables predictoras**.

## 9. Verificaciones

- Las variables tienen dato en todos los casos de estudio y solo en ellos: **sí**.
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
