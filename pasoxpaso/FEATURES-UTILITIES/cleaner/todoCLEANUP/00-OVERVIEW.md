# CLEANUP FEATURE - Overview

**Propósito:** Agregar comando CLI para limpiar artifacts (videos, transcripts, clips, copys) sin hacerlo manualmente

**Motivación:** Actualmente hay que eliminar archivos manualmente (`rm -rf output/*`, `rm temp/*.json`) para re-testear features o liberar espacio

---

## 🎯 Objetivo

Crear comando `cliper cleanup` que permita:

1. Limpiar videos descargados (`downloads/`)
2. Limpiar transcripciones (`temp/*_transcript.json`)
3. Limpiar clips detectados (`temp/*_clips.json`)
4. Limpiar copys generados (datos en `project_state.json`)
5. Limpiar videos exportados (`output/`)
6. Control granular: por video específico o todos
7. Confirmación antes de eliminar (safety)

---

## 📐 Arquitectura Propuesta

### DECISIÓN: Módulo independiente vs integrar en cliper.py

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
- Pros: Separación de responsabilidades, reutilizable
- Cons: Un archivo más en src/

**B) Integrar en StateManager (`src/utils/state_manager.py`):**
- Pros: State ya conoce qué archivos existen
- Cons: Mezcla gestión de estado con filesystem operations

**C) Comando inline en cliper.py:**
- Pros: Más rápido de implementar
- Cons: Código monolítico, difícil de testear

**TRADE-OFFS:**

```
Opción A (Recomendada):
+ Modular (patrón CLIPER)
+ Testeable aisladamente
+ Fácil extender (cleanup de copys específicos, etc.)
+ Coherente con StateManager
- +50 líneas de código

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

**RESULTADO:** Opción A - Crear `src/cleanup_manager.py` siguiendo filosofía modular de CLIPER

---

## 🗂️ Estructura de Archivos Afectados

```
src/
├── cleanup_manager.py       # [NUEVO] Lógica de cleanup
└── utils/
    └── state_manager.py      # [MODIFICAR] Agregar métodos helper

cliper.py                     # [MODIFICAR] Agregar comando 'cleanup'

pasoxpaso/todoCLEANUP/
├── 00-OVERVIEW.md            # Este archivo
├── 01-cleanup-manager.md     # Implementar CleanupManager
├── 02-cli-integration.md     # Integrar en cliper.py
└── 03-testing.md             # Testing de cleanup
```

---

## 🔄 User Flow

### Caso de Uso 1: Limpiar TODO de un video específico

```bash
$ uv run python cliper.py cleanup

Available videos:
  1. Storycraft in the Age of AI (LZlXASa8CZM)
  2. AI CDMX Live Stream (gjPVlCHU9OM)
  3. All videos

Select video to clean: 1

What to clean for "Storycraft in the Age of AI"?
  [x] Downloaded video (757 MB)
  [x] Transcript (2.7 MB)
  [x] Detected clips (86 KB)
  [x] Generated copys
  [x] Exported clips (284 MB)
  [ ] Keep project state

Total to free: 1,043 MB

⚠️  This will DELETE 5 items. Continue? (y/N): y

Cleaning...
✓ Deleted downloads/Storycraft_LZlXASa8CZM.mp4
✓ Deleted temp/Storycraft_LZlXASa8CZM_transcript.json
✓ Deleted temp/Storycraft_LZlXASa8CZM_clips.json
✓ Deleted output/Storycraft_LZlXASa8CZM/ (10 clips)
✓ Cleaned state entry

Freed 1,043 MB
```

### Caso de Uso 2: Limpiar SOLO outputs (conservar transcripts)

```bash
$ uv run python cliper.py cleanup --output-only

This will delete ALL exported clips from output/
Videos: 3 videos, 28 clips, 856 MB

Continue? (y/N): y

✓ Deleted output/ (856 MB freed)
```

### Caso de Uso 3: Limpiar TODO el proyecto (fresh start)

```bash
$ uv run python cliper.py cleanup --all

⚠️  WARNING: This will DELETE ALL project data:
  - 3 downloaded videos (2.1 GB)
  - 3 transcripts (5.4 MB)
  - 3 clip sets (195 KB)
  - 28 exported clips (856 MB)
  - Project state

Total: 2,961 MB

Type "DELETE ALL" to confirm: DELETE ALL

Cleaning entire project...
✓ Deleted downloads/ (2.1 GB)
✓ Deleted temp/ (5.6 MB)
✓ Deleted output/ (856 MB)
✓ Reset project state

Fresh start ready. Run 'cliper.py' to begin.
```

---

## 📋 Pasos de Implementación

### ✅ Step 01: CleanupManager Module
**File:** `01-cleanup-manager.md`

Crear `src/cleanup_manager.py` con:
- Clase `CleanupManager`
- Métodos: `list_cleanable_items()`, `delete_video_artifacts()`, `delete_all()`
- Integración con StateManager

### ✅ Step 02: CLI Integration
**File:** `02-cli-integration.md`

Modificar `cliper.py`:
- Agregar opción "Cleanup project data" al menú principal
- Implementar flujo interactivo (selección de videos, confirmación)
- Flags: `--output-only`, `--all`, `--yes` (skip confirmación)

### ✅ Step 03: Testing
**File:** `03-testing.md`

Testing completo:
- Test cleanup de video específico
- Test cleanup parcial (solo outputs)
- Test cleanup total
- Test confirmación (no eliminar sin confirmar)
- Test cleanup con state corrupto

---

## 🚀 Decisiones Clave

### 1. Confirmación Obligatoria

**DECISIÓN:** Siempre pedir confirmación, salvo `--yes` flag

**RAZÓN:**
- Operación destructiva (no hay undo)
- Usuario puede perder horas de procesamiento
- Better safe than sorry

**EXCEPCIÓN:** CI/CD puede usar `--yes` para cleanup automático

### 2. Granularidad

**DECISIÓN:** Permitir cleanup granular (por tipo de artifact)

**RAZÓN:**
- Usuario puede querer conservar transcripts (caros de regenerar)
- Usuario puede querer solo liberar espacio de outputs
- Flexibilidad > simplicidad en este caso

### 3. State Management

**DECISIÓN:** Actualizar `project_state.json` después de cleanup

**RAZÓN:**
- State debe reflejar realidad del filesystem
- Evitar referencias a archivos eliminados
- CLIPER puede detectar "transcribed: true pero archivo missing" y re-transcribir

**IMPLEMENTACIÓN:**
```python
# Si eliminamos transcript de video X:
state[video_key]['transcribed'] = False
state[video_key]['transcript_path'] = None

# Si eliminamos TODO de video X:
del state[video_key]
```

### 4. Safety: Dry Run Mode

**DECISIÓN:** Agregar `--dry-run` flag para simular cleanup

**RAZÓN:**
- Usuario puede ver qué se eliminará sin riesgo
- Útil para debugging
- Patrón común en tools de cleanup (git clean --dry-run, docker system prune --dry-run)

**EJEMPLO:**
```bash
$ uv run python cliper.py cleanup --all --dry-run

[DRY RUN] Would delete:
  - downloads/video1.mp4 (757 MB)
  - temp/video1_transcript.json (2.7 MB)
  - output/video1/ (284 MB)

Total: 1,043 MB

No files were deleted (dry run mode)
```

---

## 📊 Métricas de Éxito

Feature considerado exitoso si:

1. Usuario puede limpiar videos específicos sin tocar otros
2. Usuario puede limpiar solo outputs (conservar transcripts)
3. Usuario puede hacer fresh start total en 10 segundos
4. Confirmación previene eliminaciones accidentales
5. State se actualiza correctamente post-cleanup
6. No deja archivos huérfanos

---

## 🔗 Integración con Features Existentes

### StateManager (src/utils/state_manager.py)

**Agregar métodos:**
```python
def get_video_artifacts(self, video_key: str) -> Dict[str, Path]:
    """Retorna paths de todos los artifacts de un video"""

def remove_video_from_state(self, video_key: str):
    """Elimina video del state"""

def mark_video_stage_incomplete(self, video_key: str, stage: str):
    """Marca stage como no completado (ej: transcribed=False)"""
```

### CLIPER Main Menu (cliper.py)

**Agregar opción:**
```python
menu_options = {
    "1": "Process new video",
    "2": "Export clips from existing",
    "3": "Cleanup project data",  # [NUEVO]
    "4": "Exit"
}
```

---

## ⏱️ Estimación de Tiempo

| Paso | Descripción | Tiempo Estimado |
|------|-------------|-----------------|
| 01   | CleanupManager module | 1-2 horas |
| 02   | CLI integration | 1 hora |
| 03   | Testing | 30 min |
| **Total** | | **2.5-3.5 horas** |

---

## 📝 Notas de Implementación

### Paths a Limpiar

```python
# Para un video con key "video_name_ID":
ARTIFACTS = {
    'download': f'downloads/{filename}.mp4',
    'transcript': f'temp/{video_key}_transcript.json',
    'clips': f'temp/{video_key}_clips.json',
    'copys': 'Stored in project_state.json (no file to delete)',
    'output': f'output/{video_key}/'  # Directorio completo
}
```

### Edge Cases

1. **Archivo ya eliminado manualmente:**
   - No crashear, solo logear warning
   - Actualizar state correctamente

2. **State corrupto (referencia a archivo inexistente):**
   - Detectar y ofrecer "cleanup state"
   - Sincronizar state con filesystem real

3. **Proceso interrumpido (Ctrl+C durante cleanup):**
   - Cleanup es transaccional? O best-effort?
   - **DECISIÓN:** Best-effort (eliminar lo que se pueda, actualizar state al final)

4. **Permisos insuficientes:**
   - Capturar PermissionError
   - Mostrar error claro: "Cannot delete X (permission denied)"

---

**Estado:** TODO - Feature no implementado

**Prioridad:** MEDIA - Útil para development, no crítico para producción

**Dependencias:** Ninguna - puede implementarse independientemente de PASO3

---

**Next Steps:**
1. Leer `01-cleanup-manager.md`
2. Implementar `CleanupManager`
3. Integrar en CLI
4. Testing
