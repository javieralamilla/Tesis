# Partición inicial y reserva del conjunto de prueba (actividad 2.3, script 10)

Generado por `2.3_validacion_particion/scripts/10_particionar.py`. Entrada: `data/processed/grd_etiquetado.parquet`, versión 3 del conjunto analítico. Parámetros: `2.3_validacion_particion/reglas/parametros.csv`. Las decisiones están en `2.3_validacion_particion/bitacora.md`.

El conjunto de prueba se aparta aquí y no se vuelve a abrir hasta la evaluación final: todo lo que sigue (ingeniería de variables, filtro, entrenamiento y ajuste) se hace solo con `desarrollo.parquet`. Las cifras del conjunto de prueba que aparecen en este reporte son las necesarias para comprobar que la partición quedó equilibrada.

## 1. Cómo se reparte

**Unidad de reparto:** el identificador de paciente. Todos los egresos de un identificador quedan en un solo conjunto, también cuando el identificador reúne a más de una persona (3.915 identificadores). Los identificadores del bloque A (2019–2020) y del bloque B (2021–2024) no se enlazan: una persona con un identificador en cada bloque puede quedar en los dos conjuntos.

**Estratos:** los identificadores se separan por bloque y por el patrón de sus variables objetivo, es decir, por las variables en las que alguno de sus casos de estudio tiene reingreso. Los identificadores sin casos de estudio forman su propio estrato.

**Reparto:** dentro de cada estrato, los identificadores se ordenan por su número de casos de estudio con `REING_30D` y por su número de casos de estudio, y uno de cada 5 va al conjunto de prueba. El punto de partida de cada estrato se sortea con la semilla del proyecto (2026), así que la partición es la misma cada vez que se ejecuta el script.

**Esta versión conserva el reparto registrado** (parámetro `reparto` = REGISTRADO; bitácora H34 y D51): cada identificador queda en el conjunto que tenía en la lista registrada, así que el conjunto de prueba reúne a los mismos pacientes. Un sorteo nuevo con la misma semilla cambiaría de conjunto a 967.219 de los 4.035.768 identificadores (23,97 %), porque el reparto depende del lugar de cada identificador en la fila ordenada de su estrato, y ese lugar cambia cuando cambian sus casos de estudio. Por eso, en la sección 5, la parte de cada estrato que va a prueba puede alejarse un poco del 20 %.

## 2. Tamaño de los conjuntos

|  | Desarrollo | Prueba | Total | % en prueba |
|---|---|---|---|---|
| Identificadores de paciente | 3.228.615 | 807.153 | 4.035.768 | 20,00 % |
|   del bloque A | 1.149.566 | 287.391 | 1.436.957 | 20,00 % |
|   del bloque B | 2.079.049 | 519.762 | 2.598.811 | 20,00 % |
| Personas | 3.231.777 | 807.922 | 4.039.699 | 20,00 % |
| Egresos | 4.623.286 | 1.157.342 | 5.780.628 | 20,02 % |
| **Casos de estudio** | 3.347.652 | 836.720 | 4.184.372 | 20,00 % |
|   del bloque A | 1.091.338 | 272.796 | 1.364.134 | 20,00 % |
|   del bloque B | 2.256.314 | 563.924 | 2.820.238 | 20,00 % |

Los egresos que no son caso de estudio acompañan a su identificador, porque sirven para calcular la historia de hospitalizaciones de la persona. Quedan fuera de los dos conjuntos los 20.345 egresos sin persona asignada (sin identificador o con identificador genérico), que no son casos de estudio.

## 3. Tasas de reingreso en cada conjunto

Porcentaje de los casos de estudio con seguimiento suficiente para cada variable. La diferencia está en puntos porcentuales.

| Variable | Definición | Casos en desarrollo | Tasa | Casos en prueba | Tasa | Diferencia |
|---|---|---|---|---|---|---|
| `REING_7D` | 7 días, por cualquier causa | 3.347.652 | 2,067 % | 836.720 | 2,066 % | -0,001 |
| `REING_7D_CDM` | 7 días, relacionado (misma CDM) | 2.855.319 | 1,266 % | 713.886 | 1,258 % | -0,008 |
| `REING_30D` | 30 días, por cualquier causa | 3.275.432 | 5,897 % | 818.579 | 5,900 % | +0,003 |
| `REING_30D_CDM` | 30 días, relacionado (misma CDM) | 2.792.482 | 3,553 % | 698.106 | 3,549 % | -0,004 |

`REING_30D` por año del alta:

| Conjunto | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| Desarrollo | 5,70 % | 5,66 % | 5,62 % | 5,76 % | 6,14 % | 6,45 % |
| Prueba | 5,73 % | 5,62 % | 5,62 % | 5,75 % | 6,15 % | 6,46 % |

## 4. Composición de los casos de estudio

Porcentaje de los casos de estudio de cada conjunto en cada categoría. Las dos columnas deben ser casi iguales. Mayor diferencia de cada tabla, en puntos porcentuales:

| Tabla | Mayor diferencia entre los dos conjuntos |
|---|---|
| Año del alta | 0,09 |
| Bloque de identificador | 0,00 |
| Sexo | 0,02 |
| Edad al ingreso | 0,07 |
| Tipo de ingreso | 0,11 |
| CDM | 0,07 |
| Hospital | 0,08 |

| Año del alta | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| 2019 | 19,25 % | 19,21 % | -0,04 |
| 2020 | 13,35 % | 13,39 % | +0,04 |
| 2021 | 15,20 % | 15,13 % | -0,06 |
| 2022 | 16,85 % | 16,94 % | +0,09 |
| 2023 | 18,40 % | 18,42 % | +0,02 |
| 2024 | 16,96 % | 16,91 % | -0,05 |

| Bloque de identificador | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| A | 32,60 % | 32,60 % | +0,00 |
| B | 67,40 % | 67,40 % | -0,00 |

| Sexo | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| (sin dato) | 0,01 % | 0,01 % | -0,00 |
| HOMBRE | 38,99 % | 39,01 % | +0,02 |
| MUJER | 61,00 % | 60,99 % | -0,02 |

| Edad al ingreso | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| Menos de 1 año | 5,93 % | 5,91 % | -0,02 |
| 1 a 14 años | 10,12 % | 10,16 % | +0,04 |
| 15 a 44 años | 39,57 % | 39,50 % | -0,07 |
| 45 a 64 años | 21,01 % | 20,99 % | -0,02 |
| 65 a 79 años | 16,62 % | 16,67 % | +0,06 |
| 80 años o más | 6,75 % | 6,77 % | +0,01 |

| Tipo de ingreso | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| (sin dato) | 0,01 % | 0,01 % | +0,00 |
| OBSTETRICA | 21,02 % | 20,98 % | -0,04 |
| PROGRAMADA | 20,15 % | 20,07 % | -0,08 |
| URGENCIA | 58,82 % | 58,94 % | +0,11 |

| CDM | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| 01 | 5,59 % | 5,57 % | -0,02 |
| 02 | 0,55 % | 0,55 % | +0,00 |
| 03 | 2,04 % | 2,04 % | -0,01 |
| 04 | 10,33 % | 10,40 % | +0,07 |
| 05 | 7,73 % | 7,76 % | +0,03 |
| 06 | 11,18 % | 11,17 % | -0,01 |
| 07 | 6,49 % | 6,47 % | -0,03 |
| 08 | 9,48 % | 9,50 % | +0,02 |
| 09 | 3,24 % | 3,24 % | +0,01 |
| 10 | 1,50 % | 1,52 % | +0,02 |
| 11 | 5,03 % | 4,99 % | -0,04 |
| 12 | 1,52 % | 1,52 % | +0,00 |
| 13 | 10,37 % | 10,37 % | -0,00 |
| 14 | 14,71 % | 14,68 % | -0,03 |
| 15 | 2,97 % | 2,94 % | -0,03 |
| 16 | 1,36 % | 1,36 % | +0,00 |
| 17 | 0,53 % | 0,53 % | +0,00 |
| 18 | 0,97 % | 0,96 % | -0,01 |
| 19 | 1,65 % | 1,65 % | -0,00 |
| 20 | 0,28 % | 0,28 % | +0,00 |
| 21 | 1,50 % | 1,50 % | +0,00 |
| 22 | 0,98 % | 1,00 % | +0,01 |

La tabla por hospital está en el anexo.

## 5. Estratos

Identificadores de cada estrato y cuántos van al conjunto de prueba. Las columnas de las variables indican si alguno de los casos de estudio del identificador tiene reingreso en esa variable.

| Bloque | Tiene casos de estudio | `REING_30D` | `REING_30D_CDM` | `REING_7D` | `REING_7D_CDM` | Identificadores | En prueba | % |
|---|---|---|---|---|---|---|---|---|
| A | Sí | No | No | No | No | 1.041.156 | 208.232 | 20,00 % |
| A | Sí | Sí | No | No | No | 17.150 | 3.429 | 19,99 % |
| A | Sí | Sí | No | Sí | No | 11.122 | 2.223 | 19,99 % |
| A | Sí | Sí | Sí | No | No | 18.049 | 3.611 | 20,01 % |
| A | Sí | Sí | Sí | Sí | No | 1.232 | 247 | 20,05 % |
| A | Sí | Sí | Sí | Sí | Sí | 13.289 | 2.657 | 19,99 % |
| A | No | — | — | — | — | 334.959 | 66.992 | 20,00 % |
| B | Sí | No | No | No | No | 1.905.931 | 381.183 | 20,00 % |
| B | Sí | Sí | No | No | No | 36.787 | 7.358 | 20,00 % |
| B | Sí | Sí | No | Sí | No | 21.100 | 4.222 | 20,01 % |
| B | Sí | Sí | Sí | No | No | 39.570 | 7.916 | 20,01 % |
| B | Sí | Sí | Sí | Sí | No | 2.911 | 583 | 20,03 % |
| B | Sí | Sí | Sí | Sí | Sí | 28.055 | 5.609 | 19,99 % |
| B | No | — | — | — | — | 564.457 | 112.891 | 20,00 % |

## 6. Parámetros

| Parámetro | Valor | Descripción |
|---|---|---|
| `semilla` | `2026` | Semilla fija del proyecto para todo componente aleatorio: la partición inicial y, en las etapas siguientes, la validación cruzada y los modelos (D28) |
| `prueba_una_de_cada` | `5` | Tamaño del conjunto de prueba: uno de cada N identificadores de paciente de cada estrato. 5 = 20 % para prueba y 80 % para desarrollo (D28) |
| `variable_principal` | `REING_30D` | Variable objetivo principal. Dentro de cada estrato, los identificadores se ordenan por su número de casos de estudio con reingreso en esta variable antes de tomar uno de cada N (D28) |
| `anios_entrenamiento_temporal` | `2019|2020|2021|2022` | Años del alta de los casos de estudio de desarrollo con que se entrena el modelo en la validación temporal interna, separados por una barra vertical (D37, D40) |
| `anios_evaluacion_temporal` | `2023|2024` | Años del alta de los casos de estudio de desarrollo con que se evalúa ese modelo (D37, D40) |
| `paciente_visto_egresos` | `TODOS` | Un caso de evaluación es de un paciente ya visto si su identificador tiene un egreso en un año de entrenamiento de su mismo bloque. TODOS = cualquier egreso, sea o no caso de estudio, como pide la revisión del profesor guía del 13 de octubre de 2026. CASOS = solo un caso de estudio (D40) |
| `reparto` | `REGISTRADO` | Cómo se asigna el conjunto de cada identificador. NUEVO = se sortea con la semilla, como indican los parámetros anteriores (D28). REGISTRADO = cada identificador queda en el conjunto de la lista registrada (data/processed/particion_identificadores.parquet, con el hash de la última versión de docs/version_particion.csv), para que un cambio del conjunto analítico que no agrega identificadores no cambie a los pacientes del conjunto de prueba (H34, D51) |
| `pliegues_validacion_cruzada` | `5` | Número de pliegues de la validación cruzada dentro del conjunto de desarrollo. Todos los casos de un identificador de paciente quedan en el mismo pliegue, repartidos con el método de la partición: estratos por bloque y por el patrón de las variables objetivo, orden por los reingresos de variable_principal y punto de partida al azar con la semilla (D37, D52) |

## 7. Archivos y versión

| Archivo | Contenido |
|---|---|
| `data/processed/particion.parquet` | Una fila por egreso con persona: `ID_EGRESO`, `ID_PACIENTE`, `BLOQUE_ID` y `CONJUNTO` (`DESARROLLO` o `PRUEBA`). |
| `data/processed/particion_identificadores.parquet` | La lista de identificadores de cada conjunto: `ID_PACIENTE`, `BLOQUE_ID` y `CONJUNTO`. |
| `data/processed/desarrollo.parquet` | Egresos del conjunto de desarrollo, con todas las columnas del conjunto analítico. Es el único archivo que usan las etapas siguientes. |
| `data/reserva/prueba.parquet` | Egresos del conjunto de prueba, con las mismas columnas. Es de solo lectura y no se abre hasta la evaluación final. |

Versión 3 de la partición, registrada el 2026-11-02 en `docs/version_particion.csv`, sobre la versión 3 del conjunto analítico.

| Archivo | SHA-256 |
|---|---|
| `grd_etiquetado.parquet` | `3bf2bb4e7513daf6d580a9e025cdd00d55456602ccb7d78d60b722e8fe402bd2` |
| `particion_identificadores.parquet` | `5bdb99e4f7d9d9a7a9004545ce9e93c85fc172de6e93d2ff111577a42ac5f28b` |
| `desarrollo.parquet` | `50f07908f35df51c31077971d0aafaf69182c3baea926af34b00d6fff41229b1` |
| `prueba.parquet` | `4ee4f9ba09d530723055772af21319e22f89da524a70d14f4659d173ca415c21` |

El identificador de paciente (`ID_PACIENTE`) es también el grupo que debe usar la validación cruzada agrupada dentro del conjunto de desarrollo.

## 8. Verificaciones

- Todos los egresos de un identificador de paciente están en un solo conjunto: **sí**.
- Todos los egresos de una persona están en un solo conjunto: **sí**.
- Ningún identificador de paciente aparece en los dos bloques: **sí**.
- Todos los casos de estudio quedaron asignados a un conjunto: **sí**.
- Cada identificador quedó en el conjunto que tenía en la lista registrada de la partición: **sí**.
- El conjunto de prueba tiene entre 19,5 % y 20,5 % de los casos de estudio: **sí**.
- La tasa de cada variable objetivo difiere en menos de 0,05 puntos porcentuales entre los dos conjuntos: **sí**.
- Ninguna categoría de año, bloque, sexo, edad, tipo de ingreso, CDM u hospital difiere en más de 0,5 puntos porcentuales: **sí**.
- Cada archivo contiene exactamente los egresos asignados a su conjunto, en el orden del conjunto analítico: **sí**.
- Ningún identificador de paciente está en los dos archivos: **sí**.
- Los dos archivos tienen las mismas columnas que el conjunto analítico, con el mismo tipo de dato: **sí**.
- Contenido idéntico al del conjunto analítico en 6 columnas de control: **sí**.
- La suma de filas de los dos archivos es el número de egresos con persona: **sí**.
- El archivo del conjunto de prueba quedó como solo lectura: **sí**.
- La lista de identificadores escrita tiene el mismo hash que la registrada: el reparto no cambió: **sí**.

## Anexo. Casos de estudio por hospital

Porcentaje de los casos de estudio de cada conjunto que corresponde a cada hospital. Los nombres son los de la tabla maestra del DEIS.

| Hospital | Desarrollo | Prueba | Diferencia |
|---|---|---|---|
| 101100 Hospital Dr. Juan Noé Crevanni (Arica) | 2,01 % | 1,98 % | -0,03 |
| 102100 Hospital Dr. Ernesto Torres Galdames (Iquique) | 2,13 % | 2,13 % | +0,00 |
| 103100 Hospital Dr. Leonardo Guzmán (Antofagasta) | 2,29 % | 2,32 % | +0,02 |
| 103101 Hospital Dr. Carlos Cisternas (Calama) | 1,17 % | 1,17 % | +0,00 |
| 104100 Hospital San José del Carmen (Copiapó) | 1,48 % | 1,48 % | -0,00 |
| 104103 Hospital Provincial del Huasco Monseñor Fernando Ariztía Ruiz (Vallenar) | 0,63 % | 0,63 % | -0,00 |
| 105100 Hospital San Juan de Dios (La Serena) | 1,59 % | 1,61 % | +0,01 |
| 105101 Hospital San Pablo (Coquimbo) | 1,72 % | 1,72 % | -0,00 |
| 105102 Hospital Dr. Antonio Tirado Lanas (Ovalle) | 1,04 % | 1,05 % | +0,01 |
| 106100 Hospital Carlos Van Buren (Valparaíso) | 1,86 % | 1,80 % | -0,05 |
| 106102 Hospital Dr. Eduardo Pereira Ramírez (Valparaíso) | 0,53 % | 0,52 % | -0,01 |
| 106103 Hospital Claudio Vicuña (San Antonio) | 0,82 % | 0,81 % | -0,01 |
| 107100 Hospital Dr. Gustavo Fricke (Viña del Mar) | 2,34 % | 2,34 % | -0,01 |
| 107101 Hospital San Martín (Quillota) | 1,08 % | 1,09 % | +0,01 |
| 107102 Hospital de Quilpué | 0,82 % | 0,81 % | -0,00 |
| 108100 Hospital de San Camilo (San Felipe) | 1,20 % | 1,20 % | -0,00 |
| 108101 Hospital San Juan de Dios (Los Andes) | 0,98 % | 0,97 % | -0,02 |
| 109100 Complejo Hospitalario San José (Santiago, Independencia) | 2,79 % | 2,80 % | +0,01 |
| 109101 Hospital Clínico de Niños Dr. Roberto del Río (Santiago, Independencia) | 0,91 % | 0,91 % | -0,01 |
| 110100 Hospital San Juan de Dios (Santiago, Santiago) | 2,39 % | 2,35 % | -0,03 |
| 110110 Instituto Traumatológico Dr. Teodoro Gebauer | 0,14 % | 0,13 % | -0,01 |
| 110120 Hospital Dr. Félix Bulnes Cerda (Santiago, Quinta Normal) | 2,43 % | 2,44 % | +0,01 |
| 110130 Hospital Adalberto Steeger (Talagante) | 0,74 % | 0,73 % | -0,01 |
| 110150 Hospital San José (Melipilla) | 0,86 % | 0,87 % | +0,02 |
| 111100 Hospital Clínico San Borja-Arriarán (Santiago, Santiago) | 2,02 % | 2,04 % | +0,02 |
| 111101 Hospital Clínico Metropolitano El Carmen Doctor Luis Valentín Ferrada | 2,03 % | 2,04 % | +0,01 |
| 111195 Hospital de Urgencia Asistencia Pública Dr. Alejandro del Río | 1,18 % | 1,18 % | +0,00 |
| 112100 Hospital Del Salvador (Santiago, Providencia) | 1,23 % | 1,26 % | +0,03 |
| 112101 Hospital Dr. Luis Tisné B. (Santiago, Peñalolén) | 1,84 % | 1,84 % | -0,00 |
| 112102 Hospital de Niños Dr. Luis Calvo Mackenna (Santiago, Providencia) | 0,84 % | 0,85 % | +0,01 |
| 112103 Instituto Nacional de Enfermedades Respiratorias y Cirugía Torácica | 0,43 % | 0,41 % | -0,02 |
| 112104 Instituto de Neurocirugía Dr. Alfonso Asenjo | 0,43 % | 0,41 % | -0,02 |
| 113100 Hospital Barros Luco Trudeau (Santiago, San Miguel) | 3,15 % | 3,23 % | +0,08 |
| 113130 Hospital Dr. Exequiel González Cortés (Santiago, San Miguel) | 0,89 % | 0,89 % | +0,00 |
| 113150 Hospital San Luis (Buin) | 0,60 % | 0,58 % | -0,02 |
| 113180 Hospital El Pino (Santiago, San Bernardo) | 1,57 % | 1,59 % | +0,02 |
| 114101 Complejo Hospitalario Dr. Sótero del Río (Santiago, Puente Alto) | 4,56 % | 4,49 % | -0,08 |
| 114103 Hospital Padre Alberto Hurtado (San Ramón) | 1,97 % | 1,96 % | -0,00 |
| 114105 Hospital Clínico Metropolitano La Florida Dra. Eloisa Díaz Inzunza | 1,89 % | 1,89 % | -0,00 |
| 115100 Hospital Regional de Rancagua | 2,59 % | 2,61 % | +0,02 |
| 115107 Hospital San Juan de Dios (San Fernando) | 0,91 % | 0,93 % | +0,01 |
| 115110 Hospital de Santa Cruz | 0,62 % | 0,64 % | +0,02 |
| 116100 Hospital San Juan de Dios (Curicó) | 1,66 % | 1,64 % | -0,02 |
| 116105 Hospital Dr. César Garavagno Burotto (Talca) | 3,21 % | 3,23 % | +0,02 |
| 116107 Hospital de Constitución | 0,05 % | 0,05 % | +0,00 |
| 116108 Hospital Presidente Carlos Ibáñez del Campo (Linares) | 1,41 % | 1,40 % | -0,00 |
| 116110 Hospital San José (Parral) | 0,51 % | 0,52 % | +0,01 |
| 116111 Hospital San Juan de Dios (Cauquenes) | 0,08 % | 0,08 % | +0,00 |
| 117101 Hospital Clínico Herminda Martín (Chillán) | 2,24 % | 2,22 % | -0,01 |
| 117102 Hospital de San Carlos | 0,84 % | 0,82 % | -0,01 |
| 118100 Hospital Clínico Regional Dr. Guillermo Grant Benavente (Concepción) | 3,47 % | 3,47 % | -0,01 |
| 118105 Hospital San José (Coronel) | 0,73 % | 0,72 % | -0,01 |
| 118106 Hospital de Lota | 0,15 % | 0,15 % | -0,00 |
| 119100 Hospital Las Higueras (Talcahuano) | 2,43 % | 2,41 % | -0,02 |
| 119101 Hospital de Tomé | 0,13 % | 0,13 % | +0,00 |
| 119102 Hospital Penco - Lirquén | 0,05 % | 0,06 % | +0,00 |
| 120101 Complejo Asistencial Dr. Víctor Ríos Ruiz (Los Ángeles) | 3,06 % | 3,11 % | +0,04 |
| 121109 Hospital Dr. Hernán Henríquez Aravena (Temuco) | 2,90 % | 2,93 % | +0,03 |
| 121110 Hospital Dr. Abraham Godoy (Lautaro) | 0,32 % | 0,32 % | -0,00 |
| 121114 Hospital Intercultural de Nueva Imperial | 0,51 % | 0,51 % | -0,00 |
| 121117 Hospital de Pitrufquén | 0,31 % | 0,30 % | -0,00 |
| 121121 Hospital de Villarrica | 0,48 % | 0,49 % | +0,01 |
| 122100 Hospital Clínico Regional (Valdivia) | 2,20 % | 2,22 % | +0,03 |
| 123100 Hospital Base San José de Osorno | 2,02 % | 2,01 % | -0,01 |
| 124105 Hospital de Puerto Montt | 2,82 % | 2,86 % | +0,04 |
| 125100 Hospital Regional (Coihaique) | 1,04 % | 1,07 % | +0,03 |
| 126100 Hospital Clínico de Magallanes Dr. Lautaro Navarro Avaria | 1,30 % | 1,30 % | -0,00 |
| 128109 Hospital Provincial Dr. Rafael Avaría (Curanilahue) | 0,63 % | 0,64 % | +0,01 |
| 129100 Hospital Dr. Mauricio Heyermann (Angol) | 0,99 % | 0,99 % | -0,00 |
| 129106 Hospital San José (Victoria) | 0,79 % | 0,76 % | -0,04 |
| 133150 Hospital de Castro | 0,81 % | 0,77 % | -0,05 |
| 200717 (sin nombre en la tabla maestra) | 0,12 % | 0,13 % | +0,01 |
