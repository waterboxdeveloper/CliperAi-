# Paso 3: Automatización de Publicación con Postiz

## 📋 Overview

Este documento describe el plan técnico para la Fase 3 del proyecto CLIPER: la automatización completa de la publicación de contenido en redes sociales.

**Objetivo Final:** Crear un flujo de trabajo "end-to-end" donde, una vez que CLIPER ha generado los clips de video y los copies de IA, un sistema automatizado se encargue de **programar** su publicación en las plataformas de redes sociales designadas (ej. TikTok, Instagram Reels, YouTube Shorts).

Para esto, integraremos la herramienta open-source **Postiz**, que actuará como nuestro servidor de publicación y programación.

---

## 🚀 Visión del Flujo Automatizado

El proceso completo, uniendo CLIPER (Fase 1-2) con Postiz (Fase 3), se verá así:

1.  **Input**: Un usuario provee una URL de un video largo a CLIPER.
2.  **Procesamiento (CLIPER)**:
    *   Descarga, transcribe y genera clips (`.mp4`).
    *   Genera copies, hashtags y metadata optimizada para cada clip (`clips_copys.json`).
3.  **Programación (Postiz - NUEVO)**:
    *   Un nuevo comando en CLIPER (`uv run cliper.py --publish`) con opciones de scheduling (ej. `--start-date "2025-12-01 09:00" --interval 4h`) lee los videos y su metadata.
    *   Se comunica con la **API Pública de Postiz**, enviando cada clip con su fecha y hora de publicación calculada.
    *   Postiz añade las publicaciones a su calendario.
4.  **Publicación (Postiz)**: A la hora programada, Postiz publica automáticamente el contenido en la red social correspondiente.
5.  **Gestión (Dashboard de Postiz)**: El usuario puede visualizar el calendario de contenido, hacer ajustes manuales, o cancelar publicaciones desde la interfaz web de Postiz.

---

## 🛠️ Análisis de la Herramienta Open Source (Postiz)

1.  **Nombre de la Herramienta**: **Postiz**
2.  **Repositorio**: [`https://github.com/gitroomhq/postiz-app`](https://github.com/gitroomhq/postiz-app)
3.  **Descripción General**:
    *   **¿Qué es?**: Postiz es una plataforma open-source para la programación y publicación de contenido en redes sociales, con funcionalidades de IA. Su API pública está diseñada para permitir la automatización y el manejo de contenido de forma "headless".
    *   **Stack Tecnológico**: Es un monorepo moderno basado en TypeScript, utilizando **Next.js** para el frontend, **NestJS** para el backend, **Prisma** como ORM, **PostgreSQL** como base de datos y **Redis** para colas y caché.
4.  **Características Clave**:
    *   **Redes Sociales Soportadas**: TikTok, Instagram, Facebook, YouTube, X (Twitter), LinkedIn, Pinterest, Reddit, Telegram, y más.
    *   **Autenticación**: La API pública utiliza un sistema de **API Key**. La clave se genera en la interfaz de Postiz y debe ser enviada en el header `Authorization` de cada petición.
    *   **Programación**: Su función principal es programar contenido, lo cual es ideal para espaciar las publicaciones de los clips. La API permite especificar una fecha y hora de publicación (`scheduledAt`).
    *   **API**: Ofrece una **API REST pública** y bien definida para la integración. La URL base para una instancia auto-alojada es `http://<host>:<port>/public/v1`.
    *   **Configuración**: Se configura completamente a través de variables de entorno, incluyendo las credenciales de las redes sociales.
5.  **Requisitos de Despliegue**:
    *   **Docker**: Sí, el método de despliegue recomendado es a través de `docker-compose`, utilizando una imagen oficial de `ghcr.io`.
    *   **Dependencias**: PostgreSQL y Redis, ambos gestionados como servicios dentro del mismo `docker-compose`.
6.  **Análisis de Viabilidad**:
    *   **Alineación**: Excelente. Postiz está diseñado precisamente para este caso de uso. Su API pública y su arquitectura basada en Docker lo hacen un complemento perfecto para CLIPER.
    *   **Madurez**: El proyecto es muy popular (más de 24k estrellas en GitHub) y está activamente mantenido, lo que reduce el riesgo de que sea abandonado.
    *   **Curva de Aprendizaje**: Media. La integración requerirá entender su API y el flujo de autenticación, pero la documentación existente y el uso de tecnologías estándar (REST, Docker) facilitan el proceso.

---

## 🗓️ Estrategia de Programación de Contenido (Scheduling)

Proponemos un enfoque híbrido que combina la automatización del CLI con la flexibilidad de un dashboard visual.

1.  **Automatización desde CLIPER (CLI):**
    *   El comando `publish` de CLIPER será el punto de partida. Permitirá al usuario definir una campaña de publicación completa con simples parámetros.
    *   **Nuevos Parámetros del CLI:**
        *   `--start-date`: La fecha y hora para publicar el primer clip (ej. "2025-12-25 09:00").
        *   `--interval`: El tiempo entre cada publicación (ej. `6h` para 6 horas, `1d` para 1 día).
        *   `--platforms`: Los IDs de las plataformas donde se publicará (ej. `tiktok-1,youtube-2`).
    *   **Lógica:** CLIPER calculará la fecha de publicación para cada uno de los 60 clips y los enviará a Postiz a través de la API, llenando el calendario de contenido para las próximas semanas o meses con un solo comando.

2.  **Gestión y Visualización (Dashboard de Postiz):**
    *   Una vez que CLIPER ha hecho la programación masiva, el usuario puede iniciar sesión en la interfaz web de Postiz.
    *   Allí, podrá ver un calendario completo con todos los clips programados.
    *   Podrá realizar ajustes finos: arrastrar un clip a otro día, pausar una publicación, editar un copy de último minuto, etc.

Este flujo de trabajo ofrece lo mejor de ambos mundos: **eficiencia y automatización masiva** desde el CLI, y **control visual y granular** desde el dashboard.

---

## 🏗️ Arquitectura de Integración Propuesta

### **Componentes:**

1.  **CLIPER (Contenedor Existente)**:
    *   Se le añadirá un nuevo módulo `src/publisher.py`.
    *   Se modificará `cliper.py` para agregar el comando `publish` con opciones de scheduling.

2.  **Postiz (Nuevo Grupo de Contenedores)**:
    *   Se ejecutará como un conjunto de servicios separados en nuestro `docker-compose.yml`.
    *   Tendrá sus propios volúmenes para persistir su configuración, base de datos y archivos subidos.

### **Modificaciones en `docker-compose.yml`:**

Añadiremos los servicios de Postiz al `docker-compose.yml` existente.

```yaml
version: '3.8'

services:
  cliper:
    # ... configuración existente de cliper ...
    # El contenedor de cliper ahora dependerá de postiz
    depends_on:
      postiz:
        condition: service_started
    networks:
      - cliper-postiz-network

  # --- SECCIÓN DE POSTIZ ---
  postiz:
    image: ghcr.io/gitroomhq/postiz-app:latest
    container_name: postiz
    restart: always
    environment:
      # --- URLs y Secretos (ajustar para nuestro entorno) ---
      MAIN_URL: "http://localhost:5000"
      FRONTEND_URL: "http://localhost:5000"
      NEXT_PUBLIC_BACKEND_URL: "http://localhost:5000/api"
      JWT_SECRET: "GENERAR_UNA_CADENA_ALEATORIA_Y_UNICA_AQUI"
      DATABASE_URL: "postgresql://postiz-user:postiz-password@postiz-postgres:5432/postiz-db-local"
      REDIS_URL: "redis://postiz-redis:6379"
      
      # --- Configuración de Almacenamiento Local ---
      STORAGE_PROVIDER: "local"
      UPLOAD_DIRECTORY: "/uploads"
      NEXT_PUBLIC_UPLOAD_DIRECTORY: "/uploads"

      # --- API Keys de Redes Sociales (se configuran aquí) ---
      # TIKTOK_CLIENT_ID: "..."
      # TIKTOK_CLIENT_SECRET: "..."
      # YOUTUBE_CLIENT_ID: "..."
      # YOUTUBE_CLIENT_SECRET: "..."
    volumes:
      - postiz-config:/config/
      - postiz-uploads:/uploads/
    ports:
      - "5000:5000"
    networks:
      - cliper-postiz-network
    depends_on:
      postiz-postgres:
        condition: service_healthy
      postiz-redis:
        condition: service_healthy

  postiz-postgres:
    image: postgres:17-alpine
    container_name: postiz-postgres
    restart: always
    environment:
      POSTGRES_PASSWORD: postiz-password
      POSTGRES_USER: postiz-user
      POSTGRES_DB: postiz-db-local
    volumes:
      - postgres-volume:/var/lib/postgresql/data
    networks:
      - cliper-postiz-network
    healthcheck:
      test: pg_isready -U postiz-user -d postiz-db-local
      interval: 10s
      timeout: 3s
      retries: 3

  postiz-redis:
    image: redis:7.2
    container_name: postiz-redis
    restart: always
    healthcheck:
      test: redis-cli ping
      interval: 10s
      timeout: 3s
      retries: 3
    volumes:
      - postiz-redis-data:/data
    networks:
      - cliper-postiz-network

volumes:
  cliper_whisper_models:
  postgres-volume:
  postiz-redis-data:
  postiz-config:
  postiz-uploads:

networks:
  cliper-postiz-network:
```

### **Nuevo Módulo: `src/publisher.py`**

Este módulo contendrá la lógica para interactuar con la API de Postiz.

```python
# src/publisher.py

import requests
import datetime
from typing import Dict, List, Optional

class PostizPublisher:
    def __init__(self, api_base_url: str, api_key: str):
        self.api_url = f"{api_base_url}/public/v1"
        self.headers = {"Authorization": api_key}

    def check_server_status(self) -> bool:
        """Verifica que el servidor Postiz esté disponible."""
        try:
            response = requests.get(f"{self.api_url}/integrations", headers=self.headers)
            return response.status_code == 200
        except (requests.ConnectionError, requests.HTTPError):
            return False

    def _upload_media(self, video_path: str) -> Optional[str]:
        """Sube un archivo de video y retorna el ID del medio."""
        print(f"⬆️ Subiendo video: {video_path}...")
        with open(video_path, 'rb') as f:
            files = {'file': (video_path.split('/')[-1], f, 'video/mp4')}
            response = requests.post(f"{self.api_url}/media/upload", headers=self.headers, files=files)
            response.raise_for_status()
            return response.json().get('id')

    def create_post(self, copy: str, media_id: str, integration_ids: List[str], scheduled_at: Optional[datetime.datetime] = None):
        """Crea o programa una publicación con el medio ya subido."""
        if scheduled_at:
            print(f"🗓️ Programando publicación para: {scheduled_at.isoformat()}")
        else:
            print(f"📝 Publicando inmediatamente...")
        
        payload = {
            "content": copy,
            "integrations": integration_ids,
            "media": [media_id],
            "type": "video",
            # La API de Postiz espera una fecha en formato ISO 8601
            "scheduledAt": scheduled_at.isoformat() if scheduled_at else None,
        }
        response = requests.post(f"{self.api_url}/posts", headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

# Lógica para ser llamada desde cliper.py
def schedule_all_clips_for_video(
    video_id: str, 
    api_key: str, 
    start_date: datetime.datetime, 
    interval: datetime.timedelta,
    platform_ids: List[str]
):
    publisher = PostizPublisher(api_base_url="http://postiz:5000", api_key=api_key)
    if not publisher.check_server_status():
        print("❌ Error: No se pudo conectar al servidor de Postiz.")
        return

    # Cargar clips_copys.json y encontrar archivos de video...
    all_clips = [...] 

    current_schedule_date = start_date
    for clip in all_clips:
        video_path = clip['path']
        copy_text = clip['copy']
        
        media_id = publisher._upload_media(video_path)
        if media_id:
            publisher.create_post(copy_text, media_id, platform_ids, scheduled_at=current_schedule_date)
        
        # Incrementar la fecha para el siguiente clip
        current_schedule_date += interval
```

---

## 📝 Checklist de Implementación

### Fase 3.1: Análisis y Configuración del Servidor Postiz
- [x] **Analizar el repositorio de la herramienta Postiz.**
- [x] **Documentar sus características y API en esta sección.**
- [ ] Añadir los servicios de Postiz al `docker-compose.yml`.
- [ ] Crear un archivo `.env` para gestionar los secretos (JWT_SECRET, API keys de redes sociales).
- [ ] Levantar los servicios (`docker-compose up -d`) y verificar que todos los contenedores se inicien.
- [ ] Acceder a la UI de Postiz (`http://localhost:5000`), crear un usuario y **generar una API Key** desde los ajustes.
- [ ] Realizar una prueba de API manual (usando `curl` o Postman) para confirmar la comunicación.

### Fase 3.2: Integración con CLIPER
- [ ] Crear el archivo `src/publisher.py` con la clase `PostizPublisher` actualizada.
- [ ] Implementar la lógica para leer los clips y sus copies desde los archivos de salida.
- [ ] **Añadir un nuevo comando `publish` a `cliper.py` con opciones de scheduling (`--start-date`, `--interval`).**
- [ ] Añadir la opción al menú interactivo.
- [ ] **Implementar la lógica de cálculo de fechas de publicación en `cliper.py`.**

### Fase 3.3: Pruebas End-to-End
- [ ] Ejecutar el flujo completo: `uv run cliper.py --download ...` -> `uv run cliper.py --publish --start-date ...`.
- [ ] Verificar en el dashboard de Postiz que todos los clips han sido programados correctamente.
- [ ] Verificar que al menos un clip se publica correctamente a la hora programada.
- [ ] Documentar el proceso de configuración y uso final en el `README.md`.

---

## ❓ Preguntas Abiertas y Riesgos

- **Manejo de Secretos**: Las credenciales de las redes sociales se configuran como variables de entorno en el contenedor de Postiz. La API Key de Postiz para CLIPER se debe gestionar de forma segura (ej. variable de entorno, no hardcodear).
- **Tolerancia a Fallos**: El script de publicación debe ser robusto. Si la publicación de un clip falla, debe registrar el error y continuar con el siguiente, en lugar de detener todo el proceso.
- **Límites de API**: **CRÍTICO**: Postiz tiene un rate limit de **30 peticiones por hora**. Al programar las publicaciones con un intervalo (ej. cada 2, 4, o 6 horas), **resolvemos elegantemente este problema**, ya que las llamadas a la API para *crear* los posts programados se hacen de forma secuencial y no violan el límite.
- **Mantenimiento de la Herramienta**: El riesgo es bajo, ya que Postiz es un proyecto popular y activamente mantenido.
- **Selección de Canales**: La lógica de `schedule_all_clips_for_video` necesita una forma de saber a qué canales (`integration_ids`) publicar. Esto se pasará como un argumento del comando (`--platforms`). Se podría mejorar en el futuro para que el CLI pueda listar los canales disponibles desde la API de Postiz.
