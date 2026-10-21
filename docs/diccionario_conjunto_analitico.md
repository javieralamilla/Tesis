# Diccionario del conjunto analítico

Conjunto analítico: `data/processed/grd_etiquetado.parquet`. Es la tabla que usan la partición y las etapas siguientes. Tiene 5.800.973 registros (un registro por egreso hospitalario, de 2019 a 2024) y 163 columnas; 4.192.410 registros son caso de estudio (`ES_CASO_ESTUDIO`). Generado por `2.2_depuracion_etiquetado/scripts/12_diccionario_version.py`.

## Versión del conjunto

| Dato | Valor |
|---|---|
| Versión | 2 |
| Fecha de registro | 2026-10-20 |
| Registros, columnas y casos de estudio | 5.800.973, 163 y 4.192.410 |
| SHA-256 del archivo | `f9b8be4065bad16dfe27a46a95db4f742024b1e817046d1d9b26e0a893b900dc` |
| SHA-256 de la tabla integrada (`grd_2019_2024.parquet`) | `805f4dbac473b150130a5f50b1af5a895cfe4f2b498630ac58dd1148120cf684` |
| SHA-256 de `criterios_exclusion.csv` | `1d8bc19ad058d4a69d5bb21d89fe7e7cfd1e95cdb3060c8e66157c70738e1426` |
| SHA-256 de `parametros.csv` | `b97db71394bee5b0d24de8f6a84848d38def4d1e367e1c173f2336de7dd0661b` |
| SHA-256 de `08_depurar.py` | `d864ce0cdd0bae868990507ee23a4767d53a11f2de92752461a4229549dec076` |
| SHA-256 de `09_etiquetar.py` | `dfbe07b74c5638aa3325ee635e806b8bf542e9543ef512586564c504cb23138a` |
| Bibliotecas | Python 3.14.5, pandas 3.0.3, pyarrow 25.0.1 |

El historial de versiones está en `docs/version_conjunto_analitico.csv`. El hash identifica el archivo exacto: la partición (actividad 2.3) debe comprobar que el archivo que lee es el de la última versión registrada. Si se vuelven a ejecutar los scripts 08 o 09 y el archivo cambia, hay que ejecutar de nuevo este script para registrar la nueva versión. Con otras versiones de las bibliotecas el archivo puede tener otro hash aunque su contenido sea el mismo.

## Cómo leer este diccionario

- **Secciones 1 a 6:** columnas de la tabla integrada (`docs/diccionario_datos.md`), sin `DUP_EXACTO` ni `DUP_CLAVE`, porque el script 08 elimina los duplicados. **Secciones 7 a 9:** columnas que agregan los scripts 08 y 09.
- **Sin dato:** la ausencia de información se guarda como valor nulo en todas las columnas.
- **Valores:** en las columnas con pocas categorías se listan todas, con su porcentaje sobre los registros con dato; en las demás, las más frecuentes o el rango.
- **% con dato:** porcentaje de registros con valor (de celdas, en las columnas repetidas). Entre paréntesis, el mínimo y el máximo por año cuando varía. Las variables objetivo solo tienen dato en los casos de estudio.
- **Origen:** *Original* (viene de los archivos del DEIS), *Renombrada*, *Creada* (agregada en el procesamiento; se indica el script cuando es de la actividad 2.2) o *Trazabilidad* (permite volver al archivo original).
- **Para el modelado:** las columnas de la sección 9 describen lo que ocurre después del alta. Las cuatro `REING_*` son las variables objetivo; `DIAS_REING` e `ID_EGRESO_REING` nunca son predictoras. `ID_PERSONA` es la unidad para agrupar la partición y la validación cruzada.
- Las descripciones de las secciones 1 a 6 se elaboraron a partir del informe, de las tablas auxiliares del DEIS y del contenido de cada columna; deben contrastarse con la documentación oficial de la base GRD.
- Los criterios y los umbrales están en `2.2_depuracion_etiquetado/reglas/`, las cifras en `2.2_depuracion_etiquetado/reportes/` y las decisiones en `2.2_depuracion_etiquetado/bitacora.md` y `docs/bitacora.md`.

## 1. Identificación y trazabilidad

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `ID_EGRESO` | Entero | Identificador único del egreso. Se forma con el año del archivo y el número de línea del txt original (año × 10.000.000 + línea). | Identificador | 100 | Creada |
| `ANIO_ARCHIVO` | Entero | Año del archivo de origen. Coincide con el año de la fecha de alta. | `2019` 19,83 % · `2020` 13,42 % · `2021` 14,07 % · `2022` 16,07 % · `2023` 17,91 % · `2024` 18,70 % | 100 | Trazabilidad |
| `ARCHIVO_ORIGEN` | Texto | Nombre del archivo txt del que proviene el registro. | `GRD_PUBLICO_2019.txt` 19,83 % · `GRD_PUBLICO_2024.txt` 18,70 % · `GRD_PUBLICO_2023.txt` 17,91 % · `GRD_PUBLICO_EXTERNO_2022.txt` 16,07 % · `GRD_PUBLICO_2021.txt` 14,07 % · `GRD_PUBLICO_2020.txt` 13,42 % | 100 | Trazabilidad |
| `FILA_ORIGEN` | Entero | Número de línea del registro en el txt original (la línea 1 es el encabezado). | De 2 a 1.151.476 | 100 | Trazabilidad |

## 2. Paciente

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `ID_PACIENTE` | Entero | Identificador encriptado del paciente. En los archivos originales se llama CIP_ENCRIPTADO (2019 a 2023) e ID_BENEFICIARIO (2024). Solo permite seguir a un paciente dentro de un mismo BLOQUE_ID. | Identificador | 99,69 (99,28 a 99,90 según el año) | Renombrada |
| `BLOQUE_ID` | Texto | Sistema de identificador de paciente: A corresponde a 2019 y 2020, B a 2021 en adelante. Los identificadores de un bloque no se pueden vincular con los del otro. | `B` 66,74 % · `A` 33,26 % | 100 | Creada |
| `SEXO` | Texto | Sexo del paciente. | `MUJER` 58,83 % · `HOMBRE` 41,17 % | 99,99 | Original |
| `FECHA_NACIMIENTO` | Fecha | Fecha de nacimiento del paciente. | Del 10-08-1894 al 31-12-2024 | >99,99 | Original |
| `ETNIA` | Texto | Pueblo originario al que declara pertenecer el paciente. NINGUNO y OTRO no son comparables entre años: en 2022 y 2023 casi todos los registros figuran como OTRO. | `NINGUNO` 57,04 % · `OTRO` 40,78 % · `MAPUCHE` 1,74 % · `AYMARA` 0,19 % · `RAPA NUI (PASCUENSE)` 0,07 % · `DIAGUITA` 0,06 % · `KAWÉSQAR` 0,05 % · `QUECHUA` 0,03 % · `YAGÁN (YÁMANA)` 0,02 % · `LICAN ANTAI (ATACAMEÑO)` 0,01 % · `COLLA` 0,01 % | >99,99 | Original |
| `NACIONALIDAD` | Texto | Nacionalidad del paciente. Desde 2020 algunos registros indican un continente en lugar de un país. | 214 valores distintos. Más frecuentes: `CHILE`, `VENEZUELA (REPÚBLICA BOLIVARIANA DE)`, `PERÚ`, `BOLIVIA (ESTADO PLURINACIONAL DE)`, `HAITÍ` | 99,59 (98,21 a 100 según el año) | Original |
| `PROVINCIA` | Texto | Provincia de residencia del paciente. | 57 valores distintos. Más frecuentes: `SANTIAGO`, `CONCEPCION`, `CAUTIN`, `VALPARAISO`, `CORDILLERA` | 99,96 (99,92 a >99,99 según el año) | Original |
| `COMUNA` | Texto | Comuna de residencia del paciente. | 346 valores distintos. Más frecuentes: `PUENTE ALTO`, `LA FLORIDA`, `MAIPU`, `VALPARAISO`, `ARICA` | 99,98 (99,92 a >99,99 según el año) | Original |
| `SERVICIO_SALUD` | Texto | Servicio de Salud asociado al paciente, no al establecimiento: un mismo hospital atiende pacientes de varios servicios. | 29 valores distintos. Más frecuentes: `METROPOLITANO SURORIENTE`, `DEL MAULE`, `METROPOLITANO OCCIDENTE`, `METROPOLITANO SUR`, `METROPOLITANO CENTRAL` | 99,96 (99,93 a 99,99 según el año) | Original |
| `PREVISION` | Texto | Previsión de salud del paciente (tramos de FONASA, ISAPRE y otras). | `FONASA INSTITUCIONAL - (MAI) B` 46,12 % · `FONASA INSTITUCIONAL - (MAI) A` 23,73 % · `FONASA INSTITUCIONAL - (MAI) D` 14,24 % · `FONASA INSTITUCIONAL - (MAI) C` 12,04 % · `FONASA LIBRE ELECCIÓN (FMLE_B)` 0,98 % · `ISAPRE` 0,80 % · `PARTICULAR` 0,76 % · `FONASA LIBRE ELECCIÓN (FMLE_D)` 0,63 % · `FONASA LIBRE ELECCIÓN (FMLE_C)` 0,33 % · `DIPRECA` 0,22 % · `CAPREDENA` 0,09 % · `CAJA DE PREVISIÓN FFAA (SISA)` 0,06 % | 99,91 (99,65 a >99,99 según el año) | Original |

## 3. Episodio de hospitalización

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `COD_HOSPITAL` | Texto | Código del establecimiento donde ocurre el egreso. Los nombres están en la hoja Hospitales de la tabla maestra del DEIS. | 72 valores distintos. Más frecuentes: `114101`, `118100`, `116105`, `113100`, `109100` | 100 | Original |
| `TIPO_ACTIVIDAD` | Texto | Tipo de atención. HOSPITALIZACIÓN DIURNA y HOSPITALIZACIÓN EN URGENCIA solo existen en 2019. | `HOSPITALIZACIÓN` 82,71 % · `CIRUGÍA MAYOR AMBULATORIA (CMA)` 15,26 % · `HOSPITALIZACIÓN EN URGENCIA` 1,08 % · `HOSPITALIZACIÓN DIURNA` 0,95 % | >99,99 | Original |
| `TIPO_INGRESO` | Texto | Forma de ingreso del paciente: por urgencia, programada u obstétrica. | `URGENCIA` 51,29 % · `PROGRAMADA` 32,74 % · `OBSTETRICA` 15,97 % | 99,99 | Original |
| `TIPO_PROCEDENCIA` | Texto | Lugar o programa desde el que llega el paciente (servicio de emergencia, centro de especialidades, otro hospital, etc.). | 18 valores distintos. Más frecuentes: `SERVICIO EMERGENCIA (DOMICILIO)`, `CENTRO ESPECIALIDADES (CDT, CRS, CONSULTORIO ADOS. ESP)`, `OTROS HOSPITALES DE LA RED`, `APS URGENCIA (SAPU, SUR, SUC)`, `CONSULTA PRIVADA` | 99,94 (99,62 a >99,99 según el año) | Original |
| `HOSPPROCEDENCIA` | Texto | Establecimiento de procedencia cuando el paciente llega desde otro establecimiento. Los nombres no están unificados entre años. | 518 valores distintos. Más frecuentes: `HOSPITAL SAN PABLO (COQUIMBO)`, `HOSPITAL CLÍNICO DE MAGALLANES DR. LAUTARO NAVARRO AVARIA`, `HOSPITAL SAN JOSÉ (CORONEL)`, `HOSPITAL CARLOS VAN BUREN (VALPARAÍSO)`, `HOSPITAL DR. HERNÁN HENRÍQUEZ ARAVENA (TEMUCO)` | 12,07 (8,54 a 14,31 según el año) | Original |
| `ESPECIALIDAD_MEDICA` | Texto | Especialidad médica asociada al episodio. Los nombres propios de 2019 se llevaron a los usados desde 2020. | 84 valores distintos. Más frecuentes: `OBSTETRICIA Y GINECOLOGÍA`, `CIRUGÍA GENERAL`, `MEDICINA INTERNA`, `TRAUMATOLOGÍA Y ORTOPEDIA`, `PEDIATRÍA` | >99,99 | Original |
| `FECHA_INGRESO` | Fecha | Fecha de ingreso al establecimiento. | Del 25-01-2011 al 31-12-2024 | >99,99 | Original |
| `SERVICIOINGRESO` | Texto | Servicio clínico o unidad de ingreso. | 92 valores distintos. Más frecuentes: `CIRUGÍA`, `UNIDAD DE RECUPERACIÓN DE PABELLONES (CENTRAL Y CMA)`, `MEDICINA`, `OBSTETRICIA`, `PEDIATRÍA` | 99,52 (99,25 a 99,98 según el año) | Original |
| `FECHATRASLADO1` a `FECHATRASLADO9` | Fecha | Fecha de cada traslado entre servicios durante la hospitalización (hasta 9). | Del 15-02-2011 al 31-12-2024 | 2,87 (2,37 a 3,59 según el año) | Original |
| `SERVICIOTRASLADO1` a `SERVICIOTRASLADO9` | Texto | Servicio clínico de destino de cada traslado interno. Algunos valores de 2021, 2022 y 2024 son códigos numéricos sin diccionario. | 109 valores distintos. Más frecuentes: `MEDICINA`, `UNIDAD DE TRATAMIENTO INTERMEDIO (UTI) (INDIFERENCIADO) ADULTO`, `CIRUGÍA`, `PUERPERIO`, `UNIDAD DE CUIDADOS INTENSIVOS ADULTO` | 2,86 (2,37 a 3,59 según el año) | Original |
| `FECHAALTA` | Fecha | Fecha de alta. Define el año del archivo. | Del 01-01-2019 al 31-12-2024 | >99,99 | Original |
| `SERVICIOALTA` | Texto | Servicio clínico desde el que egresa el paciente. | 89 valores distintos. Más frecuentes: `CIRUGÍA`, `MEDICINA`, `UNIDAD DE RECUPERACIÓN DE PABELLONES (CENTRAL Y CMA)`, `OBSTETRICIA`, `PEDIATRÍA` | 99,58 (99,31 a 99,97 según el año) | Original |
| `TIPOALTA` | Texto | Destino o condición del paciente al alta (domicilio, fallecido, derivación a otro establecimiento, etc.). | `DOMICILIO` 89,62 % · `FALLECIDO` 2,94 % · `HOSPITALIZACIÓN DOMICILIARIA` 2,39 % · `DERIVACIÓN OTRO HOSPITAL DEL SERVICIO` 2,12 % · `ALTA VOLUNTARIA` 1,00 % · `DERIVACIÓN OTRO HOSPITAL DE LA RED NACIONAL` 0,77 % · `DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE` 0,38 % · `FUGA DEL PACIENTE` 0,33 % · `DERIVACIÓN INST. PRIVADA (COMPRA DE SERVICIOS` 0,32 % · `DERIVACIÓN INST. PRIVADA (VOLUNTARIO)` 0,13 % | >99,99 | Original |
| `MEDICOALTA_ENCRIPTADO` | Entero | Identificador encriptado del médico que da el alta. Cambia de sistema entre 2020 y 2021, igual que el identificador de paciente. | Identificador | 99,94 (99,79 a 100 según el año) | Original |

## 4. Diagnósticos, procedimientos e intervención

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `DIAGNOSTICO1` | Texto | Diagnóstico principal, codificado en CIE-10. | 9.710 valores distintos. Más frecuentes: `H26.9`, `K80.2`, `U07.1`, `K35.8`, `O80.0` | 99,80 (99,25 a 100 según el año) | Original |
| `DIAGNOSTICO2` a `DIAGNOSTICO35` | Texto | Diagnósticos secundarios, codificados en CIE-10. | 17.376 valores distintos. Más frecuentes: `I10`, `E11.9`, `Z37.0`, `Z92.2`, `Z92.4` | 12,57 (9,93 a 14,04 según el año) | Original |
| `PROCEDIMIENTO1` a `PROCEDIMIENTO30` | Texto | Procedimientos realizados, codificados en CIE-9-MC. | 3.799 valores distintos. Más frecuentes: `99.29`, `90.59`, `99.21`, `99.19`, `89.52` | 26,77 (22,47 a 30,16 según el año) | Original |
| `FECHAINTERV1` | Fecha | Fecha de la primera intervención quirúrgica. | Del 11-02-0020 al 20-10-2090 | 50,16 (48,65 a 51,16 según el año) | Original |
| `MEDICOINTERV1_ENCRIPTADO` | Entero | Identificador encriptado del médico de la primera intervención. | Identificador | 55,08 (52,45 a 57,63 según el año) | Original |
| `ESPECIALIDADINTERVENCION` | Texto | Especialidad del profesional que realiza la intervención. | 85 valores distintos. Más frecuentes: `CIRUGÍA GENERAL`, `OBSTETRICIA Y GINECOLOGÍA`, `TRAUMATOLOGÍA Y ORTOPEDIA`, `OFTALMOLOGÍA`, `MATRONAS(ES)` | 55,14 (52,64 a 57,57 según el año) | Original |
| `USOSPABELLON` | Entero | Tipo de pabellón utilizado, según la hoja Tipo de Pabellón de la tabla maestra: 1 central u obstétrico, 2 ambulatorio, 3 sala de procedimiento, 4 hemodinamia, 5 urgencia, 6 urgencia habilitado en UCI, 7 hospital de campaña, 8 operativos especiales. Casi sin datos en 2020. En 2019 hay valores fuera del rango 1 a 8. | 39 valores distintos. Más frecuentes: `1`, `2`, `3`, `4`, `5` | 50,98 (0,01 a 61,09 según el año) | Original |

## 5. Clasificación GRD

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `IR_29301_COD_GRD` | Texto | Código IR-GRD asignado al egreso. Tiene 6 dígitos y se guarda como texto para conservar los ceros iniciales. Las descripciones están en la hoja IR - GRD de la tabla maestra. | 1.063 valores distintos. Más frecuentes: `022360`, `146101`, `146121`, `146131`, `061131` | >99,99 | Original |
| `CDM` | Texto | Categoría Diagnóstica Mayor: los 2 primeros dígitos del código GRD (01 a 23, y 99 para los inagrupables). | 24 valores distintos. Más frecuentes: `14`, `04`, `06`, `08`, `13` | >99,99 | Creada |
| `IR_29301_PESO` | Decimal | Peso relativo del GRD. | De 0 a 20,6461 | >99,99 | Original |
| `IR_29301_SEVERIDAD` | Entero | Nivel de severidad del GRD: 0 sin gravedad, 1 menor, 2 moderada, 3 mayor. | `0` 16,22 % · `1` 41,60 % · `2` 23,05 % · `3` 19,13 % | >99,99 | Original |
| `IR_29301_MORTALIDAD` | Entero | Nivel de riesgo de mortalidad del GRD, en la misma escala de 0 a 3. | `0` 16,22 % · `1` 52,09 % · `2` 16,23 % · `3` 15,46 % | >99,99 | Original |

## 6. Recién nacido

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `CONDICIONDEALTANEONATO1` a `CONDICIONDEALTANEONATO4` | Texto | Condición al alta de cada recién nacido (VIVO o FALLECIDO). Solo se informó en 2019. | `VIVO` 99,36 % · `FALLECIDO` 0,64 % | 0,56 (0 a 2,84 según el año) | Original |
| `PESORN1` a `PESORN4` | Entero | Peso de cada recién nacido, en gramos. | De 0 a 9.834 | 3,47 (2,79 a 4,34 según el año) | Original |
| `SEXORN1` a `SEXORN4` | Texto | Sexo de cada recién nacido. | `HOMBRE` 50,76 % · `MUJER` 49,24 % | 2,82 (2,27 a 3,54 según el año) | Original |
| `RN1ESTADO` a `RN4ESTADO` | Entero | Valor numérico asociado a cada recién nacido. Su significado no está documentado en las tablas disponibles. En 2019 y 2020 el 0 aparece también en episodios sin recién nacido. | 13 valores distintos. Más frecuentes: `0`, `9`, `10`, `8`, `7` | 26,87 (2,29 a >99,99 según el año) | Original |

## 7. Persona y episodio asistencial

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `ID_PERSONA` | Entero | Persona a la que corresponde el egreso, dentro de su bloque de identificador: `ID_PACIENTE` × 100 + número de persona (01 la de más edad). Separa a las personas distintas que comparten un identificador (bitácora D18). Sin dato en los egresos sin identificador o con identificador genérico. Es la unidad para agrupar la partición y la validación cruzada; no es una variable predictora. | Identificador | 99,65 (99,26 a 99,89 según el año) | Creada (script 08) |
| `IDENTIDAD_AMBIGUA` | Verdadero/falso | Verdadero si el identificador del egreso aparece con más de un sexo o con más de una fecha de nacimiento, sin contar los datos faltantes: la persona se asignó con una regla operativa y no con certeza (bitácora H21 y D34). Permite repetir un análisis sin esos egresos. | Verdadero en 96.824 registros | 100 | Creada (script 08) |
| `ID_EPISODIO` | Entero | Episodio asistencial: `ID_EGRESO` del primer egreso del episodio. Une los egresos que son tramos de una misma hospitalización, como los traslados entre hospitales (bitácora D19). Sin dato en los egresos que no se pueden seguir. | Identificador | 97,63 (89,09 a 99,89 según el año) | Creada (script 08) |
| `N_EGRESOS_EPISODIO` | Entero | Número de egresos que forman el episodio asistencial. | De 1 a 32 | 97,63 (89,09 a 99,89 según el año) | Creada (script 08) |
| `CONTINUA_EPISODIO` | Verdadero/falso | Verdadero si el egreso continúa un episodio abierto por un egreso anterior (por ejemplo, la llegada de un traslado). No cuenta como reingreso. | Verdadero en 97.603 registros | 100 | Creada (script 08) |
| `ALTA_FINAL_EPISODIO` | Verdadero/falso | Verdadero si el egreso es el alta final de su episodio asistencial. Solo el alta final puede ser caso de estudio. | Verdadero en 5.565.982 registros | 100 | Creada (script 08) |

## 8. Criterios de exclusión y papeles del egreso

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `EXC_SIN_ID` | Verdadero/falso | Criterio E01 (activo): Sin identificador de paciente. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 17.864 registros | 100 | Creada (script 08) |
| `EXC_ID_GENERICO` | Verdadero/falso | Criterio E02 (activo): Identificador genérico: lo usan muchas personas distintas. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 2.481 registros | 100 | Creada (script 08) |
| `EXC_FECHAS` | Verdadero/falso | Criterio E03 (activo): Sin fecha de ingreso o de alta, o con el alta anterior al ingreso. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 83 registros | 100 | Creada (script 08) |
| `EXC_ACTIVIDAD_2019` | Verdadero/falso | Criterio E04 (activo): Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 117.586 registros | 100 | Creada (script 08) |
| `EXC_TRAMO_EPISODIO` | Verdadero/falso | Criterio E05 (activo): Tramo de un traslado: no es el alta final de su episodio asistencial. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 97.603 registros | 100 | Creada (script 08) |
| `EXC_FALLECIDO` | Verdadero/falso | Criterio E06 (activo): Alta por fallecimiento. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 170.563 registros | 100 | Creada (script 08) |
| `EXC_DERIVADO_HOSPITAL` | Verdadero/falso | Criterio E07 (activo): Alta por derivación a otro hospital. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 167.418 registros | 100 | Creada (script 08) |
| `EXC_DERIVADO_PRIVADO` | Verdadero/falso | Criterio E08 (activo): Alta por derivación a una institución privada. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 26.081 registros | 100 | Creada (script 08) |
| `EXC_SIN_GRD` | Verdadero/falso | Criterio E09 (activo): Sin GRD válido: sin código GRD o con CDM 99. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 5.042 registros | 100 | Creada (script 08) |
| `EXC_DATOS_FALTANTES` | Verdadero/falso | Criterio E10 (activo): Sin fecha de nacimiento válida (falta, es posterior al ingreso o la edad supera el máximo) o sin tipo de alta. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 149 registros | 100 | Creada (script 08) |
| `EXC_CENSURA` | Verdadero/falso | Criterio E11 (activo): Seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 188.737 registros | 100 | Creada (script 08) |
| `EXC_ALTA_VOLUNTARIA_FUGA` | Verdadero/falso | Criterio E12 (desactivado): Alta voluntaria o fuga del paciente. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 77.385 registros | 100 | Creada (script 08) |
| `EXC_CMA` | Verdadero/falso | Criterio E13 (activo): Cirugía mayor ambulatoria. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 885.384 registros | 100 | Creada (script 08) |
| `EXC_SESION` | Verdadero/falso | Criterio E14 (activo): Sesión de tratamiento: diagnóstico principal Z51. Verdadero si el egreso lo cumple, sin considerar los demás criterios. | Verdadero en 100.229 registros | 100 | Creada (script 08) |
| `MOTIVO_EXCLUSION` | Texto | Código del primer criterio activo que excluye al egreso como caso de estudio, en el orden de `criterios_exclusion.csv`. Sin dato en los casos de estudio. | 13 valores distintos. Más frecuentes: `E13`, `E11`, `E06`, `E04`, `E05` | 27,73 (22,08 a 34,47 según el año) | Creada (script 08) |
| `ES_CASO_ESTUDIO` | Verdadero/falso | Verdadero si el egreso es caso de estudio (egreso índice): no cumple ningún criterio de exclusión activo. Las variables objetivo solo tienen dato en estos egresos. | Verdadero en 4.192.410 registros | 100 | Creada (script 08) |
| `PUEDE_SER_REINGRESO` | Verdadero/falso | Verdadero si el egreso puede contar como reingreso de un alta anterior: se puede seguir y abre un episodio asistencial. Un egreso excluido como caso de estudio, por ejemplo un fallecido, puede serlo. | Verdadero en 5.565.982 registros | 100 | Creada (script 08) |

## 9. Variables objetivo de reingreso

| Columna | Tipo | Descripción | Valores | % con dato | Origen |
|---|---|---|---|---|---|
| `REING_7D` | Entero | Variable objetivo. Reingreso no planificado dentro de 7 días del alta, por cualquier causa: 1 = sí, 0 = no (bitácora D20, D26 y D33). Con dato solo en los casos de estudio con seguimiento suficiente para la ventana (D30). | `0` 97,93 % · `1` 2,07 % | 72,27 (65,53 a 77,92 según el año) | Creada (script 09) |
| `REING_7D_CDM` | Entero | Variable objetivo. Reingreso no planificado dentro de 7 días, relacionado con el diagnóstico: algún ingreso de la ventana tiene la misma CDM que el caso de estudio (D31). 1 = sí, 0 = no. Con dato en los mismos casos que `REING_7D`, salvo los partos (casos de estudio de la CDM 14), que quedan sin dato porque con la comparación literal no pueden tener un reingreso relacionado (D38). | `0` 98,74 % · `1` 1,26 % | 61,67 (57,52 a 66,37 según el año) | Creada (script 09) |
| `REING_30D` | Entero | Variable objetivo. Reingreso no planificado dentro de 30 días del alta, por cualquier causa: 1 = sí, 0 = no. Incluye a los de 7 días. Con dato solo en los casos de estudio con seguimiento suficiente para la ventana (D30). | `0` 94,10 % · `1` 5,90 % | 70,71 (61,06 a 77,92 según el año) | Creada (script 09) |
| `REING_30D_CDM` | Entero | Variable objetivo. Reingreso no planificado dentro de 30 días, relacionado con el diagnóstico (misma CDM, D31). 1 = sí, 0 = no. Con dato en los mismos casos que `REING_30D`, salvo los partos (casos de estudio de la CDM 14), que quedan sin dato porque con la comparación literal no pueden tener un reingreso relacionado (D38). | `0` 96,45 % · `1` 3,55 % | 60,31 (53,57 a 66,37 según el año) | Creada (script 09) |
| `DIAS_REING` | Entero | Trazabilidad. Días entre el alta del caso de estudio y el primer ingreso posterior que cuenta como reingreso, a cualquier distancia dentro del bloque. Sin dato si no hay ninguno. Describe lo que ocurre después del alta: no debe usarse como variable predictora. | De 0 a 1.454 | 14,39 (7,97 a 21,75 según el año) | Creada (script 09) |
| `ID_EGRESO_REING` | Entero | Trazabilidad. `ID_EGRESO` de ese primer ingreso posterior, para poder revisar cada par. No debe usarse como variable predictora. | Identificador | 14,39 (7,97 a 21,75 según el año) | Creada (script 09) |
