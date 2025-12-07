# Architecture Alignment Review: Branding Feature

**Purpose:** Verificar que la implementación propuesta para la feature de "Branding Automático" se alinea con la arquitectura y filosofía existentes de CLIPER.

---

## ✅ Verified Architecture Alignment

### 1. **Punto de Integración: `video_exporter.py`** ✓

**Filosofía de CLIPER:** Cada módulo tiene una única responsabilidad. `video_exporter.py` es el orquestador de FFmpeg.

**Plan Propuesto (`branding.md`):**
-   La lógica de overlay de logo y concatenación de outro reside en `video_exporter.py`.

**Análisis de Alineación:**
-   ✅ **Correcto.** Ambas operaciones (overlay y concat) son tareas de manipulación de video realizadas por FFmpeg. Centralizar esta lógica en `video_exporter` es coherente con el principio de responsabilidad única.
-   ✅ **Evita Overhead.** Crear un `branding_manager.py` sería sobre-ingeniería para esta tarea, como se identificó correctamente en el análisis de alternativas.

---

### 2. **Uso de Dependencias: FFmpeg Nativo** ✓

**Filosofía de CLIPER:** Minimizar dependencias externas y usar herramientas robustas y probadas. El uso de `subprocess` para llamar a FFmpeg es un patrón establecido.

**Plan Propuesto:**
-   Utilizar los filtros `overlay` y `concat` de FFmpeg a través de `subprocess.run()`.

**Análisis de Alineación:**
-   ✅ **Alineado.** No introduce nuevas dependencias de Python (como `moviepy` u otras librerías de alto nivel), lo que mantiene el entorno simple y estable.
-   ✅ **Consistente.** Sigue el mismo patrón que el resto de `video_exporter.py` y la solución implementada en `reframer.py` (que finalmente usó un `subprocess.Popen` para `FFmpegVideoWriter`).

---

### 3. **Flujo de Datos y Archivos Temporales** ✓

**Filosofía de CLIPER:** Los módulos operan sobre archivos y los pasan al siguiente paso. El manejo de archivos temporales es aceptado si es necesario y se realiza una limpieza adecuada.

**Plan Propuesto (`02-outro-concatenation.md`):**
1.  Exportar clip principal a `*_temp.mp4`.
2.  Concatenar `*_temp.mp4` con el video de outro.
3.  Guardar como `*.mp4` final.
4.  Eliminar `*_temp.mp4`.

**Análisis de Alineación:**
-   ✅ **Correcto.** Este enfoque de "paso intermedio" es robusto. Aísla la complejidad de la concatenación de la complejidad de los otros filtros (subtítulos, face tracking, etc.).
-   ✅ **Robusto.** En caso de que la concatenación falle, el archivo temporal aún existe y se puede usar como fallback (como se especifica en el plan), adhiriéndose al principio de "degradación elegante".

---

### 4. **Integración con CLI (`cliper.py`)** ✓

**Filosofía de CLIPER:** La interfaz de usuario debe ser interactiva, clara y permitir la configurabilidad sin necesidad de tocar el código.

**Plan Propuesto (`03-cli-integration.md`):**
-   Añadir un prompt interactivo para que el usuario elija el nivel de branding.
-   Permitir la configuración de rutas personalizadas como una opción avanzada.
-   Mantener la funcionalidad como "opt-in" (desactivada por defecto).

**Análisis de Alineación:**
-   ✅ **Alineado.** Utiliza los mismos componentes de `rich` (`Prompt`, `Confirm`) que el resto del CLI.
-   ✅ **Configurable.** Sigue el principio de no hardcodear valores y dar control al usuario.
-   ✅ **No Rompe la Retrocompatibilidad.** Al ser opt-in, los usuarios que no deseen usar la función no verán cambios en su flujo de trabajo.

---

### 5. **Estructura de Assets** ✓

**Filosofía de CLIPER:** La estructura de archivos debe ser predecible.

**Plan Propuesto:**
-   El logo se espera en `assets/logo.png`.
-   Los outros se esperan en `assets/outros/outro_{aspect_ratio}.mp4`.

**Análisis de Alineación:**
-   ✅ **Correcto.** Establece una convención clara y documentada. El plan también incluye la opción de anular estas rutas por defecto, lo que añade la flexibilidad necesaria.

---

## 🎯 Confidence Level

**Architecture Alignment: 100%**

La implementación propuesta en los archivos `todoBRANDING` está perfectamente alineada con la arquitectura y los principios de diseño de CLIPER.

-   ✅ **Modularidad:** Se integra en el módulo correcto.
-   ✅ **Robustez:** El manejo de archivos temporales y la degradación elegante están considerados.
-   ✅ **Consistencia:** Utiliza las mismas herramientas (FFmpeg, `rich`) y patrones (subprocess) que el resto del proyecto.
-   ✅ **Configurabilidad:** Es opt-in y permite personalización.

---

## 🚀 Próximo Paso

La fase de planificación está completa y validada. La arquitectura es sólida.
Proceder con la implementación de los pasos descritos en:
1.  `01-logo-overlay.md`
2.  `02-outro-concatenation.md`
3.  `03-cli-integration.md`

Comenzando por modificar `src/video_exporter.py` según el Step 01.
