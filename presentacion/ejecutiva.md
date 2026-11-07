---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · TarifaLatam"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · Problema

## Un anfitrión de Airbnb necesita saber cuánto cobrar por noche, y equivocarse sale caro

- **¿Quién decide?** El anfitrión (fija su tarifa). El inversionista usa el precio como un insumo más de sus cuentas
- **¿Qué decide con el resultado?** El anfitrión, cuánto cobrar por noche. El modelo no dice si un inmueble se paga
- **¿Cuánto cuesta equivocarse?** Cuesta distinto en cada dirección:
  - Precio **muy bajo**: pierde ingreso cada noche reservada
  - Precio **muy alto**: el inmueble queda vacío y la plataforma lo baja en las búsquedas
  - Para el inversionista, **sobrestimar** es lo más caro: compraría algo que no rinde

> **TarifaLatam sugiere un precio por noche, con su rango típico, según las características del inmueble, su barrio y su ciudad. La tarifa final la fija el anfitrión.**

---

# 2 · Enfoque

- **Los datos:** anuncios públicos de **Inside Airbnb** (septiembre de 2026) de seis ciudades: Río de Janeiro, São Paulo, Ciudad de México, Bogotá, Santiago y Belice. Tras la limpieza quedan **148.234 anuncios** (de 194.628 originales)
- **Cómo se validó con honestidad:** un mismo anfitrión puede tener muchos anuncios. Se partieron los datos **por anfitrión**, para que el modelo nunca se evalúe con anfitriones que ya vio. La prueba (29.721 anuncios de 13.345 anfitriones) se abrió **una sola vez**
- **Qué se comparó y qué se eligió:** una regla simple (mediana por ciudad y tipo de habitación), un modelo lineal, un bosque aleatorio y LightGBM. Se eligió **LightGBM optimizado**
- **Qué se descartó y por qué:** **Buenos Aires** (38,6 % de sus precios tenían una conversión a dólares sin explicación verificable) y **cinco ideas de variables nuevas** (las amenidades bajaron el error 0,91 USD, pero no superaron la regla que el grupo fijó antes de medir)

---

# 3 · Resultado y costo de negocio

| En 29.721 anuncios que el modelo nunca vio | Sin el modelo (regla simple) | Con el modelo |
|---|---|---|
| **Error promedio del precio por noche** | 57,44 USD | **41,40 USD** |
| **Anuncios con error mayor a la mitad de su precio** | 9.204 (31,0 %) | **5.549 (18,7 %)** |

- **Mejora:** el error baja **16,04 USD por noche (27,9 %)**; intervalo del 95 %: de 14,36 a 17,84 USD menos. **Las seis ciudades mejoran**
- **La meta se cumplió** (escrita antes de abrir la prueba): al menos 20 % de mejora, intervalo entero a favor del modelo y ninguna ciudad peor que la regla simple
- *Nota técnica: MAE 41,40 USD (frente a 57,44), MAPE 31,8 % (frente a 42,4 %), R² 0,67 (frente a 0,33). Cifras sobre anuncios con precio plausible (se excluyeron 86 extremos); fuente: `reports/07_validacion.md`.*

---

# 4 · Demo de la app

**Enlace:** **https://tarifalatam-unaula.streamlit.app** (abrirla unos minutos antes: si estuvo sin visitas, tarda en despertar)

1. **Un caso normal:** Bogotá, barrio Antonio Nariño, vivienda entera, 2 huéspedes → **41 USD por noche**, rango típico **32 a 48 USD**
2. **Un caso límite:** Belice, vivienda entera, 4 huéspedes → **279 USD** (rango 207 a 377) **con un aviso**: en Belice el modelo se equivoca 246 USD en promedio y no debe usarse sin revisión
3. **Un dato inválido:** 40 huéspedes → la app **no da precio** y dice que debe estar entre 1 y 16

> **Plan B:** captura con fecha (`reports/09_captura_app_2026-11-06.jpg`) y la app en local. Los casos se probaron en local (2026-11-05) y en el enlace público, sin sesión (2026-11-06).

---

# 5 · Riesgos y siguientes pasos

- **Qué NO hace el modelo:** no predice lo que se **cobrará**, sino el precio **publicado**. No dice si un inmueble **se paga** (no hay ocupación, costos ni valor de compra en los datos). El anfitrión decide; el modelo es una referencia
- **Límites de los datos:** una foto de **septiembre de 2026**, sin temporada, de **seis ciudades**. Falla en **Belice** (246 USD de error), en habitaciones de hotel y en compartidas (peor que la regla simple)
- **Uso responsable:** no usa datos del anfitrión. Sí usa la **ubicación**, así que el precio refleja las desigualdades de cada barrio: hay que revisar que no se use para discriminar zonas
- **Siguientes pasos:** (1) **mantener la app pública** (desplegada el 2026-11-06) y probar el enlace en ventana privada antes de cada exposición; (2) tratar Belice aparte o restringirlo; (3) en producción, **vigilar el error por ciudad** con precios nuevos
