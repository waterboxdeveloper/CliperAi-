# Cleanup Feature - Implementation Steps

**Feature:** Agregar comando CLI para limpiar artifacts del proyecto (videos, transcripts, clips, copys)

**Motivación:** Evitar limpieza manual (`rm -rf`) para re-testing o liberar espacio

---

## 📋 Quick Overview

| Step | Descripción | Tiempo Estimado | Status |
|------|-------------|-----------------|--------|
| 00 | Overview & Architectural Decisions | 15 min (lectura) | ✅ Completo |
| 01 | Implementar CleanupManager module | 1-2 horas | ⏳ Pendiente |
| 02 | Integrar en cliper.py (CLI) | 1 hora | ⏳ Pendiente |
| 03 | Testing (unit + manual) | 30-60 min | ⏳ Pendiente |

**Total:** 2.5-3.5 horas

---

## 🎯 Steps Breakdown

### Step 00: Overview
**File:** `00-OVERVIEW.md`

**Qué hace:**
- Define objetivo y motivación
- Analiza alternativas arquitectónicas (módulo independiente vs integrado)
- Especifica user flows (cleanup específico, outputs-only, total)
- Documenta decisiones clave (confirmación, granularidad, state management, dry run)

**Key Decisions:**
- Opción A: Módulo independiente `src/cleanup_manager.py` (modular, testeable)
- Confirmación obligatoria (operación destructiva)
- Granularidad: permitir cleanup por tipo de artifact
- Dry run mode para simular sin eliminar

---

### Step 01: CleanupManager Module
**File:** `01-cleanup-manager.md`

**Qué implementa:**
- Clase `CleanupManager` en `src/cleanup_manager.py`
- Método `get_video_artifacts()` - lista artifacts con tamaños
- Método `delete_video_artifacts()` - elimina artifacts seleccionados
- Método `delete_all_project_data()` - fresh start total
- Método `display_cleanable_artifacts()` - Rich table de artifacts
- Integración con StateManager para actualizar state

**Tasks:**
1. Crear estructura básica del CleanupManager
2. Implementar listado de artifacts
3. Implementar eliminación con actualización de state
4. Implementar cleanup total
5. Implementar display con Rich

**Validation:**
- CleanupManager se instancia sin errores
- get_video_artifacts() retorna estructura correcta
- delete_video_artifacts() elimina y actualiza state
- Dry run NO elimina archivos
- Manejo de errores (permisos, missing files)

---

### Step 02: CLI Integration
**File:** `02-cli-integration.md`

**Qué implementa:**
- Agregar opción 3: "Cleanup project data" al menú principal
- Función `cleanup_project_data()` - flujo interactivo
- Función `cleanup_specific_video()` - cleanup granular de un video
- Función `cleanup_outputs_only()` - solo outputs
- Función `cleanup_entire_project()` - fresh start con confirmación
- Flags CLI: `--cleanup-all`, `--cleanup-outputs`, `--yes`, `--dry-run`

**Tasks:**
1. Modificar menú principal en cliper.py
2. Implementar funciones interactivas de cleanup
3. Agregar argparse support para flags CLI

**Validation:**
- Menú muestra opción "Cleanup project data"
- Flujo interactivo permite selección granular
- Cleanup total requiere "DELETE ALL" para confirmar
- Flags CLI funcionan correctamente

---

### Step 03: Testing
**File:** `03-testing.md`

**Qué testea:**
- Test unitario: get_video_artifacts() lista correctamente
- Test unitario: delete_video_artifacts() elimina y actualiza state
- Test unitario: dry_run NO elimina archivos
- Test edge case: archivo ya eliminado (no crashear)
- Test edge case: permisos insuficientes (graceful handling)
- Test integración: delete_all_project_data() limpia todo
- Test manual: CLI interactivo
- Test manual: flags CLI

**Tasks:**
1. Crear `tests/test_cleanup_manager.py`
2. Implementar fixtures de testing (tmp_path con proyecto simulado)
3. Implementar tests unitarios
4. Implementar tests de edge cases
5. Realizar testing manual completo

**Coverage Target:** 80%+ en `src/cleanup_manager.py`

---

## 🗂️ Archivos Creados/Modificados

### Nuevos Archivos
```
src/
└── cleanup_manager.py          # [NUEVO] ~200 líneas

tests/
└── test_cleanup_manager.py     # [NUEVO] ~150 líneas

pasoxpaso/todoCLEANUP/
├── 00-OVERVIEW.md              # [NUEVO] Arquitectura
├── 01-cleanup-manager.md       # [NUEVO] Implementación
├── 02-cli-integration.md       # [NUEVO] CLI
├── 03-testing.md               # [NUEVO] Testing
└── README-STEPS.md             # [NUEVO] Este archivo
```

### Archivos Modificados
```
cliper.py                       # [MODIFICAR] +150 líneas
                                # - Agregar opción 3 al menú
                                # - Agregar funciones cleanup_*()
                                # - Agregar argparse support

src/utils/state_manager.py     # [OPCIONAL] +30 líneas
                                # - Helper methods si necesario
```

---

## 🚀 Implementation Order

**Orden recomendado:**

1. **Leer** `00-OVERVIEW.md` - Entender arquitectura y decisiones
2. **Implementar** `01-cleanup-manager.md` - Crear módulo core
3. **Implementar** `02-cli-integration.md` - Exponer al usuario
4. **Testing** `03-testing.md` - Validar funcionalidad

**Checkpoint después de cada step:**
- Step 01 done → CleanupManager testeable con Python import
- Step 02 done → CLI funciona interactivamente
- Step 03 done → Tests pasan, feature lista para producción

---

## 🎯 Success Criteria

Feature considerado exitoso si:

1. **Funcionalidad:**
   - ✅ Usuario puede limpiar videos específicos
   - ✅ Usuario puede limpiar solo outputs (conservar transcripts)
   - ✅ Usuario puede hacer fresh start total
   - ✅ State se actualiza correctamente post-cleanup

2. **Seguridad:**
   - ✅ Confirmación previene eliminaciones accidentales
   - ✅ Dry run permite simular sin riesgo
   - ✅ Mensajes claros de qué se eliminará

3. **Robustez:**
   - ✅ No crashea con archivos missing
   - ✅ Maneja permisos insuficientes gracefully
   - ✅ State corrupto no rompe feature

4. **UX:**
   - ✅ Rich tables muestran artifacts claramente
   - ✅ Tamaños en MB para decisiones informadas
   - ✅ Proceso rápido (< 10 seg para fresh start)

---

## 📊 Integration with CLIPER

**Integración con features existentes:**

- **StateManager:** CleanupManager lee y actualiza `project_state.json`
- **CLI (cliper.py):** Nueva opción en menú principal
- **Logging:** Usa loguru para reportar operaciones
- **Rich:** Display de artifacts con tablas

**NO afecta:**
- Downloader, Transcriber, ClipsGenerator, VideoExporter (no se modifican)
- Docker, pyproject.toml (no hay dependencias nuevas)

---

## 🔗 Related Documentation

- `/pasoxpaso/contextofull.md` - Arquitectura global de CLIPER
- `/.claude/claude.md` - Filosofía de desarrollo del proyecto
- `/src/utils/state_manager.py` - Manejo de state actual

---

## 📝 Notes

**Prioridad:** MEDIA
- Útil para development (re-testing features)
- No crítico para producción
- Quick win (2-3 horas implementación)

**Future Enhancements:**
- Cleanup de copys específicos (por estilo)
- Cleanup por antigüedad (videos >30 días)
- Estadísticas de uso de espacio (dashboard)
- Auto-cleanup al alcanzar límite de disco

---

**Status:** TODO - Listo para implementación

**Next:** Implementar Step 01 (CleanupManager module)
