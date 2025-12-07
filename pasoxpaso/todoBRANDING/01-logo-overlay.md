# Step 01: Logo Overlay

**Goal:** Integrar la funcionalidad de superposición de logo en `video_exporter.py`.

---

## 📋 Integration Strategy

El logo se agregará dinámicamente como un input adicional y se aplicará usando la opción `-filter_complex` en el comando de FFmpeg, lo que permite un encadenamiento robusto con otros filtros existentes como subtítulos o corrección de aspect ratio.

**Flujo de FFmpeg:**
```
Input Clip → [Filtros existentes] → [Nuevo Filtro Overlay] → Output
```
---

## ✅ Tasks

### Task 1.1: Añadir Parámetros de Logo a `export_clips()`

**File:** `/src/video_exporter.py`

**Action:** Modificar la firma del método `export_clips` para incluir los nuevos parámetros de branding.

- [x] Añadidos `add_logo`, `logo_path`, `logo_position`, y `logo_scale` a la firma de `export_clips`.
- [x] Actualizado el docstring correspondiente.

---

### Task 1.2: Pasar Parámetros a `_export_single_clip()`

**File:** `/src/video_exporter.py`

**Action:** Localizar la llamada a `_export_single_clip` dentro de `export_clips` y pasar los nuevos parámetros.

- [x] `_export_single_clip()` ahora recibe los parámetros de branding.

---

### Task 1.3: Actualizar Firma de `_export_single_clip()`

**File:** `/src/video_exporter.py`

**Action:** Modificar la firma del método `_export_single_clip` para aceptar los nuevos parámetros.

- [x] Firma de `_export_single_clip` actualizada.
- [x] Docstring de `_export_single_clip` actualizado.

---

### Task 1.4: Crear Método `_get_logo_overlay_filter()`

**File:** `/src/video_exporter.py`

**Action:** Añadir un nuevo método a la clase `VideoExporter` para generar el string del filtro de FFmpeg.

- [x] **Decisión de implementación:** En lugar de un método helper que devuelve un string de filtro estático, la lógica se ha integrado directamente en `_export_single_clip` para construir dinámicamente un grafo de `-filter_complex`. Esto permite un encadenamiento flexible con otros filtros (aspect ratio, subtítulos) y es más robusto. El método `_get_logo_overlay_filter` fue eliminado para evitar confusión.

---

### Task 1.5: Integrar el Filtro del Logo en el Comando FFmpeg

**File:** `/src/video_exporter.py` dentro de `_export_single_clip()`

**Action:** Modificar la construcción del comando de FFmpeg para incluir el logo como un input y añadir el filtro a la cadena de filtros.

- [x] Modificada la construcción del comando para añadir el logo como un input condicional.
- [x] Añadida la lógica para construir una cadena `-filter_complex` que maneja correctamente el overlay del logo en conjunto con los filtros de aspect ratio y subtítulos.
- [x] Verificada la lógica de manejo de inputs (`[0:v]`, `[1:v]`, etc.) y el mapeo de streams de audio y video.
- [x] Lógica de escalado del logo corregida para usar `scale2ref`, asegurando que el tamaño es relativo al video principal.

**Nota de Regresión (2025-11-30):** Durante la implementación, se descubrió que la combinación del filtro `overlay` (para el logo) y el filtro `subtitles` en una misma cadena de `-filter_complex` reintroducía un bug antiguo que duplicaba los subtítulos.

**Solución Arquitectónica:** Se refactorizó la lógica a un **proceso de dos pasos** cuando ambos, logo y subtítulos, están activados:
1.  **Primer Paso:** Se genera un video temporal que incluye todos los filtros **excepto** los subtítulos (ej. face tracking, aspect ratio, y el overlay del logo).
2.  **Segundo Paso:** Se toma el video temporal como input y se aplica únicamente el filtro de subtítulos usando la bandera `-vf`, que es el método estable.

Esto asegura la compatibilidad y previene el bug de duplicación, a costa de un paso de procesamiento adicional.

---

## 🎯 Validation Checklist

Antes de pasar al Step 02:

- [x] Los nuevos parámetros están correctamente añadidos y documentados en `video_exporter.py`.
- [x] Los parámetros se pasan en cascada desde `export_clips` hasta `_export_single_clip`.
- [x] La lógica de construcción del comando FFmpeg en `_export_single_clip` ha sido actualizada para manejar la adición del logo como un segundo input y aplicar el filtro `overlay` de forma robusta.
- [x] El código es sintácticamente correcto (`uv run python -m py_compile src/video_exporter.py`).

---

**Next Step:** `02-outro-concatenation.md` →