# Homogenización de los seis años (Paso 3)

Generado por `2.1_integracion_homogenizacion/scripts/05_homogenizar.py` desde `data/interim/crudo_<año>.parquet` hacia `data/interim/homog_<año>.parquet`. No se elimina ni agrega ninguna fila. Las cifras son celdas (un registro tiene varias celdas en los grupos de columnas repetidas).

## 1. Resultado

| Año | Registros crudo | Registros homogenizado | Columnas | MB | Segundos | Verificación |
|---|---|---|---|---|---|---|
| 2019 | 1.151.475 | 1.151.475 | 133 | 52 | 71 | OK |
| 2020 | 781.912 | 781.912 | 133 | 39 | 48 | OK |
| 2021 | 816.909 | 816.909 | 133 | 43 | 50 | OK |
| 2022 | 932.840 | 932.840 | 133 | 47 | 56 | OK |
| 2023 | 1.039.587 | 1.039.587 | 133 | 51 | 64 | OK |
| 2024 | 1.085.813 | 1.085.813 | 133 | 56 | 66 | OK |

**Total:** 5.808.536 registros crudos y 5.808.536 homogenizados. Esquema idéntico en los seis años: **sí**. Columnas: las 129 originales, menos `FECHAPROCEDIMIENTO1`, más `BLOQUE_ID`, `CDM` y las 3 de trazabilidad.

## 2. "Sin dato" unificado

Valores que representaban ausencia de información y pasaron a nulo (además de las celdas vacías).

| Valor original | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| `DESCONOCIDO` | 52.849 | 11.201 | 18.330 | 43.609 | 27.036 | 31.371 | 184.396 |
| `DESCONOCIDA` | — | — | — | — | — | 19.669 | 19.669 |
| `SIN INFORMACIÓN` | 8.307 | 1.893 | — | — | — | — | 10.200 |
| `NO IDENTIFICADA` | 3.882 | 916 | 5 | — | — | — | 4.803 |
| `SERVICIO NO DEFINIDO` | — | — | — | — | 1.386 | — | 1.386 |
| `NO ESPECIFICADO` | 430 | 257 | — | — | — | — | 687 |
| `NO CONSIGNADO` | 489 | 127 | 5 | — | — | — | 621 |
| `NO APLICA` | 7 | 202 | 403 | 7 | — | — | 619 |
| `NO IDENTIFICADO` | 224 | 93 | 5 | — | — | — | 322 |
| `IGNORADO` | 89 | 88 | 77 | — | — | — | 254 |
| `0` | 2 | — | — | 2 | 1 | 1 | 6 |
| `NO RESPONDE` | 1 | — | — | — | — | — | 1 |

Detalle por columna (total de los seis años):

| Columna | Valores convertidos a nulo |
|---|---|
| ID_PACIENTE | `SIN INFORMACIÓN` 10.200; `DESCONOCIDO` 5.621 |
| SEXO | `DESCONOCIDO` 559 |
| FECHA_NACIMIENTO | `DESCONOCIDO` 13; `NO APLICA` 7 |
| ETNIA | `DESCONOCIDO` 19; `NO RESPONDE` 1 |
| PROVINCIA | `DESCONOCIDO` 2.208 |
| COMUNA | `DESCONOCIDO` 1.261 |
| NACIONALIDAD | `DESCONOCIDO` 23.677 |
| PREVISION | `NO IDENTIFICADA` 4.405; `NO CONSIGNADO` 621; `DESCONOCIDO` 142 |
| SERVICIO_SALUD | `DESCONOCIDO` 1.399; `NO APLICA` 612; `IGNORADO` 254 |
| TIPO_PROCEDENCIA | `DESCONOCIDO` 3.111; `NO IDENTIFICADO` 319 |
| TIPO_INGRESO | `NO IDENTIFICADA` 318; `DESCONOCIDO` 145 |
| ESPECIALIDAD_MEDICA | `DESCONOCIDO` 59 |
| TIPO_ACTIVIDAD | `DESCONOCIDO` 18; `NO IDENTIFICADO` 3 |
| FECHA_INGRESO | `DESCONOCIDO` 52 |
| SERVICIOINGRESO | `DESCONOCIDO` 27.844 |
| SERVICIOTRASLADO1-9 | `DESCONOCIDO` 5.398; `SERVICIO NO DEFINIDO` 1.386; `0` 4 |
| SERVICIOALTA | `DESCONOCIDO` 24.589 |
| TIPOALTA | `NO IDENTIFICADA` 80; `DESCONOCIDO` 22 |
| SEXORN1-4 | `DESCONOCIDO` 480 |
| DIAGNOSTICO1-35 | `DESCONOCIDO` 82.466 |
| PROCEDIMIENTO1-30 | `DESCONOCIDO` 940; `0` 2 |
| FECHAINTERV1 | `DESCONOCIDA` 19.669 |
| ESPECIALIDADINTERVENCION | `DESCONOCIDO` 1.409; `NO ESPECIFICADO` 687 |
| IR_29301_COD_GRD | `DESCONOCIDO` 90 |
| IR_29301_PESO | `DESCONOCIDO` 90 |
| IR_29301_SEVERIDAD | `DESCONOCIDO` 90 |
| IR_29301_MORTALIDAD | `DESCONOCIDO` 90 |
| HOSPPROCEDENCIA | `DESCONOCIDO` 2.604 |

## 3. Textos: espacios sobrantes y mayúsculas

Celdas cuyo texto cambió al quitar espacios sobrantes o pasar a mayúsculas.

| Columna | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| ETNIA | 313.518 | 96.019 | 28.492 | — | — | — | 438.029 |
| NACIONALIDAD | 58 | 44 | 31 | 35 | 61 | 87 | 316 |
| ESPECIALIDAD_MEDICA | — | 2.509 | 1.527 | 1.800 | 2.166 | 1.618 | 9.620 |
| SERVICIOINGRESO | — | — | — | — | — | 358 | 358 |
| ESPECIALIDADINTERVENCION | — | 33.886 | 24.951 | 32.957 | 34.314 | 29.877 | 155.985 |
| HOSPPROCEDENCIA | — | 1.137 | 3.180 | 3.244 | 1.043 | — | 8.604 |

## 4. Equivalencias aplicadas

Reglas de `2.1_integracion_homogenizacion/reglas/equivalencias_categorias.csv`.

| Columna | Valor original | Valor homogenizado | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|---|---|
| ETNIA | `NINGUNA` | `NINGUNO` | 11.422 | — | — | — | — | — | 11.422 |
| NACIONALIDAD | `HAITI` | `HAITÍ` | 124 | — | — | — | — | — | 124 |
| NACIONALIDAD | `MEXICO` | `MÉXICO` | 2 | — | — | — | — | — | 2 |
| NACIONALIDAD | `REPUBLICA DOMINICANA` | `REPÚBLICA DOMINICANA` | 1 | — | — | — | — | — | 1 |
| TIPO_INGRESO | `NO PROGRAMADA` | `URGENCIA` | 20 | 5 | — | — | — | — | 25 |
| ESPECIALIDAD_MEDICA | `MEDICINA GENERAL` | `MÉDICO GENERAL` | 26.493 | — | — | — | — | — | 26.493 |
| ESPECIALIDAD_MEDICA | `NEFROLOGÍA` | `NEFROLOGÍA ADULTO` | 10.689 | — | — | — | — | — | 10.689 |
| ESPECIALIDAD_MEDICA | `MEDICINA INTENSIVA` | `MEDICINA INTENSIVA ADULTO` | 7.117 | — | — | — | — | — | 7.117 |
| ESPECIALIDAD_MEDICA | `HEMATOLOGÍA ONCOLÓGICA PEDIÁTRICA` | `HEMATO-ONCOLOGÍA PEDIÁTRICA` | 6.880 | — | — | — | — | — | 6.880 |
| ESPECIALIDAD_MEDICA | `CIRUGÍA Y TRAUMATOLOGÍA BUCOMAXILOFACIAL` | `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | 5.345 | — | — | — | — | — | 5.345 |
| ESPECIALIDAD_MEDICA | `CIRUGÍA CABEZA CUELLO Y PLÁSTICA MAXILO FACIAL` | `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | 5.327 | — | — | — | — | — | 5.327 |
| ESPECIALIDAD_MEDICA | `ENFERMEDADES RESPIRATORIAS` | `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | 4.880 | — | — | — | — | — | 4.880 |
| ESPECIALIDAD_MEDICA | `GASTROENTEROLOGÍA` | `GASTROENTEROLOGÍA ADULTO` | 3.709 | — | — | — | — | — | 3.709 |
| ESPECIALIDAD_MEDICA | `CIRUGÍA COLOPROCTOLÓGICA` | `COLOPROCTOLOGÍA` | 3.307 | — | — | — | — | — | 3.307 |
| ESPECIALIDAD_MEDICA | `MATRONA` | `MATRONAS(ES)` | 3.296 | — | — | — | — | — | 3.296 |
| ESPECIALIDAD_MEDICA | `CIRUGÍA TÓRAX` | `CIRUGÍA DE TÓRAX` | 2.750 | — | — | — | — | — | 2.750 |
| ESPECIALIDAD_MEDICA | `ENFERNEDADES RESPIRATORIAS PEDIÁTRICA` | `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | 2.288 | — | — | — | — | — | 2.288 |
| ESPECIALIDAD_MEDICA | `DERMATOLOGÍA` | `DERMATOLOGÍA Y VENEROLOGÍA` | 1.183 | — | — | — | — | — | 1.183 |
| ESPECIALIDAD_MEDICA | `NEFROLOGÍA PEDIÁTRICA` | `NEFROLOGÍA PEDIÁTRICO` | 1.149 | — | — | — | — | — | 1.149 |
| ESPECIALIDAD_MEDICA | `CUIDADOS INTENSIVOS PEDIÁTRICO` | `MEDICINA INTENSIVA PEDIÁTRICA` | 923 | — | — | — | — | — | 923 |
| ESPECIALIDAD_MEDICA | `ENDOCRINOLOGÍA` | `ENDOCRINOLOGÍA ADULTO` | 421 | — | — | — | — | — | 421 |
| ESPECIALIDAD_MEDICA | `INMUNOLOGÍA` | `INMUNOLOGÍA CLÍNICA` | 223 | — | — | — | — | — | 223 |
| ESPECIALIDAD_MEDICA | `IMPLANTOLOGÍA` | `IMPLANTOLOGIA BUCO MAXILOFACIAL` | 34 | — | — | — | — | — | 34 |
| ESPECIALIDAD_MEDICA | `INFECTOLOGÍA PEDIÁTRICA` | `INFECTOLOGÍA PEDIATRICA` | 2 | — | — | — | — | — | 2 |
| ESPECIALIDADINTERVENCION | `MATRONA` | `MATRONAS(ES)` | 50.771 | — | — | — | — | — | 50.771 |
| ESPECIALIDADINTERVENCION | `MEDICINA GENERAL` | `MÉDICO GENERAL` | 15.791 | — | — | — | — | — | 15.791 |
| ESPECIALIDADINTERVENCION | `CIRUGÍA CABEZA CUELLO Y PLÁSTICA MAXILO FACIAL` | `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | 4.833 | — | — | — | — | — | 4.833 |
| ESPECIALIDADINTERVENCION | `CIRUGÍA Y TRAUMATOLOGÍA BUCOMAXILOFACIAL` | `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | 4.460 | — | — | — | — | — | 4.460 |
| ESPECIALIDADINTERVENCION | `CIRUGÍA TÓRAX` | `CIRUGÍA DE TÓRAX` | 2.366 | — | — | — | — | — | 2.366 |
| ESPECIALIDADINTERVENCION | `CIRUGÍA COLOPROCTOLÓGICA` | `COLOPROCTOLOGÍA` | 2.190 | — | — | — | — | — | 2.190 |
| ESPECIALIDADINTERVENCION | `GASTROENTEROLOGÍA` | `GASTROENTEROLOGÍA ADULTO` | 1.377 | — | — | — | — | — | 1.377 |
| ESPECIALIDADINTERVENCION | `DERMATOLOGÍA` | `DERMATOLOGÍA Y VENEROLOGÍA` | 919 | — | — | — | — | — | 919 |
| ESPECIALIDADINTERVENCION | `NEFROLOGÍA` | `NEFROLOGÍA ADULTO` | 165 | — | — | — | — | — | 165 |
| ESPECIALIDADINTERVENCION | `MEDICINA INTENSIVA` | `MEDICINA INTENSIVA ADULTO` | 76 | — | — | — | — | — | 76 |
| ESPECIALIDADINTERVENCION | `ENFERMEDADES RESPIRATORIAS` | `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | 46 | — | — | — | — | — | 46 |
| ESPECIALIDADINTERVENCION | `ENFERNEDADES RESPIRATORIAS PEDIÁTRICA` | `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | 44 | — | — | — | — | — | 44 |
| ESPECIALIDADINTERVENCION | `IMPLANTOLOGÍA` | `IMPLANTOLOGIA BUCO MAXILOFACIAL` | 35 | — | — | — | — | — | 35 |
| ESPECIALIDADINTERVENCION | `HEMATOLOGÍA ONCOLÓGICA PEDIÁTRICA` | `HEMATO-ONCOLOGÍA PEDIÁTRICA` | 18 | — | — | — | — | — | 18 |
| ESPECIALIDADINTERVENCION | `INMUNOLOGÍA` | `INMUNOLOGÍA CLÍNICA` | 17 | — | — | — | — | — | 17 |
| ESPECIALIDADINTERVENCION | `NEFROLOGÍA PEDIÁTRICA` | `NEFROLOGÍA PEDIÁTRICO` | 5 | — | — | — | — | — | 5 |
| ESPECIALIDADINTERVENCION | `ENDOCRINOLOGÍA` | `ENDOCRINOLOGÍA ADULTO` | 2 | — | — | — | — | — | 2 |
| HOSPPROCEDENCIA | `HOSPITAL CLINICO METROPOLITANO LA FLORIDA DRA. ELOISA DIAZ INZUNZA` | `HOSPITAL CLÍNICO METROPOLITANO LA FLORIDA DRA. ELOISA DÍAZ INZUNZA` | — | — | — | — | — | 732 | 732 |
| HOSPPROCEDENCIA | `COMPLEJO ASISTENCIAL DR. VÍCTOR RÍOS RUIZ (LOS ANGELES)` | `COMPLEJO ASISTENCIAL DR. VÍCTOR RÍOS RUIZ (LOS ÁNGELES)` | — | — | — | — | — | 202 | 202 |
| HOSPPROCEDENCIA | `|114101` | `COMPLEJO HOSPITALARIO DR. SÓTERO DEL RÍO (SANTIAGO, PUENTE ALTO)` | — | — | — | 1 | — | — | 1 |

### Continuidad en `ESPECIALIDAD_MEDICA` después de homogenizar

Celdas por año del valor homogenizado. 2019 incluye tipos de actividad que no existen desde 2020 (bitácora H09), por lo que su volumen puede ser mayor.

| Valor homogenizado | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | 5.327 | 2.553 | 3.227 | 4.015 | 4.982 | 5.287 |
| `CIRUGÍA DE TÓRAX` | 2.750 | 2.114 | 2.804 | 3.540 | 3.989 | 4.284 |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | 5.345 | 2.429 | 2.661 | 3.869 | 5.175 | 6.306 |
| `COLOPROCTOLOGÍA` | 3.307 | 2.326 | 3.568 | 4.448 | 5.831 | 6.663 |
| `DERMATOLOGÍA Y VENEROLOGÍA` | 1.183 | 97 | 106 | 111 | 93 | 156 |
| `ENDOCRINOLOGÍA ADULTO` | 421 | 293 | 277 | 274 | 371 | 253 |
| `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | 4.880 | 6.997 | 8.803 | 3.983 | 4.038 | 4.183 |
| `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | 2.288 | 473 | 583 | 1.797 | 3.257 | 2.186 |
| `GASTROENTEROLOGÍA ADULTO` | 3.709 | 1.372 | 1.314 | 1.863 | 2.276 | 2.288 |
| `HEMATO-ONCOLOGÍA PEDIÁTRICA` | 6.880 | 3.975 | 3.884 | 4.024 | 4.385 | 4.287 |
| `IMPLANTOLOGIA BUCO MAXILOFACIAL` | 34 | 18 | 168 | 339 | 916 | 686 |
| `INFECTOLOGÍA PEDIATRICA` | 2 | 15 | 1 | 2 | 3 | 1 |
| `INMUNOLOGÍA CLÍNICA` | 223 | 248 | 374 | 330 | 299 | 347 |
| `MATRONAS(ES)` | 3.296 | 2.197 | 1.110 | 969 | 1.149 | 948 |
| `MEDICINA INTENSIVA ADULTO` | 7.117 | 11.195 | 15.597 | 12.475 | 12.053 | 13.101 |
| `MEDICINA INTENSIVA PEDIÁTRICA` | 923 | 716 | 729 | 1.268 | 1.437 | 1.853 |
| `MÉDICO GENERAL` | 26.493 | 13.303 | 10.242 | 8.612 | 7.788 | 9.055 |
| `NEFROLOGÍA ADULTO` | 10.689 | 1.096 | 1.601 | 1.758 | 2.439 | 2.541 |
| `NEFROLOGÍA PEDIÁTRICO` | 1.149 | 171 | 138 | 140 | 152 | 135 |

Nombres de `ESPECIALIDAD_MEDICA` que siguen existiendo solo en 2019 (sin equivalente claro; no se modificaron):

| Valor | Celdas en 2019 |
|---|---|
| `ODONTOLOGÍA` | 1.483 |
| `NEUROCIRUGÍA PEDIÁTRICA` | 1.026 |
| `NUTRICIÓN Y DIABETES` | 275 |
| `MEDICINA TRANSFUSIONAL` | 5 |

### Continuidad en `ESPECIALIDADINTERVENCION` después de homogenizar

Celdas por año del valor homogenizado. 2019 incluye tipos de actividad que no existen desde 2020 (bitácora H09), por lo que su volumen puede ser mayor.

| Valor homogenizado | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | 4.833 | 2.509 | 3.115 | 3.995 | 4.950 | 5.717 |
| `CIRUGÍA DE TÓRAX` | 2.366 | 1.746 | 2.205 | 2.333 | 2.539 | 3.006 |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | 4.460 | 2.172 | 2.553 | 3.732 | 4.932 | 6.103 |
| `COLOPROCTOLOGÍA` | 2.190 | 1.875 | 2.307 | 2.487 | 3.557 | 3.745 |
| `DERMATOLOGÍA Y VENEROLOGÍA` | 919 | 74 | 100 | 121 | 113 | 211 |
| `ENDOCRINOLOGÍA ADULTO` | 2 | 7 | 1 | 30 | 8 | 1.674 |
| `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | 46 | 98 | 68 | 114 | 146 | 190 |
| `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | 44 | 18 | 33 | 68 | 51 | 67 |
| `GASTROENTEROLOGÍA ADULTO` | 1.377 | 1.437 | 1.308 | 2.029 | 2.146 | 2.599 |
| `HEMATO-ONCOLOGÍA PEDIÁTRICA` | 18 | 21 | 25 | 8 | 14 | 10 |
| `IMPLANTOLOGIA BUCO MAXILOFACIAL` | 35 | 38 | 180 | 341 | 912 | 676 |
| `INFECTOLOGÍA PEDIATRICA` | — | 4 | 2 | 23 | 27 | 14 |
| `INMUNOLOGÍA CLÍNICA` | 17 | 1 | — | — | 10 | 9 |
| `MATRONAS(ES)` | 50.771 | 33.684 | 24.718 | 32.686 | 34.197 | 29.836 |
| `MEDICINA INTENSIVA ADULTO` | 76 | 65 | 61 | 79 | 81 | 150 |
| `MEDICINA INTENSIVA PEDIÁTRICA` | — | 2 | 4 | — | 1 | 1 |
| `MÉDICO GENERAL` | 15.791 | 6.911 | 5.593 | 10.812 | 16.234 | 17.452 |
| `NEFROLOGÍA ADULTO` | 165 | 425 | 1.068 | 1.365 | 1.563 | 1.829 |
| `NEFROLOGÍA PEDIÁTRICO` | 6 | 7 | 4 | 11 | 16 | 7 |

Nombres de `ESPECIALIDADINTERVENCION` que siguen existiendo solo en 2019 (sin equivalente claro; no se modificaron):

| Valor | Celdas en 2019 |
|---|---|
| `ODONTOLOGÍA` | 762 |
| `NEUROCIRUGÍA PEDIÁTRICA` | 337 |
| `MEDICINA TRANSFUSIONAL` | 6 |
| `FACOERESIS EXTRACAPSULAR CON I` | 1 |

## 5. Fechas convertidas

| Columna | Formato de origen | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|---|
| FECHA_NACIMIENTO | AAAA-MM-DD | 1.151.459 | 781.911 | 816.909 | 932.833 | 1.039.577 | 1.085.810 | 5.808.499 |
| FECHA_INGRESO | AAAA-MM-DD | 1.151.456 | 781.912 | 816.909 | 932.840 | — | 1.085.761 | 4.768.878 |
| FECHA_INGRESO | DD-MM-AAAA | — | — | — | — | 1.039.587 | — | 1.039.587 |
| FECHATRASLADO1-9 | AAAA-MM-DD | 245.422 | 251.952 | 257.577 | 239.233 | — | 258.526 | 1.252.710 |
| FECHATRASLADO1-9 | DD-MM-AAAA | — | — | — | — | 248.298 | — | 248.298 |
| FECHAALTA | AAAA-MM-DD | 1.151.457 | 781.912 | 816.909 | 932.840 | — | 1.085.813 | 4.768.931 |
| FECHAALTA | DD-MM-AAAA | — | — | — | — | 1.039.587 | — | 1.039.587 |
| FECHAINTERV1 | AAAA-MM-DD | 589.190 | 396.057 | 406.876 | 465.237 | — | 528.824 | 2.386.184 |
| FECHAINTERV1 | DD-MM-AAAA | — | — | — | — | 528.813 | — | 528.813 |

## 6. Números

| Columna | Cambio | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|---|
| IR_29301_PESO | Coma decimal convertida a punto | 1.150.907 | 781.721 | 816.544 | 932.090 | 1.037.875 | 1.084.323 | 5.803.460 |
| IR_29301_PESO | Cero inicial agregado (,3045 -> 0.3045) | — | 548.775 | 550.246 | — | — | — | 1.099.021 |

## 7. Valores que no se pudieron convertir

Quedaron como "sin dato". Se muestra solo su formato (9 = dígito, A = letra), no el valor.

| Columna | Formato del valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|---|
| FECHA_NACIMIENTO | `--99` | 15 | — | — | — | — | — | 15 |
| FECHA_NACIMIENTO | `--9` | 1 | — | — | — | — | — | 1 |
| FECHA_NACIMIENTO | `--` | — | 1 | — | — | — | — | 1 |
| FECHA_INGRESO | `--9` | 18 | — | — | — | — | — | 18 |
| FECHA_INGRESO | `--` | 1 | — | — | — | — | — | 1 |
| FECHATRASLADO1-9 | `-99-99` | 26 | — | — | — | — | — | 26 |
| FECHATRASLADO1-9 | `--99` | 2 | — | — | — | — | — | 2 |
| FECHATRASLADO1-9 | `9999-99-99` | — | 1 | — | — | — | — | 1 |
| USOSPABELLON | `99999999-9` | 8 | — | — | — | — | — | 8 |
| USOSPABELLON | `99999999-A` | 5 | — | — | — | — | — | 5 |
| USOSPABELLON | `9999` | 2 | — | — | — | — | — | 2 |
| USOSPABELLON | `9999999-9` | 2 | — | — | — | — | — | 2 |
| USOSPABELLON | `99999999` | 2 | — | — | — | — | — | 2 |
| USOSPABELLON | `9.` | 2 | — | — | — | — | — | 2 |
| USOSPABELLON | `A?AA` | 1 | — | — | — | — | — | 1 |
| USOSPABELLON | `A?A¿9` | 1 | — | — | — | — | — | 1 |
| USOSPABELLON | `99/99/9999` | 1 | — | — | — | — | — | 1 |
| USOSPABELLON | `999999999` | 1 | — | — | — | — | — | 1 |
| USOSPABELLON | `9+` | 1 | — | — | — | — | — | 1 |

## 8. Columna eliminada

| Columna | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total de celdas no vacías descartadas |
|---|---|---|---|---|---|---|---|
| FECHAPROCEDIMIENTO1 | 9 | — | — | — | — | — | 9 |

## 9. Alertas de coherencia de fechas

Se informan para la actividad 2.2; en este paso no se corrigen ni se excluyen registros.

| Alerta | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Sin fecha de ingreso | 19 | — | — | — | — | 52 | 71 |
| Sin fecha de alta | 18 | — | — | — | — | — | 18 |
| Sin fecha de nacimiento | 16 | 1 | — | 7 | 10 | 3 | 37 |
| Alta anterior al ingreso | 1 | 10 | — | 1 | — | — | 12 |
| Nacimiento posterior al ingreso | 1 | — | — | — | — | — | 1 |
| Edad al ingreso mayor de 110 años | 12 | 7 | 7 | — | — | — | 26 |
| Alta fuera del año del archivo | — | — | — | — | — | — | 0 |
| Ingreso anterior al año previo al archivo | 45 | 53 | 56 | 47 | — | — | 201 |

## 10. Verificaciones

- Registros conservados y en el mismo orden en los seis años: **sí**.
- Celdas con forma de RUT en la base homogenizada: **0**.
- Valor máximo de `USOSPABELLON` por año: 2019: 999, 2020: 3, 2021: 8, 2022: 8, 2023: 8, 2024: 8.
- Variantes de un mismo valor que difieren solo en tildes: **0**.

Valores distintos por columna de texto, antes y después (seis años):

| Columna | Antes | Después |
|---|---|---|
| SEXO | 3 | 2 |
| ETNIA | 15 | 11 |
| PROVINCIA | 58 | 57 |
| COMUNA | 347 | 346 |
| NACIONALIDAD | 218 | 214 |
| PREVISION | 15 | 12 |
| SERVICIO_SALUD | 32 | 29 |
| TIPO_PROCEDENCIA | 20 | 18 |
| TIPO_INGRESO | 6 | 3 |
| ESPECIALIDAD_MEDICA | 104 | 84 |
| TIPO_ACTIVIDAD | 6 | 4 |
| SERVICIOINGRESO | 93 | 92 |
| SERVICIOTRASLADO1-9 | 112 | 109 |
| SERVICIOALTA | 90 | 89 |
| TIPOALTA | 12 | 10 |
| CONDICIONDEALTANEONATO1-4 | 2 | 2 |
| SEXORN1-4 | 3 | 2 |
| ESPECIALIDADINTERVENCION | 104 | 85 |
| HOSPPROCEDENCIA | 543 | 518 |
