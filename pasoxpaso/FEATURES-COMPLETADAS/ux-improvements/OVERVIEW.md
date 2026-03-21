# UX Improvements - Overview

**Status:** 🚧 In Progress
**Date Started:** 2026-03-21

---

## 📋 What This Is

Mejoras generales a la experiencia del usuario en CLIPER CLI. Inicialmente:

- Flujos más claros
- Menos pasos innecesarios
- Información mejor presentada
- Acceso a archivos locales simplificado

---

## 🎯 Feature 1: Import Videos from ~/Downloads/

**Problem:**
- Solo se podían descargar videos de YouTube
- No hay forma de procesar archivos .mp4 locales

**Solution:**
- Detectar automáticamente .mp4 y .mov en `~/Downloads/`
- Mostrar lista numerada de videos disponibles
- Usuario selecciona por número
- CLIPER copia a proyecto y registra en state

**User Flow:**

```
Main Menu
└─ Add video
   ├─ [1] Download from YouTube
   └─ [2] Import from ~/Downloads/
      └─ Lists: video1.mp4, video2.mov, ...
         └─ User selects by number
```

**Implementation:**
- New class: `LocalVideoImporter` en `src/local_importer.py`
- Refactor: `opcion_descargar_video()` → `opcion_agregar_video()`
- Cross-platform: Auto-detects macOS/Linux/Windows Downloads folder

**Files Modified:**
- cliper.py (menu principal)
- src/local_importer.py (nuevo)

---

## 🔮 Planned: Feature 2, 3, ... (TBD)

Space for future UX improvements:
- Better error messages?
- Batch processing?
- Keyboard shortcuts?
- Progress indicators?

---

## 📍 References

- **UX Flow Map:** `pasoxpaso/CLIPER-UX-FLOW.md`
- **Code Entry Point:** `cliper.py` - `opcion_agregar_video()` (TBD)
- **Related:** Cleanup improvements already done (Option 1 & 2)

---

## ✅ Checklist - Feature 1: Import from ~/Downloads/

- [x] Implement LocalVideoImporter (`src/local_importer.py`)
- [x] Refactor `opcion_descargar_video()` → `opcion_agregar_video()`
- [x] Add submenu: YouTube vs Local
- [x] Implement `_agregar_video_local()` function
- [x] Auto-detect system Downloads folder (cross-platform)
- [x] List videos with file sizes
- [x] User selection by number
- [x] Copy to project + register in state
- [x] Error handling (file validation, permissions)
- [x] Spanish UI/UX
- [ ] Test: macOS, Linux, Windows (real testing)
- [ ] Documentation (user guide)
