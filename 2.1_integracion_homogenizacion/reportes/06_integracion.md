# Integración de los seis años (Paso 4)

Generado por `2.1_integracion_homogenizacion/scripts/06_integrar.py`. Entrada: `data/interim/homog_<año>.parquet`. Salida: `data/processed/grd_2019_2024.parquet`. No se elimina ningún registro.

## 1. Resultado

|  | Valor |
|---|---|
| Registros en la tabla integrada | 5.808.536 |
| Suma de los seis archivos homogenizados | 5.808.536 |
| Columnas | 136 |
| Tamaño del archivo | 295 MB |
| `ID_EGRESO` distintos | 5.808.536 |

| Año | Registros homogenizados | Registros integrados |
|---|---|---|
| 2019 | 1.151.475 | 1.151.475 |
| 2020 | 781.912 | 781.912 |
| 2021 | 816.909 | 816.909 |
| 2022 | 932.840 | 932.840 |
| 2023 | 1.039.587 | 1.039.587 |
| 2024 | 1.085.813 | 1.085.813 |

**Verificación:** registros por año conservados: **sí**; `ID_EGRESO` único: **sí**.

## 2. Columnas nuevas

| Columna | Contenido |
|---|---|
| `ID_EGRESO` | Identificador único del egreso: año del archivo × 10.000.000 + número de línea en el txt original. Ejemplo: la línea 2 del archivo 2023 es `20230000002`. |
| `DUP_EXACTO` | Verdadero en los registros que son copia idéntica, en todas las columnas de datos, de un registro anterior del mismo archivo. La primera aparición queda en falso. |
| `DUP_CLAVE` | Verdadero en todos los registros que comparten paciente, hospital, fecha de ingreso y fecha de alta con otro registro. Solo se evalúa cuando esos cuatro datos existen. |

## 3. Duplicados marcados

Como cada archivo contiene los egresos de un año de alta, los duplicados solo pueden darse dentro de un mismo año.

| Año | Copias exactas (`DUP_EXACTO`) | Registros con clave repetida (`DUP_CLAVE`) | Grupos con clave repetida | Registros sin clave completa (no evaluables) |
|---|---|---|---|---|
| 2019 | 159 | 1.953 | 973 | 8.324 |
| 2020 | 2.818 | 6.648 | 3.319 | 1.893 |
| 2021 | 279 | 1.297 | 648 | 2.044 |
| 2022 | 63 | 1.459 | 726 | 2.949 |
| 2023 | 169 | 1.958 | 976 | 1.635 |
| 2024 | 330 | 2.419 | 1.208 | 1.089 |
| **Total** | **3.818** | **15.734** | **7.850** | **17.934** |

## 4. Tabla de control por año

Sirve para detectar años que se comporten distinto al resto.

| Indicador | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Egresos | 1.151.475 | 781.912 | 816.909 | 932.840 | 1.039.587 | 1.085.813 |
| Pacientes distintos | 876.183 | 639.102 | 660.299 | 746.486 | 819.915 | 848.073 |
| Hospitales | 65 | 65 | 65 | 65 | 68 | 72 |
| Egresos por paciente | 1,3 | 1,22 | 1,23 | 1,25 | 1,27 | 1,28 |
| % mujeres | 59,2 | 59 | 58,2 | 59,3 | 58,9 | 58,3 |
| Edad media al ingreso (años) | 43,7 | 44,2 | 44,7 | 44,3 | 44,9 | 46,1 |
| % ingreso por urgencia | 47,6 | 55,3 | 56 | 50,2 | 49,9 | 50,8 |
| % cirugía mayor ambulatoria | 12,8 | 10,2 | 12,6 | 16,6 | 18,6 | 19,5 |
| % alta por fallecimiento | 2,57 | 3,83 | 3,91 | 2,94 | 2,42 | 2,46 |
| Estadía mediana (días) | 2 | 3 | 3 | 3 | 2 | 2 |
| Estadía media (días) | 5,26 | 6,59 | 6,86 | 6,18 | 5,8 | 5,69 |
| Peso GRD medio | 0,8447 | 1,0064 | 1,1054 | 0,9739 | 0,9603 | 0,9666 |

Promedio de valores informados por egreso en las columnas repetidas:

| Grupo de columnas | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Diagnósticos (de 35) | 4,37 | 5,20 | 5,55 | 5,35 | 5,50 | 5,77 |
| Procedimientos (de 30) | 6,74 | 8,34 | 9,04 | 8,35 | 8,13 | 8,02 |
| Traslados internos (de 9) | 0,21 | 0,32 | 0,32 | 0,26 | 0,24 | 0,24 |
| Recién nacidos con peso (de 4) | 0,14 | 0,17 | 0,15 | 0,15 | 0,13 | 0,11 |

## 5. Egresos por mes de alta

| Año | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 95.942 | 85.225 | 98.816 | 97.999 | 99.860 | 99.136 | 103.904 | 104.545 | 91.746 | 98.017 | 84.070 | 92.197 |
| 2020 | 88.314 | 79.555 | 74.977 | 48.087 | 52.086 | 52.282 | 57.898 | 60.712 | 63.378 | 69.116 | 69.223 | 66.284 |
| 2021 | 65.664 | 59.835 | 67.965 | 61.983 | 63.576 | 63.009 | 66.850 | 72.641 | 72.024 | 74.980 | 73.776 | 74.606 |
| 2022 | 70.738 | 60.671 | 76.570 | 76.173 | 79.616 | 77.886 | 77.755 | 84.213 | 79.922 | 81.875 | 82.923 | 84.498 |
| 2023 | 81.710 | 74.776 | 90.914 | 84.951 | 92.271 | 88.732 | 88.159 | 92.597 | 83.516 | 87.134 | 88.471 | 86.356 |
| 2024 | 89.516 | 83.304 | 89.175 | 93.144 | 92.799 | 87.377 | 95.835 | 95.443 | 83.970 | 97.395 | 88.519 | 89.336 |

## 6. Porcentaje de registros sin dato, por columna y año

Solo columnas con algún valor faltante. De las columnas repetidas se muestra la primera (`DIAGNOSTICO1` es el diagnóstico principal).

| Columna | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `ID_PACIENTE` | 0,72 | 0,24 | 0,25 | 0,32 | 0,16 | 0,10 |
| `SEXO` | 0,01 | 0,02 | 0,01 | 0,01 | <0,01 | 0,01 |
| `FECHA_NACIMIENTO` | <0,01 | <0,01 | 0 | <0,01 | <0,01 | <0,01 |
| `ETNIA` | <0,01 | 0 | 0 | 0 | 0 | 0 |
| `PROVINCIA` | 0,07 | 0,08 | <0,01 | <0,01 | 0,03 | 0,04 |
| `COMUNA` | 0,08 | 0,03 | <0,01 | 0,01 | <0,01 | <0,01 |
| `NACIONALIDAD` | 1,79 | 0,39 | 0 | 0 | 0 | 0 |
| `PREVISION` | 0,35 | 0,13 | <0,01 | 0,01 | <0,01 | <0,01 |
| `SERVICIO_SALUD` | 0,01 | 0,04 | 0,06 | 0,01 | 0,07 | 0,05 |
| `TIPO_PROCEDENCIA` | 0,02 | 0,01 | 0,38 | <0,01 | <0,01 | <0,01 |
| `TIPO_INGRESO` | 0,03 | <0,01 | <0,01 | <0,01 | 0,01 | <0,01 |
| `ESPECIALIDAD_MEDICA` | <0,01 | <0,01 | 0 | 0 | 0 | 0 |
| `TIPO_ACTIVIDAD` | <0,01 | 0 | 0 | 0 | 0 | 0 |
| `FECHA_INGRESO` | <0,01 | 0 | 0 | 0 | 0 | <0,01 |
| `SERVICIOINGRESO` | 0,25 | 0,02 | 0,45 | 0,59 | 0,71 | 0,75 |
| `FECHAALTA` | <0,01 | 0 | 0 | 0 | 0 | 0 |
| `SERVICIOALTA` | 0,26 | 0,03 | 0,34 | 0,49 | 0,63 | 0,69 |
| `TIPOALTA` | 0,01 | <0,01 | 0 | 0 | 0 | 0 |
| `DIAGNOSTICO1` | 0,75 | 0,30 | 0,03 | 0,02 | 0 | 0 |
| `PROCEDIMIENTO1` | 0,96 | 0,86 | 0,02 | 0,02 | 0,02 | 0,01 |
| `MEDICOINTERV1_ENCRIPTADO` | 47,51 | 47,57 | 47,09 | 42,50 | 42,33 | 43,06 |
| `FECHAINTERV1` | 48,83 | 49,35 | 50,19 | 50,13 | 49,13 | 51,30 |
| `ESPECIALIDADINTERVENCION` | 47,35 | 47,34 | 47,04 | 42,67 | 42,39 | 42,91 |
| `MEDICOALTA_ENCRIPTADO` | 0,21 | 0,14 | 0 | 0 | 0 | 0 |
| `USOSPABELLON` | 44,22 | 99,99 | 43,35 | 39,41 | 38,88 | 39,62 |
| `IR_29301_COD_GRD` | <0,01 | 0 | 0 | <0,01 | <0,01 | <0,01 |
| `CDM` | <0,01 | 0 | 0 | <0,01 | <0,01 | <0,01 |
| `IR_29301_PESO` | <0,01 | 0 | 0 | <0,01 | <0,01 | <0,01 |
| `IR_29301_SEVERIDAD` | <0,01 | 0 | 0 | <0,01 | <0,01 | <0,01 |
| `IR_29301_MORTALIDAD` | <0,01 | 0 | 0 | <0,01 | <0,01 | <0,01 |
| `HOSPPROCEDENCIA` | 89,06 | 86,51 | 85,70 | 87,11 | 86,52 | 91,47 |

## 7. Pacientes que reaparecen al año siguiente

Confirma que la tabla integrada permite seguir a un paciente entre años dentro de cada bloque de identificador (A: 2019–2020; B: 2021–2024) y que entre bloques no hay vínculo (bitácora H02 y D03).

| Años | Pacientes del primer año | Reaparecen al año siguiente | % |
|---|---|---|---|
| 2019 → 2020 | 876.183 | 78.320 | 8,9 % |
| 2020 → 2021 | 639.102 | 0 | 0,0 % |
| 2021 → 2022 | 660.299 | 91.939 | 13,9 % |
| 2022 → 2023 | 746.486 | 112.475 | 15,1 % |
| 2023 → 2024 | 819.915 | 127.250 | 15,5 % |
