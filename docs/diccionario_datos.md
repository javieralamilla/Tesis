# Diccionario de datos

Tabla integrada: `data/processed/grd_2019_2024.parquet`. Tiene 5.808.536 registros (un registro por egreso hospitalario, de 2019 a 2024) y 136 columnas. Generado por `2.1_integracion_homogenizacion/scripts/07_diccionario_datos.py` con las descripciones de `2.1_integracion_homogenizacion/reglas/descripciones_columnas.csv`.

## Cómo leer este diccionario

- **Sin dato:** la ausencia de información se guarda como valor nulo en todas las columnas.
- **Valores:** en las columnas con pocas categorías se listan todas, con su porcentaje sobre los registros con dato; en las demás, las más frecuentes o el rango.
- **% con dato:** porcentaje de registros con valor (de celdas, en las columnas repetidas). Entre paréntesis, el mínimo y el máximo por año cuando varía.
- **Origen:** *Original* (viene de los archivos del DEIS), *Renombrada*, *Creada* (agregada en el procesamiento) o *Trazabilidad* (permite volver al archivo original).
- Las descripciones se elaboraron a partir del informe, de las tablas auxiliares del DEIS y del contenido de cada columna; deben contrastarse con la documentación oficial de la base GRD.
- Las reglas aplicadas a cada columna están en `2.1_integracion_homogenizacion/reportes/05_homogenizacion.md` y las decisiones, en `docs/bitacora.md`.

## 1. Identificación y trazabilidad

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `ID_EGRESO` | Entero | Identificador único del egreso. Se forma con el año del archivo y el número de línea del txt original (año × 10.000.000 + línea). | Identificador | 100 | Creada |
| `ANIO_ARCHIVO` | Entero | Año del archivo de origen. Coincide con el año de la fecha de alta. | `2019` 19,82 % · `2020` 13,46 % · `2021` 14,06 % · `2022` 16,06 % · `2023` 17,90 % · `2024` 18,69 % | 100 | Trazabilidad |
| `ARCHIVO_ORIGEN` | Texto | Nombre del archivo txt del que proviene el registro. | `GRD_PUBLICO_2019.txt` 19,82 % · `GRD_PUBLICO_2024.txt` 18,69 % · `GRD_PUBLICO_2023.txt` 17,90 % · `GRD_PUBLICO_EXTERNO_2022.txt` 16,06 % · `GRD_PUBLICO_2021.txt` 14,06 % · `GRD_PUBLICO_2020.txt` 13,46 % | 100 | Trazabilidad |
| `FILA_ORIGEN` | Entero | Número de línea del registro en el txt original (la línea 1 es el encabezado). | De 2 a 1.151.476 | 100 | Trazabilidad |
| `DUP_EXACTO` | Verdadero/falso | Verdadero si el registro es copia idéntica de un registro anterior del mismo año, con todas las columnas de datos iguales. | Verdadero en 3.818 registros | 100 | Creada |
| `DUP_CLAVE` | Verdadero/falso | Verdadero si el registro comparte paciente, hospital, fecha de ingreso y fecha de alta con otro registro. Solo se evalúa cuando esos cuatro datos existen. | Verdadero en 15.734 registros | 100 | Creada |

## 2. Paciente

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `ID_PACIENTE` | Entero | Identificador encriptado del paciente. En los archivos originales se llama CIP_ENCRIPTADO (2019 a 2023) e ID_BENEFICIARIO (2024). Solo permite seguir a un paciente dentro de un mismo BLOQUE_ID. | Identificador | 99,69 (99,28 a 99,90 según el año) | Renombrada |
| `BLOQUE_ID` | Texto | Sistema de identificador de paciente: A corresponde a 2019 y 2020, B a 2021 en adelante. Los identificadores de un bloque no se pueden vincular con los del otro. | `B` 66,71 % · `A` 33,29 % | 100 | Creada |
| `SEXO` | Texto | Sexo del paciente. | `MUJER` 58,83 % · `HOMBRE` 41,17 % | 99,99 | Original |
| `FECHA_NACIMIENTO` | Fecha | Fecha de nacimiento del paciente. | Del 10-08-1894 al 31-12-2024 | >99,99 | Original |
| `ETNIA` | Texto | Pueblo originario al que declara pertenecer el paciente. NINGUNO y OTRO no son comparables entre años: en 2022 y 2023 casi todos los registros figuran como OTRO. | `NINGUNO` 57,05 % · `OTRO` 40,75 % · `MAPUCHE` 1,76 % · `AYMARA` 0,19 % · `RAPA NUI (PASCUENSE)` 0,07 % · `DIAGUITA` 0,06 % · `KAWÉSQAR` 0,05 % · `QUECHUA` 0,03 % · `YAGÁN (YÁMANA)` 0,02 % · `COLLA` 0,01 % · `LICAN ANTAI (ATACAMEÑO)` 0,01 % | >99,99 | Original |
| `NACIONALIDAD` | Texto | Nacionalidad del paciente. Desde 2020 algunos registros indican un continente en lugar de un país. | 214 valores distintos. Más frecuentes: `CHILE`, `VENEZUELA (REPÚBLICA BOLIVARIANA DE)`, `PERÚ`, `BOLIVIA (ESTADO PLURINACIONAL DE)`, `HAITÍ` | 99,59 (98,21 a 100 según el año) | Original |
| `PROVINCIA` | Texto | Provincia de residencia del paciente. | 57 valores distintos. Más frecuentes: `SANTIAGO`, `CONCEPCION`, `CAUTIN`, `CORDILLERA`, `VALPARAISO` | 99,96 (99,92 a >99,99 según el año) | Original |
| `COMUNA` | Texto | Comuna de residencia del paciente. | 346 valores distintos. Más frecuentes: `PUENTE ALTO`, `LA FLORIDA`, `MAIPU`, `VALPARAISO`, `ARICA` | 99,98 (99,92 a >99,99 según el año) | Original |
| `SERVICIO_SALUD` | Texto | Servicio de Salud asociado al paciente, no al establecimiento: un mismo hospital atiende pacientes de varios servicios. | 29 valores distintos. Más frecuentes: `METROPOLITANO SURORIENTE`, `DEL MAULE`, `METROPOLITANO OCCIDENTE`, `METROPOLITANO SUR`, `METROPOLITANO CENTRAL` | 99,96 (99,93 a 99,99 según el año) | Original |
| `PREVISION` | Texto | Previsión de salud del paciente (tramos de FONASA, ISAPRE y otras). | `FONASA INSTITUCIONAL - (MAI) B` 46,14 % · `FONASA INSTITUCIONAL - (MAI) A` 23,72 % · `FONASA INSTITUCIONAL - (MAI) D` 14,24 % · `FONASA INSTITUCIONAL - (MAI) C` 12,03 % · `FONASA LIBRE ELECCIÓN (FMLE_B)` 0,98 % · `ISAPRE` 0,80 % · `PARTICULAR` 0,76 % · `FONASA LIBRE ELECCIÓN (FMLE_D)` 0,63 % · `FONASA LIBRE ELECCIÓN (FMLE_C)` 0,32 % · `DIPRECA` 0,22 % · `CAPREDENA` 0,09 % · `CAJA DE PREVISIÓN FFAA (SISA)` 0,06 % | 99,91 (99,65 a >99,99 según el año) | Original |

## 3. Episodio de hospitalización

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `COD_HOSPITAL` | Texto | Código del establecimiento donde ocurre el egreso. Los nombres están en la hoja Hospitales de la tabla maestra del DEIS. | 72 valores distintos. Más frecuentes: `114101`, `118100`, `116105`, `113100`, `109100` | 100 | Original |
| `TIPO_ACTIVIDAD` | Texto | Tipo de atención. HOSPITALIZACIÓN DIURNA y HOSPITALIZACIÓN EN URGENCIA solo existen en 2019. | `HOSPITALIZACIÓN` 82,65 % · `CIRUGÍA MAYOR AMBULATORIA (CMA)` 15,32 % · `HOSPITALIZACIÓN EN URGENCIA` 1,08 % · `HOSPITALIZACIÓN DIURNA` 0,95 % | >99,99 | Original |
| `TIPO_INGRESO` | Texto | Forma de ingreso del paciente: por urgencia, programada u obstétrica. | `URGENCIA` 51,26 % · `PROGRAMADA` 32,79 % · `OBSTETRICA` 15,95 % | 99,99 | Original |
| `TIPO_PROCEDENCIA` | Texto | Lugar o programa desde el que llega el paciente (servicio de emergencia, centro de especialidades, otro hospital, etc.). | 18 valores distintos. Más frecuentes: `SERVICIO EMERGENCIA (DOMICILIO)`, `CENTRO ESPECIALIDADES (CDT, CRS, CONSULTORIO ADOS. ESP)`, `OTROS HOSPITALES DE LA RED`, `APS URGENCIA (SAPU, SUR, SUC)`, `CONSULTA PRIVADA` | 99,94 (99,62 a >99,99 según el año) | Original |
| `HOSPPROCEDENCIA` | Texto | Establecimiento de procedencia cuando el paciente llega desde otro establecimiento. Los nombres no están unificados entre años. | 518 valores distintos. Más frecuentes: `HOSPITAL SAN PABLO (COQUIMBO)`, `HOSPITAL CLÍNICO DE MAGALLANES DR. LAUTARO NAVARRO AVARIA`, `HOSPITAL SAN JOSÉ (CORONEL)`, `HOSPITAL CARLOS VAN BUREN (VALPARAÍSO)`, `HOSPITAL DR. HERNÁN HENRÍQUEZ ARAVENA (TEMUCO)` | 12,07 (8,53 a 14,30 según el año) | Original |
| `ESPECIALIDAD_MEDICA` | Texto | Especialidad médica asociada al episodio. Los nombres propios de 2019 se llevaron a los usados desde 2020. | 84 valores distintos. Más frecuentes: `OBSTETRICIA Y GINECOLOGÍA`, `CIRUGÍA GENERAL`, `MEDICINA INTERNA`, `TRAUMATOLOGÍA Y ORTOPEDIA`, `PEDIATRÍA` | >99,99 | Original |
| `FECHA_INGRESO` | Fecha | Fecha de ingreso al establecimiento. | Del 25-01-2011 al 31-12-2024 | >99,99 | Original |
| `SERVICIOINGRESO` | Texto | Servicio clínico o unidad de ingreso. | 92 valores distintos. Más frecuentes: `CIRUGÍA`, `UNIDAD DE RECUPERACIÓN DE PABELLONES (CENTRAL Y CMA)`, `MEDICINA`, `OBSTETRICIA`, `PEDIATRÍA` | 99,52 (99,25 a 99,98 según el año) | Original |
| `FECHATRASLADO1` a `FECHATRASLADO9` | Fecha | Fecha de cada traslado entre servicios durante la hospitalización (hasta 9). | Del 15-02-2011 al 31-12-2024 | 2,87 (2,37 a 3,58 según el año) | Original |
| `SERVICIOTRASLADO1` a `SERVICIOTRASLADO9` | Texto | Servicio clínico de destino de cada traslado interno. Algunos valores de 2021, 2022 y 2024 son códigos numéricos sin diccionario. | 109 valores distintos. Más frecuentes: `MEDICINA`, `UNIDAD DE TRATAMIENTO INTERMEDIO (UTI) (INDIFERENCIADO) ADULTO`, `CIRUGÍA`, `PUERPERIO`, `UNIDAD DE CUIDADOS INTENSIVOS ADULTO` | 2,86 (2,37 a 3,58 según el año) | Original |
| `FECHAALTA` | Fecha | Fecha de alta. Define el año del archivo. | Del 01-01-2019 al 31-12-2024 | >99,99 | Original |
| `SERVICIOALTA` | Texto | Servicio clínico desde el que egresa el paciente. | 89 valores distintos. Más frecuentes: `CIRUGÍA`, `MEDICINA`, `UNIDAD DE RECUPERACIÓN DE PABELLONES (CENTRAL Y CMA)`, `OBSTETRICIA`, `PEDIATRÍA` | 99,58 (99,31 a 99,97 según el año) | Original |
| `TIPOALTA` | Texto | Destino o condición del paciente al alta (domicilio, fallecido, derivación a otro establecimiento, etc.). | `DOMICILIO` 89,62 % · `FALLECIDO` 2,94 % · `HOSPITALIZACIÓN DOMICILIARIA` 2,39 % · `DERIVACIÓN OTRO HOSPITAL DEL SERVICIO` 2,12 % · `ALTA VOLUNTARIA` 1,00 % · `DERIVACIÓN OTRO HOSPITAL DE LA RED NACIONAL` 0,76 % · `DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE` 0,38 % · `FUGA DEL PACIENTE` 0,33 % · `DERIVACIÓN INST. PRIVADA (COMPRA DE SERVICIOS` 0,32 % · `DERIVACIÓN INST. PRIVADA (VOLUNTARIO)` 0,13 % | >99,99 | Original |
| `MEDICOALTA_ENCRIPTADO` | Entero | Identificador encriptado del médico que da el alta. Cambia de sistema entre 2020 y 2021, igual que el identificador de paciente. | Identificador | 99,94 (99,79 a 100 según el año) | Original |

## 4. Diagnósticos, procedimientos e intervención

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `DIAGNOSTICO1` | Texto | Diagnóstico principal, codificado en CIE-10. | 9.711 valores distintos. Más frecuentes: `H26.9`, `K80.2`, `U07.1`, `K35.8`, `O80.0` | 99,80 (99,25 a 100 según el año) | Original |
| `DIAGNOSTICO2` a `DIAGNOSTICO35` | Texto | Diagnósticos secundarios, codificados en CIE-10. | 17.376 valores distintos. Más frecuentes: `I10`, `E11.9`, `Z37.0`, `Z92.2`, `Z92.4` | 12,57 (9,92 a 14,04 según el año) | Original |
| `PROCEDIMIENTO1` a `PROCEDIMIENTO30` | Texto | Procedimientos realizados, codificados en CIE-9-MC. | 3.800 valores distintos. Más frecuentes: `99.29`, `90.59`, `99.21`, `99.19`, `89.52` | 26,76 (22,46 a 30,15 según el año) | Original |
| `FECHAINTERV1` | Fecha | Fecha de la primera intervención quirúrgica. | Del 11-02-0020 al 20-10-2090 | 50,18 (48,70 a 51,17 según el año) | Original |
| `MEDICOINTERV1_ENCRIPTADO` | Entero | Identificador encriptado del médico de la primera intervención. | Identificador | 55,10 (52,43 a 57,67 según el año) | Original |
| `ESPECIALIDADINTERVENCION` | Texto | Especialidad del profesional que realiza la intervención. | 85 valores distintos. Más frecuentes: `CIRUGÍA GENERAL`, `OBSTETRICIA Y GINECOLOGÍA`, `TRAUMATOLOGÍA Y ORTOPEDIA`, `OFTALMOLOGÍA`, `MATRONAS(ES)` | 55,16 (52,65 a 57,61 según el año) | Original |
| `USOSPABELLON` | Entero | Tipo de pabellón utilizado, según la hoja Tipo de Pabellón de la tabla maestra: 1 central u obstétrico, 2 ambulatorio, 3 sala de procedimiento, 4 hemodinamia, 5 urgencia, 6 urgencia habilitado en UCI, 7 hospital de campaña, 8 operativos especiales. Casi sin datos en 2020. En 2019 hay valores fuera del rango 1 a 8. | 39 valores distintos. Más frecuentes: `1`, `2`, `3`, `4`, `5` | 50,98 (0,01 a 61,12 según el año) | Original |

## 5. Clasificación GRD

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `IR_29301_COD_GRD` | Texto | Código IR-GRD asignado al egreso. Tiene 6 dígitos y se guarda como texto para conservar los ceros iniciales. Las descripciones están en la hoja IR - GRD de la tabla maestra. | 1.063 valores distintos. Más frecuentes: `022360`, `146101`, `146121`, `146131`, `061131` | >99,99 | Original |
| `CDM` | Texto | Categoría Diagnóstica Mayor: los 2 primeros dígitos del código GRD (01 a 23, y 99 para los inagrupables). | 24 valores distintos. Más frecuentes: `14`, `04`, `06`, `08`, `13` | >99,99 | Creada |
| `IR_29301_PESO` | Decimal | Peso relativo del GRD. | De 0 a 20,6461 | >99,99 | Original |
| `IR_29301_SEVERIDAD` | Entero | Nivel de severidad del GRD: 0 sin gravedad, 1 menor, 2 moderada, 3 mayor. | `0` 16,28 % · `1` 41,57 % · `2` 23,03 % · `3` 19,12 % | >99,99 | Original |
| `IR_29301_MORTALIDAD` | Entero | Nivel de riesgo de mortalidad del GRD, en la misma escala de 0 a 3. | `0` 16,28 % · `1` 52,05 % · `2` 16,22 % · `3` 15,45 % | >99,99 | Original |

## 6. Recién nacido

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `CONDICIONDEALTANEONATO1` a `CONDICIONDEALTANEONATO4` | Texto | Condición al alta de cada recién nacido (VIVO o FALLECIDO). Solo se informó en 2019. | `VIVO` 99,36 % · `FALLECIDO` 0,64 % | 0,56 (0 a 2,83 según el año) | Original |
| `PESORN1` a `PESORN4` | Entero | Peso de cada recién nacido, en gramos. | De 0 a 9.834 | 3,46 (2,78 a 4,33 según el año) | Original |
| `SEXORN1` a `SEXORN4` | Texto | Sexo de cada recién nacido. | `HOMBRE` 50,76 % · `MUJER` 49,24 % | 2,82 (2,26 a 3,53 según el año) | Original |
| `RN1ESTADO` a `RN4ESTADO` | Entero | Valor numérico asociado a cada recién nacido. Su significado no está documentado en las tablas disponibles. En 2019 y 2020 el 0 aparece también en episodios sin recién nacido. | 13 valores distintos. Más frecuentes: `0`, `9`, `10`, `8`, `7` | 26,85 (2,28 a >99,99 según el año) | Original |
