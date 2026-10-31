# Validación e interpretación

> Plantilla en blanco. Complétala **después** de ejecutar `notebooks/07_validacion_interpretacion.ipynb`.
> Todo lo que escribas aquí lo tienes que poder sostener ante una pregunta del instructor.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | | |
| Parámetros (optimizados o de partida) | | |
| ¿Corregir el sesgo al volver del logaritmo? (`exp` de la predicción tiende a subestimar) | | |
| Métrica principal | MAE en USD por noche | `especificacion-proyecto.md`, sección 4 |
| Regla de decisión (cómo se entrega el precio sugerido: valor puntual, rango, redondeo) | | |
| **Fecha y hora en que se congelaron** | | |

## 2. Corrección al volver del logaritmo (con entidades reservadas, no con la prueba)

> En regresión no hay probabilidades que calibrar. El equivalente es revisar si `exp(predicción)` queda sistemáticamente
> por debajo del precio real y si conviene un factor de corrección.

- ¿Se evaluó? ☐ sí  ☐ no → si no, por qué no hace falta: _______________
- Resultado y decisión: _______________

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió (la marca está en `reports/prueba_abierta.txt`): _______________
- ¿Se cambió algo del modelo después de verla? ☐ no  ☐ sí → qué y por qué (hay que declararlo): _______________

| Métrica | Modelo final | Baseline | Intervalo del 95 % (entidades) |
|---|---|---|---|
| MAE (USD por noche) | | | |
| MAPE (%) | | | |
| R² | | | |

> **Declarar siempre (auditoría de fuga, 2026-10-30):** la prueba excluye por ciudad los precios fuera de [0,1 ×, 20 ×] la
> mediana del entrenamiento (182 filas en la prueba en seco; cifra final en `reports/03_exclusiones.csv`). El MAE de arriba es
> sobre "anuncios con precio plausible". Reportar también, una sola vez y sin usarlo para decidir, el MAE sin ese filtro: la
> app no filtra nada.

- MAE sin el filtro de extremos (sensibilidad): _______________

**¿Mejora al baseline con confianza?** (¿el intervalo de la diferencia excluye el cero?): _______________

## 4. Errores y carga de trabajo

| Segmento (ciudad / `room_type`) | Anuncios | MAE (USD) | MAPE (%) | Sesgo medio (USD) |
|---|---|---|---|---|
| Río de Janeiro | | | | |
| São Paulo | | | | |
| Ciudad de México | | | | |
| Buenos Aires | | | | |
| Bogotá | | | | |
| Santiago | | | | |
| Belice | | | | |

- ¿Hay un segmento al que le va peor? ¿Por qué podría ser?: _______________
- ¿El modelo sobrestima más de lo que subestima? (para el inversionista sobrestimar es el error caro): _______________

## 5. Interpretación

- Variables que más pesan (y qué significa para el negocio): _______________
- **Límite de la explicación:** explica al modelo, no al mundo; no dice si el modelo acertó: _______________
- Atributos sensibles o de uso regulado entre las variables (¿cuáles, y qué se hace?): _______________

## 6. Conclusión

- ¿El modelo sirve para la decisión del caso? ¿Con qué condiciones?: _______________
- Qué NO debe hacerse con él: _______________
