# Paso 4: Branding Automático (Logo + Outro)

**Feature:** Agregar logo y outro automáticamente a los clips exportados.
**Goal:** Aumentar el branding y la consistencia visual sin trabajo manual.

---

## 📚 Implementation Steps

Este directorio contiene las instrucciones detalladas para cada fase de la implementación.

1.  **`01-logo-overlay.md`** - Implementar la superposición del logo.
2.  **`02-outro-concatenation.md`** - Implementar la concatenación del video de outro.
3.  **`03-cli-integration.md`** - Agregar las opciones de control en la interfaz de línea de comandos (`cliper.py`).
4.  **`04-testing.md`** - Probar la funcionalidad de branding de forma integral.

---

## 🎯 Key Design Decisions

Basado en el análisis de `pasoxpaso/branding.md`:

✅ **Integración en `video_exporter.py`:** La lógica residirá en el módulo que ya orquesta FFmpeg.
✅ **FFmpeg Nativo:** Se usarán los filtros `overlay` para el logo y `concat` para el outro, sin nuevas dependencias pesadas.
✅ **Opt-In por Defecto:** Las funciones de branding estarán desactivadas por defecto (`add_logo=False`, `add_outro=False`) para no alterar el comportamiento existente.
✅ **Assets Configurables:** Las rutas al logo y a los outros serán parámetros, con una estructura de directorios `assets/` por defecto.
✅ **Manejo de Aspect Ratio:** El sistema seleccionará el video de outro correcto (`outro_9-16.mp4`, `outro_1-1.mp4`, etc.) según el aspect ratio del clip.

---

## 🚦 Getting Started

**Leer en orden:**
1.  Empezar con este overview.
2.  Seguir los pasos `01` → `04` secuencialmente.
3.  Cada archivo contiene instrucciones detalladas y ejemplos de código.
4.  Marcar las casillas de verificación a medida que se completan las tareas.

**Prerrequisitos:**
- Proyecto CLIPER funcional.
- Assets de branding (logo en PNG, videos de outro) disponibles en una carpeta `assets/`.

---

## 📖 Reference Documents

- `../branding.md` - Especificación original y análisis de factibilidad.
- `../contextofull.md` - Arquitectura y filosofía del proyecto.
- `../todoPASO3/` - Ejemplo de una implementación de feature compleja anterior.

---

**Ready?** Start with `01-logo-overlay.md` →
