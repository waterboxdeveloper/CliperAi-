# Paso 1: Instalar langchain-anthropic

**Tiempo**: 15 minutos
**Cambios**: pyproject.toml, .env

---

## ✅ Paso 1.1: Agregar dependencia a pyproject.toml

Editar `/Users/ee/Documents/opino.tech/Cliper/pyproject.toml`:

```diff
  dependencies = [
    "clipsai",
    "whisperx @ git+https://github.com/m-bain/whisperx.git",
    "yt-dlp>=2026.02.04",
    "python-dotenv",
    "loguru",
    "typer",
    "tqdm",
    "pydantic",
    "ffmpeg-python",
    "rich>=14.2.0",
    "faster-whisper>=1.2.0",
-   "langchain-google-genai>=2.1.12",  ← REMOVER
+   "langchain-anthropic>=0.1.0",       ← AGREGAR
    "langgraph>=0.6.11",
    "opencv-python>=4.8.0",
    "mediapipe>=0.10.0",
  ]
```

---

## ✅ Paso 1.2: Instalar dependencias

```bash
cd /Users/ee/Documents/opino.tech/Cliper
uv sync
```

Expected output:
```
Resolved 150+ packages
Installed langchain-anthropic==0.1.x
```

---

## ✅ Paso 1.3: Agregar ANTHROPIC_API_KEY a .env

Editar `/Users/ee/Documents/opino.tech/Cliper/.env`:

```bash
# Anthropic Claude API (reemplaza Gemini)
ANTHROPIC_API_KEY=sk-ant-...your-key-here...

# (Puedes dejar GOOGLE_API_KEY si quieres fallback a Gemini)
# GOOGLE_API_KEY=...
```

**Obtener API Key**:
1. Ve a https://console.anthropic.com/
2. Crea cuenta o inicia sesión
3. Ve a "API Keys"
4. Crea nueva clave
5. Cópiala al .env

---

## ✅ Paso 1.4: Verificar instalación

```bash
python -c "from langchain_anthropic import ChatAnthropic; print('✅ langchain-anthropic installed')"
```

Expected output:
```
✅ langchain-anthropic installed
```

---

## ✅ Verificación

- [ ] pyproject.toml actualizado (langchain-anthropic agregado)
- [ ] uv sync ejecutado exitosamente
- [ ] .env tiene ANTHROPIC_API_KEY
- [ ] Import funciona correctamente

---

## 🚀 Próximo: Paso 2

Una vez completado este paso, proceder a cambiar los imports en copys_generator.py.

**Paso 2**: `02-change-imports.md`
