# Prueba independiente de las métricas

Generado por `3.2_entrenamiento_modelos/pruebas/verificar_18_metricas.py` el 27-11-2026. Revisa por otro camino lo que dejó el script 18: recalcula con scikit-learn las áreas y el Brier, con scipy la calibración, rehace desde cero el primer y el último sorteo de cada combinación con la receta de D63 y vuelve a calcular las comparaciones y sus veredictos con una segunda transcripción de las reglas de D61 y D64.

Tablas para los modelos: versión 1. Tablas de métricas revisadas: 51.

**Resultado: todas las comprobaciones se cumplen** (15 comprobaciones, 0 fallas).

- Las tablas para los modelos son la versión registrada (versión 1): **sí**.
- Los parámetros del script 18 coinciden con la segunda transcripción y la semilla es 2026 (distintos: ninguno): **sí**.
- Hay tablas de métricas para revisar (51): **sí**.
- Hay una tabla de métricas por cada tabla de predicciones, y ninguna de más (sin métricas: ninguna; de más: ninguna): **sí**.
- Cada tabla de métricas se hizo con la tabla de predicciones que hay ahora (misma huella) (distintas: ninguna): **sí**.
- Cada tabla de métricas tiene el valor sin sorteo y los 1000 sorteos, sin valores vacíos (distintas: ninguna): **sí**.
- Sin sorteo, la AUPRC, el AUROC, el Brier y la prevalencia coinciden con scikit-learn sobre las predicciones unidas a modelos_casos (51 combinaciones; distintas: ninguna): **sí**.
- Los casos, los reingresos, los casos con probabilidad 0 y sus reingresos coinciden con un recuento (distintas: ninguna): **sí**.
- Sin sorteo, el intercepto con offset y la pendiente coinciden con los calculados con scipy (y la regla de los 0 escrita aquí) (distintas: ninguna): **sí**.
- Sin sorteo, el intercepto y la pendiente de cada año coinciden con los calculados con scipy (distintos: ninguna): **sí**.
- El primer y el último sorteo, rehechos desde cero con la receta de D63, dan las métricas guardadas en todas las combinaciones (los mismos sorteos para todas) (102 sorteos; distintos: ninguna): **sí**.
- En una combinación de cada modelo, la calibración de cada año de esos sorteos coincide con scipy (3 combinaciones; distintos: ninguna): **sí**.
- Cada valor e intervalo de 18_metricas.csv coincide con el recalculado aquí (percentiles 2,5 y 97,5, cada año y cada vuelta) (2244 filas, se esperaban 2244; distintas: ninguna): **sí**.
- 18_comparaciones.csv tiene exactamente las comparaciones posibles con las tablas de métricas (ensayo, listas y sin hospital) (75 filas esperadas; faltan 0, sobran 0): **sí**.
- Las caídas, la mejora del ensayo, sus intervalos y los veredictos coinciden con los recalculados aquí sorteo por sorteo (distintas: ninguna): **sí**.
