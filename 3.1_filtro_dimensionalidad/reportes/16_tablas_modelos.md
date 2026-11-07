# Tablas para los modelos

Generado por `3.1_filtro_dimensionalidad/scripts/16_tablas_modelos.py` el 03-11-2026. Cierre de la actividad 3.1 (D57): junta en dos tablas lo que dejaron los scripts 13, 14 y 15 para los modelos de la actividad 3.2. Lee el conjunto de desarrollo de la versión 3 de la partición (registrada el 2026-11-02); no abre el conjunto de prueba.

Versión 1 de las tablas, registrada el 2026-11-03 en `docs/version_tablas_modelos.csv`. El diccionario está en `docs/diccionario_tablas_modelos.md`.

## 1. Tablas

| Archivo | Filas | Columnas | MB | Contenido |
|---|---|---|---|---|
| `data/processed/modelos_casos.parquet` | 3.347.652 | 40 | 63,1 | una fila por caso de estudio de desarrollo |
| `data/processed/modelos_codigos.parquet` | 59.214.795 | 4 | 124,1 | una fila por caso de estudio y código |

Los modelos leen estas dos tablas y las listas de códigos (`data/processed/listas_codigos.parquet`, del script 14). Juntas ocupan 187 MB, frente a 280 MB de `desarrollo.parquet`.

## 2. Casos de cada variable objetivo

Una sola tabla de casos para las cuatro variables: cada modelo usa los casos con dato en la suya. Los casos sin dato no son 0.

| Variable | Casos con dato | Reingresos | Tasa | Sin dato | Por qué no tienen dato |
|---|---|---|---|---|---|
| `REING_7D` | 3.347.652 | 69.190 | 2,07 % | 0 | — |
| `REING_7D_CDM` | 2.855.319 | 36.141 | 1,27 % | 492.333 | partos (CDM 14) |
| `REING_30D` | 3.275.432 | 193.153 | 5,90 % | 72.220 | alta a menos de 60 días del cierre del bloque |
| `REING_30D_CDM` | 2.792.482 | 99.219 | 3,55 % | 555.170 | partos o sin dato en REING_30D |

## 3. Columnas de la tabla de casos, por papel

| Papel | Columnas | Cuáles |
|---|---|---|
| IDENTIFICADOR | 2 | `ID_EGRESO`, `ID_PACIENTE` |
| VALIDACION | 4 | `ANIO_ALTA`, `PERIODO`, `PACIENTE_VISTO`, `PLIEGUE` |
| PREDICTORA | 30 | las 30 variables del script 15 (D46 a D49 y D54) |
| OBJETIVO | 4 | `REING_7D`, `REING_7D_CDM`, `REING_30D`, `REING_30D_CDM` |

La descripción de cada columna está en `docs/diccionario_tablas_modelos.md` y en `3.1_filtro_dimensionalidad/reglas/columnas_modelos.csv`.

## 4. Códigos de los casos

Se guardan en formato largo: una fila por caso y código, solo con los códigos que están en alguna lista de alguna variable y pliegue. Ningún modelo usa los demás: los códigos completos que quedan fuera tienen menos de 100 casos en todas las variables, y las categorías que quedan fuera no pasan la regla de la lista agrupada en ninguna variable ni pliegue.

| Códigos | Distintos en desarrollo | Pares caso–código | Distintos en alguna lista | Pares en la tabla | % de los pares |
|---|---|---|---|---|---|
| Diagnósticos completos | 16.335 | 18.431.449 | 5.228 | 18.230.547 | 98,9 % |
| Diagnósticos en su categoría | 2.028 | 17.681.902 | 264 | 11.729.951 | 66,3 % |
| Procedimientos completos | 3.753 | 29.310.101 | 1.956 | 29.254.297 | 99,8 % |

139 casos (0,004 %) no tienen ninguna fila en la tabla de códigos: 8 no tienen ningún diagnóstico ni procedimiento, y los demás solo tienen códigos que no están en ninguna lista. En la matriz, su fila queda con 0 en todas las columnas.

## 5. Tamaño de las matrices

Para cada variable y lista de todo desarrollo: cuántas filas (casos con dato) y columnas (códigos) tiene la matriz, cuántas celdas valen 1 y cuánto ocuparía guardada entera (un byte por celda) o como matriz dispersa (solo los 1: unos 5 bytes por cada uno y 8 por fila). Las listas de cada pliegue tienen un número parecido de columnas.

| Variable | Lista | Filas | Columnas | Celdas con 1 | % de celdas con 1 | Casos con algún código | Entera (GB) | Dispersa (MB) |
|---|---|---|---|---|---|---|---|---|
| `REING_7D` | A | 3.347.652 | 108 | 16.620.224 | 4,597 % | 92,1 % | 0,36 | 110 |
| `REING_7D` | C | 3.347.652 | 849 | 18.355.940 | 0,646 % | 95,6 % | 2,84 | 119 |
| `REING_7D` | Agrupada | 3.347.652 | 112 | 18.694.271 | 4,986 % | 93,5 % | 0,37 | 120 |
| `REING_7D` | Sin filtro | 3.347.652 | 7.184 | 47.484.844 | 0,197 % | 100,0 % | 24,05 | 264 |
| `REING_7D_CDM` | A | 2.855.319 | 57 | 5.818.937 | 3,575 % | 83,6 % | 0,16 | 52 |
| `REING_7D_CDM` | C | 2.855.319 | 629 | 7.820.789 | 0,435 % | 91,2 % | 1,80 | 62 |
| `REING_7D_CDM` | Agrupada | 2.855.319 | 46 | 6.099.891 | 4,644 % | 84,3 % | 0,13 | 53 |
| `REING_7D_CDM` | Sin filtro | 2.855.319 | 6.975 | 40.335.429 | 0,203 % | 100,0 % | 19,92 | 225 |
| `REING_30D` | A | 3.275.432 | 424 | 30.366.906 | 2,187 % | 98,2 % | 1,39 | 178 |
| `REING_30D` | C | 3.275.432 | 1.595 | 31.750.402 | 0,608 % | 99,0 % | 5,22 | 185 |
| `REING_30D` | Agrupada | 3.275.432 | 348 | 31.498.995 | 2,763 % | 98,5 % | 1,14 | 184 |
| `REING_30D` | Sin filtro | 3.275.432 | 7.116 | 46.426.696 | 0,199 % | 100,0 % | 23,31 | 258 |
| `REING_30D_CDM` | A | 2.792.482 | 191 | 14.268.238 | 2,675 % | 95,5 % | 0,53 | 94 |
| `REING_30D_CDM` | C | 2.792.482 | 1.165 | 16.144.167 | 0,496 % | 97,9 % | 3,25 | 103 |
| `REING_30D_CDM` | Agrupada | 2.792.482 | 168 | 17.167.880 | 3,659 % | 97,5 % | 0,47 | 108 |
| `REING_30D_CDM` | Sin filtro | 2.792.482 | 6.913 | 39.417.535 | 0,204 % | 100,0 % | 19,30 | 219 |

## 6. Ejemplo

El caso `20230000956` (hombre de 73 años, alta en 2023, CDM 01, 2 hospitalizaciones previas, pliegue 4, `REING_30D` = 0) tiene 13 filas en `modelos_codigos.parquet`. Con `REING_30D`, cada «sí» es un 1 en la columna de ese código en la matriz de esa lista (todo desarrollo):

| Código | Bloque | Nivel | Lista A | Lista C | Lista agrupada | Lista sin filtro |
|---|---|---|---|---|---|---|
| `G91.9` | Diagnóstico | Completo | sí | sí | — | sí |
| `H40.9` | Diagnóstico | Completo | — | — | — | sí |
| `I48.9` | Diagnóstico | Completo | sí | sí | — | sí |
| `Z92.1` | Diagnóstico | Completo | sí | sí | — | sí |
| `G91` | Diagnóstico | Categoría | — | — | sí | — |
| `I48` | Diagnóstico | Categoría | — | — | sí | — |
| `Z92` | Diagnóstico | Categoría | — | — | sí | — |
| `02.34` | Procedimiento | Completo | sí | sí | sí | sí |
| `87.03` | Procedimiento | Completo | sí | sí | sí | sí |
| `90.02` | Procedimiento | Completo | — | — | — | sí |
| `93.12` | Procedimiento | Completo | sí | sí | sí | sí |
| `99.26` | Procedimiento | Completo | sí | sí | sí | sí |
| `99.29` | Procedimiento | Completo | sí | sí | sí | sí |

## 7. Verificaciones

15 verificaciones, 0 fallidas.

- El conjunto de desarrollo es el de la versión 3 registrada de la partición, y validacion_temporal.parquet y variables_casos.parquet tienen exactamente sus casos de estudio, en el mismo orden: **sí**.
- La tabla de casos tiene una fila por caso de estudio de desarrollo, sin repetir ID_EGRESO: **sí**.
- Sus columnas son las de columnas_modelos.csv, en su orden, y no tiene ninguna de las que nunca pueden estar: **sí**.
- ID_PACIENTE de desarrollo es igual al de validacion_temporal.parquet en todos los casos: **sí**.
- ANIO_ALTA es el año de la fecha de alta, y PERIODO corresponde a los años de la validación temporal: **sí**.
- PACIENTE_VISTO tiene dato justo en los casos de evaluación: **sí**.
- PLIEGUE va de 1 a 5 y ningún paciente está en dos pliegues: **sí**.
- Las variables objetivo valen 0 o 1, y REING_7D tiene dato en todos los casos: **sí**.
- Las variables relacionadas no tienen dato justo en los partos (CDM 14) y, a 30 días, en los casos sin dato en REING_30D: **sí**.
- Antes de quitar los códigos que no están en ninguna lista, cada caso tiene tantos diagnósticos y procedimientos distintos como dicen N_DIAGNOSTICOS y N_PROCEDIMIENTOS (script 15): **sí**.
- La tabla de códigos no repite un código en un caso, y está ordenada por caso: **sí**.
- Todo código de alguna lista aparece en la tabla de códigos, y la tabla no tiene códigos fuera de las listas: **sí**.
- Para cada variable y cada código de alguna lista, la tabla de códigos tiene los mismos casos con dato que filtro_codigos.parquet (las columnas de la matriz suman lo mismo que el filtro): **sí**.
- En las listas de cada pliegue, todo código tiene al menos 100 casos con dato en el entrenamiento del pliegue, y en las de todo desarrollo, en todo desarrollo: **sí**.
- Lo releído de modelos_casos.parquet y de modelos_codigos.parquet es igual a lo calculado: **sí**.
