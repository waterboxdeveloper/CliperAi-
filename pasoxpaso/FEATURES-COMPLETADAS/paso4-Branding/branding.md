# Feature: Branding Automático (Logo + Outro)

**Fecha:** 2025-11-29

**Estado:** ANÁLISIS

**Propósito:** Agregar logo y outro automáticamente a todos los clips exportados

---

## Motivación

**PROBLEMA:**
```
Actualmente:
- Clips se exportan sin branding
- Logo se agrega manualmente en post-producción
- Outro se agrega manualmente en post-producción
- Tiempo perdido en edición repetitiva
- Inconsistencia visual entre clips
```

**SOLUCIÓN PROPUESTA:**
```
Branding automático en pipeline de exportación:
- Logo SVG en esquina superior derecha (siempre visible)
- Outro predefinido al final de cada clip (3-5 seg)
- Configurable (enable/disable por clip)
- Sin trabajo manual de post-producción
```

---

## Análisis de Factibilidad

### Feature 1: Logo Overlay

**Complejidad:** BAJA

**FFmpeg soporta:**
```bash
# Overlay de imagen sobre video
ffmpeg -i video.mp4 -i logo.png \
  -filter_complex "[0:v][1:v] overlay=W-w-10:10" \
  output.mp4

# Posición: esquina superior derecha
# W-w-10 = ancho_video - ancho_logo - 10px margin
# 10 = 10px desde arriba
```

**Formato logo:**
- SVG directo: NO soportado por FFmpeg (necesita conversión)
- PNG con transparencia: ✓ Soportado nativamente
- Solución: Convertir SVG → PNG al inicio (una vez)

**Trade-offs:**
```
+ Implementación simple (1 línea FFmpeg filter)
+ Sin dependencias nuevas
+ Performance mínimo (overlay es rápido)
- SVG necesita conversión previa a PNG
- Tamaño logo debe ser apropiado para resolución
```

---

### Feature 2: Outro Predefinido

**Complejidad:** MEDIA

**FFmpeg soporta:**
```bash
# Concatenar videos
ffmpeg -i clip.mp4 -i outro.mp4 \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=1" \
  output.mp4

# n=2: 2 videos a concatenar
# v=1: 1 stream de video
# a=1: 1 stream de audio
```

**Consideraciones:**
- Outro debe tener mismo aspect ratio que clip (9:16, 16:9, 1:1)
- Outro debe tener audio (o silencio)
- Transición suave (fade opcional)

**Trade-offs:**
```
+ Branding consistente
+ Profesional sin esfuerzo
+ Call-to-action al final (subscribe, follow, etc.)
- Aumenta duración de clips (outro 3-5 seg)
- Outro debe existir para cada aspect ratio
- Concatenación aumenta tiempo de procesamiento
```

---

## Decisión Arquitectónica

### DECISIÓN: Integrar en video_exporter.py

**PROBLEMA:**
```
Necesitamos branding automático sin:
- Crear módulo separado (overhead)
- Romper flujo existente de exportación
- Complicar pipeline
```

**ALTERNATIVAS:**

**A) Integrar en video_exporter.py (RECOMENDADA):**
```
Pros:
+ Coherente con arquitectura actual
+ video_exporter ya maneja FFmpeg
+ Configuración por clip (aspect_ratio, add_logo, add_outro)
+ Sin módulos nuevos

Cons:
- video_exporter.py crece ~100 líneas
- Más parámetros en export_clips()
```

**B) Módulo separado (src/branding_manager.py):**
```
Pros:
+ Separación de responsabilidades
+ Reutilizable para otros casos

Cons:
- Overhead arquitectónico
- video_exporter → branding_manager → video_exporter (circular)
- Más complejidad sin beneficio claro
```

**C) Post-procesamiento manual:**
```
Pros:
+ Sin cambios en código

Cons:
- Tiempo perdido (5-10 min por video)
- Inconsistencia
- No escala
```

**TRADE-OFFS:**

```
Opción A:
+ Implementación directa (2-3 horas)
+ Usa infraestructura FFmpeg existente
+ Configuración granular
- video_exporter.py más grande

Opción B:
+ Modular
- Complejidad innecesaria para feature simple
- Tiempo de implementación mayor

Opción C:
+ Sin código
- No resuelve problema
```

**RESULTADO:** Opción A - Integrar en video_exporter.py

**RAZÓN:**
- video_exporter ya orquesta FFmpeg
- Logo overlay = 1 filtro FFmpeg adicional
- Outro = concatenación FFmpeg
- Coherente con filosofía CLIPER (modularidad sin over-engineering)

---

## Arquitectura Propuesta

### Estructura de Archivos

```
assets/
├── logo.svg                    # Logo original (SVG)
├── logo.png                    # Logo convertido (PNG, transparente)
└── outros/
    ├── outro_9-16.mp4          # Outro para vertical (1080x1920)
    ├── outro_16-9.mp4          # Outro para horizontal (1920x1080)
    └── outro_1-1.mp4           # Outro para cuadrado (1080x1080)

src/video_exporter.py           # [MODIFICAR] +150 líneas
  - _prepare_branding_assets()  # [NUEVO] Convierte SVG → PNG
  - _get_logo_overlay_filter()  # [NUEVO] Genera filtro overlay
  - _concatenate_outro()         # [NUEVO] Concatena outro

cliper.py                       # [MODIFICAR] +30 líneas
  - Flags CLI: --add-logo, --add-outro
```

---

### Flujo de Exportación con Branding

**ANTES (actual):**
```
Clip → FFmpeg (cut + aspect ratio + subtitles) → output.mp4
```

**DESPUÉS (con branding):**
```
Clip → FFmpeg Pipeline:
  1. Cut temporal (start/end)
  2. Face tracking (si enabled)
  3. Aspect ratio conversion
  4. Subtitles burn-in
  5. Logo overlay (si enabled)      [NUEVO]
  6. Outro concatenation (si enabled) [NUEVO]
→ output.mp4
```

---

### Parámetros de Configuración

**video_exporter.export_clips():**

```python
def export_clips(
    self,
    video_path: str,
    clips: List[Dict],
    aspect_ratio: Optional[str] = None,
    add_subtitles: bool = False,
    # ... parámetros existentes ...

    # BRANDING (NUEVO)
    add_logo: bool = False,                    # Enable logo overlay
    logo_path: Optional[str] = None,           # Path a logo PNG
    logo_position: str = "top-right",          # Position del logo
    logo_scale: float = 0.1,                   # Tamaño relativo (10% del ancho)

    add_outro: bool = False,                   # Enable outro
    outro_path: Optional[str] = None,          # Path a outro video
    outro_transition: str = "none"             # Transition: "none", "fade"
) -> List[str]:
```

**Defaults sensatos:**
- `add_logo=False`: Opt-in (no rompe flujo existente)
- `logo_position="top-right"`: Estándar de branding
- `logo_scale=0.1`: 10% del ancho del video (visible pero no intrusivo)
- `add_outro=False`: Opt-in
- `outro_transition="none"`: Simple por defecto

---

### Logo Overlay - Implementación

**Conversión SVG → PNG (una vez al inicio):**

```python
def _prepare_branding_assets(self):
    """
    Convierte assets de branding a formatos compatibles con FFmpeg

    DECISIÓN: Conversión bajo demanda
    - SVG → PNG (si no existe PNG)
    - Tamaño: 1920px ancho (max resolution)
    - Transparencia preservada
    """
    logo_svg = Path("assets/logo.svg")
    logo_png = Path("assets/logo.png")

    if logo_svg.exists() and not logo_png.exists():
        # Opción 1: ImageMagick (si disponible)
        subprocess.run([
            "convert",
            "-background", "none",
            "-resize", "1920x",  # Max 1920px ancho
            str(logo_svg),
            str(logo_png)
        ])

        # Opción 2: cairosvg (Python library)
        # from cairosvg import svg2png
        # svg2png(url=str(logo_svg), write_to=str(logo_png), scale=2.0)

        logger.info(f"Logo converted: {logo_svg} → {logo_png}")

    return logo_png
```

**FFmpeg Filter para Overlay:**

```python
def _get_logo_overlay_filter(
    self,
    logo_path: str,
    position: str = "top-right",
    scale: float = 0.1
) -> str:
    """
    Genera filtro FFmpeg para overlay de logo

    Args:
        logo_path: Path al logo PNG
        position: "top-right", "top-left", "bottom-right", "bottom-left"
        scale: Tamaño relativo (0.1 = 10% del ancho del video)

    Returns:
        String de filtro FFmpeg
    """
    # Escapar path para FFmpeg
    logo_escaped = str(logo_path).replace('\\', '\\\\').replace(':', '\\:')

    # Posiciones
    positions = {
        "top-right": "W-w-20:20",        # 20px desde derecha, 20px desde arriba
        "top-left": "20:20",              # 20px desde izquierda, 20px desde arriba
        "bottom-right": "W-w-20:H-h-20", # 20px desde derecha, 20px desde abajo
        "bottom-left": "20:H-h-20"       # 20px desde izquierda, 20px desde abajo
    }

    pos = positions.get(position, positions["top-right"])

    # Filtro completo
    # movie: cargar logo
    # scale: ajustar tamaño (iw*scale = ancho_input * 0.1)
    # overlay: superponer en posición
    return f"movie={logo_escaped},scale=iw*{scale}:-1[logo];[in][logo]overlay={pos}[out]"
```

**Integración en _export_single_clip():**

```python
# Dentro de _export_single_clip()

# ... existing filters (aspect ratio, subtitles) ...

# Logo overlay
if add_logo and logo_path and Path(logo_path).exists():
    logo_filter = self._get_logo_overlay_filter(logo_path, logo_position, logo_scale)
    filters.append(logo_filter)
    logger.debug(f"Added logo overlay: {logo_path}")

# Apply filters
if filters:
    filter_string = ','.join(filters)
    cmd.extend(["-vf", filter_string])
```

---

### Outro Concatenation - Implementación

**Validar outro existe para aspect ratio:**

```python
def _get_outro_path_for_aspect_ratio(self, aspect_ratio: str) -> Optional[Path]:
    """
    Obtiene path al outro correspondiente al aspect ratio

    DECISIÓN: Outro específico por aspect ratio
    - 9:16 → outro_9-16.mp4 (1080x1920)
    - 16:9 → outro_16-9.mp4 (1920x1080)
    - 1:1 → outro_1-1.mp4 (1080x1080)
    """
    outros = {
        "9:16": Path("assets/outros/outro_9-16.mp4"),
        "16:9": Path("assets/outros/outro_16-9.mp4"),
        "1:1": Path("assets/outros/outro_1-1.mp4")
    }

    outro_path = outros.get(aspect_ratio)

    if outro_path and outro_path.exists():
        return outro_path
    else:
        logger.warning(f"Outro not found for aspect ratio {aspect_ratio}")
        return None
```

**Concatenar con FFmpeg:**

```python
def _concatenate_outro(
    self,
    clip_path: Path,
    outro_path: Path,
    output_path: Path,
    transition: str = "none"
) -> bool:
    """
    Concatena outro al final del clip

    Args:
        clip_path: Path al clip procesado
        outro_path: Path al outro video
        output_path: Path final del output
        transition: "none" o "fade"

    Returns:
        True si exitoso, False si falla
    """
    try:
        if transition == "fade":
            # Fade out en clip + fade in en outro
            filter_complex = (
                "[0:v]fade=t=out:st=END-1:d=1[v0];"
                "[1:v]fade=t=in:st=0:d=1[v1];"
                "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]"
            )
            # END se reemplaza con duración del clip
            # Esto requiere conocer duración del clip

        else:
            # Concatenación simple sin transición
            filter_complex = "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]"

        cmd = [
            "ffmpeg",
            "-i", str(clip_path),
            "-i", str(outro_path),
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-y",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            logger.error(f"Outro concatenation failed: {result.stderr}")
            return False

        logger.info(f"Outro concatenated: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error concatenating outro: {e}")
        return False
```

**Integración en _export_single_clip():**

```python
# Al FINAL de _export_single_clip(), después de generar clip base

if add_outro and aspect_ratio:
    outro_path = self._get_outro_path_for_aspect_ratio(aspect_ratio)

    if outro_path:
        # Generar clip temporal sin outro
        temp_clip_path = output_dir / f"{clip_id}_temp.mp4"

        # Mover output actual a temp
        output_path.rename(temp_clip_path)

        # Concatenar outro
        success = self._concatenate_outro(
            clip_path=temp_clip_path,
            outro_path=outro_path,
            output_path=output_path,
            transition=outro_transition
        )

        # Cleanup temp file
        if success and temp_clip_path.exists():
            temp_clip_path.unlink()
            logger.debug(f"Cleaned up temp clip: {temp_clip_path}")

        if not success:
            logger.warning(f"Failed to add outro to clip {clip_id}")
```

---

## Estimación de Complejidad

### Logo Overlay

**Tiempo estimado:** 1-2 horas

**Tareas:**
1. Crear `_prepare_branding_assets()` (conversión SVG → PNG)
2. Crear `_get_logo_overlay_filter()` (generar filtro FFmpeg)
3. Integrar en `_export_single_clip()` (agregar filtro)
4. Agregar parámetros a `export_clips()`
5. Testing con diferentes resoluciones

**Complejidad:** BAJA
- FFmpeg overlay es feature estándar
- Sin dependencias nuevas (ImageMagick ya común en sistemas)
- Configuración simple

---

### Outro Concatenation

**Tiempo estimado:** 2-3 horas

**Tareas:**
1. Crear `_get_outro_path_for_aspect_ratio()`
2. Crear `_concatenate_outro()` (FFmpeg concat)
3. Integrar en `_export_single_clip()` (post-procesamiento)
4. Agregar parámetros a `export_clips()`
5. Crear outros de ejemplo (9:16, 16:9, 1:1)
6. Testing con transiciones

**Complejidad:** MEDIA
- Concatenación FFmpeg es estándar
- Manejo de archivos temporales
- Verificación de aspect ratio matching
- Creación de outros (diseño, no código)

---

### Total

**Tiempo total:** 3-5 horas

**Breakdown:**
- Logo overlay: 1-2 horas
- Outro concatenation: 2-3 horas

**Factibilidad:** ALTA
- Ambas features son factibles con FFmpeg
- Sin dependencias complejas
- Integración limpia en video_exporter.py

---

## Configuración CLI

**Flags propuestos:**

```bash
# Habilitar logo
uv run python cliper.py --add-logo

# Habilitar outro
uv run python cliper.py --add-outro

# Ambos
uv run python cliper.py --add-logo --add-outro

# Custom logo path
uv run python cliper.py --add-logo --logo-path assets/custom_logo.png

# Custom outro
uv run python cliper.py --add-outro --outro-path assets/outros/custom_outro.mp4
```

**Configuración interactiva (menu):**

```
Export clips:
  - Aspect ratio: 9:16
  - Add subtitles: Yes
  - Face tracking: Yes
  - Add logo: [Yes/No]          [NUEVO]
  - Add outro: [Yes/No]         [NUEVO]
```

---

## Próximos Pasos

**Si apruebas esta arquitectura:**

1. Crear `pasoxpaso/todoBRANDING/` con steps detallados
2. Implementar logo overlay (Step 01)
3. Implementar outro concatenation (Step 02)
4. Integrar en CLI (Step 03)
5. Testing (Step 04)

**Pendiente de tu aprobación:**
- ¿Te parece correcta esta arquitectura?
- ¿Prefieres logo overlay solo, outro solo, o ambos?
- ¿Tienes ya los assets (logo SVG, outros videos)?
- ¿Quieres defaults (siempre enabled) o opt-in?

---

**Estado:** ANÁLISIS COMPLETO, esperando aprobación para implementar
