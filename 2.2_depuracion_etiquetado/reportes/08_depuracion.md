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
| Casos de estudio (`ES_CASO_ESTUDIO`) | 5.154.605 (88,9 %) |
| Pueden contar como reingreso (`PUEDE_SER_REINGRESO`) | 5.565.982 (95,9 %) |

La tabla depurada tiene 155 columnas: las de la tabla integrada, menos `DUP_EXACTO` y `DUP_CLAVE`, más las columnas nuevas de la sección 9.

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

Respaldo de la regla: proporción de los ingresos en otro hospital que además tienen una marca explícita de traslado (el alta anterior es una derivación o el ingreso declara que procede de otro hospital).

| Ingreso en otro hospital | Egresos | Con marca de traslado | % |
|---|---|---|---|
| El mismo día del alta | 70.933 | 68.689 | 96,8 % |
| En los días siguientes | 16.126 | 14.615 | 90,6 % |

El tipo de alta no basta para reconocer un traslado. Egresos con alta por derivación a otro hospital y cuántos tienen la continuación visible en la base (el resto fue a establecimientos que no reportan GRD):

|  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Total |
|---|---|---|---|---|---|---|---|
| Alta por derivación a otro hospital | 21.013 | 24.343 | 25.428 | 22.918 | 27.925 | 32.810 | **154.437** |
| Con continuación visible | 10.013 | 10.703 | 12.206 | 11.827 | 15.255 | 17.828 | **77.832** |
| % | 47,7 % | 44,0 % | 48,0 % | 51,6 % | 54,6 % | 54,3 % | 50,4 % |

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
| E11 | Ventana de seguimiento incompleta: el alta está demasiado cerca del cierre del bloque | Caso | Sí | 151.633 | 141.391 | 5.154.605 |
| E12 | Alta voluntaria o fuga del paciente | Caso | No | 77.385 | — | 5.154.605 |
| E13 | Cirugía mayor ambulatoria | Caso | No | 885.384 | — | 5.154.605 |
|  | **Casos de estudio** |  |  |  |  | **5.154.605** |

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
| E11 | 0 | 59.038 | 0 | 0 | 0 | 82.353 | **141.391** |
| **Casos de estudio** | 971.438 | 656.043 | 748.059 | 871.460 | 974.925 | 932.680 | **5.154.605** |
| % de la tabla depurada | 84,4 % | 84,3 % | 91,6 % | 93,5 % | 93,9 % | 86,0 % | 88,9 % |

Criterios desactivados: no quitan ningún egreso. La columna indica cuántos casos de estudio quitaría cada uno si se activara (cambiando `NO` por `SI` en la tabla de criterios).

| Código | Criterio | Casos de estudio que quitaría | % |
|---|---|---|---|
| E12 | Alta voluntaria o fuga del paciente | 70.142 | 1,4 % |
| E13 | Cirugía mayor ambulatoria | 851.948 | 16,5 % |

E07 y E05 se complementan: los egresos derivados a otro hospital cuya continuación está en la base ya quedan fuera en E05, porque no son el alta final de su episodio; E07 quita los derivados cuya continuación no se ve. Detalle de E09: Sin código GRD: 90; CDM 99: 4.952. Detalle de E10 (un egreso puede cumplir más de una condición): sin fecha de nacimiento: 37; fecha de nacimiento posterior al ingreso: 1; edad al ingreso mayor de 110 años: 26; sin tipo de alta: 101.

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
| DOMICILIO | 4.932.337 | 95,69 % |
| HOSPITALIZACIÓN DOMICILIARIA | 131.548 | 2,55 % |
| ALTA VOLUNTARIA | 53.216 | 1,03 % |
| DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE | 20.578 | 0,40 % |
| FUGA DEL PACIENTE | 16.926 | 0,33 % |

| Tipo de actividad | Casos de estudio | % |
|---|---|---|
| HOSPITALIZACIÓN | 4.302.657 | 83,47 % |
| CIRUGÍA MAYOR AMBULATORIA (CMA) | 851.948 | 16,53 % |

| Tipo de ingreso | Casos de estudio | % |
|---|---|---|
| URGENCIA | 2.502.556 | 48,55 % |
| PROGRAMADA | 1.766.662 | 34,27 % |
| OBSTETRICA | 884.979 | 17,17 % |
| (sin dato) | 408 | 0,01 % |

## 8. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `persona_dias_fnac` | 366 | Dos egresos con el mismo identificador son de personas distintas cuando sus fechas de nacimiento difieren en más de este número de días (D18) |
| `persona_mismo_dia_mes` | SI | SI = si las fechas de nacimiento coinciden en día y mes son de la misma persona aunque difieran en más de un año: error de digitación en el año (D18) |
| `id_generico_min_personas` | 5 | Un identificador con este número de combinaciones distintas de sexo y fecha de nacimiento, o más, se considera genérico (D18) |
| `traslado_dias_max` | 1 | Un ingreso en otro hospital hasta este número de días después del alta continúa el mismo episodio asistencial: 0 = solo el mismo día; 1 = el mismo día o el siguiente (D19) |
| `traslado_exige_marca` | NO | SI = además debe constar el traslado en el tipo de alta (derivación) o en la procedencia del ingreso (otros hospitales) (D19) |
| `censura_dias` | 30 | Días de seguimiento que deben quedar dentro del bloque después del alta (D22) |
| `edad_maxima` | 110 | Edad al ingreso, en años, sobre la cual la fecha de nacimiento se considera no válida (D21) |

Cierre de cada bloque de identificador: A, 31-12-2020; B, 31-12-2024.

## 9. Columnas nuevas

| Columna | Contenido |
|---|---|
| `ID_PERSONA` | Identificador de la persona: `ID_PACIENTE` × 100 + número de persona. Sin dato en los egresos sin identificador o con identificador genérico. |
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
| `EXC_CENSURA` | E11. Ventana de seguimiento incompleta: el alta está demasiado cerca del cierre del bloque. |
| `EXC_ALTA_VOLUNTARIA_FUGA` | E12. Alta voluntaria o fuga del paciente. |
| `EXC_CMA` | E13. Cirugía mayor ambulatoria. |
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
- El archivo escrito tiene las filas esperadas: **sí**.
- Las columnas originales conservan su nombre, orden y tipo de dato: **sí**.
- Contenido idéntico al de la tabla integrada en 7 columnas de control: **sí**.
- Las columnas nuevas releídas del archivo son iguales a las calculadas: **sí**.
