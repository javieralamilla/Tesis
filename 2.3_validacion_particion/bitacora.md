# Bitácora de la actividad 2.3: validación, partición y reserva del conjunto de prueba

Registro de los hallazgos y decisiones de la actividad 2.3 de la Carta Gantt. Continúa la numeración
de las bitácoras anteriores (`docs/bitacora.md` y `2.2_depuracion_etiquetado/bitacora.md`): aquí están
el hallazgo H19 y las decisiones D27 a D29, D37 y D40 a D44. Una entrada no se borra: si una decisión cambia,
se agrega una nueva entrada que la reemplaza y se indica en el campo **Estado**.

Esta bitácora se reescribió el 8 de octubre de 2026. La versión del 6 de octubre no llegó a
presentarse y describía una partición que unía identificadores de paciente por fecha de nacimiento y
sexo; el profesor guía pidió, en su revisión del 7 de octubre, no enlazar pacientes entre los dos
sistemas de identificador sin una llave válida. Esa alternativa queda registrada como descartada en
D27. Los parámetros de la partición están en `reglas/parametros.csv`.

El profesor guía revisó la partición y el esquema de validación el 13 de octubre de 2026: considera
que la partición por paciente está bien construida, y aprueba D27 a D29 y D37 a condición de
incorporar dos puntos de su revisión: la validación temporal informada en tres grupos (punto 2.2) y
las métricas y la calibración (punto 2.3). Los dos quedaron incorporados el 20 de octubre (D40 y
D41). Ese día la partición también se volvió a ejecutar sobre la versión 2 del conjunto analítico
(D38 de la bitácora de la 2.2), con el mismo reparto de identificadores (versión 2 de la partición, D29).

En su revisión del 24 de octubre de 2026 el profesor guía dio por subsanados los dos puntos y aprobó D40 a
D42, dos de ellas con un ajuste: el intercepto de calibración se estima con el logit de la probabilidad
predicha como *offset* (observación O1) y la historia cortada se trata en el entrenamiento (observación
O2). Los dos ajustes quedaron como D43 y D44 el 26 de octubre, antes de modelar. Consideró que nada impide
seguir con la Etapa 3 del procedimiento (ingeniería de variables; actividad 3.1 de la Carta Gantt).

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

| Tema | Entrada | Definición |
|---|---|---|
| Unidad de reparto | D27 | El identificador de paciente: todos sus egresos van al mismo conjunto. Los dos bloques de identificador no se enlazan. |
| Estratificación, proporción y semilla | D28 | Uno de cada cinco identificadores va a prueba, dentro de estratos por bloque y por patrón de las cuatro variables objetivo. Semilla del proyecto: 2026. |
| Reserva | D29 | El conjunto de prueba queda en `data/reserva/`, como archivo de solo lectura y con su hash registrado. No se abre hasta la evaluación final. |
| Esquema de validación | D37 | Validación cruzada estratificada de cinco particiones, agrupada por paciente, dentro del conjunto de desarrollo; validación temporal interna; una sola evaluación final en el conjunto de prueba. |
| Validación temporal en tres grupos | D40 | Se informa con todos los casos de 2023 y 2024, solo con los de pacientes nuevos (sin ningún egreso en 2021 ni 2022) y solo con los de pacientes ya vistos. Los grupos quedan fijados en `validacion_temporal.parquet` (script 13). |
| Métricas | D41, D43 | Área bajo la curva de precisión y exhaustividad junto a la prevalencia, área bajo la curva ROC, puntaje de Brier junto al de referencia y calibración, con intervalos al 95 % por remuestreo de pacientes; recalibración de Platt si se equilibran las clases. La pendiente de calibración sale de una regresión logística sobre el logit de la probabilidad predicha, y el intercepto, de otra con ese logit como *offset* (D43). |
| Variables de historia (Etapa 3) | D42, D44 | Solo egresos anteriores al ingreso índice, en una ventana de 12 meses. Se marcan los casos cuya ventana empieza antes del inicio de su bloque (todo 2019 y todo 2021); la marca es una variable más del modelo, y una sensibilidad entrena solo con 2020 y 2022 (D44). |

---

### H19 · 2026-10-08 · Una persona puede tener un identificador en cada bloque
- **Actividad:** 2.3
- **Hallazgo:** Los identificadores del bloque A (2019–2020) y del bloque B (2021–2024) no se pueden vincular (H02 y D03 de `docs/bitacora.md`). Una persona hospitalizada en los dos períodos tiene dos identificadores, y una partición agrupada por identificador puede dejar sus egresos repartidos entre el conjunto de desarrollo y el de prueba.
- **Magnitud:** No se puede medir directamente. Como referencia, dentro del bloque B el 19,5 % de las personas con egresos en 2021–2022 vuelve a tener egresos en 2023–2024 (256.409 personas). Por analogía, del orden de una de cada cinco personas del bloque A estaría también en el bloque B, y con un reparto independiente el 32 % de ellas quedaría con egresos en los dos conjuntos: cerca del 6 % de las personas del bloque A.
- **No sirve enlazar por datos personales:** 530.172 combinaciones de sexo, fecha de nacimiento y comuna aparecen en los dos bloques, pero dentro del bloque B solo el 36,6 % de las coincidencias de ese tipo corresponde a la misma persona.
- **Consecuencia:** Es una limitación que se declara y no se corrige (D27). El identificador no es una variable del modelo, así que una persona repartida entre los dos conjuntos solo comparte sus características estables, como la edad, el sexo o sus diagnósticos crónicos.
- **Evidencia:** exploración del 6 de octubre de 2026 sobre la tabla etiquetada. Las personas y los egresos no cambiaron con las correcciones del 8 de octubre.

### D27 · 2026-10-08 · Unidad de reparto: el identificador de paciente, sin enlazar bloques
- **Actividad:** 2.3
- **Decisión:** La unidad que se reparte entre los dos conjuntos es el identificador de paciente (`ID_PACIENTE`). Todos los egresos de un identificador van al mismo conjunto, sean o no casos de estudio, porque los que no lo son sirven para calcular la historia de hospitalizaciones de la persona. Los identificadores de los bloques A y B no se enlazan.
- **Resultado:** Se reparten 4.035.768 identificadores. Los 3.915 que reúnen a más de una persona (D18), como una madre y su recién nacido, quedan enteros en un conjunto. Quedan fuera de los dos conjuntos los 20.345 egresos sin persona asignada (sin identificador o con identificador genérico), que no son casos de estudio.
- **Fundamento:** La propuesta de tesis indica que la partición agrupa por paciente y que todos los egresos de un mismo identificador quedan en uno solo de los dos conjuntos. El profesor guía pidió, en su revisión del 7 de octubre de 2026, agrupar por persona reconstruida de modo que ningún paciente esté en los dos conjuntos dentro de un mismo bloque, y no corregir el cambio de identificador con emparejamiento heurístico.
- **Alternativas descartadas:** (1) Repartir por `ID_PERSONA`: permitiría que dos personas de un mismo identificador quedaran en conjuntos distintos, y en esos identificadores la identidad es ambigua (H21 de la bitácora de la 2.2). (2) Unir los identificadores con la misma fecha de nacimiento y el mismo sexo, para mantener junta a una persona con un identificador en cada bloque: se ensayó el 6 de octubre de 2026 (76.183 unidades de reparto) y se descartó por ser un emparejamiento heurístico.
- **Limitación:** Una persona con un identificador en cada bloque puede quedar en los dos conjuntos (H19).
- **Consecuencia:** `ID_PACIENTE` es también el grupo que debe usar la validación cruzada agrupada dentro del conjunto de desarrollo (D37).
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026 a condición de incorporar los puntos 2.2 y 2.3 de su revisión (validación temporal en tres grupos; métricas y calibración), incorporados el 20 de octubre (D40 y D41).

### D28 · 2026-10-08 · Estratificación, proporción y semilla
- **Actividad:** 2.3
- **Decisión:** Uno de cada cinco identificadores va al conjunto de prueba (20 %) y el resto, al de desarrollo (80 %). Los identificadores se separan en 14 estratos: por bloque y por el patrón de sus cuatro variables objetivo, es decir, por las variables en las que alguno de sus casos de estudio tiene reingreso (seis patrones, más el de los identificadores sin casos de estudio). Dentro de cada estrato se ordenan por su número de casos de estudio con reingreso a 30 días por cualquier causa (`REING_30D`, la variable principal) y por su número de casos de estudio, y se toma uno de cada cinco. El punto de partida de cada estrato se sortea con la semilla del proyecto, 2026.
- **Por qué un patrón:** La partición es única y común a las cuatro definiciones. Estratificar por el patrón de las cuatro variables cuida la prevalencia de todas a la vez; la variable principal solo decide el orden dentro de cada estrato.
- **Detalle del patrón:** Un reingreso dentro de 7 días también lo es dentro de 30. Se cuenta así aunque la variable de 30 días no tenga dato por la censura (D30 de la bitácora de la 2.2).
- **Tamaño de los conjuntos:**

  |  | Desarrollo | Prueba | % en prueba |
  |---|---|---|---|
  | Identificadores de paciente | 3.228.615 | 807.153 | 20,00 % |
  | Personas | 3.231.777 | 807.922 | 20,00 % |
  | Egresos | 4.623.286 | 1.157.342 | 20,02 % |
  | Casos de estudio | 3.354.118 | 838.292 | 20,00 % |

- **Tasas de reingreso:** Porcentaje de los casos de estudio con seguimiento suficiente para cada variable.

  | Variable | Definición | Desarrollo | Prueba |
  |---|---|---|---|
  | `REING_7D` | 7 días, por cualquier causa | 2,066 % | 2,065 % |
  | `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 1,079 % | 1,073 % |
  | `REING_30D` | 30 días, por cualquier causa | 5,899 % | 5,897 % |
  | `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 3,030 % | 3,025 % |

- **Con la versión 2 del conjunto analítico (20 de octubre de 2026):** El reparto no cambió: cada identificador y cada egreso quedó en el mismo conjunto, porque los estratos y el orden dependen de los reingresos positivos, y los partos no tenían ninguno en las variables relacionadas. Esas dos variables ya no incluyen los partos (D38 de la bitácora de la 2.2): `REING_7D_CDM` tiene 1,265 % en desarrollo (2.861.785 casos con dato) y 1,257 % en prueba (715.458), y `REING_30D_CDM`, 3,553 % (2.798.814) y 3,546 % (699.646). Las de cualquier causa no cambian.
- **Composición:** La mayor diferencia entre las cuatro tasas es de 0,006 puntos porcentuales (0,008 con la versión 2). En la composición de los casos de estudio, la mayor diferencia entre los dos conjuntos es de 0,08 puntos en el año del alta, 0,08 en el hospital, 0,02 en el sexo, 0,07 en la edad, 0,06 en la CDM y 0,12 en el tipo de ingreso. La tasa a 30 días por año del alta es casi igual en los dos conjuntos (en 2024, 6,45 % en ambos).
- **Reproducibilidad:** Con la misma tabla y la misma semilla, la partición es siempre la misma. Un segundo programa, escrito de otra forma, vuelve a calcularla y asigna cada identificador al mismo conjunto. La lista de identificadores de cada conjunto queda guardada (D29).
- **Fundamento:** La propuesta pide una partición única, común a las cuatro definiciones, agrupada por paciente y estratificada por la variable objetivo, con prevalencias comparables y con una semilla fija. El profesor guía pidió preservar la prevalencia, definir la variable principal o usar una estratificación para varias etiquetas, y comprobar después la distribución por año, hospital, sexo, edad y CDM.
- **Parámetros:** `semilla` (2026), `prueba_una_de_cada` (5) y `variable_principal` (`REING_30D`).
- **Evidencia:** `2.3_validacion_particion/scripts/10_particionar.py` → `2.3_validacion_particion/reportes/10_particion.md`, secciones 2 a 5 y anexo.
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026 a condición de incorporar los puntos 2.2 y 2.3 de su revisión (validación temporal en tres grupos; métricas y calibración), incorporados el 20 de octubre (D40 y D41).

### D29 · 2026-10-08 · Reserva del conjunto de prueba
- **Actividad:** 2.3
- **Decisión:** El conjunto de prueba se guarda en `data/reserva/prueba.parquet`, separado de `data/processed/desarrollo.parquet`, como archivo de solo lectura. Las etapas siguientes (ingeniería de variables, filtro de dimensionalidad, entrenamiento, ajuste de hiperparámetros y extracción del subconjunto) leen solo `desarrollo.parquet`. El conjunto de prueba se usa una sola vez, en la evaluación final.
- **Sello:** El hash SHA-256 de los archivos queda registrado en `docs/version_particion.csv`. Versión 1, del 8 de octubre de 2026, sobre la versión 1 del conjunto analítico (D36 de la bitácora de la 2.2); conjunto de prueba, `8b568766715af5df011cffa05e07f35484c4ac0970c5ad3fcca4b92e00dd9a17`.
- **Versión 2 (vigente):** Del 20 de octubre de 2026, sobre la versión 2 del conjunto analítico (D38 de la bitácora de la 2.2). Conjunto de prueba, `3b34135288309a40463f23cd509b3d113f6a32c94c03a88a3bbbc6386338d2b2`; conjunto de desarrollo, `9546c8c7e80f634295e7c0538173661884aa6ce602e201a3cbd8ae615912abbb`. La lista de identificadores conserva el hash de la versión 1 (`5bdb99e4f7d9d9a7a9004545ce9e93c85fc172de6e93d2ff111577a42ac5f28b`): el reparto es idéntico y dentro de los archivos solo cambiaron las dos variables relacionadas de los partos. El conjunto de prueba no se abrió para nada más que regenerarlo. Antes de la evaluación final hay que comprobar que el archivo conserva el hash de la versión 2.
- **Contenido:** Los dos archivos tienen las 163 columnas del conjunto analítico, sin ningún cambio. `data/processed/particion.parquet` indica el conjunto de cada egreso y `data/processed/particion_identificadores.parquet`, el de cada identificador; ninguno de los dos contiene nada que dependa de las variables objetivo.
- **Antes de repartir:** El script comprueba que la tabla que lee sea la última versión registrada del conjunto analítico, y se detiene si no lo es.
- **Qué se miró del conjunto de prueba:** Solo las cifras agregadas necesarias para comprobar la partición (tamaño, tasas y composición), que están en el reporte 10.
- **Advertencia para la etapa siguiente:** `DIAS_REING` e `ID_EGRESO_REING` describen lo que ocurre después del alta y no son variables predictoras. Toda variable que cuente hospitalizaciones de una persona debe limitarse a las anteriores al alta del caso de estudio (H18 de la bitácora de la 2.2). **Precisada por D42:** a las anteriores al ingreso índice, en una ventana de 12 meses.
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026 a condición de incorporar los puntos 2.2 y 2.3 de su revisión (validación temporal en tres grupos; métricas y calibración), incorporados el 20 de octubre (D40 y D41).

### D37 · 2026-10-08 · Esquema de validación
- **Actividad:** 2.3
- **Decisión:** El ajuste y la comparación de modelos se hacen dentro del conjunto de desarrollo con validación cruzada estratificada de cinco particiones, agrupada por paciente: el grupo es `ID_PACIENTE`, de modo que ningún paciente esté a la vez en entrenamiento y en validación, y se estratifica por la variable objetivo de cada modelo. Todo preprocesamiento que dependa de los datos se ajusta dentro de cada partición y el desbalance se maneja solo sobre los datos de entrenamiento.
- **Validación temporal:** Se complementa con una validación temporal interna al conjunto de desarrollo: se reentrena con los casos de estudio de 2019 a 2022 (2.168.337) y se evalúa en los de 2023 y 2024 (1.185.781). Como sensibilidad se reporta el resultado sin 2020 ni 2021.
- **Evaluación final:** Fijados las variables, los hiperparámetros y el subconjunto seleccionado, los modelos se reajustan con todo el conjunto de desarrollo y se evalúan una sola vez en el conjunto de prueba.
- **Por qué no dejar uno fuera:** Con 3,35 millones de casos de estudio en desarrollo, la validación que deja un caso o un paciente fuera cada vez exigiría millones de ajustes. Cinco particiones agrupadas dan una estimación estable con un costo abordable.
- **Alcance de cada esquema:** La validación cruzada agrupada mide cómo generaliza el modelo a pacientes que no vio. La validación temporal mide cómo generaliza a un período posterior; en ella, un paciente del bloque B puede estar en los dos períodos.
- **Fundamento:** Es el esquema de la propuesta de tesis (etapas 4 y 7). El profesor guía pidió indicar la metodología y considerar una evaluación temporal complementaria, y la tasa de reingreso sube en 2023 y 2024 (H24 de la bitácora de la 2.2), de modo que una partición al azar no mide por sí sola el efecto de ese cambio.
- **Semilla:** Las particiones de la validación cruzada usan la semilla del proyecto, 2026.
- **Completada por:** D40 (la validación temporal se informa en tres grupos) y D41 (métricas, intervalos y recalibración).
- **Estado:** Adoptada. Aprobada por el profesor guía el 13 de octubre de 2026 a condición de incorporar los puntos 2.2 y 2.3 de su revisión (validación temporal en tres grupos; métricas y calibración), incorporados el 20 de octubre (D40 y D41).

### D40 · 2026-10-20 · La validación temporal se informa en tres grupos
- **Actividad:** 2.3
- **Decisión:** La validación temporal interna (D37) se informa de tres maneras: con todos los casos de estudio de evaluación (2023 y 2024), solo con los de pacientes nuevos, cuyo identificador no tiene ningún egreso en 2021 ni en 2022, y solo con los de pacientes ya vistos, que sí lo tienen. Cuenta cualquier egreso, sea o no caso de estudio (parámetro `paciente_visto_egresos` = TODOS). El script 13 deja los grupos fijados en `data/processed/validacion_temporal.parquet`, para que todos los modelos se evalúen con los mismos; lee solo el conjunto de desarrollo.
- **Fundamento:** Revisión del profesor guía del 13 de octubre de 2026 (punto 2.2). La validación cruzada agrupada por paciente mide el desempeño en pacientes que el modelo no vio. La temporal no: un paciente del bloque B con egresos en 2021 o 2022 y también en 2023 o 2024 está a la vez en el entrenamiento y en la evaluación. No es un error, porque al aplicar el modelo también llegarán pacientes que ya estuvieron hospitalizados, pero mezcla dos preguntas: como el reingreso depende mucho de cada paciente, en los ya vistos el desempeño será mejor por razones que no se trasladan a pacientes nuevos.
- **Resultado:**

  | Grupo (conjunto de desarrollo) | Casos de estudio | Pacientes | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|---|---|
  | Entrenamiento (2019–2022) | 2.168.337 | 1.732.822 | 2,00 % | 1,23 % | 5,69 % | 3,45 % |
  | Evaluación (2023–2024): todos los casos | 1.185.781 | 915.896 | 2,18 % | 1,32 % | 6,28 % | 3,74 % |
  | Evaluación: pacientes nuevos | 943.588 (79,6 %) | 758.487 | 1,96 % | 1,22 % | 5,42 % | 3,30 % |
  | Evaluación: pacientes ya vistos | 242.193 (20,4 %) | 157.409 | 3,05 % | 1,70 % | 9,65 % | 5,34 % |

- **Interpretación:** Los pacientes ya vistos reingresan casi el doble que los nuevos (9,65 % frente a 5,42 % a 30 días), así que el resultado de la validación temporal depende de cuántos haya: separarlos permite distinguir el desempeño en pacientes nuevos del desempeño en pacientes conocidos. En 2023 son el 22,6 % de los casos de evaluación y en 2024, el 18,1 %.
- **Alcance:** La separación vale dentro del bloque 2021–2024. Los egresos de 2019 y 2020 tienen otro identificador (H19): un paciente «nuevo» pudo estar hospitalizado en esos años, y los 1.093.656 casos de entrenamiento del bloque A no hacen visto a nadie.
- **Alternativa:** Contar solo los casos de estudio de 2021 y 2022 (`paciente_visto_egresos` = CASOS): serían 218.041 casos de pacientes ya vistos (18,4 %).
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 20 de octubre de 2026, por ser lo que indica la revisión.
- **Evidencia:** `2.3_validacion_particion/scripts/13_validacion_temporal.py` → `2.3_validacion_particion/reportes/13_validacion_temporal.md`; contraste independiente en `pruebas/verificar_13_validacion_temporal.py` (9 comprobaciones, sin fallas).
- **Estado:** Adoptada, por recomendación del profesor guía. Aprobada por el profesor guía el 24 de octubre de 2026: los tres grupos quedan fijados en un archivo común para todos los modelos y la limitación de los pacientes vistos en 2019 y 2020 con otro identificador está declarada.

### D41 · 2026-10-20 · Métricas de evaluación, intervalos y recalibración
- **Actividad:** 2.3
- **Decisión:** Las métricas se fijan antes de modelar, para cada una de las cuatro variables objetivo:
  - Área bajo la curva de precisión y exhaustividad, informada junto a la prevalencia, que es lo que obtiene un modelo al azar, y como cociente entre ambas.
  - Área bajo la curva ROC.
  - Puntaje de Brier, junto al de referencia: el que se obtiene al asignar a todos los casos la prevalencia, p(1 − p).
  - Calibración, con su intercepto (si el nivel general del riesgo es correcto; ideal 0) y su pendiente (si las probabilidades se separan en la medida justa; ideal 1), estimados con una regresión logística del resultado sobre el logit de la probabilidad predicha.
  - La exactitud no se usa: con tasas de 1 % a 6 %, un modelo que diga siempre «no reingresa» acierta más del 94 % de las veces.
- **Intervalos de confianza:** Al 95 %, por remuestreo de pacientes (`ID_PACIENTE`) con reposición: 1.000 repeticiones con la semilla del proyecto (2026) y los percentiles 2,5 y 97,5. Se remuestrean pacientes y no casos porque los casos de una misma persona no son independientes. Se calculan sobre las predicciones fuera de partición de la validación cruzada, sobre las de la validación temporal (en cada uno de sus tres grupos, D40) y sobre las del conjunto de prueba.
- **Recalibración:** Si al entrenar se equilibran las clases (submuestreo, sobremuestreo o pesos), las probabilidades quedan desplazadas hacia arriba y no se pueden leer como riesgo. Antes de evaluar la calibración se recalibran con el método de Platt (una regresión logística sobre el logit de la probabilidad), ajustada con datos que el modelo no usó para entrenar: en la validación cruzada, con una parte de las particiones de entrenamiento separada por paciente; para la evaluación final, con las predicciones fuera de partición del conjunto de desarrollo. Nunca con el conjunto de prueba. Las dos áreas no cambian con la recalibración, porque no cambia el orden de los casos.
- **Referencias en el conjunto de desarrollo:**

  | Variable | Prevalencia (área de precisión y exhaustividad de un modelo al azar) | Brier de referencia |
  |---|---|---|
  | `REING_7D` | 0,021 | 0,0202 |
  | `REING_7D_CDM` | 0,013 | 0,0125 |
  | `REING_30D` | 0,059 | 0,0555 |
  | `REING_30D_CDM` | 0,036 | 0,0343 |

- **Fundamento:** Revisión del profesor guía del 13 de octubre de 2026 (punto 2.3): con tasas tan bajas la exactitud no sirve y una sola métrica de discriminación no alcanza; la tasa sube en 2023 y 2024, así que un modelo entrenado con 2019–2022 tenderá a subestimar el riesgo en la validación temporal, lo que mide el intercepto; y equilibrar las clases desplaza las probabilidades. El profesor indicó las métricas, los intervalos por remuestreo de pacientes y la recalibración con datos de validación; las 1.000 repeticiones y el método de Platt son la forma concreta de aplicarlos.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 20 de octubre de 2026, por ser lo que indica la revisión.
- **Completa a:** D37. La revisión de la calidad del identificador por año que pide el mismo punto está en H28 de la bitácora de la 2.2.
- **Precisada por:** D43 (26 de octubre de 2026): el intercepto de calibración ya no se toma de la misma regresión que la pendiente, sino de una segunda regresión con el logit de la probabilidad predicha como *offset*. El resto de esta entrada no cambia.
- **Estado:** Adoptada, por recomendación del profesor guía. Aprobada por el profesor guía el 24 de octubre de 2026 con un ajuste en el intercepto de calibración (observación O1 de su revisión), incorporado en D43.

### D42 · 2026-10-20 · Variables de historia: solo el pasado, ventana de 12 meses y marca de ventana cortada
- **Actividad:** 2.3 (se aplica en la Etapa 3 del procedimiento de la propuesta, actividad 3.1 de la Carta Gantt)
- **Decisión:** Las variables que se construyan con la historia del paciente, como el número de hospitalizaciones previas que lista la propuesta, siguen tres reglas:
  - Solo usan egresos del mismo identificador de paciente cuya alta es anterior al ingreso índice: el ingreso que abre el episodio asistencial del caso de estudio. Nunca egresos posteriores, ni los tramos de traslado del propio episodio.
  - La ventana es de 12 meses antes del ingreso índice.
  - Se marcan los casos cuya ventana empieza antes del inicio de su bloque de identificador: los que tienen el ingreso índice antes del 1 de enero de 2020 en el bloque A, o antes del 1 de enero de 2022 en el bloque B. En ellos, un 0 puede significar falta de datos y no ausencia de hospitalizaciones. La marca no excluye casos.
- **Fundamento:** Revisión del profesor guía del 13 de octubre de 2026 (punto 2.5). Una variable de historia que usara egresos posteriores al ingreso le daría al modelo información del futuro. Además, la historia está cortada al comienzo de cada bloque: la base parte en 2019, y los egresos de 2019 y 2020 tienen otro identificador que los de 2021 en adelante (H19). Por eso, en el conjunto de desarrollo, el porcentaje de casos con alguna hospitalización en los 12 meses previos es de 5,9 % en enero de 2019 y de 25,9 % en diciembre de 2019; de 4,4 % en enero de 2021 y de 22,9 % en diciembre de 2021, y de 23 % a 28 % entre 2022 y 2024. Los pacientes no cambian: cambia lo que se puede ver.
- **Magnitud:** Con 12 meses quedan marcados 1.465.830 de los 4.192.410 casos de estudio (34,96 %) y 1.173.474 de los 3.354.118 del conjunto de desarrollo (34,99 %): todos los de 2019 y 2021, y cerca del 2 % de los de 2020 y 2022, cuyo episodio comenzó el año anterior. En 59.557 casos de estudio el ingreso índice es anterior al ingreso de su propio egreso, porque el episodio incluye un traslado.
- **Alternativa:** Una ventana de 6 meses marcaría cerca de la mitad de los casos de 2019 y de 2021 (17,6 % del total), pero miraría menos pasado. Se adopta la de 12 meses que sugiere el profesor guía; es también la de la variable de hospitalizaciones previas del puntaje HOSPITAL de predicción de reingreso.
- **Aplicación:** En la Etapa 3 (actividad 3.1), junto con las variables de historia. La marca depende solo de la fecha del ingreso índice y del bloque, así que no hace falta cambiar ahora el conjunto analítico ni el conjunto de prueba sellado.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 20 de octubre de 2026 («sí, hazlo como lo sugiere el profesor»).
- **Precisa a:** la advertencia de D29 y la de H18 de la bitácora de la 2.2, que hablaban de los egresos anteriores al alta.
- **Completada por:** D44 (26 de octubre de 2026): la marca de ventana cortada es además una variable del modelo, y una sensibilidad entrena solo con 2020 y 2022.
- **Estado:** Adoptada, por recomendación del profesor guía. Aprobada por el profesor guía el 24 de octubre de 2026 con un ajuste sobre la historia cortada en el entrenamiento (observación O2 de su revisión), incorporado en D44.

### D43 · 2026-10-26 · El intercepto de calibración se estima con el logit como offset
- **Actividad:** 2.3 (se aplica en cada evaluación de los modelos: validación cruzada, validación temporal y evaluación final)
- **Decisión:** La calibración se resume con dos números, cada uno estimado con su propia regresión logística sobre las predicciones que se evalúan (p̂ es la probabilidad predicha y logit(p̂) = ln(p̂ / (1 − p̂))):
  - **Pendiente** (ideal 1): regresión del resultado observado (0 o 1) sobre logit(p̂), con intercepto libre: logit P(reingreso) = a + b · logit(p̂). La pendiente es b. Menor que 1 indica predicciones demasiado extremas (el modelo exagera las diferencias entre pacientes); mayor que 1, demasiado tímidas.
  - **Intercepto** o calibración global (ideal 0): regresión con logit(p̂) como *offset*, es decir, con su coeficiente fijo en 1, y solo el intercepto libre: logit P(reingreso) = a + logit(p̂). El intercepto es a. Positivo indica que el modelo subestima el riesgo; negativo, que lo sobreestima.
  - Los intervalos de confianza de los dos números se calculan como los de las demás métricas (D41).
- **Fundamento:** Revisión del profesor guía del 24 de octubre de 2026 (observación O1), que cita a Van Calster, McLernon, van Smeden, Wynants y Steyerberg (2019), «Calibration: the Achilles heel of predictive analytics», *BMC Medicine*, 17, 230 (https://doi.org/10.1186/s12916-019-1466-7). En la regresión de la pendiente, a es el valor de la recta cuando logit(p̂) = 0, es decir, cuando el riesgo predicho es 50 %, muy lejos de los riesgos de esta base (prevalencias de 1,3 % a 5,9 % en desarrollo). Si la pendiente no es 1, ese a se mueve aunque el nivel general del riesgo sea correcto. Ejemplo: un modelo cuyo riesgo promedio coincide con la tasa observada, con logits en torno a −2,8 y pendiente 0,8, tendría a ≈ −2,8 − 0,8 × (−2,8) = −0,56, como si sobreestimara el riesgo; con el *offset*, a ≈ 0. Con el *offset*, a responde solo a cuánto hay que subir o bajar todas las predicciones para que su nivel coincida con lo observado.
- **Ejemplo con los datos:** Si un modelo entrenado con 2019–2022 asignara en la validación temporal un riesgo promedio igual a la tasa de `REING_30D` del entrenamiento (5,69 %), frente al 6,28 % observado en 2023–2024 (D40), el intercepto sería de alrededor de logit(0,0628) − logit(0,0569) ≈ +0,10: el modelo subestimaría el riesgo. Es una aproximación: el valor exacto depende de cómo se repartan las predicciones.
- **No cambia:** La recalibración de Platt (D41) sigue siendo una regresión logística sobre logit(p̂) con intercepto y pendiente libres: corrige las dos cosas a la vez y no es una medida de calibración.
- **Aplicación:** Todavía no hay código de evaluación. Al programarlo, la regresión con *offset* se puede ajustar, por ejemplo, con un modelo lineal generalizado de familia binomial que acepte un término *offset* (como `GLM` de statsmodels); la regresión logística de scikit-learn no lo admite.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 26 de octubre de 2026 («sí, haz los cuatro ajustes como los propones»).
- **Precisa a:** D41.
- **Estado:** Adoptada, por recomendación del profesor guía.

### D44 · 2026-10-26 · La historia cortada se trata en el entrenamiento: la marca entra al modelo y se agrega una sensibilidad
- **Actividad:** 2.3 (se aplica en la actividad 3.1, al crear la marca, y en las etapas de modelado)
- **Situación:** Con la ventana de 12 meses (D42), la historia cortada se concentra en el entrenamiento de la validación temporal. Casos de estudio del conjunto de desarrollo, por año del alta:

  | Período | Año | Casos de estudio | Con la ventana cortada |
  |---|---|---|---|
  | Entrenamiento | 2019 | 645.964 | 645.964 (100 %) |
  | Entrenamiento | 2020 | 447.692 | 9.346 (2,1 %) |
  | Entrenamiento | 2021 | 509.336 | 509.336 (100 %) |
  | Entrenamiento | 2022 | 565.345 | 8.820 (1,6 %) |
  | **Entrenamiento** | **2019–2022** | **2.168.337** | **1.173.466 (54,1 %)** |
  | **Evaluación** | **2023–2024** | **1.185.781** | **8 (0,0 %)** |

  En 2020 y 2022 solo quedan marcados los casos cuyo episodio comenzó el año anterior; los 8 de la evaluación son episodios que comenzaron antes de 2022 y terminaron en 2023.
- **Decisión:**
  1. La marca de ventana cortada se usa como una variable más del modelo, junto con las variables de historia. Así el modelo puede aprender que, en un caso marcado, «ninguna hospitalización previa» puede deberse a falta de datos.
  2. Sensibilidad: además del modelo principal, entrenado con 2019–2022, se entrena el mismo modelo solo con los casos de 2020 y 2022, cuya ventana está casi siempre completa (1.013.037 casos de desarrollo; 18.166 marcados, 1,8 %). Los dos se comparan en 2023–2024 con las métricas de D41 y D43, en los tres grupos de D40. Si el modelo de 2020 y 2022 se calibra mejor, la historia cortada está afectando al modelo principal.
- **Fundamento:** Revisión del profesor guía del 24 de octubre de 2026 (observación O2). El modelo principal aprende la relación entre la historia y el reingreso con historias incompletas y se evalúa con historias completas. Eso puede afectar más a la calibración (que el riesgo predicho sea correcto) que a la discriminación (que el modelo ordene bien a los pacientes, de mayor a menor riesgo).
- **Advertencia:** 2020 es el primer año de la pandemia: tiene menos casos (447.692 en desarrollo, frente a 645.964 en 2019) y otra mezcla, con más ingresos por urgencia y más fallecimientos (H11 de `docs/bitacora.md`). Una diferencia entre los dos modelos puede deberse también a eso, y se declara al informar la sensibilidad. En la evaluación la marca vale 0 en casi todos los casos: solo cambia lo que el modelo aprende al entrenar, y su efecto se mide con esta sensibilidad.
- **Aplicación:** La marca se crea en la actividad 3.1, como indica D42. Los años de la sensibilidad se fijarán como parámetro cuando se programe el entrenamiento, junto a `anios_entrenamiento_temporal`; ahora no cambia ningún archivo.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 26 de octubre de 2026 («sí, haz los cuatro ajustes como los propones»).
- **Completa a:** D42 y D40.
- **Estado:** Adoptada, por recomendación del profesor guía.

---

## Verificación del script 10

El script se ejecutó el 8 de octubre de 2026 sobre la versión 1 del conjunto analítico. Antes se había
probado completo con la salida en una carpeta temporal: los archivos definitivos tienen el mismo hash
que los de la prueba, lo que confirma además que la partición es reproducible.

El contraste independiente está en `2.3_validacion_particion/pruebas/verificar_10_particion.py` y deja
`reportes/pruebas_independientes.md`. Se cumplen sus 21 comprobaciones:

- Ningún identificador de paciente, persona ni egreso está en los dos conjuntos, y ningún identificador aparece en los dos bloques.
- Los dos archivos reúnen exactamente los 5.780.628 egresos con persona del conjunto analítico y sus 4.192.410 casos de estudio.
- Las 163 columnas de cada archivo son idénticas, celda a celda, a las del conjunto analítico.
- La partición se reproduce a partir de la semilla: el recálculo, hecho con otro programa, asigna los 4.035.768 identificadores al mismo conjunto.
- Los archivos tienen el hash registrado y el del conjunto de prueba es de solo lectura.
- Las tasas del reporte 10 coinciden con el recálculo.

El 20 de octubre de 2026 el script se volvió a ejecutar sobre la versión 2 del conjunto analítico.
Antes se guardó una copia de la lista de identificadores y del conjunto de cada egreso de la versión 1:
la comparación no encontró ningún identificador (de 4.035.768) ni ningún egreso (de 5.780.628) en un
conjunto distinto, y la lista de identificadores quedó con el mismo hash. El contraste independiente
volvió a cumplir sus 21 comprobaciones sobre la versión 2.

## Verificación del script 13

El script se ejecutó el 20 de octubre de 2026 sobre el conjunto de desarrollo de la versión 2 de la
partición, sin abrir el conjunto de prueba. El contraste independiente está en
`2.3_validacion_particion/pruebas/verificar_13_validacion_temporal.py` y deja
`reportes/pruebas_validacion_temporal.md`. Vuelve a calcular los grupos por otro camino (el año sale
de la fecha de alta y los pacientes ya vistos, de agrupar por identificador con pyarrow) y se cumplen
sus 9 comprobaciones: el archivo tiene exactamente los 3.354.118 casos de estudio de desarrollo, el
período y la marca de paciente ya visto coinciden caso por caso, el archivo no contiene nada que
dependa de las variables objetivo y la tabla del reporte 13 coincide con el recálculo.

---

## Pendientes

- [x] Presentar al profesor guía las decisiones D27 a D29 y D37. Las revisó el 13 de octubre de 2026 y las aprobó a condición de incorporar los puntos 2.2 y 2.3 de su revisión.
- [x] Punto 2.2 de la revisión: informar la validación temporal de tres maneras. Hecho el 20 de octubre de 2026 (D40, script 13).
- [x] Punto 2.3 de la revisión: fijar antes de modelar las métricas, los intervalos y la recalibración (D41) y revisar por año los identificadores faltantes o ambiguos (H28 de la bitácora de la 2.2). Hecho el 20 de octubre de 2026.
- [x] Presentar al profesor guía, en el próximo avance, D40 y D41. Las revisó el 24 de octubre de 2026: aprobó D40, y D41 con un ajuste en el intercepto de calibración (O1), incorporado en D43.
- [ ] En las etapas de modelado, evaluar con los grupos de `data/processed/validacion_temporal.parquet` y con las métricas de D41, con el intercepto de calibración de D43.
- [x] Punto 2.5 de la revisión: fijar la ventana de historia. Hecho el 20 de octubre de 2026: 12 meses (D42).
- [ ] En la Etapa 3 (actividad 3.1), construir las variables de historia y la marca de ventana cortada según D42, con la marca como variable del modelo (D44).
- [x] Presentar al profesor guía D42 en el próximo avance. La revisó el 24 de octubre de 2026 y la aprobó con un ajuste sobre la historia cortada en el entrenamiento (O2), incorporado en D44.
- [ ] En el modelado, entrenar también el modelo de sensibilidad con 2020 y 2022 y compararlo con el principal en 2023–2024 (D44).
- [ ] Presentar al profesor guía D43 y D44 en el próximo avance.
- [ ] Declarar en el informe la limitación descrita en H19.
- [ ] En las etapas siguientes, leer solo `desarrollo.parquet`, usar `ID_PACIENTE` como grupo de la validación cruzada y la semilla 2026.
- [ ] Antes de la evaluación final, comprobar el hash del conjunto de prueba con `pruebas/verificar_10_particion.py`.
