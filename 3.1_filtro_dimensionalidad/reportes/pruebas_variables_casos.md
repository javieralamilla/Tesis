# Prueba independiente de las variables de los casos de estudio

Generado por `3.1_filtro_dimensionalidad/pruebas/verificar_15_variables_casos.py` el 29-10-2026. El programa vuelve a calcular, sin usar ninguna función del script 15, lo que el script dejó en `data/processed/variables_casos.parquet`. Compara las tablas de reglas con una segunda transcripción (los códigos de comorbilidad, con los rangos de Quan et al., 2005); recalcula con pyarrow, para todos los casos, las variables que no dependen de la historia, y arma la historia de 12 meses recorriendo uno por uno los egresos de cada persona en una muestra de 3.062 casos (2000 al azar con la semilla 2026, los ejemplos del reporte 15 y casos en los bordes de la ventana). Solo lee el conjunto de desarrollo.

Partición probada: versión 2, registrada el 2026-10-20 en `docs/version_particion.csv`.

**Resultado: todas las comprobaciones se cumplen** (17 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 2 registrada de la partición: **sí**.
- variables_casos.parquet tiene las 31 columnas esperadas, en orden: **sí**.
- No contiene identificadores de pacientes, variables objetivo ni el año: **sí**.
- La tabla de previsión coincide con la decisión 1 (12 valores en 8 grupos): **sí**.
- La tabla de regiones coincide con la segunda transcripción (57 provincias en 16 regiones): **sí**.
- Los códigos de comorbilidad coinciden con los rangos de Quan et al. (2005), condición por condición (48 condiciones, 688 códigos): **sí**.
- Los pesos (1 en Elixhauser; Quan et al. 2011 en Charlson) y las jerarquías de la tabla son los esperados: **sí**.
- Hay exactamente una fila por caso de estudio de desarrollo (3.354.118 casos): **sí**.
- Decisión 1: edad, sexo, previsión, región, tipo de ingreso, CDM y peso iguales en todos los casos: **sí**.
- Episodio: estadía, traslado, UCI o UTI, marca de ventana cortada e intervención iguales en todos los casos: **sí**.
- Ningún egreso E04 de 2019 tiene episodio: **sí**.
- Número de diagnósticos y de procedimientos distintos iguales en todos los casos: **sí**.
- Las sumas coinciden con los pares caso–código del filtro del script 14 (18.458.052 diagnósticos y 29.327.510 procedimientos): **sí**.
- Índice de comorbilidad (ELIXHAUSER) igual en todos los casos: **sí**.
- Demás columnas del CMBD y valores juntados en OTRO iguales en todos los casos: **sí**.
- Muestra: las seis variables de la historia iguales, recorriendo egreso por egreso (3.062 casos): **sí**.
- Toda la tabla: DIAS_ULTIMA_HOSP vale 366 solo sin hospitalizaciones previas, y las no planificadas no superan al total: **sí**.

Casos de borde incluidos en la muestra: episodio propio de 0 días: 291; hospitalización el mismo día del ingreso índice: 154; hospitalización justo 365 días antes: 151; marca en 2020 o 2022: 164; cirugía ambulatoria previa: 216; sesión previa: 172; traslado: 204.

Los ejemplos del reporte 15 (script / recálculo):

| Caso | Hospitalizaciones previas | No planificadas | Días desde la última | Cirugías ambulatorias |
|---|---|---|---|---|
| `20230001746` | 0 / 0 | 0 / 0 | 366 / 366 | 0 / 0 |
| `20230000956` | 2 / 2 | 1 / 1 | 154 / 154 | 1 / 1 |
| `20230120079` | 0 / 0 | 0 / 0 | 366 / 366 | 0 / 0 |
