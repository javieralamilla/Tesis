# Entrenamiento de los modelos con validación cruzada (script 17)

Última ejecución: etapa `c`, el 2026-11-27 00:55, en 289.8 minutos. Commit del código: `ca88716` (cambios sin confirmar en los scripts o las reglas: NO). Tablas para los modelos: versión 1 del 2026-11-03. Python 3.14.5, numpy 2.5.3, pandas 3.0.3, scipy 1.18.1, scikit-learn 1.9.0, XGBoost 3.3.0. Semilla 2026; hasta 50 procesadores.

## 1. Verificaciones de esta ejecución

- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D__LR__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D__RF__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D__XGB__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D_CDM__LR__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D_CDM__RF__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_7D_CDM__XGB__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D__LR__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D__RF__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D__XGB__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D_CDM__LR__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D_CDM__RF__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Cada vuelta usa la lista calculada sin su pliegue (la sin filtro, la de todo desarrollo) (D53)
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Entrenamiento y validación no comparten casos ni pacientes (D52)
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: La matriz tiene las columnas esperadas: 13 numéricas, 3 sí/no, los valores de las categorías y los códigos de la lista
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Cada código vale 0 o 1 en cada caso
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento (recalculadas desde las tablas)
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Entran solo las columnas predictoras (sin HOSPITAL en los entrenamientos sin hospital) y los códigos de la lista; nunca identificadores, pliegue, año ni variables objetivo
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Cada caso con dato tiene exactamente una probabilidad, de la vuelta en que estuvo en validación
- ✓ REING_30D_CDM__XGB__C__con_hospital__sin_ponderar: Las probabilidades están entre 0 y 1, sin valores vacíos

Códigos de las listas que ningún caso de la tabla tiene (su columna queda en 0): 0. Con las tablas completas debe ser 0, porque toda lista exige al menos 100 casos (D45).

## 2. Prueba de tiempos

Todavía no se ejecuta.

## 3. Combinaciones guardadas

| Variable | Modelo | Lista | Hospital | Ponderación | Casos | Minutos | Llegó a la solución |
|---|---|---|---|---|---|---|---|
| REING_30D_CDM | LR | AGRUPADA | con hospital | sin ponderar | 2.792.482 | 8,1 | SI |
| REING_30D_CDM | LR | A | con hospital | sin ponderar | 2.792.482 | 8,5 | SI |
| REING_30D_CDM | LR | A | sin hospital | sin ponderar | 2.792.482 | 9,2 | SI |
| REING_30D_CDM | LR | C | con hospital | sin ponderar | 2.792.482 | 8,2 | SI |
| REING_30D_CDM | RF | AGRUPADA | con hospital | sin ponderar | 2.792.482 | 28,6 | — |
| REING_30D_CDM | RF | A | con hospital | sin ponderar | 2.792.482 | 27,6 | — |
| REING_30D_CDM | RF | A | sin hospital | sin ponderar | 2.792.482 | 39,3 | — |
| REING_30D_CDM | RF | C | con hospital | sin ponderar | 2.792.482 | 25,3 | — |
| REING_30D_CDM | XGB | AGRUPADA | con hospital | sin ponderar | 2.792.482 | 0,4 | — |
| REING_30D_CDM | XGB | A | con hospital | sin ponderar | 2.792.482 | 0,4 | — |
| REING_30D_CDM | XGB | A | sin hospital | sin ponderar | 2.792.482 | 0,5 | — |
| REING_30D_CDM | XGB | C | con hospital | sin ponderar | 2.792.482 | 0,4 | — |
| REING_30D | LR | AGRUPADA | con hospital | sin ponderar | 3.275.432 | 6,5 | SI |
| REING_30D | LR | A | con hospital | sin ponderar | 3.275.432 | 5,2 | SI |
| REING_30D | LR | A | sin hospital | sin ponderar | 3.275.432 | 5,7 | SI |
| REING_30D | LR | C | con hospital | sin ponderar | 3.275.432 | 6,8 | SI |
| REING_30D | RF | AGRUPADA | con hospital | sin ponderar | 3.275.432 | 53,4 | — |
| REING_30D | RF | A | con hospital | sin ponderar | 3.275.432 | 52,6 | — |
| REING_30D | RF | A | sin hospital | sin ponderar | 3.275.432 | 50,2 | — |
| REING_30D | RF | C | con hospital | sin ponderar | 3.275.432 | 45,4 | — |
| REING_30D | XGB | AGRUPADA | con hospital | sin ponderar | 3.275.432 | 0,5 | — |
| REING_30D | XGB | A | con hospital | sin ponderar | 3.275.432 | 0,4 | — |
| REING_30D | XGB | A | sin hospital | sin ponderar | 3.275.432 | 0,5 | — |
| REING_30D | XGB | C | con hospital | sin ponderar | 3.275.432 | 0,5 | — |
| REING_7D_CDM | LR | AGRUPADA | con hospital | sin ponderar | 2.855.319 | 47,3 | SI |
| REING_7D_CDM | LR | A | con hospital | ponderado | 2.855.319 | 1203,1 | SI |
| REING_7D_CDM | LR | A | con hospital | sin ponderar | 2.855.319 | 72,0 | SI |
| REING_7D_CDM | LR | A | sin hospital | sin ponderar | 2.855.319 | 76,9 | SI |
| REING_7D_CDM | LR | C | con hospital | sin ponderar | 2.855.319 | 84,6 | SI |
| REING_7D_CDM | RF | AGRUPADA | con hospital | sin ponderar | 2.855.319 | 18,5 | — |
| REING_7D_CDM | RF | A | con hospital | ponderado | 2.855.319 | 15,6 | — |
| REING_7D_CDM | RF | A | con hospital | sin ponderar | 2.855.319 | 19,8 | — |
| REING_7D_CDM | RF | A | sin hospital | sin ponderar | 2.855.319 | 17,7 | — |
| REING_7D_CDM | RF | C | con hospital | sin ponderar | 2.855.319 | 17,8 | — |
| REING_7D_CDM | XGB | AGRUPADA | con hospital | sin ponderar | 2.855.319 | 0,4 | — |
| REING_7D_CDM | XGB | A | con hospital | ponderado | 2.855.319 | 0,3 | — |
| REING_7D_CDM | XGB | A | con hospital | sin ponderar | 2.855.319 | 0,4 | — |
| REING_7D_CDM | XGB | A | sin hospital | sin ponderar | 2.855.319 | 0,4 | — |
| REING_7D_CDM | XGB | C | con hospital | sin ponderar | 2.855.319 | 0,3 | — |
| REING_7D | LR | AGRUPADA | con hospital | sin ponderar | 3.347.652 | 54,6 | SI |
| REING_7D | LR | A | con hospital | sin ponderar | 3.347.652 | 43,6 | SI |
| REING_7D | LR | A | sin hospital | sin ponderar | 3.347.652 | 14,4 | SI |
| REING_7D | LR | C | con hospital | sin ponderar | 3.347.652 | 38,5 | SI |
| REING_7D | RF | AGRUPADA | con hospital | sin ponderar | 3.347.652 | 34,3 | — |
| REING_7D | RF | A | con hospital | sin ponderar | 3.347.652 | 33,1 | — |
| REING_7D | RF | A | sin hospital | sin ponderar | 3.347.652 | 45,6 | — |
| REING_7D | RF | C | con hospital | sin ponderar | 3.347.652 | 48,9 | — |
| REING_7D | XGB | AGRUPADA | con hospital | sin ponderar | 3.347.652 | 0,4 | — |
| REING_7D | XGB | A | con hospital | sin ponderar | 3.347.652 | 0,5 | — |
| REING_7D | XGB | A | sin hospital | sin ponderar | 3.347.652 | 0,6 | — |
| REING_7D | XGB | C | con hospital | sin ponderar | 3.347.652 | 0,6 | — |

Combinaciones guardadas: 51 de 63 (D64).

## 4. Valores completos de cada modelo

Los de D62 están escritos explícitos en `reglas/parametros.csv`; el resto son los de la biblioteca.

- **regresión logística con multa L1:** `C` = 1.0, `dual` = False, `fit_intercept` = True, `intercept_scaling` = 100.0, `l1_ratio` = 1.0, `max_iter` = 1000, `penalty` = deprecated, `random_state` = 2026, `solver` = liblinear, `tol` = 0.0001, `verbose` = 0, `warm_start` = False
- **Random Forest:** `bootstrap` = True, `ccp_alpha` = 0.0, `criterion` = gini, `max_features` = sqrt, `min_impurity_decrease` = 0.0, `min_samples_leaf` = 1, `min_samples_split` = 10, `min_weight_fraction_leaf` = 0.0, `n_estimators` = 100, `n_jobs` = 50, `oob_score` = False, `random_state` = 2026, `verbose` = 0, `warm_start` = False
- **XGBoost:** `device` = cpu, `enable_categorical` = True, `learning_rate` = 0.3, `max_depth` = 6, `missing` = nan, `n_estimators` = 100, `n_jobs` = 50, `objective` = binary:logistic, `random_state` = 2026, `scale_pos_weight` = 1.0, `tree_method` = hist
