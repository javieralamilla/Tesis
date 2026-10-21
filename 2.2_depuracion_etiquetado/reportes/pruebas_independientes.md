# Pruebas independientes de la actividad 2.2

Generado por `2.2_depuracion_etiquetado/pruebas/ejecutar_pruebas.py` el 20-10-2026. Cada programa vuelve a calcular con otro método lo que dejaron los scripts 08, 09 y 11, sin usar sus funciones, y compara el resultado con los archivos y con las tablas de los reportes.

Conjunto analítico probado: `data/processed/grd_etiquetado.parquet`, SHA-256 `f9b8be4065bad16dfe27a46a95db4f742024b1e817046d1d9b26e0a893b900dc`. Coincide con la versión 2 registrada el 2026-10-20 en `docs/version_conjunto_analitico.csv`: **sí**.

**Resultado: todas las comprobaciones se cumplen.**

| Programa | Qué contrasta | Comprobaciones | Fallas | Segundos |
|---|---|---|---|---|
| `verificar_08_depuracion.py` | Duplicados, personas, identidad ambigua, criterios, episodios y papeles de `grd_depurado.parquet`, y la tabla «paso a paso» del reporte 08. | 43 | 0 | 193 |
| `verificar_09_etiquetado.py` | Las cuatro variables objetivo de `grd_etiquetado.parquet`, de dos formas distintas, y las tablas del reporte 09. | 20 | 0 | 76 |
| `verificar_11_sensibilidad.py` | Casos de estudio y tasas de cada escenario de la tabla del reporte 11. | 11 | 0 | 362 |

## Depuración (script 08)

- Las filas de la tabla depurada son filas de la tabla integrada (5808536 -> 5800973; eliminadas 7563): **sí**.
- Las filas conservan el orden de la tabla integrada: **sí**.
- Las columnas originales están al comienzo y en el mismo orden (134 originales + 23 nuevas): **sí**.
- Las 134 columnas originales son idénticas celda a celda: **sí**.
- No quedan dos registros con igual paciente, hospital, fechas, sexo y fecha de nacimiento: **sí**.
- Todo registro repetido eliminado tenía la clave completa (copias exactas 3818; registros repetidos 3745): **sí**.
- Cada registro repetido eliminado tiene exactamente un registro conservado con la misma clave: **sí**.
- El registro conservado es el más completo (diagnósticos, procedimientos, peso GRD, primero del archivo) (0 excepciones en 3745): **sí**.
- ID_PERSONA = ID_PACIENTE x 100 + número de persona: **sí**.
- Identificadores genéricos (contados con otro método) (12 identificadores; 2481 egresos): **sí**.
- Los identificadores genéricos no tienen persona: **sí**.
- Todo egreso con identificador no genérico y con fecha de nacimiento tiene persona (sin persona: 0): **sí**.
- Una fecha de nacimiento de un identificador pertenece a una sola persona: **sí**.
- Identificador con una sola fecha de nacimiento: persona 1 (4011984 identificadores): **sí**.
- Identificadores con dos fechas de nacimiento: una persona si y solo si lo indica la regla (23609 identificadores: 19748 con una persona y 3861 con dos): **sí**.
- Con dos personas, la 1 es la de más edad: **sí**.
- Identificadores con tres o más fechas de nacimiento: las personas son los grupos de fechas compatibles (149 identificadores): **sí**.
- IDENTIDAD_AMBIGUA: identificador con más de un sexo o más de una fecha de nacimiento (30616 identificadores; 96824 egresos; 63278 casos de estudio): **sí**.
- Todo identificador con más de una persona tiene identidad ambigua: **sí**.
- E01 (EXC_SIN_ID) (cumplen 17864; diferencias 0): **sí**.
- E02 (EXC_ID_GENERICO) (cumplen 2481; diferencias 0): **sí**.
- E03 (EXC_FECHAS) (cumplen 83; diferencias 0): **sí**.
- E04 (EXC_ACTIVIDAD_2019) (cumplen 117586; diferencias 0): **sí**.
- E06 (EXC_FALLECIDO) (cumplen 170563; diferencias 0): **sí**.
- E07 (EXC_DERIVADO_HOSPITAL) (cumplen 167418; diferencias 0): **sí**.
- E08 (EXC_DERIVADO_PRIVADO) (cumplen 26081; diferencias 0): **sí**.
- E09 (EXC_SIN_GRD) (cumplen 5042; diferencias 0): **sí**.
- E10 (EXC_DATOS_FALTANTES) (cumplen 149; diferencias 0): **sí**.
- E11 (EXC_CENSURA) (cumplen 188737; diferencias 0): **sí**.
- E12 (EXC_ALTA_VOLUNTARIA_FUGA) (cumplen 77385; diferencias 0): **sí**.
- E13 (EXC_CMA) (cumplen 885384; diferencias 0): **sí**.
- E14 (EXC_SESION) (cumplen 100229; diferencias 0): **sí**.
- Episodios: ID_EPISODIO igual al del recorrido (5565982 episodios en 5663585 egresos): **sí**.
- Episodios: CONTINUA_EPISODIO igual (97603 continuaciones): **sí**.
- Episodios: ALTA_FINAL_EPISODIO igual: **sí**.
- Episodios: N_EGRESOS_EPISODIO igual: **sí**.
- Los egresos que no se pueden seguir no tienen episodio: **sí**.
- E05 (EXC_TRAMO_EPISODIO) (cumplen 97603): **sí**.
- ES_CASO_ESTUDIO (4192410 casos de estudio): **sí**.
- MOTIVO_EXCLUSION: **sí**.
- PUEDE_SER_REINGRESO (5565982 egresos): **sí**.
- Los casos de estudio están vivos al alta y tienen persona, GRD válido y el seguimiento mínimo (mínimo de días al cierre: 37): **sí**.
- La tabla «paso a paso» de 08_depuracion.md coincide con el recálculo en los 14 criterios: **sí**.

## Etiquetado (script 09)

- Las columnas de la tabla depurada están al comienzo y en el mismo orden (157 + 6 nuevas): **sí**.
- Las 157 columnas de la tabla depurada son idénticas celda a celda: **sí**.
- Las columnas nuevas son las esperadas ['REING_7D', 'REING_7D_CDM', 'REING_30D', 'REING_30D_CDM', 'DIAS_REING', 'ID_EGRESO_REING']: **sí**.
- REING_7D: con dato solo en los casos de estudio con al menos 37 días antes del cierre; valores 0 o 1 (con dato 4192410): **sí**.
- REING_7D_CDM: con dato solo en los casos de estudio con al menos 37 días antes del cierre, sin los de la CDM 14; valores 0 o 1 (con dato 3577243): **sí**.
- REING_30D: con dato solo en los casos de estudio con al menos 60 días antes del cierre; valores 0 o 1 (con dato 4101883): **sí**.
- REING_30D_CDM: con dato solo en los casos de estudio con al menos 60 días antes del cierre, sin los de la CDM 14; valores 0 o 1 (con dato 3498460): **sí**.
- DIAS_REING e ID_EGRESO_REING: sin dato fuera de los casos de estudio: **sí**.
- Recorrido caso por caso: REING_7D (casos 4192410; con reingreso 86609; diferencias 0): **sí**.
- Recorrido caso por caso: REING_7D_CDM (casos 3577243; con reingreso 45195; diferencias 0): **sí**.
- Recorrido caso por caso: REING_30D (casos 4101883; con reingreso 241953; diferencias 0): **sí**.
- Recorrido caso por caso: REING_30D_CDM (casos 3498460; con reingreso 124256; diferencias 0): **sí**.
- Recorrido caso por caso: los casos de la CDM 14, sin dato en las relacionadas, no tienen ningún reingreso de su misma CDM (el 0 era obligatorio) (casos 615167): **sí**.
- Recorrido caso por caso: DIAS_REING e ID_EGRESO_REING (casos con algún reingreso posterior: 834693): **sí**.
- Unión literal en la muestra: REING_7D (casos 167627; con reingreso 3523; solo en el archivo 0; solo en la unión 0): **sí**.
- Unión literal en la muestra: REING_7D_CDM (casos 142830; con reingreso 1830; solo en el archivo 0; solo en la unión 0): **sí**.
- Unión literal en la muestra: REING_30D (casos 164065; con reingreso 9748; solo en el archivo 0; solo en la unión 0): **sí**.
- Unión literal en la muestra: REING_30D_CDM (casos 139722; con reingreso 5049; solo en el archivo 0; solo en la unión 0): **sí**.
- La tabla de las cuatro variables de 09_etiquetado.md coincide con el recorrido caso por caso: **sí**.
- La tabla de verificación de la censura de 09_etiquetado.md coincide con el recálculo (7 tramos): **sí**.

## Análisis de sensibilidad (script 11)

- Análisis principal: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4192410 casos; tasas [2.07, 1.26, 5.9, 3.55]): **sí**.
- Con los partos en las variables relacionadas: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4192410 casos; tasas [2.07, 1.08, 5.9, 3.03]): **sí**.
- Con las CDM: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4192410 casos; tasas [2.07, 1.17, 5.9, 3.19]): **sí**.
- Sin los casos con identidad ambigua: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4129132 casos; tasas [2.03, 1.25, 5.79, 3.49]): **sí**.
- Con la cirugía mayor ambulatoria: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (5036703 casos; tasas [1.79, 1.05, 5.1, 2.94]): **sí**.
- Con las sesiones de tratamiento: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4274335 casos; tasas [2.08, 1.24, 5.94, 3.5]): **sí**.
- Censura sin margen: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4313289 casos; tasas [2.06, 1.26, 5.89, 3.54]): **sí**.
- Solo los traslados con marca explícita: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4195786 casos; tasas [2.12, 1.3, 5.95, 3.59]): **sí**.
- Con los derivados sin continuación como casos de estudio: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4286199 casos; tasas [2.12, 1.3, 5.98, 3.59]): **sí**.
- Con las actividades que solo existen en 2019: casos de estudio y las cuatro tasas iguales a los de 11_sensibilidad.md (4275385 casos; tasas [2.11, 1.29, 5.99, 3.59]): **sí**.
- Todas las filas de la tabla del reporte fueron contrastadas (10 filas): **sí**.
