# Variables de los casos de estudio (actividad 3.1, script 15)

Generado por `3.1_filtro_dimensionalidad/scripts/15_variables_casos.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 2 de la partición (SHA-256 `9546c8c7e80f634295e7c0538173661884aa6ce602e201a3cbd8ae615912abbb`), y la regla de «no planificado» de `2.2_depuracion_etiquetado/reglas/parametros.csv`. Salida: `data/processed/variables_casos.parquet`, con una fila por caso de estudio. No se abre el conjunto de prueba. Las decisiones están en `3.1_filtro_dimensionalidad/bitacora.md` (D46 a D49).

**Variables:** las 30 de la tabla siguiente, para los 3.354.118 casos de estudio de desarrollo. Ninguna se elige ni se descarta por su relación con el reingreso; las tasas de este reporte son solo descriptivas.

## 1. Las variables

«Sin dato» cuenta los casos con el valor SIN DATO (en las de categorías) o sin valor (en las numéricas).

| Variable | Decisión | Contenido | Valores | Sin dato |
|---|---|---|---|---|
| `EDAD` | D46 | Edad en años, con decimales, al ingreso del propio egreso | de 0,0 a 109,9 | — |
| `SEXO` | D46 | Sexo, tal cual | 3 valores | 313 |
| `PREVISION_GRUPO` | D46 | Previsión en 8 grupos (reglas/prevision_grupos.csv) | 9 valores | 2.439 |
| `REGION` | D46 | Región de residencia, desde la provincia (reglas/provincia_region.csv) | 17 valores | 1.090 |
| `TIPO_INGRESO` | D46 | Tipo de ingreso del propio egreso, tal cual | 4 valores | 295 |
| `ESTADIA` | D46 | Días desde el ingreso índice (el que abre el episodio) hasta el alta del caso | de 0 a 3.146 | — |
| `CDM` | D46 | Categoría diagnóstica mayor, tal cual | 22 valores | — |
| `PESO_GRD` | D46 | Peso del GRD; el peso 0 queda sin dato | de 0,1 a 20,6 | 1 |
| `HOSP_PREVIAS` | D47 | Hospitalizaciones de la misma persona (episodios) terminadas en la ventana | de 0 a 342 | — |
| `HOSP_PREVIAS_NO_PLANIF` | D47 | De ellas, las que empezaron con un ingreso no planificado (D20 y D33) | de 0 a 30 | — |
| `DIAS_ULTIMA_HOSP` | D47 | Días desde el alta de la última hospitalización de la ventana hasta el ingreso índice | de 0 a 366 | — |
| `CMA_PREVIAS` | D47 | Cirugías mayores ambulatorias terminadas en la ventana | de 0 a 11 | — |
| `SESIONES_PREVIAS` | D47 | Sesiones de tratamiento (diagnóstico principal Z51) terminadas en la ventana | de 0 a 200 | — |
| `VENTANA_CORTADA` | D47 | 1 si la ventana empieza antes del inicio del bloque del identificador (D42 y D44) | de 0 a 1 | — |
| `INDICE_COMORBILIDAD` | D48 | Índice de comorbilidad con todos los diagnósticos del egreso | de 0 a 15 | — |
| `TIPO_ALTA` | D49 | Destino al alta, tal cual | 5 valores | — |
| `SEVERIDAD` | D49 | Nivel de severidad del GRD (1 a 3; es el último dígito del código) | de 1 a 3 | — |
| `RIESGO_MORTALIDAD` | D49 | Nivel de riesgo de mortalidad del GRD (1 a 3) | de 1 a 3 | — |
| `ESPECIALIDAD_INTERVENCION` | D49 | Especialidad de la intervención del episodio, o SIN INTERVENCIÓN | 48 valores | — |
| `UCI_UTI` | D49 | 1 si algún egreso del episodio pasó por una unidad de cuidados intensivos o intermedios | de 0 a 1 | — |
| `TRASLADO` | D49 | 1 si el episodio pasó por más de un hospital (D19) | de 0 a 1 | — |
| `N_DIAGNOSTICOS` | D49 | Diagnósticos distintos del egreso | de 0 a 35 | — |
| `N_PROCEDIMIENTOS` | D49 | Procedimientos distintos del egreso | de 0 a 30 | — |
| `ESPECIALIDAD` | D49 | Especialidad médica del episodio, tal cual | 59 valores | — |
| `TIPO_PROCEDENCIA` | D49 | De dónde llega el paciente, tal cual | 18 valores | 988 |
| `SERVICIO_INGRESO` | D49 | Servicio clínico de ingreso, tal cual | 85 valores | 16.736 |
| `SERVICIO_ALTA` | D49 | Servicio clínico de alta, tal cual | 83 valores | 14.030 |
| `PUEBLO_ORIGINARIO` | D49 | SÍ si la etnia nombra un pueblo originario; NO si dice NINGUNO u OTRO | 3 valores | 3 |
| `NACIONALIDAD_EXTRANJERA` | D49 | SÍ si la nacionalidad no es chilena | 3 valores | 13.028 |
| `HOSPITAL` | D49 | Código del hospital del egreso; su uso como predictora lo decide la revisión del profesor guía | 72 valores | — |

Índice de comorbilidad en uso: **ELIXHAUSER**, número de condiciones de Elixhauser presentes (códigos de Quan et al., 2005).

## 2. Episodio e historia

**Ingreso índice.** En 47.504 casos el episodio empezó antes del ingreso a este hospital (traslados). En ellos la mediana de la estadía es de 20 días contando todo el episodio y de 9 en el último hospital.

**Ventana.** Cuenta lo que terminó entre el ingreso índice menos 365 días y el ingreso índice, ambos días incluidos, sin el propio episodio: una hospitalización que terminó el mismo día del ingreso índice cuenta, igual que el etiquetado cuenta el día 0 como reingreso (D20). En 143.031 casos el propio episodio dura 0 días: como termina el mismo día del ingreso índice, se descuenta para no contarlo como hospitalización previa.

**Valores extremos.** `HOSP_PREVIAS` llega a 342. 697 casos, de 13 personas, tienen 50 o más; de los egresos de esas personas, el 72,4 % dura 0 días y el 94,5 % es programado.

Hospitalizaciones previas y reingreso a 30 días, sin y con la marca de ventana cortada:

| Hospitalizaciones previas | Casos sin marca | Reingreso a 30 días | Casos con marca | Reingreso a 30 días |
|---|---|---|---|---|
| 0 | 1.663.338 | 4,53 % | 978.106 | 4,64 % |
| 1 | 344.466 | 8,19 % | 142.843 | 9,04 % |
| 2 | 99.865 | 12,29 % | 33.250 | 13,84 % |
| 3 | 36.099 | 17,00 % | 10.344 | 19,08 % |
| 4 | 15.548 | 21,04 % | 3.847 | 23,52 % |
| 5 o más | 21.328 | 26,07 % | 5.084 | 24,04 % |

Casos con la ventana cortada, por año del alta:

| Año | Casos de estudio | Con la ventana cortada | % |
|---|---|---|---|
| 2019 | 645.964 | 645.964 | 100,0 % |
| 2020 | 447.692 | 9.346 | 2,1 % |
| 2021 | 509.336 | 509.336 | 100,0 % |
| 2022 | 565.345 | 8.820 | 1,6 % |
| 2023 | 616.853 | 8 | 0,0 % |
| 2024 | 568.928 | 0 | 0,0 % |

Días desde la última hospitalización (reingreso a 30 días de los casos sin marca):

| Días | Casos | Reingreso a 30 días sin marca |
|---|---|---|
| 0 a 7 | 109.997 | 12,57 % |
| 8 a 30 | 178.777 | 13,25 % |
| 31 a 90 | 181.019 | 11,13 % |
| 91 a 180 | 121.244 | 9,13 % |
| 181 a 365 | 121.637 | 7,52 % |
| sin hospitalización previa | 2.641.444 | 4,53 % |

Cirugías mayores ambulatorias y sesiones previas (casos y reingreso a 30 días sin marca):

| Variable | 0 | 1 | 2 o más |
|---|---|---|---|
| `CMA_PREVIAS` | 3.296.406 (5,95 %) | 50.297 (8,16 %) | 7.415 (8,91 %) |
| `SESIONES_PREVIAS` | 3.331.598 (5,92 %) | 9.661 (14,42 %) | 12.859 (18,03 %) |

## 3. Índice de comorbilidad

Las 31 condiciones de Elixhauser con los códigos de Quan et al. (2005), buscadas en todos los diagnósticos del egreso. Las jerarquías ya están aplicadas: la diabetes con complicaciones reemplaza a la sin complicaciones, el cáncer metastásico al tumor sólido y la hipertensión con complicaciones a la sin complicaciones. Los códigos están en `3.1_filtro_dimensionalidad/reglas/comorbilidad_quan2005.csv`.

| N.º | Condición | Casos | % de los casos | Reingreso a 30 días |
|---|---|---|---|---|
| 1 | Insuficiencia cardíaca congestiva | 165.981 | 4,95 % | 12,02 % |
| 2 | Arritmias cardíacas | 186.813 | 5,57 % | 9,24 % |
| 3 | Enfermedad valvular | 62.811 | 1,87 % | 10,03 % |
| 4 | Trastornos de la circulación pulmonar | 46.269 | 1,38 % | 10,77 % |
| 5 | Trastornos vasculares periféricos | 102.521 | 3,06 % | 12,59 % |
| 6 | Hipertensión sin complicaciones | 898.816 | 26,80 % | 7,96 % |
| 7 | Hipertensión con complicaciones | 32.385 | 0,97 % | 12,30 % |
| 8 | Parálisis | 25.185 | 0,75 % | 10,10 % |
| 9 | Otros trastornos neurológicos | 127.037 | 3,79 % | 9,22 % |
| 10 | Enfermedad pulmonar crónica | 245.697 | 7,33 % | 8,28 % |
| 11 | Diabetes sin complicaciones | 394.203 | 11,75 % | 8,21 % |
| 12 | Diabetes con complicaciones | 142.658 | 4,25 % | 11,76 % |
| 13 | Hipotiroidismo | 279.137 | 8,32 % | 6,87 % |
| 14 | Insuficiencia renal | 200.315 | 5,97 % | 13,41 % |
| 15 | Enfermedad hepática | 114.804 | 3,42 % | 11,82 % |
| 16 | Úlcera péptica sin sangrado | 13.170 | 0,39 % | 10,29 % |
| 17 | VIH/sida | 13.740 | 0,41 % | 9,92 % |
| 18 | Linfoma | 17.730 | 0,53 % | 12,06 % |
| 19 | Cáncer metastásico | 48.347 | 1,44 % | 11,83 % |
| 20 | Tumor sólido sin metástasis | 167.839 | 5,00 % | 8,35 % |
| 21 | Artritis reumatoide y enfermedades del colágeno | 49.270 | 1,47 % | 8,36 % |
| 22 | Coagulopatía | 51.892 | 1,55 % | 12,23 % |
| 23 | Obesidad | 418.371 | 12,47 % | 5,43 % |
| 24 | Pérdida de peso | 51.953 | 1,55 % | 12,04 % |
| 25 | Trastornos de líquidos y electrolitos | 207.903 | 6,20 % | 11,21 % |
| 26 | Anemia por pérdida de sangre | 8.150 | 0,24 % | 9,04 % |
| 27 | Anemia por deficiencia | 38.026 | 1,13 % | 10,32 % |
| 28 | Abuso de alcohol | 125.855 | 3,75 % | 7,79 % |
| 29 | Abuso de drogas | 96.157 | 2,87 % | 7,64 % |
| 30 | Psicosis | 25.238 | 0,75 % | 8,26 % |
| 31 | Depresión | 114.301 | 3,41 % | 7,39 % |

Número de condiciones de Elixhauser:

| Condiciones | Casos | % | Reingreso a 30 días |
|---|---|---|---|
| 0 | 1.369.983 | 40,8 % | 3,81 % |
| 1 | 808.644 | 24,1 % | 5,21 % |
| 2 | 501.416 | 14,9 % | 6,78 % |
| 3 | 322.899 | 9,6 % | 8,68 % |
| 4 | 183.729 | 5,5 % | 10,70 % |
| 5 o más | 167.447 | 5,0 % | 13,09 % |

Comparación con Charlson (sensibilidad). El área bajo la curva ROC mide qué tan bien el índice, solo, ordena a los casos que reingresan a 30 días por sobre los que no (0,5 es el azar):

| Índice | Casos con al menos una condición | Promedio | Área bajo la curva ROC |
|---|---|---|---|
| Elixhauser (número de condiciones) | 59,2 % | 1,33 | 0,617 |
| Charlson (pesos de Quan 2011) | 37,2 % | 0,63 | 0,608 |
| Número de diagnósticos (para comparar) | — | 5,50 | 0,613 |

Con los pesos de Quan et al. (2011) cinco condiciones de Charlson valen 0 puntos (infarto agudo de miocardio, enfermedad vascular periférica, enfermedad cerebrovascular, úlcera péptica, diabetes sin complicaciones crónicas): por eso solo el 27,1 % de los casos tiene un puntaje de Charlson mayor que 0.

Casos con al menos una condición, por año del alta:

| Año | Elixhauser | Charlson |
|---|---|---|
| 2019 | 52,2 % | 33,1 % |
| 2020 | 55,0 % | 35,2 % |
| 2021 | 59,8 % | 37,2 % |
| 2022 | 60,2 % | 37,4 % |
| 2023 | 62,1 % | 38,9 % |
| 2024 | 65,5 % | 41,5 % |

## 4. Otras variables del CMBD

En las columnas tomadas tal cual, los valores con menos de 100 casos de estudio pasan a OTRO (D45). Reingreso a 30 días menor y mayor entre los valores con 1.000 casos o más:

| Variable | Valores | Juntados en OTRO | Menor reingreso | Mayor reingreso |
|---|---|---|---|---|
| `TIPO_ALTA` | 5 | — | DOMICILIO: 5,57 % | FUGA DEL PACIENTE: 20,09 % |
| `ESPECIALIDAD_INTERVENCION` | 48 | 36 (694 casos) | MATRONAS(ES): 1,06 % | ANESTESIOLOGÍA: 13,49 % |
| `ESPECIALIDAD` | 59 | 23 (250 casos) | CIRUGÍA Y TRAUMATOLOGÍA BUCO MAXILOFACIAL: 1,61 % | HEMATO-ONCOLOGÍA PEDIÁTRICA: 23,11 % |
| `TIPO_PROCEDENCIA` | 18 | 2 (4 casos) | CARDIOCIRUGÍA PAGO GRD: 1,52 % | HOSPITALIZACIÓN DOMICILIARIA: 13,17 % |
| `SERVICIO_INGRESO` | 85 | 8 (248 casos) | PENSIONADO MATERNIDAD: 1,08 % | ONCOLOGÍA: 13,22 % |
| `SERVICIO_ALTA` | 83 | 8 (170 casos) | PENSIONADO MATERNIDAD: 1,07 % | ONCOLOGÍA: 15,55 % |
| `HOSPITAL` | 72 | — | 110110: 3,15 % | 116107: 14,35 % |
| `PUEBLO_ORIGINARIO` | 3 | — | SÍ: 5,64 % | NO: 5,90 % |
| `NACIONALIDAD_EXTRANJERA` | 3 | — | SÍ: 3,81 % | NO: 6,04 % |

| Variable | Casos y reingreso a 30 días por valor |
|---|---|
| `SEVERIDAD` | 1: 1.766.981 casos (3,89 %) · 2: 930.253 casos (7,09 %) · 3: 656.884 casos (9,62 %) |
| `RIESGO_MORTALIDAD` | 1: 2.222.887 casos (4,16 %) · 2: 617.924 casos (8,24 %) · 3: 513.307 casos (10,63 %) |
| `UCI_UTI` | 0: 2.879.698 casos (5,55 %) · 1: 474.420 casos (8,05 %) |
| `TRASLADO` | 0: 3.297.951 casos (5,85 %) · 1: 56.167 casos (8,82 %) |

Reingreso a 30 días según el número de diagnósticos y de procedimientos:

| Variable | Reingreso a 30 días por tramo |
|---|---|
| `N_DIAGNOSTICOS` | 0 a 1: 3,46 % · 2 a 3: 4,10 % · 4 a 5: 4,99 % · 6 a 7: 6,19 % · 8 a 9: 7,72 % · 10 a 12: 9,87 % · 13 o más: 13,01 % |
| `N_PROCEDIMIENTOS` | 0: 8,90 % · 1 a 4: 4,89 % · 5 a 9: 4,95 % · 10 a 14: 6,43 % · 15 a 20: 9,41 % · 21 o más: 10,79 % |

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
| `ESPECIALIDAD` | ANESTESIOLOGÍA | 48 |
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
| `indice_comorbilidad` | `ELIXHAUSER` | Índice de la columna INDICE_COMORBILIDAD. ELIXHAUSER = número de condiciones de Elixhauser presentes (códigos de Quan et al. 2005). CHARLSON = puntaje de Charlson con los pesos de Quan et al. (2011), para la comparación. El reporte siempre muestra los dos (script 15) |
| `casos_minimos_categoria` | `100` | En las variables del CMBD tomadas tal cual, los valores con menos de estos casos de estudio se juntan en OTRO: el mismo mínimo del filtro de códigos (D45, script 15) |
| `servicios_criticos` | `CUIDADOS INTENSIVOS / (UCI) / TRATAMIENTO INTERMEDIO / TRATAMIENTOS INTERMEDIOS / UTI ADULTOS / CUIDADOS INTERMEDIOS` | Textos que marcan una unidad de cuidados intensivos o de tratamiento intermedio en los servicios de ingreso, de traslado interno o de alta, separados por una barra vertical (script 15) |
| `servicios_criticos_excluidos` | `PSIQUIATR` | Textos que anulan la marca anterior: las áreas de «cuidados intensivos en psiquiatría» no son unidades de paciente crítico (script 15) |
| `etnia_sin_pueblo` | `NINGUNO / OTRO` | Valores de ETNIA que no nombran un pueblo originario. Se juntan porque se intercambian entre años (script 15) |
| `nacionalidad_local` | `CHILE` | Valor de NACIONALIDAD que no es extranjero (script 15) |

De `2.2_depuracion_etiquetado/reglas/parametros.csv` (regla de «no planificado», D20 y D33): `ingresos_no_planificados` = `URGENCIA / OBSTETRICA`; `grd_parto` = `146 / 147`; `diagnosticos_sesion` = `Z51`.

## 6. Verificaciones

- El conjunto de desarrollo es el de la versión 2 registrada de la partición: **sí**.
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
- El índice de Elixhauser está entre 0 y 28 condiciones y el de Charlson entre 0 y 24 puntos: **sí**.
- Después de las jerarquías, ningún caso tiene a la vez una condición y la versión que esta reemplaza: **sí**.
- En las columnas agrupadas no queda ningún valor propio con menos del mínimo de casos (OTRO puede tener menos): **sí**.
- Lo releído de variables_casos.parquet es igual a lo calculado: **sí**.
