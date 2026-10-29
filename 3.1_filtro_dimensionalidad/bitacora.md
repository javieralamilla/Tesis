# Bitácora de la actividad 3.1: filtro de dimensionalidad (tamaño de efecto)

Registro de los hallazgos y decisiones de la actividad 3.1 de la Carta Gantt, que corresponde a la Etapa 3
del procedimiento de la propuesta (ingeniería de variables y reducción de la dimensionalidad). Continúa la
numeración de las bitácoras anteriores (`docs/bitacora.md`, `2.2_depuracion_etiquetado/bitacora.md` y
`2.3_validacion_particion/bitacora.md`): aquí están los hallazgos H30 a H33 y las decisiones D45 a D49. Una entrada no
se borra: si una decisión cambia, se agrega una nueva entrada que la reemplaza y se indica en el campo
**Estado**.

La actividad se hace en dos pasos y un cierre. El primero, registrado aquí el 28 de octubre de 2026, es el
filtro de los códigos de diagnósticos y procedimientos (D45). El segundo, registrado el 29 de octubre de 2026,
construye las demás variables, que no pasan por el filtro: las administrativas y demográficas de la propuesta,
la historia de 12 meses de D42 y D44 de la bitácora de la 2.3, el índice de comorbilidad y las demás columnas
del CMBD (D46 a D49). El cierre armará las tablas que usarán los modelos. Todo se calcula solo con el conjunto
de desarrollo; el conjunto de prueba no se abre. Al terminar se pedirá una sola revisión al profesor guía, que
incluirá la consulta sobre el umbral de V (H30), el índice de comorbilidad (D48) y el hospital como predictora
(D49).

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

| Tema | Entrada | Definición |
|---|---|---|
| Filtro de códigos | D45 | Para cada variable de reingreso pasa un código de diagnóstico o de procedimiento si su V de Cramér es mayor o igual a 0,01 y lo tienen al menos 100 casos de estudio con dato en esa variable. Se calcula una sola vez con todo el conjunto de desarrollo y la lista queda fija. |
| La V y los códigos poco frecuentes | H30 | La V mezcla la fuerza del efecto con la frecuencia del código. Con `REING_30D` deja fuera 1.178 códigos con 100 casos o más que duplican o reducen a la mitad el riesgo. Se propone comparar en la 3.2 los modelos con la lista actual y con una lista ampliada. |
| Códigos que cambian con los años | H31 | 27 de los 423 códigos que pasan con `REING_30D` cambian su frecuencia más del triple entre años; varios siguen el ritmo de la pandemia. |
| Códigos que dependen de una persona | H32 | El único código que deja fuera solo el mínimo de 100 casos debe 18 de sus 19 reingresos a una misma paciente. Entre los que pasan, solo dos dependen así de una persona. |
| Variables de la propuesta | D46 | Edad al propio ingreso, sexo, previsión en 8 grupos, región desde la provincia, tipo de ingreso, estadía del episodio completo, CDM y peso GRD. Los faltantes quedan como SIN DATO, sin imputar. |
| Historia de 12 meses | D47 | Hospitalizaciones previas (todas y las no planificadas), días desde la última, cirugías mayores ambulatorias y sesiones en los 365 días antes del ingreso índice, sin el propio episodio, y la marca de ventana cortada. |
| Índice de comorbilidad | D48 | Número de condiciones de Elixhauser (Quan et al., 2005) en todos los diagnósticos del egreso, con tres jerarquías; Charlson con los pesos de Quan et al. (2011) como comparación. |
| Demás columnas del CMBD | D49 | Entran sin filtro las 15 columnas que describen al paciente o su hospitalización; en las tomadas tal cual, los valores con menos de 100 casos pasan a OTRO. El hospital queda en la tabla y su uso como predictora se consulta. |
| Tratamientos periódicos | H33 | Trece personas con tratamientos de un día sin código Z51 suman 697 casos con 50 o más hospitalizaciones previas. |

---

### D45 · 2026-10-28 · Filtro de los códigos por tamaño de efecto
- **Actividad:** 3.1
- **Decisión:** Los diagnósticos (CIE-10) y los procedimientos (CIE-9-MC) de cada caso de estudio se usan como indicadores sí/no. Para cada una de las cuatro variables de reingreso y cada código se arma la tabla de 2×2 (tiene o no el código, reingresa o no) con los casos de estudio que tienen dato en esa variable, y se calculan el chi-cuadrado de Pearson (sin corrección de Yates), su valor p y la V de Cramér, que en una tabla de 2×2 es la raíz de chi-cuadrado dividido por el número de casos. Pasa un código si su V es mayor o igual a 0,01 y lo tienen al menos 100 casos. El valor p se informa, pero no decide.
- **Detalle:** Se usa el código completo, tal como viene (E11.9), en cualquier posición; un código repetido en un caso cuenta una vez. Los casos sin dato en una variable no entran en su filtro: las variables de 30 días no incluyen los casos sin 60 días de seguimiento (D30 de la bitácora de la 2.2), y las de misma CDM no incluyen los partos (D38). Pasan tanto los códigos que suben el riesgo como los que lo bajan.
- **Una sola vez y fijo:** El filtro se calcula una vez con todo el conjunto de desarrollo y la lista queda fija: las etapas siguientes la aplican sin recalcularla, también al conjunto de prueba en la evaluación final. Es lo que dice la Etapa 3 de la propuesta («los umbrales y los códigos retenidos quedan fijados aquí y se aplican después sin recalcular»); la reserva previa del conjunto de prueba controla la fuga desde la selección hacia la estimación final (Etapa 4). El ajuste dentro de cada partición de D37 vale para los pasos de los modelos de la actividad 3.2, como el desbalance o los datos faltantes.
- **Resultado:** En los 3.354.118 casos de estudio de desarrollo hay 16.336 diagnósticos y 3.753 procedimientos distintos (18.458.052 y 29.327.510 pares caso–código; 5,50 y 8,74 por caso).

  | Variable | Casos con dato | Reingresos | Diagnósticos que pasan | Procedimientos que pasan | Total |
  |---|---|---|---|---|---|
  | `REING_7D` | 3.354.118 | 69.299 (2,07 %) | 60 | 48 | 108 |
  | `REING_7D_CDM` | 2.861.785 | 36.200 (1,26 %) | 43 | 14 | 57 |
  | `REING_30D` | 3.281.764 | 193.589 (5,90 %) | 281 | 142 | 423 |
  | `REING_30D_CDM` | 2.798.814 | 99.444 (3,55 %) | 131 | 59 | 190 |

  En las cuatro listas aparecen 490 códigos distintos (337 diagnósticos y 153 procedimientos); 19.599 no pasan en ninguna variable, y solo 5 diagnósticos y 9 procedimientos pasan en las cuatro.
- **Qué queda fuera y por qué:** Cada código tiene que cumplir los dos umbrales. El primero, el mínimo de casos, deja fuera sobre todo códigos muy raros: 6.234 diagnósticos tienen menos de 10 casos. El segundo, la V, deja fuera códigos frecuentes que casi no cambian el reingreso, pero también algunos de efecto grande (H30). El número de códigos con menos de 100 casos cambia según la variable porque cada una cuenta solo sus casos con dato: 115 y 170 códigos, como Z37.0 (nacido vivo, único), no tienen ningún caso en las variables de misma CDM, que no incluyen los partos.

  |  | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|
  | Códigos distintos | 20.089 | 20.089 | 20.089 | 20.089 |
  | Fuera por tener menos de 100 casos | 12.893 | 13.101 | 12.963 | 13.166 |
  | Fuera por V menor que 0,01, con 100 casos o más | 7.088 | 6.931 | 6.703 | 6.733 |
  | Pasan | 108 | 57 | 423 | 190 |
  | Parte de las apariciones de códigos que corresponde a los que pasan | 34,8 % | 14,3 % | 65,0 % | 35,9 % |
  | Casos con al menos un código de la lista | 92,1 % | 83,5 % | 98,2 % | 95,5 % |

- **Ejemplos con `REING_30D`:** N18.5 (enfermedad renal crónica, estadio 5) está en 76.223 casos; reingresa el 15,31 % frente al 5,68 % sin el código, chi-cuadrado 12.441 y V 0,0616: pasa. Z37.0 (nacido vivo, único) reingresa el 1,43 % frente al 6,65 %, V 0,0777: pasa, porque baja el riesgo. K80.2 (cálculo de la vesícula biliar sin colecistitis) tiene p = 0,0000000004 pero V 0,0035: no pasa. U07.1 (COVID-19, virus identificado) reingresa el 5,84 % frente al 5,90 %: no pasa.
- **Por qué un mínimo de 100 casos:** El valor viene de la propuesta («una prevalencia mínima de 100 egresos»). Lo respaldan cuatro razones:
  1. Con pocos casos, la tasa de reingreso de un código es demasiado imprecisa. Para una tasa observada de 5,9 %, el intervalo de confianza al 95 % (de Wilson) va de 1,2 % a 24,8 % con 20 casos, de 2,7 % a 12,3 % con 100 y de 4,6 % a 7,5 % con 1.000. Un código que pasa con unos 100 casos necesita al menos 48,6 % de reingreso a 30 días, y su intervalo (39,0 % a 58,3 %) queda lejos de 5,9 %.
  2. Con pocos casos, un código puede reflejar a una sola persona hospitalizada muchas veces. El único código que el mínimo deja fuera tiene ese problema (H32).
  3. Los modelos necesitan ver el código en todas las particiones: con 100 casos quedan unos 80 para entrenar y unos 20 para evaluar en cada partición de la validación cruzada. Todos los códigos que pasan conservan al menos 134 casos en 2019–2022 (validación temporal) y 61 en 2020 y 2022 (sensibilidad de D44). Una variable con muy pocos casos da coeficientes exagerados en la regresión logística (sesgo por datos escasos).
  4. Es un valor laxo: 100 casos son el 0,003 % de los casos de estudio. Los códigos con menos de 100 casos son el 67,9 % de los diagnósticos distintos y el 47,9 % de los procedimientos, pero solo el 1,09 % y el 0,19 % de sus apariciones.

  Además, con 100 casos y la tasa a 30 días (5,9 %) se esperan 5,9 reingresos si el código no tuviera relación con el reingreso, lo que cumple la regla de al menos 5 casos esperados por celda del chi-cuadrado (Cochran). En las variables de 7 días no se cumple (harían falta 242 y 395 casos), otra razón para que el filtro decida con la V y no con el valor p.
- **Sensibilidad:** Con V mínima de 0,005 pasarían 417, 206, 1.074 y 601 códigos; con 0,02, 19, 10, 145 y 54. El mínimo de casos casi no cambia el resultado:

  | Casos mínimos (con V de 0,01) | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|
  | Sin mínimo | 108 | 58 | 423 | 190 |
  | 50 | 108 | 58 | 423 | 190 |
  | 100 (principal) | 108 | 57 | 423 | 190 |
  | 500 | 108 | 53 | 421 | 188 |

  Es tan estable porque la V ya exige mucho a un código raro: con `REING_30D`, un código necesita al menos 21 casos para llegar a 0,01 aunque todos reingresen (H30). La tabla completa de la sensibilidad está en la sección 3 del reporte 14; la fila «sin mínimo» y el desglose de los códigos que quedan fuera salen de una exploración de solo lectura del 28 de octubre de 2026 sobre `filtro_codigos.parquet` y el conjunto de desarrollo.
- **Alternativas descartadas:** (1) Usar solo la categoría del código, los tres primeros caracteres (E11): juntaría códigos con riesgos distintos, como I50.0 (insuficiencia cardíaca congestiva, 12,76 % de reingreso a 30 días) e I50.9 (no especificada, 10,52 %); queda como parámetro (`nivel_codigo`). (2) Calcular el filtro dentro de cada partición de la validación cruzada: no es lo que dice la propuesta; en un ensayo del 26 de octubre las listas de cinco particiones al azar diferían de la de todo el conjunto de desarrollo en 12 a 21 de los 281 diagnósticos de `REING_30D`, todos cerca del umbral. (3) Agregar el GRD como tercer bloque del filtro: no está en la propuesta.
- **Verificación:** El script tiene 12 verificaciones internas, todas cumplidas. La prueba independiente (`pruebas/verificar_14_filtro_codigos.py`) vuelve a calcular, sin usar las funciones del script, 358 códigos (300 al azar con la semilla 2026, los que quedan en el límite de los umbrales y los cinco ejemplos) revisando columna por columna, calcula la V como la correlación entre «tiene el código» y «reingresa» y el valor p con la distribución normal, y revisa la tabla completa y la lista: 17 de 17 comprobaciones cumplidas. Con una copia de los resultados con dos errores puestos a propósito, la prueba los detectó.
- **Parámetros:** `variables_objetivo`, `nivel_codigo` (`COMPLETO`), `v_minima` (0,01), `casos_minimos` (100), `v_sensibilidad` (0,005, 0,01 y 0,02) y `casos_sensibilidad` (50, 100 y 500), en `reglas/parametros.csv`.
- **Evidencia:** `3.1_filtro_dimensionalidad/scripts/14_filtro_codigos.py` → `data/processed/filtro_codigos.parquet` (80.356 filas: cada código con cada variable, pase o no), `reportes/14_codigos_retenidos.csv` (la lista fija, 778 filas) y `reportes/14_filtro_codigos.md`; prueba en `reportes/pruebas_filtro_codigos.md`. Las descripciones vienen de `Datos/Tablas auxiliares/CIE-10.xlsx` y `CIE-9.xlsx`, que describen todos los códigos que pasan.
- **Referencias del mínimo:** Wilson, E. B. (1927), *Journal of the American Statistical Association*, 22, 209–212 (intervalo de confianza); Cochran, W. G. (1954), *Biometrics*, 10(4), 417–451 (casos esperados en el chi-cuadrado); Greenland, S., Mansournia, M. A. y Altman, D. G. (2016), *BMJ*, 352, i1981 (sesgo por datos escasos).
- **Estado:** Adoptada (aprobada por la persona a cargo el 26 de octubre de 2026). Pendiente de validar con profesor guía, en especial el umbral de V (H30).

### H30 · 2026-10-28 · La V castiga a los códigos poco frecuentes
- **Actividad:** 3.1
- **Hallazgo:** La V mide cuánto explica un código el reingreso de todos los casos, no solo el de los suyos, así que mezcla dos cosas: la fuerza del efecto y la frecuencia del código. Un código con pocos casos explica poco aunque su efecto sea grande, y necesita una tasa de reingreso muy alta para llegar a 0,01. Con `REING_30D` (tasa general 5,90 %):

  | Casos con el código | Reingreso a 30 días necesario para pasar | V máxima posible, si todos reingresan |
  |---|---|---|
  | 100 | 48,6 % | 0,022 |
  | 1.000 | 19,4 % | 0,070 |
  | 10.000 | 10,2 % | 0,221 |
  | 100.000 | 7,2 % | 0,708 |

- **Ejemplo:** D61.3 (anemia aplástica idiopática) tiene 149 casos y 35,6 % de reingreso a 30 días, seis veces la tasa general, y no pasa (V 0,0085).
- **Códigos que bajan el riesgo:** Aunque ninguno de sus casos reingrese, un código necesita al menos 5.227 casos para pasar con `REING_30D` (15.824 con `REING_7D`, 22.165 con `REING_7D_CDM` y 7.577 con `REING_30D_CDM`).
- **Escala de la V:** La V más alta de toda la tabla es 0,078 (Z37.0 con `REING_30D`) y 0,088 (75.34 con `REING_30D_CDM`). En la escala habitual (Cohen, 1988) 0,1 ya es un efecto pequeño: la propuesta llama laxo al umbral de 0,01 porque está diez veces por debajo, pero con un reingreso poco frecuente la V de casi todos los códigos es baja, y 0,01 resulta exigente para los que tienen unos pocos miles de casos.
- **Códigos de efecto grande que quedan fuera:** Con `REING_30D`, de los 6.703 códigos con 100 casos o más que no llegan a V 0,01, 1.178 tienen un efecto grande y claro: con el código el riesgo es al menos el doble o como máximo la mitad que sin él, con p < 0,001 (691 suben el riesgo y 487 lo bajan; mediana de 642 casos). Por ejemplo, R57.0 (choque cardiogénico: 3.512 casos, 11,9 % de reingreso, V 0,0084), C79.3 (tumor maligno secundario del encéfalo: 3.530 casos, 11,8 %) y J84.9 (enfermedad pulmonar intersticial: 3.318 casos, 12,1 %), y entre los que lo bajan, 69.09 (legrado y dilatación del útero: 12.414 casos, 2,2 %). Los otros 5.525 tienen, en general, un efecto menor: en el caso típico el riesgo con el código es solo 11 % mayor. Con las otras variables, los de efecto grande y claro que quedan fuera son 741 (`REING_7D`), 572 (`REING_7D_CDM`) y 979 (`REING_30D_CDM`).
- **Y al revés:** Pasan 54 códigos de efecto débil (riesgo con el código entre 0,67 y 1,5 veces el de sin él) solo porque son muy frecuentes, como 99.29 (inyección de otra sustancia terapéutica o profiláctica: 2.299.500 casos, 0,91 veces) y 90.59 (1.947.450 casos, 1,26 veces).
- **Cuánto se pierde:** Con `REING_30D`, 938.101 casos (28,6 %) tienen alguno de los 1.178 códigos de efecto grande que quedan fuera, pero el 97,2 % de ellos tiene además algún código de la lista. Solo 26.283 casos (0,8 %) tienen uno de esos códigos y ninguno de la lista. Parte de esa información vuelve por las variables del paso 2; por ejemplo, la metástasis cuenta en el índice de Charlson.
- **Interpretación:** La V favorece los códigos que pueden aportar a la predicción en toda la población, que es como se evalúan los modelos (AUROC y AUPRC sobre todos los casos): un código poco frecuente, aunque duplique el riesgo, cambia la predicción de pocos casos. Su costo es clínico, porque deja fuera marcadores fuertes pero poco frecuentes. En la literatura, los filtros univariados se usan como un primer cribado laxo antes de la selección dentro de los modelos (Guyon y Elisseeff, 2003), muchas veces ordenando los códigos en vez de usar un umbral fijo (Fan y Lv, 2008), y los modelos de reingreso más usados resumen los diagnósticos con índices de comorbilidad (Kansagara et al., 2011).
- **Alternativas para la consulta:** (A) Mantener V ≥ 0,01, como dice la propuesta: 108, 57, 423 y 190 códigos. (B) Bajar a V ≥ 0,005: 417, 206, 1.074 y 601; recupera solo 325 de los 1.178 códigos de efecto grande de `REING_30D` y agrega 103 frecuentes de efecto débil, como 99.21 (inyección de antibiótico: 1.499.078 casos, 1,05 veces). (C) Pasa un código con al menos 100 casos si su V es mayor o igual a 0,01 o si su riesgo es al menos el doble o como máximo la mitad que sin él, con p < 0,001: 849, 629, 1.601 y 1.169; con unos 7.000 códigos de 100 casos o más, ese valor p deja pasar como mucho unos 7 por azar.
- **Propuesta para el profesor guía:** Mantener A como lista principal y medir su costo en la actividad 3.2: entrenar los mismos modelos, con la misma validación cruzada, con la lista A y con la lista C, y comparar la AUPRC y la AUROC. Si dan igual, el filtro no pierde nada importante; si C predice mejor, se adopta C. Cambiar la lista solo requiere el parámetro correspondiente y volver a ejecutar el script 14 y su prueba.
- **Evidencia:** `reportes/14_filtro_codigos.md`, secciones 3 y 4. Los códigos de efecto grande que quedan fuera, los de efecto débil que pasan, la V máxima posible y la opción C salen de una exploración de solo lectura del 28 de octubre de 2026 sobre `filtro_codigos.parquet` y el conjunto de desarrollo.
- **Referencias:** Cohen, J. (1988), *Statistical Power Analysis for the Behavioral Sciences* (2.ª ed.); Guyon, I. y Elisseeff, A. (2003), *Journal of Machine Learning Research*, 3, 1157–1182; Fan, J. y Lv, J. (2008), *Journal of the Royal Statistical Society, Series B*, 70(5), 849–911; Kansagara, D., et al. (2011), *JAMA*, 306(15), 1688–1698.

### H31 · 2026-10-28 · Algunos códigos que pasan cambian mucho con los años
- **Actividad:** 3.1
- **Hallazgo:** El formato de los códigos no cambia entre años, pero sí la frecuencia de algunos. Con `REING_30D`, 17 de los 281 diagnósticos y 10 de los 142 procedimientos que pasan varían más del triple entre su año de menor y de mayor frecuencia; con las otras variables, entre 1 y 5. Ningún código que pasa falta en algún año.
- **Ejemplos:** 90.39 («examen microscópico ORL, otro») está en el 3,4 % de los casos de estudio de 2019, el 39,3 % de 2021 y el 10,6 % de 2024: sigue el ritmo de la pandemia. 99.84 («aislamiento») va de 2,5 % a 10,1 % y 4,2 %, y J96.00 (insuficiencia respiratoria aguda tipo I), de 0,4 % a 3,0 % y 2,1 %. Otros crecen todos los años, como E55.9 (deficiencia de vitamina D), de 0,13 % a 0,98 %, de la mano del aumento de diagnósticos por caso (de 4,60 en 2019 a 6,18 en 2024).
- **Consecuencia:** El filtro no cambia, pero el significado de esos códigos depende del período. Es parte de lo que medirá la validación temporal (D40 de la bitácora de la 2.3) y conviene comentarlo con el profesor guía.
- **Evidencia:** `reportes/14_filtro_codigos.md`, sección 7.

### H32 · 2026-10-28 · Pocos códigos dependen de una sola persona
- **Actividad:** 3.1
- **Hallazgo:** Sin el mínimo de 100 casos pasaría un solo código más: O35.2 (atención materna por presunta enfermedad hereditaria en el feto), con `REING_7D_CDM`. Tiene 63 casos con dato, 19 reingresos y V 0,0121, pero 22 de esos casos y 18 de los 19 reingresos son de una misma paciente. Sin ella quedan 41 casos y 1 reingreso (2,4 %): el código no describe un riesgo, describe a una persona.
- **Entre los que pasan:** Solo en dos códigos, ambos de `REING_7D_CDM`, una persona aporta más de la mitad de los reingresos: K90.8 (otros tipos de malabsorción intestinal: 289 casos, 37 reingresos, 33 de una misma persona) y O36.1 (atención materna por otra isoinmunización: 145 casos, 25 reingresos, 17 de una misma persona). En las otras tres variables ningún código que pasa tiene una persona con más del 10 % de sus reingresos; en el caso típico, la persona que más aporta tiene entre el 0,2 % y el 1,2 % de los reingresos del código.
- **Consecuencia:** El mínimo cuenta egresos, no personas: es una limitación que se declara. No invalida el filtro, que es laxo a propósito: en la actividad 3.2 la validación cruzada agrupada por paciente (D37) mostrará que un código así no sirve para predecir en otras personas. Se puede consultar al profesor guía si conviene exigir además un mínimo de pacientes distintos.
- **Evidencia:** exploración de solo lectura del 28 de octubre de 2026 sobre el conjunto de desarrollo (casos y reingresos por identificador de paciente de cada código, sin mostrar identificadores).

### D46 · 2026-10-29 · Variables administrativas y demográficas de la propuesta
- **Actividad:** 3.1
- **Decisión:** Las ocho variables de la Etapa 3 que describen al paciente y su hospitalización se construyen así, sin pasar por el filtro de códigos (la Etapa 3 dice que a ese filtro «no quedan expuestas las variables administrativas»):

  | Variable | Construcción | Sin dato |
  |---|---|---|
  | `EDAD` | Años con decimales al ingreso del propio egreso: días entre el nacimiento y el ingreso, divididos por 365,25 | — |
  | `SEXO` | Tal cual (hombre o mujer) | 313 |
  | `PREVISION_GRUPO` | Los 12 valores en 8 grupos: FONASA A, B, C y D; FONASA libre elección (sus tres modalidades); ISAPRE; particular; DIPRECA, CAPREDENA y SISA | 2.439 |
  | `REGION` | Región de residencia, desde la provincia: las 57 provincias de la base (también la antigua ÑUBLE) en 16 regiones | 1.090 |
  | `TIPO_INGRESO` | Tal cual (urgencia, programada u obstétrica), del propio egreso | 295 |
  | `ESTADIA` | Días del episodio completo, desde el ingreso índice (el que abre el episodio, D42) hasta el alta del caso | — |
  | `CDM` | Tal cual: los 22 valores de los casos de estudio, de 01 a 22 | — |
  | `PESO_GRD` | Número; el único caso con peso 0 (GRD 158021, de 2019) queda sin dato | 1 |

- **Faltantes y rangos:** En las variables de categorías el faltante es el valor SIN DATO; en las numéricas, un vacío. En la 3.1 no se imputa nada, y los números no se agrupan en rangos: eso se decide con cada modelo en la actividad 3.2.
- **Por qué la edad al propio ingreso:** Al ingreso índice salen 43 edades negativas, casi todas de recién nacidos (36 de la CDM 15) cuyo episodio empieza unos días antes de la fecha de nacimiento registrada (mediana de 3 días). Al ingreso del propio egreso no hay ninguna.
- **Estadía de los traslados:** En los 47.504 casos cuyo episodio empezó antes del ingreso a su último hospital, la mediana de la estadía es de 20 días contando todo el episodio y de 9 en el último hospital. Ejemplo: el caso `20230001746` (hospital 121109, del 29-12-2022 al 05-01-2023) continúa el egreso `20220068830` (hospital 129106, desde el 19-12-2022): `ESTADIA` vale 17 días, frente a 7 en el último hospital.
- **Reglas:** `reglas/prevision_grupos.csv` y `reglas/provincia_region.csv`.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 28 de octubre de 2026 (decisión 1 del paso 2).
- **Evidencia:** `3.1_filtro_dimensionalidad/scripts/15_variables_casos.py` → `data/processed/variables_casos.parquet` y `reportes/15_variables_casos.md`, secciones 1 y 2; prueba en `reportes/pruebas_variables_casos.md`.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D47 · 2026-10-29 · Historia de 12 meses y marca de ventana cortada
- **Actividad:** 3.1 (aplica D42 y D44 de la bitácora de la 2.3)
- **Decisión:** Seis variables describen lo ocurrido a la misma persona (`ID_PERSONA`, D18) en los 365 días antes del ingreso índice, sin contar el propio episodio. Se usan todos sus egresos, sean o no casos de estudio; los de hospitalización diurna o en urgencia de 2019 (E04) no tienen episodio y no entran.

  | Variable | Qué cuenta |
  |---|---|
  | `HOSP_PREVIAS` | Episodios (no egresos) con al menos un egreso que no es cirugía mayor ambulatoria ni sesión, cuya alta final cae en la ventana |
  | `HOSP_PREVIAS_NO_PLANIF` | De ellos, los que empezaron con un ingreso no planificado, con la regla de D20 y D33 |
  | `DIAS_ULTIMA_HOSP` | Días desde el alta de la última de esas hospitalizaciones hasta el ingreso índice; 366 si no hay ninguna |
  | `CMA_PREVIAS` | Egresos de cirugía mayor ambulatoria terminados en la ventana |
  | `SESIONES_PREVIAS` | Egresos de sesión de tratamiento (diagnóstico principal Z51) terminados en la ventana |
  | `VENTANA_CORTADA` | 1 si la ventana empieza antes del primer día del bloque del identificador (D42 y D44) |

- **Ventana:** Cuenta lo que terminó entre el ingreso índice menos 365 días y el ingreso índice, ambos días incluidos. Una hospitalización que terminó el mismo día del ingreso índice cuenta, igual que el etiquetado cuenta el día 0 como reingreso (D20). Los 365 días son los 12 meses de D42 y mantienen las fechas de la marca: la ventana está cortada si el ingreso índice es anterior al 1 de enero de 2020 en el bloque A o al 1 de enero de 2022 en el bloque B.
- **Detalles:** La regla de «no planificado» se lee de los parámetros de la 2.2, para que sea la misma del etiquetado. Las cirugías ambulatorias y las sesiones cuentan egresos; un egreso que es las dos cosas (1.085 en desarrollo) cuenta como cirugía, por el orden de los criterios E13 y E14. En 143.031 casos el propio episodio dura 0 días: termina el mismo día del ingreso índice y se descuenta para no contarlo como hospitalización previa.
- **Ejemplo:** El caso `20230000956` (ingreso índice el 15-02-2023) tiene en su ventana una hospitalización por urgencia (`20220430860`, alta el 02-08-2022, tuberculosis), una programada (`20220568135`, alta el 14-09-2022) y una cirugía mayor ambulatoria de catarata (`20220694463`, 02-11-2022). Resultado: `HOSP_PREVIAS` = 2, `HOSP_PREVIAS_NO_PLANIF` = 1, `CMA_PREVIAS` = 1 y `DIAS_ULTIMA_HOSP` = 154, contados desde el 14 de septiembre, porque la catarata no es una hospitalización.
- **Resultado:** 1.173.474 casos con la ventana cortada (todos los de 2019 y 2021, 9.346 de 2020, 8.820 de 2022 y 8 de 2023), igual que en D44. Reingreso a 30 días según las hospitalizaciones previas:

  | Hospitalizaciones previas | Casos sin marca | Reingreso a 30 días | Casos con marca | Reingreso a 30 días |
  |---|---|---|---|---|
  | 0 | 1.663.338 | 4,53 % | 978.106 | 4,64 % |
  | 1 | 344.466 | 8,19 % | 142.843 | 9,04 % |
  | 2 | 99.865 | 12,29 % | 33.250 | 13,84 % |
  | 3 | 36.099 | 17,00 % | 10.344 | 19,08 % |
  | 4 | 15.548 | 21,04 % | 3.847 | 23,52 % |
  | 5 o más | 21.328 | 26,07 % | 5.084 | 24,04 % |

- **Diferencia con la exploración:** La exploración del 28 de octubre usó 12 meses de calendario y no contaba la hospitalización terminada el mismo día del ingreso índice; con 5 o más hospitalizaciones previas daba 26,08 % en vez de 26,07 % (22 casos de 21.328).
- **Alternativas descartadas:** (1) 12 meses de calendario: la ventana mediría 365 o 366 días según el año, y 366 se confundiría con «sin hospitalización». (2) No contar la hospitalización terminada el mismo día del ingreso índice: se perdería la información de quien vuelve a hospitalizarse el mismo día de un alta.
- **Parámetros:** `ventana_historia_dias` (365), `inicio_bloques` (A desde el 1-1-2019, B desde el 1-1-2021) y `dias_sin_hospitalizacion` (366), en `reglas/parametros.csv`; de la 2.2, `ingresos_no_planificados`, `grd_parto` y `diagnosticos_sesion`.
- **Visto bueno:** La persona a cargo de la tesis aprobó la decisión 2 del paso 2 el 28 de octubre de 2026, y los detalles de la ventana el 29 de octubre, al aceptar el borrador del script («Sí, sigue»).
- **Completa a:** D42 y D44 de la bitácora de la 2.3. Ver también H33.
- **Evidencia:** `reportes/15_variables_casos.md`, sección 2. La prueba independiente recalcula la historia egreso por egreso en 3.062 casos, también en los bordes de la ventana.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D48 · 2026-10-29 · Índice de comorbilidad: Elixhauser, con Charlson como comparación
- **Actividad:** 3.1
- **Decisión:** `INDICE_COMORBILIDAD` es el número de condiciones de Elixhauser presentes en el caso: 31 condiciones con los códigos CIE-10 de Quan et al. (2005), buscadas en todos los diagnósticos del egreso (principal y secundarios), con tres jerarquías: la diabetes con complicaciones reemplaza a la sin complicaciones, el cáncer metastásico al tumor sólido sin metástasis y la hipertensión con complicaciones a la sin complicaciones. El índice de Charlson con los pesos de Quan et al. (2011) se calcula siempre como comparación: el reporte muestra los dos, y con `indice_comorbilidad` = CHARLSON reemplaza a Elixhauser en la misma columna, para compararlos en la actividad 3.2. No se agrega una segunda columna.
- **Fundamento:** Solo, el índice de Elixhauser ordena algo mejor a los casos que reingresan a 30 días (área bajo la curva ROC de 0,617, frente a 0,608 de Charlson; el número de diagnósticos da 0,613) y cubre condiciones que Charlson no tiene, como arritmias, trastornos de líquidos y electrolitos, anemias, depresión, abuso de alcohol o drogas y obesidad. Charlson se diseñó para predecir la mortalidad. Con solo los diagnósticos secundarios, los dos índices ordenaban peor.
- **Resultado:** Tienen al menos una condición el 59,2 % de los casos con Elixhauser (de 0 a 15 condiciones; promedio de 1,33) y el 37,2 % con Charlson. Con los pesos de Quan et al. (2011) cinco condiciones de Charlson valen 0 puntos, así que solo el 27,1 % tiene un puntaje de Charlson mayor que 0. El reingreso a 30 días va de 3,81 % sin condiciones de Elixhauser a 13,09 % con 5 o más.
- **Jerarquías:** Sin ellas, 6.078 casos contarían dos veces la diabetes y 13.852 la hipertensión. Ejemplo: el caso `20230120079` (diagnósticos E11.1, N39.0, I13.9, I10, Z88.0, Z91.1 y E11.6) tiene cuatro condiciones antes de las jerarquías y dos después: diabetes con complicaciones e hipertensión con complicaciones.
- **Contraste de la tabla de códigos:** El artículo de Quan et al. (2005) es de pago y su copia en PubMed Central no se pudo abrir. La tabla se contrastó de forma automática con dos reproducciones independientes: el programa de Stata de la Universidad de Calgary escrito con H. Quan (Stagg) y el paquete comorbidity de R (Gasparini, 2018), del que se tomó. Las tres versiones, incluida la de la exploración del 28 de octubre, coinciden en las 48 condiciones (31 de Elixhauser y 17 de Charlson) y en sus 688 códigos. Los pesos de Quan et al. (2011) coinciden en dos paquetes de R (comorbidity y comorbidities.icd10). Queda pendiente revisar la tabla 2 del artículo, si se consigue.
- **Deriva:** Los casos con al menos una condición pasan de 52,2 % en 2019 a 65,5 % en 2024 con Elixhauser, y de 33,1 % a 41,5 % con Charlson, junto con el aumento de los diagnósticos por caso (H31).
- **Parámetros y reglas:** `indice_comorbilidad` (ELIXHAUSER), en `reglas/parametros.csv`; `reglas/comorbilidad_quan2005.csv`, con una fila por condición: sus códigos, su peso y a cuál reemplaza.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 28 de octubre de 2026 («Elixhauser, pero igualmente se puede dejar como validación»).
- **Evidencia:** `reportes/15_variables_casos.md`, sección 3. La prueba independiente compara la tabla con una transcripción de los rangos de Quan et al. (2005) y recalcula el índice de todos los casos con otro método.
- **Referencias:** Charlson, M. E., et al. (1987), *Journal of Chronic Diseases*, 40(5), 373–383; Elixhauser, A., et al. (1998), *Medical Care*, 36(1), 8–27; Quan, H., et al. (2005), *Medical Care*, 43(11), 1130–1139; Quan, H., et al. (2011), *American Journal of Epidemiology*, 173(6), 676–682; Gasparini, A. (2018), *Journal of Open Source Software*, 3(23), 648.
- **Estado:** Adoptada. Pendiente de validar con profesor guía (Charlson o Elixhauser).

### D49 · 2026-10-29 · Las demás columnas del CMBD entran sin filtro
- **Actividad:** 3.1
- **Decisión:** Además de las diez variables de la propuesta (D46 a D48), entran todas las columnas del CMBD que describen al paciente o su hospitalización. Ninguna se elige ni se descarta por su relación con el reingreso: la Etapa 3 aplica el filtro solo a los códigos y deja la selección a los modelos, para «preservar toda variable potencialmente relevante en un modelo multivariado». Cada columna entra tal cual si sus valores significan lo mismo todos los años, y si no, en la forma que sí se mantiene. En las tomadas tal cual, los valores con menos de 100 casos de estudio pasan a OTRO, con el mismo mínimo del filtro de códigos (D45).

  | Variable | Contenido | Forma | Valores |
  |---|---|---|---|
  | `TIPO_ALTA` | Destino al alta | Tal cual | 5 |
  | `SEVERIDAD` | Nivel de severidad del GRD (el último dígito del código) | Tal cual, de 1 a 3 | 3 |
  | `RIESGO_MORTALIDAD` | Nivel de riesgo de mortalidad del GRD | Tal cual, de 1 a 3 | 3 |
  | `ESPECIALIDAD_INTERVENCION` | Especialidad de la intervención del episodio | Tal cual, con SIN INTERVENCIÓN; la del tramo anterior si el egreso no tiene (11.574 casos) | 48 (36 valores, con 694 casos, en OTRO) |
  | `UCI_UTI` | Paso por cuidados intensivos o intermedios en el episodio | Sí o no, desde los servicios de ingreso, de traslado interno y de alta | 2 |
  | `TRASLADO` | El episodio pasó por más de un hospital (D19) | Sí o no | 2 |
  | `N_DIAGNOSTICOS` | Diagnósticos distintos del egreso | Número | De 0 a 35 |
  | `N_PROCEDIMIENTOS` | Procedimientos distintos del egreso | Número | De 0 a 30 |
  | `ESPECIALIDAD` | Especialidad médica del episodio | Tal cual | 59 (23 valores, con 250 casos, en OTRO) |
  | `TIPO_PROCEDENCIA` | De dónde llega el paciente | Tal cual | 18 (2 valores, con 4 casos, en OTRO) |
  | `SERVICIO_INGRESO` | Servicio clínico de ingreso | Tal cual | 85 (8 valores, con 248 casos, en OTRO) |
  | `SERVICIO_ALTA` | Servicio clínico de alta | Tal cual | 83 (8 valores, con 170 casos, en OTRO) |
  | `PUEBLO_ORIGINARIO` | La etnia nombra un pueblo originario | Sí o no: tal cual no es comparable, porque NINGUNO y OTRO se intercambian entre años | 3, con 3 casos sin dato |
  | `NACIONALIDAD_EXTRANJERA` | La nacionalidad no es chilena | Sí o no: desde 2020 algunos registros dicen un continente en vez de un país | 3, con 13.028 casos sin dato |
  | `HOSPITAL` | Código del hospital del egreso | Tal cual | 72 |

- **Episodio o egreso:** Lo que ocurre durante la hospitalización (la estadía de D46, la intervención, el paso por UCI o UTI y el traslado) se mide en todo el episodio; lo demás, en el egreso del caso, igual que los códigos de D45 y el índice de D48. Los tramos del propio episodio no son hospitalizaciones previas (D42): describen la hospitalización actual.
- **Reingreso a 30 días, solo descriptivo:** Domicilio 5,57 % y fuga 20,09 %; severidad 1, 2 y 3: 3,89, 7,09 y 9,62 %; riesgo de mortalidad 1, 2 y 3: 4,16, 8,24 y 10,63 %; sin intervención 8,21 %; con UCI o UTI 8,05 % frente a 5,55 % (474.420 casos, 14,1 %); con traslado 8,82 % frente a 5,85 % (56.167 casos, 1,7 %).
- **No son variables (no es un filtro):** Estas columnas no describen al paciente o su hospitalización, o ya entran en otra forma:

  | Columnas | Por qué no son variables |
  |---|---|
  | Identificadores y datos del archivo: `ID_EGRESO`, `ID_PACIENTE`, `ID_PERSONA`, `ID_EPISODIO`, los médicos encriptados, el año, `BLOQUE_ID` y el origen del registro | No describen la salud del paciente; con el año, la validación temporal evaluaría años que el modelo nunca vio |
  | La respuesta: las cuatro `REING_*`, `DIAS_REING` e `ID_EGRESO_REING` | Es lo que se quiere predecir |
  | Las marcas de la depuración: los criterios `EXC_*`, `MOTIVO_EXCLUSION`, `ES_CASO_ESTUDIO`, `PUEDE_SER_REINGRESO`, `IDENTIDAD_AMBIGUA` y las marcas del episodio | Describen cómo se armó la base; en los casos de estudio valen lo mismo para todos o repiten otra variable (`EXC_ALTA_VOLUNTARIA_FUGA` marca los mismos 55.435 casos de alta voluntaria y fuga del tipo de alta) |
  | Las fechas, los diagnósticos y los procedimientos, la provincia, la comuna, el servicio de salud, el código GRD y los servicios de traslado interno | Son la materia prima de otras variables: la edad, la estadía y la historia; los códigos de D45, los conteos y el índice; la región (la comuna y el servicio de salud son la misma información en otro tamaño, y la propuesta eligió la región); la CDM, el peso y la severidad; el paso por UCI o UTI |
  | `USOSPABELLON`, `FECHAINTERV1`, `HOSPPROCEDENCIA` y la condición y el «estado» del recién nacido | No se registran igual todos los años: el tipo de pabellón no tiene datos en 2020; la fecha de intervención está en el 50,6 % de los casos de 2019 y en el 38,5 % de los de 2024; el hospital de procedencia tiene 518 nombres sin unificar; la condición del recién nacido solo existe en 2019 y su «estado» no tiene un significado documentado |
  | `TIPO_ACTIVIDAD` y el peso y el sexo del recién nacido | El tipo de actividad vale lo mismo en todos los casos de estudio (hospitalización); el peso y el sexo del recién nacido están completos en los partos, pero describen al bebé, no a la paciente del caso |
- **Antecedente:** La primera propuesta, del 28 de octubre de 2026, dejaba fuera el servicio de alta y el de ingreso, el pueblo originario y la nacionalidad extranjera, con razones de interpretación y, en el pueblo originario, por su poca relación con el reingreso. La persona a cargo observó que en la propuesta las columnas del CMBD no pasan por ningún filtro («por lo que entiendo las variables del cmbd pasan todas, exceptuando procedimientos y diagnosticos») y se corrigió. Esas razones quedan como limitaciones.
- **Limitaciones para interpretar los resultados:**

  | Tema | Limitación |
  |---|---|
  | Servicios de ingreso y de alta | Los nombres dependen de cómo organiza sus camas cada hospital: «ÁREA MÉDICO-QUIRÚRGICO CUIDADOS MEDIOS», que usan 27 hospitales, mezcla 29.612 casos de cirugía general, 25.384 de medicina interna y 13.623 de traumatología, y 26 de los 90 servicios de alta se usan en 3 hospitales o menos |
  | Nacionalidad extranjera | Los extranjeros reingresan menos aun considerando su edad y sus partos (observado frente a esperado, 0,88), pero su seguimiento es más incompleto: el 85 % de los egresos sin identificador que no son de recién nacidos es de extranjeros (D21 de la bitácora de la 2.2) |
  | Paso por UCI o UTI | En 8 hospitales (108.186 casos, 3,2 %) casi no hay traslados internos registrados ni estadías en UCI o UTI: puede que no tengan esas unidades o que no las registren. Una de cada cinco estadías en UCI o UTI (103.100) solo se ve en los traslados internos |
  | Variables parecidas | La severidad y el riesgo de mortalidad, o el número de diagnósticos y el índice de comorbilidad, miden cosas cercanas: al medir la importancia de las variables en la actividad 3.2, se la repartirán |
  | Deriva de la codificación | La severidad 3 pasa de 13,2 % de los casos en 2019 a 21,8 % en 2024 y los diagnósticos por caso, de 4,60 a 6,18 (H31) |
- **Hospital:** `HOSPITAL` queda en la tabla. Considerando el tipo de paciente (CDM, severidad, edad, tipo de ingreso y sexo), el reingreso observado frente al esperado va de 0,77 a 2,03 entre hospitales; 7 hospitales no tienen casos antes de 2023 (24.055 de los 1.185.781 casos de evaluación de la validación temporal), y en 5 regiones un solo hospital tiene más del 90 % de los casos. Si se usa como predictora lo decide la revisión del profesor guía, antes de la actividad 3.2.
- **Parámetros:** `casos_minimos_categoria` (100), `servicios_criticos`, `servicios_criticos_excluidos`, `etnia_sin_pueblo` y `nacionalidad_local`, en `reglas/parametros.csv`.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 28 de octubre de 2026 («Sí, apruébala»).
- **Evidencia:** `reportes/15_variables_casos.md`, sección 4; la observación por hospital y por nacionalidad sale de una exploración de solo lectura del 28 de octubre de 2026 sobre el conjunto de desarrollo.
- **Referencias:** Li, Yao y Échevin (2020), citado en la propuesta (destino y departamento al alta entre los predictores más importantes); Donzé, J., et al. (2013), *JAMA Internal Medicine*, 173(8), 632–638 (puntaje HOSPITAL: alta desde oncología y procedimiento durante la estadía).
- **Estado:** Adoptada. Pendiente de validar con profesor guía, en especial el hospital como predictora.

### H33 · 2026-10-29 · Tratamientos periódicos de un día registrados como hospitalización
- **Actividad:** 3.1
- **Hallazgo:** 697 casos de 13 personas tienen 50 o más hospitalizaciones previas en la ventana de D47; el máximo es 342, mientras que el percentil 99 es 4 y el 99,9 es 13. De los 1.603 egresos de esas personas, el 72,4 % dura 0 días y el 94,5 % es programado. Sus diagnósticos principales más frecuentes son D66 (deficiencia hereditaria del factor VIII: 426 egresos), E76 (trastornos del metabolismo de los glucosaminoglicanos: 366), E78 (trastornos del metabolismo de las lipoproteínas: 229), Z29 (necesidad de otras medidas profilácticas: 198) y K91 (trastornos del sistema digestivo consecutivos a procedimientos: 151). Son tratamientos periódicos de un día, como infusiones o terapias de reemplazo, que no se codifican como sesión: D33 solo trata como sesión el diagnóstico principal Z51, así que cuentan como hospitalizaciones.
- **Consecuencia:** Las variables de historia no se corrigen: cuentan lo registrado, como define D47. Los valores extremos afectan sobre todo a la regresión logística; en la actividad 3.2 se decide, con cada modelo, si se transforma la variable (por ejemplo, con un logaritmo o un tope). Se puede consultar al profesor guía si estos tratamientos deberían tratarse como sesiones, lo que cambiaría la cohorte de la 2.2 (criterio E14).
- **Evidencia:** `reportes/15_variables_casos.md`, sección 2 (valores extremos); exploración de solo lectura del 28 de octubre de 2026 (diagnósticos y tipo de ingreso de los egresos de esas personas, sin mostrar identificadores).

---

## Pendientes

- Cierre de la actividad: armar las tablas que usarán los modelos (para cada variable de reingreso, las 30 variables de D46 a D49, los códigos de su lista de D45 y la variable objetivo), con su prueba, su diccionario y su registro de versión. Conviene que su reporte incluya también el desglose de los códigos que quedan fuera y la lista ampliada de H30, para que esas cifras queden reproducibles.
- Revisión del profesor guía, al terminar la actividad, en un informe de avance que incluya: el umbral de V y la comparación de las listas A y C en la actividad 3.2 (H30), el mínimo de pacientes distintos (H32), la deriva de la codificación (H31), el índice de comorbilidad (D48), el hospital como predictora y las limitaciones de las columnas del CMBD (D49) y los tratamientos periódicos (H33).
- Revisar la tabla 2 de Quan et al. (2005) si se consigue el artículo (D48).
- Para la actividad 3.2: decidir con cada modelo cómo se codifican las categorías y si se transforman los números con valores extremos (H33), y tener en cuenta que las variables parecidas se reparten la importancia (D49).
