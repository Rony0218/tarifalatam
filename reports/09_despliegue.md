# Despliegue de la app

> Plantilla en blanco. Complétala durante la clase 5 (viernes 6 de noviembre), después de desplegar la app.
> Guía paso a paso: `material-del-curso/guias/streamlit-despliegue.md` y `material-del-curso/kit/guia-despliegue-y-presentacion.md`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | |
| Versión de Python elegida | ☐ 3.12  ☐ otra → motivo: _______________ |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☐ no |
| ¿Se desplegó? | ☐ sí  ☐ no → **plan B** (apartado 4) |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | |
| Versiones fijadas en `requirements.txt` | |
| Qué NO se subió al repo (y por qué) | |
| | |

## 3. Pruebas del enlace público

> **En local (2026-11-05, antes del despliegue):** los cuatro casos se probaron con `streamlit.testing` sobre
> `app/streamlit_app.py` y el modelo exportado. Mañana se repiten en el enlace público y se agrega la columna de ese resultado.

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | Bogotá, barrio Antonio Nariño, vivienda entera (*Entire rental unit*), 2 huéspedes; lo demás con sus valores por defecto | precio y rango en USD | local: 41 USD por noche, rango típico 32 a 48 USD, sin advertencias |
| Límite (cambia la decisión) | Belice, barrio Belize Islands, vivienda entera, 4 huéspedes (la ciudad donde el modelo falla más) | precio, rango y aviso de error alto | local: 279 USD, rango 207 a 377 USD y el aviso de Belice (246 USD de error medio en la prueba) |
| Inválido (debe rechazarse con un mensaje claro) | 40 huéspedes | no da precio y dice qué corregir | local: el campo de huéspedes solo admite de 1 a 16; con `predict_price` (notebook 09) responde «Huéspedes (accommodates): debe estar entre 1 y 16» |
| Con un campo en «No sé» | el caso normal con «No sé» en baños, camas y tipo de propiedad | precio sin error | local: 52 USD, rango 41 a 60 USD, sin errores |

## 4. Problemas encontrados y plan B

- Errores de despliegue que aparecieron y cómo se resolvieron (qué decía el registro y qué se cambió): _______________
- **Plan B** (si la app falla en vivo): captura con fecha y repo → `_______________`; app en local → `_______________`
- Si **no se desplegó**: **plan de despliegue escrito** (qué se intentó, qué error dio, qué harían): _______________

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
| **Total** | **10 min** | |

- ¿Se pasó de 10 minutos? ☐ no  ☐ sí → qué se recortó: _______________
- Retroalimentación recibida (lo mejor y la corrección que propusieron): _______________
- **Corrección concreta que hicimos por ella:** _______________
- Quién habla de qué y quién responde las preguntas técnicas: _______________
