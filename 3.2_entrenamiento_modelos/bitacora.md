# Bitácora de la actividad 3.2: entrenamiento de LR, RF y XGBoost con validación cruzada

Registro de los hallazgos y decisiones de la actividad 3.2 de la Carta Gantt («Entrenamiento LR, RF y XGBoost (CV)»), que corresponde a las Etapas 4 (esquema de partición y validación) y 5 (entrenamiento y comparación de modelos) del procedimiento de la propuesta. Continúa la numeración de las bitácoras anteriores (`docs/bitacora.md`, `2.2_depuracion_etiquetado/bitacora.md`, `2.3_validacion_particion/bitacora.md` y `3.1_filtro_dimensionalidad/bitacora.md`): aquí están las decisiones D58 a D65. Una entrada no se borra: si una decisión cambia, se agrega una nueva entrada que la reemplaza y se indica en el campo **Estado**.

Las decisiones D58 a D64 se tomaron el 7 y el 8 de noviembre de 2026, antes de escribir el código, una por una y con el visto bueno de la persona a cargo; D65, el 14 de noviembre, con el diagnóstico del servidor. Fijan dónde se entrena y cómo se prepara el servidor (D58 y D65), qué le toca a esta actividad y qué a las siguientes (D59), cómo entra cada variable a cada modelo (D60), cómo se trata el desbalance (D61), con qué hiperparámetros se entrena (D62), cómo se calculan las métricas (D63) y cómo se hacen y se juzgan las comparaciones que pidió el profesor guía en su revisión del 30 de octubre de 2026 (D64). Los modelos leen solo las tablas para los modelos de D57 (bitácora de la 3.1), que tienen solo el conjunto de desarrollo. El conjunto de prueba no se abre: se usa una sola vez, en la actividad 4.1. Los resultados se presentarán en el informe de avance 6, junto con D50 a D57, H34 y la respuesta a la observación O6.

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

| Tema | Entrada | Definición |
|---|---|---|
| Dónde se entrena | D58 | En el servidor del laboratorio SBCB de la UFRGS, entrando por RStudio Server, y no en el portátil. Se sube el código con `git clone` y las tres tablas para los modelos a mano; nunca el conjunto de prueba ni los archivos crudos de 2019. |
| Qué se hace en la 3.2 | D59 | Los tres modelos con las cuatro variables objetivo y los cinco pliegues, con hiperparámetros fijos; las métricas, la calibración por año en las predicciones fuera de pliegue y las comparaciones de listas y del hospital. El ajuste de hiperparámetros, el subconjunto y la importancia son de la 3.3; la validación temporal y sus sensibilidades, de la 4.1. |
| Cómo entra cada variable | D60 | Las categorías, como columnas sí/no (431). En la regresión logística, logaritmo en seis numéricas de cola larga, las 13 numéricas estandarizadas y las columnas sí/no divididas por su desviación típica; en los árboles, los valores tal cual. Todo se calcula con el entrenamiento de cada vuelta. |
| Desbalance | D61 | Un ensayo con y sin ponderación en `REING_7D_CDM`, antes de los demás entrenamientos. Un modelo se pondera solo si su AUPRC mejora más de un 10 % relativo, con todo el intervalo sobre ese margen; si se pondera, se recalibra con Platt. |
| Hiperparámetros de partida | D62 | Los valores por defecto de las bibliotecas, iguales en todas las comparaciones, con multa L1 en la regresión logística y un tamaño mínimo de 10 casos para dividir en Random Forest. |
| Métricas | D63 | Una sola cuenta con las predicciones fuera de pliegue de las cinco vueltas; la AUPRC como precisión promedio; los mismos 1.000 sorteos de pacientes para todos los modelos; la calibración programada con numpy. Se guardan las predicciones, no los modelos. |
| Comparaciones | D64 | 315 entrenamientos en un orden fijado. La lista A se compara con las otras tres con el margen del objetivo específico 3, mirando el intervalo completo: no pierde, no se puede afirmar o pierde. Sin hospital se informa la diferencia. |
| Entorno del servidor | D65 | Una carpeta propia (`~/Tesis_Javiera/`), Python 3.14.5 con conda, las bibliotecas con versiones exactas, los entrenamientos largos dentro de tmux y como máximo 32 procesadores mientras el profesor guía no indique otra cosa. |

---

### D58 · 2026-11-08 · Los modelos se entrenan en el servidor del laboratorio SBCB (UFRGS)
- **Actividad:** 3.2
- **Decisión:** Los modelos de la tesis se entrenan en el servidor del laboratorio SBCB de la UFRGS, al que la persona a cargo entra por el navegador con su sesión de RStudio Server. No se entrenan en el portátil.
- **Qué dice la propuesta:** En «Ambiente experimental», que el estudio se ejecuta en un computador portátil con Windows 11 y 16 GB de RAM. En «Software y hardware requerido» se detalla un procesador de cuatro núcleos y se advierte que ese equipamiento «es modesto frente al volumen de la base y constituye el principal riesgo de factibilidad».
- **Por qué:** La actividad tiene 315 entrenamientos (D64), cada uno con entre 2,2 y 2,7 millones de casos y hasta 7.631 columnas con la lista sin filtro (7.184 códigos de `REING_7D` más las 447 columnas de las 30 variables). Un Random Forest de ese tamaño puede necesitar varios GB de memoria y muchas horas de cálculo. El cambio afecta el costo de cómputo y no el diseño: los datos, el código, la semilla y las versiones de las bibliotecas son los mismos.
- **Cómo se entra:** Por RStudio Server, que es solo la puerta de entrada. Los scripts de Python se ejecutan desde su pestaña Terminal, una ventana de comandos en el servidor (no desde Console, que es para R), y las tablas se suben con el panel Files. Al principio se pensó entrar por el Jupyter del laboratorio, porque el código es Python, pero el 8 de noviembre de 2026 las credenciales no funcionaron ahí y sí en RStudio Server. El 14 de noviembre la persona a cargo informó que el profesor guía aprobó entrenar desde RStudio Server.
- **Qué se sube y qué no:** El código, con `git clone` desde GitHub. A mano, las tres tablas para los modelos de D57 (`modelos_casos.parquet`, `modelos_codigos.parquet` y `listas_codigos.parquet`, unos 190 MB), comprobando antes su hash con `docs/version_tablas_modelos.csv`. Nunca `data/reserva/prueba.parquet`, que se usa una sola vez, en la actividad 4.1, ni los archivos crudos de 2019, que contienen valores con forma de RUT.
- **Versiones:** Las de la propuesta: Python 3.14.5, pandas 3.0.3, scikit-learn 1.9.0, XGBoost 3.3.0 y shap 0.52.0, más pyarrow 25.0.1, que es la del entorno del proyecto. Las tres bibliotecas que el proyecto aún no tiene están disponibles en esas versiones (comprobado el 8 de noviembre de 2026). Hay que respetarlas porque entre versiones cambian a veces los valores por defecto de los modelos (D62), y el mismo código daría otro resultado.
- **Lo que falta saber del servidor:** Qué versión de Python y qué bibliotecas tiene, cuánta memoria, cuántos procesadores y si tiene tarjeta gráfica, el disco libre, si se puede instalar, si hay conexión a internet para `git clone` y con qué herramienta se deja corriendo un entrenamiento largo. Se averigua con un bloque de comandos que solo lee y no instala nada, para pegar en la Terminal de RStudio, probado en el portátil el 14 de noviembre de 2026. Reemplaza a la celda para Jupyter del 8 de noviembre.
- **Cómo se prueba el código:** El asistente no tiene acceso al servidor. Cada script se prueba antes en el portátil, con una muestra y en una carpeta temporal, junto con su prueba independiente, y la persona a cargo lo ejecuta en el servidor.
- **Visto bueno:** La persona a cargo de la tesis contó el 12 de octubre de 2026 que los modelos se entrenarían en ese servidor y pidió el 7 de noviembre registrarlo como decisión en esta bitácora, con la regla de qué se sube y qué no. El 14 de noviembre aprobó corregir esta entrada, antes de subirla a Git, para que diga que se entra por RStudio Server («Sí, corrígela»).
- **Completada por:** D65 (14 de noviembre de 2026): qué tiene el servidor, cómo se instalan las versiones y cómo se corren los entrenamientos largos sin depender de que el navegador quede abierto.
- **Estado:** Adoptada. El profesor guía aprobó entrenar desde RStudio Server (lo informó la persona a cargo el 14 de noviembre de 2026); el resto de la entrada, pendiente de validar con él.

### D59 · 2026-11-08 · Qué se hace en la actividad 3.2 y qué queda para la 3.3 y la 4.1
- **Actividad:** 3.2
- **Decisión:** La propuesta tiene dos numeraciones: las Etapas 1 a 8 del procedimiento y las actividades de la Carta Gantt (Anexo A). Las tres actividades que siguen se reparten las Etapas 4 a 7 así:

  | Actividad | Semanas | Etapas | Qué se hace |
  |---|---|---|---|
  | 3.2 Entrenamiento LR, RF y XGBoost (CV) | 9 a 11 | 4 y 5 | Para cada una de las cuatro variables de reingreso se entrenan la regresión logística con multa L1, Random Forest y XGBoost con la validación cruzada de cinco pliegues (D52 de la bitácora de la 2.3), con hiperparámetros fijos (D62). El desbalance y el preprocesamiento se ajustan solo con el entrenamiento de cada vuelta. Se comparan los modelos por AUPRC, AUROC, Brier y calibración, también por año en las predicciones fuera de pliegue (D56), y se comparan las listas de códigos y el modelo sin hospital (D64) |
  | 3.3 Hiperparámetros y extracción del subconjunto | 10 a 12 | 5 (optimización de los hiperparámetros) y 6 | Se ajustan los hiperparámetros con validación cruzada interna. Se ordenan las variables (coeficientes no nulos del LASSO e importancia por permutación en Random Forest y XGBoost), se elige el subconjunto y se comparan las cuatro definiciones (núcleo común y ampliado). Se comparan los subconjuntos con y sin hospital (D55) |
  | 4.1 Evaluación en conjunto de prueba y validación temporal | 12 y 13 | 7 y la validación temporal de la 4 | Se reajusta con todo el conjunto de desarrollo y se evalúa una sola vez en el conjunto de prueba. Se hace la validación temporal en sus tres grupos (D40), con los 7 hospitales sin casos antes de 2023 aparte (D55), la calibración de 2023 y 2024 (D56) y las dos sensibilidades por año: entrenar solo con 2020 y 2022 (D44) y excluir 2020 y 2021 (propuesta) |

- **Lo que otras entradas decían «en la 3.2»:** Cinco puntos se reparten así:

  | Entrada | Qué decía | Dónde queda |
  |---|---|---|
  | D55 (bitácora de la 3.1) | Entrenar con y sin `HOSPITAL`, comparando el subconjunto seleccionado en los dos | En la 3.2 se entrena con y sin hospital y se compara el desempeño (D64). Comparar los subconjuntos es de la 3.3, y los 7 hospitales nuevos, de la 4.1 |
  | D56 (bitácora de la 2.3) | La calibración por año se aplica en la actividad 3.2 | En la 3.2, cada año de 2019 a 2024 en las predicciones fuera de pliegue. La de 2023 y 2024 en la validación temporal es de la 4.1 |
  | D49 (bitácora de la 3.1) | Las variables parecidas se reparten la importancia al medirla en la actividad 3.2 | Medir la importancia es de la 3.3 (Etapa 6) y de la 4.2 (SHAP) |
  | D44 (bitácora de la 2.3) | Los años de la sensibilidad se fijan cuando se programe el entrenamiento | La sensibilidad es de la 4.1 |
  | Etapa 5 de la propuesta | Los hiperparámetros se optimizan mediante validación cruzada interna | En la 3.3. En la 3.2 se entrena con valores fijos, iguales en todas las comparaciones (D62) |

- **Las variables parecidas, para la 3.3:** Correlación de rangos en el conjunto de desarrollo (1 = siempre suben juntas; 0 = sin relación): `SEVERIDAD` y `RIESGO_MORTALIDAD`, 0,73; `HOSP_PREVIAS` y `HOSP_PREVIAS_NO_PLANIF`, 0,90; `HOSP_PREVIAS` y `DIAS_ULTIMA_HOSP`, −0,99. El servicio de ingreso es el mismo que el de alta en el 82,3 % de los casos.
- **Fundamento:** La Carta Gantt (Anexo A de la propuesta) y el texto de las Etapas 4 a 7. Se sigue el orden de la propuesta, sin adelantar pasos de otra actividad.
- **Visto bueno:** La persona a cargo de la tesis aprobó el reparto el 8 de noviembre de 2026 («Sí, de acuerdo»).
- **Precisa a:** D44 y D56 (bitácora de la 2.3) y D49 y D55 (bitácora de la 3.1), en la actividad a la que corresponde cada parte.
- **Evidencia:** exploración de solo lectura del 7 de noviembre de 2026 sobre `modelos_casos.parquet` (correlaciones).
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D60 · 2026-11-08 · Cómo entra cada variable a cada modelo
- **Actividad:** 3.2
- **Decisión:** Las 30 variables predictoras de D57 y los códigos de la lista elegida se convierten en una matriz de números así:

  | Columnas | Regresión logística | Random Forest y XGBoost |
  |---|---|---|
  | Las 14 categorías | Una columna sí/no por valor (431 columnas), dividida por su desviación típica, sin restar el promedio | Las mismas columnas sí/no, tal cual |
  | `ESTADIA`, `PESO_GRD`, `HOSP_PREVIAS`, `HOSP_PREVIAS_NO_PLANIF`, `CMA_PREVIAS` y `SESIONES_PREVIAS` | log(1 + x); luego se resta el promedio y se divide por la desviación típica | Tal cual |
  | Las otras 7 numéricas (`EDAD`, `INDICE_COMORBILIDAD`, `DIAS_ULTIMA_HOSP`, `N_DIAGNOSTICOS`, `N_PROCEDIMIENTOS`, `SEVERIDAD` y `RIESGO_MORTALIDAD`) | Se resta el promedio y se divide por la desviación típica | Tal cual |
  | `UCI_UTI`, `TRASLADO`, `VENTANA_CORTADA` y los códigos de la lista | Divididas por su desviación típica, sin restar el promedio | Tal cual (0 o 1) |
  | Faltantes | SIN DATO es un valor más de su categoría (D46). El único caso sin `PESO_GRD` recibe la mediana del entrenamiento | Igual |

- **Todo con el entrenamiento de cada vuelta:** El promedio, la desviación típica y la mediana se calculan solo con los casos de entrenamiento de cada vuelta y se aplican sin recalcular al pliegue que se valida, como pide la Etapa 4 («todo preprocesamiento dependiente de los datos se ajusta por partición»). El logaritmo no aprende nada de los datos.
- **Las categorías:** Cada valor es una columna que vale 1 si el caso lo tiene. Numerar los valores (1, 2, 3…) haría creer al modelo que el servicio 80 es «más» que el 3. Se conservan todos los valores, también SIN DATO, y en cada caso valen 1 exactamente 14 de las 431 columnas. Los tres modelos usan la misma matriz, para que vean lo mismo: XGBoost tiene una forma propia de leer categorías, pero no se usa. Cómo se suma la importancia de las columnas de una misma variable se decide en la 3.3.
- **Por qué el logaritmo:** La regresión logística multiplica cada número por un peso, así que supone que cada día de estadía suma lo mismo. Los datos no se comportan así: el reingreso a 30 días es 3,9 % con 1 o 2 días de estadía, 8,3 % con 7 a 14, 10,5 % con 30 a 89 y 11,0 % con un año o más. Además, `ESTADIA` tiene una mediana de 3 días y llega a 3.146 (367 casos de un año o más), y `SESIONES_PREVIAS` vale 0 en el 99,3 % de los casos y llega a 340 (24 casos, de 10 pacientes, con 50 o más). Con log(1 + x), 3 días pasan a 1,39, 8 a 2,20, 30 a 3,43 y 3.146 a 8,05, y el 0 sigue siendo 0. El índice de Moore no lleva logaritmo porque tiene valores negativos.
- **Por qué estandarizar:** El LASSO cobra una multa por el tamaño de los pesos, y sin una misma unidad cobraría distinto a una variable medida en días que a una medida en años. Ejemplo con el logaritmo de `ESTADIA` (promedio 1,62 y desviación típica 0,86 en todo el conjunto de desarrollo, solo para ilustrar): el caso `20230000956`, con 8 días, queda en 0,67; la estadía de 3.146 días, en 7,4, y sin el logaritmo quedaría en 224.
- **Por qué también las columnas sí/no:** Sin estandarizar, el LASSO castigaría por segunda vez a los códigos poco frecuentes, que la V ya castiga (H30). D61.3 (anemia aplástica: 149 casos y 35,6 % de reingreso a 30 días) tiene una desviación típica de 0,0067, y un código presente en el 30 % de los casos, de 0,458: para dejar entrar a D61.3, el LASSO le exigiría una V 68 veces más alta. Estandarizando, el primer criterio del LASSO para que entre un código es su correlación con el reingreso, que en una tabla de 2×2 es la V de Cramér del filtro de la 3.1. Es lo que hace por defecto glmnet (Friedman, Hastie y Tibshirani, 2010) y lo que recomendó Tibshirani (1997) para las variables sí/no.
- **Por qué sin restar el promedio:** Restar el promedio llenaría la matriz: con la lista sin filtro ocuparía unos 200 GB, en vez de unos 260 MB, y el LASSO haría unas 180 veces más cálculo. Dividir solo por la desviación típica da el mismo modelo, porque lo que el modelo usa es el salto de 0 a 1. Con N18.5 (en el 2,3 % de los casos, desviación típica 0,151), al estandarizar por completo un caso sin el código vale −0,15 y uno con el código, 6,49; al dividir solo, 0 y 6,64. El salto es 6,64 en los dos, y el corrimiento lo absorbe el intercepto, que no paga multa. Por eso se usa un método de cálculo que no le cobra multa al intercepto (saga, en scikit-learn).
- **Por qué los árboles van tal cual:** Un árbol pregunta, por ejemplo, «¿la estadía es de 15 días o más?», y para responder solo importa el orden de los valores: un valor extremo no lo afecta.
- **Alternativas descartadas:** (1) Un tope en el percentil 99,9: hay que calcularlo en cada vuelta y elegir arbitrariamente dónde cortar; el logaritmo hace un trabajo parecido sin eso. (2) Dejar los 0 y 1 como están y dividir los números por dos desviaciones típicas (Gelman, 2008): es válido, pero suma el castigo extra a los códigos poco frecuentes. (3) Numerar los valores de las categorías.
- **Referencias:** Tibshirani, R. (1997), *Statistics in Medicine*, 16(4), 385–395; Friedman, J., Hastie, T. y Tibshirani, R. (2010), *Journal of Statistical Software*, 33(1), 1–22; Gelman, A. (2008), *Statistics in Medicine*, 27(15), 2865–2873.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 8 de noviembre de 2026 («Sí, apruébala»). La estandarización de las columnas sí/no la pidió ella al revisar la primera versión, que las dejaba como 0 y 1 («si esto es necesario hay que hacerlo»).
- **Resuelve:** El pendiente de la bitácora de la 3.1 sobre cómo se codifican las categorías con cada modelo y si se transforman los números con valores extremos, como las sesiones previas.
- **Evidencia:** exploración de solo lectura del 7 y el 8 de noviembre de 2026 sobre `modelos_casos.parquet`.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D61 · 2026-11-08 · El desbalance: un ensayo con ponderación antes de los demás entrenamientos
- **Actividad:** 3.2
- **El desbalance:** En el entrenamiento de cada vuelta, por cada reingreso hay 16 casos sin reingreso en `REING_30D` (unos 154.500 reingresos), 27 en `REING_30D_CDM` (unos 79.400), 47 en `REING_7D` (unos 55.400) y 78 en `REING_7D_CDM` (unos 28.900). Los modelos dan una probabilidad y no un sí o un no, así que lo correcto es que la mayoría de las probabilidades sean bajas; la AUPRC y el AUROC miden si los que reingresan quedan más arriba en la fila. Aun en la variable más desbalanceada hay casi 29 mil reingresos para aprender.
- **Qué dice la propuesta:** Que el desbalance se maneja «mediante ponderación y métricas robustas», solo con los datos de entrenamiento (Etapa 4). Las métricas robustas ya están fijadas: la AUPRC junto a la prevalencia, sin la exactitud (D41).
- **El costo de ponderar:** Ponderar es contar cada reingreso como si estuviera repetido: en `REING_7D_CDM`, 78 veces. El modelo aprende entonces como si reingresar fuera tan común como no reingresar, y las probabilidades salen infladas: un paciente con el riesgo promedio (1,27 %) aparecería con 50 %, y uno con 5 %, con 80 %. Por eso D41 exige recalibrar con Platt usando casos que el modelo no usó al entrenar. En la validación cruzada hay que apartar una parte del entrenamiento: si se aparta uno de los cuatro pliegues, el modelo aprende con el 60 % de los casos en vez del 80 %.
- **La evidencia:** van den Goorbergh et al. (2022) encontraron que, en la regresión logística, corregir el desbalance no mejora el AUROC y deja las probabilidades muy infladas. La documentación de XGBoost recomienda ponderar cuando solo importa ordenar a los casos, y no hacerlo cuando importa la probabilidad. En la tesis importan las dos cosas: el orden (la AUPRC, criterio principal) y la probabilidad (la calibración de D41).
- **Decisión:** Se comprueba con los datos si la ponderación ayuda antes de aplicarla a los demás entrenamientos:

  | Paso | Qué se hace |
  |---|---|
  | Ensayo | Con `REING_7D_CDM` (78 a 1), donde más podría ayudar: lista A, los tres modelos y las cinco vueltas, con y sin ponderación. Son 15 entrenamientos más y van antes que todos los demás (D64). El peso de cada reingreso es el número de casos sin reingreso dividido por el de reingresos, en el entrenamiento de cada vuelta |
  | Regla, fijada antes de ver los resultados | Un modelo se entrena ponderado solo si su AUPRC con ponderación supera en más de un 10 % relativo a la sin ponderar, con todo el intervalo pareado sobre ese margen (D63 y D64). Por ejemplo, si sin ponderar diera 0,040, con ponderación tendría que pasar de 0,044 en todo el intervalo. Si no, ese modelo se entrena sin ponderar en las cuatro variables, y el resultado del ensayo se informa |
  | Si algún modelo se pondera | Se recalibra con Platt (D41), y en ese momento se define qué parte del entrenamiento se aparta para hacerlo |

- **En cualquier caso:** El peso se calcula solo con el entrenamiento de cada vuelta, y el pliegue que se valida nunca se toca (Etapa 4).
- **Alternativas descartadas:** (1) El submuestreo, que bota casos sin reingreso hasta equilibrar: con `REING_7D_CDM` habría que botar 77 de cada 78, información real. (2) El sobremuestreo o SMOTE, que repite reingresos o inventa casos parecidos: inventar casos con códigos sí/no no tiene sentido clínico, y además agranda los datos.
- **Referencias:** van den Goorbergh, R., van Smeden, M., Timmerman, D. y Van Calster, B. (2022), *Journal of the American Medical Informatics Association*, 29(9), 1525–1534; documentación de XGBoost, «Notes on Parameter Tuning» (datos desbalanceados).
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 8 de noviembre de 2026 («Sí, apruébala»). La exigencia de todo el intervalo se agregó al redactar esta entrada, para que la regla sea la misma de D64, y la aprobó el mismo día al revisar el borrador de esta bitácora («Sí, créala así»).
- **Completa a:** D41 (bitácora de la 2.3), en la recalibración.
- **Estado:** Adoptada. Pendiente de validar con profesor guía. El ensayo, pendiente.

### D62 · 2026-11-08 · Hiperparámetros de partida: los valores por defecto, con dos ajustes declarados
- **Actividad:** 3.2
- **Qué es un hiperparámetro:** Una perilla que se fija antes de entrenar y que el modelo no aprende solo: cuánta multa paga el LASSO, cuántos árboles tiene el bosque, qué tan grandes pueden ser.
- **Decisión:** En la 3.2 se entrena con valores fijos, decididos antes de ver resultados e iguales en todas las comparaciones (las cuatro listas, con y sin hospital, y el ensayo de la ponderación), para que una diferencia entre listas se deba a la lista y no a perillas mejor ajustadas. Son los valores por defecto de las bibliotecas, con dos ajustes:

  | Modelo | Perilla | Qué controla | Valor | De dónde sale |
  |---|---|---|---|---|
  | Regresión logística | Tipo de multa | Que sea la del LASSO, que puede dejar pesos en 0 | L1 | La propuesta |
  | Regresión logística | C | Lo contrario de la fuerza de la multa: con C grande, la multa es chica | 1 | Por defecto |
  | Regresión logística | Método de cálculo | Cómo se llega a la solución | saga, hasta converger | Ajuste 2 y D60 |
  | Random Forest | Número de árboles | Cuántos árboles se promedian | 100 | Por defecto |
  | Random Forest | Columnas por pregunta | Cuántas columnas, al azar, mira cada pregunta | La raíz cuadrada del total (29 de 871 con la lista A de `REING_30D`) | Por defecto |
  | Random Forest | Tamaño mínimo para dividir | Un grupo con menos casos ya no se divide | 10 | Ajuste 1 |
  | XGBoost | Número de árboles | Cuántos árboles se suman | 100 | Por defecto |
  | XGBoost | Tasa de aprendizaje | Qué parte del error corrige cada árbol nuevo | 0,3 | Por defecto |
  | XGBoost | Profundidad | Cuántas preguntas seguidas puede hacer cada árbol | 6 | Por defecto |
  | Los tres | Semilla | Todo lo que se sortea | 2026 | La propuesta |

- **Por qué los valores por defecto:** No hay que inventar números, cualquiera puede repetir el resultado con la misma versión y ningún resultado influye en cómo se eligieron. Random Forest es de los algoritmos que menos mejoran al ajustar sus perillas, y la regresión penalizada y XGBoost, de los que más (Probst, Boulesteix y Bischl, 2019): ese ajuste es de la 3.3 (D59). Los valores por defecto se confirmarán al instalar las versiones de la propuesta (D58).
- **Ajuste 1, el tamaño mínimo en Random Forest:** Por defecto, scikit-learn divide cada grupo hasta que quedan solo casos que reingresan o solo casos que no, y cada árbol vota 0 o 1. Con 100 árboles, la probabilidad de un caso solo podría ser 0,00; 0,01; 0,02…, y con tasas de 1 % a 6 % muchísimos casos quedarían empatados en 0,00 o 0,01, sin que la AUPRC pueda ordenarlos. Para estimar probabilidades, ranger, el programa de Random Forest más usado en R, no divide grupos de menos de 10 casos, y se usa ese valor. Además, los árboles quedan más chicos y el entrenamiento es más rápido.
- **Ajuste 2, que el LASSO llegue a su solución:** El LASSO se calcula por aproximaciones sucesivas: se le dan todas las pasadas que necesite y se informa si no converge. Si saga tarda demasiado, se usa otro método que da el mismo modelo y se deja anotado.
- **Con C = 1 la multa casi no pesa:** En scikit-learn el error se suma sobre todos los casos y la multa se cobra una vez, así que con 2,6 millones de casos casi ningún peso queda en 0. En la 3.2 está bien, porque se mide cuánto predice cada lista y no qué variables elige el LASSO. El valor de C que decide eso se busca en la 3.3; si el ajuste cambia mucho los resultados, la comparación de la lista A con la sin filtro se puede repetir con los valores ajustados.
- **Lo que depende del servidor:** Antes de lanzar todo se miden el tiempo y la memoria con un entrenamiento de prueba que incluye la lista sin filtro (D64). Si un valor no cabe, se cambia solo lo necesario y se anota con la medición. XGBoost puede usar el procesador o la tarjeta gráfica; los resultados son casi idénticos, pero no exactos, así que se usa la misma opción en todos los entrenamientos.
- **Referencia:** Probst, P., Boulesteix, A.-L. y Bischl, B. (2019), *Journal of Machine Learning Research*, 20(53), 1–32.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 8 de noviembre de 2026 («Sí, apruébala»).
- **Completada por:** D65 (14 de noviembre de 2026): cuántos procesadores usa cada entrenamiento y que la opción de procesador o tarjeta gráfica de XGBoost se decide con la prueba de tiempos.
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D63 · 2026-11-08 · Cómo se calculan las métricas en la validación cruzada
- **Actividad:** 3.2 (aplica D41, D43 y D56 de la bitácora de la 2.3; D56 responde a la observación O10 de la revisión del profesor guía del 30 de octubre de 2026)
- **Decisión:** Las métricas de D41, con el intercepto de D43 y la calibración por año de D56, se calculan así:

  | Punto | Cómo |
  |---|---|
  | Una sola cuenta | Se juntan las predicciones fuera de pliegue de las cinco vueltas (3.275.432 en `REING_30D`) y se calcula cada métrica una sola vez, como dice D41. Es también lo que necesita la calibración por año, porque cada año tiene casos en las cinco vueltas. Al lado se informan la AUPRC y el AUROC de cada vuelta |
  | AUPRC | Como precisión promedio: se ordena a los casos de mayor a menor riesgo y se promedia la precisión en cada reingreso encontrado. Es la función estándar de scikit-learn; unir los puntos de la curva con rectas infla el área (Davis y Goadrich, 2006) |
  | Intervalos | Los mismos 1.000 sorteos de pacientes, con la semilla 2026, para todos los modelos, todas las listas y con o sin hospital. Así dos configuraciones se comparan de a pares: en cada sorteo se calculan las dos con los mismos pacientes y se restan |
  | Calibración | El intercepto con offset y la pendiente (D43) se programan con numpy, por aproximaciones sucesivas (método de Newton), sin agregar statsmodels, que la propuesta no lista. La prueba independiente los comprueba por otro camino. Sus intervalos usan los mismos sorteos |
  | Qué se guarda | La predicción fuera de pliegue de cada caso, para cada combinación de variable, modelo, lista y con o sin hospital (unas 60, de unos 13 MB cada una). Los modelos entrenados no se guardan |

- **Ejemplo de la precisión promedio:** De 10 pacientes, 3 reingresan y quedan en los lugares 1, 3 y 6 de la fila. Las precisiones en esos lugares son 1 de 1, 2 de 3 y 3 de 6, y la AUPRC es (1,00 + 0,67 + 0,50) / 3 = 0,72, frente a una prevalencia de 0,30.
- **Por qué sorteos pareados:** Con un árbol de juguete de dos preguntas (¿hospitalización previa?, ¿estadía de 7 días o más?), evaluado con los pliegues y `REING_30D`, la AUPRC es 0,0977 (intervalo de 0,0968 a 0,0985), y la del árbol de una pregunta, 0,0832. La diferencia, 0,0144, tiene un intervalo de 0,0140 a 0,0149 con los mismos sorteos, y de 0,0132 a 0,0156, casi tres veces más ancho, con sorteos distintos para cada árbol. La suerte de cada sorteo afecta a los dos modelos y se cancela al restar.
- **Calibración por año:** Hay casos de sobra en todos los años: el grupo más chico es 2020 en `REING_7D_CDM`, con 4.707 reingresos entre 369.956 casos. En el árbol de juguete, todos los años juntos dan intercepto 0,00 y pendiente 1,00, pero 2024 da intercepto +0,05 (32.507 reingresos predichos frente a 34.120 observados) y 2020, pendiente 0,94 (el árbol separa a los grupos más de lo que se separaron ese año).
- **Por qué no se guardan los modelos:** Un Random Forest puede ocupar varios GB, y la 3.3 vuelve a entrenar con los hiperparámetros ajustados. Con las predicciones guardadas (menos de 1 GB en total) se calculan las métricas, los intervalos y las comparaciones sin volver a entrenar, y sirven para recalibrar en la evaluación final si algún modelo se pondera (D41). Además, permiten separar el trabajo en dos scripts: uno que entrena y guarda las predicciones, y otro que calcula las métricas.
- **Referencia:** Davis, J. y Goadrich, M. (2006), «The relationship between Precision-Recall and ROC curves», *Proceedings of the 23rd International Conference on Machine Learning*, 233–240.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 8 de noviembre de 2026 («Sí, apruébala»).
- **Precisa a:** D41, D43 y D56 (bitácora de la 2.3).
- **Evidencia:** exploración de solo lectura del 8 de noviembre de 2026 sobre `modelos_casos.parquet` (árboles de juguete, solo para ilustrar).
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D64 · 2026-11-08 · Las comparaciones que pidió el profesor guía: cuántas, en qué orden y cómo se juzgan
- **Actividad:** 3.2 (responde a las observaciones O5, O7 y O9 de la revisión del profesor guía del 30 de octubre de 2026)
- **Lo que ya estaba decidido:** Además de la lista A, la principal, los mismos modelos se entrenan con las listas C, agrupada y sin filtro (D53), y la lista A se entrena también sin `HOSPITAL` (D55). Cada vuelta usa la lista calculada sin su pliegue; la sin filtro es la misma en todas, porque no mira el reingreso. Todo lo demás queda igual (D60 a D63), así que si el resultado cambia es por la lista o por el hospital.

  | Lista | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
  |---|---|---|---|---|
  | A (principal) | 108 | 57 | 424 | 191 |
  | C | 849 | 629 | 1.595 | 1.165 |
  | Agrupada | 112 | 46 | 348 | 168 |
  | Sin filtro | 7.184 | 6.975 | 7.116 | 6.913 |

- **Cuántos entrenamientos y en qué orden:** Cada fila de 60 son 4 variables × 3 modelos × 5 vueltas. De los 30 entrenamientos del ensayo de la ponderación, los 15 de la versión que se elija para cada modelo son parte de la fila 2; por eso el ensayo suma solo 15.

  | Orden | Qué se entrena | Entrenamientos | Por qué |
  |---|---|---|---|
  | 1 | Ensayo de la ponderación (D61) | 15 más | Decidir primero si se pondera |
  | 2 | Lista A con hospital | 60 | Resultado principal |
  | 3 | Lista sin filtro | 60 | Saber si el filtro pierde algo (O7) |
  | 4 | Lista agrupada | 60 | La pidió el profesor guía (O7) |
  | 5 | Lista A sin hospital | 60 | D55 (O9) |
  | 6 | Lista C | 60 | Propuesta de H30 |
  | | Total | 315 | |

  Se hace todo, en ese orden. El orden solo importa si el servidor no alcanza: lo último quedaría pendiente, y se decidiría después de la prueba de tiempos (D62), dejándolo escrito. La lista sin filtro es la más pesada (con `REING_30D`, 7.563 columnas frente a 871 de la A), así que la prueba de tiempos incluye un entrenamiento con ella.
- **El criterio:** El del objetivo específico 3 de la propuesta: el modelo más chico no puede caer más de 0,02 en AUROC ni más de un 10 % relativo en AUPRC frente al más grande, y se tienen que cumplir los dos. La caída de AUROC se mide en puntos: si la lista sin filtro da 0,700, la A tiene que llegar al menos a 0,680. La de AUPRC se mide en proporción del valor del modelo más grande: si la sin filtro da 0,150, la A tiene que llegar al menos a 0,135. En la propuesta ese criterio es para el subconjunto de variables (actividades 3.3 y 4.1); D53 sugirió usarlo para juzgar el filtro, y esto no reemplaza esa evaluación.
- **Decisión:** La lista A se compara con cada una de las otras tres mirando el intervalo pareado completo (D63) de las dos caídas:

  | Veredicto | Cuándo | Qué pasa |
  |---|---|---|
  | No pierde | Todo el intervalo de las dos caídas queda dentro de su margen | La A sigue |
  | No se puede afirmar | El intervalo cruza algún margen | La A sigue, y se informa tal cual |
  | Pierde | Todo el intervalo pasa alguno de los dos márgenes | Se le presenta al profesor guía antes de la 3.3, con la propuesta de cambiar la lista en esa variable |

- **Detalle:** El veredicto se da por separado en cada variable y en cada modelo, 12 por comparación, porque la propuesta evalúa cada definición por separado. Otra lista «predice mejor» que la A solo si la A pierde frente a ella. H30 decía que si la C predice mejor se adopta la C, pero no cuánto mejor: con millones de casos, hasta una mejora de 0,001 tendría su intervalo sobre cero, y eso no justifica una lista con 4 a 11 veces más códigos. El cambio de lista nunca es automático, porque el profesor guía aprobó la A el 30 de octubre de 2026. Frente a la lista sin filtro, «pierde» querría decir que el filtro deja fuera información útil. El Brier y la calibración se informan en todas las comparaciones, pero el veredicto usa solo AUROC y AUPRC, como el criterio de la propuesta.
- **Ejemplo con árboles de juguete:** Con `REING_30D` y los pliegues, cada fila compara un árbol con otro que tiene una pregunta más; el más chico hace de lista A y el más grande, de lista sin filtro.

  | El árbol más chico no tiene… | Caída relativa de AUPRC | Caída de AUROC | Veredicto |
  |---|---|---|---|
  | «edad ≥ 50» (2 preguntas frente a 3) | 4,1 % (3,7 a 4,5) | 0,013 (0,012 a 0,013) | No pierde |
  | «índice de Moore ≥ 20» (2 preguntas frente a 3) | 10,2 % (9,7 a 10,6) | 0,015 (0,014 a 0,016) | No se puede afirmar |
  | «estadía ≥ 7» (1 pregunta frente a 2) | 14,8 % (14,4 a 15,2) | 0,044 (0,043 a 0,045) | Pierde |

  Mirando solo el valor central, la segunda fila perdería por 0,2 puntos, aunque con otros pacientes parecidos podría haber dado 9,7 %: el veredicto dependería de la suerte. Exigir el intervalo completo es la lógica de los estudios de no inferioridad (Piaggio et al., 2012) y cuesta poco: con millones de casos los intervalos son angostos, de menos de medio punto hacia cada lado en el ejemplo.
- **Sin hospital:** No decide nada en la 3.2, porque D55 ya dejó el hospital en el análisis principal: mide cuánto se apoya el modelo en él. Para cada variable y modelo se informan las métricas sin hospital y la diferencia pareada con su intervalo, con el veredicto anterior solo como información. En el ejemplo, el árbol de dos preguntas calculado dentro de cada uno de los 72 hospitales sube la AUPRC de 0,0977 a 0,1095: sin el hospital pierde un 10,8 % (10,3 a 11,4). En el conjunto de desarrollo, el reingreso a 30 días va de 3,16 % a 14,35 % según el hospital. Parte de esa información puede volver por otras variables, como la región o los servicios clínicos; eso se mira en la 3.3, al comparar las variables elegidas con y sin hospital (D55).
- **Referencia:** Piaggio, G., Elbourne, D. R., Pocock, S. J., Evans, S. J. W. y Altman, D. G. (2012), *JAMA*, 308(24), 2594–2604.
- **Visto bueno:** La persona a cargo de la tesis lo aprobó el 8 de noviembre de 2026 («Sí, apruébala»).
- **Completa a:** D53 y D55 (bitácora de la 3.1). Responde a la propuesta de H30.
- **Evidencia:** exploración de solo lectura del 8 de noviembre de 2026 sobre `modelos_casos.parquet` y `listas_codigos.parquet` (árboles de juguete, solo para ilustrar).
- **Estado:** Adoptada. Pendiente de validar con profesor guía.

### D65 · 2026-11-14 · El entorno del servidor: carpeta propia, Python 3.14.5 con conda y entrenamientos en tmux
- **Actividad:** 3.2
- **Lo que tiene el servidor:** Según el diagnóstico de solo lectura del 14 de noviembre de 2026, hecho en la Terminal de RStudio Server:

  | Qué | En el servidor |
  |---|---|
  | Procesadores | 64, con la carga casi nula (0,23) |
  | Memoria | 1.007 GB, de los que 986 GB están disponibles |
  | Tarjeta gráfica | NVIDIA RTX A6000 de 48 GB, sin uso |
  | Disco de la carpeta personal | 13 TB libres de 18 TB |
  | Python | 3.13.2 (de conda) y 3.12.3 (del sistema), sin ninguna biblioteca de modelos; no hay 3.14 |
  | Herramientas | git, curl, conda, tmux, screen, nohup y setsid |
  | Límites de los procesos | Ninguno de tiempo ni de memoria |
  | Internet | Responden PyPI y GitHub |

- **Decisión:** El servidor se prepara así:

  | Punto | Cómo |
  |---|---|
  | Carpeta propia | Todo va en `~/Tesis_Javiera/`: el código, las tablas, el entorno, los resultados y las descargas de conda. No se modifica nada fuera de ella. El nombre sigue el formato de las carpetas de otras tesis en la misma cuenta, a pedido de la persona a cargo |
  | Python 3.14.5 | Se instala con conda, desde el canal conda-forge, en un entorno dentro de la carpeta (`~/Tesis_Javiera/entorno`). No cambia el Python ni el conda que usan otras personas |
  | Bibliotecas | Con versiones exactas, desde PyPI (tabla siguiente) |
  | Código y tablas | El código, con `git clone` del repositorio, que es público, en `~/Tesis_Javiera/Codigo`. Las tres tablas de D57 se suben con Files → Upload a `~/Tesis_Javiera/Codigo/data/processed/`, comprobando su hash (D58) |
  | Entrenamientos largos | Dentro de tmux, una Terminal que sigue corriendo aunque se cierre el navegador o se corte la conexión. Cada script deja además un registro de su avance en un archivo |
  | Procesadores | Cada entrenamiento usa como máximo los que indique el profesor guía; mientras tanto, 32, la mitad. El número quedará como parámetro en `reglas/parametros.csv`, para cambiarlo sin tocar el código |

- **Versiones de las bibliotecas:**

  | Biblioteca | Versión | Por qué esa |
  |---|---|---|
  | numpy, pandas y pyarrow | 2.5.3, 3.0.3 y 25.0.1 | Las del entorno del proyecto, con el que se crearon las tablas |
  | scikit-learn y XGBoost | 1.9.0 y 3.3.0 | Las de la propuesta |
  | scipy | 1.18.1 | La piden scikit-learn y XGBoost |
  | joblib, threadpoolctl, narwhals y cloudpickle | 1.6.0, 3.7.0, 2.27.1 y 3.1.2 | Las piden scikit-learn y joblib |
  | python-dateutil y six | 2.9.0.post0 y 1.17.0 | Las pide pandas |
  | nvidia-nccl-cu12 | 2.32.3 | La pide XGBoost en Linux, para comunicar tarjetas gráficas |
  | shap | 0.52.0 | No se instala ahora: se usa en la actividad 4.2 |

  Cuando hay una versión más nueva, se eligió una publicada hace más de dos semanas: threadpoolctl 3.7.0 y no 3.8.0 (5 de noviembre), y nvidia-nccl-cu12 2.32.3 y no 2.32.6 (11 de noviembre). Todas tienen versión para Linux y Python 3.14 (comprobado en PyPI y conda-forge el 14 de noviembre de 2026). Se descargan unos 550 MB de PyPI, 335 de ellos de nvidia-nccl-cu12, más el Python de conda-forge (35 MB) y sus dependencias.
- **Por qué conda y no el Python que ya hay:** Ninguno de los dos es 3.14.5, y los usan otras personas: instalar bibliotecas ahí cambiaría su entorno. conda crea un entorno con la versión exacta dentro de una carpeta propia, sin permisos de administrador. Se usa solo el canal conda-forge.
- **La tarjeta gráfica:** XGBoost puede entrenar en la RTX A6000. Si se usa, es en todos los entrenamientos de XGBoost (D62); se decide con la prueba de tiempos.
- **Cuenta compartida:** Se entra con la cuenta del profesor guía, que también usa otra persona para su análisis, y en RStudio Server una cuenta tiene una sola sesión de R. Por eso se trabaja solo desde la Terminal, sin tocar Console, las pestañas abiertas ni el proyecto de esa persona. Se consultará al profesor guía si conviene una cuenta propia; si la hay, el plan es el mismo con otra carpeta.
- **Cómo se instala:** Con comandos preparados paso a paso. Antes de ejecutarlos se informa qué descarga cada uno y de dónde, y la instalación necesita el visto bueno de la persona a cargo. Al terminar se comprueban las versiones instaladas.
- **Instalación:** La persona a cargo la hizo el 14 de noviembre de 2026 en la Terminal de RStudio Server. Primero quedó en una carpeta `~/tesis_javiera` y después se rehízo en `~/Tesis_Javiera`: como un entorno de conda no se puede mover de carpeta sin que algunas partes sigan apuntando a la ubicación vieja, se creó de nuevo ahí, reutilizando las descargas de conda, y la carpeta antigua se borró al final, comprobando antes que no tuviera nada más. Resultado: Python 3.14.5, numpy 2.5.3, pandas 3.0.3, pyarrow 25.0.1, scipy 1.18.1, scikit-learn 1.9.0 y XGBoost 3.3.0, con soporte para la tarjeta gráfica; pip no encontró dependencias faltantes («No broken requirements found»). Se descargaron 48,5 MB de conda-forge y unos 573 MB de PyPI.
- **Visto bueno:** La persona a cargo de la tesis aprobó el plan el 14 de noviembre de 2026 («Sí, apruébalo»).
- **Completa a:** D58 y D62 (cuántos procesadores usa cada entrenamiento y la opción de procesador o tarjeta gráfica).
- **Evidencia:** diagnóstico del servidor del 14 de noviembre de 2026 (bloque de comandos de solo lectura en la Terminal de RStudio Server); versiones y tamaños, de PyPI y conda-forge.
- **Estado:** Adoptada. Instalación hecha y comprobada el 14 de noviembre de 2026. Pendiente de validar con profesor guía, sobre todo los procesadores y la cuenta.

---

## Pendientes

- En el servidor (D65): clonar el código en `~/Tesis_Javiera/Codigo` y subir las tablas, comprobando su hash. El entorno ya está instalado y comprobado.
- Consultar al profesor guía cuántos procesadores se pueden usar y si conviene una cuenta propia en el servidor (D65).
- Entorno de prueba en una carpeta temporal del portátil, con scikit-learn, scipy y XGBoost, sin tocar el `.venv` del proyecto (necesita el permiso de la persona a cargo).
- Script 17 (entrenamiento y predicciones fuera de pliegue) y, si conviene, un script 18 para las métricas (D63), cada uno con su prueba independiente, probada también con errores puestos a propósito.
- En el servidor: la prueba de tiempos y memoria (D62 y D64), el ensayo de la ponderación (D61) y los entrenamientos en el orden de D64.
- Confirmar los valores por defecto con las versiones instaladas (D62).
- Si algún modelo se pondera, definir qué parte del entrenamiento se aparta para la recalibración de Platt (D61).
- Informe de avance 6: los resultados de la 3.2, D50 a D57, H34, la respuesta a la O6 (cómo se separó el conjunto de prueba) y D58 a D65.
