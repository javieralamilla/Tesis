# Diagnóstico del identificador de paciente (Paso 1)

Generado por `1.2_exploracion_calidad/scripts/01_diagnostico_ids.py`. Nulos: vacío, `DESCONOCIDO`, `SIN INFORMACIÓN` o `0`.

## 1. Descripción del ID por año

| año | registros | pacientes_distintos | egresos_por_paciente | pct_id_nulo | pct_id_no_numerico | id_min | id_max | largo_id_% |
|---|---|---|---|---|---|---|---|---|
| 2019 | 1151475 | 876183 | 1.3 | 0.721 | 0.0 | 1 | 1464884 | 4 dig: 0.6%, 5 dig: 5.9%, 6 dig: 60.9%, 7 dig: 32.5% |
| 2020 | 781912 | 639102 | 1.22 | 0.242 | 0.0 | 7 | 1464879 | 4 dig: 0.6%, 5 dig: 6.5%, 6 dig: 62.1%, 7 dig: 30.7% |
| 2021 | 816909 | 660299 | 1.23 | 0.25 | 0.0 | 66987933 | 99257716 | 8 dig: 100.0% |
| 2022 | 932840 | 746486 | 1.25 | 0.316 | 0.0 | 66987994 | 100143617 | 8 dig: 99.7%, 9 dig: 0.3% |
| 2023 | 1039587 | 819915 | 1.27 | 0.157 | 0.0 | 66988016 | 974871074 | 8 dig: 98.5%, 9 dig: 1.5% |
| 2024 | 1085813 | 848073 | 1.28 | 0.096 | 0.0 | 66987948 | 102211126 | 8 dig: 94.3%, 9 dig: 5.7% |

## 2. Consistencia dentro del año

Porcentaje de pacientes cuyo ID presenta más de un sexo o fecha de nacimiento.

| año | pacientes | pct_con_>1_sexo | pct_con_>1_fnac |
|---|---|---|---|
| 2019 | 876183.0 | 0.202 | 0.427 |
| 2020 | 639102.0 | 0.135 | 0.345 |
| 2021 | 660299.0 | 0.103 | 0.333 |
| 2022 | 746486.0 | 0.124 | 0.358 |
| 2023 | 819915.0 | 0.114 | 0.313 |
| 2024 | 848073.0 | 0.137 | 0.341 |

## 3. Presencia entre años

Porcentaje de pacientes distintos del año de la fila que aparecen en el año de la columna.

| desde \ en | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| 2019 | — | 8.9% | 0.0% | 0.0% | 0.0% | 0.0% |
| 2020 | 12.3% | — | 0.0% | 0.0% | 0.0% | 0.0% |
| 2021 | 0.0% | 0.0% | — | 13.9% | 11.0% | 10.0% |
| 2022 | 0.0% | 0.0% | 12.3% | — | 15.1% | 11.5% |
| 2023 | 0.0% | 0.0% | 8.9% | 13.7% | — | 15.5% |
| 2024 | 0.0% | 0.0% | 7.8% | 10.1% | 15.0% | — |

## 4. Concordancia entre años

Entre los ID que coinciden, porcentaje con igual sexo y fecha de nacimiento. Valores cercanos a 100% indican que el ID corresponde a la misma persona; valores bajos indican coincidencias numéricas entre personas distintas.

| desde \ en | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| 2019 | — | 97.1% (n=78,320) | sin coincidencias | sin coincidencias | sin coincidencias | sin coincidencias |
| 2020 | 97.1% (n=78,320) | — | sin coincidencias | sin coincidencias | sin coincidencias | sin coincidencias |
| 2021 | sin coincidencias | sin coincidencias | — | 97.8% (n=91,939) | 97.5% (n=72,764) | 97.3% (n=65,731) |
| 2022 | sin coincidencias | sin coincidencias | 97.8% (n=91,939) | — | 97.8% (n=112,475) | 97.6% (n=85,778) |
| 2023 | sin coincidencias | sin coincidencias | 97.5% (n=72,764) | 97.8% (n=112,475) | — | 98.0% (n=127,250) |
| 2024 | sin coincidencias | sin coincidencias | 97.3% (n=65,731) | 97.6% (n=85,778) | 98.0% (n=127,250) | — |
