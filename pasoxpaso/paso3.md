# Paso 3: Reframing Inteligente con Detección de Rostros

## 📋 Overview

Este documento describe el plan técnico para una nueva característica en CLIPER: **Reframing Inteligente con Detección de Rostros**.

**Objetivo Final:** Mejorar drásticamente la calidad visual de los clips verticales generados por la herramienta. En lugar de un simple recorte central, el sistema detectará el rostro del orador en el video original (formato ancho) y ajustará dinámicamente el encuadre vertical (9:16) para mantener siempre al orador como el punto focal.

---

## 🎨 Decisiones de Diseño (Basado en Requerimientos)

Tras analizar la idea, se han definido los siguientes comportamientos clave para la funcionalidad:

1.  **Manejo de Múltiples Rostros:**
    *   **Decisión:** El sistema se centrará en el **rostro más grande** que aparezca en el encuadre. Esto asume que el orador principal ocupará más espacio en la pantalla.

2.  **Ausencia de Rostros:**
    *   **Decisión:** En los segmentos del video donde no se detecte ningún rostro (por ejemplo, al mostrar una diapositiva o un producto), el sistema aplicará un **recorte central estático** por defecto.

3.  **Estilo de Movimiento de Cámara:**
    *   **Decisión:** Se implementarán **dos modos** de seguimiento para poder probar y elegir el más adecuado:
        *   **Modo `instant`:** El encuadre se centra perfectamente en el rostro en cada fotograma. Es más fácil de implementar y preciso, pero puede resultar robótico.
        *   **Modo `smooth`:** El encuadre sigue al rostro con una ligera suavidad y aceleración, imitando a un operador de cámara real. Es más complejo pero ofrece un resultado más profesional y agradable a la vista.

4.  **Control del Usuario (CLI):**
    *   **Decisión:** La funcionalidad se activará a través de un flag opcional en el CLI.
        *   Flag de activación: `--enable-face-tracking`
        *   Flag de estilo: `--face-tracking-style <instant|smooth>` (con `smooth` como valor por defecto).

---

## 🔬 Investigación Técnica Propuesta

Para implementar esta funcionalidad, se investigarán y utilizarán librerías de Python especializadas en computer vision.

1.  **Procesamiento de Video (Lectura y Escritura de Frames):**
    *   **Herramienta Principal:** **OpenCV (`cv2`)**. Es el estándar de la industria para la manipulación de video en Python. Nos permitirá leer el video de entrada fotograma a fotograma, procesarlos y escribir el video vertical de salida.

2.  **Detección de Rostros:**
    *   **Candidato Principal:** **MediaPipe (de Google)**. Es una librería moderna, de alto rendimiento y alta precisión, optimizada para flujos de video en tiempo real. Ofrece un excelente balance entre velocidad y exactitud.
    *   **Alternativa:** **MTCNN (Multi-task Cascaded Convolutional Networks)**. Es conocido por su alta precisión, aunque puede ser más lento. Podría considerarse para un modo de "ultra alta calidad" en el futuro.

3.  **Suavizado de Trayectoria (Path Smoothing) para el modo `smooth`:**
    *   Para evitar movimientos bruscos, las coordenadas del rostro detectado a lo largo del tiempo deben ser suavizadas.
    *   **Técnica Propuesta:** Investigar el uso de un **filtro de media móvil (moving average)** o un **Filtro de Kalman**. Un filtro de media móvil es más simple de implementar y debería ser suficiente para lograr un efecto de paneo suave.

---

## 📝 Plan de Implementación Preliminar

1.  **Fase 3.1 (Prueba de Concepto - "Spike"):**
    *   [ ] Instalar `opencv-python` y `mediapipe`.
    *   [ ] Crear un script de prueba aislado para detectar rostros en una sola imagen estática y dibujar un recuadro sobre ellos.
    *   [ ] Extender el script para procesar un video corto (5-10 segundos), detectando y almacenando las coordenadas del rostro más grande en cada fotograma.
    *   [ ] Validar el rendimiento y la precisión.

2.  **Fase 3.2 (Lógica de Recorte):**
    *   [ ] Crear un nuevo módulo, por ejemplo `src/reframer.py`.
    *   [ ] Implementar la lógica de recorte `instant`. Esta función tomará las coordenadas de un rostro y las dimensiones de un frame, y devolverá el área de recorte (9:16) centrada en el rostro.
    *   [ ] Implementar la lógica de suavizado (media móvil) sobre una lista de coordenadas.
    *   [ ] Implementar la lógica de recorte `smooth` utilizando las coordenadas suavizadas.

3.  **Fase 3.3 (Integración con CLIPER):**
    *   [ ] Modificar el proceso de generación de clips en `cliper.py` (o donde corresponda).
    *   [ ] Añadir los nuevos flags (`--enable-face-tracking`, `--face-tracking-style`) al CLI.
    *   [ ] Si el flag está activado, invocar la nueva lógica del `reframer.py` para generar los clips con encuadre dinámico en lugar del recorte estático.

4.  **Fase 3.4 (Pruebas):**
    *   [ ] Probar la funcionalidad con diferentes videos de entrada (una persona, varias personas, sin personas).
    *   [ ] Comparar la calidad visual de los clips generados con y sin la nueva funcionalidad.
    *   [ ] Comparar los resultados de los modos `instant` y `smooth`.
