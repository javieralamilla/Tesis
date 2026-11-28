# Bitácora de la actividad 3.2: entrenamiento de LR, RF y XGBoost con validación cruzada

Registro de los hallazgos y decisiones de la actividad 3.2 de la Carta Gantt («Entrenamiento LR, RF y XGBoost (CV)»), que corresponde a las Etapas 4 (esquema de partición y validación) y 5 (entrenamiento y comparación de modelos) del procedimiento de la propuesta. Continúa la numeración de las bitácoras anteriores (`docs/bitacora.md`, `2.2_depuracion_etiquetado/bitacora.md`, `2.3_validacion_particion/bitacora.md` y `3.1_filtro_dimensionalidad/bitacora.md`): aquí están las decisiones D58 a D68 y los hallazgos H35 a H44. Una entrada no se borra: si una decisión cambia, se agrega una nueva entrada que la reemplaza y se indica en el campo **Estado**.

Las decisiones D58 a D64 se tomaron el 7 y el 8 de noviembre de 2026, antes de escribir el código, una por una y con el visto bueno de la persona a cargo; D65, el 14 de noviembre, con el diagnóstico del servidor, y D66 y D67, el mismo día, con los scripts 17 y 18 escritos y probados. Fijan dónde se entrena y cómo se prepara el servidor (D58 y D65), qué le toca a esta actividad y qué a las siguientes (D59), cómo entra cada variable a cada modelo (D60), cómo se trata el desbalance (D61), con qué hiperparámetros se entrena (D62), cómo se calculan las métricas (D63), cómo se hacen y se juzgan las comparaciones que pidió el profesor guía en su revisión del 30 de octubre de 2026 (D64) y cómo se programan el entrenamiento (D66) y las métricas (D67). Los hallazgos H35 y H36 salieron al probar el script 17: cómo se pide la multa L1 en la versión de scikit-learn de la propuesta y por qué la regresión logística se calcula con liblinear. El hallazgo H37, del mismo día, es la prueba de tiempos en el servidor: cuánto tarda y cuánta memoria usa cada modelo, por qué XGBoost queda en el procesador y qué cambia con el número de procesadores. El hallazgo H38, del 16 de noviembre, es el resultado del ensayo de la ponderación: ningún modelo se pondera. H39 y H40, del 17 y el 18 de noviembre, son los resultados con la lista A y la primera comparación de listas, la A frente a la sin filtro. El 20 de noviembre se perdió el acceso al servidor, con las etapas agrupada, sin hospital y C todavía pendientes. D68, del 25 de noviembre, traslada el entrenamiento a bioserver5, del DIINF de la USACH, con el mismo entorno y 50 procesadores, y fija qué se vuelve a entrenar. H41, del 26 de noviembre, muestra que la repetición da exactamente los mismos resultados; H42 trae la calibración por año del alta y las métricas de cada vuelta; H43 y H44, del 26 y el 27, cierran las comparaciones de D64: la lista A no pierde frente a ninguna otra lista, y sin hospital el modelo pierde poco. Los modelos leen solo las tablas para los modelos de D57 (bitácora de la 3.1), que tienen solo el conjunto de desarrollo. El conjunto de prueba no se abre: se usa una sola vez, en la actividad 4.1. Los resultados se presentarán en el informe de avance 6, junto con D50 a D57, H34 y la respuesta a la observación O6.

**Tipos de entrada:** `H` = hallazgo (algo que se observó en los datos),
`D` = decisión (algo que se resolvió hacer).

**Estados:** *Adoptada* · *Pendiente de validar con profesor guía* · *Reemplazada por …*

---

## Resumen de las definiciones

| Tema | Entrada | Definición |
|---|---|---|
| Dónde se entrena | D58 | En el servidor del laboratorio SBCB de la UFRGS, entrando por RStudio Server, y no en el portátil. Se sube el código con `git clone` y las tres tablas para los modelos a mano; nunca el conjunto de prueba ni los archivos crudos de 2019. Hasta el 20 de noviembre de 2026; desde el 25, en bioserver5 (D68). |
| Qué se hace en la 3.2 | D59 | Los tres modelos con las cuatro variables objetivo y los cinco pliegues, con hiperparámetros fijos; las métricas, la calibración por año en las predicciones fuera de pliegue y las comparaciones de listas y del hospital. El ajuste de hiperparámetros, el subconjunto y la importancia son de la 3.3; la validación temporal y sus sensibilidades, de la 4.1. |
| Cómo entra cada variable | D60 | Las categorías, como columnas sí/no (431). En la regresión logística, logaritmo en seis numéricas de cola larga, las 13 numéricas estandarizadas y las columnas sí/no divididas por su desviación típica; en los árboles, los valores tal cual. Todo se calcula con el entrenamiento de cada vuelta. |
| Desbalance | D61 | Un ensayo con y sin ponderación en `REING_7D_CDM`, antes de los demás entrenamientos. Un modelo se pondera solo si su AUPRC mejora más de un 10 % relativo, con todo el intervalo sobre ese margen; si se pondera, se recalibra con Platt. |
| Hiperparámetros de partida | D62 | Los valores por defecto de las bibliotecas, iguales en todas las comparaciones, con multa L1 en la regresión logística y un tamaño mínimo de 10 casos para dividir en Random Forest. |
| Métricas | D63 | Una sola cuenta con las predicciones fuera de pliegue de las cinco vueltas; la AUPRC como precisión promedio; los mismos 1.000 sorteos de pacientes para todos los modelos; la calibración programada con numpy. Se guardan las predicciones, no los modelos. |
| Comparaciones | D64 | 315 entrenamientos en un orden fijado. La lista A se compara con las otras tres con el margen del objetivo específico 3, mirando el intervalo completo: no pierde, no se puede afirmar o pierde. Sin hospital se informa la diferencia. |
| Entorno del servidor | D65 | Una carpeta propia (`~/Tesis_Javiera/`), Python 3.14.5 con conda, las bibliotecas con versiones exactas, los entrenamientos largos dentro de tmux y como máximo 32 procesadores mientras el profesor guía no indique otra cosa. En bioserver5, 50 procesadores (D68). |
| Valores por defecto | H35 | Confirmados con scikit-learn 1.9.0 y XGBoost 3.3.0. La multa L1 se pide con `l1_ratio` = 1, porque `penalty` está obsoleto, y los valores de D62 se escriben explícitos en `reglas/parametros.csv`. |
| Método de cálculo de la regresión logística | H36 | liblinear, con `intercept_scaling` = 100, en vez de saga, que no llega a la solución con las columnas sí/no divididas por su desviación típica (D60). Da el mismo modelo. |
| Script 17 | D66 | Entrena por etapas, en el orden de D64, y guarda la predicción fuera de pliegue de cada caso, en una tabla por combinación (63). Comprueba la versión de las tablas, no repite lo ya guardado y verifica cada vuelta; su prueba independiente tiene 19 comprobaciones. |
| Script 18 | D67 | Calcula las métricas de D63 con 1.000 sorteos de pacientes, los mismos en todas las combinaciones, y da los veredictos del ensayo (D61) y de las comparaciones (D64). Para el logit de la calibración, un 0 exacto se cuenta como 0,0001; la caída se mide siempre desde la otra lista hacia la A. Su prueba independiente tiene 15 comprobaciones. |
| Tiempos y procesadores | H37 | Con la lista más pesada, una vuelta tarda 22,9 minutos con la regresión logística, 47,5 con Random Forest (32 procesadores) y 12 segundos con XGBoost, que queda en el procesador. El número de procesadores cambia solo el tiempo, no los modelos; se le preguntará al profesor guía si se pueden usar 40. |
| Ponderación | H38 | El ensayo no mejora la AUPRC de ningún modelo (−3,9 %, −13,3 % y −1,2 %) y empeora mucho la calibración: los tres modelos se entrenan sin ponderar y no hace falta la recalibración de Platt. |
| Resultado principal | H39 | Con la lista A, XGBoost tiene la AUPRC y el AUROC más altos en las cuatro variables (AUROC de 0,730 a 0,777). La regresión logística y XGBoost están calibrados; el Random Forest da predicciones demasiado extremas. |
| La A frente a la sin filtro | H40 | La lista A no pierde en ninguna de las 12 comparaciones: su AUPRC cae a lo más un 3,1 % y su AUROC, a lo más 0,010. |
| Servidor nuevo | D68 | Desde el 25 de noviembre de 2026, bioserver5, del DIINF de la USACH, por SSH: el entorno de D65, con conda instalado desde Miniforge, y 50 procesadores. Se vuelven a entrenar la lista A y el ensayo, porque lo del servidor de la UFRGS se perdió; la sin filtro no (H40). |
| Repetición | H41 | En bioserver5 los resultados de la lista A y del ensayo son idénticos, celda por celda, a los de H38 y H39. |
| Calibración por año | H42 | La pendiente de la regresión logística y de XGBoost queda cerca de 1 en los seis años; el intercepto va de −0,10 a +0,07. Las métricas de cada vuelta son parejas. |
| La A frente a la agrupada y la C | H43 | La lista A no pierde en ninguna de las 24 comparaciones; con H40, en ninguna de las 36. Sigue como la lista principal. |
| Sin hospital | H44 | Sin `HOSPITAL`, la AUPRC baja entre 0,5 % y 3,5 % y el AUROC, como mucho, 0,003. Se decide en la 3.3. |

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
- **Estado:** Adoptada. El profesor guía aprobó entrenar desde RStudio Server (lo informó la persona a cargo el 14 de noviembre de 2026); el resto de la entrada, pendiente de validar con él. Reemplazada en parte por D68 (25 de noviembre de 2026): desde el 20 de noviembre no hay acceso a ese servidor, y se entrena en bioserver5, del DIINF de la USACH, por SSH. Lo de qué se sube y qué no sigue vigente.

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
- **Precisada por:** D66 (14 de noviembre de 2026): la regresión logística se calcula con liblinear y no con saga, que no llega a la solución con estas columnas (H36). liblinear le cobra multa también al intercepto, pero con `intercept_scaling` = 100 esa multa deja de influir en las probabilidades. La forma de escalar las columnas no cambia.
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
- **Completada por:** H38 (16 de noviembre de 2026): el resultado del ensayo. Ponderar no mejora la AUPRC de ningún modelo, así que los tres se entrenan sin ponderar y no hace falta la recalibración de Platt.
- **Estado:** Adoptada. Pendiente de validar con profesor guía. El ensayo se hizo del 14 al 16 de noviembre de 2026 (H38).

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
- **Completada por:** D65 (14 de noviembre de 2026): cuántos procesadores usa cada entrenamiento y que la opción de procesador o tarjeta gráfica de XGBoost se decide con la prueba de tiempos. H35 (14 de noviembre de 2026): los valores por defecto, confirmados con las versiones instaladas.
- **Precisada por:** D66 (14 de noviembre de 2026): la regresión logística se calcula con liblinear, `intercept_scaling` = 100 y hasta 1.000 pasadas, como preveía el ajuste 2 (H36).
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
- **Precisada por:** D67 (14 de noviembre de 2026): cómo se programan los sorteos (el sorteo b sale solo de la semilla y de su número), la AUPRC con los empates contados juntos y la calibración por el método de Newton, y que para el logit de la calibración una probabilidad exactamente 0 o 1 se cuenta como 0,0001 o 0,9999.
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
- **Precisada por:** D67 (14 de noviembre de 2026): la caída se mide siempre desde la otra lista hacia la A, como proporción del valor de la otra lista, también frente a la agrupada, y el veredicto se lee en los extremos del intervalo.
- **Resultados:** H40 (18 de noviembre de 2026): la A no pierde frente a la sin filtro en las 12 comparaciones. H43 (27 de noviembre de 2026): tampoco frente a la agrupada ni la C, en las 24. H44 (26 de noviembre de 2026): sin hospital, la AUPRC baja entre 0,5 % y 3,5 %.
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
- **Completada por:** H37 (14 de noviembre de 2026): XGBoost queda en el procesador y se le preguntará al profesor guía si se pueden usar 40 procesadores.
- **Evidencia:** diagnóstico del servidor del 14 de noviembre de 2026 (bloque de comandos de solo lectura en la Terminal de RStudio Server); versiones y tamaños, de PyPI y conda-forge.
- **Estado:** Adoptada. Instalación hecha y comprobada el 14 de noviembre de 2026; el mismo día se clonó el código en `~/Tesis_Javiera/Codigo` (commit `a64bed4`) y se subieron las tres tablas a su `data/processed/`, con el hash igual al registrado. Pendiente de validar con profesor guía, sobre todo los procesadores y la cuenta. Reemplazada en parte por D68 (25 de noviembre de 2026): en bioserver5 se usan 50 procesadores y conda se instala desde Miniforge; el resto del entorno es el mismo.

### H35 · 2026-11-14 · En scikit-learn 1.9 la multa L1 se pide con l1_ratio = 1
- **Actividad:** 3.2
- **Hallazgo:** Al confirmar los valores por defecto de D62 con las versiones de la propuesta (scikit-learn 1.9.0 y XGBoost 3.3.0, las mismas que quedaron en el servidor, D65), se vio que el parámetro `penalty`, con el que se pedía la multa L1 de la regresión logística, está obsoleto desde scikit-learn 1.8 y desaparece en la 1.10. Si se usa `penalty='l1'`, la versión 1.9 avisa que el parámetro está obsoleto y que su valor no concuerda con el de `l1_ratio`, que por defecto es 0. La forma nueva es `l1_ratio`: 0 es la multa L2 y 1, la multa L1 (el LASSO). Se comprobó con datos de ejemplo que tenían 20 columnas sin ninguna relación con la respuesta: con `l1_ratio` = 1 quedan en cero 18 de sus 20 pesos, y con `l1_ratio` = 0, ninguno.
- **Valores por defecto confirmados:**

  | Modelo | Perilla | Por defecto | Se usa |
  |---|---|---|---|
  | Regresión logística | C | 1 | 1 |
  | Regresión logística | Tipo de multa (`l1_ratio`) | 0 (multa L2) | 1 (multa L1) |
  | Regresión logística | Método de cálculo | lbfgs, que no admite la multa L1 | liblinear (H36) |
  | Regresión logística | Escala del intercepto (`intercept_scaling`, solo en liblinear) | 1 | 100 (H36) |
  | Regresión logística | Pasadas máximas | 100 | 1.000 |
  | Regresión logística | Tolerancia | 0,0001 | 0,0001 |
  | Random Forest | Número de árboles | 100 | 100 |
  | Random Forest | Columnas por pregunta | La raíz cuadrada del total | La raíz cuadrada del total |
  | Random Forest | Tamaño mínimo para dividir | 2 | 10 (D62) |
  | Random Forest | Semilla | Ninguna | 2026 |
  | XGBoost | Número de árboles | 100 | 100 |
  | XGBoost | Tasa de aprendizaje | 0,3 | 0,3 |
  | XGBoost | Profundidad | 6 | 6 |
  | XGBoost | Método para buscar las preguntas | auto, que es hist | hist |
  | XGBoost | Procesador o tarjeta gráfica | Procesador | Procesador, mientras la prueba de tiempos no indique otra cosa (D65) |
  | XGBoost | Semilla | 0 | 2026 |

- **Consecuencia:** Los valores de D62 se escriben explícitos en `reglas/parametros.csv`, aunque coincidan con los de la biblioteca: si otra versión cambia un valor por defecto, como pasó con `penalty`, el modelo sigue siendo el mismo. El reporte del script 17 lista todos los valores de cada modelo, también los que no se escriben.
- **Evidencia:** entorno de prueba del 14 de noviembre de 2026 en una carpeta temporal del portátil (scikit-learn 1.9.0 y XGBoost 3.3.0 sobre Python 3.14.5), sin tocar el `.venv` del proyecto.
- **Resuelve:** El pendiente de D62 de confirmar los valores por defecto con las versiones instaladas.

### H36 · 2026-11-14 · saga no llega a la solución con las columnas sí/no divididas por su desviación típica; liblinear da el mismo modelo
- **Actividad:** 3.2
- **Hallazgo:** D60 divide cada columna sí/no por su desviación típica, y la de una columna con pocos casos es muy chica, así que su 1 queda muy grande. En la vuelta 1 de `REING_30D` con la lista A, con las tablas completas (2.620.256 casos de entrenamiento), 38 de las 857 columnas sí/no quedan con su 1 sobre 100. Las dos más raras llegan a 1.145 (el valor SIN DATO de `PUEBLO_ORIGINARIO`, que tienen 3 casos de desarrollo, todos de 2019, y 2 en el entrenamiento de esa vuelta) y a 809 (el valor OTRO de `TIPO_PROCEDENCIA`, con 4 casos, todos de 2020). saga, el método que eligió D60, avanza con un paso del mismo tamaño para todas las columnas, y ese tamaño lo fija el caso con los valores más grandes: basta un caso así para que todos los pasos sean diminutos y se necesiten miles de pasadas por los datos. liblinear avanza de a una columna, con un paso propio para cada una, y esos valores no lo frenan. Una vuelta de `REING_30D` con la lista A, en dos muestras de los pacientes:

  | Muestra | Método | Pasadas | Tiempo | ¿Llegó a la solución? |
  |---|---|---|---|---|
  | 2 % (52.738 casos de entrenamiento) | saga, hasta 1.000 pasadas | 1.000 | 3,2 minutos | No |
  | 2 % (52.738 casos de entrenamiento) | saga, hasta 3.000 pasadas | 2.771 | 5,9 minutos | Sí |
  | 2 % (52.738 casos de entrenamiento) | liblinear | 25 | 1,7 minutos | Sí |
  | 25 % (655.815 casos de entrenamiento) | saga, 10 pasadas | 10 | 3,8 segundos por pasada | No |
  | 25 % (655.815 casos de entrenamiento) | liblinear | 15 | 3,9 minutos | Sí |

  Con la muestra del 25 %, si saga necesitara las mismas 2.771 pasadas, una sola vuelta tardaría casi tres horas.
- **El mismo modelo:** En la muestra del 2 %, liblinear y saga (cuando llegó, con 2.771 pasadas) dan casi las mismas probabilidades: la diferencia promedio es 0,0002 y la más grande, 0,079. El AUROC es 0,7126 con liblinear y 0,7131 con saga, y la AUPRC, 0,1353 con los dos.
- **El intercepto:** liblinear le cobra multa también al intercepto, y por eso D60 había elegido saga. Con `intercept_scaling` = 100 esa multa es 100 veces más chica que la de un peso y deja de influir: con 100 y con 1.000 las probabilidades difieren en promedio 0,00003 (como máximo 0,0033). El valor del intercepto sí cambia (−1,87 y −2,92), porque cada caso tiene exactamente un 1 entre las columnas de cada categoría y lo que pierde el intercepto lo absorben esas columnas; las probabilidades, que es lo que se guarda, no cambian. La escala de las columnas de D60 queda igual: cambia solo el método de cálculo.
- **Con ponderación:** En la muestra, liblinear llegó a la solución en todas las vueltas: sin ponderar, en 24 a 58 pasadas (30 a 49 segundos); con ponderación, en 87 a 236 (3 a 8 minutos). En el ensayo de D61, la regresión logística ponderada tardará varias veces más que la sin ponderar.
- **Consecuencia:** La regresión logística se calcula con liblinear, `intercept_scaling` = 100 y hasta 1.000 pasadas (D66). Es lo que preveía el ajuste 2 de D62: «si saga tarda demasiado, se usa otro método que da el mismo modelo y se deja anotado».
- **Evidencia:** pruebas del 14 de noviembre de 2026 en la carpeta temporal del portátil, con muestras del 2 % y del 25 % de los pacientes de las tablas para los modelos (entorno de prueba de H35), y exploración de solo lectura de las tablas completas (columnas más raras de la vuelta 1).

### D66 · 2026-11-14 · El script 17: entrena los modelos y guarda las predicciones fuera de pliegue
- **Actividad:** 3.2
- **Decisión:** Los entrenamientos de D59 a D65 se programan en `scripts/17_entrenar_modelos.py`, con sus valores en `reglas/parametros.csv` y su prueba independiente en `pruebas/verificar_17_entrenamiento.py`. El script entrena y guarda la predicción fuera de pliegue de cada caso: la probabilidad que le da el modelo que no lo vio. No calcula métricas, que son del script 18 (D63).

  | Punto | Cómo |
  |---|---|
  | Qué lee | Las tres tablas de D57, solo si su hash es el de la última versión de `docs/version_tablas_modelos.csv`. También el papel de cada columna (`3.1_filtro_dimensionalidad/reglas/columnas_modelos.csv`) y la semilla y el número de pliegues (`2.3_validacion_particion/reglas/parametros.csv`) |
  | Etapas | Siete, en el orden de D64, y se elige cuál ejecutar: `tiempos`, `ensayo`, `base`, `sin_filtro`, `agrupada`, `sin_hospital` y `c`. Mientras `ensayo_resuelto` valga NO, solo se pueden ejecutar `tiempos` y `ensayo` |
  | Etapa de tiempos | Entrena solo la primera vuelta de cada modelo con `REING_30D` y la lista sin filtro, la más pesada, para medir el tiempo y la memoria; no guarda predicciones. Con esa medición, el reporte estima cuántas horas tomaría todo lo demás, como máximo |
  | Combinaciones | 63, de cinco vueltas cada una (315 entrenamientos): 6 en el ensayo (`REING_7D_CDM`, los tres modelos, con y sin ponderación), 9 en la etapa base (las otras tres variables con la lista A; la de `REING_7D_CDM` sale del ensayo) y 12 en cada una de las otras cuatro etapas |
  | Matriz de cada vuelta | Como D60, con la lista calculada sin el pliegue que se valida (la sin filtro es la de todo desarrollo; D53) y con las estadísticas sacadas solo del entrenamiento de la vuelta |
  | Modelos | Los valores de D62, escritos explícitos (H35), y la semilla 2026. La regresión logística, con liblinear, `intercept_scaling` = 100 y hasta 1.000 pasadas (H36); usa un procesador. Random Forest y XGBoost, con como máximo los procesadores del parámetro `procesadores` (32, D65) |
  | Ponderación | Si `ponderar_LR`, `ponderar_RF` o `ponderar_XGB` vale SI, el peso de cada reingreso es el número de casos sin reingreso dividido por el de reingresos, en el entrenamiento de la vuelta (D61) |
  | Predicciones | Una tabla por combinación en `data/processed/predicciones_3.2/` (fuera de Git), con `ID_EGRESO`, `PLIEGUE` y `PROBABILIDAD`. Dentro de la tabla quedan anotados la combinación, la semilla, el commit del código, la versión de las tablas y las de scikit-learn y XGBoost. Se escribe con otro nombre y se renombra al terminar, para que un corte no deje una tabla a medias |
  | Registro | `reportes/17_registro.csv`, una fila por vuelta: casos y reingresos del entrenamiento, casos de validación, columnas, códigos, peso de cada reingreso, segundos, memoria, pasadas y si la regresión logística llegó a la solución, avisos de las bibliotecas, commit del código y si los scripts o las reglas tenían cambios sin confirmar |
  | Reporte | `reportes/17_entrenamiento.md`: las verificaciones, la prueba de tiempos, las combinaciones guardadas y los valores completos de cada modelo |
  | Si se corta | Una combinación ya guardada no se repite: el mismo comando sigue con las que faltan |
  | Verificaciones | En cada vuelta, cinco: la lista es la de la vuelta; entrenamiento y validación no comparten casos ni pacientes; la matriz tiene las columnas esperadas; cada código vale 0 o 1, y las medianas, los promedios, las desviaciones y las proporciones salen solo del entrenamiento, recalculadas desde las tablas. En cada combinación, tres más: entran solo las predictoras (sin `HOSPITAL` cuando corresponde); cada caso tiene exactamente una probabilidad, y todas están entre 0 y 1 (estas dos, salvo en la etapa de tiempos, que no guarda). Si alguna falla, esa combinación no se guarda y el script se detiene |
  | Cómo se ejecuta | En el servidor, desde `~/Tesis_Javiera/Codigo`, con el Python del entorno de D65, dentro de tmux y con la etapa como argumento (`--etapa`). Se pueden limitar los modelos o las variables (`--modelos` y `--variables`) |

- **La prueba independiente:** Revisa por otro camino lo que deja el script, con 19 comprobaciones en cinco grupos: (1) la versión de las tablas, los valores de los parámetros y las columnas de cada tipo, contra una segunda transcripción escrita en la prueba; (2) que cada tabla de predicciones sea una de las 63 combinaciones, con la información guardada dentro que le corresponde, exactamente los casos con dato en su variable, su pliegue y probabilidades entre 0 y 1; (3) el registro, recontado desde las tablas, que la regresión logística haya llegado a la solución en todas las vueltas y que cada vuelta tenga su commit; (4) la matriz: en 200 casos al azar de cada vuelta, los códigos (con la receta del diccionario de D57), las categorías y los números transformados se vuelven a calcular con pandas y se comparan con los del script, igual que las proporciones del entrenamiento; (5) la primera vuelta de un XGBoost entrenada otra vez, que debe dar las mismas probabilidades guardadas, también con las respuestas de los casos de validación desordenadas, lo que muestra que el modelo nunca las miró. Termina con código 1 si alguna falla y deja `reportes/pruebas_entrenamiento.md`.
- **Cómo se probó:** En la carpeta temporal del portátil, con una muestra del 2 % de los pacientes (50.181 pacientes y 67.207 casos) y el entorno de prueba de H35:

  | Prueba | Resultado |
  |---|---|
  | Script 17 | Random Forest y XGBoost, en las siete etapas, con una variable en cada una; la regresión logística, en la etapa de tiempos (lista sin filtro, 7.560 columnas) y en el ensayo, con y sin ponderación. Se guardaron 16 combinaciones; sin hospital hay 72 columnas menos; la reanudación no repite lo guardado, y la etapa base no se deja ejecutar antes de resolver el ensayo |
  | Prueba independiente, con las salidas correctas | 19 de 19 |
  | Datos alterados a propósito: un pliegue cambiado, un caso quitado y un registro con la cuenta de códigos de la lista de todo desarrollo | Fallan exactamente las tres comprobaciones que corresponden |
  | Script cambiado para usar en cada vuelta la lista de todo desarrollo | Falla la comprobación de la lista, en 20 de las 25 vueltas revisadas (las otras 5 son de la lista sin filtro, que es la misma en todas), y las dos de volver a entrenar |
  | Script cambiado para entrenar también con los casos de validación | Fallan las dos comprobaciones de volver a entrenar |

- **Visto bueno:** La persona a cargo de la tesis aprobó el diseño el 14 de noviembre de 2026 («Sí, apruébalo») y, el mismo día, el cambio de saga a liblinear («Sí, apruébalo»). Se le explicaron los dos programas bloque por bloque, con el caso `20230000956` en la vuelta 4. También el 14 de noviembre aprobó crearlos en el proyecto, con esta entrada y con H35 y H36 («Sí, hazlo así»).
- **Precisa a:** D60 y D62, en el método de cálculo de la regresión logística (H36).
- **Estado:** Adoptada. Pendiente de validar con profesor guía. En el servidor se ejecutaron la etapa de tiempos el 14 de noviembre de 2026 (H37), el ensayo de la ponderación del 14 al 16 (H38), la etapa base el 16 y el 17 (H39) y la sin filtro el 17 y el 18 (H40). Las etapas agrupada, sin hospital y C quedan pendientes: el 20 de noviembre se perdió el acceso al servidor.

### D67 · 2026-11-14 · El script 18: las métricas con sus intervalos y los veredictos del ensayo y de las listas
- **Actividad:** 3.2
- **Decisión:** Las métricas de D63 y los veredictos de D61 y D64 se programan en `scripts/18_metricas.py`, con sus valores en `reglas/parametros.csv` (7 parámetros nuevos) y su prueba independiente en `pruebas/verificar_18_metricas.py`. El script lee las predicciones fuera de pliegue que guarda el script 17 (D66) y no entrena nada.

  | Punto | Cómo |
  |---|---|
  | Qué lee | Las tablas de predicciones del script 17 y, de `modelos_casos.parquet`, la respuesta, el paciente, el año del alta y el pliegue de cada caso, solo si las tablas para los modelos son la versión registrada (D57). Usa el script 17 para leer sus parámetros, la versión y los nombres de las combinaciones, así los dos scripts leen lo mismo. Nunca abre el conjunto de prueba |
  | Qué combinaciones | Mientras `ensayo_resuelto` valga NO, solo las 6 del ensayo; después, las 63 de D64. Si hay otra tabla de predicciones, se detiene |
  | Métricas | Las de D41 con el intercepto de D43: la prevalencia, la AUPRC como precisión promedio (D63), el AUROC, el Brier, el intercepto con el logit como offset y la pendiente, y el intercepto y la pendiente de cada año del alta (D56). Al lado, el cociente entre la AUPRC y la prevalencia, el Brier de referencia, la AUPRC y el AUROC de cada vuelta y, por año, el porcentaje observado y el predicho |
  | Sorteos | Los 2.509.082 pacientes de desarrollo se sortean con reposición, 1.000 veces. El sorteo b sale de `numpy.random.default_rng([2026, b])`, así que es el mismo en todas las combinaciones, se calcule donde se calcule. Cada caso cuenta tantas veces como salió su paciente. El intervalo son los percentiles 2,5 y 97,5 (D41) |
  | Cómo se calcula | La AUPRC y el AUROC con sumas acumuladas, ordenando los casos una sola vez y contando juntos los empates, como scikit-learn. La calibración, por el método de Newton, con pasos de a lo más 1 y los seis años a la vez; en cada sorteo parte del valor sin sorteo |
  | Comparaciones | De a pares, sorteo por sorteo con los mismos pacientes: el ensayo (mejora relativa de la AUPRC al ponderar), las listas (la A frente a la sin filtro, la agrupada y la C) y la A sin hospital frente a la A con hospital, solo para informar |
  | Qué deja | Una tabla por combinación en `data/processed/metricas_3.2/` (fuera de Git), con el valor sin sorteo y los de cada sorteo y lo que los produjo anotado adentro; `reportes/18_metricas.csv`, `reportes/18_comparaciones.csv` y el reporte `reportes/18_metricas.md`, que dice además qué fijar en `parametros.csv` después del ensayo |
  | Si se repite | No recalcula una combinación cuyas métricas salen de la misma tabla de predicciones (misma huella), del mismo script y con los mismos parámetros |
  | Dónde y cuánto | En el servidor, con hasta `procesadores` combinaciones a la vez (32, D65). Con el tamaño real, cada sorteo tarda unos 3,5 segundos (medido en el portátil con datos inventados de 3,3 millones de casos), casi una hora por combinación: cerca de una hora para el ensayo y unas dos horas para las 63, si cada procesador del servidor rinde como uno del portátil |
  | Verificaciones | En cada combinación, cuatro: la tabla de predicciones tiene exactamente los casos con dato en su variable, con su pliegue y probabilidades entre 0 y 1; lo anotado en ella coincide con su nombre, la semilla y la versión; sin sorteo, la AUPRC, el AUROC y el Brier coinciden con scikit-learn, y la calibración llegó a la solución en todos los sorteos. Además, que todas las combinaciones usen los mismos pacientes y sorteos, que cada comparación junte dos combinaciones con los mismos casos y, con el ensayo resuelto, que la ponderación fijada coincida con su veredicto. Si algo falla, esa combinación no se guarda y el script se detiene |

- **Las probabilidades 0 y 1 (decisión nueva):** La calibración usa el logit de cada probabilidad, ln(p / (1 − p)), que no existe para 0 ni para 1. La regresión logística y XGBoost no dan 0 (sus mínimos en la muestra del 2 %, con `REING_7D_CDM`, fueron 0,00000013 y 0,000029), pero Random Forest sí, cuando sus 100 árboles dejan al caso en hojas sin reingresos: en la muestra, con `REING_7D_CDM`, a 8.279 de 57.244 casos (14,5 %), de los que reingresaron 44 (0,53 %). Para el logit, un 0 exacto se cuenta como 0,0001 y un 1 exacto, como 0,9999; las demás probabilidades quedan tal cual, y la AUPRC, el AUROC y el Brier las usan sin cambios. 0,0001 es el valor redondo más grande que queda por debajo de la menor probabilidad positiva que puede dar un bosque de 100 árboles, cerca de 0,0004 (un árbol con un reingreso entre unos 25 casos de su hoja: 1/25 × 1/100, justo el mínimo de la muestra), así que un 0 sigue siendo el riesgo más bajo. El intercepto casi no depende de la regla, pero la pendiente sí, y por eso el reporte informa al lado cuántos casos tienen 0 y cuántos de ellos reingresaron. En la muestra:

  | Qué se hace con los 0 | Intercepto | Pendiente |
  |---|---|---|
  | Se cuentan como 10⁻¹⁵ | +0,006 | 0,04 |
  | Se cuentan como 0,000001 | +0,006 | 0,19 |
  | Se cuentan como 0,0001 (la regla) | +0,005 | 0,35 |
  | Se cuentan como 0,001 (quedan sobre riesgos positivos) | −0,007 | 0,48 |
  | Se dejan fuera | −0,064 | 0,50 |

  Dejarlos fuera esconde el problema y mueve el intercepto, como si el modelo sobreestimara el riesgo.
- **La dirección de las comparaciones (precisa a D64):** La caída se mide siempre desde la otra lista hacia la A: la del AUROC en puntos y la de la AUPRC como proporción del valor de la otra lista, también frente a la agrupada, que tiene menos códigos que la A en tres variables (46 frente a 57, 348 frente a 424 y 168 frente a 191). Así el veredicto responde siempre lo mismo: si la A predice peor que esa lista más allá del margen. Sin hospital se mide la caída de la A sin hospital frente a la A con hospital.
- **Los veredictos, con los extremos del intervalo:** D64 se aplica así: pierde si el extremo inferior de alguna de las dos caídas pasa su margen (0,02 o 10 %); no pierde si los extremos superiores de las dos quedan dentro; si no, no se puede afirmar. En el ensayo (D61), un modelo se pondera si el extremo inferior de la mejora pasa de 10 %.
- **La prueba independiente:** No usa funciones del script 18. Tiene 15 comprobaciones en seis grupos: (1) la versión de las tablas, y los parámetros del script 18 y la semilla, contra una segunda transcripción; (2) una tabla de métricas por cada tabla de predicciones, hecha con la que hay ahora (misma huella), con el valor sin sorteo y los 1.000 sorteos, sin vacíos; (3) sin sorteo, la AUPRC, el AUROC, el Brier y la prevalencia recalculados con scikit-learn, los casos con 0 recontados, y el intercepto y la pendiente, en general y de cada año, recalculados con scipy (el método de Brent y L-BFGS-B) y la regla de los 0 escrita de nuevo; (4) el primer y el último sorteo de cada combinación, rehechos desde cero con la receta escrita de nuevo, dan las métricas guardadas, lo que muestra también que todas usaron los mismos sorteos, y en una combinación de cada modelo se revisa además la calibración de cada año de esos sorteos; (5) cada fila de `18_metricas.csv`, recalculada desde las tablas de métricas (los percentiles con pandas) o desde las predicciones; (6) todas las comparaciones posibles, con sus valores, intervalos y veredictos recalculados con una segunda transcripción de D61 y D64. Termina con código 1 si alguna falla y deja `reportes/pruebas_metricas.md`.
- **Cómo se probó:** En la carpeta temporal del portátil, con la muestra del 2 % de los pacientes y las 16 tablas de predicciones que dejó con ella el borrador del script 17:

  | Prueba | Resultado |
  |---|---|
  | Script 18 | Las 16 combinaciones, con 1.000 sorteos, en 6,6 minutos con 4 procesos, y se cumplen todas sus verificaciones. Al ejecutarlo de nuevo no recalcula nada; con `ensayo_resuelto` = NO rechaza las 10 tablas que no son del ensayo, y con un caso de menos en una tabla de predicciones no guarda esa combinación y se detiene |
  | Prueba independiente, con las salidas correctas | 15 de 15 |
  | El script sortea con otra semilla en una combinación, sin anotarlo | Falla la comprobación de los sorteos rehechos |
  | La caída de AUPRC dividida por la AUPRC de la A, o la del AUROC al revés | Falla la comprobación de las comparaciones |
  | Los intervalos de la AUPRC con los percentiles 5 y 95 | Falla la comprobación del CSV de métricas |
  | La regla de los 0 con 0,000001 en un Random Forest, sin anotarlo | Fallan la calibración sin sorteo, la de cada año y los sorteos rehechos |
  | Una probabilidad cambiada después de calcular las métricas | Fallan la huella y otras cinco comprobaciones |

- **Visto bueno:** La persona a cargo de la tesis aprobó el diseño el 14 de noviembre de 2026 («Sí, apruébalo»), con las tres decisiones nuevas: la regla de los 0, la dirección de las comparaciones y que se calcule en el servidor con varias combinaciones a la vez. El mismo día se le explicaron el script y su prueba bloque por bloque, con las cifras de la muestra, y aprobó crearlos en el proyecto con esta entrada («Sí, créalo»).
- **Precisa a:** D41 y D43 (bitácora de la 2.3), en el logit de una probabilidad 0 o 1, y D63 y D64, en cómo se calculan las métricas, la dirección de las comparaciones y cómo se lee el veredicto.
- **Evidencia:** pruebas del 14 de noviembre de 2026 en la carpeta temporal del portátil, con la muestra del 2 % de los pacientes (entorno de prueba de H35); el tiempo, con datos inventados del tamaño de `REING_30D`.
- **Estado:** Adoptada. Pendiente de validar con profesor guía. En el servidor evaluó el ensayo el 16 de noviembre de 2026, en 42,6 minutos (H38); la etapa base el 17, en 55,1 minutos (H39), y la sin filtro el 18, en 51,9 minutos (H40). Las demás etapas, pendientes.

### H37 · 2026-11-14 · La prueba de tiempos en el servidor: el Random Forest es el más lento y XGBoost queda en el procesador
- **Actividad:** 3.2
- **Hallazgo:** La etapa de tiempos del script 17 (D66) se ejecutó en el servidor el 14 de noviembre de 2026, dentro de tmux, y tardó 74,2 minutos. Leyó las tablas en 123 segundos (3.347.652 casos y 59.214.795 pares caso–código) y entrenó con cada modelo la vuelta 1 de `REING_30D` con la lista sin filtro, la más pesada: 2.620.256 casos de entrenamiento y 7.563 columnas. Se cumplieron sus 18 verificaciones (6 por modelo, porque esta etapa no guarda predicciones) y ningún código de las listas quedó sin casos.

  | Modelo | Una vuelta | Pasadas | Memoria máxima | Procesadores |
  |---|---|---|---|---|
  | Regresión logística | 22,9 minutos (1.374,7 s) | 18 | 15,9 GB | 1 |
  | Random Forest | 47,5 minutos (2.847,1 s) | — | 19,1 GB | 32 |
  | XGBoost | 11,7 segundos | — | 19,1 GB | 32 |

  La memoria es la más alta que usó el proceso hasta ese momento, así que la de XGBoost repite la del Random Forest. El servidor tiene 1.007 GB (D65): la memoria no limita.
- **Cuánto tomaría todo:** El reporte del script 17 da como máximo 123,5 horas, una combinación tras otra (40,1 de la regresión logística, 83,0 del Random Forest y 0,3 de XGBoost), porque calcula como si los 105 entrenamientos de cada modelo usaran la lista sin filtro. Es una cota: solo la etapa sin filtro tiene ese tamaño, y tomaría unas 24 horas, 16 de ellas del Random Forest. Las demás listas son mucho más chicas: la vuelta 1 de `REING_30D` con la lista A tiene 870 columnas (H36), y la lista A de `REING_7D_CDM`, la del ensayo, 57 códigos, unas 500 columnas con las de las 30 variables. Un modelo ponderado puede tardar varias veces más (H36).
- **XGBoost en el procesador:** Con 12 segundos por vuelta, todos los entrenamientos de XGBoost suman menos de media hora, aun con la lista más pesada, así que la tarjeta gráfica no ahorraría nada que importe. `xgb_device` queda en cpu, como ya estaba en `reglas/parametros.csv`, y es la misma opción en todos los entrenamientos (D62). El ensayo de la ponderación (D61) se lanzó así el mismo 14 de noviembre, en la sesión de tmux `javiera_ensayo`.
- **El número de procesadores no cambia los modelos:** Se comprobó en el portátil con las mismas versiones del servidor (scikit-learn 1.9.0 y XGBoost 3.3.0), con datos inventados de la forma de los reales (40.000 casos, 13 columnas numéricas y 300 sí/no en una matriz dispersa, 4,06 % de positivos), los valores de D62 y la semilla 2026, sin ponderar y ponderados, con 1, 2, 4 y 8 procesadores:

  | Modelo | Resultado |
  |---|---|
  | XGBoost | Las mismas probabilidades, con todos sus decimales |
  | Random Forest | Los mismos 100 árboles. Las probabilidades difieren en menos de 10⁻¹⁵, porque el bosque suma los votos de sus árboles en el orden en que van terminando; el mismo bosque, predicho dos veces con 8 procesadores, también difiere así. La AUPRC y el AUROC coinciden en sus 15 decimales |

  Cambiar el parámetro `procesadores` cambia solo el tiempo. Las predicciones del Random Forest se reproducen con una diferencia menor que 10⁻¹⁵, no idénticas, también con 32 procesadores. La prueba independiente del script 17 vuelve a entrenar un XGBoost y acepta diferencias de hasta 10⁻¹² (D66), así que no le afecta.
- **Cuántos procesadores pedir:** El Random Forest arma cada árbol en un procesador y reparte los 100 entre los que tenga, así que su tiempo lo marca el número de rondas. La regresión logística usa uno solo y XGBoost tarda segundos: solo el Random Forest ganaría con más.

  | Procesadores | Rondas | Una vuelta del Random Forest con la lista sin filtro |
  |---|---|---|
  | 32 (ahora, D65) | 4 (32 + 32 + 32 + 4) | 47,5 minutos (medido) |
  | 34 a 49 | 3 | Unos 36 minutos (estimado) |
  | 50 a 64 | 2 | Unos 24 minutos (estimado) |

  La persona a cargo prefirió preguntarle al profesor guía si se pueden usar hasta 40 procesadores: son 3 rondas, un cuarto menos de tiempo (en la etapa sin filtro, de unas 16 a unas 12 horas de Random Forest), y quedan 24 libres para las demás personas del servidor. Si no, se sigue con 32. Si lo aprueba, se cambia solo el parámetro `procesadores`, después del ensayo y junto con la ponderación (D61).
- **Evidencia:** la salida de la etapa de tiempos (`~/Tesis_Javiera/salida_17_tiempos.txt`) y las secciones 1 y 2 de `reportes/17_entrenamiento.md` en el servidor, del 14 de noviembre de 2026; la prueba de los procesadores, el mismo día, en la carpeta temporal del portátil, con su Python 3.14.5 general, que tiene scikit-learn 1.9.0 y XGBoost 3.3.0, sin tocar el `.venv` del proyecto.
- **Visto bueno:** La persona a cargo de la tesis aprobó el 14 de noviembre de 2026 lanzar el ensayo con XGBoost en el procesador («Sí, lánzalo así») y, el mismo día, anotar esta entrada («sí, escríbela»), con su propuesta de pedir 40 procesadores en vez de 50 y de seguir con 32 si no se puede.
- **Resuelve:** Lo que D65 dejó para la prueba de tiempos: XGBoost no usa la tarjeta gráfica.

### H38 · 2026-11-16 · El ensayo de la ponderación: ningún modelo mejora su AUPRC al ponderar
- **Actividad:** 3.2
- **Hallazgo:** El ensayo de D61 se entrenó en el servidor del 14 al 16 de noviembre de 2026, con la etapa `ensayo` del script 17 dentro de tmux (2.894,9 minutos), y el script 18 lo evaluó el 16 de noviembre (42,6 minutos). Usa `REING_7D_CDM`, con 2.855.319 casos de desarrollo con dato, de los que reingresa el 1,27 %; la lista A con hospital, y las cinco vueltas. Ponderar no mejora la AUPRC de ningún modelo:

  | Modelo | AUPRC sin ponderar | AUPRC ponderada | Cambio relativo (intervalo pareado) | Veredicto |
  |---|---|---|---|---|
  | Regresión logística | 0,049 | 0,047 | −3,9 % (−4,5 % a −3,5 %) | No ponderar |
  | Random Forest | 0,057 | 0,049 | −13,3 % (−16,0 % a −10,8 %) | No ponderar |
  | XGBoost | 0,060 | 0,059 | −1,2 % (−3,5 % a 1,6 %) | No ponderar |

  La regla, fijada antes de ver los resultados, pedía una mejora de más de un 10 % en todo el intervalo. Ningún modelo se acerca: en la regresión logística y en el Random Forest todo el intervalo es una caída, y en XGBoost el cambio no se distingue de cero. Sin ponderar, la AUPRC de XGBoost es 4,7 veces la prevalencia; la del Random Forest, 4,5 veces, y la de la regresión logística, 3,8 veces.
- **Las probabilidades:** Ponderar las infla, como anticipaba D61:

  | Modelo | Brier sin / con ponderar (referencia 0,0125) | Intercepto sin / con | Pendiente sin / con | AUROC sin / con |
  |---|---|---|---|---|
  | Regresión logística | 0,0123 / 0,2031 | +0,001 / −4,375 | 0,98 / 0,92 | 0,740 / 0,741 |
  | Random Forest | 0,0123 / 0,0240 | −0,025 / −2,172 | 0,63 / 0,80 | 0,732 / 0,746 |
  | XGBoost | 0,0122 / 0,1803 | +0,005 / −4,249 | 0,95 / 0,99 | 0,767 / 0,763 |

  Cada reingreso pesa unos 78 casos, y las chances que da el modelo se multiplican por cerca de 78: el intercepto de la regresión ponderada, −4,375, es casi −ln(78) = −4,36. Un paciente con el riesgo promedio aparecería con un 50 %. Sin ponderar, la regresión logística y XGBoost quedan bien calibrados, con el intercepto cerca de 0 y la pendiente en 0,98 y 0,95.
- **El Random Forest:** Sin ponderar, da probabilidad 0 a 455.804 casos, de los que reingresan 1.221; como quedan empatados, no los puede ordenar entre sí. Ponderado, da 0 a 210.314, de los que reingresan 310. Por eso su AUROC sube al ponderar, de 0,732 a 0,746, aunque su AUPRC baje: ordena un poco mejor al conjunto, pero peor a los de más riesgo. Su pendiente sin ponderar, 0,63, dice que sus predicciones son demasiado extremas. Se informa (D63); los hiperparámetros se ajustan en la actividad 3.3.
- **Tiempos:**

  | Combinación | Tiempo de ajuste | Por vuelta |
  |---|---|---|
  | Regresión logística sin ponderar | 2 h 27 min | 17 a 36 min (24 a 34 pasadas) |
  | Regresión logística ponderada | 43 h 4 min | 3 h 18 min a 11 h 37 min (48 a 186 pasadas) |
  | Random Forest sin ponderar | 85 min | 15 a 19 min |
  | Random Forest ponderado | 68 min | 13 a 15 min |
  | XGBoost, sin ponderar y ponderado | Menos de 1 min cada uno | Unos 9 s |

  Ponderar hace 17,6 veces más lenta a la regresión logística: necesita más pasadas, y cada una tarda de 222 a 380 segundos, frente a 42 a 75 sin ponderar.
- **Verificaciones:**

  | Qué | Resultado |
  |---|---|
  | Script 17 | Las 48 verificaciones de las 6 combinaciones, 8 en cada una |
  | Registro del script 17 | La regresión logística llegó a la solución en sus 10 vueltas, sin avisos. Los casos y los reingresos de entrenamiento y el peso de cada reingreso (77,898 a 78,074) coinciden con los recalculados en el portátil |
  | Script 18 | Sus 7 verificaciones, entre ellas que las áreas y el Brier coinciden con scikit-learn y que la calibración llegó a la solución en los 1.000 sorteos |
  | Prueba independiente del script 17 | 19 de 19 (189 s) |
  | Prueba independiente del script 18 | 15 de 15 (122 s) |

- **Consecuencia:** Los tres modelos se entrenan sin ponderar en las cuatro variables (D61). `ponderar_LR`, `ponderar_RF` y `ponderar_XGB` quedan en NO, como estaban, y `ensayo_resuelto` pasa a SI en `reglas/parametros.csv`, lo que habilita las demás etapas. No hace falta la recalibración de Platt. Las tres combinaciones sin ponderar del ensayo son el resultado de `REING_7D_CDM` con la lista A (D64); las ponderadas quedan guardadas solo como parte del ensayo.
- **Evidencia:** en el servidor, la salida del ensayo (`~/Tesis_Javiera/salida_17_ensayo.txt`), `reportes/17_registro.csv`, `reportes/17_entrenamiento.md`, `reportes/18_metricas.md` y los reportes de las dos pruebas (`reportes/pruebas_entrenamiento.md` y `reportes/pruebas_metricas.md`), del 14 al 16 de noviembre de 2026; en el portátil, un contraste de solo lectura de los casos, las columnas y los pesos de cada vuelta.
- **Visto bueno:** La persona a cargo de la tesis aprobó el 16 de noviembre de 2026 anotar esta entrada y fijar `ensayo_resuelto` = SI («Sí, hazlo»), una vez pasadas las dos pruebas.
- **Resuelve:** El ensayo de D61.

### H39 · 2026-11-17 · Resultados con la lista A: XGBoost queda arriba en las cuatro variables, y la regresión logística y XGBoost están calibrados
- **Actividad:** 3.2
- **Hallazgo:** La etapa base de D64 se entrenó en el servidor el 16 y el 17 de noviembre de 2026 (script 17, 704,7 minutos, 9 combinaciones), y el script 18 la evaluó el 17 (55,1 minutos). Junto con las tres combinaciones sin ponderar del ensayo (H38), completa las 12 del resultado principal: las cuatro variables y los tres modelos, con la lista A, con hospital y sin ponderar. Discriminación, con el intervalo de los 1.000 sorteos de pacientes:

  | Variable | Casos | Prevalencia | Modelo | AUPRC (intervalo) | Veces la prevalencia | AUROC (intervalo) |
  |---|---|---|---|---|---|---|
  | `REING_7D` | 3.347.652 | 2,07 % | Regresión logística | 0,058 (0,057 a 0,060) | 2,81 | 0,713 (0,711 a 0,715) |
  | `REING_7D` | 3.347.652 | 2,07 % | Random Forest | 0,064 (0,062 a 0,066) | 3,09 | 0,706 (0,704 a 0,708) |
  | `REING_7D` | 3.347.652 | 2,07 % | XGBoost | 0,068 (0,066 a 0,070) | 3,28 | 0,730 (0,728 a 0,732) |
  | `REING_7D_CDM` | 2.855.319 | 1,27 % | Regresión logística | 0,049 (0,047 a 0,051) | 3,84 | 0,740 (0,737 a 0,743) |
  | `REING_7D_CDM` | 2.855.319 | 1,27 % | Random Forest | 0,057 (0,054 a 0,060) | 4,51 | 0,732 (0,729 a 0,735) |
  | `REING_7D_CDM` | 2.855.319 | 1,27 % | XGBoost | 0,060 (0,057 a 0,062) | 4,71 | 0,767 (0,765 a 0,770) |
  | `REING_30D` | 3.275.432 | 5,90 % | Regresión logística | 0,169 (0,167 a 0,171) | 2,86 | 0,749 (0,748 a 0,750) |
  | `REING_30D` | 3.275.432 | 5,90 % | Random Forest | 0,178 (0,176 a 0,181) | 3,02 | 0,750 (0,749 a 0,751) |
  | `REING_30D` | 3.275.432 | 5,90 % | XGBoost | 0,181 (0,179 a 0,184) | 3,07 | 0,757 (0,756 a 0,759) |
  | `REING_30D_CDM` | 2.792.482 | 3,55 % | Regresión logística | 0,122 (0,120 a 0,124) | 3,43 | 0,758 (0,756 a 0,760) |
  | `REING_30D_CDM` | 2.792.482 | 3,55 % | Random Forest | 0,133 (0,130 a 0,136) | 3,75 | 0,761 (0,759 a 0,763) |
  | `REING_30D_CDM` | 2.792.482 | 3,55 % | XGBoost | 0,136 (0,133 a 0,139) | 3,83 | 0,777 (0,775 a 0,779) |

- **Calibración:** El Brier de referencia es el de darle a todos la prevalencia; el intercepto ideal es 0 y la pendiente ideal, 1 (D43).

  | Variable | Modelo | Brier (referencia) | Intercepto (intervalo) | Pendiente (intervalo) | Casos con probabilidad 0 (reingresan) |
  |---|---|---|---|---|---|
  | `REING_7D` | Regresión logística | 0,0199 (0,0202) | +0,000 (−0,007 a +0,009) | 0,98 (0,97 a 0,99) | 0 |
  | `REING_7D` | Random Forest | 0,0199 (0,0202) | −0,020 (−0,027 a −0,012) | 0,63 (0,62 a 0,64) | 251.693 (1.159) |
  | `REING_7D` | XGBoost | 0,0198 (0,0202) | +0,002 (−0,005 a +0,011) | 0,96 (0,95 a 0,97) | 0 |
  | `REING_7D_CDM` | Regresión logística | 0,0123 (0,0125) | +0,001 (−0,010 a +0,012) | 0,98 (0,97 a 0,99) | 0 |
  | `REING_7D_CDM` | Random Forest | 0,0123 (0,0125) | −0,025 (−0,035 a −0,014) | 0,63 (0,62 a 0,64) | 455.804 (1.221) |
  | `REING_7D_CDM` | XGBoost | 0,0122 (0,0125) | +0,005 (−0,006 a +0,016) | 0,95 (0,94 a 0,96) | 0 |
  | `REING_30D` | Regresión logística | 0,0524 (0,0555) | +0,000 (−0,004 a +0,006) | 0,99 (0,99 a 1,00) | 0 |
  | `REING_30D` | Random Forest | 0,0522 (0,0555) | −0,001 (−0,006 a +0,004) | 0,89 (0,88 a 0,89) | 56.622 (401) |
  | `REING_30D` | XGBoost | 0,0520 (0,0555) | +0,002 (−0,003 a +0,006) | 1,00 (0,99 a 1,00) | 0 |
  | `REING_30D_CDM` | Regresión logística | 0,0328 (0,0343) | +0,001 (−0,006 a +0,008) | 0,99 (0,98 a 1,00) | 0 |
  | `REING_30D_CDM` | Random Forest | 0,0326 (0,0343) | −0,017 (−0,024 a −0,010) | 0,87 (0,86 a 0,88) | 156.822 (532) |
  | `REING_30D_CDM` | XGBoost | 0,0325 (0,0343) | +0,004 (−0,003 a +0,011) | 1,00 (1,00 a 1,01) | 0 |

- **Lectura:** XGBoost tiene la AUPRC y el AUROC más altos en las cuatro variables. En AUROC su intervalo no toca el de ningún otro modelo en ninguna variable; por ejemplo, en `REING_30D_CDM` va de 0,775 a 0,779, y el del Random Forest, de 0,759 a 0,763. En AUPRC las diferencias son chicas, y los intervalos de XGBoost y del Random Forest se tocan en las cuatro variables. El script 18 no compara los modelos entre sí sorteo por sorteo, así que no se afirma qué modelo es mejor en AUPRC. Los modelos superan a la prevalencia entre 2,8 y 4,7 veces, más en las variables de misma CDM. Los tres quedan bajo el Brier de referencia. La regresión logística y XGBoost están calibrados: el intercepto queda cerca de 0 y la pendiente, entre 0,95 y 1,00. El Random Forest da predicciones demasiado extremas, con pendiente 0,63 en las variables de 7 días y de 0,87 a 0,89 en las de 30, y deja muchos casos con probabilidad 0. Se informa (D63); sus hiperparámetros se ajustan en la actividad 3.3.
- **Lo que no se alcanzó a leer:** El reporte del script 18 trae también la calibración de cada año del alta (D56; la pidió el profesor guía en la O10) y la AUPRC y el AUROC de cada vuelta (D63). No se alcanzaron a leer antes de perder el acceso al servidor, el 20 de noviembre de 2026. Quedan en el servidor, o hay que volver a calcularlos.
- **Tiempos:** En `REING_30D_CDM`, una vuelta de la regresión logística tardó de 2 a 16 minutos (de 15 a 23 pasadas); una del Random Forest, unos 24 minutos, y una de XGBoost, unos 8 segundos.
- **Verificaciones:**

  | Qué | Resultado |
  |---|---|
  | Script 17, etapa base | Las 72 verificaciones de las 9 combinaciones, 8 en cada una |
  | Script 18 | Sus 8 verificaciones sobre 15 combinaciones, entre ellas que la ponderación fijada coincide con el veredicto del ensayo |
  | Prueba independiente del script 17 | Todas sus comprobaciones se cumplen (949 s) |
  | Prueba independiente del script 18 | Todas sus comprobaciones se cumplen (286 s) |

- **Evidencia:** en el servidor, `~/Tesis_Javiera/salida_17_base.txt`, `salida_18_base.txt`, `salida_pruebas_base.txt` y las secciones 1 a 4 de `reportes/18_metricas.md`, del 17 de noviembre de 2026. La persona a cargo las copió desde la Terminal. Los archivos quedaron en el servidor, al que se perdió el acceso el 20 de noviembre.
- **Visto bueno:** La persona a cargo de la tesis aprobó el 20 de noviembre de 2026 pasar estos resultados a la bitácora («Sí, pásalos»).
- **Completada por:** H41 y H42 (26 de noviembre de 2026): la repetición en bioserver5 da las mismas cifras, y la calibración por año y las métricas de cada vuelta ya se leyeron.

### H40 · 2026-11-18 · La lista A no pierde frente a la lista sin filtro en ninguna de las 12 comparaciones
- **Actividad:** 3.2 (responde a la observación O7 de la revisión del profesor guía del 30 de octubre de 2026)
- **Hallazgo:** La etapa sin filtro de D64 se entrenó en el servidor el 17 y el 18 de noviembre de 2026 (script 17, 1.606,3 minutos, 12 combinaciones, con entre 7.360 y 7.631 columnas), y el script 18 la evaluó el 18 (51,9 minutos). La comparación usa los mismos sorteos de pacientes para las dos listas, y la caída se mide desde la sin filtro hacia la A (D67): la del AUROC en puntos y la de la AUPRC como proporción del valor de la sin filtro. Los márgenes del objetivo específico 3 son 0,02 y 10 %.

  | Variable | Modelo | Caída de la AUPRC (intervalo) | Caída del AUROC (intervalo) | Veredicto |
  |---|---|---|---|---|
  | `REING_7D` | Regresión logística | 0,4 % (−0,7 % a 1,4 %) | +0,004 (+0,002 a +0,005) | No pierde |
  | `REING_7D` | Random Forest | 0,8 % (−0,5 % a 2,0 %) | +0,005 (+0,003 a +0,006) | No pierde |
  | `REING_7D` | XGBoost | 1,9 % (0,9 % a 2,9 %) | +0,003 (+0,002 a +0,004) | No pierde |
  | `REING_7D_CDM` | Regresión logística | 0,7 % (−1,1 % a 2,7 %) | +0,002 (−0,000 a +0,004) | No pierde |
  | `REING_7D_CDM` | Random Forest | 3,1 % (1,2 % a 4,9 %) | +0,007 (+0,005 a +0,009) | No pierde |
  | `REING_7D_CDM` | XGBoost | 0,1 % (−1,8 % a 2,0 %) | +0,003 (+0,001 a +0,004) | No pierde |
  | `REING_30D` | Regresión logística | 1,0 % (0,6 % a 1,4 %) | +0,005 (+0,005 a +0,006) | No pierde |
  | `REING_30D` | Random Forest | −0,4 % (−0,9 % a −0,0 %) | +0,003 (+0,002 a +0,004) | No pierde |
  | `REING_30D` | XGBoost | 0,4 % (0,1 % a 0,7 %) | +0,001 (+0,001 a +0,002) | No pierde |
  | `REING_30D_CDM` | Regresión logística | 2,0 % (1,3 % a 2,6 %) | +0,010 (+0,009 a +0,011) | No pierde |
  | `REING_30D_CDM` | Random Forest | −0,4 % (−1,1 % a 0,3 %) | +0,005 (+0,004 a +0,006) | No pierde |
  | `REING_30D_CDM` | XGBoost | −0,0 % (−0,6 % a 0,6 %) | +0,002 (+0,002 a +0,003) | No pierde |

- **Lectura:** Las 12 comparaciones quedan lejos de los márgenes. La mayor caída de la AUPRC es la del Random Forest de `REING_7D_CDM`, 3,1 % (1,2 % a 4,9 %), menos de la mitad del margen. La mayor del AUROC es la de la regresión logística de `REING_30D_CDM`, 0,010 (0,009 a 0,011), la mitad del margen. En tres casos la lista A queda igual o apenas por encima en AUPRC: el Random Forest de `REING_30D` y de `REING_30D_CDM` (−0,4 %) y XGBoost de `REING_30D_CDM` (0,0 %). Con entre 57 y 424 códigos, según la variable, la lista A conserva prácticamente toda la información de los casi 7.000 códigos con al menos 100 casos: el filtro de la Etapa 3 (D45) no deja fuera información útil para estos modelos.
- **Costo:** La etapa sin filtro tardó 134 minutos por combinación, frente a 78 de la etapa base. En `REING_30D_CDM`, una vuelta de la regresión logística tardó de 16 a 18 minutos (una, 55), y una del Random Forest, de 28 a 32.
- **Verificaciones:**

  | Qué | Resultado |
  |---|---|
  | Script 17, etapa sin filtro | Las 96 verificaciones de las 12 combinaciones, 8 en cada una |
  | Script 18 | Sus 8 verificaciones sobre 27 combinaciones |
  | Prueba independiente del script 17 | Todas sus comprobaciones se cumplen (410 s) |
  | Prueba independiente del script 18 | Todas sus comprobaciones se cumplen (515 s) |

- **Consecuencia:** Frente a la lista sin filtro, la lista A sigue como la principal (D64). Faltan las comparaciones con la lista agrupada y la lista C, y el modelo sin hospital.
- **Evidencia:** en el servidor, `~/Tesis_Javiera/salida_17_sin_filtro.txt`, `salida_18_sin_filtro.txt`, `salida_pruebas_sin_filtro.txt` y las secciones 1 y 7 de `reportes/18_metricas.md`, del 18 de noviembre de 2026. La persona a cargo las copió desde la Terminal. Los archivos quedaron en el servidor, al que se perdió el acceso el 20 de noviembre.
- **Visto bueno:** La persona a cargo de la tesis aprobó el 20 de noviembre de 2026 pasar estos resultados a la bitácora («Sí, pásalos»).
- **Completa a:** D64, con su primer veredicto.

### D68 · 2026-11-25 · Los modelos se entrenan en bioserver5 (DIINF, USACH), con el mismo entorno y 50 procesadores
- **Actividad:** 3.2
- **Qué pasó:** El 20 de noviembre de 2026 se perdió el acceso al servidor de la UFRGS (D58 y D65) para todos sus usuarios, también para el profesor guía, y sus administradores no han respondido. Lo que había allá se da por perdido: las predicciones, las métricas de los 1.000 sorteos, los reportes y las salidas de las 27 combinaciones del ensayo, la etapa base y la sin filtro. No se intenta recuperarlo por otra vía. Se salvaron el código, que está en GitHub; las tres tablas para los modelos, en el portátil, con el hash registrado (comprobado el 25 de noviembre de 2026); los resultados escritos en H37 a H40, y una copia de las tablas del reporte del script 18. El 23 de noviembre la Mesa de ayuda del DIINF de la USACH agregó a la persona a cargo, con una cuenta propia, a los usuarios de bioserver5; otro estudiante recibió acceso el mismo día.
- **Cómo se entra:** Por SSH, desde el Símbolo del sistema del portátil, en la red cableada del DIINF o, fuera de la USACH, con la VPN institucional. Ya no hay RStudio Server: los comandos se escriben en la sesión de SSH y las tablas se suben con `scp`, el programa de copia de SSH. La persona a cargo inicia sesión; el asistente no tiene acceso y trabaja con lo que ella copia de la pantalla.
- **Lo que tiene el servidor:** Según el diagnóstico de solo lectura del 25 de noviembre de 2026:

  | Qué | En el servidor |
  |---|---|
  | Procesadores | 128: dos AMD EPYC 9334 de 32 núcleos, con dos hilos por núcleo. Al revisarlo, el 99 % estaba libre: otra persona usaba cerca de uno |
  | Memoria | 1.007 GB, de los que 996 GB estaban disponibles |
  | Tarjeta gráfica | No tiene |
  | Disco de la carpeta personal | 2,1 TB libres |
  | Python | Solo 3.10.12, del sistema; no hay conda |
  | Herramientas | git, curl, tmux, screen, nohup y setsid |
  | Límites de los procesos | Ninguno de tiempo ni de memoria |
  | Internet | Responden PyPI, GitHub y conda-forge |
  | Reinicio | Pendiente: si lo reinician, se detiene lo que esté corriendo, también dentro de tmux |

- **Decisión:**

  | Punto | Cómo |
  |---|---|
  | Servidor | bioserver5 reemplaza al servidor de la UFRGS. Lo de D58 sobre qué se sube y qué no sigue igual: nunca el conjunto de prueba ni los archivos crudos de 2019 |
  | Entorno | El de D65, en `~/Tesis_Javiera/`: Python 3.14.5 de conda-forge en `~/Tesis_Javiera/entorno` y las mismas 13 bibliotecas con sus versiones exactas. Como el servidor no tiene conda, antes se instala Miniforge 26.9.4-2, el instalador de conda de conda-forge, en `~/Tesis_Javiera/miniforge3`. Es la versión publicada el 6 de noviembre de 2026, más de dos semanas antes, como pide D65, y se comprobó el hash del instalador con el de su página en GitHub |
  | Procesadores | 50, en el parámetro `procesadores` de `reglas/parametros.csv`. El Random Forest arma sus 100 árboles de a tantos como procesadores tenga: con 32 son 4 rondas (32, 32, 32 y 4), y con 50, 2 rondas. Con 64 también son 2 rondas, así que 50 es el menor número con esa ganancia. Son el 39 % de los 128 procesadores; en la UFRGS se usaba el 50 % (32 de 64). El número de procesadores cambia solo el tiempo, no los modelos (H37) |
  | XGBoost | En el procesador, como en H37: el servidor no tiene tarjeta gráfica |
  | Entrenamientos largos | Dentro de tmux, como en D65. Con SSH es indispensable: lo que no esté en tmux se detiene si se corta la conexión o la VPN |
  | Copias en el portátil | Después de cada etapa se traen al portátil, con `scp`, los reportes y, si se puede, las tablas de métricas y de predicciones, para que el servidor no tenga la única copia |

- **Qué se vuelve a entrenar:** Las 12 combinaciones de la lista A con hospital y sin ponderar: las 9 de la etapa base y las 3 sin ponderar del ensayo. Hacen falta porque las comparaciones con la lista agrupada, la lista C y sin hospital se calculan sorteo por sorteo contra las predicciones de la lista A (D64 y D67). Con ellas se recuperan también la calibración de cada año del alta (D56, O10) y las métricas de cada vuelta, que no se alcanzaron a leer (H39). Las 3 combinaciones ponderadas del ensayo también se repiten, para recuperar H38 completo. La regresión logística de `REING_7D_CDM`, sin ponderar y ponderada, corre en una sesión de tmux aparte, con un solo procesador, porque la ponderada tardó 43 horas (H38); en la otra sesión van el Random Forest y XGBoost del ensayo y después la etapa base. A la vez se usan como máximo 51 procesadores. La etapa sin filtro no se repite: sus veredictos ya están en H40 y las comparaciones que faltan no la usan. Después siguen las etapas agrupada, sin hospital y C, en el orden de D64.
- **Cómo se comprueba:** Con las mismas tablas, versiones, semillas y parámetros, las métricas deben coincidir con las de H38 y H39 en los decimales anotados. El procesador es de otro fabricante, así que podría cambiar el último decimal; si cambia más que eso, se revisa antes de seguir.
- **Instalación:** La persona a cargo la hizo el 25 de noviembre de 2026 por SSH. Resultado: Python 3.14.5, numpy 2.5.3, pandas 3.0.3, pyarrow 25.0.1, scipy 1.18.1, scikit-learn 1.9.0, XGBoost 3.3.0, joblib 1.6.0, threadpoolctl 3.7.0, narwhals 2.27.1, cloudpickle 3.1.2, python-dateutil 2.9.0.post0, six 1.17.0 y nvidia-nccl-cu12 2.32.3: las 13 de D65 y ninguna otra, aparte de pip. pip no encontró dependencias faltantes («No broken requirements found»). La carpeta ocupa 2,2 GB. El código se clonó en `~/Tesis_Javiera/Codigo` (commit `c625ac9`) y las tres tablas se subieron a su `data/processed/` con `scp`, con el hash igual al registrado.
- **Visto bueno:** La persona a cargo de la tesis aprobó escribir esta entrada el 25 de noviembre de 2026, con los 50 procesadores («escríbela»). Antes, ese mismo día, había ejecutado la instalación después de que se le explicó el plan.
- **Reemplaza en parte a:** D58, en dónde se entrena y cómo se entra, y D65, en cuántos procesadores se usan y cómo se instala conda. El resto de las dos sigue vigente.
- **Evidencia:** diagnóstico de solo lectura del 25 de noviembre de 2026 en bioserver5 (bloque de comandos por SSH); salidas de la instalación, de la comprobación de versiones, del `git clone` y de la comprobación del hash de las tablas; hash del instalador de Miniforge, de la página de la versión 26.9.4-2 en GitHub.
- **Estado:** Adoptada. La repetición quedó comprobada en H41 (26 de noviembre de 2026).

### H41 · 2026-11-26 · La repetición en bioserver5 da exactamente los mismos resultados que en la UFRGS
- **Actividad:** 3.2
- **Hallazgo:** Con el entorno de D68 se volvieron a entrenar en bioserver5 las 12 combinaciones de la lista A con hospital y sin ponderar y las 3 ponderadas del ensayo, entre el 25 y el 26 de noviembre de 2026. El script 18 las evaluó con los mismos 1.000 sorteos de pacientes. En las 15, la AUPRC, el AUROC, el Brier, el intercepto, la pendiente y sus intervalos son idénticos, celda por celda, a los de H38 y H39. Se comparó con un programa de solo lectura contra la copia de esos reportes que había quedado en el portátil.
- **Señales de que el cálculo es el mismo:**

  | Qué | UFRGS | bioserver5 |
  |---|---|---|
  | Casos con probabilidad 0 del Random Forest de `REING_7D_CDM` (reingresan) | 455.804 (1.221) | 455.804 (1.221) |
  | Pasadas de la regresión logística ponderada en las cinco vueltas | 48, 186, 102, 73 y 115 | 48, 186, 102, 73 y 115 |
  | Veredicto del ensayo (cambio de la AUPRC al ponderar) | LR −3,9 %, RF −13,3 %, XGB −1,2 % | LR −3,9 %, RF −13,3 %, XGB −1,2 % |

- **Lectura:** Con las mismas tablas, versiones, semillas y parámetros, el resultado no depende del equipo ni del número de procesadores, aunque el procesador sea de otro fabricante. Por eso los veredictos de la lista sin filtro (H40), que no se repitió (D68), se mantienen.
- **Tiempos en bioserver5:**

  | Etapa | Tiempo | En la UFRGS |
  |---|---|---|
  | Ensayo: Random Forest y XGBoost | 40 min | Unas 2 h 33 min |
  | Ensayo: regresión logística, sin ponderar y ponderada | 1.277 min (21 h 17 min) | Unas 45 h 30 min |
  | Base | 177 min | 705 min |
  | Agrupada | 260 min | — |
  | Sin hospital | 271 min | — |
  | C | 290 min | — |
  | Script 18 de cada etapa | 22 a 62 min | 42 a 55 min |

- **Verificaciones:** el script 18 final cumple sus 8 verificaciones sobre 51 combinaciones, entre ellas que la ponderación fijada coincide con el veredicto del ensayo. Las pruebas independientes cumplen sus 19 y 15 comprobaciones (343 y 425 s). El registro tiene todas las vueltas con el commit `ca88716`, sin avisos.
- **Evidencia:** reportes del 17 y del 18, salidas y registro de bioserver5, copiados al portátil el 27 de noviembre de 2026 en `Resultados_servidor/2026-11-27_3.2_completa/`, con el hash del archivo comprimido igual en el servidor y en el portátil.
- **Visto bueno:** La persona a cargo de la tesis aprobó pasar estos resultados a la bitácora el 28 de noviembre de 2026 («sí»).
- **Completa a:** D68.

### H42 · 2026-11-26 · La calibración por año del alta y las métricas de cada vuelta
- **Actividad:** 3.2 (responde a la observación O10 de la revisión del profesor guía del 30 de octubre de 2026; D56)
- **Hallazgo:** Con las predicciones fuera de pliegue de la lista A se calcularon, por primera vez, el intercepto y la pendiente de cada año del alta (D56) y la AUPRC y el AUROC de cada vuelta (D63). No se habían alcanzado a leer en el servidor de la UFRGS (H39).
- **Pendiente por año:**

  | Modelo | Variables de 7 días | Variables de 30 días |
  |---|---|---|
  | Regresión logística | 0,94 a 1,03 | 0,96 a 1,05 |
  | Random Forest | 0,59 a 0,66 | 0,85 a 0,91 |
  | XGBoost | 0,94 a 0,99 | 0,98 a 1,04 |

- **Intercepto por año, ejemplo con XGBoost y `REING_30D`:**

  | Año | Casos | Reingresó | Predicho | Intercepto (intervalo) |
  |---|---|---|---|---|
  | 2019 | 644.415 | 5,70 % | 5,49 % | +0,041 (+0,030 a +0,052) |
  | 2020 | 413.202 | 5,66 % | 5,71 % | −0,009 (−0,023 a +0,005) |
  | 2021 | 508.698 | 5,62 % | 5,77 % | −0,029 (−0,042 a −0,016) |
  | 2022 | 564.053 | 5,76 % | 5,90 % | −0,027 (−0,040 a −0,015) |
  | 2023 | 615.867 | 6,14 % | 6,10 % | +0,008 (−0,003 a +0,018) |
  | 2024 | 529.197 | 6,45 % | 6,36 % | +0,015 (+0,003 a +0,027) |

- **Lectura:** La pendiente de la regresión logística y de XGBoost queda cerca de 1 en los seis años. La del Random Forest es baja en todos, así que sus predicciones demasiado extremas (H39) no dependen del año. El intercepto va de −0,10 a +0,07 en las cuatro variables y los tres modelos, con el mismo patrón: los tres modelos se quedan algo cortos en 2019 y se pasan algo en 2021 y 2022; en 2024, la regresión logística y XGBoost se quedan levemente cortos, y el Random Forest queda cerca de 0. La explicación más probable es que el año no es una variable del modelo (D49), así que el modelo usa una tasa promedio; además, `VENTANA_CORTADA` marca por igual 2019 y 2021. Las diferencias son de décimas de punto: en el ejemplo, 5,49 % predicho frente a 5,70 % real. La parte temporal de D56, entrenar con 2019–2022 y evaluar 2023–2024, es de la actividad 4.1 (D59).
- **Métricas de cada vuelta:** muy parejas en las 12 combinaciones. Por ejemplo, el AUROC de XGBoost con `REING_30D` va de 0,756 a 0,758, y la AUPRC de la regresión logística con `REING_30D_CDM`, de 0,121 a 0,124. Ninguna vuelta se aparta de las demás.
- **Evidencia:** secciones 5 y 6 del reporte del script 18 del 27 de noviembre de 2026.
- **Visto bueno:** La persona a cargo de la tesis aprobó pasar estos resultados a la bitácora el 28 de noviembre de 2026 («sí»).
- **Completa a:** D56 (bitácora de la 2.3), en la parte de las predicciones fuera de pliegue.

### H43 · 2026-11-27 · La lista A no pierde frente a la lista agrupada ni frente a la lista C
- **Actividad:** 3.2 (responde a la observación O7 de la revisión del profesor guía del 30 de octubre de 2026)
- **Hallazgo:** Las etapas agrupada y C de D64 se entrenaron en bioserver5 el 26 de noviembre de 2026, y el script 18 las comparó con la lista A con los mismos sorteos de pacientes. La caída se mide desde la otra lista hacia la A (D67); los márgenes del objetivo específico 3 son 0,02 en AUROC y 10 % en AUPRC.

  | Variable | Modelo | Frente a | Caída de la AUPRC (intervalo) | Caída del AUROC (intervalo) | Veredicto |
  |---|---|---|---|---|---|
  | `REING_7D` | Regresión logística | agrupada | 0,1 % (−0,3 % a 0,5 %) | −0,001 (−0,001 a −0,000) | No pierde |
  | `REING_7D` | Regresión logística | C | 0,9 % (0,2 % a 1,5 %) | +0,007 (+0,006 a +0,007) | No pierde |
  | `REING_7D` | Random Forest | agrupada | 1,6 % (0,7 % a 2,5 %) | +0,001 (+0,000 a +0,003) | No pierde |
  | `REING_7D` | Random Forest | C | 1,5 % (0,6 % a 2,4 %) | +0,004 (+0,003 a +0,006) | No pierde |
  | `REING_7D` | XGBoost | agrupada | 1,3 % (0,3 % a 2,2 %) | +0,001 (+0,000 a +0,002) | No pierde |
  | `REING_7D` | XGBoost | C | 0,3 % (−0,5 % a 1,0 %) | +0,000 (−0,000 a +0,001) | No pierde |
  | `REING_7D_CDM` | Regresión logística | agrupada | 1,3 % (0,4 % a 2,3 %) | +0,000 (−0,000 a +0,001) | No pierde |
  | `REING_7D_CDM` | Regresión logística | C | 4,7 % (3,5 % a 6,0 %) | +0,011 (+0,010 a +0,012) | No pierde |
  | `REING_7D_CDM` | Random Forest | agrupada | 1,2 % (−0,3 % a 2,7 %) | +0,001 (−0,001 a +0,003) | No pierde |
  | `REING_7D_CDM` | Random Forest | C | 1,2 % (−0,1 % a 2,4 %) | +0,003 (+0,001 a +0,004) | No pierde |
  | `REING_7D_CDM` | XGBoost | agrupada | 1,3 % (−0,4 % a 3,0 %) | +0,001 (−0,000 a +0,001) | No pierde |
  | `REING_7D_CDM` | XGBoost | C | −0,4 % (−2,3 % a 1,6 %) | −0,000 (−0,001 a +0,001) | No pierde |
  | `REING_30D` | Regresión logística | agrupada | −0,3 % (−0,5 % a −0,1 %) | −0,000 (−0,001 a −0,000) | No pierde |
  | `REING_30D` | Regresión logística | C | 0,7 % (0,5 % a 0,9 %) | +0,003 (+0,003 a +0,003) | No pierde |
  | `REING_30D` | Random Forest | agrupada | −0,1 % (−0,5 % a 0,2 %) | +0,000 (−0,000 a +0,001) | No pierde |
  | `REING_30D` | Random Forest | C | 0,3 % (−0,1 % a 0,6 %) | +0,002 (+0,001 a +0,002) | No pierde |
  | `REING_30D` | XGBoost | agrupada | −0,1 % (−0,4 % a 0,3 %) | +0,000 (−0,000 a +0,000) | No pierde |
  | `REING_30D` | XGBoost | C | −0,1 % (−0,4 % a 0,1 %) | −0,000 (−0,001 a −0,000) | No pierde |
  | `REING_30D_CDM` | Regresión logística | agrupada | −0,4 % (−0,8 % a −0,1 %) | +0,001 (+0,000 a +0,001) | No pierde |
  | `REING_30D_CDM` | Regresión logística | C | 1,9 % (1,5 % a 2,2 %) | +0,008 (+0,007 a +0,008) | No pierde |
  | `REING_30D_CDM` | Random Forest | agrupada | −0,0 % (−0,6 % a 0,5 %) | +0,001 (+0,000 a +0,002) | No pierde |
  | `REING_30D_CDM` | Random Forest | C | 0,9 % (0,4 % a 1,4 %) | +0,002 (+0,001 a +0,003) | No pierde |
  | `REING_30D_CDM` | XGBoost | agrupada | 0,9 % (0,3 % a 1,5 %) | +0,002 (+0,001 a +0,002) | No pierde |
  | `REING_30D_CDM` | XGBoost | C | −0,9 % (−1,4 % a −0,4 %) | −0,000 (−0,001 a +0,000) | No pierde |

- **Lectura:** Las 24 comparaciones quedan lejos de los márgenes. Frente a la agrupada, que junta los diagnósticos en su categoría de tres caracteres, la mayor caída es 1,6 % en AUPRC y 0,002 en AUROC: agrupar no mejora la predicción. Frente a la C, que tiene entre 629 y 1.595 códigos, la mayor caída es la de la regresión logística de `REING_7D_CDM`, 4,7 % (3,5 % a 6,0 %) en AUPRC y 0,011 en AUROC, menos de la mitad del margen. La regresión logística es el modelo que más aprovecha los códigos extra; con XGBoost la A queda igual o un poco mejor que la C.
- **Consecuencia:** Junto con H40, la lista A no pierde en ninguna de las 36 comparaciones de D64. Sigue como la lista principal para la actividad 3.3, y no hay nada que llevar al profesor guía antes de esa actividad.
- **Evidencia:** sección 7 del reporte del script 18 del 27 de noviembre de 2026, después de que las dos pruebas independientes cumplieran todas sus comprobaciones.
- **Visto bueno:** La persona a cargo de la tesis aprobó pasar estos resultados a la bitácora el 28 de noviembre de 2026 («sí»).
- **Completa a:** D64, junto con H40.

### H44 · 2026-11-26 · Sin hospital, el modelo pierde poco
- **Actividad:** 3.2 (responde a la observación O9 de la revisión del profesor guía del 30 de octubre de 2026; D55)
- **Hallazgo:** La etapa sin hospital de D64 entrenó la lista A sin la variable `HOSPITAL` el 26 de noviembre de 2026. Como pide D64, solo se informa la caída frente al modelo con hospital, con los mismos sorteos de pacientes.

  | Variable | Modelo | Caída de la AUPRC (intervalo) | Caída del AUROC (intervalo) |
  |---|---|---|---|
  | `REING_7D` | Regresión logística | 1,3 % (1,0 % a 1,7 %) | +0,002 (+0,002 a +0,003) |
  | `REING_7D` | Random Forest | 0,8 % (−0,1 % a 1,6 %) | +0,002 (+0,001 a +0,003) |
  | `REING_7D` | XGBoost | 1,5 % (0,6 % a 2,3 %) | +0,002 (+0,002 a +0,003) |
  | `REING_7D_CDM` | Regresión logística | 1,4 % (1,0 % a 1,8 %) | +0,002 (+0,002 a +0,003) |
  | `REING_7D_CDM` | Random Forest | 3,5 % (2,1 % a 4,7 %) | +0,003 (+0,001 a +0,005) |
  | `REING_7D_CDM` | XGBoost | 1,6 % (−0,3 % a 3,4 %) | +0,003 (+0,002 a +0,003) |
  | `REING_30D` | Regresión logística | 0,9 % (0,8 % a 1,1 %) | +0,001 (+0,001 a +0,001) |
  | `REING_30D` | Random Forest | 0,7 % (0,3 % a 1,0 %) | +0,001 (+0,000 a +0,001) |
  | `REING_30D` | XGBoost | 0,8 % (0,6 % a 1,1 %) | +0,001 (+0,000 a +0,001) |
  | `REING_30D_CDM` | Regresión logística | 0,8 % (0,6 % a 0,9 %) | +0,001 (+0,001 a +0,001) |
  | `REING_30D_CDM` | Random Forest | 0,6 % (0,0 % a 1,2 %) | +0,000 (−0,000 a +0,001) |
  | `REING_30D_CDM` | XGBoost | 0,5 % (−0,0 % a 1,0 %) | +0,000 (−0,000 a +0,001) |

- **Lectura:** Sin el hospital, la AUPRC baja entre 0,5 % y 3,5 % y el AUROC, como mucho, 0,003. El modelo se apoya poco en el hospital: buena parte de esa información parece llegar por otras variables. Si conviene dejarlo o sacarlo se decide en la actividad 3.3, al elegir las variables (D55).
- **Evidencia:** sección 8 del reporte del script 18 del 27 de noviembre de 2026.
- **Visto bueno:** La persona a cargo de la tesis aprobó pasar estos resultados a la bitácora el 28 de noviembre de 2026 («sí»).
- **Completa a:** D64 y D55 (bitácora de la 3.1).

---

## Pendientes

- Guardar en Git los reportes finales de los scripts 17 y 18 y de sus pruebas, que hoy están en el servidor y en `Resultados_servidor/2026-11-27_3.2_completa/` del portátil, fuera de Git.
- Informe de avance 6: los resultados de la 3.2, D50 a D57, H34, la respuesta a la O6 (cómo se separó el conjunto de prueba), D58 a D68 y H35 en adelante.
