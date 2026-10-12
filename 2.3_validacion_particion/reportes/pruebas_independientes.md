# Prueba independiente de la actividad 2.3

Generado por `2.3_validacion_particion/pruebas/verificar_10_particion.py` el 08-10-2026. El programa comprueba la partición sin usar ninguna función del script 10: que ningún paciente esté en los dos conjuntos, que los archivos sean el conjunto analítico repartido sin cambios, que la partición se reproduzca a partir de la semilla y que los archivos tengan el hash registrado.

Partición probada: versión 1, registrada el 2026-10-08 en `docs/version_particion.csv`, sobre la versión 1 del conjunto analítico. SHA-256 del conjunto de prueba: `8b568766715af5df011cffa05e07f35484c4ac0970c5ad3fcca4b92e00dd9a17`.

**Resultado: todas las comprobaciones se cumplen** (21 comprobaciones, 0 fallas).

- El conjunto analítico es el de la última versión registrada (versión 1): **sí**.
- La partición se hizo sobre esa versión del conjunto analítico: **sí**.
- El conjunto de prueba tiene el hash registrado: no cambió desde que se apartó: **sí**.
- El conjunto de desarrollo y la lista de identificadores tienen el hash registrado: **sí**.
- El archivo del conjunto de prueba es de solo lectura: **sí**.
- Ningún identificador de paciente está en los dos conjuntos (3228615 en desarrollo y 807153 en prueba): **sí**.
- Ninguna persona está en los dos conjuntos (3231777 en desarrollo y 807922 en prueba): **sí**.
- Ningún egreso está en los dos conjuntos (4623286 en desarrollo y 1157342 en prueba): **sí**.
- Ningún identificador de paciente aparece en los dos bloques: **sí**.
- Los dos conjuntos reúnen exactamente los egresos con persona del conjunto analítico (4623286 + 1157342 = 5780628; quedan fuera 20345 sin persona): **sí**.
- Todos los casos de estudio están en uno de los dos conjuntos: **sí**.
- Los dos archivos tienen las mismas columnas que el conjunto analítico, en el mismo orden (163 columnas): **sí**.
- Las 163 columnas de cada archivo son idénticas, celda a celda, a las del conjunto analítico: **sí**.
- La lista tiene una fila por identificador de paciente con persona (4035768 identificadores): **sí**.
- La lista de identificadores coincide con los identificadores de cada archivo: **sí**.
- La lista solo tiene el identificador, su bloque y su conjunto (nada que dependa de las variables objetivo): **sí**.
- particion.parquet indica el mismo conjunto que los archivos para cada egreso: **sí**.
- La partición se reproduce con la semilla 2026: el recálculo asigna cada identificador al mismo conjunto (14 estratos; 807153 identificadores a prueba): **sí**.
- El conjunto de prueba tiene cerca del 20 % de los casos de estudio (3354118 en desarrollo y 838292 en prueba: 19,995 %): **sí**.
- La tasa de cada variable objetivo difiere en menos de 0,05 puntos porcentuales entre los dos conjuntos (REING_7D -0,001; REING_7D_CDM -0,006; REING_30D -0,002; REING_30D_CDM -0,005): **sí**.
- La tabla de tasas de 10_particion.md coincide con el recálculo: **sí**.
