# Bitácora de la actividad 2.3: validación, partición y reserva del conjunto de prueba

Registro de los hallazgos y decisiones de la actividad 2.3 de la Carta Gantt. Continúa la numeración
de las bitácoras anteriores (`docs/bitacora.md` y `2.2_depuracion_etiquetado/bitacora.md`): aquí están
el hallazgo H19 y las decisiones D27 a D29 y D37. Una entrada no se borra: si una decisión cambia,
se agrega una nueva entrada que la reemplaza y se indica en el campo **Estado**.

Esta bitácora se reescribió el 8 de octubre de 2026. La versión del 6 de octubre no llegó a
presentarse y describía una partición que unía identificadores de paciente por fecha de nacimiento y
sexo; el profesor guía pidió, en su revisión del 7 de octubre, no enlazar pacientes entre los dos
sistemas de identificador sin una llave válida. Esa alternativa queda registrada como descartada en
D27. Los parámetros de la partición están en `reglas/parametros.csv`.

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
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

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

- **Composición:** La mayor diferencia entre las cuatro tasas es de 0,006 puntos porcentuales. En la composición de los casos de estudio, la mayor diferencia entre los dos conjuntos es de 0,08 puntos en el año del alta, 0,08 en el hospital, 0,02 en el sexo, 0,07 en la edad, 0,06 en la CDM y 0,12 en el tipo de ingreso. La tasa a 30 días por año del alta es casi igual en los dos conjuntos (en 2024, 6,45 % en ambos).
- **Reproducibilidad:** Con la misma tabla y la misma semilla, la partición es siempre la misma. Un segundo programa, escrito de otra forma, vuelve a calcularla y asigna cada identificador al mismo conjunto. La lista de identificadores de cada conjunto queda guardada (D29).
- **Fundamento:** La propuesta pide una partición única, común a las cuatro definiciones, agrupada por paciente y estratificada por la variable objetivo, con prevalencias comparables y con una semilla fija. El profesor guía pidió preservar la prevalencia, definir la variable principal o usar una estratificación para varias etiquetas, y comprobar después la distribución por año, hospital, sexo, edad y CDM.
- **Parámetros:** `semilla` (2026), `prueba_una_de_cada` (5) y `variable_principal` (`REING_30D`).
- **Evidencia:** `2.3_validacion_particion/scripts/10_particionar.py` → `2.3_validacion_particion/reportes/10_particion.md`, secciones 2 a 5 y anexo.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D29 · 2026-10-08 · Reserva del conjunto de prueba
- **Actividad:** 2.3
- **Decisión:** El conjunto de prueba se guarda en `data/reserva/prueba.parquet`, separado de `data/processed/desarrollo.parquet`, como archivo de solo lectura. Las etapas siguientes (ingeniería de variables, filtro de dimensionalidad, entrenamiento, ajuste de hiperparámetros y extracción del subconjunto) leen solo `desarrollo.parquet`. El conjunto de prueba se usa una sola vez, en la evaluación final.
- **Sello:** El hash SHA-256 de los archivos queda registrado en `docs/version_particion.csv`. Versión 1, del 8 de octubre de 2026, sobre la versión 1 del conjunto analítico (D36 de la bitácora de la 2.2); conjunto de prueba, `8b568766715af5df011cffa05e07f35484c4ac0970c5ad3fcca4b92e00dd9a17`. Antes de la evaluación final hay que comprobar que el archivo conserva ese hash.
- **Contenido:** Los dos archivos tienen las 163 columnas del conjunto analítico, sin ningún cambio. `data/processed/particion.parquet` indica el conjunto de cada egreso y `data/processed/particion_identificadores.parquet`, el de cada identificador; ninguno de los dos contiene nada que dependa de las variables objetivo.
- **Antes de repartir:** El script comprueba que la tabla que lee sea la última versión registrada del conjunto analítico, y se detiene si no lo es.
- **Qué se miró del conjunto de prueba:** Solo las cifras agregadas necesarias para comprobar la partición (tamaño, tasas y composición), que están en el reporte 10.
- **Advertencia para la etapa siguiente:** `DIAS_REING` e `ID_EGRESO_REING` describen lo que ocurre después del alta y no son variables predictoras. Toda variable que cuente hospitalizaciones de una persona debe limitarse a las anteriores al alta del caso de estudio (H18 de la bitácora de la 2.2).
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D37 · 2026-10-08 · Esquema de validación
- **Actividad:** 2.3
- **Decisión:** El ajuste y la comparación de modelos se hacen dentro del conjunto de desarrollo con validación cruzada estratificada de cinco particiones, agrupada por paciente: el grupo es `ID_PACIENTE`, de modo que ningún paciente esté a la vez en entrenamiento y en validación, y se estratifica por la variable objetivo de cada modelo. Todo preprocesamiento que dependa de los datos se ajusta dentro de cada partición y el desbalance se maneja solo sobre los datos de entrenamiento.
- **Validación temporal:** Se complementa con una validación temporal interna al conjunto de desarrollo: se reentrena con los casos de estudio de 2019 a 2022 (2.168.337) y se evalúa en los de 2023 y 2024 (1.185.781). Como sensibilidad se reporta el resultado sin 2020 ni 2021.
- **Evaluación final:** Fijados las variables, los hiperparámetros y el subconjunto seleccionado, los modelos se reajustan con todo el conjunto de desarrollo y se evalúan una sola vez en el conjunto de prueba.
- **Por qué no dejar uno fuera:** Con 3,35 millones de casos de estudio en desarrollo, la validación que deja un caso o un paciente fuera cada vez exigiría millones de ajustes. Cinco particiones agrupadas dan una estimación estable con un costo abordable.
- **Alcance de cada esquema:** La validación cruzada agrupada mide cómo generaliza el modelo a pacientes que no vio. La validación temporal mide cómo generaliza a un período posterior; en ella, un paciente del bloque B puede estar en los dos períodos.
- **Fundamento:** Es el esquema de la propuesta de tesis (etapas 4 y 7). El profesor guía pidió indicar la metodología y considerar una evaluación temporal complementaria, y la tasa de reingreso sube en 2023 y 2024 (H24 de la bitácora de la 2.2), de modo que una partición al azar no mide por sí sola el efecto de ese cambio.
- **Semilla:** Las particiones de la validación cruzada usan la semilla del proyecto, 2026.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

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

---

## Pendientes

- [ ] Presentar al profesor guía, el 9 de octubre de 2026, las decisiones D27 a D29 y D37.
- [ ] Declarar en el informe la limitación descrita en H19.
- [ ] En las etapas siguientes, leer solo `desarrollo.parquet`, usar `ID_PACIENTE` como grupo de la validación cruzada y la semilla 2026.
- [ ] Antes de la evaluación final, comprobar el hash del conjunto de prueba con `pruebas/verificar_10_particion.py`.
