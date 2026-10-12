# Depuración de la tabla integrada (actividad 2.2, script 08)

Generado por `2.2_depuracion_etiquetado/scripts/08_depurar.py`. Entrada: `data/processed/grd_2019_2024.parquet`. Salida: `data/processed/grd_depurado.parquet`. Criterios: `2.2_depuracion_etiquetado/reglas/criterios_exclusion.csv`; umbrales: `2.2_depuracion_etiquetado/reglas/parametros.csv`. Las decisiones están en `2.2_depuracion_etiquetado/bitacora.md`.

Cada egreso puede cumplir dos papeles: **caso de estudio** (el alta desde la que se cuentan los días hasta un posible reingreso) y **reingreso** de un alta anterior. Solo se eliminan los duplicados. Las exclusiones son marcas (columnas `EXC_*`): un egreso que no sirve como caso de estudio, por ejemplo un fallecido, puede seguir contando como el reingreso de un alta anterior.

## 1. Resultado

|  | Egresos |
|---|---|
| Tabla integrada | 5.808.536 |
| Copias exactas eliminadas | 3.818 |
| Registros repetidos eliminados | 3.745 |
| **Tabla depurada** | **5.800.973** |
| Casos de estudio (`ES_CASO_ESTUDIO`) | 4.192.410 (72,3 %) |
| Pueden contar como reingreso (`PUEDE_SER_REINGRESO`) | 5.565.982 (95,9 %) |

La tabla depurada tiene 157 columnas: las de la tabla integrada, menos `DUP_EXACTO` y `DUP_CLAVE`, más las columnas nuevas de la sección 9.

## 2. Duplicados eliminados

Se eliminan las copias exactas. Cuando varios registros comparten paciente, hospital, fecha de ingreso, fecha de alta, sexo y fecha de nacimiento, se conserva el más completo: el que tiene más diagnósticos; si empatan, más procedimientos; luego mayor peso GRD; luego el primero del archivo (bitácora D15).

|  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Tabla integrada | 1.151.475 | 781.912 | 816.909 | 932.840 | 1.039.587 | 1.085.813 | **5.808.536** |
| Copias exactas | 159 | 2.818 | 279 | 63 | 169 | 330 | **3.818** |
| Registros repetidos | 780 | 459 | 345 | 573 | 748 | 840 | **3.745** |
| Tabla depurada | 1.150.536 | 778.635 | 816.285 | 932.204 | 1.038.670 | 1.084.643 | **5.800.973** |

No se fusionan 634 registros, en 312 grupos, que comparten paciente, hospital y fechas pero difieren en el sexo o en la fecha de nacimiento. Según la regla de la sección 3, en 146 grupos son personas distintas y en 124 el identificador no tiene persona asignada (genérico). En los otros 42 la regla los considera una misma persona: no se borran, pero quedan unidos en un mismo episodio asistencial (sección 4), de modo que solo uno es caso de estudio y ninguno cuenta como reingreso del otro.

## 3. Personas

Un mismo identificador puede corresponder a más de una persona. Dos egresos con el mismo identificador se consideran de personas distintas cuando sus fechas de nacimiento difieren en más de 366 días, salvo que coincidan en el día y el mes (error de digitación en el año). El sexo no se usa. `ID_PERSONA` es el identificador seguido de dos dígitos con el número de persona (01 la de más edad, 02 la siguiente).

|  | Cantidad |
|---|---|
| Identificadores de paciente | 4.035.780 |
| Con más de una combinación de sexo y fecha de nacimiento | 30.778 (0,76 %) |
| Egresos de esos identificadores | 97.378 |
| Identificadores genéricos (5 combinaciones o más) | 12 |
| Egresos con identificador genérico | 2.481 |
| Combinaciones del identificador genérico más usado | 1.101 |
| Identificadores con una misma fecha de nacimiento registrada con más de un sexo (no se separan) | 7.124 |
| **Personas** | **4.039.699** |

Los identificadores genéricos quedan sin persona asignada (criterio E02). Hay 23.758 identificadores no genéricos con más de una fecha de nacimiento. Los 23.609 que tienen exactamente dos se resuelven así:

| Las dos fechas de nacimiento… | Identificadores | Resultado |
|---|---|---|
| difieren en hasta 366 días | 17.795 | Una persona (error de digitación) |
| difieren en más, pero coinciden en día y mes | 1.953 | Una persona (error en el año) |
| difieren en más | 3.861 | Dos personas |

Otros 149 identificadores tienen tres fechas o más. Identificadores según el número de personas que resultan: 1 persona: 4.031.853; 2 personas: 3.901; 3 personas: 12; 4 personas: 2. En 1.827 de los identificadores con dos personas, la menor tiene menos de un año en su primer ingreso y la otra le lleva más de 12 años: es el patrón de un recién nacido registrado con el identificador de su madre.

**Identidad ambigua.** La regla anterior es una definición operativa: cuando los registros de un identificador no coinciden, no hay evidencia suficiente para saber con certeza si son de una persona o de varias. Por eso la columna `IDENTIDAD_AMBIGUA` marca los egresos de todo identificador que aparece con más de un sexo o con más de una fecha de nacimiento (sin contar los datos faltantes), para poder repetir cualquier análisis sin ellos. La tabla muestra qué dato cambia dentro del identificador y cómo lo resolvió la regla:

| Qué cambia dentro del identificador | Resultado de la regla | Identificadores | Egresos | Casos de estudio |
|---|---|---|---|---|
| Solo el sexo | Una persona | 6.846 | 22.760 | 14.674 |
| Solo la fecha de nacimiento | Una persona | 19.454 | 59.134 | 39.318 |
| Solo la fecha de nacimiento | Varias personas | 2.800 | 8.135 | 5.918 |
| El sexo y la fecha de nacimiento | Una persona | 389 | 1.333 | 856 |
| El sexo y la fecha de nacimiento | Varias personas | 1.115 | 2.981 | 2.512 |
| El sexo y la fecha de nacimiento | Sin persona (identificador genérico) | 12 | 2.481 | 0 |
| **Total con identidad ambigua** |  | **30.616** | **96.824** | **63.278** |

Es el 0,76 % de los identificadores y el 1,51 % de los casos de estudio. **Cambian de persona** bajo la regla los 3.915 identificadores que se separan en varias personas (11.116 egresos; 8.430 casos de estudio): 4.964 de esos egresos (3.552 casos de estudio) quedan asignados a la segunda persona o a una posterior. En sentido contrario, 19.843 identificadores con más de una fecha de nacimiento se mantienen como una sola persona (60.467 egresos; 40.174 casos de estudio). Los más dudosos son los que tienen sexo y fecha de nacimiento distintos a la vez y aun así quedan como una persona (389 identificadores; 856 casos de estudio). El efecto de dejar fuera todos los casos con identidad ambigua está en `2.2_depuracion_etiquetado/reportes/11_sensibilidad.md`.

## 4. Episodios asistenciales

Un traslado no es un reingreso: es la continuación de la misma hospitalización. Los egresos de una persona se unen en un mismo episodio asistencial cuando el segundo ingresa antes del alta del primero, o ingresa en otro hospital el mismo día del alta o al día siguiente. Solo el alta final del episodio puede ser caso de estudio, y un egreso que continúa un episodio no cuenta como reingreso.

|  | Cantidad |
|---|---|
| Egresos que se pueden seguir (con persona y fechas, sin los criterios que afectan a ambos papeles) | 5.663.585 |
| Episodios asistenciales | 5.565.982 |
| Episodios con más de un egreso | 83.904 |
|   de 2 egresos | 72.366 |
|   de 3 egresos | 10.280 |
|   de 4 egresos | 812 |
|   de 5 egresos o más | 446 |
| Egresos que continúan un episodio | 97.603 |
|   porque ingresan antes del alta anterior (solapados) | 10.524 |
|   porque ingresan en otro hospital el mismo día del alta | 70.933 |
|   porque ingresan en otro hospital en los días siguientes | 16.126 |
|   porque repiten hospital y fechas del egreso anterior | 20 |

**Validación de la regla.** La regla es una definición operacional. Se valida comparándola con las dos marcas explícitas de traslado que trae la base: que el alta anterior sea por derivación, o que el ingreso declare que procede de otro hospital. La tabla muestra los ingresos en un hospital distinto del que dio el alta anterior, según los días transcurridos entre esa alta y el ingreso:

| Ingreso en otro hospital | Egresos | Con marca de traslado | % | Los une la regla |
|---|---|---|---|---|
| Antes del alta anterior (estadías solapadas) | 9.939 | 6.778 | 68,2 % | 9.939 |
| El mismo día del alta | 70.933 | 68.689 | 96,8 % | 70.933 |
| Al día siguiente | 16.126 | 14.615 | 90,6 % | 16.126 |
| 2 días después | 2.600 | 1.223 | 47,0 % | 0 |
| 3 días después | 2.073 | 750 | 36,2 % | 0 |
| 4 a 7 días después | 7.818 | 2.089 | 26,7 % | 0 |
| 8 a 30 días después | 27.826 | 6.198 | 22,3 % | 0 |

Dentro de los primeros 7 días, la regla une 96.998 ingresos en otro hospital, y el 92,9 % tiene marca de traslado; no une 12.491, y el 67,5 % no la tiene. Las marcas tampoco son exactas: como referencia, tiene marca el 6,1 % de los ingresos al mismo hospital dentro de 7 días, que no son traslados.

El tipo de alta no basta para reconocer un traslado. Egresos con alta por derivación a otro hospital y cuántos tienen la continuación visible en la base (el resto fue a establecimientos que no reportan GRD):

|  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Alta por derivación a otro hospital | 21.013 | 24.343 | 25.428 | 22.918 | 27.925 | 32.810 | **154.437** |
| Con continuación visible | 10.013 | 10.703 | 12.206 | 11.827 | 15.255 | 17.828 | **77.832** |
| % | 47,7 % | 44,0 % | 48,0 % | 51,6 % | 54,6 % | 54,3 % | 50,4 % |
| % en los 65 hospitales presentes todos los años | 47,7 % | 44,0 % | 48,0 % | 51,6 % | 54,2 % | 52,8 % | 49,9 % |
| Excluidos como caso de estudio por derivación (E07 y E08) | 14.302 | 17.122 | 18.201 | 14.507 | 16.545 | 18.896 | **99.573** |
| % de los egresos del año | 1,2 % | 2,2 % | 2,2 % | 1,6 % | 1,6 % | 1,7 % | 1,7 % |

Los derivados cuya continuación no se ve quedan fuera como caso de estudio (criterios E07 y E08): es una censura administrativa del seguimiento, no una característica clínica del paciente. La continuación solo se ve si el hospital de destino está en la base, así que la tabla sirve para revisar cambios de cobertura entre años. El detalle por hospital está en el anexo, y por hospital y año, en `2.2_depuracion_etiquetado/reportes/08_derivaciones_por_hospital.csv`.

Un ingreso en el mismo hospital el mismo día del alta no es un traslado: abre un episodio nuevo y puede contar como reingreso (9.425 egresos).

## 5. Criterios de exclusión, paso a paso

Los criterios se aplican en el orden de la tabla. **Cumplen el criterio**: egresos de la tabla depurada que lo cumplen, sin considerar los demás. **Quita en este paso**: los que lo cumplen entre los que quedaban. Los criterios de papel *Ambos* dejan al egreso fuera como caso de estudio y como reingreso; los de papel *Caso*, solo como caso de estudio.

| Paso | Criterio | Papel | Activo | Cumplen el criterio | Quita en este paso | Quedan |
|---|---|---|---|---|---|---|
|  | Tabla integrada |  |  |  |  | 5.808.536 |
|  | Copias exactas (se eliminan) |  |  | 3.818 | 3.818 | 5.804.718 |
|  | Registros repetidos (se eliminan) |  |  | 3.745 | 3.745 | 5.800.973 |
| E01 | Sin identificador de paciente | Ambos | Sí | 17.864 | 17.864 | 5.783.109 |
| E02 | Identificador genérico: lo usan muchas personas distintas | Ambos | Sí | 2.481 | 2.481 | 5.780.628 |
| E03 | Sin fecha de ingreso o de alta, o con el alta anterior al ingreso | Ambos | Sí | 83 | 81 | 5.780.547 |
| E04 | Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019 | Ambos | Sí | 117.586 | 116.962 | 5.663.585 |
| E05 | Tramo de un traslado: no es el alta final de su episodio asistencial | Caso | Sí | 97.603 | 97.603 | 5.565.982 |
| E06 | Alta por fallecimiento | Caso | Sí | 170.563 | 165.515 | 5.400.467 |
| E07 | Alta por derivación a otro hospital | Caso | Sí | 167.418 | 76.605 | 5.323.862 |
| E08 | Alta por derivación a una institución privada | Caso | Sí | 26.081 | 22.968 | 5.300.894 |
| E09 | Sin GRD válido: sin código GRD o con CDM 99 | Caso | Sí | 5.042 | 4.799 | 5.296.095 |
| E10 | Sin fecha de nacimiento válida (falta, es posterior al ingreso o la edad supera el máximo) o sin tipo de alta | Caso | Sí | 149 | 99 | 5.295.996 |
| E11 | Seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta | Caso | Sí | 188.737 | 176.057 | 5.119.939 |
| E12 | Alta voluntaria o fuga del paciente | Caso | No | 77.385 | — | 5.119.939 |
| E13 | Cirugía mayor ambulatoria | Caso | Sí | 885.384 | 845.604 | 4.274.335 |
| E14 | Sesión de tratamiento: diagnóstico principal Z51 | Caso | Sí | 100.229 | 81.925 | 4.192.410 |
|  | **Casos de estudio** |  |  |  |  | **4.192.410** |

Egresos que quita cada paso, por año del archivo:

| Paso | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Tabla integrada | 1.151.475 | 781.912 | 816.909 | 932.840 | 1.039.587 | 1.085.813 | **5.808.536** |
| Copias exactas | 159 | 2.818 | 279 | 63 | 169 | 330 | **3.818** |
| Registros repetidos | 780 | 459 | 345 | 573 | 748 | 840 | **3.745** |
| E01 | 8.307 | 1.892 | 2.044 | 2.949 | 1.635 | 1.037 | **17.864** |
| E02 | 247 | 769 | 330 | 651 | 370 | 114 | **2.481** |
| E03 | 18 | 10 | 0 | 1 | 0 | 52 | **81** |
| E04 | 116.962 | 0 | 0 | 0 | 0 | 0 | **116.962** |
| E05 | 13.906 | 13.816 | 15.414 | 14.629 | 18.414 | 21.424 | **97.603** |
| E06 | 24.838 | 29.767 | 31.897 | 27.291 | 25.088 | 26.634 | **165.515** |
| E07 | 11.000 | 13.640 | 13.222 | 11.091 | 12.670 | 14.982 | **76.605** |
| E08 | 3.302 | 3.482 | 4.979 | 3.416 | 3.875 | 3.914 | **22.968** |
| E09 | 469 | 153 | 333 | 709 | 1.684 | 1.451 | **4.799** |
| E10 | 49 | 25 | 7 | 7 | 9 | 2 | **99** |
| E11 | 0 | 73.672 | 0 | 0 | 0 | 102.385 | **176.057** |
| E13 | 145.180 | 68.864 | 100.854 | 152.597 | 190.083 | 188.026 | **845.604** |
| E14 | 19.115 | 12.630 | 11.166 | 11.553 | 13.570 | 13.891 | **81.925** |
| **Casos de estudio** | 807.143 | 559.915 | 636.039 | 707.310 | 771.272 | 710.731 | **4.192.410** |
| % de la tabla depurada | 70,2 % | 71,9 % | 77,9 % | 75,9 % | 74,3 % | 65,5 % | 72,3 % |

Criterios desactivados: no quitan ningún egreso. La columna indica cuántos casos de estudio quitaría cada uno si se activara (cambiando `NO` por `SI` en la tabla de criterios).

| Código | Criterio | Casos de estudio que quitaría | % |
|---|---|---|---|
| E12 | Alta voluntaria o fuga del paciente | 69.296 | 1,7 % |

E07 y E05 se complementan: los egresos derivados a otro hospital cuya continuación está en la base ya quedan fuera en E05, porque no son el alta final de su episodio; E07 quita los derivados cuya continuación no se ve. Detalle de E09: Sin código GRD: 90; CDM 99: 4.952. Detalle de E10 (un egreso puede cumplir más de una condición): sin fecha de nacimiento: 37; fecha de nacimiento posterior al ingreso: 1; edad al ingreso mayor de 110 años: 26; sin tipo de alta: 101.

**Censura (E11).** Los archivos están organizados por año de alta, así que un reingreso solo aparece en la base si termina antes del cierre del bloque. Por eso cada ventana exige, además de sus días, un margen de 30 días entre el alta y el cierre. E11 quita los egresos que no alcanzan el seguimiento de la ventana más corta (7 + 30 = 37 días). Casos de estudio con seguimiento suficiente para cada ventana: 7 días (alta al menos 37 días antes del cierre), 4.192.410; 30 días (alta al menos 60 días antes del cierre), 4.101.883. Un caso que no alcanza una ventana queda sin las variables de esa ventana (reporte 09).

Justificación de cada criterio:

| Código | Criterio | Justificación |
|---|---|---|
| E01 | Sin identificador de paciente | Sin identificador no se puede saber si la persona vuelve a ingresar ni reconocer sus reingresos. |
| E02 | Identificador genérico: lo usan muchas personas distintas | El identificador reúne a personas distintas: seguirlo produciría reingresos falsos. |
| E03 | Sin fecha de ingreso o de alta, o con el alta anterior al ingreso | Sin fechas coherentes no se pueden contar los días entre un alta y un nuevo ingreso. |
| E04 | Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019 | Solo se registraron en 2019: con ellos ese año no es comparable con los demás. |
| E05 | Tramo de un traslado: no es el alta final de su episodio asistencial | El paciente sigue hospitalizado en otro establecimiento: el alta que cuenta es la final del episodio. |
| E06 | Alta por fallecimiento | Quien fallece no puede reingresar; la propuesta de tesis los excluye. |
| E07 | Alta por derivación a otro hospital | La hospitalización continúa en un establecimiento que no está en la base. Es una censura administrativa del seguimiento, no una característica clínica del paciente. |
| E08 | Alta por derivación a una institución privada | La atención continúa fuera de la red pública, donde no se puede observar. También es una censura administrativa. |
| E09 | Sin GRD válido: sin código GRD o con CDM 99 | Sin GRD válido no hay CDM ni peso GRD, que son variables del estudio. |
| E10 | Sin fecha de nacimiento válida (falta, es posterior al ingreso o la edad supera el máximo) o sin tipo de alta | Sin fecha de nacimiento no hay edad, y sin tipo de alta no se sabe si el paciente egresó vivo. |
| E11 | Seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta | Un reingreso solo aparece en la base si termina antes del cierre del bloque; sin ese seguimiento no se puede saber si lo hubo. |
| E12 | Alta voluntaria o fuga del paciente | Se conservan: son egresos hospitalarios, y dejarlos fuera quitaría un grupo de mayor riesgo de reingreso. |
| E13 | Cirugía mayor ambulatoria | Es un proceso asistencial distinto de la hospitalización convencional, y el estudio trata del reingreso después de un egreso hospitalario (revisión del profesor guía, 7 de octubre de 2026). |
| E14 | Sesión de tratamiento: diagnóstico principal Z51 | Son atenciones planificadas o repetitivas, con una dinámica distinta de la del episodio agudo (revisión del profesor guía, 7 de octubre de 2026). |

## 6. Egresos que pueden contar como reingreso

Un egreso puede contar como el reingreso de un alta anterior si se puede seguir (tiene persona y fechas, y no cumple ningún criterio activo de papel *Ambos*) y además abre un episodio asistencial, es decir, no es la continuación de un traslado.

|  | Egresos |
|---|---|
| Tabla depurada | 5.800.973 |
| No se pueden seguir | 137.388 |
| Continúan un episodio (traslados) | 97.603 |
| **Pueden contar como reingreso** | **5.565.982** |

|  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Pueden contar como reingreso | 1.011.618 | 761.626 | 799.109 | 914.057 | 1.018.256 | 1.061.316 | **5.565.982** |

## 7. Composición de los casos de estudio

| Tipo de alta | Casos de estudio | % |
|---|---|---|
| DOMICILIO | 3.973.075 | 94,77 % |
| HOSPITALIZACIÓN DOMICILIARIA | 129.823 | 3,10 % |
| ALTA VOLUNTARIA | 52.562 | 1,25 % |
| DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE | 20.216 | 0,48 % |
| FUGA DEL PACIENTE | 16.734 | 0,40 % |

| Tipo de actividad | Casos de estudio | % |
|---|---|---|
| HOSPITALIZACIÓN | 4.192.410 | 100,00 % |

| Tipo de ingreso | Casos de estudio | % |
|---|---|---|
| URGENCIA | 2.462.241 | 58,73 % |
| OBSTETRICA | 879.251 | 20,97 % |
| PROGRAMADA | 850.539 | 20,29 % |
| (sin dato) | 379 | 0,01 % |

## 8. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `persona_dias_fnac` | `366` | Dos egresos con el mismo identificador son de personas distintas cuando sus fechas de nacimiento difieren en más de este número de días (D18) |
| `persona_mismo_dia_mes` | `SI` | SI = si las fechas de nacimiento coinciden en día y mes son de la misma persona aunque difieran en más de un año: error de digitación en el año (D18) |
| `id_generico_min_personas` | `5` | Un identificador con este número de combinaciones distintas de sexo y fecha de nacimiento, o más, se considera genérico (D18) |
| `traslado_dias_max` | `1` | Un ingreso en otro hospital hasta este número de días después del alta continúa el mismo episodio asistencial: 0 = solo el mismo día; 1 = el mismo día o el siguiente (D19) |
| `traslado_exige_marca` | `NO` | SI = además debe constar el traslado en el tipo de alta (derivación) o en la procedencia del ingreso (otros hospitales) (D19) |
| `edad_maxima` | `110` | Edad al ingreso, en años, sobre la cual la fecha de nacimiento se considera no válida (D21) |
| `ventanas_dias` | `7 / 30` | Ventanas de reingreso, en días, separadas por una barra vertical (D20) |
| `censura_margen_dias` | `30` | Días que se suman a cada ventana para la censura. Un caso de estudio tiene las variables de una ventana solo si su alta ocurre al menos ventana + margen días antes del cierre del bloque, porque un reingreso solo aparece en la base si termina antes del cierre. 0 = solo la ventana (H20, D30) |
| `diagnosticos_sesion` | `Z51` | Comienzo del diagnóstico principal de las sesiones de tratamiento, separados por una barra vertical si son varios. Esos egresos no son caso de estudio (criterio E14) ni cuentan como reingreso no planificado (D33) |

Cierre de cada bloque de identificador: A, 31-12-2020; B, 31-12-2024.

## 9. Columnas nuevas

| Columna | Contenido |
|---|---|
| `ID_PERSONA` | Identificador de la persona: `ID_PACIENTE` × 100 + número de persona. Sin dato en los egresos sin identificador o con identificador genérico. |
| `IDENTIDAD_AMBIGUA` | Verdadero si el identificador del egreso aparece con más de un sexo o con más de una fecha de nacimiento (sección 3). Falso en los egresos sin identificador. |
| `ID_EPISODIO` | Episodio asistencial: `ID_EGRESO` del primer egreso del episodio. Sin dato en los egresos que no se pueden seguir. |
| `N_EGRESOS_EPISODIO` | Número de egresos del episodio asistencial. |
| `CONTINUA_EPISODIO` | Verdadero si el egreso continúa un episodio abierto por un egreso anterior (traslado). |
| `ALTA_FINAL_EPISODIO` | Verdadero si el egreso es el alta final de su episodio asistencial. |
| `EXC_SIN_ID` | E01. Sin identificador de paciente. |
| `EXC_ID_GENERICO` | E02. Identificador genérico: lo usan muchas personas distintas. |
| `EXC_FECHAS` | E03. Sin fecha de ingreso o de alta, o con el alta anterior al ingreso. |
| `EXC_ACTIVIDAD_2019` | E04. Hospitalización diurna o en urgencia: tipos de actividad que solo existen en 2019. |
| `EXC_TRAMO_EPISODIO` | E05. Tramo de un traslado: no es el alta final de su episodio asistencial. |
| `EXC_FALLECIDO` | E06. Alta por fallecimiento. |
| `EXC_DERIVADO_HOSPITAL` | E07. Alta por derivación a otro hospital. |
| `EXC_DERIVADO_PRIVADO` | E08. Alta por derivación a una institución privada. |
| `EXC_SIN_GRD` | E09. Sin GRD válido: sin código GRD o con CDM 99. |
| `EXC_DATOS_FALTANTES` | E10. Sin fecha de nacimiento válida (falta, es posterior al ingreso o la edad supera el máximo) o sin tipo de alta. |
| `EXC_CENSURA` | E11. Seguimiento incompleto: el alta está demasiado cerca del cierre del bloque incluso para la ventana más corta. |
| `EXC_ALTA_VOLUNTARIA_FUGA` | E12. Alta voluntaria o fuga del paciente. |
| `EXC_CMA` | E13. Cirugía mayor ambulatoria. |
| `EXC_SESION` | E14. Sesión de tratamiento: diagnóstico principal Z51. |
| `MOTIVO_EXCLUSION` | Código del primer criterio activo que excluye al egreso como caso de estudio. Sin dato en los casos de estudio. |
| `ES_CASO_ESTUDIO` | Verdadero si el egreso no cumple ningún criterio activo. |
| `PUEDE_SER_REINGRESO` | Verdadero si el egreso puede contar como reingreso de un alta anterior (sección 6). |

Las columnas `EXC_*` se calculan siempre, también para los criterios desactivados.

## 10. Verificaciones

- Registros de salida = registros de entrada − duplicados eliminados: **sí**.
- `ID_EGRESO` único en la tabla depurada: **sí**.
- Ningún identificador de paciente aparece en los dos bloques: **sí**.
- La suma de los pasos coincide: egresos depurados − excluidos = casos de estudio: **sí**.
- Todo egreso que no es caso de estudio tiene un motivo, y ningún caso de estudio lo tiene: **sí**.
- Cada episodio asistencial tiene exactamente un alta final: **sí**.
- Cada episodio asistencial pertenece a una sola persona: **sí**.
- Los episodios de una persona no se solapan entre sí: **sí**.
- Todo caso de estudio tiene persona, episodio y es el alta final de su episodio: **sí**.
- Todo egreso de un identificador genérico o separado en varias personas tiene `IDENTIDAD_AMBIGUA`: **sí**.
- El archivo escrito tiene las filas esperadas: **sí**.
- Las columnas originales conservan su nombre, orden y tipo de dato: **sí**.
- Contenido idéntico al de la tabla integrada en 7 columnas de control: **sí**.
- Las columnas nuevas releídas del archivo son iguales a las calculadas: **sí**.

## Anexo. Altas por derivación, por hospital

Egresos de la tabla depurada. **Con continuación visible**: derivados a otro hospital cuyo ingreso siguiente está en la base (sección 4). **Excluidos**: los que quedan fuera como caso de estudio por los criterios E07 (derivación a otro hospital sin continuación visible) y E08 (derivación a una institución privada). Los nombres son los de la tabla maestra del DEIS.

| Hospital | Años | Egresos | Derivados a otro hospital | Con continuación visible | % | Excluidos por E07 | Excluidos por E08 | % de los egresos |
|---|---|---|---|---|---|---|---|---|
| 101100 Hospital Dr. Juan Noé Crevanni (Arica) | Todos | 108.650 | 675 | 517 | 76,6 % | 158 | 257 | 0,38 % |
| 102100 Hospital Dr. Ernesto Torres Galdames (Iquique) | Todos | 117.714 | 2.490 | 1.114 | 44,7 % | 1.376 | 627 | 1,70 % |
| 103100 Hospital Dr. Leonardo Guzmán (Antofagasta) | Todos | 127.027 | 864 | 441 | 51,0 % | 423 | 296 | 0,57 % |
| 103101 Hospital Dr. Carlos Cisternas (Calama) | Todos | 60.442 | 1.517 | 1.294 | 85,3 % | 223 | 255 | 0,79 % |
| 104100 Hospital San José del Carmen (Copiapó) | Todos | 76.741 | 1.280 | 851 | 66,5 % | 429 | 281 | 0,93 % |
| 104103 Hospital Provincial del Huasco Monseñor Fernando Ariztía Ruiz (Vallenar) | Todos | 33.542 | 807 | 615 | 76,2 % | 192 | 132 | 0,97 % |
| 105100 Hospital San Juan de Dios (La Serena) | Todos | 101.685 | 2.181 | 1.637 | 75,1 % | 544 | 192 | 0,72 % |
| 105101 Hospital San Pablo (Coquimbo) | Todos | 100.968 | 1.447 | 998 | 69,0 % | 449 | 199 | 0,64 % |
| 105102 Hospital Dr. Antonio Tirado Lanas (Ovalle) | Todos | 64.559 | 1.405 | 1.030 | 73,3 % | 375 | 111 | 0,75 % |
| 106100 Hospital Carlos Van Buren (Valparaíso) | Todos | 129.704 | 5.377 | 4.454 | 82,8 % | 923 | 798 | 1,33 % |
| 106102 Hospital Dr. Eduardo Pereira Ramírez (Valparaíso) | Todos | 27.395 | 586 | 281 | 48,0 % | 305 | 15 | 1,17 % |
| 106103 Hospital Claudio Vicuña (San Antonio) | Todos | 48.970 | 1.526 | 1.194 | 78,2 % | 332 | 550 | 1,80 % |
| 107100 Hospital Dr. Gustavo Fricke (Viña del Mar) | Todos | 138.733 | 4.286 | 2.342 | 54,6 % | 1.944 | 568 | 1,81 % |
| 107101 Hospital San Martín (Quillota) | Todos | 67.769 | 3.161 | 1.422 | 45,0 % | 1.739 | 403 | 3,16 % |
| 107102 Hospital de Quilpué | Todos | 51.851 | 1.858 | 1.026 | 55,2 % | 832 | 140 | 1,87 % |
| 108100 Hospital de San Camilo (San Felipe) | Todos | 68.358 | 1.665 | 847 | 50,9 % | 818 | 184 | 1,47 % |
| 108101 Hospital San Juan de Dios (Los Andes) | Todos | 48.838 | 1.376 | 868 | 63,1 % | 508 | 202 | 1,45 % |
| 109100 Complejo Hospitalario San José (Santiago, Independencia) | Todos | 169.685 | 1.370 | 617 | 45,0 % | 753 | 867 | 0,95 % |
| 109101 Hospital Clínico de Niños Dr. Roberto del Río (Santiago, Independencia) | Todos | 47.859 | 832 | 683 | 82,1 % | 149 | 58 | 0,43 % |
| 110100 Hospital San Juan de Dios (Santiago, Santiago) | Todos | 152.271 | 1.224 | 727 | 59,4 % | 497 | 263 | 0,50 % |
| 110110 Instituto Traumatológico Dr. Teodoro Gebauer | 2023 a 2024 | 9.104 | 93 | 73 | 78,5 % | 20 | 2 | 0,24 % |
| 110120 Hospital Dr. Félix Bulnes Cerda (Santiago, Quinta Normal) | Todos | 130.456 | 1.239 | 850 | 68,6 % | 389 | 346 | 0,56 % |
| 110130 Hospital Adalberto Steeger (Talagante) | Todos | 34.862 | 1.139 | 777 | 68,2 % | 362 | 149 | 1,47 % |
| 110150 Hospital San José (Melipilla) | Todos | 48.322 | 1.297 | 1.090 | 84,0 % | 207 | 124 | 0,68 % |
| 111100 Hospital Clínico San Borja-Arriarán (Santiago, Santiago) | Todos | 113.238 | 774 | 468 | 60,5 % | 306 | 277 | 0,51 % |
| 111101 Hospital Clínico Metropolitano El Carmen Doctor Luis Valentín Ferrada | Todos | 118.845 | 2.434 | 1.236 | 50,8 % | 1.198 | 376 | 1,32 % |
| 111195 Hospital de Urgencia Asistencia Pública Dr. Alejandro del Río | Todos | 64.038 | 2.820 | 1.875 | 66,5 % | 945 | 408 | 2,11 % |
| 112100 Hospital Del Salvador (Santiago, Providencia) | Todos | 108.343 | 4.755 | 1.212 | 25,5 % | 3.543 | 289 | 3,54 % |
| 112101 Hospital Dr. Luis Tisné B. (Santiago, Peñalolén) | Todos | 99.189 | 3.948 | 1.575 | 39,9 % | 2.373 | 279 | 2,67 % |
| 112102 Hospital de Niños Dr. Luis Calvo Mackenna (Santiago, Providencia) | Todos | 51.903 | 1.444 | 1.165 | 80,7 % | 279 | 80 | 0,69 % |
| 112103 Instituto Nacional de Enfermedades Respiratorias y Cirugía Torácica | Todos | 24.224 | 619 | 413 | 66,7 % | 206 | 16 | 0,92 % |
| 112104 Instituto de Neurocirugía Dr. Alfonso Asenjo | Todos | 19.951 | 714 | 500 | 70,0 % | 214 | 9 | 1,12 % |
| 113100 Hospital Barros Luco Trudeau (Santiago, San Miguel) | Todos | 171.323 | 3.404 | 541 | 15,9 % | 2.863 | 588 | 2,01 % |
| 113130 Hospital Dr. Exequiel González Cortés (Santiago, San Miguel) | Todos | 51.354 | 487 | 406 | 83,4 % | 81 | 53 | 0,26 % |
| 113150 Hospital San Luis (Buin) | Todos | 32.203 | 924 | 766 | 82,9 % | 158 | 292 | 1,40 % |
| 113180 Hospital El Pino (Santiago, San Bernardo) | Todos | 90.556 | 4.298 | 1.464 | 34,1 % | 2.834 | 2.852 | 6,28 % |
| 114101 Complejo Hospitalario Dr. Sótero del Río (Santiago, Puente Alto) | Todos | 280.168 | 7.970 | 3.135 | 39,3 % | 4.835 | 2.842 | 2,74 % |
| 114103 Hospital Padre Alberto Hurtado (San Ramón) | Todos | 110.090 | 1.179 | 841 | 71,3 % | 338 | 335 | 0,61 % |
| 114105 Hospital Clínico Metropolitano La Florida Dra. Eloisa Díaz Inzunza | Todos | 114.033 | 883 | 599 | 67,8 % | 284 | 303 | 0,51 % |
| 115100 Hospital Regional de Rancagua | Todos | 155.017 | 5.011 | 1.403 | 28,0 % | 3.608 | 494 | 2,65 % |
| 115107 Hospital San Juan de Dios (San Fernando) | Todos | 52.902 | 1.373 | 662 | 48,2 % | 711 | 99 | 1,53 % |
| 115110 Hospital de Santa Cruz | Todos | 40.793 | 1.323 | 833 | 63,0 % | 490 | 145 | 1,56 % |
| 116100 Hospital San Juan de Dios (Curicó) | Todos | 102.398 | 1.766 | 974 | 55,2 % | 792 | 277 | 1,04 % |
| 116105 Hospital Dr. César Garavagno Burotto (Talca) | Todos | 179.074 | 2.858 | 1.636 | 57,2 % | 1.222 | 349 | 0,88 % |
| 116107 Hospital de Constitución | 2024 | 3.204 | 262 | 190 | 72,5 % | 72 | 10 | 2,56 % |
| 116108 Hospital Presidente Carlos Ibáñez del Campo (Linares) | Todos | 81.745 | 2.680 | 1.960 | 73,1 % | 720 | 201 | 1,13 % |
| 116110 Hospital San José (Parral) | Todos | 27.399 | 2.106 | 1.885 | 89,5 % | 221 | 35 | 0,93 % |
| 116111 Hospital San Juan de Dios (Cauquenes) | 2024 | 4.681 | 465 | 333 | 71,6 % | 132 | 4 | 2,91 % |
| 117101 Hospital Clínico Herminda Martín (Chillán) | Todos | 136.666 | 4.374 | 1.481 | 33,9 % | 2.893 | 1.346 | 3,10 % |
| 117102 Hospital de San Carlos | Todos | 47.502 | 1.340 | 615 | 45,9 % | 725 | 32 | 1,59 % |
| 118100 Hospital Clínico Regional Dr. Guillermo Grant Benavente (Concepción) | Todos | 193.943 | 5.264 | 2.442 | 46,4 % | 2.822 | 495 | 1,71 % |
| 118105 Hospital San José (Coronel) | Todos | 39.525 | 2.569 | 1.815 | 70,7 % | 754 | 46 | 2,02 % |
| 118106 Hospital de Lota | 2023 a 2024 | 11.691 | 658 | 547 | 83,1 % | 111 | 2 | 0,97 % |
| 119100 Hospital Las Higueras (Talcahuano) | Todos | 131.006 | 2.994 | 1.066 | 35,6 % | 1.928 | 201 | 1,63 % |
| 119101 Hospital de Tomé | 2023 a 2024 | 8.473 | 434 | 358 | 82,5 % | 76 | 4 | 0,94 % |
| 119102 Hospital Penco - Lirquén | 2024 | 4.157 | 184 | 171 | 92,9 % | 13 | 11 | 0,58 % |
| 120101 Complejo Asistencial Dr. Víctor Ríos Ruiz (Los Ángeles) | Todos | 168.916 | 4.133 | 930 | 22,5 % | 3.203 | 525 | 2,21 % |
| 121109 Hospital Dr. Hernán Henríquez Aravena (Temuco) | Todos | 167.089 | 7.085 | 4.041 | 57,0 % | 3.044 | 592 | 2,18 % |
| 121110 Hospital Dr. Abraham Godoy (Lautaro) | Todos | 27.736 | 1.821 | 1.033 | 56,7 % | 788 | 14 | 2,89 % |
| 121114 Hospital Intercultural de Nueva Imperial | Todos | 33.546 | 2.259 | 1.481 | 65,6 % | 778 | 40 | 2,44 % |
| 121117 Hospital de Pitrufquén | Todos | 24.518 | 2.226 | 1.074 | 48,2 % | 1.152 | 29 | 4,82 % |
| 121121 Hospital de Villarrica | Todos | 30.463 | 2.160 | 1.273 | 58,9 % | 887 | 25 | 2,99 % |
| 122100 Hospital Clínico Regional (Valdivia) | Todos | 125.849 | 3.029 | 763 | 25,2 % | 2.266 | 143 | 1,91 % |
| 123100 Hospital Base San José de Osorno | Todos | 108.423 | 1.789 | 652 | 36,4 % | 1.137 | 250 | 1,28 % |
| 124105 Hospital de Puerto Montt | Todos | 160.087 | 3.394 | 1.035 | 30,5 % | 2.359 | 437 | 1,75 % |
| 125100 Hospital Regional (Coihaique) | Todos | 52.578 | 1.847 | 799 | 43,3 % | 1.048 | 325 | 2,61 % |
| 126100 Hospital Clínico de Magallanes Dr. Lautaro Navarro Avaria | Todos | 70.755 | 741 | 284 | 38,3 % | 457 | 286 | 1,05 % |
| 128109 Hospital Provincial Dr. Rafael Avaría (Curanilahue) | Todos | 37.593 | 5.384 | 1.110 | 20,6 % | 4.274 | 123 | 11,70 % |
| 129100 Hospital Dr. Mauricio Heyermann (Angol) | Todos | 54.959 | 1.434 | 923 | 64,4 % | 511 | 118 | 1,14 % |
| 129106 Hospital San José (Victoria) | Todos | 44.250 | 2.260 | 1.050 | 46,5 % | 1.210 | 90 | 2,94 % |
| 133150 Hospital de Castro | Todos | 48.718 | 2.484 | 779 | 31,4 % | 1.705 | 196 | 3,90 % |
| 200717 (sin nombre en la tabla maestra) | 2024 | 10.354 | 382 | 290 | 75,9 % | 92 | 6 | 0,95 % |
