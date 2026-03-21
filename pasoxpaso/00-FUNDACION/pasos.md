
## Módulos del Sistema
- **Downloader**: Descarga videos YouTube con yt-dlp
- **Transcriber**: Transcribe con WhisperX (timestamps precisos)
- **Clipper**: Detecta clips con ClipsAI (algoritmo TextTiling)
- **Editor**: Corta clips del video original
- **Resizer**: Adapta formato para redes sociales (9:16)
- **Pipeline**: Orquesta todo el flujo
- **Utils**: Funciones compartidas

## Pasos Completados

### 1. Estructura de Carpetas ✅
- Crear carpeta `src/` para código principal
- Crear carpeta `config/` para configuración
- Crear carpeta `output/` con subcarpetas: `videos/`, `transcriptions/`, `clips/`
- Crear carpetas `tests/` y `docs/`
- Agregar archivos `__init__.py` para hacer paquetes Python

### 2. Entorno Virtual ✅
- Crear entorno virtual con `uv venv`
- Activar entorno virtual con `source .venv/bin/activate`
- Verificar que Python apunta al entorno correcto

### 3. Dependencias del Sistema ✅
- Instalar `libmagic` y `ffmpeg` con Homebrew
- Verificar que están instalados correctamente

### 4. Configuración del Proyecto ✅
- Crear archivo `pyproject.toml` con configuración completa
- Configurar `requires-python = ">=3.9,<3.14"` (requerido por WhisperX)
- Agregar `[tool.hatch.metadata]` con `allow-direct-references = true`
- Configurar `[tool.hatch.build.targets.wheel]` con `packages = ["src"]`
- Usar `[dependency-groups]` en lugar de `[tool.uv]` deprecado

### 5. Dependencias Core ✅
- **ClipsAI**: Librería principal para detectar clips
- **WhisperX**: Desde GitHub para transcripción con timestamps precisos
- **yt-dlp**: Descarga robusta de YouTube
- **python-dotenv**: Variables de entorno
- **loguru**: Logging mejorado
- **typer**: CLI moderna
- **tqdm**: Progress bars
- **pydantic**: Validación de datos
- **ffmpeg-python**: Wrapper de FFmpeg

### 6. Dependencias de Desarrollo ✅
- **pytest**: Testing framework
- **pytest-cov**: Coverage de tests
- **black**: Formateador de código
- **isort**: Organizador de imports
- **mypy**: Type checker

### 7. Instalación de Dependencias ✅
- Ejecutar `uv sync` para instalar todas las dependencias
- Verificar que ClipsAI y WhisperX se instalan correctamente
- Confirmar que todas las 197+ dependencias se resuelven

## Próximos Pasos
1. Crear archivo `.env` con variables de entorno
2. Implementar módulo `downloader.py` (más simple, valida que todo funciona)
3. Implementar módulo `transcriber.py` (núcleo del sistema)
4. Implementar módulo `clipper.py` (usa transcripción)
5. Implementar módulo `editor.py` (usa clips detectados)
6. Implementar módulo `resizer.py` (polish final)
7. Implementar módulo `pipeline.py` (integra todo)
8. Crear CLI (interfaz de usuario)

## Tecnologías Clave
- **ClipsAI**: Algoritmo TextTiling con BERT para detectar cambios de tema
- **WhisperX**: Transcripción con alineación de palabras
- **yt-dlp**: Descarga de YouTube más robusta que pytube
- **FFmpeg**: Motor de procesamiento de video/audio
- **uv**: Gestor de dependencias rápido y moderno

## Limitaciones Conocidas
- ClipsAI solo funciona bien con contenido narrativo (podcasts, entrevistas)
- WhisperX es lento en CPU (10-15 min para 1 hora de video)
- Requiere FFmpeg instalado en sistema
- Pyannote requiere token de HuggingFace para redimensionar
