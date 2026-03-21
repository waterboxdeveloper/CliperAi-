# Step 02: Outro Concatenation

**Goal:** Añadir un video de "outro" al final de cada clip exportado.

---

## 📋 Integration Strategy

La concatenación del outro se realizará como un paso de post-procesamiento después de que el clip principal (con logo y subtítulos) haya sido generado.

**Flujo de trabajo:**
1.  Generar el clip de video principal (con todos los filtros, incluyendo el logo del Step 01) y guardarlo en un archivo temporal (ej. `clip_01_temp.mp4`).
2.  Usar FFmpeg para concatenar el video temporal con el video de outro correspondiente.
3.  Guardar el resultado como el archivo de salida final (ej. `clip_01.mp4`).
4.  Eliminar el archivo de video temporal.

Este enfoque de dos pasos es más robusto que intentar hacerlo todo en una sola cadena de filtros complejos, especialmente cuando se combinan filtros de overlay, subtítulos y concatenación.

---

## ✅ Tasks

### Task 2.1: Añadir Parámetros de Outro a `export_clips()`

**File:** `/src/video_exporter.py`

**Action:** Añadir los parámetros del outro a la firma del método `export_clips`.

```python
def export_clips(
    self,
    # ... existing parameters, including logo ...
    logo_path: Optional[str] = "assets/logo.png",
    logo_position: str = "top-right",
    logo_scale: float = 0.1,
    # OUTRO (NUEVO)
    add_outro: bool = False,
    outros_path: Optional[str] = "assets/outros"
) -> List[str]:
```
- [ ] Añadidos `add_outro` y `outros_path` a la firma de `export_clips`.
- [ ] Actualizado el docstring correspondiente.

---

### Task 2.2: Pasar Parámetros a `_export_single_clip()`

**File:** `/src/video_exporter.py`

**Action:** Localizar la llamada a `_export_single_clip` y pasar los nuevos parámetros.

```python
clip_path = self._export_single_clip(
    # ... existing parameters, including logo ...
    logo_position=logo_position,
    logo_scale=logo_scale,
    # OUTRO (NUEVO)
    add_outro=add_outro,
    outros_path=outros_path
)
```
- [ ] `_export_single_clip()` ahora recibe los parámetros del outro.

---

### Task 2.3: Actualizar Firma de `_export_single_clip()`

**File:** `/src/video_exporter.py`

**Action:** Modificar la firma de `_export_single_clip` para aceptar los nuevos parámetros.

```python
def _export_single_clip(
    self,
    # ... existing parameters, including logo ...
    logo_position: str = "top-right",
    logo_scale: float = 0.1,
    # OUTRO (NUEVO)
    add_outro: bool = False,
    outros_path: Optional[str] = "assets/outros"
) -> Optional[Path]:
```
- [ ] Firma de `_export_single_clip` actualizada.

---

### Task 2.4: Crear Métodos `_get_outro_path()` y `_concatenate_outro()`

**File:** `/src/video_exporter.py`

**Action:** Añadir dos nuevos métodos a la clase `VideoExporter`.

**1. `_get_outro_path()`**
Este método encontrará el video de outro correcto basado en el aspect ratio.

```python
def _get_outro_path(self, outros_path: str, aspect_ratio: str) -> Optional[Path]:
    """
    Encuentra el video de outro correspondiente para un aspect ratio dado.
    Busca archivos como 'outro_9-16.mp4', 'outro_1-1.mp4', etc.

    Args:
        outros_path: Directorio donde se almacenan los videos de outro.
        aspect_ratio: El aspect ratio del clip (ej. "9:16").

    Returns:
        La ruta al video de outro si se encuentra, de lo contrario None.
    """
    outro_dir = Path(outros_path)
    if not outro_dir.is_dir():
        logger.warning(f"El directorio de outros no existe: {outros_path}")
        return None

    # Normalizar aspect ratio para nombre de archivo (ej. "9:16" -> "9-16")
    aspect_ratio_str = aspect_ratio.replace(":", "-")
    
    # Buscar el archivo (ej. `outro_9-16.mp4`)
    # Se buscan varios formatos por si acaso (.mp4, .mov, etc.)
    for ext in ["mp4", "mov", "avi"]:
        outro_file = outro_dir / f"outro_{aspect_ratio_str}.{ext}"
        if outro_file.exists():
            logger.info(f"Encontrado outro para aspect ratio {aspect_ratio}: {outro_file}")
            return outro_file
            
    logger.warning(f"No se encontró un video de outro para el aspect ratio '{aspect_ratio}' en {outros_path}")
    return None
```

**2. `_concatenate_outro()`**
Este método ejecutará el comando `ffmpeg` para unir los dos videos.

```python
def _concatenate_videos(self, video1_path: Path, video2_path: Path, output_path: Path) -> bool:
    """
    Concatena dos videos usando FFmpeg.

    Args:
        video1_path: Ruta al primer video.
        video2_path: Ruta al segundo video (outro).
        output_path: Ruta para guardar el video final.

    Returns:
        True si la concatenación fue exitosa, False en caso contrario.
    """
    try:
        # Comando para concatenar. Usa el filtro `concat` con 2 inputs de video (n=2),
        # 1 stream de video (v=1) y 1 stream de audio (a=1).
        cmd = [
            "ffmpeg",
            "-i", str(video1_path),
            "-i", str(video2_path),
            "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-y",
            str(output_path)
        ]
        
        logger.info(f"Concatenando outro: {video2_path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            logger.error(f"Error al concatenar videos. FFmpeg stderr:\n{result.stderr}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Una excepción ocurrió durante la concatenación de videos: {e}")
        return False
```

- [ ] Creado el método `_get_outro_path`.
- [ ] Creado el método `_concatenate_videos`.

---

### Task 2.5: Integrar Lógica de Outro en `_export_single_clip()`

**File:** `/src/video_exporter.py`

**Action:** Modificar el final de `_export_single_clip` para manejar la concatenación.

```python
# ... al final de _export_single_clip, después de la ejecución del primer comando ffmpeg ...

# Guardar la ruta final original
final_output_path = output_path 

# Si se debe añadir un outro, el output anterior es ahora un archivo temporal.
temp_clip_path = None
if add_outro and aspect_ratio_original: # Usar aspect_ratio_original
    temp_clip_path = output_dir / f"{video_name}_{clip_id}_temp.mp4"
    output_path.rename(temp_clip_path) # Renombrar el clip recién creado a un nombre temporal
    
    # Obtener la ruta del outro
    outro_video_path = self._get_outro_path(outros_path, aspect_ratio_original)
    
    if outro_video_path:
        # Concatenar el clip temporal con el outro
        success = self._concatenate_videos(
            video1_path=temp_clip_path,
            video2_path=outro_video_path,
            output_path=final_output_path  # El output final es la ruta original
        )
        if not success:
            logger.error(f"No se pudo añadir el outro a {clip_id}. El clip se guardará sin outro.")
            # Si falla, restaurar el video temporal como el final
            temp_clip_path.rename(final_output_path)
    else:
        # Si no se encuentra un outro, restaurar el video temporal
        temp_clip_path.rename(final_output_path)
        logger.warning(f"No se encontró video de outro para el clip {clip_id}. No se añadirá outro.")


# Limpieza final del archivo temporal
if temp_clip_path and temp_clip_path.exists():
    temp_clip_path.unlink()

# Devolver la ruta final
return final_output_path
```
**Nota:** Es importante usar la variable `aspect_ratio_original` que se guardó antes de la lógica de face tracking, ya que `aspect_ratio` puede ser `None` en ese punto.

- [ ] Modificada la sección final de `_export_single_clip`.
- [ ] Se genera un archivo temporal para el clip principal.
- [ ] Se llama a `_concatenate_videos` para unir el clip y el outro.
- [ ] Se maneja el caso en que no se encuentre un video de outro.
- [ ] El archivo temporal se elimina después de la operación.

---

## 🎯 Validation Checklist

- [ ] Los parámetros de outro están añadidos a las funciones y se pasan correctamente.
- [ ] Los métodos `_get_outro_path` y `_concatenate_videos` están implementados.
- [ ] La lógica de post-procesamiento para el outro está integrada en `_export_single_clip`.
- [ ] El manejo de archivos temporales (creación, renombrado, eliminación) es correcto y robusto.
- [ ] El código es sintácticamente correcto.

---

**Next Step:** `03-cli-integration.md` →

