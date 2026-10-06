# Bitácora de la actividad 2.2: depuración y etiquetado del reingreso

Registro de los hallazgos y decisiones de la actividad 2.2 de la Carta Gantt. Continúa la numeración
de `docs/bitacora.md`, que cubre las actividades 1.2 y 2.1: aquí el primer hallazgo es H13 y la primera
decisión, D18. Las entradas anteriores que se aplican en esta actividad (D03, D07, D08, D15, H09 y H10)
están en esa bitácora. Una entrada no se borra: si una decisión cambia, se agrega una nueva entrada
que la reemplaza y se indica en el campo **Estado**.

Las decisiones de esta bitácora se aplican como provisionales: se presentan al profesor guía el
9 de octubre de 2026. Por eso cada exclusión se puede activar o desactivar en
`reglas/criterios_exclusion.csv` y cada umbral se puede cambiar en `reglas/parametros.csv`, sin
modificar el código.

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

| Tema | Entrada | Definición |
|---|---|---|
| Misma persona | D18 | Mismo identificador y fechas de nacimiento que no difieran en más de un año (o que coincidan en día y mes). |
| Traslado | D19 | Ingreso en otro hospital el mismo día del alta o al día siguiente, o ingreso anterior al alta: continúa el mismo episodio asistencial. |
| Reingreso | D20, D26 | Ingreso no planificado (no programado y que no sea un parto) dentro de 7 o 30 días del alta final del episodio. Son las cuatro variables de la propuesta. |
| Reingreso relacionado | D25 | Algún ingreso de la ventana con la misma CDM que el caso de estudio; las CDM 13 y 14 cuentan como una sola. |
| Sin identificador o sin fechas | D21 | Fuera como caso de estudio y como reingreso. |
| Censura | D22 | Altas de los últimos 30 días de cada bloque, para las cuatro variables. |
| Exclusiones | D23 | Trece criterios en una tabla; once activos y dos desactivados. |
| Duplicados | D24 | Aplicación de D15: se conserva el registro más completo. |

---

### H13 · 2026-10-06 · Identificadores compartidos por más de una persona
- **Actividad:** 2.2
- **Hallazgo:** De 4.035.780 identificadores de paciente, 30.778 (0,76 %) tienen más de una combinación de sexo y fecha de nacimiento; reúnen 97.378 egresos. Corresponden a tres situaciones distintas.
- **Madre y recién nacido:** En 1.827 identificadores hay dos personas, de las cuales la menor tiene menos de un año en su primer ingreso y la otra le lleva más de 12 años. Ejemplo: los egresos `20230204284` (un parto) y `20230646756` (una recién nacida en neonatología) tienen el mismo identificador, el mismo hospital y las mismas fechas de ingreso y de alta.
- **Errores de digitación:** De los 23.609 identificadores con exactamente dos fechas de nacimiento, en 17.795 las fechas difieren en hasta 366 días (cambia el día o el mes) y en 1.953 difieren en más, pero coinciden en el día y el mes (cambia el año). Además, 7.124 identificadores tienen una misma fecha de nacimiento registrada con los dos sexos.
- **Identificadores genéricos:** 12 identificadores se usan para muchas personas (5 o más combinaciones de sexo y fecha de nacimiento; el más usado tiene 1.101). Suman 2.481 egresos.
- **Consecuencia:** Si el reingreso se calcula solo con el identificador, la hospitalización de un recién nacido cuenta como reingreso de su madre. Si se exige que el sexo y la fecha de nacimiento sean idénticos, se pierden los reingresos reales de las personas con un error de digitación.
- **Evidencia:** `2.2_depuracion_etiquetado/scripts/08_depurar.py` → `2.2_depuracion_etiquetado/reportes/08_depuracion.md`, sección 3.

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

### D22 · 2026-10-06 · Censura común de 30 días
- **Actividad:** 2.2
- **Decisión:** No son caso de estudio los egresos con alta en los últimos 30 días de su bloque: después del 1 de diciembre de 2020 en el bloque A y después del 1 de diciembre de 2024 en el bloque B (criterio E11). El mismo corte se usa para las variables de 7 y de 30 días, de modo que las cuatro se calculan sobre los mismos casos de estudio.
- **Resultado:** 151.633 egresos cumplen el criterio; aplicado después de los demás, quita 141.391 (59.038 de 2020 y 82.353 de 2024).
- **Alternativa:** Ampliar el margen a 60 días (`censura_dias`) reduce la pérdida descrita en H16 a menos del 1 %, pero quita otros dos meses de casos.
- **Completa a:** D03 de `docs/bitacora.md`.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

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
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

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

### D25 · 2026-10-06 · Las CDM 13 y 14 cuentan como una sola al medir el reingreso relacionado
- **Actividad:** 2.2
- **Decisión:** Para decidir si un reingreso está relacionado con el caso de estudio, las CDM 13 y 14 se tratan como una sola. La columna `CDM` no se modifica: la agrupación solo se usa en esa comparación (parámetro `cdm_agrupadas` = `13+14`).
- **Efecto:** `REING_7D_CDM` pasa de 46.975 a 50.896 casos y `REING_30D_CDM`, de 131.795 a 138.380. Las variables por cualquier causa no cambian. En los partos, el reingreso relacionado a 30 días pasa de 0 a 6.585 casos.
- **Fundamento:** H17. La propuesta mide la relación por coincidencia de CDM y reconoce que es una aproximación gruesa; esta agrupación corrige el único caso en que la aproximación da cero por construcción.
- **Alternativa:** Dejar `cdm_agrupadas` vacío para comparar la CDM tal cual, como dice literalmente la propuesta.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

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
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### H18 · 2026-10-06 · Sesiones de tratamiento entre los casos de estudio
- **Actividad:** 2.2
- **Hallazgo:** 83.798 casos de estudio (1,6 %) tienen como diagnóstico principal Z51, que corresponde a sesiones de quimioterapia y tratamientos similares. El 58,6 % va seguido de otro ingreso dentro de 30 días, casi siempre programado, y el 8,7 % de un reingreso no planificado. Además, 852 personas tienen 20 o más casos de estudio; la que más tiene, 1.047.
- **Consecuencia:** En las variables objetivo pesan poco, porque los ingresos programados no cuentan como reingreso (D26). Queda por decidir con profesor guía si estas atenciones deben ser caso de estudio; si se excluyen, se agrega un criterio a la tabla de exclusiones.
- **Advertencia para la ingeniería de variables:** Las personas con un solo caso de estudio casi nunca tienen reingreso (0,5 %, frente a 9,6 % con 2 a 5 casos), porque un reingreso es otro egreso de la misma persona. Toda variable que cuente egresos de una persona debe limitarse a los anteriores al alta del caso.
- **Evidencia:** exploración del 6 de octubre de 2026 sobre la tabla etiquetada.

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

---

## Pendientes

- [ ] Validar con profesor guía, el 9 de octubre de 2026, las decisiones D18 a D26 y las de `docs/bitacora.md` que se aplican aquí (D03, D07, D08, D15 y H09).
- [x] Ejecutar el script 08 sobre la carpeta de datos y confirmar las cifras de esta bitácora con su reporte. Hecho el 6 de octubre de 2026.
- [x] Script 09: etiquetado del reingreso (D20, D25 y D26) y tasas por año y por definición. Hecho el 6 de octubre de 2026.
- [ ] Decidir con profesor guía si la cirugía mayor ambulatoria es caso de estudio (D23).
- [ ] Decidir con profesor guía si las sesiones de tratamiento son caso de estudio (H18).
- [ ] Confirmar con profesor guía la agrupación de las CDM 13 y 14 en el reingreso relacionado (D25).
- [ ] Respaldar con bibliografía la regla de traslado del mismo día o el día siguiente (D19).
