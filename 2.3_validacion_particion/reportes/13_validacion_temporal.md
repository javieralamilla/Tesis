# Grupos de la validación temporal (actividad 2.3, script 13)

Generado por `2.3_validacion_particion/scripts/13_validacion_temporal.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 2 de la partición (SHA-256 `9546c8c7e80f634295e7c0538173661884aa6ce602e201a3cbd8ae615912abbb`). Salida: `data/processed/validacion_temporal.parquet`. No se abre el conjunto de prueba. Las decisiones están en `2.3_validacion_particion/bitacora.md` (D37 y D40).

**Validación temporal interna:** el modelo se entrena con los casos de estudio de desarrollo de 2019 a 2022 y se evalúa en los de 2023 y 2024. Como el reingreso depende mucho de cada paciente, el resultado se informa de tres maneras: con todos los casos de evaluación, solo con los de pacientes nuevos y solo con los de pacientes ya vistos (revisión del profesor guía del 13 de octubre de 2026, punto 2.2).

**Paciente ya visto:** su identificador tiene cualquier egreso, sea o no caso de estudio en un año de entrenamiento de su mismo bloque (2021 y 2022). Los egresos de 2019 y 2020 tienen otro identificador y no se pueden enlazar (H19), así que la separación vale dentro del bloque 2021–2024: un paciente nuevo pudo estar hospitalizado en 2019 o 2020 con el otro identificador.

## 1. Tamaño y tasas de cada grupo

Cada tasa usa los casos de estudio del grupo con dato en esa variable.

| Grupo | Casos de estudio | % de la evaluación | Pacientes | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|---|---|
| Entrenamiento | 2.168.337 | — | 1.732.822 | 2,00 % | 1,23 % | 5,69 % | 3,45 % |
| Evaluación: todos los casos | 1.185.781 | 100,0 % | 915.896 | 2,18 % | 1,32 % | 6,28 % | 3,74 % |
| Evaluación: pacientes nuevos | 943.588 | 79,6 % | 758.487 | 1,96 % | 1,22 % | 5,42 % | 3,30 % |
| Evaluación: pacientes ya vistos | 242.193 | 20,4 % | 157.409 | 3,05 % | 1,70 % | 9,65 % | 5,34 % |

Los pacientes ya vistos reingresan más que los nuevos: por eso conviene separarlos. En ellos el modelo puede rendir mejor por haberlos visto al entrenar, y ese desempeño no se traslada a pacientes nuevos.

Casos de evaluación por año del alta:

| Año del alta | Casos de evaluación | De pacientes ya vistos | % |
|---|---|---|---|
| 2023 | 616.853 | 139.297 | 22,6 % |
| 2024 | 568.928 | 102.896 | 18,1 % |

Casos de entrenamiento por bloque de identificador: bloque A, 1.093.656; bloque B, 1.074.681.

Egresos que hacen visto a un paciente: 1.393.792 egresos de 1.051.628 identificadores, de 2021 y 2022, del bloque B.

## 2. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `anios_entrenamiento_temporal` | `2019 / 2020 / 2021 / 2022` | Años del alta de los casos de estudio de desarrollo con que se entrena el modelo en la validación temporal interna, separados por una barra vertical (D37, D40) |
| `anios_evaluacion_temporal` | `2023 / 2024` | Años del alta de los casos de estudio de desarrollo con que se evalúa ese modelo (D37, D40) |
| `paciente_visto_egresos` | `TODOS` | Un caso de evaluación es de un paciente ya visto si su identificador tiene un egreso en un año de entrenamiento de su mismo bloque. TODOS = cualquier egreso, sea o no caso de estudio, como pide la revisión del profesor guía del 13 de octubre de 2026 |

## 3. Archivo de salida

| Columna | Contenido |
|---|---|
| `ID_EGRESO` | Caso de estudio de desarrollo. |
| `ID_PACIENTE` | Identificador de paciente: es el grupo de la validación cruzada (D27). |
| `PERIODO` | `ENTRENAMIENTO` (2019 a 2022) o `EVALUACION` (2023 y 2024). |
| `PACIENTE_VISTO` | En los casos de evaluación, verdadero si el paciente ya fue visto en el entrenamiento. Sin dato en los casos de entrenamiento. |

El archivo no contiene las variables objetivo ni nada que dependa de ellas.

## 4. Verificaciones

- El conjunto de desarrollo es el de la versión 2 registrada de la partición: **sí**.
- Todo caso de estudio de desarrollo tiene un período, de entrenamiento o de evaluación: **sí**.
- Los casos de evaluación son de años posteriores a todos los de entrenamiento: **sí**.
- Los pacientes nuevos y los ya vistos suman todos los casos de evaluación, sin repetir ninguno: **sí**.
- `PACIENTE_VISTO` tiene dato solo en los casos de evaluación: **sí**.
- Un paciente ya visto tiene, en un año de entrenamiento de su bloque, un egreso anterior a su caso de evaluación: **sí**.
- El archivo tiene una fila por caso de estudio de desarrollo, como los casos registrados de la partición: **sí**.
- Lo releído del archivo es igual a lo calculado: **sí**.
