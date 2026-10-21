# Prueba independiente de los grupos de la validación temporal

Generado por `2.3_validacion_particion/pruebas/verificar_13_validacion_temporal.py` el 20-10-2026. El programa vuelve a calcular, sin usar ninguna función del script 13, el período de cada caso de estudio de desarrollo (con el año de la fecha de alta) y si el paciente ya fue visto (agrupando por identificador con pyarrow), y lo compara con el archivo y con la tabla del reporte 13. Solo lee el conjunto de desarrollo.

Partición probada: versión 2, registrada el 2026-10-20 en `docs/version_particion.csv`.

**Resultado: todas las comprobaciones se cumplen** (9 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 2 registrada de la partición: **sí**.
- El archivo de grupos tiene solo las columnas esperadas, sin nada que dependa de las variables objetivo ['ID_EGRESO', 'ID_PACIENTE', 'PERIODO', 'PACIENTE_VISTO']: **sí**.
- El archivo tiene exactamente los casos de estudio del conjunto de desarrollo (3354118 casos): **sí**.
- Todo caso de estudio tiene período y el del archivo coincide con el recálculo (año de la fecha de alta): **sí**.
- PACIENTE_VISTO del archivo coincide con el recálculo en los casos de evaluación y no tiene dato en los de entrenamiento (1185781 casos de evaluación; 242193 de pacientes ya vistos): **sí**.
- Reporte 13, fila «Entrenamiento»: casos, pacientes y tasas iguales al recálculo (2168337 casos; 1732822 pacientes; tasas [2.0, 1.23, 5.69, 3.45]): **sí**.
- Reporte 13, fila «Evaluación: todos los casos»: casos, pacientes y tasas iguales al recálculo (1185781 casos; 915896 pacientes; tasas [2.18, 1.32, 6.28, 3.74]): **sí**.
- Reporte 13, fila «Evaluación: pacientes nuevos»: casos, pacientes y tasas iguales al recálculo (943588 casos; 758487 pacientes; tasas [1.96, 1.22, 5.42, 3.3]): **sí**.
- Reporte 13, fila «Evaluación: pacientes ya vistos»: casos, pacientes y tasas iguales al recálculo (242193 casos; 157409 pacientes; tasas [3.05, 1.7, 9.65, 5.34]): **sí**.
