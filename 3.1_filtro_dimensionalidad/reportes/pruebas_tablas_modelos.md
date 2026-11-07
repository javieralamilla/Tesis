# Prueba independiente de las tablas para los modelos

Generado por `3.1_filtro_dimensionalidad/pruebas/verificar_16_tablas_modelos.py` el 03-11-2026. El programa vuelve a armar, sin usar ninguna función de los scripts 14 ni 16, lo que el script 16 dejó en `data/processed/modelos_casos.parquet` y `data/processed/modelos_codigos.parquet`. Compara las columnas con una segunda transcripción de sus papeles; empareja cada caso con su origen por su `ID_EGRESO`; vuelve a sacar los códigos de las 65 columnas con pyarrow (la categoría, con una expresión regular) y compara los pares uno por uno; comprueba que las columnas de las matrices sumen los casos de `filtro_codigos.parquet` y que la receta del diccionario funcione, y revisa el diccionario, el registro de versión y el reporte 16. Solo lee el conjunto de desarrollo.

Partición probada: versión 3, registrada el 2026-11-02 en `docs/version_particion.csv`. Tablas probadas: versión 1 de `docs/version_tablas_modelos.csv`.

**Resultado: todas las comprobaciones se cumplen** (18 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 3 registrada de la partición: **sí**.
- modelos_casos.parquet tiene las 40 columnas esperadas, en orden: **sí**.
- modelos_codigos.parquet tiene las 4 columnas esperadas, en orden: **sí**.
- Ninguna de las dos tablas tiene columnas que nunca pueden estar (después del alta, identidad o armado de la cohorte): **sí**.
- columnas_modelos.csv da a cada columna el papel de la segunda transcripción: **sí**.
- La tabla de casos tiene exactamente los casos de estudio de desarrollo, una vez cada uno (3.347.652 casos): **sí**.
- Cada columna de la tabla de casos es igual, caso por caso, a la de su origen (buscando cada caso por su ID_EGRESO) (38 columnas; ANIO_ALTA se revisa abajo): **sí**.
- ANIO_ALTA es el año de la fecha de alta, y PERIODO, el que dan los años de la validación temporal: **sí**.
- PLIEGUE va de 1 a 5 y ningún paciente está en dos pliegues: **sí**.
- Todos los pares de la tabla de códigos son de casos de desarrollo y de códigos de alguna lista: **sí**.
- La tabla de códigos está ordenada por caso y no repite un código en un caso: **sí**.
- Los pares caso–código son exactamente los recalculados con pyarrow, uno por uno (59.214.795 recalculados y 59.214.795 en la tabla): **sí**.
- Para cada variable y cada código de alguna lista, los casos con dato que lo tienen son los CASOS de filtro_codigos.parquet (7.448 códigos × 4 variables): **sí**.
- En cada lista, todo código tiene al menos 100 casos con dato en su entrenamiento (todo desarrollo en PLIEGUE 0; sin los casos del pliegue en los demás) (60.446 filas de listas revisadas; 0 bajo el mínimo): **sí**.
- La receta del diccionario arma columnas que suman los CASOS de filtro_codigos.parquet (REING_30D, lista A, pliegue 0: 3.275.432 filas, 424 columnas y 30.366.906 unos, en 46 s): **sí**.
- La última versión del registro tiene el hash de las dos tablas y de sus entradas actuales (versión 1): **sí**.
- El diccionario describe cada columna una vez, con su papel, y muestra la versión registrada: **sí**.
- La tabla de matrices del reporte 16 coincide con el recálculo (filas, columnas y celdas con 1) (16 filas; 0 distintas): **sí**.
