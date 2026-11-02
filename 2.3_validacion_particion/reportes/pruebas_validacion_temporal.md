# Prueba independiente de los grupos de la validación temporal

Generado por `2.3_validacion_particion/pruebas/verificar_13_validacion_temporal.py` el 02-11-2026. El programa vuelve a calcular, sin usar ninguna función del script 13, el período de cada caso de estudio de desarrollo (con el año de la fecha de alta) y si el paciente ya fue visto (agrupando por identificador con pyarrow), y lo compara con el archivo y con la tabla del reporte 13. Solo lee el conjunto de desarrollo.

Partición probada: versión 3, registrada el 2026-11-02 en `docs/version_particion.csv`.

**Resultado: todas las comprobaciones se cumplen** (12 comprobaciones, 0 fallas).

- El conjunto de desarrollo tiene el hash de la versión 3 registrada de la partición: **sí**.
- El archivo de grupos tiene solo las columnas esperadas, sin las variables objetivo ['ID_EGRESO', 'ID_PACIENTE', 'PERIODO', 'PACIENTE_VISTO', 'PLIEGUE']: **sí**.
- El archivo tiene exactamente los casos de estudio del conjunto de desarrollo (3347652 casos): **sí**.
- Todo caso de estudio tiene período y el del archivo coincide con el recálculo (año de la fecha de alta): **sí**.
- PACIENTE_VISTO del archivo coincide con el recálculo en los casos de evaluación y no tiene dato en los de entrenamiento (1183563 casos de evaluación; 240725 de pacientes ya vistos): **sí**.
- Reporte 13, fila «Entrenamiento»: casos, pacientes y tasas iguales al recálculo (2164089 casos; 1732822 pacientes; tasas [2.0, 1.23, 5.69, 3.45]): **sí**.
- Reporte 13, fila «Evaluación: todos los casos»: casos, pacientes y tasas iguales al recálculo (1183563 casos; 915863 pacientes; tasas [2.19, 1.32, 6.28, 3.74]): **sí**.
- Reporte 13, fila «Evaluación: pacientes nuevos»: casos, pacientes y tasas iguales al recálculo (942838 casos; 758487 pacientes; tasas [1.96, 1.22, 5.41, 3.3]): **sí**.
- Reporte 13, fila «Evaluación: pacientes ya vistos»: casos, pacientes y tasas iguales al recálculo (240725 casos; 157376 pacientes; tasas [3.06, 1.7, 9.67, 5.35]): **sí**.
- PLIEGUE del archivo coincide caso por caso con el recálculo (5 pliegues, semilla 2026) (12 estratos; 2509082 pacientes): **sí**.
- Ningún paciente está en dos pliegues: **sí**.
- Reporte 13, tabla de pliegues: casos, pacientes y tasas iguales al recálculo (pliegue 1: 669548 casos; pliegue 2: 669521 casos; pliegue 3: 669477 casos; pliegue 4: 669533 casos; pliegue 5: 669573 casos): **sí**.
