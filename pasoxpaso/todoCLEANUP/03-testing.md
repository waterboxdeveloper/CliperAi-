# Step 03: Testing Cleanup Feature

**Goal:** Validar que CleanupManager funciona correctamente en todos los casos

---

## 📋 Test Strategy

### Tests a Implementar

1. **Test unitarios:** CleanupManager métodos individuales
2. **Test de integración:** Flujo completo con state
3. **Test de edge cases:** Archivos missing, permisos, state corrupto
4. **Test manual:** CLI interactivo

---

## ✅ Test Cases

### Test 3.1: Test Unitario - get_video_artifacts()

**Objetivo:** Verificar que listado de artifacts es correcto

**Setup:**
```python
# tests/test_cleanup_manager.py
import pytest
from pathlib import Path
from src.cleanup_manager import CleanupManager
from src.utils.state_manager import StateManager


@pytest.fixture
def setup_test_project(tmp_path):
    """Crea estructura de proyecto temporal para testing"""
    downloads_dir = tmp_path / "downloads"
    temp_dir = tmp_path / "temp"
    output_dir = tmp_path / "output"

    downloads_dir.mkdir()
    temp_dir.mkdir()
    output_dir.mkdir()

    # Crear archivos de prueba
    video_file = downloads_dir / "test_video_ABC123.mp4"
    video_file.write_bytes(b"fake video data" * 1000)  # ~15 KB

    transcript_file = temp_dir / "test_video_ABC123_transcript.json"
    transcript_file.write_text('{"test": "data"}')

    output_video_dir = output_dir / "test_video_ABC123"
    output_video_dir.mkdir()
    (output_video_dir / "1.mp4").write_bytes(b"clip data" * 500)

    # Crear state
    state = {
        "test_video_ABC123": {
            "filename": "test_video_ABC123.mp4",
            "downloaded": True,
            "transcript_path": str(transcript_file),
            "transcribed": True,
            "clips_generated": False,
            "exported_clips": [str(output_video_dir / "1.mp4")]
        }
    }

    return {
        'downloads_dir': downloads_dir,
        'temp_dir': temp_dir,
        'output_dir': output_dir,
        'state': state,
        'video_key': 'test_video_ABC123'
    }


def test_get_video_artifacts(setup_test_project):
    """Test: get_video_artifacts retorna estructura correcta"""
    setup = setup_test_project

    # Mock StateManager
    state_manager = StateManager()
    state_manager.save_state(setup['state'])

    cleanup_manager = CleanupManager(
        downloads_dir=str(setup['downloads_dir']),
        temp_dir=str(setup['temp_dir']),
        output_dir=str(setup['output_dir'])
    )

    artifacts = cleanup_manager.get_video_artifacts(setup['video_key'])

    # Validaciones
    assert 'download' in artifacts
    assert artifacts['download']['exists'] == True
    assert artifacts['download']['size'] > 0

    assert 'transcript' in artifacts
    assert artifacts['transcript']['exists'] == True

    assert 'output' in artifacts
    assert artifacts['output']['exists'] == True
    assert artifacts['output']['clip_count'] == 1
```

---

### Test 3.2: Test Unitario - delete_video_artifacts()

**Objetivo:** Verificar que eliminación funciona y state se actualiza

**Código:**
```python
def test_delete_video_artifacts(setup_test_project):
    """Test: delete_video_artifacts elimina archivos y actualiza state"""
    setup = setup_test_project

    state_manager = StateManager()
    state_manager.save_state(setup['state'])

    cleanup_manager = CleanupManager(
        downloads_dir=str(setup['downloads_dir']),
        temp_dir=str(setup['temp_dir']),
        output_dir=str(setup['output_dir'])
    )

    # Eliminar solo transcript
    results = cleanup_manager.delete_video_artifacts(
        setup['video_key'],
        ['transcript']
    )

    # Validar resultado
    assert results['transcript'] == True

    # Validar archivo eliminado
    transcript_path = Path(setup['state'][setup['video_key']]['transcript_path'])
    assert not transcript_path.exists()

    # Validar state actualizado
    updated_state = state_manager.get_state()
    assert updated_state[setup['video_key']]['transcribed'] == False
    assert updated_state[setup['video_key']]['transcript_path'] is None

    # Download NO debe estar eliminado
    video_path = setup['downloads_dir'] / setup['state'][setup['video_key']]['filename']
    assert video_path.exists()
```

---

### Test 3.3: Test Unitario - dry_run mode

**Objetivo:** Verificar que dry run NO elimina archivos

**Código:**
```python
def test_dry_run_doesnt_delete(setup_test_project):
    """Test: dry_run=True NO elimina archivos"""
    setup = setup_test_project

    state_manager = StateManager()
    state_manager.save_state(setup['state'])

    cleanup_manager = CleanupManager(
        downloads_dir=str(setup['downloads_dir']),
        temp_dir=str(setup['temp_dir']),
        output_dir=str(setup['output_dir'])
    )

    # Dry run de eliminación total
    results = cleanup_manager.delete_video_artifacts(
        setup['video_key'],
        ['download', 'transcript', 'output'],
        dry_run=True
    )

    # Validar que retorna success (simulado)
    assert all(results.values())

    # Validar que archivos SIGUEN EXISTIENDO
    video_path = setup['downloads_dir'] / setup['state'][setup['video_key']]['filename']
    assert video_path.exists()

    transcript_path = Path(setup['state'][setup['video_key']]['transcript_path'])
    assert transcript_path.exists()

    # State NO debe cambiar
    updated_state = state_manager.get_state()
    assert updated_state == setup['state']
```

---

### Test 3.4: Test de Edge Case - Archivo ya eliminado

**Objetivo:** No crashear si archivo no existe

**Código:**
```python
def test_delete_already_missing_file(setup_test_project):
    """Test: Manejar archivo ya eliminado sin crashear"""
    setup = setup_test_project

    state_manager = StateManager()
    state_manager.save_state(setup['state'])

    # Eliminar archivo manualmente
    transcript_path = Path(setup['state'][setup['video_key']]['transcript_path'])
    transcript_path.unlink()

    cleanup_manager = CleanupManager(
        downloads_dir=str(setup['downloads_dir']),
        temp_dir=str(setup['temp_dir']),
        output_dir=str(setup['output_dir'])
    )

    # Intentar eliminar archivo ya missing
    results = cleanup_manager.delete_video_artifacts(
        setup['video_key'],
        ['transcript']
    )

    # Debe reportar success (nada que eliminar = éxito)
    assert results['transcript'] == True

    # State debe actualizarse igual
    updated_state = state_manager.get_state()
    assert updated_state[setup['video_key']]['transcribed'] == False
```

---

### Test 3.5: Test de Integración - delete_all_project_data()

**Objetivo:** Verificar limpieza total del proyecto

**Código:**
```python
def test_delete_all_project_data(setup_test_project):
    """Test: delete_all_project_data elimina TODO"""
    setup = setup_test_project

    state_manager = StateManager()
    state_manager.save_state(setup['state'])

    cleanup_manager = CleanupManager(
        downloads_dir=str(setup['downloads_dir']),
        temp_dir=str(setup['temp_dir']),
        output_dir=str(setup['output_dir'])
    )

    results = cleanup_manager.delete_all_project_data()

    # Validar resultados
    assert results['downloads'] == True
    assert results['temp'] == True
    assert results['output'] == True
    assert results['state'] == True

    # Validar directorios vacíos (pero existen)
    assert setup['downloads_dir'].exists()
    assert setup['temp_dir'].exists()
    assert setup['output_dir'].exists()

    # Validar que están vacíos
    assert len(list(setup['downloads_dir'].glob('*'))) == 0
    assert len(list(setup['temp_dir'].glob('*'))) == 0
    assert len(list(setup['output_dir'].glob('*'))) == 0

    # Validar state reseteado
    updated_state = state_manager.get_state()
    assert updated_state == {}
```

---

### Test 3.6: Test de Edge Case - Permisos insuficientes

**Objetivo:** Manejar errores de permisos gracefully

**Código:**
```python
import os
import stat

def test_permission_error_handling(setup_test_project):
    """Test: Manejar PermissionError sin crashear"""
    setup = setup_test_project

    # Hacer archivo read-only (simular permisos insuficientes)
    video_path = setup['downloads_dir'] / setup['state'][setup['video_key']]['filename']

    # En Unix: quitar permisos de escritura del directorio
    os.chmod(setup['downloads_dir'], stat.S_IRUSR | stat.S_IXUSR)

    try:
        cleanup_manager = CleanupManager(
            downloads_dir=str(setup['downloads_dir']),
            temp_dir=str(setup['temp_dir']),
            output_dir=str(setup['output_dir'])
        )

        results = cleanup_manager.delete_video_artifacts(
            setup['video_key'],
            ['download']
        )

        # Debe reportar fallo (no crashear)
        assert results['download'] == False

        # Archivo debe seguir existiendo
        assert video_path.exists()

    finally:
        # Restaurar permisos
        os.chmod(setup['downloads_dir'], stat.S_IRWXU)
```

---

## 🧪 Manual Testing Checklist

**Test Manual 1: Cleanup de Video Específico**
- [ ] Ejecutar `uv run python cliper.py`
- [ ] Seleccionar opción 3 (Cleanup)
- [ ] Seleccionar opción 1 (Specific video)
- [ ] Elegir video de prueba
- [ ] Seleccionar artifacts a eliminar
- [ ] Confirmar eliminación
- [ ] Validar que archivos fueron eliminados
- [ ] Validar que state se actualizó

**Test Manual 2: Cleanup Outputs Only**
- [ ] Ejecutar cleanup con opción 2 (Outputs only)
- [ ] Confirmar eliminación
- [ ] Validar que outputs/ fue limpiado
- [ ] Validar que downloads/ y temp/ SIGUEN INTACTOS

**Test Manual 3: Cleanup Total**
- [ ] Ejecutar cleanup con opción 3 (Entire project)
- [ ] Escribir "DELETE ALL" para confirmar
- [ ] Validar que TODO fue eliminado
- [ ] Validar que directorios fueron recreados vacíos
- [ ] Validar que state = {}

**Test Manual 4: Flags CLI**
```bash
# Test dry run
uv run python cliper.py --cleanup-all --dry-run

# Validar que muestra lo que HARÍA pero NO elimina

# Test cleanup outputs con confirmación
uv run python cliper.py --cleanup-outputs

# Test cleanup total sin confirmación (peligroso!)
uv run python cliper.py --cleanup-all --yes
```

---

## ✅ Overall Validation Checklist

**Funcionalidad:**
- [ ] CleanupManager lista artifacts correctamente
- [ ] Eliminación de artifacts funciona
- [ ] State se actualiza después de cleanup
- [ ] Dry run NO elimina archivos
- [ ] delete_all_project_data() limpia proyecto completo

**Edge Cases:**
- [ ] Archivos ya eliminados no causan crash
- [ ] Permisos insuficientes se manejan gracefully
- [ ] State corrupto no rompe cleanup
- [ ] Video no existente en state se maneja correctamente

**CLI:**
- [ ] Menú interactivo funciona
- [ ] Confirmación previene eliminaciones accidentales
- [ ] Flags CLI (--cleanup-all, --cleanup-outputs) funcionan
- [ ] Flag --yes skip confirmación
- [ ] Flag --dry-run simula correctamente

**UX:**
- [ ] Rich tables muestran artifacts claramente
- [ ] Mensajes de confirmación son claros
- [ ] Mensajes de éxito/error son informativos
- [ ] Tamaños de archivos se muestran en MB

---

## 🐛 Issues Conocidos

**Issue 1: State sincronizado con filesystem**
- **Problema:** Si usuario elimina archivos manualmente, state queda desincronizado
- **Solución:** CleanupManager debe ser tolerante a archivos missing

**Issue 2: Cleanup interrumpido (Ctrl+C)**
- **Problema:** Si se interrumpe durante cleanup, state puede quedar inconsistente
- **Mitigación:** Best-effort - cada eliminación es atómica, state se actualiza al final

---

## 📊 Coverage Target

**Objetivo:** 80%+ code coverage en `src/cleanup_manager.py`

```bash
# Correr tests con coverage
uv run pytest tests/test_cleanup_manager.py --cov=src/cleanup_manager --cov-report=html

# Ver reporte
open htmlcov/index.html
```

---

**Status:** TODO - Feature lista para implementación

**Estimated Time:** 30-60 min de testing (después de implementar Steps 01-02)
