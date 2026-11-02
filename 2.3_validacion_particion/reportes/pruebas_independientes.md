# Prueba independiente de la actividad 2.3

Generado por `2.3_validacion_particion/pruebas/verificar_10_particion.py` el 02-11-2026. El programa comprueba la partición sin usar ninguna función del script 10: que ningún paciente esté en los dos conjuntos, que los archivos sean el conjunto analítico repartido sin cambios, que la partición se reproduzca a partir de la semilla y que los archivos tengan el hash registrado.

Partición probada: versión 3, registrada el 2026-11-02 en `docs/version_particion.csv`, sobre la versión 3 del conjunto analítico. SHA-256 del conjunto de prueba: `4ee4f9ba09d530723055772af21319e22f89da524a70d14f4659d173ca415c21`.

**Resultado: todas las comprobaciones se cumplen** (21 comprobaciones, 0 fallas).

- El conjunto analítico es el de la última versión registrada (versión 3): **sí**.
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
- Los dos archivos tienen las mismas columnas que el conjunto analítico, en el mismo orden (164 columnas): **sí**.
- Las 164 columnas de cada archivo son idénticas, celda a celda, a las del conjunto analítico: **sí**.
- La lista tiene una fila por identificador de paciente con persona (4035768 identificadores): **sí**.
- La lista de identificadores coincide con los identificadores de cada archivo: **sí**.
- La lista solo tiene el identificador, su bloque y su conjunto (nada que dependa de las variables objetivo): **sí**.
- particion.parquet indica el mismo conjunto que los archivos para cada egreso: **sí**.
- Reparto registrado: la lista de identificadores es la del sorteo original (mismo hash que la versión 1 de la partición) (un sorteo nuevo con la semilla 2026 sobre esta versión cambiaría de conjunto a 967219 identificadores): **sí**.
- El conjunto de prueba tiene cerca del 20 % de los casos de estudio (3347652 en desarrollo y 836720 en prueba: 19,996 %): **sí**.
- La tasa de cada variable objetivo difiere en menos de 0,05 puntos porcentuales entre los dos conjuntos (REING_7D -0,001; REING_7D_CDM -0,008; REING_30D +0,003; REING_30D_CDM -0,004): **sí**.
- La tabla de tasas de 10_particion.md coincide con el recálculo: **sí**.
