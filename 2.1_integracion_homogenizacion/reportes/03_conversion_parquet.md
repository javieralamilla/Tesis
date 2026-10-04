# Conversión de los archivos GRD a Parquet (Paso 2)

Generado por `2.1_integracion_homogenizacion/scripts/03_convertir_parquet.py`. Todas las columnas se guardan como texto, sin transformar. Se agregan `ANIO_ARCHIVO`, `ARCHIVO_ORIGEN` y `FILA_ORIGEN` (número de línea en el txt original; la línea 1 es el encabezado). 'Celdas faltantes' cuenta campos ausentes por líneas con menos columnas de lo esperado. Las líneas con un campo de más (un '|' dentro de `HOSPPROCEDENCIA`) se reparan uniendo ese campo al valor de `HOSPPROCEDENCIA` con '|', lo que reproduce el texto original.

| año | archivo | codificación | registros txt | registros Parquet | celdas faltantes | líneas con '|' extra (reparadas) | verificación | MB txt | MB Parquet | segundos |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | GRD_PUBLICO_2019.txt | utf-8 | 1,151,475 | 1,151,475 | 0 | ninguna | OK | 573 | 58 | 46 |
| 2020 | GRD_PUBLICO_2020.txt | utf-8 | 781,912 | 781,912 | 0 | ninguna | OK | 397 | 43 | 29 |
| 2021 | GRD_PUBLICO_2021.txt | utf-8-sig | 816,909 | 816,909 | 0 | ninguna | OK | 429 | 48 | 31 |
| 2022 | GRD_PUBLICO_EXTERNO_2022.txt | utf-16 | 932,840 | 932,840 | 0 | 120127 | OK | 961 | 54 | 77 |
| 2023 | GRD_PUBLICO_2023.txt | utf-16 | 1,039,587 | 1,039,587 | 0 | ninguna | OK | 1,075 | 57 | 39 |
| 2024 | GRD_PUBLICO_2024.txt | cp1252 | 1,085,813 | 1,085,813 | 0 | ninguna | OK | 566 | 63 | 43 |

**Total:** 5,808,536 registros en los txt y 5,808,536 en Parquet.
