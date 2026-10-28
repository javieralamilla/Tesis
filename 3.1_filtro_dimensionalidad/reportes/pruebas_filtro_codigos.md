# Prueba independiente del filtro de dimensionalidad

Generado por `3.1_filtro_dimensionalidad/pruebas/verificar_14_filtro_codigos.py` el 28-10-2026. El programa vuelve a calcular, sin usar ninguna función del script 14, lo que el script dejó en `data/processed/filtro_codigos.parquet` y en `3.1_filtro_dimensionalidad/reportes/14_codigos_retenidos.csv`. Para una muestra de códigos (358: 300 al azar con la semilla 2026, los que quedaron justo en el límite de los umbrales y cinco ejemplos conocidos) marca los casos que tienen el código revisando columna por columna y calcula la V como la correlación entre dos columnas de ceros y unos. Solo lee el conjunto de desarrollo.

Partición probada: versión 2, registrada el 2026-10-20 en `docs/version_particion.csv`.

**Resultado: todas las comprobaciones se cumplen** (17 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 2 registrada de la partición: **sí**.
- filtro_codigos.parquet tiene las columnas esperadas, sin identificadores de egresos ni de pacientes: **sí**.
- La lista tiene las mismas columnas, salvo CHI2, VALOR_P y PASA: **sí**.
- Se leen tantos casos de estudio como los registrados en la partición (3.354.118 casos): **sí**.
- Cada variable tiene una fila por código distinto de cada bloque, contados columna por columna (16.336 diagnósticos y 3.753 procedimientos): **sí**.
- Muestra: casos y reingresos iguales a los del script (358 códigos × 4 variables): **sí**.
- Muestra: tasas de reingreso con el código y sin él iguales: **sí**.
- Muestra: V igual a la correlación entre «tiene el código» y «reingresa»: **sí**.
- Muestra: chi-cuadrado igual a N · V²: **sí**.
- Muestra: valor p igual al calculado con la distribución normal (chi-cuadrado menor que 40) (1197 filas): **sí**.
- Muestra: dirección (sube o baja) y decisión (pasa o no) iguales (108 filas pasan): **sí**.
- Muestra: descripciones iguales a las de las tablas del DEIS (leídas con openpyxl): **sí**.
- Todos los códigos: la tasa sin el código cuadra con los casos con dato y los reingresos de cada variable (REING_7D: 3.354.118 casos con dato y 69.299 reingresos; REING_7D_CDM: 2.861.785 casos con dato y 36.200 reingresos; REING_30D: 3.281.764 casos con dato y 193.589 reingresos; REING_30D_CDM: 2.798.814 casos con dato y 99.444 reingresos): **sí**.
- Todos los códigos: la V es raíz(chi-cuadrado / N) y está entre 0 y 1: **sí**.
- Todos los códigos: pasan exactamente los que cumplen los dos umbrales (778 filas): **sí**.
- La lista tiene exactamente los códigos que pasan, con los mismos casos y reingresos (778 filas: REING_7D 108, REING_7D_CDM 57, REING_30D 423, REING_30D_CDM 190): **sí**.
- En la lista, los códigos de procedimiento conservan el cero inicial (dos dígitos antes del punto): **sí**.

Los cinco ejemplos con `REING_30D` (script / recálculo):

| Código | Casos | Reingresos | V |
|---|---|---|---|
| `N18.5` | 76.223 / 76.223 | 11.667 / 11.667 | 0,061572 / 0,061572 |
| `K80.2` | 74.978 / 74.978 | 4.823 / 4.823 | 0,003463 / 0,003463 |
| `U07.1` | 94.391 / 94.391 | 5.516 / 5.516 | 0,000403 / 0,000403 |
| `Z37.0` | 472.069 / 472.069 | 6.754 / 6.754 | 0,077736 / 0,077736 |
| `D61.3` | 149 / 149 | 53 / 53 | 0,008486 / 0,008486 |
