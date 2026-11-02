# Filtro de dimensionalidad (actividad 3.1, script 14)

Generado por `3.1_filtro_dimensionalidad/scripts/14_filtro_codigos.py`. Entrada: `data/processed/desarrollo.parquet`, de la versión 3 de la partición (SHA-256 `50f07908f35df51c31077971d0aafaf69182c3baea926af34b00d6fff41229b1`), y el pliegue de cada caso de `data/processed/validacion_temporal.parquet` (script 13). Salidas: `data/processed/filtro_codigos.parquet` (todos los códigos), `data/processed/listas_codigos.parquet` (las listas de todo desarrollo y de cada pliegue) y `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv` (la lista fija). No se abre el conjunto de prueba. Las decisiones están en `3.1_filtro_dimensionalidad/bitacora.md` (D45, H30, H31 y D53).

**Filtro:** para cada variable de reingreso, pasa un código si su V de Cramér es mayor o igual a 0,010 y lo tienen al menos 100 casos de estudio con dato en esa variable. Se usa el código tal como viene (por ejemplo, E11.9), en cualquier posición y una vez por caso. La lista calculada con todo el conjunto de desarrollo queda fija para el modelo final y se aplica sin recalcularla al conjunto de prueba (propuesta, Etapa 3). Dentro de la validación cruzada de la actividad 3.2, cada pliegue usa la lista calculada sin sus casos (D53).

## 1. Códigos de los casos de estudio

| Bloque | Códigos distintos | Pares caso–código | Promedio por caso |
|---|---|---|---|
| Diagnósticos (CIE-10) | 16.335 | 18.431.449 | 5,51 |
| Procedimientos (CIE-9-MC) | 3.753 | 29.310.101 | 8,76 |

Casos de estudio de desarrollo: 3.347.652.

## 2. Códigos que pasan el filtro

Cada variable usa los casos de estudio con dato en ella: las variables de 30 días no incluyen los casos sin 60 días de seguimiento (D30), y las de misma CDM no incluyen los partos (D38).

| Variable | Casos con dato | Reingresos | Diagnósticos que pasan | Procedimientos que pasan | Total |
|---|---|---|---|---|---|
| `REING_7D` | 3.347.652 | 69.190 (2,07 %) | 60 (53 suben y 7 bajan) | 48 (36 suben y 12 bajan) | 108 |
| `REING_7D_CDM` | 2.855.319 | 36.141 (1,27 %) | 43 (42 suben y 1 baja) | 14 (11 suben y 3 bajan) | 57 |
| `REING_30D` | 3.275.432 | 193.153 (5,90 %) | 282 (254 suben y 28 bajan) | 142 (112 suben y 30 bajan) | 424 |
| `REING_30D_CDM` | 2.792.482 | 99.219 (3,55 %) | 132 (127 suben y 5 bajan) | 59 (41 suben y 18 bajan) | 191 |

## 3. Listas para comparar en la actividad 3.2

La lista A es la principal. En la actividad 3.2 los modelos se entrenan también con las demás, con la misma validación cruzada, para medir qué se pierde con el filtro (revisión del profesor guía, O7; D53):

- **A**: la principal: V ≥ v_minima y al menos casos_minimos casos (D45).
- **C**: los de la A más los de efecto grande: riesgo al menos efecto_grande_riesgo veces mayor o menor que sin el código, con valor p menor que efecto_grande_p, y al menos casos_minimos casos (H30).
- **AGRUPADA**: la regla de la A con los diagnósticos en su categoría de tres caracteres (R57.0 → R57) y los procedimientos completos.
- **SIN_FILTRO**: todos los códigos completos con al menos casos_minimos casos, sin mirar el reingreso.

Códigos de cada lista, calculada con todo el conjunto de desarrollo (en la C, efecto grande = riesgo al menos 2,0 veces mayor o menor, con valor p menor que 0,001):

| Lista | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|
| `A` | 108 | 57 | 424 | 191 |
| `C` | 849 | 629 | 1.595 | 1.165 |
| `AGRUPADA` | 112 | 46 | 348 | 168 |
| `SIN_FILTRO` | 7.184 | 6.975 | 7.116 | 6.913 |

En la lista agrupada, una categoría de diagnóstico pasa cuando sus subcódigos, sumados, llegan al umbral, aunque por separado no lleguen. Por ejemplo, con `REING_7D`, R57.0 (choque cardiogénico) no pasa por sí solo, pero su categoría R57 sí (V 0,0118). La tabla cuenta los diagnósticos completos que no pasan por sí solos y cuya categoría sí pasa, y las categorías que pasan sin que pase ninguno de sus códigos completos:

| Variable | Categorías de diagnóstico que pasan | Diagnósticos que no pasan solos y cuya categoría sí | Categorías sin ningún código completo en la A | Ejemplos |
|---|---|---|---|---|
| `REING_7D` | 64 | 353 | 19 | `A41`, `D63`, `F19`, `G40`, `I48`, `I69`, `J15`, `J98` |
| `REING_7D_CDM` | 32 | 145 | 2 | `K56`, `K72` |
| `REING_30D` | 206 | 1.094 | 39 | `C16`, `C18`, `C22`, `C40`, `C71`, `C83`, `C85`, `D37` |
| `REING_30D_CDM` | 109 | 696 | 24 | `C50`, `D61`, `F19`, `I25`, `I48`, `I51`, `I63`, `J20` |

## 4. Listas por pliegue

Las listas que miran el reingreso se calculan también con el entrenamiento de cada pliegue de la validación cruzada, es decir, sin los casos del pliegue que se evalúa (revisión del profesor guía, O5). Así, en la actividad 3.2 los casos de validación no ayudan a elegir los códigos. El índice de Jaccard compara la lista de cada pliegue con la de todo desarrollo: de los códigos que están en alguna de las dos, la parte que está en las dos (1 = iguales).

| Lista | Variable | Códigos (todo desarrollo) | En los 5 pliegues | Jaccard | Salen en un pliegue | Entran en un pliegue |
|---|---|---|---|---|---|---|
| `A` | `REING_7D` | 108 | 99 (91,7 %) | 0,904 a 0,923 | 0 a 5 | 6 a 9 |
| `A` | `REING_7D_CDM` | 57 | 47 (82,5 %) | 0,871 a 0,915 | 3 a 5 | 1 a 5 |
| `A` | `REING_30D` | 424 | 398 (93,9 %) | 0,949 a 0,974 | 6 a 12 | 5 a 10 |
| `A` | `REING_30D_CDM` | 191 | 176 (92,1 %) | 0,906 a 0,969 | 4 a 8 | 2 a 12 |
| `C` | `REING_7D` | 849 | 483 (56,9 %) | 0,720 a 0,757 | 155 a 172 | 66 a 91 |
| `C` | `REING_7D_CDM` | 629 | 391 (62,2 %) | 0,753 a 0,775 | 112 a 125 | 32 a 44 |
| `C` | `REING_30D` | 1.595 | 1.155 (72,4 %) | 0,813 a 0,841 | 168 a 213 | 94 a 107 |
| `C` | `REING_30D_CDM` | 1.165 | 846 (72,6 %) | 0,818 a 0,829 | 157 a 174 | 43 a 53 |
| `AGRUPADA` | `REING_7D` | 112 | 103 (92,0 %) | 0,915 a 0,982 | 1 a 5 | 1 a 8 |
| `AGRUPADA` | `REING_7D_CDM` | 46 | 42 (91,3 %) | 0,918 a 0,957 | 0 a 2 | 0 a 4 |
| `AGRUPADA` | `REING_30D` | 348 | 331 (95,1 %) | 0,955 a 0,974 | 4 a 9 | 3 a 8 |
| `AGRUPADA` | `REING_30D_CDM` | 168 | 150 (89,3 %) | 0,936 a 0,971 | 3 a 8 | 1 a 5 |

## 5. Sensibilidad de los umbrales

Cuántos códigos pasarían con cada combinación de umbrales: total (diagnósticos + procedimientos). Solo se cuentan; la lista fija es la de los umbrales principales.

| V mínima | Casos mínimos | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|---|
| 0,005 | 50 | 416 (276 + 140) | 208 (143 + 65) | 1.074 (747 + 327) | 603 (414 + 189) |
| 0,005 | 100 | 416 (276 + 140) | 206 (141 + 65) | 1.072 (746 + 326) | 601 (412 + 189) |
| 0,005 | 500 | 409 (272 + 137) | 193 (130 + 63) | 1.033 (717 + 316) | 570 (386 + 184) |
| 0,010 | 50 | 108 (60 + 48) | 58 (44 + 14) | 424 (282 + 142) | 191 (132 + 59) |
| 0,010 (principal) | 100 | 108 (60 + 48) | 57 (43 + 14) | 424 (282 + 142) | 191 (132 + 59) |
| 0,010 | 500 | 108 (60 + 48) | 54 (40 + 14) | 422 (281 + 141) | 189 (130 + 59) |
| 0,020 | 50 | 19 (7 + 12) | 10 (8 + 2) | 144 (83 + 61) | 54 (36 + 18) |
| 0,020 | 100 | 19 (7 + 12) | 10 (8 + 2) | 144 (83 + 61) | 54 (36 + 18) |
| 0,020 | 500 | 19 (7 + 12) | 10 (8 + 2) | 144 (83 + 61) | 54 (36 + 18) |

## 6. Cuánto reingreso necesita un código para pasar

La V mide cuánto explica el código del reingreso de todos los casos, así que un código con pocos casos necesita una diferencia muy grande para llegar a 0,010 (H30). La tabla da la tasa de reingreso mínima con que pasaría un código que sube el riesgo, según cuántos casos lo tienen. Un código que baja el riesgo necesita muchos casos para pasar, aunque ninguno de ellos reingrese (última fila).

| Casos con el código | `REING_7D` | `REING_7D_CDM` | `REING_30D` | `REING_30D_CDM` |
|---|---|---|---|---|
| 100 | 28,1 % | 20,2 % | 48,5 % | 34,5 % |
| 250 | 18,5 % | 13,2 % | 32,9 % | 23,1 % |
| 500 | 13,7 % | 9,7 % | 25,0 % | 17,4 % |
| 1.000 | 10,3 % | 7,2 % | 19,4 % | 13,3 % |
| 2.500 | 7,3 % | 5,0 % | 14,4 % | 9,7 % |
| 5.000 | 5,7 % | 3,9 % | 11,9 % | 7,9 % |
| 10.000 | 4,7 % | 3,2 % | 10,2 % | 6,6 % |
| 25.000 | 3,7 % | 2,5 % | 8,6 % | 5,5 % |
| 100.000 | 2,9 % | 1,9 % | 7,2 % | 4,5 % |
| Tasa de toda la variable | 2,07 % | 1,27 % | 5,90 % | 3,55 % |
| Casos que necesita un código que baja el riesgo | 15.788 | 22.101 | 5.219 | 7.560 |

## 7. Los códigos con mayor V

**`REING_7D`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `99.04` | TRANSFUSION CONCENTRADO HEMATIES | 178.842 | 3,75 % | 1,97 % | 0,0281 |
| `N18.5` | Enfermedad renal crónica, estadio 5 | 77.988 | 4,65 % | 2,01 % | 0,0280 |
| `93.18` | EJERCICIO RESPIRATORIO | 556.622 | 2,88 % | 1,91 % | 0,0254 |
| `39.95` | HEMODIALISIS | 56.595 | 4,74 % | 2,02 % | 0,0246 |
| `93.96` | ENRIQUECIMIENTO OXIGENO OTRO | 467.311 | 2,93 % | 1,93 % | 0,0243 |
| `87.44` | RADIOGRAFIA TORAX RUTINARIA | 501.997 | 2,88 % | 1,92 % | 0,0241 |
| `C91.0` | Leucemia linfoblástica aguda (Todas) | 8.908 | 8,54 % | 2,05 % | 0,0235 |
| `Z99.2` | Dependencia de diálisis renal | 43.354 | 4,92 % | 2,03 % | 0,0230 |
| `93.94` | AEROSOLTERAPIA | 297.061 | 3,08 % | 1,97 % | 0,0223 |
| `89.66` | GASOMETRIA VENA | 403.813 | 2,92 % | 1,95 % | 0,0222 |

**`REING_7D`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `Z37.0` | Nacido vivo, único | 481.299 | 0,77 % | 2,28 % | 0,0374 |
| `73.59` | PARTO ASISTIDO MANUALMENTE.OTRO | 265.132 | 0,54 % | 2,20 % | 0,0315 |
| `O80.0` | Parto único espontáneo, presentación cefálica de vértice | 235.131 | 0,52 % | 2,18 % | 0,0299 |
| `99.24` | INYECCION HORMONA OTRA | 296.136 | 0,82 % | 2,19 % | 0,0274 |
| `03.91` | INYECCION ANESTESICO CANAL ESPINAL PARA ANALGESIA | 228.164 | 0,81 % | 2,16 % | 0,0238 |
| `75.69` | REPARACION DESGARRO OBSTETRICO ACTUAL OTRO.OTRO | 135.195 | 0,57 % | 2,13 % | 0,0216 |
| `O70.0` | Desgarro perineal de primer grado durante el parto | 110.638 | 0,52 % | 2,12 % | 0,0201 |
| `Z38.0` | Producto único, nacido en hospital | 143.984 | 0,78 % | 2,12 % | 0,0192 |
| `75.34` | MONITORIZACION FETO OTRA | 498.965 | 1,43 % | 2,18 % | 0,0188 |
| `74.1` | CESAREA CERVICAL BAJA | 211.814 | 1,07 % | 2,13 % | 0,0183 |

**`REING_7D_CDM`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `75.34` | MONITORIZACION FETO OTRA | 86.954 | 4,18 % | 1,17 % | 0,0462 |
| `88.78` | ECOGRAFIA UTERO GRAVIDO | 114.567 | 3,61 % | 1,17 % | 0,0429 |
| `O99.2` | Enfermedades endocrinas, de la nutrición y del metabolismo que complican el embarazo, el parto y el puerperio | 47.392 | 3,90 % | 1,22 % | 0,0307 |
| `Z35.8` | Supervisión de otros embarazos de alto riesgo | 10.276 | 6,26 % | 1,25 % | 0,0268 |
| `O36.5` | Atención materna por déficit del crecimiento fetal | 6.115 | 7,65 % | 1,25 % | 0,0265 |
| `O14.0` | Preeclampsia moderada | 2.138 | 11,27 % | 1,26 % | 0,0245 |
| `O99.0` | Anemia que complica el embarazo, el parto y el puerperio | 14.342 | 4,69 % | 1,25 % | 0,0217 |
| `O00.9` | Embarazo ectópico, no especificado | 4.300 | 7,44 % | 1,26 % | 0,0215 |
| `O21.0` | Hiperemesis gravídica leve | 2.617 | 8,75 % | 1,26 % | 0,0203 |
| `O13` | Hipertensión gestacional [inducida por el embarazo] sin proteinuria significativa | 8.565 | 5,39 % | 1,25 % | 0,0203 |

**`REING_7D_CDM`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `99.21` | INYECCION ANTIBIOTICO | 1.310.727 | 1,07 % | 1,44 % | 0,0165 |
| `51.23` | COLECISTECTOMIA LAPAROSCOPICA | 112.574 | 0,40 % | 1,30 % | 0,0157 |
| `K35.8` | Apendicitis aguda, otra y no especificada | 72.360 | 0,41 % | 1,29 % | 0,0124 |
| `96.59` | IRRIGACION HERIDA OTRA | 330.055 | 0,95 % | 1,31 % | 0,0101 |

**`REING_30D`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `N18.5` | Enfermedad renal crónica, estadio 5 | 76.170 | 15,31 % | 5,67 % | 0,0617 |
| `99.04` | TRANSFUSION CONCENTRADO HEMATIES | 174.851 | 11,90 % | 5,56 % | 0,0606 |
| `93.18` | EJERCICIO RESPIRATORIO | 544.535 | 8,94 % | 5,29 % | 0,0577 |
| `99.17` | INYECCION INSULINA | 287.650 | 10,21 % | 5,48 % | 0,0569 |
| `I10` | Hipertensión esencial (primaria) | 891.544 | 8,02 % | 5,10 % | 0,0551 |
| `87.44` | RADIOGRAFIA TORAX RUTINARIA | 491.795 | 8,92 % | 5,36 % | 0,0540 |
| `39.95` | HEMODIALISIS | 55.238 | 15,58 % | 5,73 % | 0,0538 |
| `N17.9` | Insuficiencia renal aguda, no especificada | 128.354 | 11,70 % | 5,66 % | 0,0498 |
| `87.41` | TOMOGRAFIA AXIAL COMPUTERIZADA TORAX | 336.386 | 9,34 % | 5,50 % | 0,0494 |
| `93.94` | AEROSOLTERAPIA | 291.410 | 9,59 % | 5,54 % | 0,0490 |

**`REING_30D`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `Z37.0` | Nacido vivo, único | 472.069 | 1,43 % | 6,65 % | 0,0778 |
| `73.59` | PARTO ASISTIDO MANUALMENTE.OTRO | 260.186 | 1,06 % | 6,31 % | 0,0603 |
| `O80.0` | Parto único espontáneo, presentación cefálica de vértice | 230.745 | 1,02 % | 6,27 % | 0,0569 |
| `99.24` | INYECCION HORMONA OTRA | 290.194 | 1,63 % | 6,31 % | 0,0564 |
| `03.91` | INYECCION ANESTESICO CANAL ESPINAL PARA ANALGESIA | 223.767 | 1,63 % | 6,21 % | 0,0490 |
| `74.1` | CESAREA CERVICAL BAJA | 207.694 | 1,89 % | 6,17 % | 0,0442 |
| `89.26` | EXAMEN GINECOLOGICO | 326.928 | 2,93 % | 6,23 % | 0,0419 |
| `75.69` | REPARACION DESGARRO OBSTETRICO ACTUAL OTRO.OTRO | 132.566 | 1,10 % | 6,10 % | 0,0418 |
| `75.34` | MONITORIZACION FETO OTRA | 489.385 | 3,57 % | 6,31 % | 0,0414 |
| `Z38.0` | Producto único, nacido en hospital | 141.667 | 1,47 % | 6,10 % | 0,0400 |

**`REING_30D_CDM`, los que más suben el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `75.34` | MONITORIZACION FETO OTRA | 85.267 | 12,73 % | 3,26 % | 0,0880 |
| `88.78` | ECOGRAFIA UTERO GRAVIDO | 112.189 | 10,70 % | 3,25 % | 0,0789 |
| `O99.2` | Enfermedades endocrinas, de la nutrición y del metabolismo que complican el embarazo, el parto y el puerperio | 46.338 | 12,27 % | 3,41 % | 0,0612 |
| `O24.4` | Diabetes mellitus que se origina con el embarazo | 29.631 | 14,22 % | 3,44 % | 0,0597 |
| `O34.3` | Atención materna por incompetencia del cuello uterino | 9.057 | 17,94 % | 3,51 % | 0,0443 |
| `Z35.8` | Supervisión de otros embarazos de alto riesgo | 10.047 | 16,68 % | 3,51 % | 0,0426 |
| `O60.0` | Trabajo de parto prematuro sin parto | 11.646 | 14,47 % | 3,51 % | 0,0382 |
| `O10.0` | Hipertensión esencial preexistente que complica el embarazo, el parto y el puerperio | 9.394 | 15,22 % | 3,51 % | 0,0366 |
| `O36.5` | Atención materna por déficit del crecimiento fetal | 6.010 | 16,62 % | 3,52 % | 0,0328 |
| `O30.0` | Embarazo doble | 3.055 | 21,77 % | 3,53 % | 0,0326 |

**`REING_30D_CDM`, los que más bajan el riesgo:**

| Código | Descripción | Casos | Reingreso con el código | Sin el código | V |
|---|---|---|---|---|---|
| `51.23` | COLECISTECTOMIA LAPAROSCOPICA | 110.106 | 0,90 % | 3,66 % | 0,0290 |
| `K35.8` | Apendicitis aguda, otra y no especificada | 70.620 | 0,75 % | 3,63 % | 0,0244 |
| `47.01` | APENDICECTOMIA.LAPAROSCOPICA | 56.639 | 1,00 % | 3,61 % | 0,0198 |
| `99.21` | INYECCION ANTIBIOTICO | 1.281.376 | 3,22 % | 3,84 % | 0,0167 |
| `99.83` | FOTOTERAPIA OTRA | 52.583 | 1,35 % | 3,60 % | 0,0165 |
| `47.09` | APENDICECTOMIA.OTRA | 48.649 | 1,26 % | 3,59 % | 0,0165 |
| `93.59` | INMOVILIZACION,PRESION Y CUIDADO HERIDA.OTRA | 268.240 | 2,64 % | 3,65 % | 0,0160 |
| `88.71` | ECOENCEFALOGRAFIA | 48.504 | 1,42 % | 3,59 % | 0,0153 |
| `69.02` | LEGRADO Y DILATACION UTERO POSTPARTO O TRAS ABORTO | 36.265 | 1,29 % | 3,58 % | 0,0140 |
| `99.29` | INYECCION SUSTANCIA TERAPEUTICA O PROFILACTICA.OTRA | 1.919.640 | 3,38 % | 3,93 % | 0,0139 |

## 8. Códigos que pasan en varias variables

| Bloque | Pasan en alguna variable | En 4 | En 3 | En 2 | En 1 |
|---|---|---|---|---|---|
| Diagnósticos (CIE-10) | 337 | 6 | 44 | 74 | 213 |
| Procedimientos (CIE-9-MC) | 153 | 9 | 20 | 43 | 81 |

## 9. Códigos que pasan y cambian con los años

Códigos que pasan cuya frecuencia (porcentaje de los casos de estudio del año que tienen el código) varía más del triple entre el año de menor y el de mayor frecuencia (H31). El filtro no cambia, pero ayuda a interpretar la validación temporal.

| Variable | Diagnósticos (CIE-10) | Procedimientos (CIE-9-MC) |
|---|---|---|
| `REING_7D` | 1 de 60 | 0 de 48 |
| `REING_7D_CDM` | 3 de 43 | 0 de 14 |
| `REING_30D` | 16 de 282 | 10 de 142 |
| `REING_30D_CDM` | 4 de 132 | 1 de 59 |

De esos 28 códigos (contando una vez los que pasan en varias variables), los doce con la mayor diferencia entre su año de mayor y su año de menor frecuencia:

| Código | Descripción | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Pasa en |
|---|---|---|---|---|---|---|---|---|
| `90.39` | EXAMEN MICROSCOPICO ORL.OTRO | 3,398 % | 19,422 % | 39,330 % | 38,051 % | 19,516 % | 10,625 % | `REING_30D`, `REING_30D_CDM` |
| `99.84` | AISLAMIENTO | 2,525 % | 6,796 % | 10,129 % | 7,531 % | 4,460 % | 4,171 % | `REING_30D` |
| `93.83` | TERAPIA OCUPACIONAL | 1,608 % | 2,363 % | 4,234 % | 4,274 % | 4,966 % | 5,594 % | `REING_30D` |
| `Z03.8` | Observación por sospecha de otras enfermedades y afecciones | 1,008 % | 3,889 % | 2,032 % | 1,380 % | 0,954 % | 0,997 % | `REING_30D` |
| `J96.09` | Insuficiencia respiratoria aguda, Tipo no especificado | 1,242 % | 1,791 % | 3,164 % | 3,133 % | 3,986 % | 4,023 % | `REING_7D`, `REING_7D_CDM`, `REING_30D`, `REING_30D_CDM` |
| `J96.00` | Insuficiencia respiratoria aguda, Tipo I (hipoxémica) | 0,396 % | 1,108 % | 3,014 % | 1,713 % | 2,053 % | 2,129 % | `REING_30D` |
| `96.72` | VENTILACION MECANICA CONTINUA OTRA.DURANTE 96 HORAS O MAS | 0,722 % | 1,332 % | 2,298 % | 1,234 % | 1,104 % | 1,052 % | `REING_30D` |
| `93.75` | ENTRENAMIENTO Y TERAPIA HABLA OTRO | 0,412 % | 0,672 % | 1,187 % | 1,258 % | 1,601 % | 1,821 % | `REING_30D` |
| `N17.8` | Otras insuficiencias renales agudas | 0,493 % | 0,658 % | 0,876 % | 1,283 % | 1,413 % | 1,738 % | `REING_30D` |
| `E55.9` | Deficiencia de vitamina D, no especificada | 0,129 % | 0,271 % | 0,480 % | 0,611 % | 0,774 % | 0,968 % | `REING_30D` |
| `88.43` | ARTERIOGRAFIA ARTERIA PULMONAR | 0,341 % | 0,735 % | 1,165 % | 0,813 % | 0,792 % | 0,801 % | `REING_30D` |
| `38.97` | COLOCACION CATETER VENOSO CENTRAL MEDIANTE GUIADO | 0,190 % | 0,290 % | 0,619 % | 0,659 % | 0,761 % | 0,899 % | `REING_30D` |

## 10. Parámetros usados por este script

| Parámetro | Valor | Descripción |
|---|---|---|
| `variables_objetivo` | `REING_7D / REING_7D_CDM / REING_30D / REING_30D_CDM` | Variables de reingreso para las que se calcula el filtro, separadas por una barra vertical. Cada una tiene su propia lista de códigos (D45) |
| `nivel_codigo` | `COMPLETO` | COMPLETO = el código tal como viene (E11.9). CATEGORIA = solo la categoría, lo que va antes del punto (E11 en los diagnósticos y 99 en los procedimientos), como la columna «Categoría» de las tablas del DEIS (D45) |
| `v_minima` | `0,01` | Umbral del tamaño de efecto: pasa un código cuya V de Cramér con la variable de reingreso sea mayor o igual a este valor (Etapa 3 de la propuesta y D45) |
| `casos_minimos` | `100` | Prevalencia mínima: pasa un código que tengan al menos estos casos de estudio, contados entre los que tienen dato en la variable (Etapa 3 de la propuesta y D45) |
| `v_sensibilidad` | `0,005 / 0,01 / 0,02` | Umbrales de V del análisis de sensibilidad, separados por una barra vertical. Solo se cuenta cuántos códigos pasarían: la lista fija usa v_minima (D45) |
| `casos_sensibilidad` | `50 / 100 / 500` | Mínimos de casos del análisis de sensibilidad. Solo se cuenta cuántos códigos pasarían: la lista fija usa casos_minimos (D45) |
| `listas_comparacion` | `C / AGRUPADA / SIN_FILTRO` | Listas de códigos que se calculan además de la principal (A), para compararlas en la actividad 3.2, separadas por una barra vertical. C = la A más los códigos de efecto grande. AGRUPADA = la regla de la A con los diagnósticos en su categoría de tres caracteres y los procedimientos completos. SIN_FILTRO = todos los códigos con al menos casos_minimos casos. Las que miran el reingreso (A, C y AGRUPADA) se calculan también con el entrenamiento de cada pliegue (D53) |
| `efecto_grande_riesgo` | `2` | Lista C: un código tiene efecto grande si el riesgo de reingreso con el código es al menos este número de veces el riesgo sin él, o como máximo su inverso (2 = el doble o la mitad) (H30, D53) |
| `efecto_grande_p` | `0,001` | Lista C: además, el valor p del chi-cuadrado debe ser menor que este valor (H30, D53) |

## 11. Archivos de salida

`data/processed/filtro_codigos.parquet` tiene una fila por variable de reingreso y código, pase o no el filtro, con el código completo y, para la lista agrupada, también con la categoría de los diagnósticos (columna `NIVEL`), calculado con todo el conjunto de desarrollo. `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv` tiene solo los códigos de la lista A, sin las columnas `NIVEL`, `CHI2`, `VALOR_P`, `RIESGO_RELATIVO`, `PASA` y `PASA_C`; se lee con `sep=";"`, `decimal=","` y la columna `CODIGO` como texto (los procedimientos pueden empezar con cero, como `00.14`).

| Columna | Contenido |
|---|---|
| `VARIABLE` | Variable de reingreso. |
| `BLOQUE` | `DIAGNOSTICO` (CIE-10) o `PROCEDIMIENTO` (CIE-9-MC). |
| `NIVEL` | `COMPLETO` (el código tal como viene) o `CATEGORIA` (la categoría del diagnóstico, para la lista agrupada). |
| `CODIGO` | El código. |
| `DESCRIPCION` | Descripción según las tablas del DEIS (`Datos/Tablas auxiliares`). |
| `CASOS` | Casos de estudio con dato en la variable que tienen el código. |
| `REINGRESOS` | De ellos, los que reingresan. |
| `TASA_CON_CODIGO` y `TASA_SIN_CODIGO` | Porcentaje de reingreso de los casos con el código y sin él. |
| `CHI2` y `VALOR_P` | Chi-cuadrado de Pearson de la tabla de 2×2 y su valor p (1 grado de libertad). |
| `V` | V de Cramér: raíz(chi-cuadrado / casos con dato). Va de 0 (sin relación) a 1. |
| `DIRECCION` | `sube` si el reingreso es mayor con el código, `baja` si es menor. |
| `RIESGO_RELATIVO` | Tasa de reingreso con el código dividida por la tasa sin él. |
| `PASA` | Verdadero si el código pasa los dos umbrales (la regla de la lista A). |
| `PASA_C` | Verdadero si el código pasa la regla de la lista C. |

`data/processed/listas_codigos.parquet` tiene una fila por código de cada lista: `VARIABLE`, `LISTA` (A, C, AGRUPADA, SIN_FILTRO), `PLIEGUE` (0 = calculada con todo desarrollo, la del modelo final; 1 a 5 = calculada sin los casos de ese pliegue, la que usa ese pliegue en la validación cruzada), `BLOQUE`, `NIVEL` y `CODIGO`. La lista sin filtro no mira el reingreso, así que solo tiene la versión 0.

## 12. Verificaciones

- El conjunto de desarrollo es el de la versión 3 registrada de la partición: **sí**.
- Se leyeron todos los casos de estudio del conjunto de desarrollo registrado: **sí**.
- Cada variable tiene una fila por código distinto de cada bloque, sin repetir códigos: **sí**.
- En cada variable, los casos de todos los códigos suman los pares caso–código con dato: **sí**.
- Las cuatro celdas de la tabla de 2×2 de cada código son mayores o iguales a cero: **sí**.
- El chi-cuadrado coincide con el de la fórmula abreviada N·(ad − bc)² / (con · sin · R · (N − R)): **sí**.
- La V está entre 0 y 1 en todos los códigos: **sí**.
- El valor p es 0,05 cuando el chi-cuadrado es 3,841459 (control de la fórmula): **sí**.
- Todos los códigos que pasan tienen descripción en las tablas del DEIS: **sí**.
- Con los umbrales principales, la sensibilidad cuenta los mismos códigos que la lista: **sí**.
- Los casos y reingresos por pliegue suman los de todo desarrollo en cada código y variable: **sí**.
- Cada lista tiene una versión de todo desarrollo y, las que miran el reingreso, una por pliegue: **sí**.
- Todo código de una lista tiene al menos 100 casos en todo desarrollo: **sí**.
- La lista A está contenida en la C, en todo desarrollo y en cada pliegue: **sí**.
- La lista A de todo desarrollo es la de los códigos que pasan el filtro: **sí**.
- Lo releído de filtro_codigos.parquet y de listas_codigos.parquet es igual a lo calculado: **sí**.
- La lista releída tiene los mismos códigos, casos y reingresos que los que pasan el filtro: **sí**.
