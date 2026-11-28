# Métricas de la validación cruzada (script 18)

Última ejecución: el 2026-11-27 01:17, en 22,2 minutos. Commit del código: `ca88716` (cambios sin confirmar en los scripts o las reglas: NO). Tablas para los modelos: versión 1 del 2026-11-03. Python 3.14.5, numpy 2.5.3, pandas 3.0.3, scipy 1.18.1, scikit-learn 1.9.0. Semilla 2026; 1.000 sorteos de pacientes, intervalos al 95 %; para el logit de la calibración, un 0 exacto se cuenta como 0,0001 (D67).

Ninguna cifra de este reporte sale del conjunto de prueba: todas son predicciones fuera de pliegue del conjunto de desarrollo.

## 1. Verificaciones

- ✓ Todas las tablas de predicciones son combinaciones de D64 con la ponderación decidida
- ✓ La tabla de predicciones tiene exactamente los casos con dato en su variable, cada uno con su pliegue, y probabilidades entre 0 y 1, sin vacíos (51 combinaciones)
- ✓ La información guardada en la tabla de predicciones coincide con su nombre, la semilla y la versión de las tablas (51 combinaciones)
- ✓ Sin sorteo, la AUPRC, el AUROC y el Brier coinciden con las funciones de scikit-learn (51 combinaciones)
- ✓ La calibración (general y por año) llegó a la solución sin sorteo y en todos los sorteos (51 combinaciones)
- ✓ Todas las combinaciones usan los mismos pacientes y los mismos sorteos (huella de la lista de pacientes y del primer sorteo)
- ✓ Cada comparación junta dos combinaciones con los mismos casos
- ✓ La ponderación fijada en reglas/parametros.csv coincide con el veredicto del ensayo (D61)

## 2. Ensayo de la ponderación (D61)

Con `REING_7D_CDM` y la lista A. Un modelo se entrena ponderado solo si su AUPRC con ponderación supera en más de 10 % a la sin ponderar en todo el intervalo pareado.

| Modelo | AUPRC sin ponderar | AUPRC ponderada | Cambio relativo (intervalo) | Veredicto |
|---|---|---|---|---|
| Regresión logística | 0,049 | 0,047 | −3,9 % (−4,5 % a −3,5 %) | No ponderar |
| Random Forest | 0,057 | 0,049 | −13,3 % (−16,0 % a −10,8 %) | No ponderar |
| XGBoost | 0,060 | 0,059 | −1,2 % (−3,5 % a 1,6 %) | No ponderar |

El ensayo ya está resuelto en `reglas/parametros.csv`. La ponderación fijada coincide con el veredicto.

## 3. Discriminación de cada combinación

La AUPRC de un modelo al azar es la prevalencia; el cociente dice cuántas veces la supera (D41). Entre paréntesis, el intervalo de los sorteos.

| Variable | Modelo | Lista | Hospital | Ponderado | Casos | Prevalencia | AUPRC | Cociente | AUROC |
|---|---|---|---|---|---|---|---|---|---|
| REING_7D | LR | A | con | NO | 3.347.652 | 2,07 % | 0,058 (0,057 a 0,060) | 2,81 | 0,713 (0,711 a 0,715) |
| REING_7D | LR | A | sin | NO | 3.347.652 | 2,07 % | 0,057 (0,056 a 0,059) | 2,78 | 0,710 (0,708 a 0,712) |
| REING_7D | LR | agrupada | con | NO | 3.347.652 | 2,07 % | 0,058 (0,057 a 0,060) | 2,82 | 0,712 (0,710 a 0,714) |
| REING_7D | LR | C | con | NO | 3.347.652 | 2,07 % | 0,059 (0,057 a 0,060) | 2,84 | 0,719 (0,717 a 0,721) |
| REING_7D | RF | A | con | NO | 3.347.652 | 2,07 % | 0,064 (0,062 a 0,066) | 3,09 | 0,706 (0,704 a 0,708) |
| REING_7D | RF | A | sin | NO | 3.347.652 | 2,07 % | 0,063 (0,062 a 0,065) | 3,07 | 0,704 (0,702 a 0,706) |
| REING_7D | RF | agrupada | con | NO | 3.347.652 | 2,07 % | 0,065 (0,063 a 0,067) | 3,14 | 0,707 (0,705 a 0,710) |
| REING_7D | RF | C | con | NO | 3.347.652 | 2,07 % | 0,065 (0,063 a 0,067) | 3,14 | 0,710 (0,708 a 0,712) |
| REING_7D | XGB | A | con | NO | 3.347.652 | 2,07 % | 0,068 (0,066 a 0,070) | 3,28 | 0,730 (0,728 a 0,732) |
| REING_7D | XGB | A | sin | NO | 3.347.652 | 2,07 % | 0,067 (0,065 a 0,069) | 3,23 | 0,728 (0,726 a 0,730) |
| REING_7D | XGB | agrupada | con | NO | 3.347.652 | 2,07 % | 0,069 (0,067 a 0,070) | 3,32 | 0,731 (0,729 a 0,733) |
| REING_7D | XGB | C | con | NO | 3.347.652 | 2,07 % | 0,068 (0,066 a 0,070) | 3,29 | 0,730 (0,728 a 0,732) |
| REING_7D_CDM | LR | A | con | NO | 2.855.319 | 1,27 % | 0,049 (0,047 a 0,051) | 3,84 | 0,740 (0,737 a 0,743) |
| REING_7D_CDM | LR | A | con | SI | 2.855.319 | 1,27 % | 0,047 (0,045 a 0,048) | 3,68 | 0,741 (0,738 a 0,744) |
| REING_7D_CDM | LR | A | sin | NO | 2.855.319 | 1,27 % | 0,048 (0,046 a 0,050) | 3,78 | 0,738 (0,735 a 0,741) |
| REING_7D_CDM | LR | agrupada | con | NO | 2.855.319 | 1,27 % | 0,049 (0,047 a 0,051) | 3,89 | 0,740 (0,737 a 0,743) |
| REING_7D_CDM | LR | C | con | NO | 2.855.319 | 1,27 % | 0,051 (0,049 a 0,053) | 4,02 | 0,751 (0,749 a 0,754) |
| REING_7D_CDM | RF | A | con | NO | 2.855.319 | 1,27 % | 0,057 (0,054 a 0,060) | 4,51 | 0,732 (0,729 a 0,735) |
| REING_7D_CDM | RF | A | con | SI | 2.855.319 | 1,27 % | 0,049 (0,048 a 0,051) | 3,91 | 0,746 (0,744 a 0,749) |
| REING_7D_CDM | RF | A | sin | NO | 2.855.319 | 1,27 % | 0,055 (0,053 a 0,058) | 4,35 | 0,728 (0,726 a 0,731) |
| REING_7D_CDM | RF | agrupada | con | NO | 2.855.319 | 1,27 % | 0,058 (0,055 a 0,061) | 4,57 | 0,732 (0,730 a 0,735) |
| REING_7D_CDM | RF | C | con | NO | 2.855.319 | 1,27 % | 0,058 (0,055 a 0,061) | 4,56 | 0,734 (0,731 a 0,737) |
| REING_7D_CDM | XGB | A | con | NO | 2.855.319 | 1,27 % | 0,060 (0,057 a 0,062) | 4,71 | 0,767 (0,765 a 0,770) |
| REING_7D_CDM | XGB | A | con | SI | 2.855.319 | 1,27 % | 0,059 (0,056 a 0,061) | 4,65 | 0,763 (0,760 a 0,765) |
| REING_7D_CDM | XGB | A | sin | NO | 2.855.319 | 1,27 % | 0,059 (0,056 a 0,061) | 4,63 | 0,765 (0,762 a 0,767) |
| REING_7D_CDM | XGB | agrupada | con | NO | 2.855.319 | 1,27 % | 0,060 (0,058 a 0,063) | 4,77 | 0,768 (0,765 a 0,771) |
| REING_7D_CDM | XGB | C | con | NO | 2.855.319 | 1,27 % | 0,059 (0,057 a 0,062) | 4,69 | 0,767 (0,764 a 0,770) |
| REING_30D | LR | A | con | NO | 3.275.432 | 5,90 % | 0,169 (0,167 a 0,171) | 2,86 | 0,749 (0,748 a 0,750) |
| REING_30D | LR | A | sin | NO | 3.275.432 | 5,90 % | 0,167 (0,165 a 0,169) | 2,83 | 0,748 (0,746 a 0,749) |
| REING_30D | LR | agrupada | con | NO | 3.275.432 | 5,90 % | 0,168 (0,166 a 0,170) | 2,85 | 0,748 (0,747 a 0,750) |
| REING_30D | LR | C | con | NO | 3.275.432 | 5,90 % | 0,170 (0,168 a 0,172) | 2,88 | 0,752 (0,751 a 0,753) |
| REING_30D | RF | A | con | NO | 3.275.432 | 5,90 % | 0,178 (0,176 a 0,181) | 3,02 | 0,750 (0,749 a 0,751) |
| REING_30D | RF | A | sin | NO | 3.275.432 | 5,90 % | 0,177 (0,175 a 0,180) | 3,00 | 0,749 (0,748 a 0,751) |
| REING_30D | RF | agrupada | con | NO | 3.275.432 | 5,90 % | 0,178 (0,175 a 0,181) | 3,02 | 0,750 (0,749 a 0,752) |
| REING_30D | RF | C | con | NO | 3.275.432 | 5,90 % | 0,179 (0,176 a 0,181) | 3,03 | 0,752 (0,750 a 0,753) |
| REING_30D | XGB | A | con | NO | 3.275.432 | 5,90 % | 0,181 (0,179 a 0,184) | 3,07 | 0,757 (0,756 a 0,759) |
| REING_30D | XGB | A | sin | NO | 3.275.432 | 5,90 % | 0,180 (0,177 a 0,182) | 3,05 | 0,757 (0,756 a 0,758) |
| REING_30D | XGB | agrupada | con | NO | 3.275.432 | 5,90 % | 0,181 (0,179 a 0,184) | 3,07 | 0,757 (0,756 a 0,759) |
| REING_30D | XGB | C | con | NO | 3.275.432 | 5,90 % | 0,181 (0,178 a 0,184) | 3,07 | 0,757 (0,756 a 0,758) |
| REING_30D_CDM | LR | A | con | NO | 2.792.482 | 3,55 % | 0,122 (0,120 a 0,124) | 3,43 | 0,758 (0,756 a 0,760) |
| REING_30D_CDM | LR | A | sin | NO | 2.792.482 | 3,55 % | 0,121 (0,119 a 0,124) | 3,41 | 0,757 (0,755 a 0,759) |
| REING_30D_CDM | LR | agrupada | con | NO | 2.792.482 | 3,55 % | 0,122 (0,119 a 0,124) | 3,42 | 0,759 (0,757 a 0,761) |
| REING_30D_CDM | LR | C | con | NO | 2.792.482 | 3,55 % | 0,124 (0,122 a 0,127) | 3,50 | 0,766 (0,764 a 0,767) |
| REING_30D_CDM | RF | A | con | NO | 2.792.482 | 3,55 % | 0,133 (0,130 a 0,136) | 3,75 | 0,761 (0,759 a 0,763) |
| REING_30D_CDM | RF | A | sin | NO | 2.792.482 | 3,55 % | 0,132 (0,129 a 0,136) | 3,73 | 0,761 (0,759 a 0,762) |
| REING_30D_CDM | RF | agrupada | con | NO | 2.792.482 | 3,55 % | 0,133 (0,130 a 0,136) | 3,75 | 0,762 (0,760 a 0,764) |
| REING_30D_CDM | RF | C | con | NO | 2.792.482 | 3,55 % | 0,134 (0,132 a 0,138) | 3,78 | 0,763 (0,761 a 0,765) |
| REING_30D_CDM | XGB | A | con | NO | 2.792.482 | 3,55 % | 0,136 (0,133 a 0,139) | 3,83 | 0,777 (0,775 a 0,779) |
| REING_30D_CDM | XGB | A | sin | NO | 2.792.482 | 3,55 % | 0,135 (0,132 a 0,138) | 3,81 | 0,777 (0,775 a 0,778) |
| REING_30D_CDM | XGB | agrupada | con | NO | 2.792.482 | 3,55 % | 0,137 (0,134 a 0,140) | 3,86 | 0,779 (0,777 a 0,780) |
| REING_30D_CDM | XGB | C | con | NO | 2.792.482 | 3,55 % | 0,135 (0,132 a 0,138) | 3,79 | 0,777 (0,775 a 0,778) |

## 4. Brier y calibración de cada combinación

Brier de referencia: el de dar a todos la prevalencia, p(1 − p). Intercepto con el logit como offset (ideal 0; positivo, el modelo subestima el riesgo) y pendiente (ideal 1; menor que 1, predicciones demasiado extremas) (D43). La última columna dice cuántos casos tienen probabilidad 0 y, entre paréntesis, cuántos de ellos reingresaron (D67).

| Variable | Modelo | Lista | Hospital | Ponderado | Brier | Brier de referencia | Intercepto | Pendiente | Casos con 0 (reingresan) |
|---|---|---|---|---|---|---|---|---|---|
| REING_7D | LR | A | con | NO | 0,0199 (0,0198 a 0,0201) | 0,0202 | +0,000 (−0,007 a +0,009) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D | LR | A | sin | NO | 0,0199 (0,0198 a 0,0201) | 0,0202 | +0,000 (−0,007 a +0,009) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D | LR | agrupada | con | NO | 0,0199 (0,0198 a 0,0201) | 0,0202 | +0,000 (−0,007 a +0,009) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D | LR | C | con | NO | 0,0199 (0,0198 a 0,0201) | 0,0202 | +0,001 (−0,006 a +0,010) | 0,95 (0,94 a 0,96) | 0 (0) |
| REING_7D | RF | A | con | NO | 0,0199 (0,0197 a 0,0200) | 0,0202 | −0,020 (−0,027 a −0,012) | 0,63 (0,62 a 0,64) | 251.693 (1.159) |
| REING_7D | RF | A | sin | NO | 0,0199 (0,0198 a 0,0200) | 0,0202 | −0,029 (−0,037 a −0,021) | 0,63 (0,62 a 0,64) | 236.509 (1.066) |
| REING_7D | RF | agrupada | con | NO | 0,0199 (0,0197 a 0,0200) | 0,0202 | −0,020 (−0,028 a −0,012) | 0,64 (0,63 a 0,65) | 253.334 (1.133) |
| REING_7D | RF | C | con | NO | 0,0199 (0,0197 a 0,0200) | 0,0202 | +0,000 (−0,007 a +0,008) | 0,66 (0,65 a 0,68) | 230.628 (984) |
| REING_7D | XGB | A | con | NO | 0,0198 (0,0197 a 0,0200) | 0,0202 | +0,002 (−0,005 a +0,011) | 0,96 (0,95 a 0,97) | 0 (0) |
| REING_7D | XGB | A | sin | NO | 0,0198 (0,0197 a 0,0200) | 0,0202 | +0,002 (−0,005 a +0,011) | 0,95 (0,94 a 0,96) | 0 (0) |
| REING_7D | XGB | agrupada | con | NO | 0,0198 (0,0197 a 0,0200) | 0,0202 | +0,002 (−0,006 a +0,010) | 0,96 (0,95 a 0,96) | 0 (0) |
| REING_7D | XGB | C | con | NO | 0,0198 (0,0197 a 0,0200) | 0,0202 | +0,002 (−0,005 a +0,010) | 0,97 (0,96 a 0,98) | 0 (0) |
| REING_7D_CDM | LR | A | con | NO | 0,0123 (0,0122 a 0,0124) | 0,0125 | +0,001 (−0,010 a +0,012) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D_CDM | LR | A | con | SI | 0,2031 (0,2028 a 0,2033) | 0,0125 | −4,375 (−4,386 a −4,364) | 0,92 (0,91 a 0,93) | 0 (0) |
| REING_7D_CDM | LR | A | sin | NO | 0,0123 (0,0122 a 0,0124) | 0,0125 | +0,001 (−0,010 a +0,012) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D_CDM | LR | agrupada | con | NO | 0,0123 (0,0122 a 0,0124) | 0,0125 | +0,001 (−0,010 a +0,012) | 0,98 (0,97 a 0,99) | 0 (0) |
| REING_7D_CDM | LR | C | con | NO | 0,0123 (0,0121 a 0,0124) | 0,0125 | +0,002 (−0,009 a +0,013) | 0,94 (0,93 a 0,96) | 0 (0) |
| REING_7D_CDM | RF | A | con | NO | 0,0123 (0,0121 a 0,0124) | 0,0125 | −0,025 (−0,035 a −0,014) | 0,63 (0,62 a 0,64) | 455.804 (1.221) |
| REING_7D_CDM | RF | A | con | SI | 0,0240 (0,0239 a 0,0241) | 0,0125 | −2,172 (−2,183 a −2,160) | 0,80 (0,79 a 0,81) | 210.314 (310) |
| REING_7D_CDM | RF | A | sin | NO | 0,0123 (0,0121 a 0,0124) | 0,0125 | −0,033 (−0,044 a −0,022) | 0,62 (0,61 a 0,64) | 442.225 (1.208) |
| REING_7D_CDM | RF | agrupada | con | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | −0,024 (−0,035 a −0,013) | 0,63 (0,62 a 0,64) | 458.663 (1.264) |
| REING_7D_CDM | RF | C | con | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | −0,010 (−0,021 a +0,001) | 0,65 (0,64 a 0,66) | 432.610 (1.119) |
| REING_7D_CDM | XGB | A | con | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | +0,005 (−0,006 a +0,016) | 0,95 (0,94 a 0,96) | 0 (0) |
| REING_7D_CDM | XGB | A | con | SI | 0,1803 (0,1800 a 0,1805) | 0,0125 | −4,249 (−4,260 a −4,238) | 0,99 (0,98 a 1,00) | 0 (0) |
| REING_7D_CDM | XGB | A | sin | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | +0,004 (−0,006 a +0,015) | 0,95 (0,94 a 0,96) | 0 (0) |
| REING_7D_CDM | XGB | agrupada | con | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | +0,005 (−0,006 a +0,016) | 0,95 (0,94 a 0,96) | 0 (0) |
| REING_7D_CDM | XGB | C | con | NO | 0,0122 (0,0121 a 0,0124) | 0,0125 | +0,005 (−0,006 a +0,015) | 0,96 (0,95 a 0,97) | 0 (0) |
| REING_30D | LR | A | con | NO | 0,0524 (0,0522 a 0,0526) | 0,0555 | +0,000 (−0,004 a +0,006) | 0,99 (0,99 a 1,00) | 0 (0) |
| REING_30D | LR | A | sin | NO | 0,0525 (0,0522 a 0,0527) | 0,0555 | +0,000 (−0,005 a +0,005) | 0,99 (0,99 a 1,00) | 0 (0) |
| REING_30D | LR | agrupada | con | NO | 0,0524 (0,0522 a 0,0527) | 0,0555 | +0,000 (−0,005 a +0,005) | 0,99 (0,99 a 1,00) | 0 (0) |
| REING_30D | LR | C | con | NO | 0,0524 (0,0521 a 0,0526) | 0,0555 | +0,001 (−0,004 a +0,006) | 0,98 (0,97 a 0,98) | 0 (0) |
| REING_30D | RF | A | con | NO | 0,0522 (0,0519 a 0,0524) | 0,0555 | −0,001 (−0,006 a +0,004) | 0,89 (0,88 a 0,89) | 56.622 (401) |
| REING_30D | RF | A | sin | NO | 0,0522 (0,0520 a 0,0524) | 0,0555 | −0,007 (−0,012 a −0,002) | 0,89 (0,88 a 0,89) | 49.717 (346) |
| REING_30D | RF | agrupada | con | NO | 0,0522 (0,0520 a 0,0524) | 0,0555 | −0,006 (−0,011 a −0,001) | 0,89 (0,88 a 0,89) | 58.012 (391) |
| REING_30D | RF | C | con | NO | 0,0521 (0,0519 a 0,0524) | 0,0555 | +0,019 (+0,014 a +0,024) | 0,92 (0,91 a 0,92) | 48.935 (322) |
| REING_30D | XGB | A | con | NO | 0,0520 (0,0518 a 0,0522) | 0,0555 | +0,002 (−0,003 a +0,006) | 1,00 (0,99 a 1,00) | 0 (0) |
| REING_30D | XGB | A | sin | NO | 0,0521 (0,0518 a 0,0523) | 0,0555 | +0,002 (−0,003 a +0,006) | 0,99 (0,99 a 1,00) | 0 (0) |
| REING_30D | XGB | agrupada | con | NO | 0,0520 (0,0518 a 0,0522) | 0,0555 | +0,002 (−0,003 a +0,006) | 1,00 (0,99 a 1,00) | 0 (0) |
| REING_30D | XGB | C | con | NO | 0,0520 (0,0518 a 0,0522) | 0,0555 | +0,002 (−0,003 a +0,006) | 1,01 (1,00 a 1,01) | 0 (0) |
| REING_30D_CDM | LR | A | con | NO | 0,0328 (0,0326 a 0,0330) | 0,0343 | +0,001 (−0,006 a +0,008) | 0,99 (0,98 a 1,00) | 0 (0) |
| REING_30D_CDM | LR | A | sin | NO | 0,0328 (0,0326 a 0,0330) | 0,0343 | +0,001 (−0,006 a +0,008) | 0,99 (0,98 a 1,00) | 0 (0) |
| REING_30D_CDM | LR | agrupada | con | NO | 0,0328 (0,0326 a 0,0330) | 0,0343 | +0,001 (−0,006 a +0,008) | 0,99 (0,98 a 1,00) | 0 (0) |
| REING_30D_CDM | LR | C | con | NO | 0,0327 (0,0325 a 0,0329) | 0,0343 | +0,002 (−0,005 a +0,009) | 0,97 (0,96 a 0,98) | 0 (0) |
| REING_30D_CDM | RF | A | con | NO | 0,0326 (0,0324 a 0,0328) | 0,0343 | −0,017 (−0,024 a −0,010) | 0,87 (0,86 a 0,88) | 156.822 (532) |
| REING_30D_CDM | RF | A | sin | NO | 0,0326 (0,0324 a 0,0328) | 0,0343 | −0,025 (−0,032 a −0,018) | 0,88 (0,87 a 0,89) | 149.378 (488) |
| REING_30D_CDM | RF | agrupada | con | NO | 0,0326 (0,0324 a 0,0328) | 0,0343 | −0,019 (−0,026 a −0,012) | 0,88 (0,87 a 0,89) | 153.065 (499) |
| REING_30D_CDM | RF | C | con | NO | 0,0326 (0,0324 a 0,0328) | 0,0343 | −0,004 (−0,011 a +0,003) | 0,91 (0,90 a 0,92) | 136.293 (404) |
| REING_30D_CDM | XGB | A | con | NO | 0,0325 (0,0323 a 0,0327) | 0,0343 | +0,004 (−0,003 a +0,011) | 1,00 (1,00 a 1,01) | 0 (0) |
| REING_30D_CDM | XGB | A | sin | NO | 0,0325 (0,0323 a 0,0327) | 0,0343 | +0,004 (−0,003 a +0,010) | 1,00 (0,99 a 1,01) | 0 (0) |
| REING_30D_CDM | XGB | agrupada | con | NO | 0,0325 (0,0323 a 0,0327) | 0,0343 | +0,004 (−0,003 a +0,011) | 1,01 (1,00 a 1,01) | 0 (0) |
| REING_30D_CDM | XGB | C | con | NO | 0,0325 (0,0323 a 0,0327) | 0,0343 | +0,004 (−0,003 a +0,010) | 1,02 (1,01 a 1,02) | 0 (0) |

## 5. Calibración por año del alta (lista A con hospital, D56)

| Variable | Modelo | Año | Casos | Observado | Predicho | Intercepto | Pendiente |
|---|---|---|---|---|---|---|---|
| REING_7D | LR | 2019 | 644.415 | 2,04 % | 1,94 % | +0,056 (+0,038 a +0,074) | 1,01 (0,99 a 1,04) |
| REING_7D | LR | 2020 | 446.923 | 2,10 % | 2,00 % | +0,049 (+0,028 a +0,072) | 0,96 (0,94 a 0,99) |
| REING_7D | LR | 2021 | 508.698 | 1,94 % | 2,07 % | −0,069 (−0,091 a −0,047) | 1,03 (1,00 a 1,05) |
| REING_7D | LR | 2022 | 564.053 | 1,94 % | 2,07 % | −0,070 (−0,090 a −0,051) | 1,00 (0,97 a 1,02) |
| REING_7D | LR | 2023 | 615.867 | 2,13 % | 2,12 % | +0,005 (−0,013 a +0,022) | 0,97 (0,94 a 0,99) |
| REING_7D | LR | 2024 | 567.696 | 2,25 % | 2,20 % | +0,024 (+0,005 a +0,042) | 0,95 (0,92 a 0,97) |
| REING_7D | RF | 2019 | 644.415 | 2,04 % | 1,96 % | +0,043 (+0,026 a +0,061) | 0,59 (0,57 a 0,61) |
| REING_7D | RF | 2020 | 446.923 | 2,10 % | 2,06 % | +0,018 (−0,003 a +0,039) | 0,59 (0,57 a 0,62) |
| REING_7D | RF | 2021 | 508.698 | 1,94 % | 2,05 % | −0,058 (−0,079 a −0,036) | 0,66 (0,63 a 0,69) |
| REING_7D | RF | 2022 | 564.053 | 1,94 % | 2,12 % | −0,096 (−0,116 a −0,078) | 0,65 (0,62 a 0,68) |
| REING_7D | RF | 2023 | 615.867 | 2,13 % | 2,17 % | −0,024 (−0,042 a −0,006) | 0,63 (0,61 a 0,66) |
| REING_7D | RF | 2024 | 567.696 | 2,25 % | 2,27 % | −0,008 (−0,025 a +0,010) | 0,66 (0,63 a 0,68) |
| REING_7D | XGB | 2019 | 644.415 | 2,04 % | 1,93 % | +0,058 (+0,041 a +0,076) | 0,96 (0,94 a 0,98) |
| REING_7D | XGB | 2020 | 446.923 | 2,10 % | 2,02 % | +0,041 (+0,021 a +0,063) | 0,94 (0,92 a 0,96) |
| REING_7D | XGB | 2021 | 508.698 | 1,94 % | 2,04 % | −0,057 (−0,079 a −0,036) | 0,99 (0,97 a 1,01) |
| REING_7D | XGB | 2022 | 564.053 | 1,94 % | 2,07 % | −0,072 (−0,091 a −0,053) | 0,97 (0,95 a 0,99) |
| REING_7D | XGB | 2023 | 615.867 | 2,13 % | 2,12 % | +0,005 (−0,012 a +0,022) | 0,95 (0,93 a 0,97) |
| REING_7D | XGB | 2024 | 567.696 | 2,25 % | 2,19 % | +0,028 (+0,011 a +0,046) | 0,94 (0,93 a 0,96) |
| REING_7D_CDM | LR | 2019 | 544.868 | 1,25 % | 1,19 % | +0,046 (+0,023 a +0,070) | 1,03 (1,00 a 1,06) |
| REING_7D_CDM | LR | 2020 | 369.956 | 1,27 % | 1,25 % | +0,020 (−0,009 a +0,050) | 0,94 (0,91 a 0,97) |
| REING_7D_CDM | LR | 2021 | 433.203 | 1,20 % | 1,27 % | −0,056 (−0,085 a −0,028) | 0,96 (0,93 a 1,00) |
| REING_7D_CDM | LR | 2022 | 477.527 | 1,22 % | 1,27 % | −0,044 (−0,072 a −0,016) | 0,97 (0,94 a 0,99) |
| REING_7D_CDM | LR | 2023 | 531.434 | 1,30 % | 1,29 % | +0,009 (−0,017 a +0,035) | 0,99 (0,96 a 1,01) |
| REING_7D_CDM | LR | 2024 | 498.331 | 1,35 % | 1,32 % | +0,022 (−0,004 a +0,048) | 0,96 (0,94 a 0,99) |
| REING_7D_CDM | RF | 2019 | 544.868 | 1,25 % | 1,23 % | +0,014 (−0,009 a +0,039) | 0,64 (0,62 a 0,67) |
| REING_7D_CDM | RF | 2020 | 369.956 | 1,27 % | 1,30 % | −0,027 (−0,056 a +0,004) | 0,61 (0,58 a 0,65) |
| REING_7D_CDM | RF | 2021 | 433.203 | 1,20 % | 1,25 % | −0,048 (−0,077 a −0,020) | 0,60 (0,57 a 0,63) |
| REING_7D_CDM | RF | 2022 | 477.527 | 1,22 % | 1,30 % | −0,075 (−0,103 a −0,049) | 0,63 (0,60 a 0,66) |
| REING_7D_CDM | RF | 2023 | 531.434 | 1,30 % | 1,32 % | −0,016 (−0,042 a +0,010) | 0,64 (0,61 a 0,67) |
| REING_7D_CDM | RF | 2024 | 498.331 | 1,35 % | 1,36 % | −0,008 (−0,034 a +0,018) | 0,64 (0,61 a 0,67) |
| REING_7D_CDM | XGB | 2019 | 544.868 | 1,25 % | 1,20 % | +0,045 (+0,023 a +0,070) | 0,97 (0,95 a 0,99) |
| REING_7D_CDM | XGB | 2020 | 369.956 | 1,27 % | 1,26 % | +0,012 (−0,018 a +0,042) | 0,94 (0,91 a 0,96) |
| REING_7D_CDM | XGB | 2021 | 433.203 | 1,20 % | 1,24 % | −0,035 (−0,064 a −0,007) | 0,96 (0,94 a 0,99) |
| REING_7D_CDM | XGB | 2022 | 477.527 | 1,22 % | 1,27 % | −0,045 (−0,073 a −0,019) | 0,94 (0,92 a 0,96) |
| REING_7D_CDM | XGB | 2023 | 531.434 | 1,30 % | 1,29 % | +0,010 (−0,016 a +0,036) | 0,95 (0,93 a 0,97) |
| REING_7D_CDM | XGB | 2024 | 498.331 | 1,35 % | 1,31 % | +0,033 (+0,007 a +0,057) | 0,95 (0,92 a 0,97) |
| REING_30D | LR | 2019 | 644.415 | 5,70 % | 5,51 % | +0,037 (+0,026 a +0,049) | 1,04 (1,03 a 1,05) |
| REING_30D | LR | 2020 | 413.202 | 5,66 % | 5,70 % | −0,007 (−0,021 a +0,007) | 0,98 (0,97 a 1,00) |
| REING_30D | LR | 2021 | 508.698 | 5,62 % | 5,83 % | −0,042 (−0,054 a −0,029) | 1,03 (1,02 a 1,05) |
| REING_30D | LR | 2022 | 564.053 | 5,76 % | 5,88 % | −0,023 (−0,036 a −0,011) | 0,98 (0,97 a 0,99) |
| REING_30D | LR | 2023 | 615.867 | 6,14 % | 6,09 % | +0,010 (−0,001 a +0,021) | 0,97 (0,96 a 0,98) |
| REING_30D | LR | 2024 | 529.197 | 6,45 % | 6,37 % | +0,015 (+0,003 a +0,026) | 0,96 (0,94 a 0,97) |
| REING_30D | RF | 2019 | 644.415 | 5,70 % | 5,36 % | +0,069 (+0,058 a +0,080) | 0,88 (0,87 a 0,90) |
| REING_30D | RF | 2020 | 413.202 | 5,66 % | 5,70 % | −0,008 (−0,021 a +0,007) | 0,88 (0,86 a 0,90) |
| REING_30D | RF | 2021 | 508.698 | 5,62 % | 5,70 % | −0,016 (−0,028 a −0,003) | 0,91 (0,89 a 0,93) |
| REING_30D | RF | 2022 | 564.053 | 5,76 % | 5,99 % | −0,044 (−0,056 a −0,031) | 0,89 (0,88 a 0,91) |
| REING_30D | RF | 2023 | 615.867 | 6,14 % | 6,19 % | −0,009 (−0,020 a +0,002) | 0,88 (0,86 a 0,89) |
| REING_30D | RF | 2024 | 529.197 | 6,45 % | 6,51 % | −0,010 (−0,022 a +0,001) | 0,88 (0,87 a 0,90) |
| REING_30D | XGB | 2019 | 644.415 | 5,70 % | 5,49 % | +0,041 (+0,030 a +0,052) | 1,02 (1,01 a 1,03) |
| REING_30D | XGB | 2020 | 413.202 | 5,66 % | 5,71 % | −0,009 (−0,023 a +0,005) | 0,99 (0,98 a 1,00) |
| REING_30D | XGB | 2021 | 508.698 | 5,62 % | 5,77 % | −0,029 (−0,042 a −0,016) | 1,02 (1,01 a 1,04) |
| REING_30D | XGB | 2022 | 564.053 | 5,76 % | 5,90 % | −0,027 (−0,040 a −0,015) | 0,99 (0,98 a 1,01) |
| REING_30D | XGB | 2023 | 615.867 | 6,14 % | 6,10 % | +0,008 (−0,003 a +0,018) | 0,99 (0,98 a 1,00) |
| REING_30D | XGB | 2024 | 529.197 | 6,45 % | 6,36 % | +0,015 (+0,003 a +0,027) | 0,98 (0,97 a 0,99) |
| REING_30D_CDM | LR | 2019 | 544.868 | 3,49 % | 3,38 % | +0,034 (+0,018 a +0,049) | 1,05 (1,04 a 1,07) |
| REING_30D_CDM | LR | 2020 | 341.220 | 3,40 % | 3,49 % | −0,027 (−0,047 a −0,007) | 0,98 (0,96 a 1,00) |
| REING_30D_CDM | LR | 2021 | 433.203 | 3,37 % | 3,49 % | −0,038 (−0,058 a −0,021) | 0,98 (0,96 a 1,00) |
| REING_30D_CDM | LR | 2022 | 477.527 | 3,52 % | 3,54 % | −0,009 (−0,026 a +0,008) | 0,98 (0,96 a 1,00) |
| REING_30D_CDM | LR | 2023 | 531.434 | 3,69 % | 3,65 % | +0,011 (−0,004 a +0,028) | 0,98 (0,96 a 0,99) |
| REING_30D_CDM | LR | 2024 | 464.230 | 3,79 % | 3,74 % | +0,015 (−0,001 a +0,031) | 0,96 (0,94 a 0,97) |
| REING_30D_CDM | RF | 2019 | 544.868 | 3,49 % | 3,38 % | +0,033 (+0,018 a +0,048) | 0,89 (0,87 a 0,91) |
| REING_30D_CDM | RF | 2020 | 341.220 | 3,40 % | 3,57 % | −0,051 (−0,072 a −0,032) | 0,87 (0,85 a 0,90) |
| REING_30D_CDM | RF | 2021 | 433.203 | 3,37 % | 3,45 % | −0,026 (−0,045 a −0,008) | 0,85 (0,83 a 0,87) |
| REING_30D_CDM | RF | 2022 | 477.527 | 3,52 % | 3,67 % | −0,046 (−0,063 a −0,030) | 0,87 (0,85 a 0,90) |
| REING_30D_CDM | RF | 2023 | 531.434 | 3,69 % | 3,74 % | −0,016 (−0,031 a +0,001) | 0,87 (0,85 a 0,89) |
| REING_30D_CDM | RF | 2024 | 464.230 | 3,79 % | 3,84 % | −0,013 (−0,030 a +0,002) | 0,88 (0,86 a 0,90) |
| REING_30D_CDM | XGB | 2019 | 544.868 | 3,49 % | 3,37 % | +0,038 (+0,023 a +0,054) | 1,04 (1,02 a 1,05) |
| REING_30D_CDM | XGB | 2020 | 341.220 | 3,40 % | 3,50 % | −0,033 (−0,052 a −0,014) | 1,00 (0,98 a 1,02) |
| REING_30D_CDM | XGB | 2021 | 433.203 | 3,37 % | 3,42 % | −0,019 (−0,037 a −0,002) | 1,00 (0,99 a 1,02) |
| REING_30D_CDM | XGB | 2022 | 477.527 | 3,52 % | 3,57 % | −0,016 (−0,033 a −0,000) | 1,00 (0,99 a 1,02) |
| REING_30D_CDM | XGB | 2023 | 531.434 | 3,69 % | 3,65 % | +0,011 (−0,005 a +0,027) | 1,00 (0,98 a 1,01) |
| REING_30D_CDM | XGB | 2024 | 464.230 | 3,79 % | 3,71 % | +0,023 (+0,007 a +0,039) | 0,98 (0,97 a 1,00) |

## 6. AUPRC / AUROC de cada vuelta (lista A con hospital, D63)

| Variable | Modelo | Vuelta 1 | Vuelta 2 | Vuelta 3 | Vuelta 4 | Vuelta 5 |
|---|---|---|---|---|---|---|
| REING_7D | LR | 0,058 / 0,713 | 0,058 / 0,713 | 0,058 / 0,715 | 0,058 / 0,712 | 0,058 / 0,711 |
| REING_7D | RF | 0,063 / 0,705 | 0,063 / 0,706 | 0,064 / 0,708 | 0,065 / 0,706 | 0,065 / 0,705 |
| REING_7D | XGB | 0,068 / 0,729 | 0,067 / 0,729 | 0,068 / 0,734 | 0,068 / 0,730 | 0,068 / 0,728 |
| REING_7D_CDM | LR | 0,048 / 0,741 | 0,048 / 0,737 | 0,048 / 0,741 | 0,048 / 0,740 | 0,052 / 0,740 |
| REING_7D_CDM | RF | 0,056 / 0,731 | 0,056 / 0,728 | 0,057 / 0,734 | 0,058 / 0,733 | 0,060 / 0,731 |
| REING_7D_CDM | XGB | 0,060 / 0,768 | 0,058 / 0,764 | 0,059 / 0,770 | 0,061 / 0,768 | 0,060 / 0,767 |
| REING_30D | LR | 0,168 / 0,749 | 0,169 / 0,748 | 0,170 / 0,749 | 0,169 / 0,749 | 0,168 / 0,748 |
| REING_30D | RF | 0,178 / 0,750 | 0,179 / 0,750 | 0,180 / 0,751 | 0,177 / 0,750 | 0,178 / 0,749 |
| REING_30D | XGB | 0,181 / 0,758 | 0,181 / 0,757 | 0,182 / 0,758 | 0,181 / 0,758 | 0,180 / 0,756 |
| REING_30D_CDM | LR | 0,121 / 0,758 | 0,121 / 0,756 | 0,124 / 0,760 | 0,121 / 0,758 | 0,123 / 0,758 |
| REING_30D_CDM | RF | 0,133 / 0,760 | 0,132 / 0,760 | 0,137 / 0,764 | 0,132 / 0,762 | 0,133 / 0,760 |
| REING_30D_CDM | XGB | 0,135 / 0,778 | 0,134 / 0,775 | 0,138 / 0,778 | 0,136 / 0,778 | 0,137 / 0,776 |

## 7. La lista A frente a las otras listas (D64)

Caída de la lista A frente a cada otra lista, sorteo por sorteo con los mismos pacientes: el AUROC en puntos y la AUPRC como proporción del valor de la otra lista. Márgenes del objetivo específico 3: 0,02 y 10 %. **Pierde** si alguna caída pasa entera su margen; **no pierde** si las dos quedan enteras dentro; si no, **no se puede afirmar**. Si la A pierde, se lleva al profesor guía antes de la actividad 3.3.

| Variable | Modelo | Frente a | Caída de la AUPRC | Caída del AUROC | Veredicto |
|---|---|---|---|---|---|
| REING_7D | LR | agrupada | 0,1 % (−0,3 % a 0,5 %) | −0,001 (−0,001 a −0,000) | No pierde |
| REING_7D | LR | C | 0,9 % (0,2 % a 1,5 %) | +0,007 (+0,006 a +0,007) | No pierde |
| REING_7D | RF | agrupada | 1,6 % (0,7 % a 2,5 %) | +0,001 (+0,000 a +0,003) | No pierde |
| REING_7D | RF | C | 1,5 % (0,6 % a 2,4 %) | +0,004 (+0,003 a +0,006) | No pierde |
| REING_7D | XGB | agrupada | 1,3 % (0,3 % a 2,2 %) | +0,001 (+0,000 a +0,002) | No pierde |
| REING_7D | XGB | C | 0,3 % (−0,5 % a 1,0 %) | +0,000 (−0,000 a +0,001) | No pierde |
| REING_7D_CDM | LR | agrupada | 1,3 % (0,4 % a 2,3 %) | +0,000 (−0,000 a +0,001) | No pierde |
| REING_7D_CDM | LR | C | 4,7 % (3,5 % a 6,0 %) | +0,011 (+0,010 a +0,012) | No pierde |
| REING_7D_CDM | RF | agrupada | 1,2 % (−0,3 % a 2,7 %) | +0,001 (−0,001 a +0,003) | No pierde |
| REING_7D_CDM | RF | C | 1,2 % (−0,1 % a 2,4 %) | +0,003 (+0,001 a +0,004) | No pierde |
| REING_7D_CDM | XGB | agrupada | 1,3 % (−0,4 % a 3,0 %) | +0,001 (−0,000 a +0,001) | No pierde |
| REING_7D_CDM | XGB | C | −0,4 % (−2,3 % a 1,6 %) | −0,000 (−0,001 a +0,001) | No pierde |
| REING_30D | LR | agrupada | −0,3 % (−0,5 % a −0,1 %) | −0,000 (−0,001 a −0,000) | No pierde |
| REING_30D | LR | C | 0,7 % (0,5 % a 0,9 %) | +0,003 (+0,003 a +0,003) | No pierde |
| REING_30D | RF | agrupada | −0,1 % (−0,5 % a 0,2 %) | +0,000 (−0,000 a +0,001) | No pierde |
| REING_30D | RF | C | 0,3 % (−0,1 % a 0,6 %) | +0,002 (+0,001 a +0,002) | No pierde |
| REING_30D | XGB | agrupada | −0,1 % (−0,4 % a 0,3 %) | +0,000 (−0,000 a +0,000) | No pierde |
| REING_30D | XGB | C | −0,1 % (−0,4 % a 0,1 %) | −0,000 (−0,001 a −0,000) | No pierde |
| REING_30D_CDM | LR | agrupada | −0,4 % (−0,8 % a −0,1 %) | +0,001 (+0,000 a +0,001) | No pierde |
| REING_30D_CDM | LR | C | 1,9 % (1,5 % a 2,2 %) | +0,008 (+0,007 a +0,008) | No pierde |
| REING_30D_CDM | RF | agrupada | −0,0 % (−0,6 % a 0,5 %) | +0,001 (+0,000 a +0,002) | No pierde |
| REING_30D_CDM | RF | C | 0,9 % (0,4 % a 1,4 %) | +0,002 (+0,001 a +0,003) | No pierde |
| REING_30D_CDM | XGB | agrupada | 0,9 % (0,3 % a 1,5 %) | +0,002 (+0,001 a +0,002) | No pierde |
| REING_30D_CDM | XGB | C | −0,9 % (−1,4 % a −0,4 %) | −0,000 (−0,001 a +0,000) | No pierde |

Veredictos: No pierde: 24.

## 8. La lista A sin hospital (D64, solo informa)

Cuánto pierde el modelo sin `HOSPITAL`, con la misma cuenta: la caída sin hospital frente a con hospital.

| Variable | Modelo | Frente a | Caída de la AUPRC | Caída del AUROC | Veredicto |
|---|---|---|---|---|---|
| REING_7D | LR | con hospital | 1,3 % (1,0 % a 1,7 %) | +0,002 (+0,002 a +0,003) | No pierde (solo informa) |
| REING_7D | RF | con hospital | 0,8 % (−0,1 % a 1,6 %) | +0,002 (+0,001 a +0,003) | No pierde (solo informa) |
| REING_7D | XGB | con hospital | 1,5 % (0,6 % a 2,3 %) | +0,002 (+0,002 a +0,003) | No pierde (solo informa) |
| REING_7D_CDM | LR | con hospital | 1,4 % (1,0 % a 1,8 %) | +0,002 (+0,002 a +0,003) | No pierde (solo informa) |
| REING_7D_CDM | RF | con hospital | 3,5 % (2,1 % a 4,7 %) | +0,003 (+0,001 a +0,005) | No pierde (solo informa) |
| REING_7D_CDM | XGB | con hospital | 1,6 % (−0,3 % a 3,4 %) | +0,003 (+0,002 a +0,003) | No pierde (solo informa) |
| REING_30D | LR | con hospital | 0,9 % (0,8 % a 1,1 %) | +0,001 (+0,001 a +0,001) | No pierde (solo informa) |
| REING_30D | RF | con hospital | 0,7 % (0,3 % a 1,0 %) | +0,001 (+0,000 a +0,001) | No pierde (solo informa) |
| REING_30D | XGB | con hospital | 0,8 % (0,6 % a 1,1 %) | +0,001 (+0,000 a +0,001) | No pierde (solo informa) |
| REING_30D_CDM | LR | con hospital | 0,8 % (0,6 % a 0,9 %) | +0,001 (+0,001 a +0,001) | No pierde (solo informa) |
| REING_30D_CDM | RF | con hospital | 0,6 % (0,0 % a 1,2 %) | +0,000 (−0,000 a +0,001) | No pierde (solo informa) |
| REING_30D_CDM | XGB | con hospital | 0,5 % (−0,0 % a 1,0 %) | +0,000 (−0,000 a +0,001) | No pierde (solo informa) |

## 9. Combinaciones

Con métricas: 51 de 63.

| Etapa del script 17 | Combinaciones | Con métricas | Faltan |
|---|---|---|---|
| `ensayo` | 6 | 6 | 0 |
| `base` | 9 | 9 | 0 |
| `sin_filtro` | 12 | 0 | 12 |
| `agrupada` | 12 | 12 | 0 |
| `sin_hospital` | 12 | 12 | 0 |
| `c` | 12 | 12 | 0 |

Faltan: `REING_7D__LR__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_7D__RF__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_7D__XGB__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_7D_CDM__LR__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_7D_CDM__RF__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_7D_CDM__XGB__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D__LR__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D__RF__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D__XGB__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D_CDM__LR__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D_CDM__RF__SIN_FILTRO__con_hospital__sin_ponderar`, `REING_30D_CDM__XGB__SIN_FILTRO__con_hospital__sin_ponderar`.

