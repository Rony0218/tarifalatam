# Validación e interpretación

> Cifras de `notebooks/07_validacion_interpretacion.ipynb` (ejecutado el 2026-11-05) y de `reports/07_metricas_test.json`,
> `07_decisiones.json`, `07_segmentos.csv` y `07_shap_global.csv`. Especificación: `especificaciones/07-validacion-registro-app.md`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | LightGBM con las 13 columnas de la referencia | Etapa 6. **Excepción a la regla escrita, decidida por el grupo después de ver el resultado (T047):** los dos finalistas optimizados empataron en los anfitriones reservados y la regla elegía el bosque aleatorio (más rápido de ajustar); el grupo eligió LightGBM por su MAE más bajo en los reservados (dentro del ruido) y por ser más simple de operar en la app |
| Parámetros (optimizados o de partida) | Optimizados (ensayo 30, `reports/06_best_params.json`) | En los anfitriones reservados la mejora fue distinguible del ruido: MAE de 38,86 a 38,52 USD, intervalo de la diferencia [−0,64; −0,01] |
| ¿Corregir el sesgo al volver del logaritmo? | **No** | Sección 2: con los anfitriones reservados, el factor de Duan **empeora** el MAE |
| Métrica principal | MAE en USD por noche | `especificacion-proyecto.md`, sección 4 |
| Regla de decisión (cómo se entrega el precio) | Precio puntual redondeado al dólar y un **rango típico** de su ciudad: el precio × los percentiles 25 y 75 de *precio real / precio sugerido* en los anfitriones reservados | Respuesta 2 del grupo (2026-11-05) |
| Meta de éxito | (a) MAE al menos 20 % menor que la línea base; (b) intervalo del 95 % de la diferencia entero bajo cero; (c) ninguna ciudad con MAE mayor que el de la línea base | PR #5 de Rafael Jaramillo, respuesta 1 del grupo (2026-11-05) |
| **Fecha y hora en que se congelaron** | **2026-11-05 17:42 (UTC−5)** | Aprobación de la especificación por el grupo. Constancia en `reports/07_decisiones.json` (escrito a las 18:09:30, antes de la apertura) |

## 2. Corrección al volver del logaritmo (con entidades reservadas, no con la prueba)

- ¿Se evaluó? ☒ sí  ☐ no
- **Cómo:** los mismos 25 % de anfitriones reservados de la etapa 6 (29.023 anuncios de 13.347 anfitriones). El factor de
  Duan (promedio de `exp(residuo)`) salió de residuos fuera de pliegue en la búsqueda: **1,1243**. El modelo, ajustado con la
  búsqueda, da en los reservados un MAE de **38,52 USD sin factor** (el mismo de la etapa 6) y **41,16 USD con factor**.
- **Resultado y decisión:** la diferencia (con − sin) es **+2,64 USD**, intervalo del 95 % por anfitrión **[+2,21; +3,06]**:
  el factor empeora el error con confianza. Por la regla aprobada (se usa solo si el intervalo queda entero bajo cero) **no
  se aplica corrección**. Tiene sentido: el factor sube todos los precios para acercar el *promedio*, pero el MAE premia
  acercarse a la *mediana*, que es lo que ya da `exp(predicción)`.
- **Rango típico** (mismas predicciones de los reservados), percentiles 25 y 75 de *real / sugerido*:

  | Ciudad | p25 | p75 |
  |---|---|---|
  | Belice | 0,744 | 1,354 |
  | Bogotá | 0,781 | 1,149 |
  | Ciudad de México | 0,773 | 1,250 |
  | Río de Janeiro | 0,724 | 1,277 |
  | Santiago | 0,815 | 1,152 |
  | São Paulo | 0,822 | 1,209 |

  Para un precio sugerido de 100 USD en Bogotá, la app muestra un rango de 78 a 115 USD: en anfitriones que el modelo no vio,
  la mitad de los anuncios de Bogotá quedó dentro de ese rango.

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió (`reports/prueba_abierta.txt`): **2026-11-05 18:09:33**, propósito "evaluación única de la
  etapa 7". Antes de abrirla se hizo un **ensayo** del notebook con los anfitriones reservados en lugar de la prueba, solo
  para encontrar errores de código; ninguna cifra del ensayo se usa.
- **Todas las veces que se miraron los anuncios de prueba** (la marca las anota): (1) la apertura de las 18:09:33; (2) en
  esa misma ejecución, la sección 6 reconstruyó desde `data/raw/` los anuncios de los mismos anfitriones **sin** el filtro
  de extremos, para la sensibilidad (la marca lo anota a mano, tras la auditoría); (3) a las 18:17:27, el notebook 09 la
  leyó otra vez **solo** para comprobar que `models/model.joblib` da el mismo MAE. Ninguna de las tres cambió una decisión.
- ¿Se cambió algo del modelo después de verla? ☒ no  ☐ sí
- **Prueba:** 29.721 anuncios de 13.345 anfitriones que el modelo nunca vio (São Paulo 8.283 · Río 8.246 · Ciudad de México
  5.388 · Bogotá 3.552 · Santiago 3.399 · Belice 853).

| Métrica | Modelo final | Baseline | Intervalo del 95 % (anfitriones) |
|---|---|---|---|
| MAE (USD por noche) | **41,40** | 57,44 | modelo [38,29; 45,01] · línea base [53,18; 62,50] |
| MAPE (%) | 31,78 | 42,39 | — |
| R² (sobre el logaritmo) | 0,67 | 0,33 | — |
| RMSE (USD) | 120,53 | 159,57 | — |
| Sesgo medio (USD, sugerido − real) | −14,36 | −34,86 | — |
| Costo 2 a 1 (control) | 54,92 | 68,73 | — |
| Costo 1,5 a 1 / 3 a 1 (sensibilidad) | 48,16 / 68,44 | 63,08 / 80,02 | — |

> **Declarar siempre (auditoría de fuga, 2026-10-30):** la prueba excluye por ciudad los precios fuera de [0,1 ×; 20 ×] la
> mediana del entrenamiento (**86 anuncios**, `reports/03_exclusiones.csv`). El MAE de arriba es sobre "anuncios con precio
> plausible". La app no filtra nada.

- **MAE sin el filtro de extremos (sensibilidad, una sola vez y sin decidir con ella):** con los 29.807 anuncios, el MAE del
  modelo es **56,81 USD** y el de la línea base 73,94 USD. Los 86 anuncios extremos suben el MAE del modelo en 15 USD: el
  modelo no predice precios absurdos, y en la app un anuncio así tendría un error grande.

**¿Mejora al baseline con confianza?** **Sí.** La diferencia de MAE (modelo − línea base) es **−16,04 USD** por noche, con
intervalo del 95 % por anfitrión **[−17,84; −14,36]**: todo el intervalo está bajo cero.

**Meta de éxito (escrita antes de abrir la prueba): SE CUMPLE.**

| Condición | Resultado | ¿Cumple? |
|---|---|---|
| (a) MAE al menos 20 % menor que la línea base | 27,9 % menor (41,40 frente a 57,44) | ☒ sí |
| (b) Intervalo del 95 % de la diferencia entero bajo cero | [−17,84; −14,36] | ☒ sí |
| (c) Ninguna ciudad con MAE mayor que el de la línea base | las seis mejoran (tabla de la sección 4) | ☒ sí |

El costo 2 a 1 (control) también es menor con el modelo en las tres proporciones: el supuesto del 2 a 1 no cambia la conclusión.

> **Uso repetido de los anfitriones reservados:** el mismo 25 % de anfitriones sirvió en la etapa 6 (optimizar o no, elegir
> finalista, la excepción T047) y aquí (factor del logaritmo y rango típico). No toca la prueba, pero sus cifras pueden
> salir algo optimistas; la cifra honesta es la de la prueba.

## 4. Errores y carga de trabajo

| Segmento (ciudad) | Anuncios | MAE (USD) | MAPE (%) | Sesgo medio (USD) | % sobrestimados | Error > 50 % del precio | MAE línea base |
|---|---|---|---|---|---|---|---|
| Río de Janeiro | 8.246 | 53,25 | 37,89 | −18,79 | 56,6 | 2.151 | 74,10 |
| São Paulo | 8.283 | 21,35 | 25,99 | −5,78 | 54,6 | 1.026 | 28,18 |
| Ciudad de México | 5.388 | 45,38 | 34,41 | −17,24 | 52,0 | 1.140 | 59,88 |
| Bogotá | 3.552 | 22,32 | 31,64 | −4,22 | 62,6 | 618 | 27,67 |
| Santiago | 3.399 | 23,80 | 25,57 | −6,64 | 50,8 | 388 | 41,91 |
| **Belice** | 853 | **245,96** | 37,58 | **−109,70** | 45,5 | 226 | 350,88 |

| Segmento (`room_type`) | Anuncios | MAE (USD) | MAPE (%) | Sesgo medio (USD) | MAE línea base |
|---|---|---|---|---|---|
| Entire home/apt | 23.855 | 42,61 | 29,42 | −13,80 | 60,93 |
| Private room | 5.609 | 35,62 | 40,70 | −16,00 | 42,13 |
| Hotel room | 76 | 149,20 | 46,37 | −111,34 | 196,60 |
| **Shared room** | 181 | 15,42 | 60,64 | +2,62 | **12,98** |

- **¿Hay un segmento al que le va peor? ¿Por qué podría ser?** **Belice**: MAE de 246 USD por noche y sesgo de −110 USD
  (subestima). Es la ciudad más pequeña (2.604 anuncios de entrenamiento, 2,2 %), con muchas villas y casas de playa de precio
  muy alto que se parecen poco a las otras cinco ciudades. Las **habitaciones de hotel** (76 anuncios) también fallan mucho. Y
  en las **habitaciones compartidas** (181 anuncios) el modelo es **peor que la línea base** (15,42 frente a 12,98 USD): la
  meta no lo pedía (mira ciudades), pero se declara como límite.
- **¿El modelo sobrestima más de lo que subestima?** En número de anuncios sobrestima un poco más de la mitad (50,8 % a 62,6 %
  según la ciudad, salvo Belice con 45,5 %), pero el **sesgo medio es negativo en todas las ciudades**: cuando subestima, se
  equivoca por más dinero (los precios altos). Para el inversionista, para quien sobrestimar es lo caro, esto es conservador;
  para el anfitrión significa que en los inmuebles caros el precio sugerido se queda corto.
- **Carga de trabajo:** no aplica tal cual (el modelo no prioriza revisiones). Su equivalente: anuncios con un error mayor a
  la mitad de su precio real, que irían mal servidos sin una revisión humana: 5.549 de 29.721 (18,7 %) con el modelo,
  frente a 9.204 (31,0 %) con la línea base (`reports/07_segmentos.csv`).

## 5. Interpretación

- **Variables que más pesan** (promedio de |SHAP| en logaritmo, 2.000 anuncios del entrenamiento, `reports/07_shap_global.csv`):
  `bedrooms` 0,119 · `accommodates` 0,108 · `longitude` 0,102 · `bathrooms_count` 0,093 · `latitude` 0,079 ·
  `neighbourhood_cleansed` 0,065 · `city` 0,056 · `property_type` 0,045 · `room_type` 0,044 · `minimum_nights` 0,042 ·
  `bathroom_shared` 0,035 · `maximum_nights` 0,014 · `beds` 0,010. **Para el negocio:** el precio lo explican sobre todo el
  **tamaño** (habitaciones, huéspedes, baños) y la **ubicación** (coordenadas, barrio, ciudad), en ese orden. Un aporte de
  0,10 equivale a cerca de un 10 % del precio.
- **Dos anuncios de la prueba:**
  - *Error mediano* (São Paulo, apartamento entero, 2 huéspedes): real 89 USD, sugerido 73 USD. Lo bajan los pocos baños,
    habitaciones y huéspedes, y la ciudad; lo sube el barrio.
  - *Mayor error* (Belice, habitación privada, 16 huéspedes): real 6.000 USD por noche, sugerido 391 USD. El modelo ya sube
    mucho el precio por la ciudad (+0,79) y por la capacidad (+0,55), pero un precio así queda fuera de lo que aprendió.
- **Límite de la explicación:** los valores SHAP explican al **modelo**, no al mundo: no dicen si el modelo acertó (el anuncio
  de Belice tiene aportes grandes y aun así un error enorme). Latitud, longitud, barrio y ciudad están correlacionadas y se
  reparten el crédito: si se quitara una, otra subiría. Una importancia alta no es causa.
- **Atributos sensibles o de uso regulado:** el modelo **no usa datos del anfitrión** (se eliminaron al cargar y `host_id`
  solo sirvió para partir). Usa la **ubicación** (coordenadas y barrio): el precio sugerido refleja el precio de mercado de cada
  barrio, con sus desigualdades. Antes de usarlo en producción habría que revisar que no se use para discriminar zonas.

## 6. Conclusión

- **¿El modelo sirve para la decisión del caso? ¿Con qué condiciones?** Sí, como **precio de referencia** para el anfitrión
  en las cinco ciudades grandes: se equivoca en promedio 41 USD por noche, 16 USD menos que la regla simple, y la mejora es
  clara en las seis ciudades. Con estas condiciones: mostrar siempre el **rango típico**, no solo el número; la tarifa la fija
  el anfitrión.
- **Qué NO debe hacerse con él:** usarlo en **Belice** sin revisión (error de 246 USD por noche) ni para habitaciones de hotel o
  compartidas; tomarlo como el precio que se **cobrará** (es el precio **publicado**); usarlo fuera de las seis ciudades o
  lejos de septiembre de 2026; y, para el inversionista, tomarlo como una respuesta a si un inmueble se paga (no hay ocupación,
  costos ni valor de compra en los datos).

## Revisión de los subagentes (2026-11-05, tarea T036)

**`auditor-de-fuga` — sin fuga que invalide la métrica; la prueba no decidió nada.** Comprobó que el factor del logaritmo y el
rango típico salen solo de los anfitriones reservados y antes de la apertura (decisiones 18:09:30, apertura 18:09:33), que los
intervalos remuestrean anfitriones, que las entradas son las 13 columnas (sin `host_id` ni sospechosas) y que el MAE no es
"demasiado bueno". Hallazgos y qué se hizo:

| Hallazgo | Qué se hizo |
|---|---|
| La reconstrucción sin filtro (`build_unfiltered_test`) no quedaba anotada en la marca | Se anotó a mano en `reports/prueba_abierta.txt` y en la sección 3 de este informe |
| `tests/test_no_test_set.py` no vigilaba esa vía, ni `app/` y `scripts/`, ni que `open_test` se llame una sola vez | Ahora prohíbe `open_test`, `build_unfiltered_test` y `_clean_and_split` en los notebooks 04–06 y 08, revisa `app/` y `scripts/`, y cuenta las llamadas: una en el 07 y una en el 09 |
| El aviso de Belice del esquema cita el MAE de la prueba | Se acepta: es solo un mensaje y no cambia ninguna predicción; se aclara en el notebook 09 |
| El rango típico se midió con el modelo ajustado al 75 % y se aplica al final (100 %) | Se declara en la ficha del modelo |
| Uso repetido de los reservados | Se declara arriba (sección 3) |

**`revisor-de-codigo-ia` — "aceptar con cambios".** 281 pruebas en verde; funciones cortas y explicables; sin secretos, rutas
personales ni datos personales en el código, los notebooks ni el esquema; `.gitignore` correcto. Hallazgos y qué se hizo:

| Hallazgo | Qué se hizo |
|---|---|
| La segunda lectura no estaba contada en los informes | Se cuenta aquí (sección 3) y en `especificacion-proyecto.md` |
| `segment_errors` y `success_goal` dividen por un valor que podría ser 0 | `segment_errors` deja fuera del MAPE los precios ≤ 0 y `success_goal` exige una línea base positiva, con pruebas. No cambia ninguna cifra: no hay precios ≤ 0 en la prueba |
| La salida de la celda de la ficha en el notebook 09 quedó vieja | Se volvió a ejecutar solo esa celda (no lee la prueba) |
| `build_schema` y `08_registro.json` no coincidían con el contrato | Se corrigieron `contracts/functions.md` y `data-model.md` para que digan lo que hace el código |
| `test_metrics` empieza por `test_` y pytest podría tomarla como prueba | Se deja así (el notebook 07 ya ejecutado la usa) y está protegida con `__test__ = False`; anotado en el contrato |

**Preguntas que el instructor podría hacer** (sugeridas por el revisor): ¿por qué la segunda lectura no invalida el resultado?;
¿por qué no usan el factor de Duan y cómo lo decidieron sin la prueba?; ¿por qué cumplen la condición (c) si Belice se equivoca
seis veces más que el promedio? (porque (c) compara con la línea base de la misma ciudad: 245,96 frente a 350,88 USD).
