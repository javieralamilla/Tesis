# Diccionario de las tablas para los modelos

Generado por `3.1_filtro_dimensionalidad/scripts/16_tablas_modelos.py`. Son las tablas que leen los modelos de la actividad 3.2: `data/processed/modelos_casos.parquet` (una fila por caso de estudio de desarrollo: 3.347.652 filas y 40 columnas) y `data/processed/modelos_codigos.parquet` (una fila por caso de estudio y código: 59.214.795 filas), junto con las listas de códigos de `data/processed/listas_codigos.parquet` (script 14). Solo tienen los casos de estudio del conjunto de desarrollo: el conjunto de prueba se arma igual en la evaluación final, con las listas de todo desarrollo (`PLIEGUE` = 0).

## Versión de las tablas

| Dato | Valor |
|---|---|
| Versión | 1 |
| Fecha de registro | 2026-11-03 |
| Versión de la partición | 3 (`docs/version_particion.csv`) |
| Casos, columnas de la tabla de casos y pares caso–código | 3.347.652, 40 y 59.214.795 |
| SHA-256 de `modelos_casos.parquet` | `3a0274aa1b6315693582b67e7c5421ba91c17dfb0bf9a955b9d5676050673a44` |
| SHA-256 de `modelos_codigos.parquet` | `039d4dfcd8a8b45703e4c8ff1cc8ea73efaed41e7856b98d7de4ea89fce62c66` |
| SHA-256 de `desarrollo.parquet` | `50f07908f35df51c31077971d0aafaf69182c3baea926af34b00d6fff41229b1` |
| SHA-256 de `validacion_temporal.parquet` | `5add3eeccca35236293308cf6ab919ae3606a7663e61b9f9cd23a71a51db7ea9` |
| SHA-256 de `variables_casos.parquet` | `4a64a07e7eee9cd07d5174fac5085f93b650303733ce549aa692feb2c13d1cda` |
| SHA-256 de `listas_codigos.parquet` | `b185fc5ce2be25bd19fc9dc77fb82adcd8a51a1873b518aaf9b1944195adfef0` |
| SHA-256 de `columnas_modelos.csv` | `b960664a4367800560be069087bdd1b8991f703f19b57eac40bd81b02a0d3ee5` |
| SHA-256 de `16_tablas_modelos.py` | `c0edb6ab77746b5d1ac0a74cc46943da838e719fa2c72265b72b0e08f3466701` |
| Bibliotecas | Python 3.14.5, pandas 3.0.3, pyarrow 25.0.1 |

El historial está en `docs/version_tablas_modelos.csv`: solo se agrega una fila cuando cambia alguna de las dos tablas o algo de lo que las produce (sus entradas, la tabla de columnas o el script). Antes de entrenar, conviene comprobar que los archivos tengan el hash de la última versión registrada.

## Cómo se usan

1. **Elegir la variable objetivo** y usar solo los casos que tienen dato en ella. Los casos sin dato no son 0: no tienen el seguimiento necesario (las de 30 días) o son partos (las de misma CDM).
2. **Elegir la lista de códigos y el pliegue** en `listas_codigos.parquet`. En la validación cruzada, al entrenar sin el pliegue k se usa la lista de `PLIEGUE` = k, calculada con ese entrenamiento, y se evalúa en el pliegue k (D53). El modelo final y el conjunto de prueba usan la de `PLIEGUE` = 0, calculada con todo desarrollo.
3. **Armar la matriz de códigos:** una columna sí/no por código de la lista. Un caso tiene 1 en una columna si en `modelos_codigos.parquet` hay una fila con su `ID_EGRESO` y el `BLOQUE`, el `NIVEL` y el `CODIGO` de esa columna. Como casi todas las celdas son 0, conviene una matriz dispersa, que guarda solo los 1 (receta al final).
4. **Juntarla con las predictoras** (papel PREDICTORA) de la tabla de casos. Cómo se codifican las categorías y si se transforman los números se decide con cada modelo en la actividad 3.2.
5. **Evaluar** con `PLIEGUE` (validación cruzada, D52), `PERIODO` y `PACIENTE_VISTO` (validación temporal, D40), `ANIO_ALTA` (calibración por año, D56) e `ID_PACIENTE` (intervalos con remuestreo de pacientes, D41).

## Papeles de las columnas

| Papel | Qué significa |
|---|---|
| IDENTIFICADOR | identifica el caso o el paciente. Nunca es predictora |
| VALIDACION | organiza la validación (pliegues, validación temporal y año del alta). Nunca es predictora |
| PREDICTORA | variable del modelo (D46 a D49 y D54, script 15) |
| OBJETIVO | variable de reingreso que predice el modelo. Nunca es predictora |
| CODIGO | describe los códigos de cada caso: los de la lista elegida pasan a ser predictoras sí/no |

Las columnas de papel IDENTIFICADOR, VALIDACION u OBJETIVO nunca son predictoras. Tampoco están, en ninguna de las dos tablas, las columnas que describen lo que pasa después del alta (`DIAS_REING` e `ID_EGRESO_REING`), la identidad de la persona (`ID_PERSONA`, `IDENTIDAD_AMBIGUA`) ni cómo se armó la cohorte.

## 1. `modelos_casos.parquet`

Una fila por caso de estudio de desarrollo, en el orden de `desarrollo.parquet` (de menor a mayor `ID_EGRESO`). **Sin dato:** en las columnas de texto, el valor SIN DATO; en las numéricas, el valor nulo.

| Columna | Papel | Tipo | Descripción | Valores | Sin dato | Origen |
|---|---|---|---|---|---|---|
| `ID_EGRESO` | IDENTIFICADOR | Entero | Identificador del egreso del caso de estudio. Une esta tabla con modelos_codigos.parquet | 3.347.652 distintos | — | Script 06 (actividad 2.1) |
| `ID_PACIENTE` | IDENTIFICADOR | Entero | Identificador del paciente dentro de su bloque. Sirve para los intervalos con remuestreo de pacientes (D41) y para comprobar que un paciente no quede en dos pliegues | 2.509.082 distintos | — | Datos del DEIS (D27) |
| `ANIO_ALTA` | VALIDACION | Entero | Año del alta del caso. Sirve para la calibración por año (D56), para la sensibilidad que entrena solo con 2020 y 2022 (D44) y para separar los hospitales sin casos antes de 2023 (D55). El año no es una variable del modelo (D49) | de 2019 a 2024 | — | Año del archivo, que es el del alta (D56) |
| `PERIODO` | VALIDACION | Texto | ENTRENAMIENTO (alta de 2019 a 2022) o EVALUACION (alta en 2023 o 2024) en la validación temporal interna | ENTRENAMIENTO (64,6 %), EVALUACION (35,4 %) | — | Script 13 (D40) |
| `PACIENTE_VISTO` | VALIDACION | Verdadero/falso | En los casos de evaluación, verdadero si el paciente tiene algún egreso en 2021 o 2022. Sin dato en los casos de entrenamiento | verdadero o falso | 2.164.089 | Script 13 (D40) |
| `PLIEGUE` | VALIDACION | Entero | Pliegue de la validación cruzada (1 a 5). Todos los casos de un paciente están en el mismo pliegue. Elige también la lista de códigos de cada vuelta (D53) | de 1 a 5 | — | Script 13 (D52) |
| `EDAD` | PREDICTORA | Decimal | Edad en años, con decimales, al ingreso del propio egreso | de 0,0 a 109,9 | — | Script 15 (D46) |
| `SEXO` | PREDICTORA | Texto | Sexo, tal cual | MUJER (61,0 %), HOMBRE (39,0 %), SIN DATO (0,0 %) | 312 | Script 15 (D46) |
| `PREVISION_GRUPO` | PREDICTORA | Texto | Previsión en 8 grupos (reglas/prevision_grupos.csv) | 9 valores | 2.425 | Script 15 (D46) |
| `REGION` | PREDICTORA | Texto | Región de residencia, desde la provincia (reglas/provincia_region.csv) | 17 valores | 1.089 | Script 15 (D46) |
| `TIPO_INGRESO` | PREDICTORA | Texto | Tipo de ingreso del propio egreso, tal cual | URGENCIA (58,8 %), OBSTETRICA (21,0 %), PROGRAMADA (20,2 %), SIN DATO (0,0 %) | 295 | Script 15 (D46) |
| `ESTADIA` | PREDICTORA | Entero | Días desde el ingreso índice (el que abre el episodio) hasta el alta del caso | de 0 a 3146 | — | Script 15 (D46) |
| `CDM` | PREDICTORA | Texto | Categoría diagnóstica mayor, tal cual | 22 valores | — | Script 15 (D46) |
| `PESO_GRD` | PREDICTORA | Decimal | Peso del GRD. El peso 0 queda sin dato | de 0,1 a 20,6 | 1 | Script 15 (D46) |
| `HOSP_PREVIAS` | PREDICTORA | Entero | Hospitalizaciones de la misma persona (episodios) terminadas en los 365 días antes del ingreso índice | de 0 a 64 | — | Script 15 (D47, D50) |
| `HOSP_PREVIAS_NO_PLANIF` | PREDICTORA | Entero | De ellas, las que empezaron con un ingreso no planificado (D20 y D33) | de 0 a 30 | — | Script 15 (D47) |
| `DIAS_ULTIMA_HOSP` | PREDICTORA | Entero | Días desde el alta de la última hospitalización de la ventana hasta el ingreso índice. Vale 366 si no hubo ninguna | de 0 a 366 | — | Script 15 (D47) |
| `CMA_PREVIAS` | PREDICTORA | Entero | Cirugías mayores ambulatorias terminadas en la ventana | de 0 a 11 | — | Script 15 (D47) |
| `SESIONES_PREVIAS` | PREDICTORA | Entero | Sesiones de tratamiento (diagnóstico principal Z51) y tratamientos periódicos (criterio E15) terminados en la ventana | de 0 a 340 | — | Script 15 (D47, D50) |
| `VENTANA_CORTADA` | PREDICTORA | Entero | 1 si la ventana de 365 días empieza antes del inicio del bloque del identificador (D42 y D44) | 0 o 1 | — | Script 15 (D44, D47) |
| `INDICE_COMORBILIDAD` | PREDICTORA | Entero | Índice de reingreso de Moore et al. (2017) con las condiciones de Elixhauser de los diagnósticos secundarios | de -4 a 102 | — | Script 15 (D48, D54) |
| `TIPO_ALTA` | PREDICTORA | Texto | Destino al alta, tal cual | DOMICILIO (94,8 %), HOSPITALIZACIÓN DOMICILIARIA (3,1 %), ALTA VOLUNTARIA (1,3 %), DERIVACIÓN A OTROS CENTROS (CÁRCEL, HOGAR DE (0,5 %), FUGA DEL PACIENTE (0,4 %) | — | Script 15 (D49) |
| `SEVERIDAD` | PREDICTORA | Entero | Nivel de severidad del GRD (1 a 3) | de 1 a 3 | — | Script 15 (D49) |
| `RIESGO_MORTALIDAD` | PREDICTORA | Entero | Nivel de riesgo de mortalidad del GRD (1 a 3) | de 1 a 3 | — | Script 15 (D49) |
| `ESPECIALIDAD_INTERVENCION` | PREDICTORA | Texto | Especialidad de la intervención del episodio, o SIN INTERVENCIÓN | 48 valores | — | Script 15 (D49) |
| `UCI_UTI` | PREDICTORA | Entero | 1 si algún egreso del episodio pasó por una unidad de cuidados intensivos o intermedios | 0 o 1 | — | Script 15 (D49) |
| `TRASLADO` | PREDICTORA | Entero | 1 si el episodio pasó por más de un hospital (D19) | 0 o 1 | — | Script 15 (D49) |
| `N_DIAGNOSTICOS` | PREDICTORA | Entero | Diagnósticos distintos del egreso | de 0 a 35 | — | Script 15 (D49) |
| `N_PROCEDIMIENTOS` | PREDICTORA | Entero | Procedimientos distintos del egreso | de 0 a 30 | — | Script 15 (D49) |
| `ESPECIALIDAD` | PREDICTORA | Texto | Especialidad médica del episodio, tal cual | 59 valores | — | Script 15 (D49) |
| `TIPO_PROCEDENCIA` | PREDICTORA | Texto | De dónde llega el paciente, tal cual | 18 valores | 984 | Script 15 (D49) |
| `SERVICIO_INGRESO` | PREDICTORA | Texto | Servicio clínico de ingreso, tal cual | 85 valores | 16.539 | Script 15 (D49) |
| `SERVICIO_ALTA` | PREDICTORA | Texto | Servicio clínico de alta, tal cual | 83 valores | 13.834 | Script 15 (D49) |
| `PUEBLO_ORIGINARIO` | PREDICTORA | Texto | SÍ si la etnia nombra un pueblo originario, NO si dice NINGUNO u OTRO | NO (97,8 %), SÍ (2,2 %), SIN DATO (0,0 %) | 3 | Script 15 (D49) |
| `NACIONALIDAD_EXTRANJERA` | PREDICTORA | Texto | SÍ si la nacionalidad no es chilena | NO (93,3 %), SÍ (6,3 %), SIN DATO (0,4 %) | 13.024 | Script 15 (D49) |
| `HOSPITAL` | PREDICTORA | Texto | Código del hospital del egreso. Entra en el análisis principal, y los modelos se entrenan también sin él (D55) | 72 valores | — | Script 15 (D49, D55) |
| `REING_7D` | OBJETIVO | Entero | Reingreso no planificado a 7 días por cualquier causa: 1 sí, 0 no. Todos los casos de estudio tienen dato | 0 o 1 | — | Script 09 (D20, D26, D30) |
| `REING_7D_CDM` | OBJETIVO | Entero | Reingreso no planificado a 7 días con la misma CDM. Sin dato en los partos (CDM 14) | 0 o 1 | 492.333 | Script 09 (D31, D38) |
| `REING_30D` | OBJETIVO | Entero | Reingreso no planificado a 30 días por cualquier causa. Sin dato si el alta ocurrió menos de 60 días antes del cierre del bloque | 0 o 1 | 72.220 | Script 09 (D20, D30) |
| `REING_30D_CDM` | OBJETIVO | Entero | Reingreso no planificado a 30 días con la misma CDM. Sin dato en los partos y en las altas sin dato a 30 días | 0 o 1 | 555.170 | Script 09 (D31, D38) |

## 2. `modelos_codigos.parquet`

Una fila por caso de estudio y código distinto, ordenada por `ID_EGRESO`. Solo tiene los códigos que están en alguna lista de `listas_codigos.parquet`, de cualquier variable y pliegue: los diagnósticos y procedimientos completos y, para la lista agrupada, los diagnósticos en su categoría. Un caso puede no tener ninguna fila. `BLOQUE`, `NIVEL` y `CODIGO` se guardan como categorías (cada valor distinto se guarda una sola vez).

| Columna | Papel | Tipo | Descripción | Valores | Sin dato | Origen |
|---|---|---|---|---|---|---|
| `ID_EGRESO` | IDENTIFICADOR | Entero | Caso de estudio al que pertenece el código. Une esta tabla con modelos_casos.parquet | 3.347.513 distintos | — | Script 06 (actividad 2.1) |
| `BLOQUE` | CODIGO | Texto | DIAGNOSTICO (CIE-10, columnas DIAGNOSTICO1 a DIAGNOSTICO35) o PROCEDIMIENTO (CIE-9-MC, columnas PROCEDIMIENTO1 a PROCEDIMIENTO30) | DIAGNOSTICO (50,6 %), PROCEDIMIENTO (49,4 %) | — | Script 16 (D45) |
| `NIVEL` | CODIGO | Texto | COMPLETO = el código tal como viene. CATEGORIA = el diagnóstico en su categoría (lo que va antes del punto), que solo usa la lista agrupada | COMPLETO (80,2 %), CATEGORIA (19,8 %) | — | Script 16 (D45, D53) |
| `CODIGO` | CODIGO | Texto | El código. Un caso tiene una fila por código distinto, esté en la posición que esté. Solo están los códigos de alguna lista de listas_codigos.parquet. Cada código de la lista elegida pasa a ser una columna sí/no del modelo | 7.417 valores | — | Script 16 (D45, D53) |

Hay 7.448 códigos distintos pero 7.417 textos: 31 textos están con los dos niveles, como `C20`, que es a la vez un código completo y una categoría. Por eso una columna de la matriz se identifica con `BLOQUE`, `NIVEL` y `CODIGO` juntos, nunca con el código solo.

## 3. `listas_codigos.parquet` (script 14)

Una fila por código de cada lista: `VARIABLE` (la variable de reingreso), `LISTA` (`A`, la principal, o una de las de comparación de D53: `C`, `AGRUPADA` y `SIN_FILTRO`), `PLIEGUE` (0 = todo desarrollo; 1 a 5 = el entrenamiento sin ese pliegue), `BLOQUE`, `NIVEL` y `CODIGO`. La lista sin filtro no mira el reingreso, así que no tiene versión por pliegue. Códigos de cada lista:

| Variable | Lista | Todo desarrollo (PLIEGUE 0) | Pliegues 1 a 5 |
|---|---|---|---|
| `REING_7D` | `A` | 108 | 109 a 117 |
| `REING_7D` | `C` | 849 | 752 a 778 |
| `REING_7D` | `AGRUPADA` | 112 | 112 a 119 |
| `REING_7D` | `SIN_FILTRO` | 7.184 | — (no mira el reingreso) |
| `REING_7D_CDM` | `A` | 57 | 53 a 59 |
| `REING_7D_CDM` | `C` | 629 | 538 a 555 |
| `REING_7D_CDM` | `AGRUPADA` | 46 | 44 a 50 |
| `REING_7D_CDM` | `SIN_FILTRO` | 6.975 | — (no mira el reingreso) |
| `REING_30D` | `A` | 424 | 419 a 425 |
| `REING_30D` | `C` | 1.595 | 1.479 a 1.528 |
| `REING_30D` | `AGRUPADA` | 348 | 345 a 352 |
| `REING_30D` | `SIN_FILTRO` | 7.116 | — (no mira el reingreso) |
| `REING_30D_CDM` | `A` | 191 | 188 a 197 |
| `REING_30D_CDM` | `C` | 1.165 | 1.034 a 1.059 |
| `REING_30D_CDM` | `AGRUPADA` | 168 | 161 a 167 |
| `REING_30D_CDM` | `SIN_FILTRO` | 6.913 | — (no mira el reingreso) |

## 4. Receta para armar la matriz

Para la actividad 3.2, con scipy (no está en el entorno del proyecto; se instala con las bibliotecas de los modelos). Las columnas de `X` quedan en el orden de `columnas`, y cada una suma los casos con dato que tienen ese código: los mismos `CASOS` de `filtro_codigos.parquet` para esa variable.

```python
import numpy as np
import pandas as pd
import scipy.sparse as sp

casos = pd.read_parquet("data/processed/modelos_casos.parquet")
codigos = pd.read_parquet("data/processed/modelos_codigos.parquet")
listas = pd.read_parquet("data/processed/listas_codigos.parquet")

variable, lista, pliegue = "REING_30D", "A", 0   # pliegue 0: todo desarrollo; k: el entrenamiento sin el pliegue k
filas = casos[casos[variable].notna()].reset_index(drop=True)   # solo los casos con dato en la variable
columnas = (listas[(listas["VARIABLE"] == variable) & (listas["LISTA"] == lista) & (listas["PLIEGUE"] == pliegue)]
            [["BLOQUE", "NIVEL", "CODIGO"]].reset_index(drop=True))
pares = (codigos.astype({"BLOQUE": str, "NIVEL": str, "CODIGO": str})
         .merge(columnas.reset_index(names="j"), on=["BLOQUE", "NIVEL", "CODIGO"]))   # j: columna de la matriz
pares["i"] = pd.Index(filas["ID_EGRESO"]).get_indexer(pares["ID_EGRESO"])               # i: fila (-1 si no tiene dato)
pares = pares[pares["i"] >= 0]
X = sp.csr_matrix((np.ones(len(pares), dtype=np.int8), (pares["i"], pares["j"])), shape=(len(filas), len(columnas)))
y = filas[variable].to_numpy()
```
