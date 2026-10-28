# Bitácora de la actividad 3.1: filtro de dimensionalidad (tamaño de efecto)

Registro de los hallazgos y decisiones de la actividad 3.1 de la Carta Gantt, que corresponde a la Etapa 3
del procedimiento de la propuesta (ingeniería de variables y reducción de la dimensionalidad). Continúa la
numeración de las bitácoras anteriores (`docs/bitacora.md`, `2.2_depuracion_etiquetado/bitacora.md` y
`2.3_validacion_particion/bitacora.md`): aquí están los hallazgos H30 a H32 y la decisión D45. Una entrada no
se borra: si una decisión cambia, se agrega una nueva entrada que la reemplaza y se indica en el campo
**Estado**.

La actividad se hace en dos pasos. El primero, registrado aquí el 28 de octubre de 2026, es el filtro de los
códigos de diagnósticos y procedimientos. El segundo construirá las demás variables (las administrativas y
demográficas de la propuesta y la historia de 12 meses de D42 y D44 de la bitácora de la 2.3), que no pasan
por el filtro, y las tablas que usarán los modelos. Todo se calcula solo con el conjunto de desarrollo; el
conjunto de prueba no se abre. Al terminar los dos pasos se pedirá una sola revisión al profesor guía, que
incluirá la consulta sobre el umbral de V (H30).

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

---

## Pendientes

- Paso 2 de la actividad: construir las demás variables (edad, sexo, previsión, región, tipo de ingreso, estadía índice, hospitalizaciones previas e historia de 12 meses con la marca de ventana cortada, índice de comorbilidad, CDM y peso GRD). Antes hay que decidir qué variables entran, cómo contar las hospitalizaciones previas, la historia adicional y el índice de comorbilidad.
- Cierre de la actividad: armar las tablas que usarán los modelos (las variables más los códigos de la lista), con su prueba, su diccionario y su registro de versión. Conviene que su reporte incluya también el desglose de los códigos que quedan fuera y la lista ampliada de H30, para que esas cifras queden reproducibles.
- Revisión del profesor guía, al terminar la actividad, en un informe de avance que incluya: el umbral de V y la comparación de las listas A y C en la actividad 3.2 (H30), el mínimo de pacientes distintos (H32), el hospital como variable, la deriva de la codificación (H31) y si usar el índice de Charlson o el de Elixhauser.
