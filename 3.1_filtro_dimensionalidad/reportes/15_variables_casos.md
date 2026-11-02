# Variables de los casos de estudio (actividad 3.1, script 15)

Generado por `3.1_filtro_dimensionalidad/scripts/15_variables_casos.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 3 de la partición (SHA-256 `50f07908f35df51c31077971d0aafaf69182c3baea926af34b00d6fff41229b1`), y la regla de «no planificado» de `2.2_depuracion_etiquetado/reglas/parametros.csv`. Salida: `data/processed/variables_casos.parquet`, con una fila por caso de estudio. No se abre el conjunto de prueba. Las decisiones están en `3.1_filtro_dimensionalidad/bitacora.md` (D46 a D49).

**Variables:** las 30 de la tabla siguiente, para los 3.347.652 casos de estudio de desarrollo. Ninguna se elige ni se descarta por su relación con el reingreso; las tasas de este reporte son solo descriptivas.

## 1. Las variables

«Sin dato» cuenta los casos con el valor SIN DATO (en las de categorías) o sin valor (en las numéricas).

| Variable | Decisión | Contenido | Valores | Sin dato |
|---|---|---|---|---|
| `EDAD` | D46 | Edad en años, con decimales, al ingreso del propio egreso | de 0,0 a 109,9 | — |
| `SEXO` | D46 | Sexo, tal cual | 3 valores | 312 |
| `PREVISION_GRUPO` | D46 | Previsión en 8 grupos (reglas/prevision_grupos.csv) | 9 valores | 2.425 |
| `REGION` | D46 | Región de residencia, desde la provincia (reglas/provincia_region.csv) | 17 valores | 1.089 |
| `TIPO_INGRESO` | D46 | Tipo de ingreso del propio egreso, tal cual | 4 valores | 295 |
| `ESTADIA` | D46 | Días desde el ingreso índice (el que abre el episodio) hasta el alta del caso | de 0 a 3.146 | — |
| `CDM` | D46 | Categoría diagnóstica mayor, tal cual | 22 valores | — |
| `PESO_GRD` | D46 | Peso del GRD; el peso 0 queda sin dato | de 0,1 a 20,6 | 1 |
| `HOSP_PREVIAS` | D47 | Hospitalizaciones de la misma persona (episodios) terminadas en la ventana | de 0 a 64 | — |
| `HOSP_PREVIAS_NO_PLANIF` | D47 | De ellas, las que empezaron con un ingreso no planificado (D20 y D33) | de 0 a 30 | — |
| `DIAS_ULTIMA_HOSP` | D47 | Días desde el alta de la última hospitalización de la ventana hasta el ingreso índice | de 0 a 366 | — |
| `CMA_PREVIAS` | D47 | Cirugías mayores ambulatorias terminadas en la ventana | de 0 a 11 | — |
| `SESIONES_PREVIAS` | D47, D50 | Sesiones de tratamiento (diagnóstico principal Z51) y tratamientos periódicos (E15) terminados en la ventana | de 0 a 340 | — |
| `VENTANA_CORTADA` | D47 | 1 si la ventana empieza antes del inicio del bloque del identificador (D42 y D44) | de 0 a 1 | — |
| `INDICE_COMORBILIDAD` | D48, D54 | Índice de comorbilidad: el de `indice_comorbilidad` (reingreso de Moore), con los diagnósticos de `comorbilidad_diagnosticos` (secundarios) | de -4 a 102 | — |
| `TIPO_ALTA` | D49 | Destino al alta, tal cual | 5 valores | — |
| `SEVERIDAD` | D49 | Nivel de severidad del GRD (1 a 3; es el último dígito del código) | de 1 a 3 | — |
| `RIESGO_MORTALIDAD` | D49 | Nivel de riesgo de mortalidad del GRD (1 a 3) | de 1 a 3 | — |
| `ESPECIALIDAD_INTERVENCION` | D49 | Especialidad de la intervención del episodio, o SIN INTERVENCIÓN | 48 valores | — |
| `UCI_UTI` | D49 | 1 si algún egreso del episodio pasó por una unidad de cuidados intensivos o intermedios | de 0 a 1 | — |
| `TRASLADO` | D49 | 1 si el episodio pasó por más de un hospital (D19) | de 0 a 1 | — |
| `N_DIAGNOSTICOS` | D49 | Diagnósticos distintos del egreso | de 0 a 35 | — |
| `N_PROCEDIMIENTOS` | D49 | Procedimientos distintos del egreso | de 0 a 30 | — |
| `ESPECIALIDAD` | D49 | Especialidad médica del episodio, tal cual | 59 valores | — |
| `TIPO_PROCEDENCIA` | D49 | De dónde llega el paciente, tal cual | 18 valores | 984 |
| `SERVICIO_INGRESO` | D49 | Servicio clínico de ingreso, tal cual | 85 valores | 16.539 |
| `SERVICIO_ALTA` | D49 | Servicio clínico de alta, tal cual | 83 valores | 13.834 |
| `PUEBLO_ORIGINARIO` | D49 | SÍ si la etnia nombra un pueblo originario; NO si dice NINGUNO u OTRO | 3 valores | 3 |
| `NACIONALIDAD_EXTRANJERA` | D49 | SÍ si la nacionalidad no es chilena | 3 valores | 13.024 |
| `HOSPITAL` | D49 | Código del hospital del egreso; su uso como predictora lo decide la revisión del profesor guía | 72 valores | — |

Índice de comorbilidad en uso: **MOORE**, índice de reingreso de Moore et al. (2017): suma de los pesos de las condiciones de Elixhauser presentes.

## 2. Episodio e historia

**Ingreso índice.** En 47.499 casos el episodio empezó antes del ingreso a este hospital (traslados). En ellos la mediana de la estadía es de 20 días contando todo el episodio y de 9 en el último hospital.

**Ventana.** Cuenta lo que terminó entre el ingreso índice menos 365 días y el ingreso índice, ambos días incluidos, sin el propio episodio: una hospitalización que terminó el mismo día del ingreso índice cuenta, igual que el etiquetado cuenta el día 0 como reingreso (D20). En 138.294 casos el propio episodio dura 0 días: como termina el mismo día del ingreso índice, se descuenta para no contarlo como hospitalización previa.

**Valores extremos.** `HOSP_PREVIAS` llega a 64. 21 casos, de 1 persona, tienen 50 o más; de los egresos de esa persona, el 0,0 % dura 0 días y el 70,4 % es programado.

Hospitalizaciones previas y reingreso a 30 días, sin y con la marca de ventana cortada:

| Hospitalizaciones previas | Casos sin marca | Reingreso a 30 días | Casos con marca | Reingreso a 30 días |
|---|---|---|---|---|
| 0 | 1.663.433 | 4,53 % | 978.106 | 4,64 % |
| 1 | 344.519 | 8,19 % | 142.842 | 9,04 % |
| 2 | 99.574 | 12,32 % | 33.054 | 13,91 % |
| 3 | 35.821 | 17,07 % | 10.165 | 19,42 % |
| 4 | 15.281 | 21,37 % | 3.677 | 24,37 % |
| 5 o más | 17.737 | 29,63 % | 3.443 | 32,24 % |

Casos con la ventana cortada, por año del alta:

| Año | Casos de estudio | Con la ventana cortada | % |
|---|---|---|---|
| 2019 | 644.415 | 644.415 | 100,0 % |
| 2020 | 446.923 | 9.346 | 2,1 % |
| 2021 | 508.698 | 508.698 | 100,0 % |
| 2022 | 564.053 | 8.820 | 1,6 % |
| 2023 | 615.867 | 8 | 0,0 % |
| 2024 | 567.696 | 0 | 0,0 % |

Días desde la última hospitalización (reingreso a 30 días de los casos sin marca):

| Días | Casos | Reingreso a 30 días sin marca |
|---|---|---|
| 0 a 7 | 106.970 | 12,59 % |
| 8 a 30 | 176.684 | 13,33 % |
| 31 a 90 | 179.818 | 11,19 % |
| 91 a 180 | 121.055 | 9,14 % |
| 181 a 365 | 121.586 | 7,53 % |
| sin hospitalización previa | 2.641.539 | 4,53 % |

Cirugías mayores ambulatorias y sesiones previas, que incluyen las sesiones Z51 y los tratamientos periódicos del criterio E15 (casos y reingreso a 30 días sin marca):

| Variable | 0 | 1 | 2 o más |
|---|---|---|---|
| `CMA_PREVIAS` | 3.290.208 (5,95 %) | 50.033 (8,16 %) | 7.411 (8,91 %) |
| `SESIONES_PREVIAS` | 3.325.408 (5,92 %) | 9.565 (13,63 %) | 12.679 (18,70 %) |

## 3. Índice de comorbilidad

Las 31 condiciones de Elixhauser con los códigos de Quan et al. (2005), buscadas en los diagnósticos secundarios del egreso, sin el principal. El diagnóstico principal es el motivo de la hospitalización y no una comorbilidad: entra a los modelos por sus códigos (D45), la CDM, el peso GRD y la severidad (D54). Con él, el número de condiciones subiría en 389.909 casos (11,6 %), sobre todo por el mismo cáncer o la misma insuficiencia cardíaca por la que la persona se hospitalizó. Las jerarquías ya están aplicadas: la diabetes con complicaciones reemplaza a la sin complicaciones, el cáncer metastásico al tumor sólido y la hipertensión con complicaciones a la sin complicaciones. Los códigos están en `3.1_filtro_dimensionalidad/reglas/comorbilidad_quan2005.csv`.

**Índice en uso: Moore (reingreso).** Es el índice de reingreso de Moore et al. (2017): suma de los pesos de las condiciones de Elixhauser presentes. Cada condición suma su peso, de `3.1_filtro_dimensionalidad/reglas/pesos_elixhauser.csv`: por ejemplo, insuficiencia cardíaca 13, insuficiencia renal 15, cáncer metastásico 21 y obesidad -3. Moore et al. (2017) estimaron los pesos para predecir el reingreso a 30 días con las 29 medidas de AHRQ: las arritmias no tienen peso y las dos hipertensiones comparten el mismo, que se suma una sola vez porque la jerarquía deja solo una.

| N.º | Condición | Peso de Moore | Casos | % de los casos | Reingreso a 30 días |
|---|---|---|---|---|---|
| 1 | Insuficiencia cardíaca congestiva | 13 | 130.434 | 3,90 % | 11,76 % |
| 2 | Arritmias cardíacas | 0 | 161.683 | 4,83 % | 9,94 % |
| 3 | Enfermedad valvular | 0 | 55.975 | 1,67 % | 10,34 % |
| 4 | Trastornos de la circulación pulmonar | 5 | 35.952 | 1,07 % | 11,51 % |
| 5 | Trastornos vasculares periféricos | 4 | 90.562 | 2,71 % | 12,50 % |
| 6 | Hipertensión sin complicaciones | -1 | 898.193 | 26,83 % | 7,98 % |
| 7 | Hipertensión con complicaciones | -1 | 27.604 | 0,82 % | 12,32 % |
| 8 | Parálisis | 6 | 24.081 | 0,72 % | 10,24 % |
| 9 | Otros trastornos neurológicos | 7 | 99.341 | 2,97 % | 9,82 % |
| 10 | Enfermedad pulmonar crónica | 8 | 215.172 | 6,43 % | 8,17 % |
| 11 | Diabetes sin complicaciones | 6 | 381.721 | 11,40 % | 8,32 % |
| 12 | Diabetes con complicaciones | 9 | 109.226 | 3,26 % | 11,43 % |
| 13 | Hipotiroidismo | 0 | 278.280 | 8,31 % | 6,88 % |
| 14 | Insuficiencia renal | 15 | 190.730 | 5,70 % | 13,46 % |
| 15 | Enfermedad hepática | 10 | 107.533 | 3,21 % | 11,56 % |
| 16 | Úlcera péptica sin sangrado | 0 | 11.669 | 0,35 % | 10,64 % |
| 17 | VIH/sida | 19 | 10.858 | 0,32 % | 9,51 % |
| 18 | Linfoma | 16 | 8.615 | 0,26 % | 12,29 % |
| 19 | Cáncer metastásico | 21 | 41.411 | 1,24 % | 12,10 % |
| 20 | Tumor sólido sin metástasis | 15 | 68.487 | 2,05 % | 10,30 % |
| 21 | Artritis reumatoide y enfermedades del colágeno | 4 | 42.457 | 1,27 % | 8,46 % |
| 22 | Coagulopatía | 7 | 46.348 | 1,38 % | 12,41 % |
| 23 | Obesidad | -3 | 413.873 | 12,36 % | 5,46 % |
| 24 | Pérdida de peso | 10 | 50.638 | 1,51 % | 12,13 % |
| 25 | Trastornos de líquidos y electrolitos | 8 | 203.284 | 6,07 % | 11,23 % |
| 26 | Anemia por pérdida de sangre | 3 | 7.514 | 0,22 % | 8,96 % |
| 27 | Anemia por deficiencia | 9 | 35.150 | 1,05 % | 10,64 % |
| 28 | Abuso de alcohol | 6 | 121.552 | 3,63 % | 7,59 % |
| 29 | Abuso de drogas | 14 | 91.514 | 2,73 % | 7,57 % |
| 30 | Psicosis | 10 | 12.919 | 0,39 % | 8,64 % |
| 31 | Depresión | 4 | 100.899 | 3,01 % | 7,50 % |

Número de condiciones de Elixhauser:

| Condiciones | Casos | % | Reingreso a 30 días |
|---|---|---|---|
| 0 | 1.466.078 | 43,8 % | 3,99 % |
| 1 | 802.027 | 24,0 % | 5,31 % |
| 2 | 490.977 | 14,7 % | 7,07 % |
| 3 | 293.775 | 8,8 % | 8,90 % |
| 4 | 158.781 | 4,7 % | 11,01 % |
| 5 o más | 136.014 | 4,1 % | 13,31 % |

Comparación de los índices, con y sin el diagnóstico principal. El área bajo la curva ROC mide qué tan bien el índice, solo, ordena a los casos que reingresan a 30 días por sobre los que no (0,5 es el azar):

| Índice | Diagnósticos | Promedio | Área bajo la curva ROC |
|---|---|---|---|
| Moore (reingreso) (en uso) | Solo secundarios | 5,25 | 0,616 |
| Moore (reingreso) | Todos | 6,39 | 0,627 |
| Conteo de condiciones de Elixhauser | Solo secundarios | 1,22 | 0,611 |
| Conteo de condiciones de Elixhauser | Todos | 1,33 | 0,618 |
| van Walraven (mortalidad) | Solo secundarios | 1,54 | 0,599 |
| van Walraven (mortalidad) | Todos | 1,94 | 0,607 |
| Charlson (pesos de Quan 2011) | Solo secundarios | 0,49 | 0,592 |
| Charlson (pesos de Quan 2011) | Todos | 0,63 | 0,609 |
| Número de diagnósticos (para comparar) | Todos | 5,51 | 0,614 |

Tienen al menos una condición de Elixhauser el 56,2 % de los casos y al menos una de Charlson el 31,7 %.

Con los pesos de Quan et al. (2011) cinco condiciones de Charlson valen 0 puntos (infarto agudo de miocardio, enfermedad vascular periférica, enfermedad cerebrovascular, úlcera péptica, diabetes sin complicaciones crónicas): por eso solo el 21,9 % de los casos tiene un puntaje de Charlson mayor que 0.

Casos con al menos una condición, por año del alta:

| Año | Elixhauser | Charlson |
|---|---|---|
| 2019 | 49,2 % | 27,7 % |
| 2020 | 52,2 % | 29,7 % |
| 2021 | 56,9 % | 31,6 % |
| 2022 | 57,1 % | 31,7 % |
| 2023 | 59,2 % | 33,3 % |
| 2024 | 62,5 % | 35,8 % |

## 4. Otras variables del CMBD

En las columnas tomadas tal cual, los valores con menos de 100 casos de estudio pasan a OTRO (D45). Reingreso a 30 días menor y mayor entre los valores con 1.000 casos o más:

| Variable | Valores | Juntados en OTRO | Menor reingreso | Mayor reingreso |
|---|---|---|---|---|
| `TIPO_ALTA` | 5 | — | DOMICILIO: 5,57 % | FUGA DEL PACIENTE: 20,08 % |
| `ESPECIALIDAD_INTERVENCION` | 48 | 36 (694 casos) | MATRONAS(ES): 1,06 % | ANESTESIOLOGÍA: 13,52 % |
| `ESPECIALIDAD` | 59 | 23 (249 casos) | CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL: 1,61 % | HEMATO-ONCOLOGÍA PEDIÁTRICA: 23,20 % |
| `TIPO_PROCEDENCIA` | 18 | 2 (4 casos) | CARDIOCIRUGÍA PAGO GRD: 1,52 % | HOSPITALIZACIÓN DOMICILIARIA: 13,18 % |
| `SERVICIO_INGRESO` | 85 | 8 (248 casos) | PENSIONADO MATERNIDAD: 1,08 % | ONCOLOGÍA: 13,03 % |
| `SERVICIO_ALTA` | 83 | 8 (170 casos) | PENSIONADO MATERNIDAD: 1,07 % | ONCOLOGÍA: 15,47 % |
| `HOSPITAL` | 72 | — | 110110: 3,16 % | 116107: 14,35 % |
| `PUEBLO_ORIGINARIO` | 3 | — | SÍ: 5,64 % | NO: 5,90 % |
| `NACIONALIDAD_EXTRANJERA` | 3 | — | SÍ: 3,81 % | NO: 6,04 % |

| Variable | Casos y reingreso a 30 días por valor |
|---|---|
| `SEVERIDAD` | 1: 1.764.001 casos (3,89 %) · 2: 927.776 casos (7,09 %) · 3: 655.875 casos (9,63 %) |
| `RIESGO_MORTALIDAD` | 1: 2.218.905 casos (4,15 %) · 2: 615.763 casos (8,25 %) · 3: 512.984 casos (10,63 %) |
| `UCI_UTI` | 0: 2.873.646 casos (5,54 %) · 1: 474.006 casos (8,05 %) |
| `TRASLADO` | 0: 3.291.492 casos (5,85 %) · 1: 56.160 casos (8,82 %) |

Reingreso a 30 días según el número de diagnósticos y de procedimientos:

| Variable | Reingreso a 30 días por tramo |
|---|---|
| `N_DIAGNOSTICOS` | 0 a 1: 3,44 % · 2 a 3: 4,10 % · 4 a 5: 4,99 % · 6 a 7: 6,20 % · 8 a 9: 7,72 % · 10 a 12: 9,87 % · 13 o más: 13,01 % |
| `N_PROCEDIMIENTOS` | 0: 8,92 % · 1 a 4: 4,87 % · 5 a 9: 4,95 % · 10 a 14: 6,43 % · 15 a 20: 9,41 % · 21 o más: 10,79 % |

Valores juntados en OTRO:

| Variable | Valor | Casos |
|---|---|---|
| `ESPECIALIDAD_INTERVENCION` | NEONATOLOGÍA | 98 |
| `ESPECIALIDAD_INTERVENCION` | GINECOLOGÍA PEDIÁTRICA Y DE LA ADOLESCENCIA | 90 |
| `ESPECIALIDAD_INTERVENCION` | HEMATO-ONCOLOGÍA PEDIÁTRICA | 69 |
| `ESPECIALIDAD_INTERVENCION` | DIABETOLOGÍA | 55 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA FAMILIAR | 44 |
| `ESPECIALIDAD_INTERVENCION` | MICROBIOLOGIA CLINICA | 40 |
| `ESPECIALIDAD_INTERVENCION` | NEUROLOGÍA PEDIÁTRICA | 39 |
| `ESPECIALIDAD_INTERVENCION` | ORTODONCIA Y ORTOPEDIA DENTO MAXILOFACIAL | 38 |
| `ESPECIALIDAD_INTERVENCION` | INFECTOLOGÍA PEDIATRICA | 37 |
| `ESPECIALIDAD_INTERVENCION` | NEFROLOGÍA PEDIÁTRICO | 33 |
| `ESPECIALIDAD_INTERVENCION` | INMUNOLOGÍA CLÍNICA | 25 |
| `ESPECIALIDAD_INTERVENCION` | IMPLANTOLOGIA BUCO MAXILOFACIAL | 16 |
| `ESPECIALIDAD_INTERVENCION` | PSIQUIATRÍA PEDIÁTRICA Y DE LA ADOLESCENCIA | 15 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA FÍSICA Y REHABILITACIÓN | 13 |
| `ESPECIALIDAD_INTERVENCION` | PATOLOGÍA ORAL Y MAXILOFACIAL | 11 |
| `ESPECIALIDAD_INTERVENCION` | GENÉTICA CLÍNICA | 9 |
| `ESPECIALIDAD_INTERVENCION` | ENDODONCIA | 7 |
| `ESPECIALIDAD_INTERVENCION` | TRASTORNOS TEMPOROMANDIBULARES Y DOLOR OROFACIAL | 7 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA DEL DEPORTE | 6 |
| `ESPECIALIDAD_INTERVENCION` | PERIODONCIA | 5 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA INTENSIVA PEDIÁTRICA | 5 |
| `ESPECIALIDAD_INTERVENCION` | ENDOCRINOLOGÍA PEDIÁTRICA | 4 |
| `ESPECIALIDAD_INTERVENCION` | GERIATRÍA | 4 |
| `ESPECIALIDAD_INTERVENCION` | ODONTOLOGÍA LEGAL | 4 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA TRANSFUSIONAL | 3 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA LEGAL | 2 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA MATERNO FETAL | 2 |
| `ESPECIALIDAD_INTERVENCION` | SALUD PÚBLICA (ODONTOLÓGICA) | 2 |
| `ESPECIALIDAD_INTERVENCION` | REUMATOLOGÍA | 2 |
| `ESPECIALIDAD_INTERVENCION` | SALUD PÚBLICA | 2 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA FISICA Y REHABILITACIÓN PEDIÁTRICA | 2 |
| `ESPECIALIDAD_INTERVENCION` | LABORATORIO CLÍNICO | 1 |
| `ESPECIALIDAD_INTERVENCION` | REHABILITACIÓN ORAL | 1 |
| `ESPECIALIDAD_INTERVENCION` | IMAGENOLOGÍA ORAL Y MAXILOFACIAL | 1 |
| `ESPECIALIDAD_INTERVENCION` | ADOLESCENCIA | 1 |
| `ESPECIALIDAD_INTERVENCION` | MEDICINA NUCLEAR | 1 |
| `ESPECIALIDAD` | GINECOLOGÍA PEDIÁTRICA Y DE LA ADOLESCENCIA | 56 |
| `ESPECIALIDAD` | ANESTESIOLOGÍA | 47 |
| `ESPECIALIDAD` | REUMATOLOGÍA PEDIÁTRICA | 25 |
| `ESPECIALIDAD` | ANATOMÍA PATOLÓGICA | 23 |
| `ESPECIALIDAD` | ORTODONCIA Y ORTOPEDIA DENTO MAXILOFACIAL | 22 |
| `ESPECIALIDAD` | RADIOTERAPIA ONCOLÓGICA | 21 |
| `ESPECIALIDAD` | INFECTOLOGÍA PEDIATRICA | 13 |
| `ESPECIALIDAD` | SIN DATO | 12 |
| `ESPECIALIDAD` | MICROBIOLOGIA CLINICA | 8 |
| `ESPECIALIDAD` | IMPLANTOLOGIA BUCO MAXILOFACIAL | 3 |
| `ESPECIALIDAD` | PERIODONCIA | 3 |
| `ESPECIALIDAD` | GENÉTICA CLÍNICA | 3 |
| `ESPECIALIDAD` | LABORATORIO CLÍNICO | 2 |
| `ESPECIALIDAD` | ENDODONCIA | 2 |
| `ESPECIALIDAD` | MEDICINA TRANSFUSIONAL | 1 |
| `ESPECIALIDAD` | MEDICINA DEL DEPORTE | 1 |
| `ESPECIALIDAD` | PATOLOGÍA ORAL Y MAXILOFACIAL | 1 |
| `ESPECIALIDAD` | ODONTOLOGÍA LEGAL | 1 |
| `ESPECIALIDAD` | MEDICINA MATERNO FETAL | 1 |
| `ESPECIALIDAD` | IMAGENOLOGÍA | 1 |
| `ESPECIALIDAD` | MEDICINA FISICA Y REHABILITACIÓN PEDIÁTRICA | 1 |
| `ESPECIALIDAD` | ADOLESCENCIA (PEDIATRIA) | 1 |
| `ESPECIALIDAD` | NUTRIÓLOGO | 1 |
| `TIPO_PROCEDENCIA` | LISTA DE ESPERA | 3 |
| `TIPO_PROCEDENCIA` | UGCC | 1 |
| `SERVICIO_INGRESO` | MEDICINA FÍSICA Y REHABILITACIÓN | 95 |
| `SERVICIO_INGRESO` | PSIQUIATRÍA FORENSE MEDIANA COMPLEJIDAD | 50 |
| `SERVICIO_INGRESO` | ÁREA DE HOSPITALIZACIÓN DE CUIDADOS INTENSIVOS EN PSIQUIATRÍA INFANTE ADOLESCENTE | 42 |
| `SERVICIO_INGRESO` | HOSPITAL DE DÍA MÉDICO | 40 |
| `SERVICIO_INGRESO` | CIRUGÍA TÓRAX | 10 |
| `SERVICIO_INGRESO` | PSIQUIATRÍA FORENSE ALTA COMPLEJIDAD | 7 |
| `SERVICIO_INGRESO` | PSIQUIATRÍA CRÓNICO | 3 |
| `SERVICIO_INGRESO` | CARDIOCIRUGÍA (INFANTIL) | 1 |
| `SERVICIO_ALTA` | UNIDAD DE CUIDADOS INTENSIVOS QUEMADOS | 90 |
| `SERVICIO_ALTA` | PSIQUIATRÍA FORENSE MEDIANA COMPLEJIDAD | 53 |
| `SERVICIO_ALTA` | HOSPITAL DE DÍA MÉDICO | 11 |
| `SERVICIO_ALTA` | PSIQUIATRÍA FORENSE ALTA COMPLEJIDAD | 9 |
| `SERVICIO_ALTA` | HOSPITA DE DÍA ONCOLÓGICO | 4 |
| `SERVICIO_ALTA` | CARDIOCIRUGÍA (INFANTIL) | 1 |
| `SERVICIO_ALTA` | PSIQUIATRÍA MEDIANA ESTADÍA | 1 |
| `SERVICIO_ALTA` | CIRUGÍA TÓRAX | 1 |

En las variables de categorías de la decisión 1 no se junta ningún valor; tienen menos de 100 casos: ninguno.

## 5. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `ventana_historia_dias` | `365` | Días antes del ingreso índice que mira la historia del paciente (D42: 12 meses). Cuenta lo que terminó entre el ingreso índice menos estos días y el ingreso índice, sin el propio episodio (script 15) |
| `inicio_bloques` | `A=2019-01-01 / B=2021-01-01` | Primer día de cada bloque de identificador de paciente (D03). La ventana de historia de un caso está cortada si empieza antes del inicio de su bloque (D42 y D44, script 15) |
| `dias_sin_hospitalizacion` | `366` | Valor de DIAS_ULTIMA_HOSP cuando no hay ninguna hospitalización en la ventana: un día más que la ventana (script 15) |
| `indice_comorbilidad` | `MOORE` | Índice de la columna INDICE_COMORBILIDAD, con las condiciones de Elixhauser de Quan et al. (2005). MOORE = índice de reingreso de Moore et al. (2017): suma de los pesos de reglas/pesos_elixhauser.csv. CONTEO = número de condiciones. VAN_WALRAVEN = pesos de van Walraven et al. (2009). CHARLSON = puntaje de Charlson con los pesos de Quan et al. (2011). El reporte siempre muestra los cuatro (D48, D54, script 15) |
| `comorbilidad_diagnosticos` | `SECUNDARIOS` | Diagnósticos en que se buscan las condiciones del índice. SECUNDARIOS = sin el diagnóstico principal, que es el motivo de la hospitalización y no una comorbilidad (como el programa de AHRQ del índice de Moore). TODOS = también el principal. El reporte muestra las dos formas (D54, script 15) |
| `casos_minimos_categoria` | `100` | En las variables del CMBD tomadas tal cual, los valores con menos de estos casos de estudio se juntan en OTRO: el mismo mínimo del filtro de códigos (D45, script 15) |
| `servicios_criticos` | `CUIDADOS INTENSIVOS / (UCI) / TRATAMIENTO INTERMEDIO / TRATAMIENTOS INTERMEDIOS / UTI ADULTOS / CUIDADOS INTERMEDIOS` | Textos que marcan una unidad de cuidados intensivos o de tratamiento intermedio en los servicios de ingreso, de traslado interno o de alta, separados por una barra vertical (script 15) |
| `servicios_criticos_excluidos` | `PSIQUIATR` | Textos que anulan la marca anterior: las áreas de «cuidados intensivos en psiquiatría» no son unidades de paciente crítico (script 15) |
| `etnia_sin_pueblo` | `NINGUNO / OTRO` | Valores de ETNIA que no nombran un pueblo originario. Se juntan porque se intercambian entre años (script 15) |
| `nacionalidad_local` | `CHILE` | Valor de NACIONALIDAD que no es extranjero (script 15) |

De `2.2_depuracion_etiquetado/reglas/parametros.csv` (regla de «no planificado», D20 y D33): `ingresos_no_planificados` = `URGENCIA / OBSTETRICA`; `grd_parto` = `146 / 147`; `diagnosticos_sesion` = `Z51`.

## 6. Verificaciones

- El conjunto de desarrollo es el de la versión 3 registrada de la partición: **sí**.
- Se leyeron todos los casos de estudio del conjunto de desarrollo registrado: **sí**.
- Hay una fila por caso de estudio, sin repetir ID_EGRESO: **sí**.
- Cada caso de estudio tiene su episodio y cada episodio, su egreso de apertura: **sí**.
- Todos los egresos de un episodio son de la misma persona: **sí**.
- Ningún egreso E04 de 2019 forma parte de un episodio, así que no entra en la historia: **sí**.
- Todas las previsiones y provincias con dato tienen grupo y región en las tablas de reglas: **sí**.
- Ninguna variable de categorías queda vacía: **sí**.
- La edad está entre 0 y 110 años: **sí**.
- La estadía del episodio es mayor o igual que la del propio egreso, y esta, que cero: **sí**.
- Las hospitalizaciones no planificadas no superan a las hospitalizaciones previas: **sí**.
- DIAS_ULTIMA_HOSP vale 366 justo cuando no hay hospitalizaciones previas, y si no, entre 0 y 365: **sí**.
- Ninguna cuenta de la historia es negativa: **sí**.
- La marca de ventana cortada coincide con la regla de D42 calculada con fechas de calendario: **sí**.
- El conteo de Elixhauser está entre 0 y 28 condiciones, el puntaje de Charlson entre 0 y 24 y el índice de Moore entre la suma de sus pesos negativos y la de sus pesos positivos: **sí**.
- INDICE_COMORBILIDAD es el índice de `indice_comorbilidad` calculado con los diagnósticos de `comorbilidad_diagnosticos`: **sí**.
- Después de las jerarquías, ningún caso tiene a la vez una condición y la versión que esta reemplaza: **sí**.
- En las columnas agrupadas no queda ningún valor propio con menos del mínimo de casos (OTRO puede tener menos): **sí**.
- Lo releído de variables_casos.parquet es igual a lo calculado: **sí**.
