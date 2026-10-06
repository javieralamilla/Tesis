# Bitácora de decisiones sobre los datos

Registro de los hallazgos y decisiones tomadas durante el procesamiento de la base GRD.
Las entradas se numeran en orden cronológico y se etiquetan con la actividad de la
Carta Gantt a la que corresponden. Una entrada no se borra: si una decisión cambia,
se agrega una nueva entrada que la reemplaza y se indica en el campo **Estado**.

Esta bitácora cubre las actividades 1.2 (exploración y evaluación de calidad) y 2.1 (integración
y homogenización). Desde la actividad 2.2, cada actividad lleva su propia bitácora dentro de su carpeta.

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer), `C` = corrección al informe.

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Índice por actividad de la Carta Gantt

| Actividad | Entradas |
|---|---|
| 1.2 Exploración y evaluación de calidad | H01, H02, H03, H04, H05, H06, H07, H08, H09, H10, H11, H12 |
| 2.1 Integración y homogenización | D01, D02, D03, D04, D05, D06, D09, D10, D11, D12, D13, D14, D15, D16, D17 |
| 2.2 Depuración y etiquetado del reingreso | D03, D07, D08, D15, H09, H10, H11 |
| Informe | C01, C02, C03 |

---

### D01 · 2026-09-30 · Estructura del proyecto y entorno reproducible
- **Actividad:** 2.1
- **Decisión:** Separar `Tesis\Datos` (originales, solo lectura), `Tesis\Codigo` (repositorio Git con `src/`, `data/`, `reports/`, `docs/`) y `Tesis\Informe seminario`. Entorno virtual en `Codigo\.venv` con versiones fijadas en `requirements.txt` (pandas 3.0.3, pyarrow 25.0.1, openpyxl 3.1.5). Los datos quedan fuera de Git.
- **Evidencia:** `2.1_integracion_homogenizacion/reportes/hashes_originales.txt` (SHA-256 de los 12 archivos originales).
- **Estado:** Adoptada. La organización interna de `Codigo` se actualiza en D17.

### D02 · 2026-09-30 · Fuente de trabajo: archivos .txt
- **Actividad:** 2.1
- **Decisión:** Se trabaja sobre `Datos\txt`; los comprimidos de `Datos\Zip` se conservan como respaldo. El tamaño de cada .txt coincide con el declarado dentro de su .zip (el .rar de 2020 no se verificó). El archivo de 2022 se llama `GRD_PUBLICO_EXTERNO_2022.txt` también dentro del .zip.
- **Pendiente:** Confirmar que "EXTERNO" cubre el mismo universo de hospitales que los demás años.
- **Estado:** Adoptada.

### H01 · 2026-09-30 · Diferencias de formato entre archivos
- **Actividad:** 1.2
- **Hallazgo:** Los seis archivos tienen las mismas 129 columnas en el mismo orden, separador `|` y 5.808.536 registros en total, pero difieren en:

  | Año | Codificación | Fecha ingreso/alta | Peso GRD | Columna ID |
  |---|---|---|---|---|
  | 2019 | UTF-8 | AAAA-MM-DD | `0,5744` | CIP_ENCRIPTADO |
  | 2020 | UTF-8 | AAAA-MM-DD | `1,303` | CIP_ENCRIPTADO |
  | 2021 | UTF-8 con BOM | AAAA-MM-DD | `,3045` | CIP_ENCRIPTADO |
  | 2022 | UTF-16 | AAAA-MM-DD | `2,4156` | CIP_ENCRIPTADO |
  | 2023 | UTF-16 | **DD-MM-AAAA** (nacimiento sí en AAAA-MM-DD) | `0,7094` | CIP_ENCRIPTADO |
  | 2024 | Latin-1 / cp1252 | AAAA-MM-DD | `0,4384` | **ID_BENEFICIARIO** |

  Además, `IR_29301_COD_GRD` tiene ceros a la izquierda y debe leerse como texto.
- **Evidencia:** inspección inicial de encabezados y primeras filas.

### H02 · 2026-09-30 · Dos sistemas de identificador de paciente
- **Actividad:** 1.2
- **Hallazgo:** Bloque A (2019–2020): ID de 4 a 7 dígitos. Bloque B (2021–2024): ID de 8 a 9 dígitos. Dentro de cada bloque, entre 8 y 15 % de los pacientes reaparece en otro año, y entre ellos el 97–98 % coincide en sexo y fecha de nacimiento (misma persona). Entre bloques no hay ninguna coincidencia. El cambio de nombre de la columna en 2024 no implica cambio de identificador: 2024 es compatible con 2021–2023.
- **Consistencia interna:** solo 0,1–0,4 % de los ID tiene más de un sexo o fecha de nacimiento dentro del año.
- **Evidencia:** `1.2_exploracion_calidad/scripts/01_diagnostico_ids.py` → `1.2_exploracion_calidad/reportes/01_diagnostico_ids.md`.

### D03 · 2026-09-30 · Reingreso reconstruido por bloque de identificador
- **Actividad:** 2.1 y 2.2
- **Decisión:** Se agrega la variable `BLOQUE_ID` (A = 2019–2020, B = 2021–2024) y el reingreso se reconstruye solo dentro de cada bloque. Los egresos del bloque A cuya ventana de seguimiento supera el 31-12-2020 se tratan como censurados por la derecha, igual que los del bloque B que superan el 31-12-2024.
- **Alternativas descartadas:** (1) tabla de correspondencia del DEIS: no disponible; (2) enlace por sexo, fecha de nacimiento y comuna: descartado por el alto riesgo de falsos enlaces.
- **Consecuencias:** se pierden los reingresos que cruzan de 2020 a 2021, y las "hospitalizaciones previas" de los egresos de comienzos de 2021 quedan subestimadas. Se declara como limitación.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D04 · 2026-09-30 · Valores nulos
- **Actividad:** 2.1
- **Decisión:** Se consideran nulos: vacío, `DESCONOCIDO` y `SIN INFORMACIÓN` (este último solo en los ID de 2019–2020). En el ID, además, el valor `0`.
- **Evidencia:** `1.2_exploracion_calidad/reportes/01_diagnostico_ids.md`, `1.2_exploracion_calidad/reportes/02_cobertura_tablas_auxiliares.md`.
- **Estado:** Reemplazada por D11.

### H03 · 2026-09-30 · Cobertura de los códigos en las tablas auxiliares del DEIS
- **Actividad:** 1.2
- **Hallazgo:** Diagnósticos (CIE-10) 99,5–99,9 %, procedimientos (CIE-9) ~100 %, GRD ~100 %, hospitales 100 % hasta 2023 y 99 % en 2024. Lo que no aparece en los catálogos: `DESCONOCIDO`, códigos COVID posteriores al catálogo (U08.9, U09.9, U10.9, U12.9) y el hospital `200717` (10.354 egresos en 2024).
- **Evidencia:** `1.2_exploracion_calidad/scripts/02_cobertura_tablas_auxiliares.py` → `1.2_exploracion_calidad/reportes/02_cobertura_tablas_auxiliares.md`.

### H04 · 2026-09-30 · Estructura del código GRD
- **Actividad:** 1.2
- **Hallazgo:** En la tabla maestra, los 2 primeros dígitos del código toman 24 valores (CDM 01–23 y 99 = inagrupable), lo que respalda derivar la CDM desde los 2 primeros dígitos. El último dígito corresponde a la severidad (0–3). En el Excel los códigos perdieron el cero inicial. Las descripciones comienzan con PH/PA/MH/MA (se interpreta como procedimiento o médico, hospitalizado o ambulatorio; falta confirmarlo con documentación). La tabla maestra no incluye los nombres de las CDM.

### H05 · 2026-09-30 · Incorporación de hospitales al sistema GRD
- **Actividad:** 1.2
- **Hallazgo:** 65 hospitales entre 2019 y 2022, 68 en 2023 y 72 en 2024. Un reingreso en un hospital que aún no reportaba a GRD no es observable, lo que puede aumentar artificialmente la tasa de reingreso en 2023–2024.
- **Consecuencia:** Declarar como limitación y considerarlo al interpretar la validación temporal (entrenamiento 2019–2022, evaluación 2023–2024).

### D05 · 2026-09-30 · Diagnósticos COVID fuera del catálogo
- **Actividad:** 2.1
- **Decisión:** Se conservan U08.9, U09.9, U10.9 y U12.9 como códigos válidos (OMS, posteriores a la versión 2015 del catálogo) y se agregan manualmente al catálogo con su descripción.
- **Estado:** Adoptada.

### D06 · 2026-09-30 · Código GRD y CDM como texto
- **Actividad:** 2.1
- **Decisión:** `IR_29301_COD_GRD` se guarda como texto de 6 caracteres con ceros a la izquierda (también en la tabla maestra). `CDM` = 2 primeros caracteres.
- **Estado:** Adoptada.

### D07 · 2026-09-30 · Egresos sin diagnóstico principal
- **Actividad:** 2.2
- **Decisión propuesta:** Conservar los egresos sin diagnóstico principal. Son 11.396 (0,20 %) y casi todos tienen GRD, CDM, diagnósticos secundarios y procedimientos. Solo se excluyen como caso de estudio los que no tienen un GRD válido (ver D08). Reemplaza la propuesta inicial de excluirlos.
- **Fundamento:** Revisión del 5 de octubre de 2026 sobre la tabla integrada. El 95 % de estos egresos tiene diagnósticos secundarios, el 98 % tiene procedimientos y todos salvo 19 tienen código GRD; el 65 % pertenece a la CDM 08. Se concentran en 2019 (8.650) y 2020 (2.372). En un conteo preliminar, 871 ocurren dentro de los 30 días posteriores a un alta anterior del mismo paciente, por lo que eliminarlos dejaría esas altas sin su reingreso.
- **Estado:** Pendiente de validar con profesor guía.

### D08 · 2026-09-30 · GRD inagrupable (CDM 99)
- **Actividad:** 2.2
- **Decisión propuesta:** Los egresos con GRD inagrupable (CDM 99) se excluyen como caso de estudio (egreso índice), porque no tienen una categoría diagnóstica ni un peso GRD válidos. Se conservan en la tabla para identificar reingresos por cualquier causa. Un reingreso con CDM 99 no se cuenta como relacionado con el diagnóstico. El mismo criterio se aplica a los 90 egresos sin código GRD (H07).
- **Fundamento:** Revisión del 5 de octubre de 2026. Son 4.983 egresos (0,09 %). El 91 % corresponde al GRD 990099, "paciente ambulatorio con procedimiento de hospitalización" (cirugía mayor ambulatoria), y todos tienen peso GRD igual a 0. En un conteo preliminar, de unos 671.000 pares de alta seguida de un nuevo ingreso dentro de 30 días, solo 383 involucran la CDM 99.
- **Estado:** Pendiente de validar con profesor guía.

### H06 · 2026-09-30 · Línea con un separador de más en 2022
- **Actividad:** 1.2
- **Hallazgo:** En `GRD_PUBLICO_EXTERNO_2022.txt`, la línea 120127 tiene 130 campos en vez de 129. Todas las columnas están alineadas hasta `HOSPPROCEDENCIA`, que viene vacía, seguida de un campo extra `114101`. Se interpreta que el valor original de `HOSPPROCEDENCIA` era `|114101`. Es la única línea anómala en los seis archivos. El registro corresponde a un egreso fallecido con GRD `DESCONOCIDO`.
- **Evidencia:** `2.1_integracion_homogenizacion/scripts/03_convertir_parquet.py` → `2.1_integracion_homogenizacion/reportes/03_conversion_parquet.md`.

### D09 · 2026-09-30 · Conversión a Parquet sin transformar
- **Actividad:** 2.1
- **Decisión:** Cada archivo se convierte a `data/interim/crudo_<año>.parquet` con las 129 columnas como texto, sin modificaciones, más `ANIO_ARCHIVO`, `ARCHIVO_ORIGEN` y `FILA_ORIGEN` (número de línea en el txt). La línea de H06 se conserva uniendo el campo extra a `HOSPPROCEDENCIA` (`|114101`), sin descartar el registro.
- **Verificación:** 5.808.536 registros en txt y en Parquet, sin campos faltantes y con el texto (tildes, Ñ) decodificado correctamente en los seis años. Tamaño: 4,0 GB en txt frente a 0,32 GB en Parquet.
- **Estado:** Adoptada.

### C01 · 2026-09-30 · Corrección: año del cambio de identificador
- **Sección:** *Descripción de los datos o corpus*.
- **Corrección:** El informe indica un cambio de identificador "desde 2024". El cambio real ocurre entre 2020 y 2021; en 2024 solo cambia el nombre de la columna (ver H02).

### C02 · 2026-09-30 · Corrección: codificación de procedimientos
- **Sección:** *Procedimiento experimental*, etapa 3.
- **Corrección:** Dice "codificación CIE-10 de diagnósticos y procedimientos". Los procedimientos están en CIE-9-MC.

### C03 · 2026-09-30 · Corrección: software
- **Sección:** *Software y hardware requerido*.
- **Corrección:** Agregar pyarrow 25.0.1 (lectura y escritura de Parquet) y openpyxl 3.1.5 (lectura de las tablas auxiliares).

### H07 · 2026-10-02 · Valores con forma de RUT en 2019
- **Actividad:** 1.2
- **Hallazgo:** En 2019, 27 filas tienen valores anómalos en `USOSPABELLON` o `FECHAPROCEDIMIENTO1`; en la mayoría el valor tiene forma de RUT (número con dígito verificador). `FECHAPROCEDIMIENTO1` está vacía en todo el resto de la base. La mayoría de estas filas tiene GRD `DESCONOCIDO` y el resto de sus columnas está alineado (no son filas corridas). Podrían ser identificadores personales dentro de una base anonimizada.
- **Evidencia:** revisión de formatos sin mostrar los valores. `1.2_exploracion_calidad/reportes/04_perfil_columnas.md` solo muestra formatos.
- **Verificación:** El dígito verificador del RUT (módulo 11) es válido en 24 de las 27 celdas; con números al azar coincidiría en 2 o 3, por lo que casi con seguridad son RUT reales. Dos valores se repiten en pacientes distintos del mismo hospital, así que al menos esos no son del paciente (probablemente de un profesional). Provienen de 14 hospitales distintos.
- **Filas afectadas:** Se concentran en 19 de las 21 filas de 2019 con GRD `DESCONOCIDO`, que en su mayoría tienen además una fecha de nacimiento inválida (`--01`, `--02`): son registros defectuosos.
- **Consecuencia:** Los valores no se copian a reportes ni a la base homogenizada (ver D10). Informar al profesor guía. Propuesta: excluir en la actividad 2.2 los egresos sin GRD (90 en los seis años).

### H08 · 2026-10-02 · Perfil de las 129 columnas (complementa H01)
- **Actividad:** 1.2
- **Fechas:** En 2023 también están en DD-MM-AAAA `FECHATRASLADO1-9` y `FECHAINTERV1`, no solo ingreso y alta. `FECHA_NACIMIENTO` está en AAAA-MM-DD en los seis años.
- **Peso GRD:** El decimal sin cero inicial (`,3045`) aparece en 2020 (70 % de los valores) y en 2021 (67 %), no solo en 2021.
- **Sin dato:** Se expresa con distintos valores según el año y la columna: `DESCONOCIDO`, `DESCONOCIDA`, `SIN INFORMACIÓN`, `NO APLICA`, `NO IDENTIFICADA`, `NO IDENTIFICADO`, `NO CONSIGNADO`, `IGNORADO`, `NO RESPONDE`.
- **Textos:** Espacios sobrantes (`OTRO ` frente a `OTRO`, `MATRONAS(ES)  `), variantes de tildes (`HAITI` / `HAITÍ`) y valores en minúsculas en `SERVICIOINGRESO` de 2024.
- **Especialidades:** `ESPECIALIDAD_MEDICA` y `ESPECIALIDADINTERVENCION` usan otros nombres en 2019 (p. ej. `MEDICINA GENERAL` y `MATRONA`, que desde 2020 son `MÉDICO GENERAL` y `MATRONAS(ES)`).
- **Etnia:** En 2022 y 2023 desaparece `NINGUNO` y casi todos los registros quedan como `OTRO`; la variable no es comparable entre años. Los pueblos originarios (mapuche, aymara, etc.) sí se codifican igual todos los años.
- **Otros:** `USOSPABELLON` casi no se informó en 2020. Los campos de recién nacido se codifican distinto en 2019 (`CONDICIONDEALTANEONATO` solo existe ese año). `SERVICIOTRASLADO` trae códigos numéricos sin diccionario en 2021, 2022 y 2024. `HOSPPROCEDENCIA` nombra los hospitales distinto según el año. El valor `|114101` de H06 corresponde al Complejo Hospitalario Dr. Sótero del Río según la tabla maestra.
- **Evidencia:** `1.2_exploracion_calidad/scripts/04_perfil_columnas.py` → `1.2_exploracion_calidad/reportes/04_perfil_columnas.md`.

### H09 · 2026-10-02 · Tipos de actividad que solo existen en 2019
- **Actividad:** 1.2 y 2.2
- **Hallazgo:** 2019 incluye 55.328 egresos `HOSPITALIZACIÓN DIURNA` (98,6 % con estadía de 0 días, casi todos programados) y 62.551 `HOSPITALIZACIÓN EN URGENCIA` (mediana de 1 día, casi todos por urgencia). Desde 2020 solo existen `HOSPITALIZACIÓN` y `CIRUGÍA MAYOR AMBULATORIA (CMA)`, y la proporción de hospitalizaciones de 0 días se mantiene en ~5 % todos los años: esos episodios no se reclasificaron, dejaron de registrarse en la base.
- **Consecuencia:** 2019 contiene ~118 mil episodios (10 % del año) de tipos que no existen después. Propuesta: no renombrarlos en la homogenización y excluirlos en la actividad 2.2 para que 2019 sea comparable con 2020–2024.
- **Evidencia adicional:** Revisión del 5 de octubre de 2026. La hospitalización diurna corresponde sobre todo a tratamientos que se repiten: sesiones de quimioterapia (12.576) y diálisis (10.068); 649 pacientes tienen 10 o más episodios en el año, y el 30 % de los episodios diurnos va seguido de otro ingreso dentro de 7 días. Con estos dos tipos de actividad, el 14,0 % de las altas de 2019 va seguido de un nuevo ingreso del mismo paciente dentro de 30 días, frente a entre 10,7 % y 11,4 % en los demás años; sin ellos, el valor de 2019 es 11,6 % (conteo preliminar, sin otras exclusiones).
- **Estado:** Se aplicará en la actividad 2.2: estos episodios quedan fuera como caso de estudio y como reingreso de otra alta. Pendiente de validar con profesor guía.

### D10 · 2026-10-02 · Protección de los valores con forma de RUT
- **Actividad:** 2.1
- **Decisión:** Ningún reporte muestra valores con forma de RUT; el perfil de columnas publica solo sus formatos. En la base homogenizada se elimina `FECHAPROCEDIMIENTO1` (vacía salvo esos valores) y los valores no numéricos de `USOSPABELLON` quedan como nulos.
- **Estado:** Adoptada. Aplicada en la homogenización (D11).

### D11 · 2026-10-03 · Reglas de homogenización
- **Actividad:** 2.1
- **Decisión:** Se aplican a los seis años las mismas nueve reglas: (1) `ID_PACIENTE` como nombre único del identificador, más las columnas `BLOQUE_ID` y `CDM`; (2) un solo "sin dato"; (3) textos sin espacios sobrantes y en mayúsculas; (4) fechas en AAAA-MM-DD o DD-MM-AAAA convertidas a fecha; (5) peso GRD con punto decimal y enteros guardados como enteros; (6) códigos GRD, CIE-10, CIE-9 y de hospital como texto; (7) equivalencias de categorías (D12); (8) eliminación de `FECHAPROCEDIMIENTO1` (D10); (9) un tipo de dato por columna, igual en todos los años. No se elimina ni agrega ninguna fila.
- **Sin dato:** Pasan a nulo las celdas vacías y los valores `DESCONOCIDO`, `DESCONOCIDA`, `SIN INFORMACIÓN`, `NO APLICA`, `NO IDENTIFICADA`, `NO IDENTIFICADO`, `NO CONSIGNADO`, `IGNORADO`, `NO RESPONDE`, `NO ESPECIFICADO` y `SERVICIO NO DEFINIDO`: 222.964 celdas en total. El `0` solo se trata como sin dato en procedimientos y servicios de traslado (6 de esas celdas). Reemplaza a D04.
- **Valores no convertibles:** 91 celdas con fechas o números inválidos quedaron como sin dato (por ejemplo, fechas escritas `--01` y los valores con forma de RUT de `USOSPABELLON`).
- **Verificación:** 5.808.536 registros antes y después, en el mismo orden; esquema idéntico en los seis años (133 columnas); 0 celdas con forma de RUT; 0 variantes de un mismo valor. Comprobación independiente: las fechas de 2023 y el peso GRD de 2021 coinciden con el texto original en todas las filas, y el número de pacientes por año coincide con el de H02.
- **Evidencia:** `2.1_integracion_homogenizacion/scripts/05_homogenizar.py` → `2.1_integracion_homogenizacion/reportes/05_homogenizacion.md`. Salida en `data/interim/homog_<año>.parquet`.
- **Estado:** Adoptada.

### D12 · 2026-10-03 · Equivalencias de categorías entre años
- **Actividad:** 2.1
- **Decisión:** Los cambios de nombre entre años se resuelven con la tabla `2.1_integracion_homogenizacion/reglas/equivalencias_categorias.csv` (46 reglas): 19 especialidades con nombre propio de 2019, en `ESPECIALIDAD_MEDICA` y `ESPECIALIDADINTERVENCION`; variantes de tilde en `NACIONALIDAD` y `HOSPPROCEDENCIA`; `NINGUNA` → `NINGUNO` en `ETNIA`; `NO PROGRAMADA` → `URGENCIA` en `TIPO_INGRESO`; y el código `|114101` → Complejo Hospitalario Dr. Sótero del Río.
- **Criterio:** Solo se incluyen cambios 1 a 1. Cada equivalencia de especialidad se verificó comparando volúmenes: al considerar solo hospitalizaciones y cirugía mayor ambulatoria, el volumen de 2019 es similar al de 2020 (por ejemplo, `NEFROLOGÍA` tiene 1.131 egresos en 2019 y `NEFROLOGÍA ADULTO` tiene 1.096 en 2020).
- **Sin equivalente:** `ODONTOLOGÍA`, `NEUROCIRUGÍA PEDIÁTRICA`, `NUTRICIÓN Y DIABETES` y `MEDICINA TRANSFUSIONAL` existen solo en 2019 y no se modificaron.
- **Evidencia:** `2.1_integracion_homogenizacion/reportes/05_homogenizacion.md`, sección 4.
- **Estado:** Adoptada. La tabla queda pendiente de revisión.

### D13 · 2026-10-03 · Casos que requerían decisión en la homogenización
- **Actividad:** 2.1
- **Decisión:** (1) Los tipos de actividad que solo existen en 2019 no se renombran (H09); su exclusión se define en la actividad 2.2. (2) `ETNIA` solo se limpia; para el modelado se usará "pertenece a un pueblo originario: sí/no". (3) `NO PROGRAMADA` pasa a `URGENCIA`. (4) En `HOSPPROCEDENCIA` no se unifican los nombres de los hospitales; para el modelado se usará "viene de otro establecimiento: sí/no". (5) Los campos de recién nacido, `USOSPABELLON` y `SERVICIOTRASLADO` reciben solo limpieza básica y se consideran no comparables entre años.
- **Estado:** Adoptada. Los puntos 1 y 2 quedan por validar con profesor guía.

### H10 · 2026-10-03 · Coherencia de fechas tras homogenizar
- **Actividad:** 1.2 y 2.2
- **Hallazgo:** Con las fechas ya convertidas se observan 71 egresos sin fecha de ingreso (19 en 2019 y 52 en 2024), 18 sin fecha de alta (2019), 37 sin fecha de nacimiento, 12 con alta anterior al ingreso y 26 con una edad al ingreso mayor de 110 años. Ningún egreso tiene la fecha de alta fuera del año de su archivo: los archivos están organizados por año de alta. Cada año tiene egresos en sus 12 meses. En 2019, `USOSPABELLON` tiene 141 valores entre 10 y 999, cuando el máximo de 2021 a 2024 es 8.
- **Evidencia:** `2.1_integracion_homogenizacion/reportes/05_homogenizacion.md`, secciones 7 y 9.
- **Consecuencia:** Estos registros no se corrigen ni se excluyen en la homogenización; se tratan en la actividad 2.2.

### D14 · 2026-10-03 · Integración en una tabla única
- **Actividad:** 2.1
- **Decisión:** Los seis años homogenizados se apilan en `data/processed/grd_2019_2024.parquet` (5.808.536 registros, 136 columnas, 295 MB). Se agrega `ID_EGRESO`, un identificador único por egreso formado por el año del archivo y el número de línea del txt original (año × 10.000.000 + línea); por ejemplo, `20230000002`. No se elimina ningún registro.
- **Verificación:** El total y los registros por año coinciden con los archivos homogenizados; `ID_EGRESO` es único; los tipos de dato se conservan al leer el archivo; cada año tiene egresos en sus 12 meses; los pacientes que reaparecen al año siguiente coinciden con H02 (8,9 % de 2019 a 2020, 0 % de 2020 a 2021 y entre 13,9 % y 15,5 % desde 2021).
- **Evidencia:** `2.1_integracion_homogenizacion/scripts/06_integrar.py` → `2.1_integracion_homogenizacion/reportes/06_integracion.md`.
- **Estado:** Adoptada.

### D15 · 2026-10-03 · Definición y marcado de duplicados
- **Actividad:** 2.1 y 2.2
- **Decisión:** Dos registros se consideran el mismo episodio cuando coinciden paciente, hospital, fecha de ingreso y fecha de alta. En la integración los duplicados solo se marcan, con dos columnas: `DUP_EXACTO` (copia idéntica de un registro anterior, en todas las columnas de datos) y `DUP_CLAVE` (comparte los cuatro datos de la clave con otro registro). La eliminación se hará en la actividad 2.2.
- **Resultado:** 3.818 copias exactas (2.818 de ellas en 2020) y 15.734 registros con clave repetida, en 7.850 grupos de 2 a 4 registros. Los 17.934 registros sin clave completa (sin identificador de paciente o sin fechas) no se pueden evaluar por clave.
- **Regla de eliminación:** Definida el 5 de octubre de 2026. Las copias exactas se eliminan. Al quitarlas quedan 4.041 episodios con dos o más registros distintos (el 86 % con estadía de 0 días y el 78 % de cirugía mayor ambulatoria); en el 39 % de los pares lo único distinto es el médico registrado. En esos episodios se conserva el registro más completo: el que tiene más diagnósticos; si empatan, el que tiene más procedimientos; si empatan, el de mayor peso GRD; y si siguen empatados, el primero del archivo. Sobran 4.067 registros. El reingreso no depende de cuál se conserve, porque el paciente y las fechas son los mismos.
- **Caso especial:** En 296 pares los dos registros tienen distinto sexo o distinta fecha de nacimiento, es decir, son personas distintas que comparten identificador. En 124 de ellos uno es menor de un año y el otro tiene más de 12, probablemente un recién nacido registrado con el identificador de su madre. Estos pares no se fusionan; su tratamiento se define en la actividad 2.2, junto con el criterio de «mismo paciente».
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H11 · 2026-10-03 · Hallazgos de la tabla integrada
- **Actividad:** 1.2 y 2.2
- **Duplicados:** En los cerca de 4.000 pares con la misma clave que no son copias exactas, lo que más difiere es el médico de alta (74 % de los pares) y el médico de la intervención (64 %); los diagnósticos, los procedimientos y el GRD difieren en alrededor del 25 %.
- **Comparabilidad entre años:** El peso GRD medio es menor en 2019 (0,84) que en el resto (0,96 a 1,11), en línea con H09. El número de diagnósticos registrados por egreso aumenta de 4,37 en 2019 a 5,77 en 2024, lo que puede afectar a los índices de comorbilidad. En 2020 y 2021 aumentan los ingresos por urgencia (55 % a 56 %, frente a cerca del 50 %) y las altas por fallecimiento (3,8 % a 3,9 %, frente a 2,4 % a 2,9 %).
- **Evidencia:** `2.1_integracion_homogenizacion/reportes/06_integracion.md`, secciones 3 y 4.

### H12 · 2026-10-03 · Significado de USOSPABELLON y valores poco plausibles
- **Actividad:** 1.2
- **Hallazgo:** `USOSPABELLON` no es una cantidad de usos de pabellón sino el tipo de pabellón utilizado: sus valores van de 1 a 8 y corresponden a la hoja Tipo de Pabellón de la tabla maestra (1 central u obstétrico, 2 ambulatorio, 3 sala de procedimiento, etc.). En la cirugía mayor ambulatoria el 40 % de los egresos usa el código 2, frente al 1 % en la hospitalización. Hay 327 valores fuera del rango 1 a 8 (233 en 2019).
- **Otros valores poco plausibles:** `FECHAINTERV1` cae fuera del episodio en el 2,2 % de los casos de 2019 a 2023 (la mayoría, un día antes del ingreso) y 73 tienen años imposibles; en 2024 no hay ninguno, y ese año aparecen 19.669 valores `DESCONOCIDA`. En el peso de los recién nacidos hay 414 valores menores de 300 g y 33 mayores de 6.500 g.
- **Consecuencia:** Son variables secundarias; no se corrigen. `USOSPABELLON` debe tratarse como categoría, no como número.

### D16 · 2026-10-03 · Diccionario de datos
- **Actividad:** 2.1
- **Decisión:** El diccionario `docs/diccionario_datos.md` se genera con `2.1_integracion_homogenizacion/scripts/07_diccionario_datos.py` a partir de las descripciones de `2.1_integracion_homogenizacion/reglas/descripciones_columnas.csv` y de estadísticas calculadas sobre la tabla integrada (tipo, valores y porcentaje con dato). Cubre las 136 columnas en 46 entradas.
- **Estado:** Adoptada. Las descripciones deben contrastarse con la documentación oficial de la base GRD.

### D17 · 2026-10-03 · Carpetas por actividad de la Carta Gantt
- **Actividad:** 2.1
- **Decisión:** El contenido de `Codigo` se organiza en una carpeta por actividad, cada una con sus `scripts/`, `reportes/` y `reglas/`: `1.2_exploracion_calidad` (scripts 01, 02 y 04, que examinan los datos sin modificarlos) y `2.1_integracion_homogenizacion` (scripts 03, 05, 06 y 07, que los transforman). Las carpetas `data/`, `docs/` y `herramientas/` siguen siendo comunes. Reemplaza la organización por tipo de archivo (`src/`, `reports/`, `reglas/`) descrita en D01.
- **Bitácoras:** Esta bitácora se mantiene como un solo documento para las actividades 1.2 y 2.1. Las rutas citadas en sus entradas se actualizaron a la nueva ubicación, sin cambiar el contenido. Desde la actividad 2.2, cada actividad lleva su propia bitácora dentro de su carpeta.
- **Verificación:** Tras mover los archivos se volvieron a ejecutar los siete scripts desde su nueva ubicación: los 19 archivos de datos resultaron idénticos byte a byte a los anteriores, y los reportes solo cambiaron en la ruta del script que los genera.
- **Estado:** Adoptada.

---

## Pendientes

- [ ] Validar D03, D07 y D08 con profesor guía.
- [ ] Consultar al DEIS si existe una tabla de correspondencia de ID entre 2020 y 2021 (si existe, D03 se reemplaza).
- [ ] Identificar el hospital `200717` en el registro de establecimientos del DEIS.
- [ ] Confirmar el alcance del archivo "EXTERNO" 2022.
- [ ] Construir la tabla de nombres de las 23 CDM y confirmar el significado de PH/PA/MH/MA.
- [ ] Informar al profesor guía sobre los valores con forma de RUT (H07) y evaluar si avisar al DEIS.
- [ ] Validar con profesor guía la exclusión en 2.2 de los 90 egresos con GRD `DESCONOCIDO` (H07).
- [ ] Revisar la tabla de equivalencias y decidir qué hacer con los 4 nombres de especialidad sin equivalente (D12).
- [ ] En la actividad 2.2, definir el tratamiento de los egresos con fechas faltantes o incoherentes (H10).
- [x] En la actividad 2.2, definir qué registro se conserva en los grupos con clave repetida (D15). Definido el 5 de octubre de 2026: el más completo.
- [ ] En la actividad 2.2, definir cómo se tratan los identificadores compartidos por dos personas, por ejemplo madre y recién nacido (D15).
- [ ] Contrastar el diccionario de datos con la documentación oficial de la base GRD (D16).
- [ ] Validar con profesor guía la propuesta de H09 (excluir en 2.2 los tipos de actividad que solo existen en 2019).
