# Grupos de la validación temporal y pliegues de la validación cruzada (actividad 2.3, script 13)

Generado por `2.3_validacion_particion/scripts/13_validacion_temporal.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 3 de la partición (SHA-256 `50f07908f35df51c31077971d0aafaf69182c3baea926af34b00d6fff41229b1`). Salida: `data/processed/validacion_temporal.parquet`. No se abre el conjunto de prueba. Las decisiones están en `2.3_validacion_particion/bitacora.md` (D37, D40 y D52).

**Validación temporal interna:** el modelo se entrena con los casos de estudio de desarrollo de 2019 a 2022 y se evalúa en los de 2023 y 2024. Como el reingreso depende mucho de cada paciente, el resultado se informa de tres maneras: con todos los casos de evaluación, solo con los de pacientes nuevos y solo con los de pacientes ya vistos (revisión del profesor guía del 13 de octubre de 2026, punto 2.2).

**Paciente ya visto:** su identificador tiene cualquier egreso, sea o no caso de estudio en un año de entrenamiento de su mismo bloque (2021 y 2022). Los egresos de 2019 y 2020 tienen otro identificador y no se pueden enlazar (H19), así que la separación vale dentro del bloque 2021–2024: un paciente nuevo pudo estar hospitalizado en 2019 o 2020 con el otro identificador.

## 1. Tamaño y tasas de cada grupo

Cada tasa usa los casos de estudio del grupo con dato en esa variable.

| Grupo | Casos de estudio | % de la evaluación | Pacientes | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|---|
| Entrenamiento | 2.164.089 | — | 1.732.822 | 2,00 % | 1,23 % | 5,69 % | 3,45 % |
| Evaluación: todos los casos | 1.183.563 | 100,0 % | 915.863 | 2,19 % | 1,32 % | 6,28 % | 3,74 % |
| Evaluación: pacientes nuevos | 942.838 | 79,7 % | 758.487 | 1,96 % | 1,22 % | 5,41 % | 3,30 % |
| Evaluación: pacientes ya vistos | 240.725 | 20,3 % | 157.376 | 3,06 % | 1,70 % | 9,67 % | 5,35 % |

Los pacientes ya vistos reingresan más que los nuevos: por eso conviene separarlos. En ellos el modelo puede rendir mejor por haberlos visto al entrenar, y ese desempeño no se traslada a pacientes nuevos.

Casos de evaluación por año del alta:

| Año del alta | Casos de evaluación | De pacientes ya vistos | % |
|---|---|---|---|
| 2023 | 615.867 | 138.495 | 22,5 % |
| 2024 | 567.696 | 102.230 | 18,0 % |

Casos de entrenamiento por bloque de identificador: bloque A, 1.091.338; bloque B, 1.072.751.

Egresos que hacen visto a un paciente: 1.393.792 egresos de 1.051.628 identificadores, de 2021 y 2022, del bloque B.

## 2. Pliegues de la validación cruzada

La validación cruzada reparte los casos de estudio de desarrollo en 5 pliegues: el modelo se entrena 5 veces, cada vez con 4 pliegues, y se evalúa con el que quedó fuera. Los pliegues se arman por paciente: todos los casos de un identificador de paciente quedan en el mismo pliegue, para que el modelo nunca se evalúe con un paciente que vio al entrenar (D37 y D52). El reparto usa el método de la partición (D28): estratos por bloque y por el patrón de las variables objetivo del paciente, orden por sus casos con reingreso en `REING_30D` y por sus casos de estudio, y punto de partida al azar con la semilla del proyecto (2026).

**Por qué por paciente:** 536.792 de los 2.509.082 pacientes tienen dos casos de estudio o más, y suman 1.375.362 casos (41,1 %); un paciente llega a 71. Si los pliegues se armaran por egreso, el 36,2 % de los casos de validación tendría otro caso de su mismo paciente en el entrenamiento, y un modelo como Random Forest o XGBoost podría aprender a reconocer a esa persona en vez de predecir el reingreso.

Tamaño y tasas de cada pliegue (cada tasa usa los casos de estudio del pliegue con dato en esa variable):

| Pliegue | Casos de estudio | % de los casos | Pacientes | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|---|
| 1 | 669.548 | 20,00 % | 501.816 | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
| 2 | 669.521 | 20,00 % | 501.815 | 2,07 % | 1,27 % | 5,90 % | 3,55 % |
| 3 | 669.477 | 20,00 % | 501.815 | 2,06 % | 1,26 % | 5,89 % | 3,55 % |
| 4 | 669.533 | 20,00 % | 501.816 | 2,08 % | 1,27 % | 5,89 % | 3,55 % |
| 5 | 669.573 | 20,00 % | 501.820 | 2,06 % | 1,27 % | 5,90 % | 3,55 % |

La mayor diferencia de una tasa entre dos pliegues es de 0,016 puntos porcentuales.

## 3. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `anios_entrenamiento_temporal` | `2019 / 2020 / 2021 / 2022` | Años del alta de los casos de estudio de desarrollo con que se entrena el modelo en la validación temporal interna, separados por una barra vertical (D37, D40) |
| `anios_evaluacion_temporal` | `2023 / 2024` | Años del alta de los casos de estudio de desarrollo con que se evalúa ese modelo (D37, D40) |
| `paciente_visto_egresos` | `TODOS` | Un caso de evaluación es de un paciente ya visto si su identificador tiene un egreso en un año de entrenamiento de su mismo bloque. TODOS = cualquier egreso, sea o no caso de estudio, como pide la revisión del profesor guía del 13 de octubre de 2026. CASOS = solo un caso de estudio (D40) |
| `semilla` | `2026` | Semilla fija del proyecto para todo componente aleatorio: la partición inicial y, en las etapas siguientes, la validación cruzada y los modelos (D28) |
| `variable_principal` | `REING_30D` | Variable objetivo principal. Dentro de cada estrato, los identificadores se ordenan por su número de casos de estudio con reingreso en esta variable antes de tomar uno de cada N (D28) |
| `pliegues_validacion_cruzada` | `5` | Número de pliegues de la validación cruzada dentro del conjunto de desarrollo. Todos los casos de un identificador de paciente quedan en el mismo pliegue, repartidos con el método de la partición: estratos por bloque y por el patrón de las variables objetivo, orden por los reingresos de variable_principal y punto de partida al azar con la semilla (D37, D52) |

## 4. Archivo de salida

| Columna | Contenido |
|---|---|
| `ID_EGRESO` | Caso de estudio de desarrollo. |
| `ID_PACIENTE` | Identificador de paciente: es el grupo de la validación cruzada (D27). |
| `PERIODO` | `ENTRENAMIENTO` (2019 a 2022) o `EVALUACION` (2023 y 2024). |
| `PACIENTE_VISTO` | En los casos de evaluación, verdadero si el paciente ya fue visto en el entrenamiento. Sin dato en los casos de entrenamiento. |
| `PLIEGUE` | Pliegue de la validación cruzada, de 1 a 5: el mismo para todos los casos de un paciente (D52). |

El archivo no contiene las variables objetivo. Los pliegues se estratifican por el patrón de reingresos del paciente, igual que la partición, solo para que las tasas queden parejas entre pliegues: no son una variable del modelo.

## 5. Verificaciones

- El conjunto de desarrollo es el de la versión 3 registrada de la partición: **sí**.
- Todo caso de estudio de desarrollo tiene un período, de entrenamiento o de evaluación: **sí**.
- Los casos de evaluación son de años posteriores a todos los de entrenamiento: **sí**.
- Los pacientes nuevos y los ya vistos suman todos los casos de evaluación, sin repetir ninguno: **sí**.
- `PACIENTE_VISTO` tiene dato solo en los casos de evaluación: **sí**.
- Un paciente ya visto tiene, en un año de entrenamiento de su bloque, un egreso anterior a su caso de evaluación: **sí**.
- Todo caso de estudio tiene un pliegue de 1 a 5 y todos los casos de un paciente están en el mismo pliegue: **sí**.
- Cada pliegue tiene entre 19,5 % y 20,5 % de los casos de estudio: **sí**.
- La tasa de cada variable objetivo difiere en menos de 0,05 puntos porcentuales entre los pliegues: **sí**.
- El archivo tiene una fila por caso de estudio de desarrollo, como los casos registrados de la partición: **sí**.
- Lo releído del archivo es igual a lo calculado: **sí**.
