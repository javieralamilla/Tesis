# Prueba independiente del entrenamiento

Generado por `3.2_entrenamiento_modelos/pruebas/verificar_17_entrenamiento.py` el 27-11-2026. Revisa por otro camino las tablas de predicciones fuera de pliegue que dejó el script 17 y su registro: rehace con pandas, sin las funciones del script, los casos, los pliegues, los códigos de cada lista, las columnas de las categorías, los números transformados y las proporciones del entrenamiento, y los compara con lo del script; además repite una vuelta, también con las respuestas de los casos de validación desordenadas, para mostrar que el modelo nunca las miró.

Tablas para los modelos: versión 1. Tablas de predicciones revisadas: 51.

**Resultado: todas las comprobaciones se cumplen** (19 comprobaciones, 0 fallas).

- Las tablas para los modelos son la versión registrada (versión 1): **sí**.
- Los valores de D62 de reglas/parametros.csv coinciden con la segunda transcripción (11 valores; distintos: ninguno): **sí**.
- La semilla es 2026 y hay 5 pliegues (parámetros de la 2.3): **sí**.
- Las columnas de cada tipo coinciden con la segunda transcripción (14 categorías, 6 con logaritmo, 7 numéricas y 3 sí/no, en ese orden): **sí**.
- Hay tablas de predicciones para revisar (51): **sí**.
- Cada tabla es una de las 63 combinaciones de D64, con la ponderación decidida (fuera de lugar: ninguna): **sí**.
- La información guardada en cada tabla coincide con su nombre, la semilla y la versión (distintas: ninguna): **sí**.
- Cada tabla tiene exactamente los casos con dato en su variable, sin repetir (distintas: ninguna): **sí**.
- Cada caso tiene en la tabla su pliegue de modelos_casos (distintas: ninguna): **sí**.
- Las probabilidades están entre 0 y 1, sin valores vacíos (distintas: ninguna): **sí**.
- El registro tiene las cinco vueltas de cada combinación, con los casos, reingresos, códigos y columnas recalculados aquí (distintas: ninguna): **sí**.
- La regresión logística llegó a su solución en todas sus vueltas (no llegó: ninguna): **sí**.
- Cada vuelta registra el commit del código (sin commit: ninguna): **sí**.
- La lista de cada vuelta es la de la receta del diccionario (PLIEGUE = k, o 0 en la sin filtro), y cada caso revisado tiene exactamente sus códigos de esa lista (20 vueltas, 200 casos en cada una; distintas: ninguna): **sí**.
- Cada caso revisado tiene un 1 justo en el valor de cada una de sus categorías (sin HOSPITAL en los entrenamientos sin hospital) (distintas: ninguna): **sí**.
- Los números transformados (mediana, logaritmo y estandarización del entrenamiento) coinciden con los recalculados aquí (distintas: ninguna): **sí**.
- Las proporciones de las columnas sí/no en el entrenamiento coinciden con las contadas aquí (todas las categorías y 50 códigos por vuelta) (distintas: ninguna): **sí**.
- Repetir la vuelta 1 da las mismas probabilidades guardadas (REING_30D_CDM__XGB__AGRUPADA__con_hospital__sin_ponderar; 558.765 casos; diferencia máxima 0.0e+00): **sí**.
- Con las respuestas de los casos de validación desordenadas, sus probabilidades no cambian: el modelo nunca las miró (cambiaron 38296 respuestas; diferencia máxima 0.0e+00): **sí**.
