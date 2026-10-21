# Bitácora de la actividad 2.2: depuración y etiquetado del reingreso

Registro de los hallazgos y decisiones de la actividad 2.2 de la Carta Gantt. Continúa la numeración
de `docs/bitacora.md`, que cubre las actividades 1.2 y 2.1: aquí el primer hallazgo es H13 y la primera
decisión, D18. Las entradas anteriores que se aplican en esta actividad (D03, D07, D08, D15, H09 y H10)
están en esa bitácora. Una entrada no se borra: si una decisión cambia, se agrega una nueva entrada
que la reemplaza y se indica en el campo **Estado**.

Las decisiones del 6 de octubre de 2026 (D18 a D26) se aplicaron como provisionales. El profesor guía
las revisó el 7 de octubre («satisfactorio, con correcciones metodológicas antes de congelar el
conjunto de prueba») y las entradas del 8 de octubre (H20 a H25 y D30 a D36) recogen sus correcciones.
En su revisión del 13 de octubre aprobó D30 y D34, y aprobó la tabla de criterios (D35) a condición de
incorporar dos puntos: los partos en las variables relacionadas (punto 2.1 de esa revisión) y la
sensibilidad de las reglas de traslado y de derivación (punto 2.4). Las entradas del 20 de octubre
(H26, H27, D38 y D39) los incorporan; H28 responde a otro punto de la misma revisión (2.3), sobre la
calidad del identificador por año. Cada exclusión se puede activar o desactivar en
`reglas/criterios_exclusion.csv` y cada umbral se puede cambiar en `reglas/parametros.csv`, sin
modificar el código.

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

Definiciones vigentes desde el 20 de octubre de 2026.

| Tema | Entrada | Definición |
|---|---|---|
| Misma persona | D18, D34 | Mismo identificador y fechas de nacimiento que no difieran en más de un año (o que coincidan en día y mes). Los identificadores con datos que no coinciden llevan la marca `IDENTIDAD_AMBIGUA`. |
| Traslado | D19, H22 | Ingreso en otro hospital el mismo día del alta o al día siguiente, o ingreso anterior al alta: continúa el mismo episodio asistencial. |
| Reingreso | D20, D26, D33 | Ingreso no planificado (no programado y que no sea un parto ni una sesión de tratamiento) dentro de 7 o 30 días del alta final del episodio. Son las cuatro variables de la propuesta. |
| Reingreso relacionado | D31, D38 | Algún ingreso de la ventana con la misma CDM que el caso de estudio, sin agrupar CDM. Los partos (CDM 14) quedan sin dato en estas dos variables, porque no pueden tener un reingreso de su misma CDM. La unión de las CDM 13 y 14 queda como análisis de sensibilidad. |
| Sin identificador o sin fechas | D21 | Fuera como caso de estudio y como reingreso. |
| Censura | D30 | Cada ventana exige sus días más 30 de margen antes del cierre del bloque: 37 días para las variables de 7 días y 60 para las de 30 días. |
| Exclusiones | D23, D32, D33, D35 | Catorce criterios en una tabla, con su justificación; trece activos y uno desactivado. La cirugía mayor ambulatoria y las sesiones de tratamiento no son caso de estudio. |
| Duplicados | D24 | Aplicación de D15: se conserva el registro más completo. |
| Versión de los datos | D36 | El conjunto analítico es `grd_etiquetado.parquet`; su versión y su hash están registrados. |

Resultado vigente: 4.192.410 casos de estudio. Las variables de 30 días se calculan sobre los 4.101.883
que tienen 60 días de seguimiento, y las dos relacionadas no incluyen los partos (D38).

| Variable | Definición | Casos con dato | Casos con reingreso | % |
|---|---|---|---|---|
| `REING_7D` | 7 días, por cualquier causa | 4.192.410 | 86.609 | 2,07 % |
| `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 3.577.243 | 45.195 | 1,26 % |
| `REING_30D` | 30 días, por cualquier causa | 4.101.883 | 241.953 | 5,90 % |
| `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 3.498.460 | 124.256 | 3,55 % |

---

### H13 · 2026-10-06 · Identificadores compartidos por más de una persona
- **Actividad:** 2.2
- **Hallazgo:** De 4.035.780 identificadores de paciente, 30.778 (0,76 %) tienen más de una combinación de sexo y fecha de nacimiento; reúnen 97.378 egresos. Corresponden a tres situaciones distintas.
- **Madre y recién nacido:** En 1.827 identificadores hay dos personas, de las cuales la menor tiene menos de un año en su primer ingreso y la otra le lleva más de 12 años. Ejemplo: los egresos `20230204284` (un parto) y `20230646756` (una recién nacida en neonatología) tienen el mismo identificador, el mismo hospital y las mismas fechas de ingreso y de alta.
- **Errores de digitación:** De los 23.609 identificadores con exactamente dos fechas de nacimiento, en 17.795 las fechas difieren en hasta 366 días (cambia el día o el mes) y en 1.953 difieren en más, pero coinciden en el día y el mes (cambia el año). Además, 7.124 identificadores tienen una misma fecha de nacimiento registrada con los dos sexos.
- **Identificadores genéricos:** 12 identificadores se usan para muchas personas (5 o más combinaciones de sexo y fecha de nacimiento; el más usado tiene 1.101). Suman 2.481 egresos.
- **Consecuencia:** Si el reingreso se calcula solo con el identificador, la hospitalización de un recién nacido cuenta como reingreso de su madre. Si se exige que el sexo y la fecha de nacimiento sean idénticos, se pierden los reingresos reales de las personas con un error de digitación.
- **Evidencia:** `2.2_depuracion_etiquetado/scripts/08_depurar.py` → `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 3.
- **Precisado por:** H21, que no cuenta un dato faltante como una combinación distinta (30.616 identificadores en vez de 30.778).

### D18 · 2026-10-06 · Criterio de «misma persona»
- **Actividad:** 2.2
- **Decisión:** Dos egresos con el mismo identificador son de personas distintas cuando sus fechas de nacimiento difieren en más de 366 días, salvo que coincidan en el día y el mes, caso que se interpreta como un error de digitación en el año. El sexo no se usa. Cada egreso recibe un `ID_PERSONA`, formado por el identificador seguido de dos dígitos con el número de persona (01 la de más edad). Los 12 identificadores genéricos quedan sin persona asignada y se tratan igual que los egresos sin identificador (criterio E02).
- **Fundamento:** De unos 626.000 pares de alta seguida de un nuevo ingreso del mismo identificador dentro de 30 días, en 2.089 las fechas de nacimiento difieren en más de un año (755 de ellos coinciden en día y mes), en 6.684 difieren entre 1 y 366 días y en 2.860 solo cambia el sexo. La regla adoptada deja de contar unos 1.300 pares, que son personas distintas.
- **Alternativas descartadas:** (1) Usar solo el identificador: cuenta al recién nacido como reingreso de su madre. (2) Exigir identificador, sexo y fecha de nacimiento idénticos: deja de contar 11.633 pares, de los que unos 10.000 son la misma persona con un error de digitación.
- **Limitación:** Dos gemelos registrados con el identificador de su madre tienen la misma fecha de nacimiento y no se pueden distinguir: quedan como una sola persona. En la exploración hay 397 pares de menores de un año con igual fecha de nacimiento y distinto sexo. Tampoco se separan una madre y su hijo que hayan nacido el mismo día y mes (uno de cada 365 casos).
- **Resultado:** 4.039.699 personas. De los identificadores no genéricos, 3.901 corresponden a dos personas, 12 a tres y 2 a cuatro.
- **Parámetros:** `persona_dias_fnac` (366), `persona_mismo_dia_mes` (SI) e `id_generico_min_personas` (5).
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H14 · 2026-10-06 · El tipo de alta no basta para reconocer un traslado
- **Actividad:** 2.2
- **Hallazgo:** Entre los egresos que se pueden seguir, 154.437 tienen alta por derivación a otro hospital, pero solo en 77.832 (50,4 %; entre 44 % y 55 % según el año) la continuación está en la base. El resto fue a establecimientos que no reportan GRD. En sentido inverso, 87.059 egresos ingresan en otro hospital el mismo día del alta anterior de la misma persona (70.933) o al día siguiente (16.126), y unos 13.800 de esas altas anteriores figuran como alta a domicilio.
- **Respaldo de la regla por fechas:** El 96,8 % de los ingresos del mismo día y el 90,6 % de los del día siguiente tienen además una marca explícita de traslado: el alta anterior es una derivación o el ingreso declara que procede de otro hospital.
- **Episodios dentro de otro:** 10.524 egresos ingresan antes del alta anterior de la misma persona, casi todos en otro hospital: el paciente sale a un procedimiento y vuelve. El caso extremo es una hospitalización de casi seis meses que contiene 31 atenciones de un día en otro hospital.
- **Ejemplo:** El egreso `20230696755` (alta por derivación el 19 de mayo de 2023) continúa en el `20230179771` (otro hospital, ingreso el mismo día, procedencia «otros hospitales»). Sin una regla, contaría como un reingreso el día 0 con la misma CDM.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 4.

### D19 · 2026-10-06 · Episodio asistencial y tratamiento de los traslados
- **Actividad:** 2.2
- **Decisión:** Los egresos de una persona se unen en un mismo episodio asistencial (`ID_EPISODIO`) cuando el segundo ingresa antes del alta del primero, o ingresa en otro hospital el mismo día del alta o al día siguiente. También se unen dos registros de la misma persona con el mismo hospital y las mismas fechas (D24). Dentro de un episodio, solo el alta final puede ser caso de estudio (criterio E05) y un egreso que continúa el episodio no cuenta como reingreso.
- **Derivaciones sin continuación:** Los egresos con alta por derivación a otro hospital cuya continuación no está en la base (criterio E07, 76.605) y los derivados a instituciones privadas (E08, 22.968) tampoco son caso de estudio: el paciente sigue hospitalizado donde no se lo puede observar.
- **Mismo hospital, mismo día:** Un ingreso en el mismo hospital el mismo día del alta no es un traslado: abre un episodio nuevo y puede contar como reingreso (9.425 egresos). Ejemplo: el egreso `20230989214` es una cirugía ambulatoria con alta a domicilio y el `20230366798`, un ingreso por urgencia ese mismo día por una hemorragia del procedimiento.
- **Fundamento:** La propuesta de tesis excluye «los traslados, que corresponden a la continuidad de un mismo episodio asistencial».
- **Alternativas:** (1) Considerar traslado solo el ingreso del mismo día (`traslado_dias_max` = 0). (2) Exigir además la marca explícita de traslado (`traslado_exige_marca` = SI). Con la regla adoptada, 3.755 ingresos sin marca se tratan como traslado (2.244 del mismo día y 1.511 del día siguiente); en su mayoría vienen de un alta a domicilio e ingresan por urgencia, por lo que algunos pueden ser reingresos reales en otro hospital.
- **Resultado:** 5.565.982 episodios asistenciales; 83.904 tienen más de un egreso (72.366 de dos, 10.280 de tres y 1.258 de cuatro o más) y 97.603 egresos continúan un episodio.
- **Pendiente:** Respaldar con bibliografía la regla del mismo día o el día siguiente.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H15 · 2026-10-06 · Qué tipo de ingreso es el reingreso
- **Actividad:** 2.2
- **Hallazgo:** De 537.887 altas seguidas de un nuevo ingreso dentro de 30 días (sin traslados), el nuevo ingreso es por urgencia en el 43,8 %, programado en el 39,5 % y obstétrico en el 16,7 %.
- **Programados:** Los diagnósticos más frecuentes son sesiones de tratamiento como la quimioterapia (Z51, 51.877), cataratas (H25 y H26, 38.021; suele ser el segundo ojo) y cálculos biliares (K80, 5.337).
- **Obstétricos:** De 89.637, unos 56.000 son el parto (GRD de parto o cesárea) de una mujer hospitalizada antes por su embarazo. El resto sí son complicaciones: trastornos del anteparto (17.932) y del posparto (4.482), entre otros. En el GRD, los trastornos del anteparto y del posparto pertenecen a la CDM 13 y los partos, a la CDM 14.
- **Tasas preliminares:** Sobre unos 5,15 millones de casos de estudio, según qué ingreso se cuente como reingreso:

  | Qué cuenta como reingreso | 30 días | 7 días | 30 días, misma CDM | 7 días, misma CDM |
  |---|---|---|---|---|
  | Cualquier ingreso | 10,04 % | 3,67 % | 5,42 % | 2,05 % |
  | No programado (urgencia y obstétrico) | 6,21 % | 2,18 % | 2,52 % | 0,91 % |
  | No programado y sin partos | 5,16 % | 1,81 % | 2,52 % | 0,91 % |
  | Solo urgencia | 4,50 % | 1,54 % | 2,05 % | 0,74 % |

- **Evidencia:** exploración del 5 de octubre de 2026 sobre la tabla integrada. Son cifras preliminares: las definitivas las entrega el script 09.

### D20 · 2026-10-06 · Qué ingreso cuenta como reingreso
- **Actividad:** 2.2
- **Decisión:** En la etiqueta principal cuenta como reingreso un ingreso no planificado: por urgencia u obstétrico, siempre que no sea un parto ni una cesárea (GRD que comienza con 146 o 147). Los ingresos programados no cuentan. Además se calculan las cuatro variables contando cualquier ingreso, como análisis de sensibilidad.
- **Ventana:** Los días se cuentan desde el alta final del episodio asistencial hasta el ingreso que abre el episodio siguiente de la misma persona. El día 0 cuenta (D19).
- **Reingreso relacionado:** Se cumple si algún ingreso dentro de la ventana tiene la misma CDM que el caso de estudio, no solo el primero. Un reingreso con CDM 99 no cuenta como relacionado (D08).
- **Fundamento:** El resumen de la propuesta habla de reingresos no planificados; la sección de datos define el reingreso como «una admisión posterior», sin filtrar. Con las dos versiones calculadas, la elección no obliga a rehacer el trabajo.
- **Consecuencia:** Es la decisión que más cambia la prevalencia: de 10,0 % a 5,2 % a 30 días (H15).
- **Estado:** Adoptada; se aplica en el script 09. Reemplazada en parte por D26: no se guardan las variables calculadas con cualquier ingreso. Pendiente de validar con profesor guía.

### D21 · 2026-10-06 · Egresos sin identificador, sin fechas válidas o con datos básicos faltantes
- **Actividad:** 2.2
- **Sin identificador:** Los 17.864 egresos sin identificador de paciente (8.307 de 2019) quedan fuera como caso de estudio y como reingreso, porque no se pueden seguir (criterio E01). De ellos, 5.246 son recién nacidos de menos de 28 días; de los otros 12.618, el 85 % tiene una nacionalidad distinta de la chilena y el 55 %, previsión «particular». Los 2.481 egresos con identificador genérico reciben el mismo tratamiento (E02, D18).
- **Fechas:** Los egresos sin fecha de ingreso (71, de los cuales 18 tampoco tienen fecha de alta) o con el alta anterior al ingreso (12) quedan fuera en los dos papeles (E03, 83 egresos). No se corrigen: no se puede saber cuál de las dos fechas es la errónea.
- **Datos básicos:** No son caso de estudio, pero sí pueden contar como reingreso, los egresos sin fecha de nacimiento (37), con fecha de nacimiento posterior al ingreso (1), con más de 110 años al ingreso (26) o sin tipo de alta (101) (E10, 149 egresos).
- **Se conservan:** Las 578 estadías de más de un año.
- **Completa a:** H10 de `docs/bitacora.md`.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H16 · 2026-10-06 · Un reingreso solo se ve si su alta ocurre antes del cierre del bloque
- **Actividad:** 2.2
- **Hallazgo:** Los archivos están organizados por año de alta (H10). Un reingreso que comienza en diciembre de 2024 y termina en 2025 no está en la base, aunque su ingreso caiga dentro de la ventana de 30 días. Lo mismo ocurre en diciembre de 2020, al cierre del bloque A.
- **Magnitud:** Medido en los años que sí tienen el año siguiente disponible (2021, 2022 y 2023): entre las altas ocurridas de 31 a 60 días antes del 31 de diciembre, del 4,2 % al 4,9 % de sus reingresos a 30 días tiene el alta después de esa fecha; entre las ocurridas de 61 a 90 días antes, el 0,9 %.
- **Consecuencia:** Con una censura de 30 días, las altas de noviembre de 2020 y de noviembre de 2024 pierden cerca del 5 % de sus reingresos. Se declara como limitación.
- **Evidencia:** exploración del 5 de octubre de 2026 sobre la tabla integrada (cifras preliminares).
- **Medido de nuevo en:** H20, con la cohorte final y también para la ventana de 7 días.

### D22 · 2026-10-06 · Censura común de 30 días
- **Actividad:** 2.2
- **Decisión:** No son caso de estudio los egresos con alta en los últimos 30 días de su bloque: después del 1 de diciembre de 2020 en el bloque A y después del 1 de diciembre de 2024 en el bloque B (criterio E11). El mismo corte se usa para las variables de 7 y de 30 días, de modo que las cuatro se calculan sobre los mismos casos de estudio.
- **Resultado:** 151.633 egresos cumplen el criterio; aplicado después de los demás, quita 141.391 (59.038 de 2020 y 82.353 de 2024).
- **Alternativa:** Ampliar el margen a 60 días (`censura_dias`) reduce la pérdida descrita en H16 a menos del 1 %, pero quita otros dos meses de casos.
- **Completa a:** D03 de `docs/bitacora.md`.
- **Estado:** Reemplazada por D30 el 8 de octubre de 2026.

### D23 · 2026-10-06 · Tabla de criterios de exclusión
- **Actividad:** 2.2
- **Decisión:** Las exclusiones se aplican como marcas, sin borrar filas: un egreso que no sirve como caso de estudio (por ejemplo, un fallecido) puede ser el reingreso de un alta anterior. Cada criterio es una fila de `reglas/criterios_exclusion.csv`, con su papel (ambos, o solo caso de estudio) y una columna para activarlo o desactivarlo. Los criterios E01 y E03 no se pueden desactivar. Los umbrales están en `reglas/parametros.csv`.
- **Resultado:** Cada criterio se aplica sobre los egresos que quedan después de los anteriores.

  | Código | Criterio | Papel | Activo | Quita |
  |---|---|---|---|---|
  | E01 | Sin identificador de paciente | Ambos | Sí | 17.864 |
  | E02 | Identificador genérico | Ambos | Sí | 2.481 |
  | E03 | Fechas faltantes o alta anterior al ingreso | Ambos | Sí | 81 |
  | E04 | Tipos de actividad que solo existen en 2019 (H09) | Ambos | Sí | 116.962 |
  | E05 | Tramo de un traslado (D19) | Caso | Sí | 97.603 |
  | E06 | Alta por fallecimiento | Caso | Sí | 165.515 |
  | E07 | Alta por derivación a otro hospital | Caso | Sí | 76.605 |
  | E08 | Alta por derivación a una institución privada | Caso | Sí | 22.968 |
  | E09 | Sin GRD válido (D07, D08) | Caso | Sí | 4.799 |
  | E10 | Datos básicos faltantes (D21) | Caso | Sí | 99 |
  | E11 | Ventana de seguimiento incompleta (D22) | Caso | Sí | 141.391 |
  | E12 | Alta voluntaria o fuga del paciente | Caso | No | — |
  | E13 | Cirugía mayor ambulatoria | Caso | No | — |

- **Conjunto final:** De los 5.800.973 egresos de la tabla depurada, 5.154.605 (88,9 %) son caso de estudio y 5.565.982 (95,9 %) pueden contar como reingreso.
- **Criterios desactivados:** La cirugía mayor ambulatoria se conserva porque la propuesta no la excluye: son 851.948 casos de estudio (16,5 %), con un reingreso no planificado a 30 días cercano al 1,1 %, frente al 6,0 % de la hospitalización (cifras preliminares). El alta voluntaria y la fuga se conservan (70.142 casos de estudio). Si se activan, quitan esas cantidades.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 5.
- **Estado:** Adoptada en cuanto a aplicar las exclusiones como marcas en una tabla de criterios. La tabla y sus cifras fueron reemplazadas por D35 el 8 de octubre de 2026; la cirugía mayor ambulatoria dejó de conservarse (D32).

### D24 · 2026-10-06 · Aplicación de la regla de duplicados
- **Actividad:** 2.2
- **Decisión:** Se aplica D15. Se eliminan las 3.818 copias exactas. Cuando varios registros comparten paciente, hospital, fecha de ingreso, fecha de alta, sexo y fecha de nacimiento, se conserva el más completo: se eliminan 3.745 registros. La tabla depurada queda con 5.800.973 egresos.
- **Registros que no se fusionan:** 634 registros, en 312 grupos (302 pares y 10 tríos), comparten paciente, hospital y fechas, pero difieren en el sexo o en la fecha de nacimiento. Según D18, en 146 grupos son personas distintas y en 124 el identificador es genérico. En los otros 42 son la misma persona: no se borran, pero quedan en un mismo episodio asistencial (D19), de modo que solo uno es caso de estudio y ninguno cuenta como reingreso del otro.
- **Corrige a:** D15 de `docs/bitacora.md`, que indicaba 4.067 registros sobrantes (incluía los 322 de estos grupos) y 296 pares con distinto sexo o fecha de nacimiento.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H17 · 2026-10-06 · Un parto no puede tener un reingreso de la misma CDM
- **Actividad:** 2.2
- **Hallazgo:** La CDM 14 contiene solo partos y cesáreas (GRD que comienzan con 146 o 147). Las complicaciones del embarazo y del puerperio pertenecen a la CDM 13. Como un parto no cuenta como reingreso no planificado (D20), un caso de estudio con CDM 14 no puede tener un reingreso relacionado si la relación se mide por coincidencia exacta de CDM.
- **Magnitud:** Los partos son 618.882 casos de estudio (12,0 %). De ellos, 8.938 tienen un reingreso no planificado dentro de 30 días, y en 6.565 (73 %) el primer reingreso es de la CDM 13, sobre todo infecciones y complicaciones del puerperio (O86, O90 y O85). Ejemplo: el egreso `20230009620` (un parto) reingresa a los 5 días por una infección puerperal (`20230594946`, CDM 13).
- **Consecuencia:** Sin corrección, la variable de reingreso relacionado vale 0 en todos los partos, y un modelo aprendería esa regla, que es un efecto de la clasificación y no de los pacientes.
- **Evidencia:** `2.2_depuracion_etiquetado/scripts/09_etiquetar.py` → `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, secciones 5 y 6.
- **Actualizado por:** D31, que deja la comparación sin agrupar y da las cifras de la cohorte final.

### D25 · 2026-10-06 · Las CDM 13 y 14 cuentan como una sola al medir el reingreso relacionado
- **Actividad:** 2.2
- **Decisión:** Para decidir si un reingreso está relacionado con el caso de estudio, las CDM 13 y 14 se tratan como una sola. La columna `CDM` no se modifica: la agrupación solo se usa en esa comparación (parámetro `cdm_agrupadas` = `13+14`).
- **Efecto:** `REING_7D_CDM` pasa de 46.975 a 50.896 casos y `REING_30D_CDM`, de 131.795 a 138.380. Las variables por cualquier causa no cambian. En los partos, el reingreso relacionado a 30 días pasa de 0 a 6.585 casos.
- **Fundamento:** H17. La propuesta mide la relación por coincidencia de CDM y reconoce que es una aproximación gruesa; esta agrupación corrige el único caso en que la aproximación da cero por construcción.
- **Alternativa:** Dejar `cdm_agrupadas` vacío para comparar la CDM tal cual, como dice literalmente la propuesta.
- **Estado:** Reemplazada por D31 el 8 de octubre de 2026.

### D26 · 2026-10-06 · Las variables objetivo son las cuatro de la propuesta, con reingresos no planificados
- **Actividad:** 2.2
- **Decisión:** La tabla etiquetada contiene solo las cuatro variables objetivo de la propuesta, calculadas con reingresos no planificados, como indica su resumen: `REING_7D` y `REING_30D` (por cualquier causa) y `REING_7D_CDM` y `REING_30D_CDM` (relacionado con el diagnóstico). No se guardan las variables calculadas con todo ingreso que preveía D20: esa forma de contar queda solo como una tabla de comparación en el reporte y se activa con el parámetro `reingreso_solo_no_planificado` = NO.
- **Aclaración:** Las cuatro variables están contenidas unas en otras. La ventana de 30 días incluye los primeros 7 días. «Por cualquier causa» significa que no se mira la causa, de modo que incluye a los reingresos relacionados.
- **Resultado:** Sobre 5.154.605 casos de estudio.

  | Variable | Definición | Casos con reingreso | % |
  |---|---|---|---|
  | `REING_7D` | 7 días, por cualquier causa | 93.282 | 1,81 % |
  | `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 50.896 | 0,99 % |
  | `REING_30D` | 30 días, por cualquier causa | 265.874 | 5,16 % |
  | `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 138.380 | 2,68 % |

- **Por año:** El reingreso a 30 días por cualquier causa va de 5,00 % a 5,36 % entre 2019 y 2024: es estable entre los seis años y entre los dos bloques de identificador. El 10,0 % de los reingresos ocurre en un hospital distinto del que dio el alta.
- **Comparación:** Si se contara todo ingreso, también los programados y los partos, las tasas serían 3,67 %, 2,49 %, 10,05 % y 6,74 %, en el mismo orden.
- **Columnas de trazabilidad:** `DIAS_REING` (días hasta el primer reingreso) e `ID_EGRESO_REING` (el egreso que lo constituye). Describen lo que ocurre después del alta y no deben usarse como variables predictoras.
- **Fundamento:** Lo confirmó la persona a cargo de la tesis el 6 de octubre de 2026: el trabajo estudia los reingresos no planificados bajo las cuatro definiciones. Mantener dos versiones de cada definición se prestaba a confusión.
- **Reemplaza a:** la parte de D20 que mantenía una segunda familia de variables.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, secciones 1, 2 y 4.
- **Estado:** Adoptada. Las cifras de esta entrada son las del 6 de octubre de 2026; las vigentes están en el resumen del comienzo y cambiaron por D30 a D33.

### H18 · 2026-10-06 · Sesiones de tratamiento entre los casos de estudio
- **Actividad:** 2.2
- **Hallazgo:** 83.798 casos de estudio (1,6 %) tienen como diagnóstico principal Z51, que corresponde a sesiones de quimioterapia y tratamientos similares. El 58,6 % va seguido de otro ingreso dentro de 30 días, casi siempre programado, y el 8,7 % de un reingreso no planificado. Además, 852 personas tienen 20 o más casos de estudio; la que más tiene, 1.047.
- **Consecuencia:** En las variables objetivo pesan poco, porque los ingresos programados no cuentan como reingreso (D26). Queda por decidir con profesor guía si estas atenciones deben ser caso de estudio; si se excluyen, se agrega un criterio a la tabla de exclusiones.
- **Advertencia para la ingeniería de variables:** Las personas con un solo caso de estudio casi nunca tienen reingreso (0,5 %, frente a 9,6 % con 2 a 5 casos), porque un reingreso es otro egreso de la misma persona. Toda variable que cuente egresos de una persona debe limitarse a los anteriores al alta del caso.
- **Evidencia:** exploración del 6 de octubre de 2026 sobre la tabla etiquetada.
- **Resuelto por:** D33, que deja las sesiones de tratamiento fuera como caso de estudio.
- **Advertencia precisada por:** D42 de la bitácora de la 2.3, del 20 de octubre de 2026: las variables de historia usan los egresos anteriores al ingreso índice, en una ventana de 12 meses, y se marcan los casos cuya ventana empieza antes del inicio de su bloque.

### H20 · 2026-10-08 · Cuántos reingresos se pierden junto al cierre del bloque
- **Actividad:** 2.2
- **Hallazgo:** Como los archivos están organizados por año de alta (H16), un reingreso solo aparece en la base si termina antes del cierre del bloque. No basta con que la ventana quepa entera antes del cierre.
- **Ejemplo ilustrativo:** Una paciente recibe el alta el 20 de diciembre de 2024, reingresa por urgencia el 24 de diciembre y el alta de ese reingreso es el 3 de enero de 2025. El reingreso queda en el archivo de 2025, que no se tiene: en la base, la paciente parece no haber reingresado.
- **Magnitud:** Se midió en los años cuyo año siguiente está en la base con el mismo identificador (2019, 2021, 2022 y 2023), contando qué parte de los reingresos reales no se vería si la base terminara el 31 de diciembre del año del alta.

  | Días entre el alta y el 31 de diciembre | Reingresos a 7 días que no se verían | Reingresos a 30 días que no se verían |
  |---|---|---|
  | 7 a 13 | 40,2 % | — |
  | 14 a 20 | 17,1 % | — |
  | 21 a 29 | 9,5 % | — |
  | 30 a 36 | 4,9 % | 16,4 % |
  | 37 a 59 | 2,4 % | 5,3 % |
  | 60 a 89 | 0,9 % | 1,5 % |
  | 90 a 120 | 0,2 % | 0,5 % |

- **Estadía de los reingresos:** La mediana es de 6 días y el 95 % dura 33 días o menos (exploración del 8 de octubre de 2026): con 30 días de margen, casi todos terminan antes del cierre.
- **Completa a:** H16.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, sección 6.

### D30 · 2026-10-08 · Censura diferenciada por ventana, con margen
- **Actividad:** 2.2
- **Decisión:** Cada ventana tiene su propio corte: sus días más un margen de 30 días antes del cierre del bloque. Las variables de 7 días tienen dato si el alta ocurre al menos 37 días antes del cierre (hasta el 24 de noviembre de 2020 o de 2024) y las de 30 días, si ocurre al menos 60 días antes (hasta el 1 de noviembre). El criterio E11 deja fuera como caso de estudio solo a los egresos que no alcanzan el seguimiento de la ventana más corta. Un caso de estudio con entre 37 y 59 días de seguimiento conserva las variables de 7 días y queda sin dato en las de 30 días.
- **Fundamento:** El profesor guía indicó en su revisión del 7 de octubre de 2026 que para la ventana de 7 días no es necesario eliminar 30 días de seguimiento. El margen se agrega por H20: sin él, se etiquetarían como «sin reingreso» casos cuyo reingreso no se ve.
- **Resultado:** E11 quita 176.057 egresos (73.672 de 2020 y 102.385 de 2024). Quedan 4.192.410 casos de estudio con las variables de 7 días y 4.101.883 con las de 30 días; 90.527 casos tienen solo las de 7 días.
- **Alternativa:** Sin margen (`censura_margen_dias` = 0) habría 4.313.289 casos para 7 días y 4.220.181 para 30 días. Los casos que así ganan dato tienen una tasa observada menor que el resto (1,73 % frente a 2,07 % a 7 días y 5,60 % frente a 5,90 % a 30 días), porque parte de sus reingresos no se ve. Las tasas totales cambian poco: 2,06 %, 1,07 %, 5,89 % y 3,02 %.
- **Seguimiento por bloques:** Se mantiene D03. Un reingreso que cruza de diciembre de 2020 a 2021 es inobservable, porque el identificador cambia, y esa limitación no se corrige con imputación ni con emparejamiento heurístico de pacientes.
- **Parámetros:** `ventanas_dias` (7 y 30) y `censura_margen_dias` (30).
- **Reemplaza a:** D22.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 5; `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, sección 6.
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026, con el margen de 30 días: lo considera bien respaldado, porque baja la pérdida de reingresos junto al cierre a 2,4 % (7 días) y 1,5 % (30 días) y casi no cambia las tasas.

### D31 · 2026-10-08 · El reingreso relacionado se mide con la misma CDM, sin agrupar
- **Actividad:** 2.2
- **Decisión:** Para decidir si un reingreso está relacionado con el caso de estudio se compara la CDM tal cual, sin agrupar ninguna (`cdm_agrupadas` vacío). La unión de las CDM 13 y 14 se informa solo como análisis de sensibilidad (`cdm_sensibilidad` = `13+14`).
- **Fundamento:** Revisión del profesor guía del 7 de octubre de 2026: la unión modifica por construcción la variable y no tiene una justificación clínica explícita en el protocolo.
- **Resultado:** `REING_7D_CDM` tiene 45.195 casos (1,08 %) y `REING_30D_CDM`, 124.256 (3,03 %). Con las CDM 13 y 14 unidas serían 49.087 (1,17 %) y 130.654 (3,19 %): 3.892 y 6.398 casos más.
- **Consecuencia:** Con la comparación literal, ninguno de los 603.423 partos con seguimiento de 30 días (CDM 14) tiene reingreso relacionado, porque la CDM 14 solo contiene partos y un parto no cuenta como reingreso (H17). Con la unión serían 6.398. Debe declararse como limitación: en las variables relacionadas, el valor 0 de los partos es un efecto de la clasificación.
- **Reemplaza a:** D25.
- **Completada por:** D38, del 20 de octubre de 2026: los partos quedan sin dato en las dos variables relacionadas, en vez de 0.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, sección 5.
- **Estado:** Adoptada, por recomendación del profesor guía.

### D32 · 2026-10-08 · La cirugía mayor ambulatoria no es caso de estudio
- **Actividad:** 2.2
- **Decisión:** Se activa el criterio E13: los egresos de cirugía mayor ambulatoria no son caso de estudio. Siguen pudiendo contar como reingreso de un alta anterior, si son un ingreso no planificado.
- **Fundamento:** Revisión del profesor guía del 7 de octubre de 2026: es un proceso asistencial distinto de la hospitalización convencional, y el estudio trata del reingreso después de un egreso hospitalario.
- **Resultado:** 885.384 egresos cumplen el criterio; aplicado después de los anteriores, quita 845.604. Todos los casos de estudio son hospitalizaciones.
- **Sensibilidad:** Con la cirugía mayor ambulatoria habría 5.036.703 casos de estudio y las tasas bajarían a 1,79 %, 0,92 %, 5,10 % y 2,58 %. Por sí sola tiene 0,41 %, 0,14 %, 1,14 % y 0,33 %. Es la decisión que más cambia las tasas.
- **Modifica a:** D23, que la conservaba.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, secciones 1 y 3.
- **Estado:** Adoptada, por recomendación del profesor guía.

### D33 · 2026-10-08 · Las sesiones de tratamiento no son caso de estudio ni cuentan como reingreso
- **Actividad:** 2.2
- **Decisión:** Se agrega el criterio E14: un egreso cuyo diagnóstico principal comienza con Z51 (sesión de tratamiento) no es caso de estudio. Además, un ingreso con ese diagnóstico principal no cuenta como reingreso no planificado, cualquiera sea su tipo de ingreso (parámetro `diagnosticos_sesion`).
- **Caracterización:** Son 81.925 casos de estudio de 28.428 personas; 229 personas tienen 20 o más y suman 9.264 (11,3 %). El 98,1 % ingresa de forma programada. El 60,4 % es Z51.1 y el 26,1 %, Z51.8. El 29,2 % ingresa y egresa el mismo día; la mediana de la estadía es de 2 días. El 59,3 % va seguido de otro ingreso dentro de 30 días, contando los programados, y el 8,15 %, de un reingreso no planificado.
- **Regla completa de «no planificado»:** En orden de precedencia: (1) el ingreso debe abrir un episodio asistencial nuevo; (2) si su GRD comienza con 146 o 147, es un parto y no cuenta; (3) si su diagnóstico principal comienza con Z51, es una sesión y no cuenta; (4) cuenta si su tipo de ingreso es `URGENCIA` u `OBSTETRICA`; (5) no cuenta si es otro o si falta. Señales contradictorias resueltas por ese orden: 2.493 partos con un tipo de ingreso distinto de obstétrico, 1.649 sesiones con tipo de ingreso no programado y 339 ingresos sin tipo.
- **Fundamento:** Revisión del profesor guía del 7 de octubre de 2026: son atenciones planificadas o repetitivas, con una dinámica distinta de la del episodio agudo, y una sesión programada posterior no debe etiquetarse como reingreso.
- **Resultado:** 100.229 egresos cumplen el criterio; aplicado al final, quita 81.925.
- **Sensibilidad:** Con las sesiones como caso de estudio habría 4.274.335 casos y las tasas serían 2,08 %, 1,06 %, 5,94 % y 2,99 %.
- **Completa a:** D20 y D26. **Responde a:** H18.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, sección 4; `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, sección 4.
- **Estado:** Adoptada, por recomendación del profesor guía.

### H21 · 2026-10-08 · Identidad ambigua: qué cambia dentro de un identificador
- **Actividad:** 2.2
- **Hallazgo:** 30.616 identificadores (0,76 %) aparecen con más de un sexo o con más de una fecha de nacimiento, sin contar los datos faltantes. Reúnen 96.824 egresos y 63.278 casos de estudio (1,51 %).

  | Qué cambia dentro del identificador | Resultado de la regla D18 | Identificadores | Egresos | Casos de estudio |
  |---|---|---|---|---|
  | Solo el sexo | Una persona | 6.846 | 22.760 | 14.674 |
  | Solo la fecha de nacimiento | Una persona | 19.454 | 59.134 | 39.318 |
  | Solo la fecha de nacimiento | Varias personas | 2.800 | 8.135 | 5.918 |
  | El sexo y la fecha de nacimiento | Una persona | 389 | 1.333 | 856 |
  | El sexo y la fecha de nacimiento | Varias personas | 1.115 | 2.981 | 2.512 |
  | El sexo y la fecha de nacimiento | Sin persona (identificador genérico) | 12 | 2.481 | 0 |

- **Cuántos cambian de persona:** La regla separa en varias personas 3.915 identificadores (11.116 egresos y 8.430 casos de estudio); 4.964 de esos egresos (3.552 casos de estudio) quedan asignados a la segunda persona o a una posterior. En sentido contrario, 19.843 identificadores con más de una fecha de nacimiento se mantienen como una sola persona (60.467 egresos y 40.174 casos de estudio). Los más dudosos son los 389 identificadores con sexo y fecha de nacimiento distintos a la vez que quedan como una persona.
- **Tasas:** Los casos de estudio con identidad ambigua tienen cerca del doble de reingreso que el resto: 4,18 %, 2,17 %, 12,88 % y 6,61 %, frente a 2,03 %, 1,06 %, 5,79 % y 2,97 %. No prueba que haya reingresos falsos: un identificador con más egresos tiene más oportunidades de registrar un dato distinto, y también más reingresos.
- **Precisa a:** H13.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 3; `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, sección 7.

### D34 · 2026-10-08 · Se conserva una marca de identidad ambigua
- **Actividad:** 2.2
- **Decisión:** La tabla depurada tiene la columna `IDENTIDAD_AMBIGUA`, verdadera en los egresos de los identificadores de H21. La regla D18 se mantiene como definición operativa, pero esos egresos no se tratan como identidades ciertas: quedan marcados para poder repetir cualquier análisis sin ellos. No se excluyen del análisis principal.
- **Fundamento:** Revisión del profesor guía del 7 de octubre de 2026: no conviene transformar una inconsistencia administrativa en una identidad individual con certeza aparente.
- **Sensibilidad:** Sin los casos con identidad ambigua quedarían 4.129.132 casos de estudio, con tasas de 2,03 %, 1,06 %, 5,79 % y 2,97 %.
- **Completa a:** D18.
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026: excluir esos casos casi no cambia las tasas (a 30 días, de 5,90 % a 5,79 %) y la marca permite repetir el análisis sin ellos.

### H22 · 2026-10-08 · La regla de traslado coincide con las marcas explícitas
- **Actividad:** 2.2
- **Hallazgo:** La regla D19 se comparó con las dos marcas de traslado que trae la base: que el alta anterior sea por derivación, o que el ingreso declare que procede de otro hospital. Ingresos en un hospital distinto del que dio el alta anterior, según los días transcurridos:

  | Ingreso en otro hospital | Egresos | Con marca de traslado | Los une la regla |
  |---|---|---|---|
  | Antes del alta anterior (estadías solapadas) | 9.939 | 68,2 % | Sí |
  | El mismo día del alta | 70.933 | 96,8 % | Sí |
  | Al día siguiente | 16.126 | 90,6 % | Sí |
  | 2 días después | 2.600 | 47,0 % | No |
  | 3 días después | 2.073 | 36,2 % | No |
  | 4 a 7 días después | 7.818 | 26,7 % | No |
  | 8 a 30 días después | 27.826 | 22,3 % | No |

- **Concordancia:** Dentro de los primeros 7 días, la regla une 96.998 ingresos, de los que el 92,9 % tiene marca, y no une 12.491, de los que el 67,5 % no la tiene. Las marcas tampoco son exactas: tiene marca el 6,1 % de los ingresos al mismo hospital dentro de 7 días, que no son traslados.
- **Consecuencia:** La proporción con marca cae de 90,6 % a 47,0 % entre el día siguiente y el segundo día, lo que respalda el corte de la regla (`traslado_dias_max` = 1). La regla se presenta como una definición operacional.
- **Completa a:** H14 y D19.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 4.

### H23 · 2026-10-08 · Derivados sin continuación observable, por año y por hospital
- **Actividad:** 2.2
- **Hallazgo:** Los criterios E07 y E08 dejan fuera 99.573 egresos derivados cuya continuación no se ve (76.605 a otro hospital y 22.968 a una institución privada). Es una censura administrativa del seguimiento, no una característica clínica del paciente.

  | | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
  |---|---|---|---|---|---|---|
  | Excluidos por E07 y E08 | 14.302 | 17.122 | 18.201 | 14.507 | 16.545 | 18.896 |
  | % de los egresos del año | 1,2 % | 2,2 % | 2,2 % | 1,6 % | 1,6 % | 1,7 % |
  | Derivados a otro hospital con continuación visible | 47,7 % | 44,0 % | 48,0 % | 51,6 % | 54,6 % | 54,3 % |
  | Lo mismo, en los 65 hospitales presentes todos los años | 47,7 % | 44,0 % | 48,0 % | 51,6 % | 54,2 % | 52,8 % |

- **Por hospital:** La proporción de derivados con continuación visible va de 15,9 % a 92,9 % según el hospital (mediana 60,0 %): depende de si el hospital de destino informa a la base.
- **Cobertura:** La continuación visible sube desde 2022, también en los 65 hospitales presentes todos los años. Hay un cambio de cobertura moderado, que debe declararse.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 4 y anexo; `2.2_depuracion_etiquetado/reportes/08_derivaciones_por_hospital.csv`.

### H24 · 2026-10-08 · Tasas por hospital y aumento de la tasa en 2023 y 2024
- **Actividad:** 2.2
- **Hallazgo:** La tasa de reingreso a 30 días por cualquier causa va de 3,01 % a 14,28 % entre los 72 hospitales (mediana 5,95 %; la mitad central, entre 5,27 % y 6,73 %). Por año es 5,70 %, 5,66 %, 5,62 %, 5,77 %, 6,14 % y 6,45 %: sube en 2023 y 2024.
- **No se debe a los hospitales incorporados:** En los 65 hospitales presentes todos los años, la tasa también sube (6,13 % en 2023 y 6,36 % en 2024), y sin contar los reingresos que ocurren en un hospital incorporado después queda en 6,11 % y 6,31 %. La incorporación de hospitales (H05) explica entre 0,02 y 0,05 puntos. Los 7 hospitales incorporados tienen tasas más altas (7,71 % y 9,31 %), pero pocos casos de estudio (8.915 en 2023 y 21.206 en 2024).
- **Composición:** Entre 2019 y 2024, los casos de estudio de 65 años o más pasan de 22,1 % a 25,8 % y los de ingreso obstétrico, de 21,7 % a 18,2 %. La tasa sube además dentro de cada tipo de ingreso: en urgencia, de 7,39 % a 7,85 % (exploración del 8 de octubre de 2026).
- **Consecuencia:** Es un cambio real en el tiempo. Una partición aleatoria no mide por sí sola cómo generaliza un modelo frente a ese cambio: respalda la evaluación temporal complementaria que pide el profesor guía.
- **Completa a:** H05 de `docs/bitacora.md`.
- **Completado por:** H28, del 20 de octubre de 2026: la calidad del identificador tampoco explica el aumento.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, secciones 2 y 7 y anexo; `2.2_depuracion_etiquetado/reportes/09_tasas_por_hospital.csv`.

### H25 · 2026-10-08 · Análisis de sensibilidad de las decisiones
- **Actividad:** 2.2
- **Hallazgo:** Cada fila cambia una sola decisión y vuelve a calcular las cuatro variables con las mismas funciones de los scripts 08 y 09.

  | Escenario | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|---|
  | Análisis principal | 4.192.410 | 2,07 % | 1,08 % | 5,90 % | 3,03 % |
  | Con las actividades que solo existen en 2019 (E04) | 4.275.385 | 2,11 % | 1,10 % | 5,99 % | 3,07 % |
  | Con la cirugía mayor ambulatoria (E13) | 5.036.703 | 1,79 % | 0,92 % | 5,10 % | 2,58 % |
  | Con las sesiones de tratamiento (E14) | 4.274.335 | 2,08 % | 1,06 % | 5,94 % | 2,99 % |
  | Con las CDM 13 y 14 como una sola | 4.192.410 | 2,07 % | 1,17 % | 5,90 % | 3,19 % |
  | Censura sin margen | 4.313.289 | 2,06 % | 1,07 % | 5,89 % | 3,02 % |
  | Sin los casos con identidad ambigua | 4.129.132 | 2,03 % | 1,06 % | 5,79 % | 2,97 % |

- **Actividades de 2019:** Al incluirlas, la tasa a 30 días de 2019 pasaría de 5,70 % a 6,15 % y ese año dejaría de ser comparable con los demás. Se agregarían 43.217 casos de hospitalización en urgencia (10,06 % de reingreso a 30 días) y 39.855 de hospitalización diurna (4,02 %), y cambiaría la composición clínica: la CDM 14 bajaría de 15,4 % a 14,0 % de los casos de 2019 y la CDM 11 subiría de 4,8 % a 5,9 %. Respalda mantener E04 (H09).
- **Conclusión:** La única decisión que cambia mucho las tasas es la cirugía mayor ambulatoria. Las demás las mueven menos de 0,2 puntos.
- **Evidencia:** `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py` → `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`.
- **Actualizado por:** H27, del 20 de octubre de 2026, con las variables relacionadas sin los partos (D38) y dos filas nuevas (traslados y derivados).

### D35 · 2026-10-08 · Tabla final de criterios de exclusión
- **Actividad:** 2.2
- **Decisión:** `reglas/criterios_exclusion.csv` queda con catorce criterios, cada uno con una justificación breve (columna `justificacion`). Trece están activos; E12 se mantiene desactivado. Los duplicados no son un criterio: se eliminan antes y se cuentan aparte (3.818 copias exactas y 3.745 registros repetidos, D24).

  | Código | Criterio | Papel | Activo | Quita |
  |---|---|---|---|---|
  | E01 | Sin identificador de paciente | Ambos | Sí | 17.864 |
  | E02 | Identificador genérico | Ambos | Sí | 2.481 |
  | E03 | Fechas faltantes o alta anterior al ingreso | Ambos | Sí | 81 |
  | E04 | Tipos de actividad que solo existen en 2019 (H09) | Ambos | Sí | 116.962 |
  | E05 | Tramo de un traslado (D19) | Caso | Sí | 97.603 |
  | E06 | Alta por fallecimiento | Caso | Sí | 165.515 |
  | E07 | Alta por derivación a otro hospital | Caso | Sí | 76.605 |
  | E08 | Alta por derivación a una institución privada | Caso | Sí | 22.968 |
  | E09 | Sin GRD válido (D07, D08) | Caso | Sí | 4.799 |
  | E10 | Datos básicos faltantes (D21) | Caso | Sí | 99 |
  | E11 | Seguimiento incompleto (D30) | Caso | Sí | 176.057 |
  | E12 | Alta voluntaria o fuga del paciente | Caso | No | — |
  | E13 | Cirugía mayor ambulatoria (D32) | Caso | Sí | 845.604 |
  | E14 | Sesión de tratamiento, diagnóstico principal Z51 (D33) | Caso | Sí | 81.925 |

- **Conjunto final:** De los 5.800.973 egresos de la tabla depurada, 4.192.410 (72,3 %) son caso de estudio y 5.565.982 (95,9 %) pueden contar como reingreso.
- **Criterio desactivado:** El alta voluntaria y la fuga se conservan: son 69.296 casos de estudio con más reingreso que el resto (12,69 % y 20,08 % a 30 días, frente a 5,57 % del alta a domicilio), y dejarlos fuera quitaría un grupo de mayor riesgo.
- **Reemplaza a:** la tabla de D23.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 5.
- **Estado:** Adoptada. El profesor guía la aprobó el 13 de octubre de 2026 a condición de incorporar los puntos 2.1 y 2.4 de su revisión, incorporados el 20 de octubre (H26, H27, D38 y D39). Los catorce criterios no cambiaron.

### D36 · 2026-10-08 · Versión del conjunto analítico, diccionario y pruebas independientes
- **Actividad:** 2.2
- **Decisión:** El conjunto analítico es `data/processed/grd_etiquetado.parquet`. Su versión se registra en `docs/version_conjunto_analitico.csv` con el hash SHA-256 del archivo y de lo que lo produce (tabla integrada, tablas de reglas y scripts 08 y 09). El diccionario de sus 163 columnas está en `docs/diccionario_conjunto_analitico.md`. Ambos los genera el script 12.
- **Versión 1:** Registrada el 8 de octubre de 2026. SHA-256 `b4016246501d73a6bafa3fde20ab8b8c58e7482cbc259da8730f5b6dd70cbfe5`; 5.800.973 registros, 163 columnas y 4.192.410 casos de estudio.
- **Versión 2:** Registrada el 20 de octubre de 2026, con D38. SHA-256 `f9b8be4065bad16dfe27a46a95db4f742024b1e817046d1d9b26e0a893b900dc`; mismos registros, columnas y casos de estudio. Respecto de la versión 1 solo cambian `REING_7D_CDM` y `REING_30D_CDM` de los partos (615.167 y 603.423 celdas, todas de 0 a sin dato).
- **Uso:** La partición (actividad 2.3) debe comprobar que el archivo que lee tiene el hash de la última versión registrada. Si se vuelven a ejecutar los scripts 08 o 09 y el archivo cambia, hay que registrar una versión nueva.
- **Pruebas independientes:** Los tres programas que contrastan los resultados con otro método quedan en `2.2_depuracion_etiquetado/pruebas/`. `ejecutar_pruebas.py` los ejecuta y deja `reportes/pruebas_independientes.md`.
- **Fundamento:** Revisión del profesor guía del 7 de octubre de 2026: mantener pruebas automáticas y el versionado del conjunto analítico, y entregar el diccionario final con la versión o el hash del conjunto que se usará en la partición.
- **Estado:** Adoptada.

### H26 · 2026-10-20 · La CDM 14 solo contiene partos y las complicaciones del puerperio están en la CDM 13
- **Actividad:** 2.2
- **Contexto:** En su revisión del 13 de octubre de 2026 (punto 2.1), el profesor guía pidió verificar qué GRD agrupa la CDM 14 en la base: en los sistemas GRD, la categoría de embarazo, parto y puerperio suele incluir también los ingresos antes y después del parto, y si estuvieran en la CDM 14, que ninguno cuente como reingreso relacionado de un parto apuntaría a un error en la regla.
- **Hallazgo:** En esta base, la CDM 14 tiene solo 15 GRD y todos son partos o cesáreas: los 12 hospitalarios 146101 a 146133 (cesárea; parto vaginal con esterilización o legrado; parto vaginal con otros procedimientos; parto vaginal; cada uno en tres niveles de severidad), con 640.199 egresos y los 615.167 casos de estudio de la CDM, y tres ambulatorios (147100, 147120 y 147130) con 46 egresos y ningún caso de estudio. Los ingresos del embarazo y del puerperio que no son partos están en la CDM 13: «Trastornos del postparto» (134171 a 134173, 7.433 egresos), «Trastornos del anteparto», aborto, amenaza de aborto y falso trabajo de parto.
- **Por qué el 0:** Un parto no cuenta como reingreso (D20, D33), así que ningún reingreso puede ser de la CDM 14; y una complicación del puerperio es de la CDM 13, que con la comparación literal (D31) no coincide con la 14. No es un error de la regla: es la clasificación GRD combinada con la comparación literal.
- **Magnitud:** De los 603.423 partos con seguimiento de 30 días, 8.686 (1,44 %) tienen un reingreso no planificado dentro de 30 días. El primero es de la CDM 13 en el 73,4 % (6.379), sobre todo «Trastornos del postparto» (134171 y 134172: 43,4 %) y «Trastornos del anteparto» (134161: 9,1 %); los diagnósticos más frecuentes son O86, O90 y O85 (infecciones y complicaciones del puerperio). Ejemplo: el egreso `20230009620` (parto vaginal, GRD 146131) reingresa a los 5 días por una sepsis puerperal (`20230594946`, O85, GRD 134171, CDM 13): vale 1 en `REING_7D` y `REING_30D` y 0 en las dos variables relacionadas.
- **Solo la CDM 14:** Ninguna otra CDM tiene una tasa de reingreso relacionado igual a 0. La siguiente más baja es la CDM 22 (quemaduras), con 0,82 % a 30 días.
- **Completa a:** H17, con las cifras de la cohorte final.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, sección 5 (GRD de la CDM 14 con las descripciones de la tabla maestra del DEIS, y CDM, GRD y diagnóstico del primer reingreso de los partos).

### D38 · 2026-10-20 · Los partos quedan sin dato en las dos variables relacionadas
- **Actividad:** 2.2
- **Decisión:** Los casos de estudio de la CDM 14 (partos) quedan sin dato en `REING_7D_CDM` y `REING_30D_CDM`, igual que un caso sin seguimiento suficiente queda sin dato en las variables de 30 días. Conservan las dos variables por cualquier causa, en las que sí tienen reingresos reales (0,77 % a 7 días y 1,44 % a 30 días). Se aplica con el parámetro `cdm_sin_relacionado` = 14. Si `cdm_agrupadas` une la CDM 14 con otra, los partos vuelven a tener dato, porque entonces sí pueden tener un reingreso relacionado.
- **Fundamento:** Revisión del profesor guía del 13 de octubre de 2026 (punto 2.1). Con la comparación literal, los partos son un cero estructural: el 14,7 % de los casos de estudio tendría 0 por construcción, un modelo acertaría en todos ellos sin aprender nada sobre el reingreso, lo que infla las métricas, y en la selección de variables la CDM 14 y los diagnósticos del parto aparecerían como importantes por esa razón. Pidió excluir los partos de la cohorte de las dos variables relacionadas, o modelarlos aparte, y reportar sus tasas sin partos.
- **Resultado:** `REING_7D_CDM`: 45.195 de 3.577.243 casos (1,26 %); `REING_30D_CDM`: 124.256 de 3.498.460 (3,55 %). Los reingresos no cambian: solo baja el número de casos con dato. Las variables por cualquier causa, `DIAS_REING` e `ID_EGRESO_REING` quedan idénticas.
- **Alternativa descartada:** Modelar los partos aparte. En las dos variables relacionadas no tienen ningún caso positivo (0 de 615.167), así que no hay nada que modelar.
- **Sensibilidad:** Con los partos con valor 0, como antes, las tasas serían 1,08 % y 3,03 %. Con las CDM 13 y 14 unidas, los partos tienen dato y las tasas son 1,17 % y 3,19 % (6.398 partos con reingreso relacionado a 30 días). Ambas filas están en el reporte 11.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 20 de octubre de 2026 («si esto es lo que recomienda el profesor, sí»).
- **Completa a:** D31 y H17. Se fundamenta en H26.
- **Alcance:** Solo se aplica cuando cuentan únicamente los ingresos no planificados (`reingreso_solo_no_planificado` = SI). Si se cuenta todo ingreso, un parto también es reingreso y los partos sí pueden tener un reingreso relacionado.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, secciones 1 y 5; `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`.
- **Estado:** Adoptada, por recomendación del profesor guía.

### H27 · 2026-10-20 · Tabla de sensibilidad actualizada: partos, traslados y derivados
- **Actividad:** 2.2
- **Contexto:** En su revisión del 13 de octubre de 2026 (punto 2.4), el profesor guía pidió dos filas nuevas en la tabla de sensibilidad: una que una solo los traslados con marca explícita, para ver cuánto cambia la tasa a 7 días, y otra para los derivados sin continuación (D39). Con D38, además, cambian las tasas de las variables relacionadas del análisis principal.
- **Hallazgo:** Cada fila cambia una sola decisión y vuelve a calcular las cuatro variables con las mismas funciones de los scripts 08 y 09. En las dos variables relacionadas, los partos quedan sin dato salvo en las filas que los vuelven a incluir (la de los partos con valor 0 y la de las CDM 13 y 14 unidas).

  | Escenario | Casos de estudio | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|---|
  | Análisis principal | 4.192.410 | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
  | Con las actividades que solo existen en 2019 (E04) | 4.275.385 | 2,11 % | 1,29 % | 5,99 % | 3,59 % |
  | Con la cirugía mayor ambulatoria (E13) | 5.036.703 | 1,79 % | 1,05 % | 5,10 % | 2,94 % |
  | Con las sesiones de tratamiento (E14) | 4.274.335 | 2,08 % | 1,24 % | 5,94 % | 3,50 % |
  | Con los partos en las variables relacionadas, con valor 0 | 4.192.410 | 2,07 % | 1,08 % | 5,90 % | 3,03 % |
  | Con las CDM 13 y 14 como una sola | 4.192.410 | 2,07 % | 1,17 % | 5,90 % | 3,19 % |
  | Censura sin margen | 4.313.289 | 2,06 % | 1,26 % | 5,89 % | 3,54 % |
  | Solo los traslados con marca explícita | 4.195.786 | 2,12 % | 1,30 % | 5,95 % | 3,59 % |
  | Con los derivados sin continuación como casos de estudio (E07 y E08) | 4.286.199 | 2,12 % | 1,30 % | 5,98 % | 3,59 % |
  | Sin los casos con identidad ambigua | 4.129.132 | 2,03 % | 1,25 % | 5,79 % | 3,49 % |

- **Traslados:** De los 96.998 ingresos en otro hospital que la regla D19 une dentro de 7 días, 6.916 (7,1 %) no tienen marca de traslado. De ellos, 3.161 comienzan antes del alta anterior (estadías solapadas): la persona todavía no había salido, no pueden ser un reingreso con ninguna regla y siguen unidos. Exigir la marca separa los otros 3.755 (2.244 del mismo día del alta y 1.511 del día siguiente). Resultado: 3.376 casos de estudio más y 75 casos comunes con alguna variable distinta; los casos con `REING_7D` pasan de 86.609 a 88.742 (2.133 más, un 2,5 %) y la tasa, de 2,07 % a 2,12 %. El peor caso estimado en la revisión (cerca del 8 % de los reingresos a 7 días) incluía las estadías solapadas; el efecto medido es de 2,5 % y ninguna tasa cambia más de 0,05 puntos. Se mantiene la regla D19.
- **Conclusión:** La única decisión que cambia mucho las tasas sigue siendo la cirugía mayor ambulatoria. Dejar los partos sin dato sube las tasas de las variables relacionadas (1,08 % y 3,03 % pasan a 1,26 % y 3,55 %) solo porque baja el número de casos con dato: los reingresos son los mismos. Los traslados y los derivados mueven las tasas 0,08 puntos o menos.
- **Actualiza a:** H25.
- **Evidencia:** `2.2_depuracion_etiquetado/scripts/11_sensibilidad.py` → `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, secciones 1, 5, 6, 8 y 9.

### D39 · 2026-10-20 · Regla de los derivados sin continuación, declarada
- **Actividad:** 2.2
- **Decisión:** Se declara la regla vigente desde D19 y D23. Los egresos con alta por derivación a otro hospital cuya continuación no aparece en la base (E07, 76.605) y los derivados a una institución privada (E08, 22.968) no son casos de estudio: no tienen valor en ninguna de las cuatro variables objetivo, de modo que no quedan como «sin reingreso». Sí pueden contar como reingreso de un alta anterior (95.720 de los 99.573). Un derivado cuya continuación sí aparece en la base es un tramo de traslado (E05) y su episodio sigue en el hospital de destino.
- **Contexto:** En su revisión del 13 de octubre de 2026 (punto 2.4), el profesor guía señaló que el informe describía a estos egresos como una censura administrativa del seguimiento, pero no decía cómo entraban a las variables objetivo: si quedaran como casos de estudio con valor 0, serían falsos negativos, porque la persona siguió su atención donde la base no la ve. Pidió declarar la regla y agregar una fila que los excluya como casos de estudio. Como el análisis principal ya los excluye, la fila de sensibilidad es la inversa: los incluye.
- **Sensibilidad:** Con E07 y E08 desactivados se agregan 93.789 casos de estudio (los demás derivados quedan fuera por criterios posteriores de la tabla). Tienen más reingreso observado que el resto (4,38 % a 7 días y 9,42 % a 30 días, frente a 2,07 % y 5,90 %), aunque parte de su seguimiento ocurre fuera de la base. Las tasas totales suben 0,05 puntos a 7 días y 0,08 a 30 días (H27).
- **Visto bueno:** La persona a cargo de la tesis aprobó el 20 de octubre de 2026 la fila de traslados con marca y la de derivados al revés.
- **Reafirma a:** D19 y D23 (criterios E07 y E08). Completa a H23.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 4; `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`, sección 9.
- **Estado:** Adoptada.

### H28 · 2026-10-20 · La calidad del identificador no explica el aumento de 2023 y 2024
- **Actividad:** 2.2
- **Contexto:** En su revisión del 13 de octubre de 2026 (punto 2.3), el profesor guía pidió revisar por año la proporción de identificadores ambiguos o faltantes antes de tratar el aumento de la tasa en 2023 y 2024 (H24) como un cambio real: una mejora en la calidad del identificador también hace visibles más reingresos.
- **Hallazgo:** Por año del alta, en la tabla depurada:

  | | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
  |---|---|---|---|---|---|---|
  | Egresos sin identificador de paciente (E01) | 0,72 % | 0,24 % | 0,25 % | 0,32 % | 0,16 % | 0,10 % |
  | Egresos con identificador genérico (E02) | 0,02 % | 0,10 % | 0,04 % | 0,07 % | 0,04 % | 0,01 % |
  | Egresos con identidad ambigua | 1,61 % | 1,53 % | 1,65 % | 1,84 % | 1,67 % | 1,69 % |
  | Casos de estudio con identidad ambigua | 1,32 % | 1,27 % | 1,52 % | 1,70 % | 1,59 % | 1,63 % |
  | `REING_30D`, todos los casos | 5,70 % | 5,66 % | 5,62 % | 5,77 % | 6,14 % | 6,45 % |
  | `REING_30D`, sin identidad ambigua | 5,58 % | 5,52 % | 5,53 % | 5,67 % | 6,05 % | 6,35 % |

- **Interpretación:** Los egresos sin identificador bajan de 0,32 % en 2022 a 0,16 % en 2023 y 0,10 % en 2024. Si se reparten como el resto de los egresos, esa diferencia haría visibles cerca de un 0,2 % más de reingresos, del orden de 0,01 puntos de tasa, mientras la subida es de 0,37 puntos en 2023 y 0,68 en 2024. La identidad ambigua no tiene tendencia (entre 1,5 % y 1,8 % de los egresos), y sin esos casos la tasa sube igual: 5,67 %, 6,05 % y 6,35 %. En 2019, con más egresos sin identificador (0,72 %), la tasa es igual a la de 2020 a 2022.
- **Consecuencia:** El aumento de 2023 y 2024 no se explica por cambios en la calidad del identificador. Junto con H24 (no se debe a los hospitales incorporados y ocurre dentro de cada tipo de ingreso), se trata como un cambio real en el tiempo, que es lo que mide la validación temporal (D37 y D40 de la bitácora de la 2.3).
- **Completa a:** H24.
- **Evidencia:** `2.2_depuracion_etiquetado/reportes/09_etiquetado.md`, sección 2 («Calidad del identificador»).

---

## Verificación del script 08

El script se ejecutó el 6 de octubre de 2026 y dejó `data/processed/grd_depurado.parquet` (5.800.973
egresos, 155 columnas). Antes se había probado completo con la salida en una carpeta temporal: el
archivo definitivo es idéntico, byte a byte, al de la prueba. El resultado se contrastó con un segundo
cálculo escrito de otra forma, sin ninguna diferencia:

- Las 134 columnas originales de la tabla depurada son idénticas, celda a celda, a las de la tabla integrada.
- Cada registro repetido eliminado tiene un registro conservado con la misma clave y al menos igual de completo.
- La asignación de personas coincide con la regla D18 en los 23.609 identificadores con dos fechas de nacimiento y en los 149 con tres o más.
- Los episodios asistenciales, recalculados con un recorrido egreso por egreso, coinciden en los 5.663.585 egresos que se pueden seguir.
- Los trece criterios, recalculados con otra biblioteca, no tienen ninguna diferencia.

## Verificación del script 09

El script se ejecutó el 6 de octubre de 2026 y dejó `data/processed/grd_etiquetado.parquet` (5.800.973
egresos, 161 columnas). También se probó antes con la salida en una carpeta temporal, con un resultado
idéntico. El contraste independiente no encontró ninguna diferencia:

- Las cuatro variables, recalculadas caso por caso con un programa escrito de otra forma, coinciden en los 5.154.605 casos de estudio.
- En una muestra del 4 % de los identificadores (206.713 casos de estudio), el cálculo como unión literal de cada alta con los ingresos posteriores de la misma persona da el mismo resultado.
- Las 155 columnas de la tabla depurada son idénticas, celda a celda, en la tabla etiquetada.

## Verificación de las ejecuciones del 8 de octubre de 2026

Los scripts 08, 09 y 11 se ejecutaron el 8 de octubre de 2026 con las decisiones D30 a D34. Dejaron
`data/processed/grd_depurado.parquet` (5.800.973 egresos, 157 columnas) y
`data/processed/grd_etiquetado.parquet` (163 columnas), que reemplazan a los del 6 de octubre. Cada
script se probó antes con la salida en una carpeta temporal: los archivos definitivos son idénticos,
byte a byte, a los de la prueba. Al agregar la columna `IDENTIDAD_AMBIGUA` (D34), las demás columnas y
las cuatro variables objetivo no cambiaron.

Los contrastes independientes están ahora en `2.2_depuracion_etiquetado/pruebas/` y se ejecutan con
un solo comando (D36). Sobre la versión 1 del conjunto analítico se cumplen las 70 comprobaciones
(`reportes/pruebas_independientes.md`):

- Depuración (43 comprobaciones): columnas originales idénticas a las de la tabla integrada, duplicados, personas, identidad ambigua, los catorce criterios recalculados con otra biblioteca, episodios recalculados egreso por egreso y la tabla «paso a paso» del reporte 08.
- Etiquetado (19): las cuatro variables recalculadas caso por caso en los 4.192.410 casos de estudio y, como unión literal de cada alta con los ingresos posteriores, en una muestra del 4 % de los identificadores (167.627 casos de estudio); además, la tabla de las variables y la de verificación de la censura del reporte 09.
- Análisis de sensibilidad (8): los casos de estudio y las tasas de los siete escenarios, recalculados desde las columnas del archivo sin usar las funciones de los scripts.

## Verificación de las ejecuciones del 20 de octubre de 2026

Los scripts 09, 11 y 12 se ejecutaron el 20 de octubre de 2026 con D38 y las dos filas nuevas de
sensibilidad (H27 y D39); el script 08 y la tabla depurada no cambiaron. Antes de escribir, el script 09
se probó en memoria y se comparó celda por celda con la versión 1: solo cambiaron `REING_7D_CDM` y
`REING_30D_CDM` de los partos (615.167 y 603.423 celdas, todas de 0 a sin dato); las demás columnas
quedaron idénticas. El script 12 registró la versión 2 del conjunto analítico (D36).

En la primera ejecución del script 11, una verificación nueva falló en la pasada que cuenta todo ingreso
(solo se usa para describir las sesiones de tratamiento): al contar todo ingreso, un parto también es
reingreso y la exclusión de D38 no corresponde. Se corrigió para que D38 se aplique solo cuando cuentan
únicamente los ingresos no planificados; la tabla de datos quedó idéntica byte a byte y el script 11 se
volvió a ejecutar sin fallas.

Sobre la versión 2 se cumplen las 74 comprobaciones de los contrastes independientes
(`reportes/pruebas_independientes.md`): depuración (43), etiquetado (20; ahora incluye que los partos
tengan dato solo donde corresponde y que su 0 haya sido obligatorio) y análisis de sensibilidad (11; los
diez escenarios, incluidos los partos con valor 0, los traslados con marca y los derivados).

---

## Pendientes

- [x] Validar con profesor guía las decisiones D18 a D26 y las de `docs/bitacora.md` que se aplican aquí (D03, D07, D08, D15 y H09). Las revisó el 7 de octubre de 2026; sus correcciones están en D30 a D36.
- [x] Presentar al profesor guía las entradas del 8 de octubre: el margen de la censura (D30), la marca de identidad ambigua (D34), la tabla final de criterios (D35) y el análisis de sensibilidad (H25). Las revisó el 13 de octubre de 2026: aprobó D30 y D34, y D35 a condición de incorporar los puntos 2.1 y 2.4 de su revisión.
- [x] Incorporar los puntos 2.1 (partos) y 2.4 (traslados y derivados) de la revisión del 13 de octubre. Hecho el 20 de octubre de 2026: H26, H27, D38 y D39.
- [x] Punto 2.3 de la revisión, en lo que toca a esta actividad: revisar por año los identificadores faltantes o ambiguos antes de tratar el aumento de 2023 y 2024 como un cambio real (H24). Hecho el 20 de octubre de 2026: H28 y reporte 09, sección 2.
- [ ] Presentar al profesor guía, en el próximo avance, H26, H27, H28, D38 y D39.
- [x] Ejecutar el script 08 sobre la carpeta de datos y confirmar las cifras de esta bitácora con su reporte. Hecho el 6 de octubre de 2026 y repetido el 8 de octubre.
- [x] Script 09: etiquetado del reingreso (D20, D25 y D26) y tasas por año y por definición. Hecho el 6 de octubre de 2026 y repetido el 8 de octubre.
- [x] Decidir con profesor guía si la cirugía mayor ambulatoria es caso de estudio (D23). Resuelto el 8 de octubre de 2026: no lo es (D32).
- [x] Decidir con profesor guía si las sesiones de tratamiento son caso de estudio (H18). Resuelto el 8 de octubre de 2026: no lo son (D33).
- [x] Confirmar con profesor guía la agrupación de las CDM 13 y 14 en el reingreso relacionado (D25). Resuelto el 8 de octubre de 2026: no se agrupan (D31).
- [ ] Respaldar con bibliografía la regla de traslado del mismo día o el día siguiente (D19). La validación con los datos está en H22.
- [ ] Declarar en el informe las limitaciones: los reingresos que no se ven junto al cierre del bloque (H20), que las variables relacionadas no incluyen los partos (D38), la identidad ambigua (H21), el cambio de cobertura en las derivaciones (H23) y el aumento de la tasa en 2023 y 2024 (H24).
