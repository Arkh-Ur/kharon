# Kharōn — Catastro de Mejoras de Diseño

> Auditoría visual completa de todas las páginas. Rama `dev`.

---

## 🔴 CRITICAL (Roto / Inusable)

| # | Problema | Página | Fix | Esfuerzo |
|---|---|---|---|---|
| 1 | Gantt chart X-axis muestra timestamps Unix crudos ("1.7773B") | Tablero | Formatear como `HH:MM:SS` con `xaxis.tickformat="%H:%M"` | <1h |
| 2 | Steps inactivos del indicador invisibles en fondo oscuro | Nuevo Script | Usar `#545B67` para inactivos, agregar línea conectora y estado completado (✓ verde) | 1-4h |
| 3 | Botón "Siguiente" apenas visible — contraste ~1.8:1 | Nuevo Script | Override CSS con color acento (`#3b82f6`), `font-weight:700`, borde visible | <1h |
| 4 | Dots de estado usan emoji 🟢🔴🟡⚪ — inconsistente cross-platform | Procesos | Reemplazar con círculos CSS `border-radius:50%;background:{color}` | 1-4h |

## 🟠 HIGH (Aspecto no profesional)

| # | Problema | Página | Fix | Esfuerzo |
|---|---|---|---|---|
| 5 | Sin sistema tipográfico — Streamlit default en todo | Todas | Importar display font (Outfit/Space Grotesk) + body font (DM Sans) + mono (JetBrains Mono) | 1-4h |
| 6 | Color primario es gris `#374151` — sin acento dominante | Todas | Elegir UN acento (azul `#3b82f6`) para CTAs, estados activos, links. Reservar verde/rojo/amarillo solo para status | 1-4h |
| 7 | Metric cards son rectángulos indiferenciados sin borde de acento | Tablero | Agregar `3px top border` color acento, ícono, reducir valor a `1.6em`, subir label a `0.9em` | 1-4h |
| 8 | Botón activo del sidebar sin diferenciación clara | Todas | Agregar `border-left:3px solid #3b82f6`, texto blanco, fondo `rgba(59,130,246,0.1)` | 1-4h |
| 9 | Progress indicator = 5 cajas desconectadas sin labels | Nuevo Script | Reemplazar con barra conectada: círculos + línea, ✓ verde completado, pulso azul actual, labels abajo | 1-2d |
| 10 | Procesos no tiene resumen scaneable — hay que abrir cada expander | Procesos | Agregar fila resumen: "🟢 5 OK · 🔴 2 Failed · 🟡 1 Running" arriba | 1-4h |
| 11 | Review step (paso 5) es texto plano sin card styling | Nuevo Script | Wrappear en card con fondo, divisores entre secciones, íconos por campo | 1-4h |
| 12 | Cero hover states ni micro-interacciones en toda la app | Todas | Agregar `:hover` a cards (lift/shadow), sidebar (glow), buttons (scale 1.02), con `transition: all 0.15s ease` | 1-4h |

## 🟡 MEDIUM (Pulido)

| # | Problema | Página | Fix | Esfuerzo |
|---|---|---|---|---|
| 13 | Donut chart sin labels en segmentos | Tablero | Agregar `textposition="inside"`, `textfont_size=14` al trace Pie | <1h |
| 14 | Chart de historial dentro de expanders muy chico (250px) | Procesos | Subir a `height=300`, limitar a 10 runs recientes | <1h |
| 15 | Títulos de página son emoji + texto genérico sin subtítulo | Todas | Agregar subtítulo contextual, usar header component custom en vez de `st.title()` | 1-4h |
| 16 | Background es color sólido plano sin profundidad | Todas | Agregar `radial-gradient` sutil + noise texture via SVG filter | 1-4h |
| 17 | `st.divider()` sobreuso — ruido visual | Tablero, Config | Reemplazar la mayoría con spacing, solo divider entre secciones distintas | <1h |
| 18 | Badges太小 (`0.78em`, `2px 10px`) y todos iguales | Procesos, Monitoreo | Subir a `0.82em`, `4px 14px`. Para failed agregar pulso o borde grueso | <1h |
| 19 | Filtro de cliente duplicado — sidebar Y contenido | Procesos | Eliminar uno de los dos | <1h |
| 20 | Config muestra JSON crudo en "Información del Registro" | Configuración | Usar `st.markdown` con key-value formateado o tabla | <1h |

## 🟢 LOW (Nice-to-have)

| # | Problema | Página | Fix | Esfuerzo |
|---|---|---|---|---|
| 21 | No hay ilustraciones para estados vacíos | Todas | Agregar SVG line-art con CTA para empty states | 1-2d |
| 22 | Logo Arkh-Ur en footer sin hover | Sidebar | Agregar `opacity:1` on hover con transición | <1h |
| 23 | `st.balloons()` al crear script es poco profesional | Nuevo Script | Reemplazar con `st.toast()` limpio o success card animada | <1h |
| 24 | Sin keyboard shortcuts ni command palette | Todas | Agregar floating action button para acciones rápidas | 1-2d |
| 25 | Sin skeleton loading states | Tablero, Monitoreo | Agregar placeholders pulsantes mientras carga data | 1-2d |

---

## Resumen por Prioridad

| Prioridad | Items | Esfuerzo Total |
|---|---|---|
| 🔴 CRITICAL | 4 | ~7h |
| 🟠 HIGH | 8 | ~18h |
| 🟡 MEDIUM | 8 | ~10h |
| 🟢 LOW | 5 | ~15h |
| **Total** | **25** | **~50h** |

## Recomendación de Implementación

**Fase 1 (1 día):** Items 1-4 CRITICAL — fix datos rotos + contraste

**Fase 2 (2 días):** Items 5, 6, 8, 12 — tipografía + acento + hover states. Transforma la percepción de calidad.

**Fase 3 (2 días):** Items 9, 10 — progress indicator conectado + resumen de procesos. Mayor impacto UX.

**Fase 4 (2 días):** Items 7, 11, 13-20 — pulido visual general.
