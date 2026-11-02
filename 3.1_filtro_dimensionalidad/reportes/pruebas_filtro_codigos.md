# Prueba independiente del filtro de dimensionalidad

Generado por `3.1_filtro_dimensionalidad/pruebas/verificar_14_filtro_codigos.py` el 02-11-2026. El programa vuelve a calcular, sin usar ninguna función del script 14, lo que el script dejó en `data/processed/filtro_codigos.parquet` y en `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv`. Para una muestra de códigos (360: 300 al azar con la semilla 2026, los que quedaron justo en el límite de los umbrales y cinco ejemplos conocidos) marca los casos que tienen el código revisando columna por columna y calcula la V como la correlación entre dos columnas de ceros y unos. Solo lee el conjunto de desarrollo.

Partición probada: versión 3, registrada el 2026-11-02 en `docs/version_particion.csv`.

**Resultado: todas las comprobaciones se cumplen** (23 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 3 registrada de la partición: **sí**.
- filtro_codigos.parquet tiene las columnas esperadas, sin identificadores de egresos ni de pacientes: **sí**.
- La lista fija (A) y listas_codigos.parquet tienen las columnas esperadas: **sí**.
- Se leen tantos casos de estudio como los registrados en la partición (3.347.652 casos): **sí**.
- Cada variable tiene una fila por código distinto de cada bloque, contados columna por columna (16.335 diagnósticos y 3.753 procedimientos): **sí**.
- Muestra: casos y reingresos iguales a los del script (360 códigos × 4 variables): **sí**.
- Muestra: tasas de reingreso con el código y sin él iguales: **sí**.
- Muestra: V igual a la correlación entre «tiene el código» y «reingresa»: **sí**.
- Muestra: chi-cuadrado igual a N · V²: **sí**.
- Muestra: valor p igual al calculado con la distribución normal (chi-cuadrado menor que 40) (1208 filas): **sí**.
- Muestra: dirección (sube o baja) y decisión (pasa o no) iguales (108 filas pasan): **sí**.
- Muestra: descripciones iguales a las de las tablas del DEIS (leídas con openpyxl): **sí**.
- Todos los códigos: la tasa sin el código cuadra con los casos con dato y los reingresos de cada variable (REING_7D: 3.347.652 casos con dato y 69.190 reingresos; REING_7D_CDM: 2.855.319 casos con dato y 36.141 reingresos; REING_30D: 3.275.432 casos con dato y 193.153 reingresos; REING_30D_CDM: 2.792.482 casos con dato y 99.219 reingresos): **sí**.
- Todos los códigos: la V es raíz(chi-cuadrado / N) y está entre 0 y 1: **sí**.
- Todos los códigos: pasan exactamente los que cumplen los dos umbrales (780 filas): **sí**.
- La lista tiene exactamente los códigos que pasan, con los mismos casos y reingresos (780 filas: REING_7D 108, REING_7D_CDM 57, REING_30D 424, REING_30D_CDM 191): **sí**.
- En la lista, los códigos de procedimiento conservan el cero inicial (dos dígitos antes del punto): **sí**.
- Toda la tabla: PASA_C es la regla de la lista C (la A, o riesgo 2,0 veces mayor o menor con valor p menor que 0,001, con al menos 100 casos) (4238 filas de códigos completos): **sí**.
- Listas de todo desarrollo: cada una tiene exactamente los códigos de su regla (A: 780 filas; C: 4.238 filas; AGRUPADA: 674 filas; SIN_FILTRO: 28.188 filas): **sí**.
- Muestra de categorías de diagnóstico: casos y reingresos iguales, marcando columna por columna (24 categorías × 4 variables, entre ellas C79, D61, J84, R57): **sí**.
- Todo caso de estudio tiene su pliegue en validacion_temporal.parquet: **sí**.
- Muestra de códigos: las listas de cada pliegue coinciden con el recálculo con los casos de entrenamiento (168 códigos, 10.080 decisiones revisadas, 109 de ellos cambian entre pliegues): **sí**.
- La tabla de listas de 14_filtro_codigos.md coincide con listas_codigos.parquet (A: 108 / 57 / 424 / 191; C: 849 / 629 / 1.595 / 1.165; AGRUPADA: 112 / 46 / 348 / 168; SIN_FILTRO: 7.184 / 6.975 / 7.116 / 6.913): **sí**.

Los cinco ejemplos con `REING_30D` (script / recálculo):

| Código | Casos | Reingresos | V |
|---|---|---|---|
| `N18.5` | 76.170 / 76.170 | 11.662 / 11.662 | 0,061659 / 0,061659 |
| `K80.2` | 74.941 / 74.941 | 4.813 / 4.813 | 0,003413 / 0,003413 |
| `U07.1` | 94.386 / 94.386 | 5.514 / 5.514 | 0,000403 / 0,000403 |
| `Z37.0` | 472.069 / 472.069 | 6.754 / 6.754 | 0,077802 / 0,077802 |
| `D61.3` | 149 / 149 | 53 / 53 | 0,008496 / 0,008496 |
