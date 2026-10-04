# Perfil de columnas por año (Paso 3.0)

Generado por `1.2_exploracion_calidad/scripts/04_perfil_columnas.py` sobre `data/interim/crudo_<año>.parquet`. Las columnas repetidas se agrupan (p. ej. `DIAGNOSTICO1-35`); en ellas el % vacío se calcula sobre todas las celdas del grupo. Registros por año: 2019: 1.151.475, 2020: 781.912, 2021: 816.909, 2022: 932.840, 2023: 1.039.587, 2024: 1.085.813.

## 1. Resumen por columna

Tipo aparente según el contenido. "Sin dato" explícito: valores como `DESCONOCIDO` que representan ausencia de información.

| Columna | Tipo | % vacío 2019·20·21·22·23·24 | "Sin dato" explícito (6 años) | Distintos (mín–máx) | Alertas |
|---|---|---|---|---|---|
| COD_HOSPITAL | código | 0·0·0·0·0·0 | — | 65–72 | — |
| ID_PACIENTE (CIP_ENCRIPTADO / ID_BENEFICIARIO) | identificador | 0·0·0·0·0·0 | `SIN INFORMACIÓN` 10.200; `DESCONOCIDO` 5.621 | 639.102–876.183 | — |
| SEXO | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 559 | 2–2 | — |
| FECHA_NACIMIENTO | fecha | 0·0·0·0·0·0 | `DESCONOCIDO` 13; `NO APLICA` 7 | 35.793–36.250 | — |
| ETNIA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 19; `NO RESPONDE` 1 | 10–12 | espacios sobrantes (438.029) |
| PROVINCIA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 2.208 | 56–57 | — |
| COMUNA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 1.261 | 343–346 | — |
| NACIONALIDAD | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 23.677 | 121–135 | espacios sobrantes (316) |
| PREVISION | categoría | 0·0·0·0·0·0 | `NO IDENTIFICADA` 4.405; `NO CONSIGNADO` 621; `DESCONOCIDO` 142 | 12–12 | — |
| SERVICIO_SALUD | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 1.399; `NO APLICA` 612; `IGNORADO` 254 | 29–29 | — |
| TIPO_PROCEDENCIA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 3.111; `NO IDENTIFICADO` 319 | 13–16 | — |
| TIPO_INGRESO | categoría | 0·0·0·0·0·0 | `NO IDENTIFICADA` 318; `DESCONOCIDO` 145 | 3–4 | — |
| ESPECIALIDAD_MEDICA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 59 | 58–73 | espacios sobrantes (9.620) |
| TIPO_ACTIVIDAD | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 18; `NO IDENTIFICADO` 3 | 2–4 | — |
| FECHA_INGRESO | fecha | 0·0·0·0·0·0 | `DESCONOCIDO` 52 | 627–670 | **formato distinto entre años** |
| SERVICIOINGRESO | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 27.844 | 86–88 | minúsculas (358) |
| FECHATRASLADO1-9 | fecha | 98·96·96·97·97·97 | — | 682–764 | **formato distinto entre años** |
| SERVICIOTRASLADO1-9 | categoría | 98·96·96·97·97·97 | `DESCONOCIDO` 5.398 | 83–100 | — |
| FECHAALTA | fecha | 0·0·0·0·0·0 | — | 365–366 | **formato distinto entre años** |
| SERVICIOALTA | categoría | 0·0·0·0·0·0 | `DESCONOCIDO` 24.589 | 85–87 | — |
| TIPOALTA | categoría | 0·0·0·0·0·0 | `NO IDENTIFICADA` 80; `DESCONOCIDO` 22 | 10–10 | — |
| CONDICIONDEALTANEONATO1-4 | categoría | 97·100·100·100·100·100 | — | 0–2 | — |
| PESORN1-4 | número | 97·96·96·96·97·97 | — | 3.066–3.532 | — |
| SEXORN1-4 | categoría | 97·96·97·97·97·98 | `DESCONOCIDO` 480 | 2–2 | — |
| RN1-4ESTADO | número | 0·61·97·97·97·98 | — | 11–13 | — |
| DIAGNOSTICO1-35 | código | 87·85·84·85·84·83 | `DESCONOCIDO` 82.466 | 12.865–13.675 | — |
| PROCEDIMIENTO1-30 | código | 78·72·70·72·73·73 | `DESCONOCIDO` 940 | 3.550–3.623 | — |
| MEDICOINTERV1_ENCRIPTADO | identificador | 48·48·47·42·42·43 | — | 9.476–11.164 | — |
| FECHAPROCEDIMIENTO1 | fecha | 100·100·100·100·100·100 | — | 0–9 | — |
| FECHAINTERV1 | fecha | 49·49·50·50·49·49 | `DESCONOCIDA` 19.669 | 566–675 | **formato distinto entre años** |
| ESPECIALIDADINTERVENCION | categoría | 47·47·47·43·42·43 | `DESCONOCIDO` 1.409 | 61–72 | espacios sobrantes (155.985) |
| MEDICOALTA_ENCRIPTADO | identificador | 0·0·0·0·0·0 | — | 14.104–17.743 | — |
| USOSPABELLON | número | 44·100·43·39·39·40 | — | 3–62 | minúsculas (1), texto dañado (2) |
| IR_29301_COD_GRD | código | 0·0·0·0·0·0 | `DESCONOCIDO` 90 | 984–1.052 | — |
| IR_29301_PESO | número | 0·0·0·0·0·0 | `DESCONOCIDO` 90 | 952–1.010 | **formato distinto entre años** |
| IR_29301_SEVERIDAD | número | 0·0·0·0·0·0 | `DESCONOCIDO` 90 | 4–4 | — |
| IR_29301_MORTALIDAD | número | 0·0·0·0·0·0 | `DESCONOCIDO` 90 | 4–4 | — |
| HOSPPROCEDENCIA | categoría | 89·86·86·87·87·91 | `DESCONOCIDO` 2.604 | 72–390 | espacios sobrantes (8.604) |

## 2. Formatos por año

Formato más frecuente de los valores (9 = dígito, A = letra). En fechas se muestra el formato exacto; en números y códigos, el resumido (`9,9` = decimal con coma; `,9` = decimal sin cero inicial).

| Columna | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| COD_HOSPITAL | `9` | `9` | `9` | `9` | `9` | `9` |
| ID_PACIENTE (CIP_ENCRIPTADO / ID_BENEFICIARIO) | `9` | `9` | `9` | `9` | `9` | `9` |
| FECHA_NACIMIENTO | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` |
| FECHA_INGRESO | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `99-99-9999` | `9999-99-99` |
| FECHATRASLADO1-9 | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `99-99-9999` | `9999-99-99` |
| FECHAALTA | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `99-99-9999` | `9999-99-99` |
| PESORN1-4 | `9` | `9` | `9` | `9` | `9` | `9` |
| RN1-4ESTADO | `9` | `9` | `9` | `9` | `9` | `9` |
| DIAGNOSTICO1-35 | `A9.9` 89.5% / `A9` 10.5% | `A9.9` 89.7% / `A9` 10.3% | `A9.9` 89.4% / `A9` 10.6% | `A9.9` 89.8% / `A9` 10.2% | `A9.9` 89.8% / `A9` 10.2% | `A9.9` 89.6% / `A9` 10.4% |
| PROCEDIMIENTO1-30 | `9.9` | `9.9` | `9.9` | `9.9` | `9.9` | `9.9` |
| MEDICOINTERV1_ENCRIPTADO | `9` | `9` | `9` | `9` | `9` | `9` |
| FECHAPROCEDIMIENTO1 | `99999999-A` 33.3% / `9999999-9` 22.2% / `99999999-9` 22.2% | (sin datos) | (sin datos) | (sin datos) | (sin datos) | (sin datos) |
| FECHAINTERV1 | `9999-99-99` | `9999-99-99` | `9999-99-99` | `9999-99-99` | `99-99-9999` | `9999-99-99` |
| MEDICOALTA_ENCRIPTADO | `9` | `9` | `9` | `9` | `9` | `9` |
| USOSPABELLON | `9` | `9` | `9` | `9` | `9` | `9` |
| IR_29301_COD_GRD | `9` | `9` | `9` | `9` | `9` | `9` |
| IR_29301_PESO | `9,9` | `,9` 70.2% / `9,9` 29.8% | `,9` 67.4% / `9,9` 32.6% | `9,9` 99.9% / `9` 0.1% | `9,9` 99.8% / `9` 0.2% | `9,9` 99.9% / `9` 0.1% |
| IR_29301_SEVERIDAD | `9` | `9` | `9` | `9` | `9` | `9` |
| IR_29301_MORTALIDAD | `9` | `9` | `9` | `9` | `9` | `9` |

## 3. Categorías que cambian entre años

### ETNIA

15 valores distintos en total.

**Variantes de un mismo valor** (difieren solo en tildes, espacios o mayúsculas):

- `OTRO` (1.929.130) · `OTRO ` (438.029)

**Valores que no aparecen en todos los años** (6):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `NINGUNO` | 805.540 | 668.295 | 769.595 | — | — | 1.058.981 |
| `OTRO` | — | — | — | 912.576 | 1.016.554 | — |
| `OTRO ` | 313.518 | 96.019 | 28.492 | — | — | — |
| `NINGUNA` | 11.422 | — | — | — | — | — |
| `DESCONOCIDO` | 19 | — | — | — | — | — |
| `NO RESPONDE` | 1 | — | — | — | — | — |

### PROVINCIA

58 valores distintos en total.

**Valores que no aparecen en todos los años** (1):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `ÑUBLE` | 8.808 | 2.432 | — | — | — | — |

### COMUNA

347 valores distintos en total.

**Valores que no aparecen en todos los años** (6):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `RÍO VERDE` | 9 | 2 | 2 | 4 | 1 | — |
| `GENERAL LAGOS` | 1 | 3 | 1 | — | 8 | 4 |
| `PUTRE` | 3 | — | 2 | 2 | 5 | 4 |
| `TORRES DEL PAINE` | 7 | 1 | 1 | — | 5 | — |
| `CAMARONES` | — | 1 | 2 | — | 2 | 9 |
| `TIMAUKEL` | 1 | 2 | 2 | 1 | 2 | — |

### NACIONALIDAD

218 valores distintos en total.

**Variantes de un mismo valor** (difieren solo en tildes, espacios o mayúsculas):

- `HAITI` (124) · `HAITÍ` (45.843)
- `REPUBLICA DOMINICANA` (1) · `REPÚBLICA DOMINICANA` (4.227)
- `MEXICO` (2) · `MÉXICO` (350)

**Valores que no aparecen en todos los años** (155):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `DESCONOCIDO` | 20.636 | 3.041 | — | — | — | — |
| `EUROPA` | — | 158 | 192 | 298 | 228 | 175 |
| `BULGARIA` | — | 39 | 58 | 89 | 49 | 143 |
| `AMÉRICA` | — | — | 5 | 55 | 52 | 24 |
| `HAITI` | 124 | — | — | — | — | — |
| `VENEZUELA` | 81 | — | — | — | — | — |
| `AMÉRICA DEL SUR` | — | 9 | 20 | 35 | 7 | 8 |
| `ÁFRICA` | — | 2 | 5 | 7 | 16 | 11 |
| `SWAZILANDIA` | 17 | 13 | — | — | 2 | — |
| `POLONIA` | 9 | 4 | 6 | — | 2 | 2 |
| `TAIWÁN (PROVINCIA DE CHINA)` | 6 | 3 | — | 4 | 2 | 8 |
| `ARGELIA` | 4 | 5 | 3 | 8 | — | 2 |
| `ISRAEL` | 7 | 4 | — | 5 | 4 | 1 |
| `COREA DEL SUR (REPÚBLICA DE)` | 5 | 2 | 4 | — | 4 | 4 |
| `NUEVA ZELANDIA` | 3 | 4 | — | 1 | 10 | — |
| `IRÁN (REPÚBLICA ISLÁMICA DE)` | 1 | — | 3 | 8 | 4 | 2 |
| `AUSTRIA` | 6 | 3 | 6 | 1 | 1 | — |
| `DINAMARCA` | 3 | — | 3 | 2 | 5 | 4 |
| `CHIPRE` | 8 | 3 | — | 3 | — | 2 |
| `MAURICIO` | 5 | 2 | 4 | 3 | — | 1 |
| `MARRUECOS` | 2 | 2 | — | 2 | 5 | 4 |
| `PUERTO RICO` | — | 1 | — | 3 | 2 | 9 |
| `HUNGRÍA` | 7 | 4 | 3 | — | — | — |
| `ANTILLAS HOLANDESAS` | 2 | — | 4 | 2 | 4 | 2 |
| `ISLAS MALVINAS` | 9 | — | — | 2 | 1 | 1 |
| `EGIPTO` | 3 | 1 | 4 | — | 5 | — |
| `GRECIA` | 6 | 1 | 2 | 2 | — | 1 |
| `ARABIA SAUDITA` | 1 | — | 1 | 3 | 1 | 6 |
| `TAILANDIA` | 4 | — | 1 | 4 | — | 2 |
| `SRI LANKA` | 10 | — | — | 1 | — | — |
| `VANUATU` | 1 | 1 | 1 | 2 | — | 6 |
| `VIETNAM` | 3 | 4 | — | 1 | — | 2 |
| `ANGOLA` | 1 | 4 | 4 | 1 | — | — |
| `BARBADOS` | — | 1 | 1 | 2 | 2 | 4 |
| `NÍGER` | — | 2 | 1 | 4 | 3 | — |
| `TERRITORIO BRITÁNICO DEL OCÉANO ÍNDICO` | — | — | 1 | 2 | 6 | 1 |
| `KENYA` | 3 | 2 | 1 | 1 | — | 2 |
| `MARTINIQUE` | 7 | 2 | — | — | — | — |
| `GEORGIA DEL SUR Y LAS ISLAS SANDWICH DEL SUR` | 7 | 2 | — | — | — | — |
| `JORDANIA` | 1 | 4 | 1 | — | 3 | — |
| … y 115 más |  |  |  |  |  |  |

### PREVISION

15 valores distintos en total.

**Valores que no aparecen en todos los años** (3):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `NO IDENTIFICADA` | 3.525 | 876 | 4 | — | — | — |
| `NO CONSIGNADO` | 489 | 127 | 5 | — | — | — |
| `DESCONOCIDO` | 20 | — | — | 59 | 24 | 39 |

### SERVICIO_SALUD

32 valores distintos en total.

**Valores que no aparecen en todos los años** (3):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `DESCONOCIDO` | 3 | 2 | — | 60 | 741 | 593 |
| `NO APLICA` | 7 | 202 | 403 | — | — | — |
| `IGNORADO` | 89 | 88 | 77 | — | — | — |

### TIPO_PROCEDENCIA

20 valores distintos en total.

**Valores que no aparecen en todos los años** (6):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `PLAN DE RESOLUCIÓN LE` | — | — | — | 31.745 | 16.937 | 57 |
| `ESTRATEGIA CRR` | — | — | — | 3.236 | 10.423 | 22.826 |
| `CARDIOCIRUGÍA PAGO GRD` | — | — | — | 1.474 | 3.264 | 3.013 |
| `NO IDENTIFICADO` | 221 | 93 | 5 | — | — | — |
| `LISTA DE ESPERA` | — | 5 | — | — | — | — |
| `UGCC` | — | 1 | — | — | — | — |

### TIPO_INGRESO

6 valores distintos en total.

**Valores que no aparecen en todos los años** (3):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `NO IDENTIFICADA` | 299 | 18 | 1 | — | — | — |
| `DESCONOCIDO` | 14 | — | — | 33 | 55 | 43 |
| `NO PROGRAMADA` | 20 | 5 | — | — | — | — |

### ESPECIALIDAD_MEDICA

104 valores distintos en total.

**Variantes de un mismo valor** (difieren solo en tildes, espacios o mayúsculas):

- `INFECTOLOGÍA PEDIATRICA` (22) · `INFECTOLOGÍA PEDIÁTRICA` (2)

**Valores que no aparecen en todos los años** (69):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `MEDICINA INTENSIVA ADULTO` | — | 11.195 | 15.597 | 12.475 | 12.053 | 13.101 |
| `MÉDICO GENERAL` | — | 13.303 | 10.242 | 8.612 | 7.788 | 9.055 |
| `CIRUGÍA DIGESTIVA` | — | 1.393 | 5.278 | 7.901 | 9.698 | 8.701 |
| `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | — | 6.997 | 8.803 | 3.983 | 4.038 | 4.183 |
| `MEDICINA GENERAL` | 26.493 | — | — | — | — | — |
| `COLOPROCTOLOGÍA` | — | 2.326 | 3.568 | 4.448 | 5.831 | 6.663 |
| `HEMATO-ONCOLOGÍA PEDIÁTRICA` | — | 3.975 | 3.884 | 4.024 | 4.385 | 4.287 |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | — | 2.429 | 2.661 | 3.869 | 5.175 | 6.306 |
| `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | — | 2.553 | 3.227 | 4.015 | 4.982 | 5.287 |
| `CIRUGÍA DE TÓRAX` | — | 2.114 | 2.804 | 3.540 | 3.989 | 4.284 |
| `NEFROLOGÍA` | 10.689 | — | — | — | — | — |
| `NEFROLOGÍA ADULTO` | — | 1.096 | 1.601 | 1.758 | 2.439 | 2.541 |
| `GASTROENTEROLOGÍA ADULTO` | — | 1.372 | 1.314 | 1.863 | 2.276 | 2.288 |
| `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | — | 473 | 583 | 1.797 | 3.257 | 2.186 |
| `MEDICINA INTENSIVA` | 7.117 | — | — | — | — | — |
| `HEMATOLOGÍA ONCOLÓGICA PEDIÁTRICA` | 6.880 | — | — | — | — | — |
| `MATRONAS(ES)  ` | — | 2.197 | 1.110 | 969 | 1.149 | 948 |
| `MEDICINA INTENSIVA PEDIÁTRICA` | — | 716 | 729 | 1.268 | 1.437 | 1.853 |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCOMAXILOFACIAL` | 5.345 | — | — | — | — | — |
| `CIRUGÍA CABEZA CUELLO Y PLÁSTICA MAXILO FACIAL` | 5.327 | — | — | — | — | — |
| `ENFERMEDADES RESPIRATORIAS` | 4.880 | — | — | — | — | — |
| `NEURORRADIOLOGIA` | — | 249 | 545 | 929 | 998 | 1.114 |
| `GASTROENTEROLOGÍA` | 3.709 | — | — | — | — | — |
| `CIRUGÍA COLOPROCTOLÓGICA` | 3.307 | — | — | — | — | — |
| `MATRONA` | 3.296 | — | — | — | — | — |
| `CIRUGÍA TÓRAX` | 2.750 | — | — | — | — | — |
| `ENFERNEDADES RESPIRATORIAS PEDIÁTRICA` | 2.288 | — | — | — | — | — |
| `IMPLANTOLOGIA BUCO MAXILOFACIAL` | — | 18 | 168 | 339 | 916 | 686 |
| `GINECOLOGÍA ONCOLÓGICA ` | — | 107 | 180 | 543 | 652 | 332 |
| `INMUNOLOGÍA CLÍNICA` | — | 248 | 374 | 330 | 299 | 347 |
| `ODONTOLOGÍA` | 1.483 | — | — | — | — | — |
| `ENDOCRINOLOGÍA ADULTO` | — | 293 | 277 | 274 | 371 | 253 |
| `DIABETOLOGÍA ` | — | 202 | 237 | 288 | 362 | 336 |
| `DERMATOLOGÍA` | 1.183 | — | — | — | — | — |
| `NEFROLOGÍA PEDIÁTRICA` | 1.149 | — | — | — | — | — |
| `CIRUJANO DENTISTA` | — | 169 | 166 | 260 | 269 | 264 |
| `NEUROCIRUGÍA PEDIÁTRICA` | 1.026 | — | — | — | — | — |
| `CUIDADOS INTENSIVOS PEDIÁTRICO` | 923 | — | — | — | — | — |
| `NEFROLOGÍA PEDIÁTRICO` | — | 171 | 138 | 140 | 152 | 135 |
| `DERMATOLOGÍA Y VENEROLOGÍA` | — | 97 | 106 | 111 | 93 | 156 |
| … y 29 más |  |  |  |  |  |  |

### TIPO_ACTIVIDAD

6 valores distintos en total.

**Valores que no aparecen en todos los años** (4):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `HOSPITALIZACIÓN EN URGENCIA` | 62.551 | — | — | — | — | — |
| `HOSPITALIZACIÓN DIURNA` | 55.328 | — | — | — | — | — |
| `DESCONOCIDO` | 18 | — | — | — | — | — |
| `NO IDENTIFICADO` | 3 | — | — | — | — | — |

### SERVICIOINGRESO

93 valores distintos en total.

**Valores que no aparecen en todos los años** (8):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `AREA MEDICO-QUIRURGICOPEDIATRICA CUIDADOS BASICOS` | — | 160 | 1.034 | 2.440 | 1.816 | 2.474 |
| `Área de Hospitalización de Cuidados Intensivos en Psiquiatría Adulto` | — | — | — | — | — | 292 |
| `Área de Hospitalización de cuidados intensivos en Psiquiatría Infante Adolescente` | — | — | — | — | — | 66 |
| `CIRUGÍA TÓRAX` | 1 | 3 | 5 | 4 | 1 | — |
| `PSIQUIATRÍA FORENSE ALTA COMPLEJIDAD` | — | — | — | — | 1 | 9 |
| `PSIQUIATRÍA CRÓNICO` | 2 | 2 | — | — | — | — |
| `CARDIOCIRUGÍA (INFANTIL)` | 1 | 1 | 1 | — | — | — |
| `OTRA` | 1 | — | — | — | — | — |

### SERVICIOTRASLADO1-9

112 valores distintos en total.

**Valores que no aparecen en todos los años** (32):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `AREA MEDICO-QUIRURGICOPEDIATRICA CUIDADOS MEDIOS` | — | 154 | 237 | 246 | 764 | 695 |
| `AREA MQ PEDIATRIA` | — | 1 | 102 | 512 | 552 | 473 |
| `SERVICIO NO DEFINIDO` | — | — | — | — | 1.386 | — |
| `AREA MEDICO-QUIRURGICOPEDIATRICA CUIDADOS BASICOS` | — | 112 | 208 | 388 | 161 | 172 |
| `408` | — | — | 146 | 362 | — | 368 |
| `ÁREA MÉDICA PEDIÁTRICA CUIDADOS MEDIOS` | — | — | — | — | 745 | — |
| `411` | — | — | 29 | 40 | — | 34 |
| `428` | — | — | — | 5 | — | 82 |
| `ÁREA CUIDADOS INTENSIVOS PEDIÁTRICOS` | — | — | — | — | 64 | — |
| `421` | — | — | 8 | 11 | — | 19 |
| `414` | — | — | 5 | 4 | — | 19 |
| `429` | — | — | — | — | — | 28 |
| `405` | — | — | 5 | 8 | — | 9 |
| `HOSPITAL DE DÍA QUIRÚRGICO` | — | 1 | 5 | 2 | 1 | 6 |
| `ÁREA NEONATOLOGÍA CUIDADOS INTENSIVOS` | — | — | — | — | 15 | — |
| `HOSPITA DE DÍA ONCOLÓGICO` | 1 | 1 | — | 1 | 2 | 9 |
| `412` | — | — | 4 | 3 | — | 5 |
| `PSIQUIATRÍA CRÓNICO` | 10 | — | — | 1 | — | — |
| `ÁREA PSIQUIATRÍA INFANTO-ADOLESCENTE CORTA ESTADÍA` | — | — | — | — | 9 | — |
| `PSIQUIATRÍA FORENSE ALTA COMPLEJIDAD` | 1 | — | — | — | — | 5 |
| `418` | — | — | 2 | 1 | — | 3 |
| `HOSPITAL DE DÍA MÉDICO` | — | 1 | 3 | — | — | 1 |
| `CIRUGÍA TÓRAX` | — | 2 | — | — | — | 2 |
| `0` | — | — | — | 2 | 1 | 1 |
| `ÁREA CUIDADOS INTERMEDIOS PEDIÁTRICOS` | — | — | — | — | 4 | — |
| `ÁREA PSIQUIATRÍA ADULTO CORTA ESTADÍA` | — | — | — | — | 3 | — |
| `ÁREA SOCIOSANITARIA ADULTO` | — | — | — | — | 3 | — |
| `CARDIOCIRUGÍA (INFANTIL)` | 2 | — | — | — | — | — |
| `420` | — | — | — | 1 | — | 1 |
| `ÁREA CUIDADOS INTENSIVOS ADULTOS` | — | — | — | — | 2 | — |
| `427` | — | — | — | — | — | 1 |
| `330` | — | — | — | — | — | 1 |

### SERVICIOALTA

90 valores distintos en total.

**Valores que no aparecen en todos los años** (5):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `AREA MEDICO-QUIRURGICOPEDIATRICA CUIDADOS BASICOS` | — | 198 | 1.136 | 2.746 | 1.906 | 2.560 |
| `PSIQUIATRÍA FORENSE ALTA COMPLEJIDAD` | — | — | — | — | 1 | 13 |
| `CIRUGÍA TÓRAX` | — | 1 | — | — | — | 1 |
| `CARDIOCIRUGÍA (INFANTIL)` | 1 | — | — | — | — | — |
| `PSIQUIATRÍA MEDIANA ESTADÍA` | — | 1 | — | — | — | — |

### TIPOALTA

12 valores distintos en total.

**Valores que no aparecen en todos los años** (2):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `NO IDENTIFICADA` | 58 | 22 | — | — | — | — |
| `DESCONOCIDO` | 21 | 1 | — | — | — | — |

### CONDICIONDEALTANEONATO1-4

2 valores distintos en total.

**Valores que no aparecen en todos los años** (2):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `VIVO` | 129.691 | 1 | — | — | — | — |
| `FALLECIDO` | 830 | — | — | — | — | — |

### ESPECIALIDADINTERVENCION

104 valores distintos en total.

**Valores que no aparecen en todos los años** (72):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `MATRONAS(ES)  ` | — | 33.684 | 24.718 | 32.686 | 34.197 | 29.836 |
| `MÉDICO GENERAL` | — | 6.911 | 5.593 | 10.812 | 16.234 | 17.452 |
| `MATRONA` | 50.771 | — | — | — | — | — |
| `CIRUGÍA DE CABEZA, CUELLO Y MAXILOFACIAL` | — | 2.509 | 3.115 | 3.995 | 4.950 | 5.717 |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL` | — | 2.172 | 2.553 | 3.732 | 4.932 | 6.103 |
| `MEDICINA GENERAL` | 15.791 | — | — | — | — | — |
| `COLOPROCTOLOGÍA` | — | 1.875 | 2.307 | 2.487 | 3.557 | 3.745 |
| `CIRUGÍA DE TÓRAX` | — | 1.746 | 2.205 | 2.333 | 2.539 | 3.006 |
| `GASTROENTEROLOGÍA ADULTO` | — | 1.437 | 1.308 | 2.029 | 2.146 | 2.599 |
| `CIRUGÍA DIGESTIVA` | — | 1.068 | 1.822 | 1.568 | 2.096 | 1.686 |
| `NEFROLOGÍA ADULTO` | — | 425 | 1.068 | 1.365 | 1.563 | 1.829 |
| `CIRUGÍA CABEZA CUELLO Y PLÁSTICA MAXILO FACIAL` | 4.833 | — | — | — | — | — |
| `CIRUGÍA Y TRAUMATOLOGÍA BUCOMAXILOFACIAL` | 4.460 | — | — | — | — | — |
| `NEURORRADIOLOGIA` | — | 259 | 568 | 967 | 1.022 | 1.214 |
| `CIRUGÍA TÓRAX` | 2.366 | — | — | — | — | — |
| `CIRUGÍA COLOPROCTOLÓGICA` | 2.190 | — | — | — | — | — |
| `IMPLANTOLOGIA BUCO MAXILOFACIAL` | — | 38 | 180 | 341 | 912 | 676 |
| `ENDOCRINOLOGÍA ADULTO` | — | 7 | 1 | 30 | 8 | 1.674 |
| `DESCONOCIDO` | 1.344 | 65 | — | — | — | — |
| `GASTROENTEROLOGÍA` | 1.377 | — | — | — | — | — |
| `CIRUJANO DENTISTA` | — | 174 | 169 | 251 | 250 | 200 |
| `DERMATOLOGÍA` | 919 | — | — | — | — | — |
| `GINECOLOGÍA ONCOLÓGICA ` | — | 124 | 231 | 265 | 109 | 35 |
| `ODONTOLOGÍA` | 762 | — | — | — | — | — |
| `NO ESPECIFICADO` | 430 | 257 | — | — | — | — |
| `DERMATOLOGÍA Y VENEROLOGÍA` | — | 74 | 100 | 121 | 113 | 211 |
| `ENFERMEDADES RESPIRATORIAS DEL ADULTO (BRONCOPULMONAR)` | — | 98 | 68 | 114 | 146 | 190 |
| `MEDICINA INTENSIVA ADULTO` | — | 65 | 61 | 79 | 81 | 150 |
| `NEUROCIRUGÍA PEDIÁTRICA` | 337 | — | — | — | — | — |
| `ENFERMEDADES RESPIRATORIAS PEDIÁTRICAS (BRONCOPULMONAR PEDIATRICO)` | — | 18 | 33 | 68 | 51 | 67 |
| `ORTODONCIA Y ORTOPEDIA DENTO MAXILOFACIAL` | — | 45 | 37 | 92 | 30 | 5 |
| `NEFROLOGÍA` | 165 | — | — | — | — | — |
| `PERIODONCIA` | — | 3 | 3 | 4 | 65 | 82 |
| `REHABILITACIÓN ORAL` | — | — | 6 | 42 | 44 | 64 |
| `DIABETOLOGÍA ` | — | 76 | — | 1 | 5 | 1 |
| `HEMATO-ONCOLOGÍA PEDIÁTRICA` | — | 21 | 25 | 8 | 14 | 10 |
| `MEDICINA INTENSIVA` | 76 | — | — | — | — | — |
| `INFECTOLOGÍA PEDIATRICA` | — | 4 | 2 | 23 | 27 | 14 |
| `MICROBIOLOGIA CLINICA` | — | 32 | 9 | 8 | 11 | 6 |
| `PATOLOGÍA ORAL Y MAXILOFACIAL` | — | 8 | 3 | 7 | 13 | 25 |
| … y 32 más |  |  |  |  |  |  |

### HOSPPROCEDENCIA

543 valores distintos en total.

**Variantes de un mismo valor** (difieren solo en tildes, espacios o mayúsculas):

- `COMPLEJO ASISTENCIAL DR. VÍCTOR RÍOS RUIZ (LOS ANGELES)` (202) · `COMPLEJO ASISTENCIAL DR. VÍCTOR RÍOS RUIZ (LOS ÁNGELES)` (1.306)
- `HOSPITAL CLINICO METROPOLITANO LA FLORIDA DRA. ELOISA DIAZ INZUNZA` (732) · `HOSPITAL CLÍNICO METROPOLITANO LA FLORIDA DRA. ELOISA DÍAZ INZUNZA` (1.613)
- `CLÍNICA PUERTO MONTT` (311) · `CLÍNICA PUERTO MONTT ` (984)
- `CLÍNICA REGIONAL LIRCAY` (307) · `CLÍNICA REGIONAL LIRCAY ` (1.092)
- `CLÍNICA ORIENTE` (66) · `CLÍNICA ORIENTE ` (13)
- `CLÍNICA INDISA` (168) · `CLÍNICA INDISA ` (219)
- `CLÍNICA ALEMANA VALDIVIA` (361) · `CLÍNICA ALEMANA VALDIVIA ` (806)
- `HOSPITAL FACH` (9) · `HOSPITAL FACH ` (33)
- `CLÍNICA LAS AMAPOLAS` (61) · `CLÍNICA LAS AMAPOLAS ` (151)
- `CLÍNICA ALEMANA DE TEMUCO` (303) · `CLÍNICA ALEMANA DE TEMUCO ` (761)
- `CLÍNICA DEL CARMEN` (12) · `CLÍNICA DEL CARMEN ` (21)
- `CLÍNICA ALEMANA` (74) · `CLÍNICA ALEMANA ` (126)
- `HOSPITAL FFAA CIRUJANO GUZMÁN` (117) · `HOSPITAL FFAA CIRUJANO GUZMÁN ` (279)
- `CLÍNICA DE SALUD INTEGRAL` (196) · `CLÍNICA DE SALUD INTEGRAL ` (688)
- `CLÍNICA SANTA MARÍA` (57) · `CLÍNICA SANTA MARÍA ` (172)
- `CLÍNICA LAS CONDES` (102) · `CLÍNICA LAS CONDES ` (380)
- `HOSPITAL CARABINEROS` (13) · `HOSPITAL CARABINEROS ` (25)
- `CLÍNICA LOS ANDES` (375) · `CLÍNICA LOS ANDES ` (643)
- `CLÍNICA COLONIAL` (38) · `CLÍNICA COLONIAL ` (77)
- `HOSPITAL MUTUAL DE SEGURIDAD CCHC LOS ÁNGELES` (3) · `HOSPITAL MUTUAL DE SEGURIDAD CCHC LOS ÁNGELES ` (3)
- `CLÍNICA MUTUAL DE SEGURIDAD CCHC RANCAGUA` (4) · `CLÍNICA MUTUAL DE SEGURIDAD CCHC RANCAGUA ` (8)
- `CLÍNICA PSICOTERAPIA LOS TIEMPOS` (1) · `CLÍNICA PSICOTERAPIA LOS TIEMPOS ` (3)
- `CLÍNICA ADVENTISTA` (76) · `CLÍNICA ADVENTISTA ` (143)

**Valores que no aparecen en todos los años** (492):

| Valor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| `HOSPITAL CLÍNICO DE MAGALLANES DR. LAUTARO NAVARRO AVARIA` | 12.059 | 7.859 | 9.046 | 10.354 | 12.018 | — |
| `HOSPITAL DR. LAUTARO NAVARRO AVARIA (PUNTA ARENAS)` | — | — | — | — | — | 12.268 |
| `HOSPITAL DE PEÑAFLOR` | 1.323 | 1.152 | 1.075 | 1.338 | 1.523 | — |
| `HOSPITAL INTERCULTURAL DE NUEVA IMPERIAL` | 1.002 | 955 | 989 | 1.047 | 1.107 | — |
| `HOSPITAL INTERCULTURAL KALLVULLANKA (CAÑETE)` | 1.067 | 1.014 | 1.219 | 1.181 | — | — |
| `HOSPITAL DE CALBUCO` | 827 | 828 | 834 | 837 | 867 | — |
| `HOSPITAL DEL SALVADOR (SANTIAGO, PROVIDENCIA)` | 1.446 | 777 | 669 | 580 | — | 632 |
| `HOSPITAL SAN MARTÍN (QUILLOTA)` | 998 | 675 | 648 | 725 | — | 911 |
| `HOSPITAL DR. MARIO SÁNCHEZ VERGARA (LA CALERA)` | 950 | 759 | 815 | 689 | 712 | — |
| `HOSPITAL DR. ABRAHAM GODOY (LAUTARO)` | 808 | 707 | 639 | 693 | — | 904 |
| `HOSPITAL DR. FÉLIX BULNES CERDA (SANTIAGO, QUINTA NORMAL)` | 687 | 524 | 755 | 834 | — | 903 |
| `HOSPITAL SAN AGUSTÍN (LA LIGUA)` | 786 | 660 | 675 | 706 | 746 | — |
| `HOSPITAL PENCO - LIRQUÉN` | 782 | 653 | 634 | 674 | — | 824 |
| `HOSPITAL SAN FRANCISCO (LLAILLAY)` | 581 | 551 | 637 | 795 | 826 | — |
| `HOSPITAL SANTO TOMÁS (LIMACHE)` | 739 | 707 | 772 | 568 | 589 | — |
| `HOSPITAL ADRIANA COUSIÑO (QUINTERO)` | 732 | 604 | 663 | 613 | 728 | — |
| `HOSPITAL CLÍNICO SAN BORJA-ARRIARÁN (SANTIAGO, SANTIAGO)` | 505 | 850 | 539 | 539 | — | 898 |
| `HOSPITAL DE URGENCIA ASISTENCIA PÚBLICA DR. ALEJANDRO DEL RÍO` | 796 | 730 | 801 | 471 | 511 | — |
| `HOSPITAL COMUNITARIO DE SALUD FAMILIAR DE BULNES` | 499 | 592 | 659 | 715 | 798 | — |
| `HOSPITAL DR. RICARDO VALENZUELA SÁEZ (RENGO)` | 554 | 442 | 595 | 726 | 790 | — |
| `HOSPITAL CLAUDIO VICUÑA (SAN ANTONIO)` | 835 | 710 | 844 | 709 | — | — |
| `HOSPITAL JUANA ROSS DE EDWARDS (PEÑABLANCA, VILLA ALEMANA)` | 745 | 672 | 604 | 484 | 568 | — |
| `HOSPITAL SAN JOSÉ (VICTORIA)` | 529 | 478 | 732 | 661 | — | 609 |
| `HOSPITAL DR. ABEL FUENTEALBA LAGOS DE SAN JAVIER` | 706 | 533 | 555 | 564 | 610 | — |
| `HOSPITAL DE LEBU` | 616 | 579 | 559 | 559 | 614 | — |
| `HOSPITAL COMUNITARIO DE MULCHÉN` | 683 | 626 | 900 | 666 | — | — |
| `HOSPITAL COMUNITARIO DE LAJA` | 618 | 549 | 526 | 486 | 579 | — |
| `HOSPITAL REGIONAL DE RANCAGUA` | 556 | 462 | 510 | 622 | — | 589 |
| `HOSPITAL PADRE BERNABÉ DE LUCERNA (PANGUIPULLI) (D)` | 573 | 484 | 537 | 541 | 587 | — |
| `HOSPITAL SAN VICENTE (ARAUCO)` | 674 | 722 | 612 | 609 | — | — |
| `DESCONOCIDO` | 23 | 203 | 378 | 2.000 | — | — |
| `HOSPITAL COMUNITARIO DE SANTA BÁRBARA` | 518 | 507 | 489 | 507 | 576 | — |
| `HOSPITAL DE PUERTO AISÉN` | 696 | 614 | 618 | 626 | — | — |
| `HOSPITAL DR. DINO STAGNO M.(TRAIGUÉN)` | 496 | 509 | 558 | 482 | 465 | — |
| `HOSPITAL SAN JUAN DE DIOS (VICUÑA)` | 482 | 486 | 431 | 450 | 581 | — |
| `HOSPITAL DE COLLIPULLI` | 253 | 440 | 585 | 560 | 551 | — |
| `HOSPITAL DE FRUTILLAR` | 482 | 480 | 475 | 450 | 496 | — |
| `HOSPITAL SAN JOSÉ (CASABLANCA)` | 651 | 343 | 424 | 484 | 444 | — |
| `HOSPITAL DE RÍO BUENO` | 545 | 386 | 379 | 487 | 543 | — |
| `HOSPITAL COMUNITARIO DE YUMBEL` | 507 | 432 | 524 | 396 | 479 | — |
| … y 452 más |  |  |  |  |  |  |
