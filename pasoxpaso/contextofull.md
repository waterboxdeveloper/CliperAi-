# Contexto Completo y Stack para Integración de Nuevas Features

## 1. Resumen del Proyecto CLIPER

*   **Misión:** CLIPER es una herramienta CLI de Python que automatiza la creación de clips de video cortos y virales a partir de contenido de formato largo. Su objetivo es gestionar todo el pipeline, desde la descarga del video hasta la generación de copys de IA y la exportación de archivos listos para publicar.

*   **Arquitectura Core:** El sistema se basa en una pipeline modular y secuencial:
    1.  **Descarga (`yt-dlp`):** Obtiene el video fuente.
    2.  **Transcripción (`WhisperX`):** Realiza una transcripción local de audio a texto con alta precisión.
    3.  **Detección de Clips (`ClipsAI`):** Identifica semánticamente los cambios de tema para encontrar los mejores puntos de corte.
    4.  **Generación de Copys (`LangGraph + Gemini`):** Crea captions atractivos y adaptados al estilo de cada clip.
    5.  **Exportación (`FFmpeg`):** Corta, redimensiona y añade subtítulos a los videos finales.

*   **Entorno de Ejecución:** Es una herramienta de línea de comandos de Python diseñada para funcionar tanto localmente (con `uv`) como dentro de un contenedor Docker, con un fuerte énfasis en Docker para la reproducibilidad.

## 2. Stack Tecnológico Actual

| Componente | Tecnología Clave | Rol en el Proyecto |
| :--- | :--- | :--- |
| **Lenguaje** | Python 3.9+ | Lenguaje principal de la aplicación. |
| **Gestor de Dependencias** | `uv` | Para una instalación y gestión de dependencias rápida y reproducible. |
| **Framework CLI** | `Typer` / `Rich` | Para crear una interfaz de línea de comandos moderna, interactiva y visualmente atractiva. |
| **Procesamiento de Video/Audio** | `FFmpeg`, `yt-dlp` | `yt-dlp` para descargas robustas; `FFmpeg` para toda la manipulación de video y audio. |
| **Transcripción (Local)** | `WhisperX` | Transcripción de voz a texto con timestamps a nivel de palabra, ejecutándose 100% localmente. |
| **Detección de Clips (Local)** | `ClipsAI` | Implementa el algoritmo TextTiling sobre embeddings BERT para la segmentación semántica del texto. |
| **Generación de IA (API)** | `LangGraph`, `Pydantic`, `langchain-google-genai` | Orquesta un flujo de 10 nodos para clasificar clips y generar copys con el modelo Gemini de Google. `Pydantic` asegura la validación estricta de los datos. |
| **Contenerización** | `Docker`, `Docker Compose` | Para empaquetar la aplicación y todas sus dependencias, garantizando un entorno consistente. |

## 3. Filosofía de Desarrollo

El análisis de los documentos de planificación (`paso2.md`, `paso3.md`) revela una filosofía de desarrollo profesional y madura:

*   **Planificación Detallada:** Se valora la creación de planes técnicos exhaustivos (`pasoxpaso/*.md`) antes de escribir código.
*   **Modularidad y Single Responsibility:** Cada componente del sistema (`downloader.py`, `transcriber.py`, etc.) tiene una única y clara responsabilidad.
*   **Robustez y Tolerancia a Fallos:** El flujo de `LangGraph` es un claro ejemplo, con reintentos automáticos, degradación elegante (acepta éxito parcial) y manejo de errores a nivel de batch.
*   **Validación de Datos Estricta:** Se utiliza `Pydantic` de forma intensiva para la validación de datos en tiempo de ejecución, incluyendo validadores personalizados para reglas de negocio (ej. `#AICDMX` obligatorio).
*   **Eficiencia de Costos y Privacidad:** Se priorizan modelos locales (`WhisperX`, `ClipsAI`) para reducir costos de API y garantizar la privacidad de los datos. Las llamadas a API son optimizadas (ej. batch processing).
*   **Reproducibilidad:** Hay un fuerte énfasis en el uso de `uv.lock` y `Dockerfile` para asegurar que el entorno de desarrollo y ejecución sea consistente en cualquier máquina.

## 4. Stack Propuesto para "Reframing Inteligente"

Basado en el plan de `paso3.md`, la integración de la nueva característica de reframing facial se alinea con la filosofía del proyecto.

*   **Objetivo de la Feature:** Convertir videos de formato ancho a vertical, manteniendo el rostro del orador centrado dinámicamente en el encuadre.

*   **Nuevas Dependencias Requeridas:**
    *   **`opencv-python`**: Esencial para el procesamiento a nivel de frame. Mientras `FFmpeg` es excelente para operaciones de alto nivel (cortar, concatenar), `OpenCV` nos dará el control necesario para leer cada fotograma, analizarlo y escribir un nuevo frame modificado.
    *   **`mediapipe`**: Será la librería principal para la detección de rostros. Es de Google, lo que la alinea con el uso de Gemini, y es conocida por su alto rendimiento y precisión en flujos de video, lo cual es crucial para no ralentizar excesivamente el proceso de exportación.

*   **Integración en la Arquitectura Actual:**
    1.  **Nuevo Módulo:** Se creará un nuevo módulo `src/reframer.py`. Este módulo encapsulará toda la lógica de detección de rostros y cálculo de las coordenadas de recorte, siguiendo el principio de modularidad del proyecto.
    2.  **Modificación del `video_exporter.py`:** El `video_exporter` será modificado. Antes de cortar un clip con `FFmpeg`, invocará al nuevo `reframer.py`.
    3.  **Nuevo Flujo de Exportación:**
        *   `video_exporter.py` recibe las marcas de tiempo del clip a exportar.
        *   Llama a `reframer.py` con la ruta del video original y las marcas de tiempo.
        *   `reframer.py` usa `OpenCV` para leer los frames correspondientes a ese clip.
        *   Para cada frame, `mediapipe` detecta la posición del rostro.
        *   La lógica de suavizado (ej. media móvil) calcula la trayectoria fluida de la "cámara virtual".
        *   `reframer.py` usa `OpenCV` para aplicar el recorte dinámico a cada frame y los compila en un nuevo archivo de video temporal en formato vertical.
        *   Finalmente, `video_exporter.py` toma este video ya reframado y le incrusta los subtítulos como lo hace actualmente.

*   **Impacto en el `Dockerfile`:**
    *   **Dependencias de Python:** Se añadirán `opencv-python` y `mediapipe` al archivo `pyproject.toml`. La imagen de Docker se reconstruirá con `uv sync` para incluirlas.
    *   **Dependencias del Sistema:** `OpenCV` puede requerir librerías de sistema adicionales para el manejo de video y GUI (aunque no se usará GUI). Será necesario verificar si la imagen base `python:3.10-slim-buster` las incluye. Es común tener que añadir paquetes como `libgl1-mesa-glx`. Esto se añadirá a la sección `RUN apt-get install` del `Dockerfile`.

## 5. Consideraciones para Futuras Integraciones (Paso 4 y más allá)

**Recordatorio Arquitectónico:** El plan para el `paso4` (integración del scheduler `Postiz`) se basa en una arquitectura de **múltiples contenedores orquestada por `docker-compose.yml`**. En esa fase, el contenedor de `cliper` necesitará comunicarse con el contenedor de `postiz` a través de una red interna de Docker.

**Implicaciones para el `paso3` (Reframing Inteligente):**
*   **Separación de incumbencias a nivel de infraestructura:** Cualquier cambio realizado en el `Dockerfile` de `cliper` para la funcionalidad de reframing debe ser **auto-contenido** y específico para las necesidades de procesamiento de video.
*   **No mezclar responsabilidades:** No se deben añadir dependencias o configuraciones relacionadas con la publicación o comunicación de red en el `Dockerfile` de `cliper`. La responsabilidad de conectar los servicios recaerá exclusivamente en `docker-compose.yml`.
*   **Visión a largo plazo:** Al implementar el reframing, debemos asegurar que el contenedor `cliper` siga siendo un "worker" de procesamiento de video puro y agnóstico a cómo su output será utilizado después. Esto mantendrá la arquitectura limpia y facilitará la integración del servicio de publicación `Postiz` en el futuro.

