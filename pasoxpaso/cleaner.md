# Feature: Cleanup Manager

**Fecha:** 2025-11-29

**Estado:** IMPLEMENTADO (testing pendiente)

**Propósito:** Gestionar eliminación de artifacts del proyecto sin limpieza manual

---

## Motivación

**PROBLEMA:**
```
Para re-testear features o liberar espacio, necesitábamos:
- rm -rf output/*
- rm -rf downloads/*
- rm temp/*.json
- Editar manualmente project_state.json

Proceso manual, propenso a errores, sin granularidad.
```

**SOLUCIÓN:**
```
Comando CLI interactivo para cleanup granular:
- Limpiar videos específicos
- Limpiar solo outputs (conservar transcripts caros)
- Fresh start total del proyecto
- Confirmación obligatoria + tamaños visibles
```

---

## Decisión Arquitectónica

### DECISIÓN: Módulo Independiente

**PROBLEMA:**
```
Necesitamos cleanup, pero:
- No debe romper flujo principal de CLIPER
- Debe ser invocable desde CLI
- Debe respetar state management actual
- Debe ser seguro (confirmación obligatoria)
```

**ALTERNATIVAS:**

**A) Módulo independiente (`src/cleanup_manager.py`):**
- Pros: Separación de responsabilidades, reutilizable, testeable
- Cons: Un archivo más en src/

**B) Integrar en StateManager (`src/utils/state_manager.py`):**
- Pros: State ya conoce qué archivos existen
- Cons: Mezcla gestión de estado con filesystem operations

**C) Comando inline en cliper.py:**
- Pros: Más rápido de implementar
- Cons: Código monolítico, difícil de testear

**TRADE-OFFS:**

```
Opción A (ELEGIDA):
+ Modular (patrón CLIPER)
+ Testeable aisladamente
+ Fácil extender (cleanup de copys específicos, etc.)
+ Coherente con StateManager
- +50 líneas de código (aceptable)

Opción B:
+ StateManager ya maneja project_state.json
+ Acceso directo a qué videos existen
- StateManager se vuelve "dios objeto"
- Rompe Single Responsibility Principle

Opción C:
+ Implementación rápida (30 min)
- cliper.py se vuelve más grande
- Difícil mantener long-term
```

**RESULTADO:** Opción A - Coherente con filosofía CLIPER (modularidad estricta)

---

## Arquitectura Implementada

### Módulo: CleanupManager

**Ubicación:** `src/cleanup_manager.py` (410 líneas)

**Responsabilidades:**
- Listar artifacts existentes (videos, transcripts, clips, outputs)
- Eliminar artifacts de forma segura
- Actualizar state después de eliminación
- Dry run mode para simular sin eliminar

**Estructura:**

```python
class CleanupManager:
    def __init__(
        downloads_dir: str = "downloads",
        temp_dir: str = "temp",
        output_dir: str = "output"
    )

    def get_video_artifacts(video_key: str) -> Dict[str, Dict]
        """
        Retorna todos los artifacts de un video con metadata:
        {
            'download': {'path': Path, 'exists': bool, 'size': int, 'type': str},
            'transcript': {...},
            'clips_metadata': {...},
            'output': {'clip_count': int, ...}
        }
        """

    def delete_video_artifacts(
        video_key: str,
        artifact_types: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict[str, bool]
        """
        Elimina artifacts específicos de un video.
        Actualiza state automáticamente.
        """

    def delete_all_project_data(dry_run: bool = False) -> Dict[str, bool]
        """
        Fresh start - elimina TODO el proyecto.
        NO pide confirmación (responsabilidad del caller).
        """

    def display_cleanable_artifacts(video_key: Optional[str] = None)
        """
        Rich table de artifacts con tamaños en MB.
        """

    def _update_state_after_cleanup(...)
        """
        Sincroniza state con filesystem después de eliminación.
        Privado - llamado automáticamente.
        """
```

**Integración con StateManager:**

```python
# Composición, no herencia
self.state_manager = StateManager()

# State se actualiza automáticamente después de cleanup
def _update_state_after_cleanup(video_key, deleted_types, results):
    # Marcar como no completado
    video_state['transcribed'] = False
    video_state['transcript_path'] = None

    # O eliminar completamente
    if all_deleted:
        del state[video_key]

    self.state_manager.save_state(state)
```

---

### CLI Integration

**Ubicación:** `cliper.py` (+268 líneas)

**Menú Principal:**

```
Con videos:
  1. Process a video
  2. Download new video
  3. Cleanup project data        [NUEVO]
  4. Full Pipeline (auto)
  5. Exit

Sin videos:
  1. Download new video
  2. Cleanup project data        [NUEVO]
  3. Exit
```

**Funciones Implementadas:**

```python
def opcion_cleanup_project()
    """Menú interactivo principal de cleanup"""

def cleanup_specific_video(cleanup_manager, state)
    """Cleanup granular de un video"""

def cleanup_outputs_only(cleanup_manager, state)
    """Elimina SOLO outputs (conserva transcripts)"""

def cleanup_entire_project(cleanup_manager)
    """Fresh start - elimina TODO"""
```

---

## User Flows

### Flow 1: Cleanup Video Específico

```
uv run python cliper.py
→ Opción 3: Cleanup project data

┌─────────────────────────────────────────┐
│ Cleanable Artifacts                     │
├──────────────┬──────────┬────────┬──────┤
│ Video        │ Download │ ...    │ Total│
├──────────────┼──────────┼────────┼──────┤
│ Video_ABC123 │ 757.0 MB │ ...    │ 1.0GB│
└──────────────┴──────────┴────────┴──────┘

→ Opción 1: Clean specific video
→ Seleccionar: 1 (Video_ABC123)

Artifacts:
  - download: 757.00 MB
  - transcript: 2.70 MB
  - output: 284.00 MB

→ Opción 2: Select specific artifacts
→ Delete download? n
→ Delete transcript? n
→ Delete output? y

This will DELETE 1 items (284.00 MB)
  - output

Continue? y

Cleaning...
✓ Deleted 1/1 items (284.00 MB freed)
```

---

### Flow 2: Cleanup Outputs Only

```
uv run python cliper.py
→ Opción 3: Cleanup
→ Opción 2: Clean all outputs only

This will delete ALL exported clips:
  - Videos: 3 videos
  - Clips: 28 clips
  - Size: 856.00 MB

Transcripts and source videos will be preserved

Continue? y

Cleaning outputs...
✓ Deleted outputs from 3 videos (856.00 MB freed)
```

---

### Flow 3: Fresh Start Total

```
uv run python cliper.py
→ Opción 3: Cleanup
→ Opción 3: Clean entire project

⚠️ WARNING: This will DELETE ALL project data:
  - All downloaded videos
  - All transcripts
  - All detected clips
  - All exported clips
  - Project state

Type 'DELETE ALL' to confirm: DELETE ALL

Cleaning entire project...
✓ Cleaned downloads/ (2.1 GB)
✓ Cleaned temp/ (5.6 MB)
✓ Cleaned output/ (856 MB)
✓ Reset project state

✓ Project cleaned successfully
Fresh start ready. Run CLIPER to begin.
```

---

## Decisiones Clave de Diseño

### 1. Confirmación Obligatoria

**DECISIÓN:** Siempre pedir confirmación, salvo flag `--yes` (futuro)

**RAZÓN:**
- Operación destructiva (no hay undo)
- Usuario puede perder horas de procesamiento
- Better safe than sorry

**IMPLEMENTACIÓN:**

```python
# Cleanup específico/outputs
if not Confirm.ask("Continue?", default=False):
    console.print("[yellow]Cleanup cancelled[/yellow]")
    return

# Cleanup total - confirmación EXTREMA
confirmation = Prompt.ask(
    "[bold]Type 'DELETE ALL' to confirm[/bold]",
    default="cancel"
)
if confirmation != "DELETE ALL":
    console.print("[yellow]Cleanup cancelled[/yellow]")
    return
```

**Trade-off:** Fricción intencional > conveniencia

---

### 2. Granularidad

**DECISIÓN:** Permitir cleanup granular por tipo de artifact

**RAZÓN:**
- Transcripts son caros de regenerar (WhisperX lento)
- Usuario puede querer solo liberar espacio de outputs
- Flexibilidad > simplicidad en operaciones destructivas

**IMPLEMENTACIÓN:**

```python
artifact_types = ['download', 'transcript', 'clips_metadata', 'output']

# Usuario puede elegir:
# - Todos
# - Individuales (Confirm.ask por cada uno)
# - Preset (solo outputs)
```

---

### 3. State Sincronizado

**DECISIÓN:** Actualizar `project_state.json` después de cleanup

**RAZÓN:**
- State debe reflejar realidad del filesystem
- Evitar referencias a archivos eliminados
- CLIPER puede detectar "transcribed: true pero archivo missing" y re-transcribir

**IMPLEMENTACIÓN:**

```python
# Si eliminamos transcript:
state[video_key]['transcribed'] = False
state[video_key]['transcript_path'] = None

# Si eliminamos TODO:
del state[video_key]
```

---

### 4. Dry Run Mode

**DECISIÓN:** Agregar flag `dry_run` para simular cleanup

**RAZÓN:**
- Usuario puede ver qué se eliminará sin riesgo
- Útil para debugging
- Patrón común en tools de cleanup (git clean --dry-run, docker system prune --dry-run)

**IMPLEMENTACIÓN:**

```python
def delete_video_artifacts(..., dry_run: bool = False):
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {artifact_type}: {path}")
        results[artifact_type] = True
        continue
    # ... eliminación real
```

**Estado:** Implementado, no expuesto en CLI (futuro: flag `--dry-run`)

---

### 5. UX: Tamaños Visibles

**DECISIÓN:** Mostrar tamaños en MB antes de confirmar

**RAZÓN:**
- Usuario toma decisión informada
- Evita sorpresas ("no sabía que eran 2GB")
- Feedback positivo después (MB freed)

**IMPLEMENTACIÓN:**

```python
# ANTES de confirmar
console.print(f"This will DELETE {len(items)} items ({total_mb:.2f} MB)")

# DESPUÉS de eliminar
console.print(f"Deleted {success_count}/{total} items ({total_mb:.2f} MB freed)")
```

---

### 6. Default "Cancel" en Opciones Destructivas

**DECISIÓN:** Default siempre en opción más segura

**RAZÓN:**
- Enter accidental no ejecuta acción destructiva
- Safety > convenience

**IMPLEMENTACIÓN:**

```python
choice = Prompt.ask(..., choices=["1", "2", "3", "4"], default="4")  # 4 = Back
video_idx = Prompt.ask(..., default=str(len(videos) + 1))  # Last = Cancel
granular_choice = Prompt.ask(..., default="3")  # 3 = Cancel
```

---

## Integración con CLIPER

### Módulos NO Modificados

**IMPORTANTE:** Cleanup es feature aislada

```
✓ downloader.py          - Sin cambios
✓ transcriber.py         - Sin cambios
✓ clips_generator.py     - Sin cambios
✓ video_exporter.py      - Sin cambios
✓ copys_generator.py     - Sin cambios
✓ state_manager.py       - Sin cambios (solo usado, no modificado)
```

**RAZÓN:** Modularidad estricta - nuevo feature no afecta core

---

### Archivos Creados/Modificados

**Nuevos:**
```
src/cleanup_manager.py                        410 líneas

pasoxpaso/
├── cleaner.md                                [NUEVO] Este archivo
└── todoCLEANUP/
    ├── 00-OVERVIEW.md                        Arquitectura
    ├── 01-cleanup-manager.md                 Implementación module
    ├── 02-cli-integration.md                 Integración CLI
    ├── 03-testing.md                         Testing plan
    └── README-STEPS.md                       Resumen steps
```

**Modificados:**
```
cliper.py                                     +268 líneas
  - Import CleanupManager                     línea 33
  - Menu actualizado                          líneas 187-198
  - Main loop actualizado                     líneas 1330-1352
  - 4 funciones cleanup_*()                   líneas 1291-1545
```

**Sin dependencias nuevas:**
- Usa Rich (ya existente)
- Usa loguru (ya existente)
- Usa StateManager (ya existente)

---

## Testing Manual (Pendiente)

### Checklist de Tests

**Test 1: Cleanup Video Específico**
- [ ] Listar videos disponibles
- [ ] Seleccionar video
- [ ] Mostrar artifacts con tamaños
- [ ] Seleccionar artifacts individuales
- [ ] Confirmación funciona
- [ ] Eliminación exitosa
- [ ] State actualizado
- [ ] Reescaneo de videos correcto

**Test 2: Cleanup Outputs Only**
- [ ] Calcular total outputs correcto
- [ ] Mostrar mensaje preservación transcripts
- [ ] Confirmación funciona
- [ ] Solo outputs eliminados
- [ ] Transcripts y downloads intactos
- [ ] State: exported_clips=[], transcribed=True

**Test 3: Cleanup Total**
- [ ] Warning explícito de qué se elimina
- [ ] Confirmación "DELETE ALL" funciona
- [ ] Confirmación con otro texto NO elimina
- [ ] Directorios eliminados y recreados vacíos
- [ ] State = {}
- [ ] Menu muestra "No videos found"

**Test 4: Edge Cases**
- [ ] State vacío: mensaje correcto, no crash
- [ ] Archivos missing: warning, no crash, state actualizado
- [ ] Permisos insuficientes: error claro, no crash
- [ ] Cancelación: nada eliminado en cada flujo

---

## Métricas de Éxito

**Feature considerado exitoso si:**

1. **Funcionalidad:**
   - [x] CleanupManager implementado
   - [x] CLI integrado
   - [ ] Tests manuales pasan (pendiente)

2. **Seguridad:**
   - [x] Confirmación implementada
   - [ ] Previene accidentes (testing pendiente)

3. **Robustez:**
   - [x] Error handling implementado
   - [ ] No crashea con edge cases (testing pendiente)

4. **UX:**
   - [x] Rich tables implementadas
   - [x] Tamaños visibles
   - [ ] Proceso < 10 seg (testing pendiente)

---

## Extensiones Futuras

**No implementadas (nice to have):**

1. **CLI Flags:**
   ```bash
   uv run python cliper.py --cleanup-all --yes
   uv run python cliper.py --cleanup-outputs --dry-run
   ```

2. **Cleanup por Estilo:**
   ```
   Clean only "viral" copys
   Clean only "educational" copys
   ```

3. **Cleanup por Antigüedad:**
   ```
   Clean videos older than 30 days
   Clean outputs not accessed in 7 days
   ```

4. **Estadísticas de Uso:**
   ```
   Dashboard: Total space used, breakdown by type
   Oldest videos, largest videos, etc.
   ```

5. **Auto-cleanup:**
   ```
   Auto-clean when disk space < 10GB
   Notification: "You have 2GB of old clips, clean?"
   ```

---

## Lecciones Aprendidas

### Arquitectura > Quick Fixes

**Aprendizaje:**
```
Módulo independiente tomó 1.5 horas.
Inline en cliper.py hubiera tomado 30 min.
Pero módulo independiente es:
- Testeable
- Extensible
- Mantenible
- Reutilizable
```

**Aplicación futura:**
- Siempre preferir modularidad
- 1 hora extra inicial = 10 horas ahorradas en mantenimiento

---

### Confirmación Multinivel

**Aprendizaje:**
```
Cleanup específico: Confirm.ask (simple)
Cleanup total: "Type DELETE ALL" (extremo)

Fricción proporcional a severidad = UX intuitivo
```

**Aplicación futura:**
- Operaciones destructivas deben tener fricción
- Default siempre en opción segura

---

### State Sincronizado es Crítico

**Aprendizaje:**
```
State desincronizado = bugs silenciosos:
- "transcribed: true" pero archivo missing
- Referencias a clips eliminados
- Proceso se salta steps porque cree que ya están hechos
```

**Aplicación futura:**
- State debe reflejar filesystem SIEMPRE
- Actualizar state inmediatamente después de operaciones

---

## Contexto de Implementación

**Relación con otras features:**

**PASO 3 (Face Tracking):**
- Cleanup facilita re-testing de face tracking
- Eliminar outputs permite re-exportar con diferentes settings
- Sin cleanup: testing manual tedioso

**PASO 2 (Copys Generator):**
- Future: cleanup de copys por estilo
- Future: re-generar solo copys de clips específicos

**StateManager:**
- Cleanup mantiene state sincronizado
- StateManager es source of truth
- CleanupManager es consumer + updater

---

**Estado:** IMPLEMENTADO, testing manual pendiente

**Prioridad:** MEDIA (útil para dev, no crítico para producción)

**Tiempo Invertido:** 1.5 horas (implementación + documentación)

**Próximo Paso:** Testing manual según `pasoxpaso/todoCLEANUP/03-testing.md`
