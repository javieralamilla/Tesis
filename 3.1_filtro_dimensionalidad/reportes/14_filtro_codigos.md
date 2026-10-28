# Filtro de dimensionalidad (actividad 3.1, script 14)

Generado por `3.1_filtro_dimensionalidad/scripts/14_filtro_codigos.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 2 de la partición (SHA-256 `9546c8c7e80f634295e7c0538173661884aa6ce602e201a3cbd8ae615912abbb`). Salidas: `data/processed/filtro_codigos.parquet` (todos los códigos) y `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv` (la lista fija). No se abre el conjunto de prueba. Las decisiones están en `3.1_filtro_dimensionalidad/bitacora.md` (D45, H30 y H31).

**Filtro:** para cada variable de reingreso, pasa un código si su V de Cramér es mayor o igual a 0,010 y lo tienen al menos 100 casos de estudio con dato en esa variable. Se usa el código tal como viene (por ejemplo, E11.9), en cualquier posición y una vez por caso. El filtro se calcula una sola vez, con todo el conjunto de desarrollo, y la lista queda fija: las etapas siguientes la aplican sin recalcularla (propuesta, Etapa 3).

## 1. Códigos de los casos de estudio

| Bloque | Códigos distintos | Pares caso–código | Promedio por caso |
|---|---|---|---|
| Diagnósticos (CIE-10) | 16.336 | 18.458.052 | 5,50 |
| Procedimientos (CIE-9-MC) | 3.753 | 29.327.510 | 8,74 |

Casos de estudio de desarrollo: 3.354.118.

## 2. Códigos que pasan el filtro

Cada variable usa los casos de estudio con dato en ella: las variables de 30 días no incluyen los casos sin 60 días de seguimiento (D30), y las de misma CDM no incluyen los partos (D38).

| Variable | Casos con dato | Reingresos | Diagnósticos que pasan | Procedimientos que pasan | Total |
|---|---|---|---|---|---|
| `REING_7D` | 3.354.118 | 69.299 (2,07 %) | 60 (53 suben y 7 bajan) | 48 (36 suben y 12 bajan) | 108 |
| `REING_7D_CDM` | 2.861.785 | 36.200 (1,26 %) | 43 (42 suben y 1 baja) | 14 (11 suben y 3 bajan) | 57 |
| `REING_30D` | 3.281.764 | 193.589 (5,90 %) | 281 (253 suben y 28 bajan) | 142 (112 suben y 30 bajan) | 423 |
| `REING_30D_CDM` | 2.798.814 | 99.444 (3,55 %) | 131 (126 suben y 5 bajan) | 59 (41 suben y 18 bajan) | 190 |

## 3. Sensibilidad de los umbrales

Cuántos códigos pasarían con cada combinación de umbrales: total (diagnósticos + procedimientos). Solo se cuentan; la lista fija es la de los umbrales principales.

| V mínima | Casos mínimos | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| 0,005 | 50 | 417 (277 + 140) | 208 (142 + 66) | 1.076 (749 + 327) | 603 (414 + 189) |
| 0,005 | 100 | 417 (277 + 140) | 206 (140 + 66) | 1.074 (748 + 326) | 601 (412 + 189) |
| 0,005 | 500 | 411 (274 + 137) | 194 (130 + 64) | 1.034 (718 + 316) | 571 (387 + 184) |
| 0,010 | 50 | 108 (60 + 48) | 58 (44 + 14) | 423 (281 + 142) | 190 (131 + 59) |
| 0,010 (principal) | 100 | 108 (60 + 48) | 57 (43 + 14) | 423 (281 + 142) | 190 (131 + 59) |
| 0,010 | 500 | 108 (60 + 48) | 53 (39 + 14) | 421 (280 + 141) | 188 (129 + 59) |
| 0,020 | 50 | 19 (7 + 12) | 10 (8 + 2) | 145 (83 + 62) | 54 (36 + 18) |
| 0,020 | 100 | 19 (7 + 12) | 10 (8 + 2) | 145 (83 + 62) | 54 (36 + 18) |
| 0,020 | 500 | 19 (7 + 12) | 10 (8 + 2) | 145 (83 + 62) | 54 (36 + 18) |

## 4. Cuánto reingreso necesita un código para pasar

La V mide cuánto explica el código del reingreso de todos los casos, así que un código con pocos casos necesita una diferencia muy grande para llegar a 0,010 (H30). La tabla da la tasa de reingreso mínima con que pasaría un código que sube el riesgo, según cuántos casos lo tienen. Un código que baja el riesgo necesita muchos casos para pasar, aunque ninguno de ellos reingrese (última fila).

| Casos con el código | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|
| 100 | 28,1 % | 20,2 % | 48,6 % | 34,5 % |
| 250 | 18,5 % | 13,2 % | 32,9 % | 23,1 % |
| 500 | 13,7 % | 9,7 % | 25,0 % | 17,4 % |
| 1.000 | 10,3 % | 7,2 % | 19,4 % | 13,3 % |
| 2.500 | 7,3 % | 5,0 % | 14,4 % | 9,7 % |
| 5.000 | 5,7 % | 3,9 % | 11,9 % | 7,9 % |
| 10.000 | 4,7 % | 3,2 % | 10,2 % | 6,6 % |
| 25.000 | 3,7 % | 2,5 % | 8,6 % | 5,5 % |
| 100.000 | 2,9 % | 1,9 % | 7,2 % | 4,5 % |
| Tasa de toda la variable | 2,07 % | 1,26 % | 5,90 % | 3,55 % |
| Casos que necesita un código que baja el riesgo | 15.824 | 22.165 | 5.227 | 7.577 |

## 5. Los códigos con mayor V

**`REING_7D`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `99.04` | TRANSFUSION CONCENTRADO HEMATIES | 179.050 | 3,75 % | 1,97 % | 0,0281 |
| `N18.5` | Enfermedad renal crónica, estadio 5 | 78.041 | 4,64 % | 2,00 % | 0,0280 |
| `93.18` | EJERCICIO RESPIRATORIO | 556.717 | 2,88 % | 1,90 % | 0,0254 |
| `39.95` | HEMODIALISIS | 56.601 | 4,74 % | 2,02 % | 0,0246 |
| `93.96` | ENRIQUECIMIENTO OXIGENO OTRO | 467.396 | 2,93 % | 1,93 % | 0,0243 |
| `87.44` | RADIOGRAFIA TORAX RUTINARIA | 502.056 | 2,88 % | 1,92 % | 0,0241 |
| `C91.0` | Leucemia linfoblástica aguda (Todas) | 9.184 | 8,48 % | 2,05 % | 0,0236 |
| `Z99.2` | Dependencia de diálisis renal | 43.383 | 4,92 % | 2,03 % | 0,0230 |
| `93.94` | AEROSOLTERAPIA | 297.171 | 3,08 % | 1,97 % | 0,0223 |
| `89.66` | GASOMETRIA VENA | 403.871 | 2,92 % | 1,95 % | 0,0222 |

**`REING_7D`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `Z37.0` | Nacido vivo, único | 481.299 | 0,77 % | 2,28 % | 0,0373 |
| `73.59` | PARTO ASISTIDO MANUALMENTE.OTRO | 265.132 | 0,54 % | 2,20 % | 0,0315 |
| `O80.0` | Parto único espontáneo, presentación cefálica de vértice | 235.131 | 0,52 % | 2,18 % | 0,0298 |
| `99.24` | INYECCION HORMONA OTRA | 296.147 | 0,82 % | 2,19 % | 0,0274 |
| `03.91` | INYECCION ANESTESICO CANAL ESPINAL PARA ANALGESIA | 228.168 | 0,81 % | 2,16 % | 0,0238 |
| `75.69` | REPARACION DESGARRO OBSTETRICO ACTUAL OTRO.OTRO | 135.195 | 0,57 % | 2,13 % | 0,0216 |
| `O70.0` | Desgarro perineal de primer grado durante el parto | 110.638 | 0,52 % | 2,12 % | 0,0201 |
| `Z38.0` | Producto único, nacido en hospital | 143.984 | 0,78 % | 2,12 % | 0,0192 |
| `75.34` | MONITORIZACION FETO OTRA | 498.965 | 1,43 % | 2,18 % | 0,0187 |
| `74.1` | CESAREA CERVICAL BAJA | 211.814 | 1,07 % | 2,13 % | 0,0183 |

**`REING_7D_CDM`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `75.34` | MONITORIZACION FETO OTRA | 86.954 | 4,18 % | 1,17 % | 0,0461 |
| `88.78` | ECOGRAFIA UTERO GRAVIDO | 114.569 | 3,61 % | 1,17 % | 0,0429 |
| `O99.2` | Enfermedades endocrinas, de la nutrición y del metabolismo que complican el embarazo, el parto y el puerperio | 47.392 | 3,90 % | 1,22 % | 0,0306 |
| `Z35.8` | Supervisión de otros embarazos de alto riesgo | 10.276 | 6,26 % | 1,25 % | 0,0268 |
| `O36.5` | Atención materna por déficit del crecimiento fetal | 6.115 | 7,65 % | 1,25 % | 0,0265 |
| `O14.0` | Preeclampsia moderada | 2.138 | 11,27 % | 1,26 % | 0,0245 |
| `O99.0` | Anemia que complica el embarazo, el parto y el puerperio | 14.342 | 4,69 % | 1,25 % | 0,0217 |
| `O00.9` | Embarazo ectópico, no especificado | 4.300 | 7,44 % | 1,26 % | 0,0214 |
| `O21.0` | Hiperemesis gravídica leve | 2.617 | 8,75 % | 1,26 % | 0,0203 |
| `O13` | Hipertensión gestacional [inducida por el embarazo] sin proteinuria significativa | 8.565 | 5,39 % | 1,25 % | 0,0202 |

**`REING_7D_CDM`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `99.21` | INYECCION ANTIBIOTICO | 1.310.943 | 1,07 % | 1,43 % | 0,0164 |
| `51.23` | COLECISTECTOMIA LAPAROSCOPICA | 112.582 | 0,40 % | 1,30 % | 0,0157 |
| `K35.8` | Apendicitis aguda, otra y no especificada | 72.360 | 0,41 % | 1,29 % | 0,0124 |
| `96.59` | IRRIGACION HERIDA OTRA | 330.215 | 0,95 % | 1,31 % | 0,0101 |

**`REING_30D`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `N18.5` | Enfermedad renal crónica, estadio 5 | 76.223 | 15,31 % | 5,68 % | 0,0616 |
| `99.04` | TRANSFUSION CONCENTRADO HEMATIES | 175.050 | 11,91 % | 5,56 % | 0,0606 |
| `93.18` | EJERCICIO RESPIRATORIO | 544.630 | 8,94 % | 5,29 % | 0,0575 |
| `99.17` | INYECCION INSULINA | 287.700 | 10,22 % | 5,48 % | 0,0568 |
| `I10` | Hipertensión esencial (primaria) | 892.119 | 8,02 % | 5,11 % | 0,0550 |
| `87.44` | RADIOGRAFIA TORAX RUTINARIA | 491.852 | 8,92 % | 5,37 % | 0,0539 |
| `39.95` | HEMODIALISIS | 55.244 | 15,58 % | 5,73 % | 0,0537 |
| `N17.9` | Insuficiencia renal aguda, no especificada | 128.359 | 11,70 % | 5,66 % | 0,0497 |
| `87.41` | TOMOGRAFIA AXIAL COMPUTERIZADA TORAX | 336.417 | 9,34 % | 5,51 % | 0,0493 |
| `93.94` | AEROSOLTERAPIA | 291.516 | 9,59 % | 5,54 % | 0,0489 |

**`REING_30D`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `Z37.0` | Nacido vivo, único | 472.069 | 1,43 % | 6,65 % | 0,0777 |
| `73.59` | PARTO ASISTIDO MANUALMENTE.OTRO | 260.186 | 1,06 % | 6,32 % | 0,0603 |
| `O80.0` | Parto único espontáneo, presentación cefálica de vértice | 230.745 | 1,02 % | 6,27 % | 0,0569 |
| `99.24` | INYECCION HORMONA OTRA | 290.205 | 1,63 % | 6,31 % | 0,0564 |
| `03.91` | INYECCION ANESTESICO CANAL ESPINAL PARA ANALGESIA | 223.770 | 1,63 % | 6,21 % | 0,0490 |
| `74.1` | CESAREA CERVICAL BAJA | 207.694 | 1,89 % | 6,17 % | 0,0442 |
| `89.26` | EXAMEN GINECOLOGICO | 326.946 | 2,93 % | 6,23 % | 0,0419 |
| `75.69` | REPARACION DESGARRO OBSTETRICO ACTUAL OTRO.OTRO | 132.566 | 1,10 % | 6,10 % | 0,0418 |
| `75.34` | MONITORIZACION FETO OTRA | 489.385 | 3,57 % | 6,31 % | 0,0414 |
| `Z38.0` | Producto único, nacido en hospital | 141.667 | 1,47 % | 6,10 % | 0,0399 |

**`REING_30D_CDM`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `75.34` | MONITORIZACION FETO OTRA | 85.267 | 12,73 % | 3,26 % | 0,0878 |
| `88.78` | ECOGRAFIA UTERO GRAVIDO | 112.191 | 10,70 % | 3,25 % | 0,0789 |
| `O99.2` | Enfermedades endocrinas, de la nutrición y del metabolismo que complican el embarazo, el parto y el puerperio | 46.338 | 12,27 % | 3,41 % | 0,0611 |
| `O24.4` | Diabetes mellitus que se origina con el embarazo | 29.631 | 14,22 % | 3,44 % | 0,0596 |
| `O34.3` | Atención materna por incompetencia del cuello uterino | 9.057 | 17,94 % | 3,51 % | 0,0443 |
| `Z35.8` | Supervisión de otros embarazos de alto riesgo | 10.047 | 16,68 % | 3,51 % | 0,0426 |
| `O60.0` | Trabajo de parto prematuro sin parto | 11.646 | 14,47 % | 3,51 % | 0,0381 |
| `O10.0` | Hipertensión esencial preexistente que complica el embarazo, el parto y el puerperio | 9.394 | 15,22 % | 3,51 % | 0,0366 |
| `O36.5` | Atención materna por déficit del crecimiento fetal | 6.010 | 16,62 % | 3,52 % | 0,0328 |
| `O30.0` | Embarazo doble | 3.055 | 21,77 % | 3,53 % | 0,0325 |

**`REING_30D_CDM`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `51.23` | COLECISTECTOMIA LAPAROSCOPICA | 110.114 | 0,90 % | 3,66 % | 0,0290 |
| `K35.8` | Apendicitis aguda, otra y no especificada | 70.620 | 0,75 % | 3,63 % | 0,0243 |
| `47.01` | APENDICECTOMIA.LAPAROSCOPICA | 56.639 | 1,00 % | 3,61 % | 0,0198 |
| `99.21` | INYECCION ANTIBIOTICO | 1.281.581 | 3,22 % | 3,84 % | 0,0166 |
| `99.83` | FOTOTERAPIA OTRA | 52.603 | 1,35 % | 3,60 % | 0,0165 |
| `47.09` | APENDICECTOMIA.OTRA | 48.649 | 1,26 % | 3,59 % | 0,0164 |
| `93.59` | INMOVILIZACION,PRESION Y CUIDADO HERIDA.OTRA | 268.285 | 2,64 % | 3,65 % | 0,0160 |
| `88.71` | ECOENCEFALOGRAFIA | 48.506 | 1,42 % | 3,59 % | 0,0153 |
| `69.02` | LEGRADO Y DILATACION UTERO POSTPARTO O TRAS ABORTO | 36.265 | 1,29 % | 3,58 % | 0,0140 |
| `99.29` | INYECCION SUSTANCIA TERAPEUTICA O PROFILACTICA.OTRA | 1.922.950 | 3,38 % | 3,93 % | 0,0139 |

## 6. Códigos que pasan en varias variables

| Bloque | Pasan en alguna variable | En 4 | En 3 | En 2 | En 1 |
|---|---|---|---|---|---|
| Diagnósticos (CIE-10) | 337 | 5 | 45 | 73 | 214 |
| Procedimientos (CIE-9-MC) | 153 | 9 | 20 | 43 | 81 |

## 7. Códigos que pasan y cambian con los años

Códigos que pasan cuya frecuencia (porcentaje de los casos de estudio del año que tienen el código) varía más del triple entre el año de menor y el de mayor frecuencia (H31). El filtro no cambia, pero ayuda a interpretar la validación temporal.

| Variable | Diagnósticos (CIE-10) | Procedimientos (CIE-9-MC) |
|---|---|---|
| `REING_7D` | 1 de 60 | 0 de 48 |
| `REING_7D_CDM` | 4 de 43 | 0 de 14 |
| `REING_30D` | 17 de 281 | 10 de 142 |
| `REING_30D_CDM` | 4 de 131 | 1 de 59 |

De esos 30 códigos (contando una vez los que pasan en varias variables), los doce con la mayor diferencia entre su año de mayor y su año de menor frecuencia:

| Código | Descripción | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Pasa en |
|---|---|---|---|---|---|---|---|---|
| `90.39` | EXAMEN MICROSCOPICO ORL.OTRO | 3,390 % | 19,392 % | 39,288 % | 37,975 % | 19,489 % | 10,609 % | `REING_30D`, `REING_30D_CDM` |
| `99.84` | AISLAMIENTO | 2,522 % | 6,785 % | 10,118 % | 7,525 % | 4,459 % | 4,164 % | `REING_30D` |
| `93.83` | TERAPIA OCUPACIONAL | 1,606 % | 2,361 % | 4,228 % | 4,266 % | 4,963 % | 5,586 % | `REING_30D` |
| `Z03.8` | Observación por sospecha de otras enfermedades y afecciones | 1,005 % | 3,884 % | 2,031 % | 1,377 % | 0,953 % | 0,995 % | `REING_30D` |
| `J96.09` | Insuficiencia respiratoria aguda, Tipo no especificado | 1,239 % | 1,788 % | 3,160 % | 3,126 % | 3,980 % | 4,014 % | `REING_7D`, `REING_7D_CDM`, `REING_30D`, `REING_30D_CDM` |
| `J96.00` | Insuficiencia respiratoria aguda, Tipo I (hipoxémica) | 0,395 % | 1,107 % | 3,010 % | 1,709 % | 2,050 % | 2,125 % | `REING_30D` |
| `96.72` | VENTILACION MECANICA CONTINUA OTRA.DURANTE 96 HORAS O MAS | 0,720 % | 1,329 % | 2,296 % | 1,231 % | 1,103 % | 1,050 % | `REING_30D` |
| `93.75` | ENTRENAMIENTO Y TERAPIA HABLA OTRO | 0,411 % | 0,671 % | 1,185 % | 1,255 % | 1,598 % | 1,817 % | `REING_30D` |
| `N17.8` | Otras insuficiencias renales agudas | 0,492 % | 0,656 % | 0,875 % | 1,280 % | 1,411 % | 1,734 % | `REING_30D` |
| `E55.9` | Deficiencia de vitamina D, no especificada | 0,128 % | 0,271 % | 0,482 % | 0,617 % | 0,777 % | 0,977 % | `REING_30D` |
| `88.43` | ARTERIOGRAFIA ARTERIA PULMONAR | 0,340 % | 0,734 % | 1,163 % | 0,811 % | 0,790 % | 0,799 % | `REING_30D` |
| `38.97` | COLOCACION CATETER VENOSO CENTRAL MEDIANTE GUIADO | 0,190 % | 0,290 % | 0,618 % | 0,657 % | 0,760 % | 0,897 % | `REING_30D` |

## 8. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `variables_objetivo` | `REING_7D / REING_7D_CDM / REING_30D / REING_30D_CDM` | Variables de reingreso para las que se calcula el filtro, separadas por una barra vertical. Cada una tiene su propia lista de códigos (D45) |
| `nivel_codigo` | `COMPLETO` | COMPLETO = el código tal como viene (E11.9). CATEGORIA = solo la categoría, lo que va antes del punto (E11 en los diagnósticos y 99 en los procedimientos), como la columna «Categoría» de las tablas del DEIS (D45) |
| `v_minima` | `0,01` | Umbral del tamaño de efecto: pasa un código cuya V de Cramér con la variable de reingreso sea mayor o igual a este valor (Etapa 3 de la propuesta y D45) |
| `casos_minimos` | `100` | Prevalencia mínima: pasa un código que tengan al menos estos casos de estudio, contados entre los que tienen dato en la variable (Etapa 3 de la propuesta y D45) |
| `v_sensibilidad` | `0,005 / 0,01 / 0,02` | Umbrales de V del análisis de sensibilidad, separados por una barra vertical. Solo se cuenta cuántos códigos pasarían: la lista fija usa v_minima (D45) |
| `casos_sensibilidad` | `50 / 100 / 500` | Mínimos de casos del análisis de sensibilidad. Solo se cuenta cuántos códigos pasarían: la lista fija usa casos_minimos (D45) |

## 9. Archivos de salida

`data/processed/filtro_codigos.parquet` tiene una fila por variable de reingreso y código, pase o no el filtro. `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv` tiene solo los que pasan, sin las columnas `CHI2`, `VALOR_P` y `PASA`; se lee con `sep=";"`, `decimal=","` y la columna `CODIGO` como texto (los procedimientos pueden empezar con cero, como `00.14`).

| Columna | Contenido |
|---|---|
| `VARIABLE` | Variable de reingreso. |
| `BLOQUE` | `DIAGNOSTICO` (CIE-10) o `PROCEDIMIENTO` (CIE-9-MC). |
| `CODIGO` | El código. |
| `DESCRIPCION` | Descripción según las tablas del DEIS (`Datos/Tablas auxiliares`). |
| `CASOS` | Casos de estudio con dato en la variable que tienen el código. |
| `REINGRESOS` | De ellos, los que reingresan. |
| `TASA_CON_CODIGO` y `TASA_SIN_CODIGO` | Porcentaje de reingreso de los casos con el código y sin él. |
| `CHI2` y `VALOR_P` | Chi-cuadrado de Pearson de la tabla de 2×2 y su valor p (1 grado de libertad). |
| `V` | V de Cramér: raíz(chi-cuadrado / casos con dato). Va de 0 (sin relación) a 1. |
| `DIRECCION` | `sube` si el reingreso es mayor con el código, `baja` si es menor. |
| `PASA` | Verdadero si el código pasa los dos umbrales. |

## 10. Verificaciones

- El conjunto de desarrollo es el de la versión 2 registrada de la partición: **sí**.
- Se leyeron todos los casos de estudio del conjunto de desarrollo registrado: **sí**.
- Cada variable tiene una fila por código distinto de cada bloque, sin repetir códigos: **sí**.
- En cada variable, los casos de todos los códigos suman los pares caso–código con dato: **sí**.
- Las cuatro celdas de la tabla de 2×2 de cada código son mayores o iguales a cero: **sí**.
- El chi-cuadrado coincide con el de la fórmula abreviada N·(ad − bc)² / (con · sin · R · (N − R)): **sí**.
- La V está entre 0 y 1 en todos los códigos: **sí**.
- El valor p es 0,05 cuando el chi-cuadrado es 3,841459 (control de la fórmula): **sí**.
- Todos los códigos que pasan tienen descripción en las tablas del DEIS: **sí**.
- Con los umbrales principales, la sensibilidad cuenta los mismos códigos que la lista: **sí**.
- Lo releído de filtro_codigos.parquet es igual a lo calculado: **sí**.
- La lista releída tiene los mismos códigos, casos y reingresos que los que pasan el filtro: **sí**.
