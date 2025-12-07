# Step 04: Testing & Validation

**Goal:** Probar de forma integral la funcionalidad de branding (logo y outro) para asegurar que funciona como se espera en diferentes escenarios.

---

## 📋 Testing Strategy

Necesitamos verificar que la superposición del logo y la concatenación del outro funcionen correctamente de forma individual y en conjunto, y que no interfieran con otras funcionalidades existentes como los subtítulos y el face tracking.

**Assets de prueba necesarios:**
-   Un archivo `assets/logo.png` con transparencia.
-   Un directorio `assets/outros/` que contenga al menos:
    -   `outro_9-16.mp4`
    -   `outro_1-1.mp4`

---

## ✅ Test Cases

### Test 4.1: Funcionalidad Básica

**Video:** Usa el video de prueba habitual.
**Exportación:** Exporta un solo clip corto (~10 segundos).

| Test | Configuración de Branding | Aspect Ratio | Otras Opciones | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **A1** | Solo Logo | `9:16` | Subtítulos: No, Face Tracking: No | ✓ El clip final tiene el logo en la esquina superior derecha. |
| **A2** | Solo Outro | `9:16` | Subtítulos: No, Face Tracking: No | ✓ El clip final dura ~13-15s y el outro se añade al final. |
| **A3** | Logo + Outro | `9:16` | Subtítulos: No, Face Tracking: No | ✓ El clip final tiene el logo y el outro. |
| **A4** | Ninguno | `9:16` | Subtítulos: No, Face Tracking: No | ✓ El clip final no tiene ni logo ni outro (comportamiento original). |

**Checklist de Validación:**
- [ ] **Test A1:** El video exportado tiene el logo. La duración es correcta.
- [ ] **Test A2:** El video exportado tiene el outro al final. La duración es mayor. El video y audio están sincronizados.
- [ ] **Test A3:** El video exportado tiene tanto el logo visible durante el clip como el outro al final.
- [ ] **Test A4:** El video se exporta sin modificaciones de branding.

---

### Test 4.2: Interacción con Otras Features

**Objetivo:** Asegurar que el branding no rompe los subtítulos ni el face tracking.

| Test | Configuración de Branding | Aspect Ratio | Otras Opciones | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **B1** | Logo + Outro | `9:16` | Subtítulos: **Sí**, Face Tracking: No | ✓ El clip tiene logo, subtítulos quemados y el outro al final. |
| **B2** | Logo + Outro | `9:16` | Subtítulos: **Sí**, Face Tracking: **Sí** | ✓ El clip tiene reencuadre dinámico, logo, subtítulos y el outro. |
| **B3** | Logo + Outro | `1:1` | Subtítulos: **Sí**, Face Tracking: No | ✓ Se usa `outro_1-1.mp4`. Todo funciona en aspect ratio cuadrado. |

**Checklist de Validación:**
- [ ] **Test B1:** Los subtítulos y el logo no se superponen de forma incorrecta. El outro se añade correctamente después del clip con subtítulos.
- [ ] **Test B2:** El flujo completo (face track → logo/subs → outro) funciona sin errores. El resultado visual es el esperado.
- [ ] **Test B3:** El sistema selecciona y concatena el outro correcto para el aspect ratio `1:1`.

---

### Test 4.3: Manejo de Errores y Casos Borde

**Objetivo:** Probar cómo se comporta el sistema cuando los assets de branding no están disponibles.

| Test | Configuración | Escenario | Resultado Esperado |
| :--- | :--- | :--- | :--- |
| **C1** | Solo Logo | Renombrar `assets/logo.png` a `logo_backup.png` | ✓ El CLI muestra un `warning` en el log. El clip se exporta sin logo. No hay crash. |
| **C2** | Solo Outro | Renombrar `assets/outros/outro_9-16.mp4` | ✓ El CLI muestra un `warning` en el log. El clip se exporta sin outro. No hay crash. |
| **C3** | Rutas Personalizadas | Usar el prompt para dar una ruta inválida al logo | ✓ El sistema avisa que no encontró el logo y continúa, exportando sin él. |

**Checklist de Validación:**
- [ ] **Test C1:** El sistema falla de forma "elegante", avisando al usuario pero completando la exportación.
- [ ] **Test C2:** El sistema no crashea si falta un video de outro específico.
- [ ] **Test C3:** La configuración de rutas personalizadas funciona y también maneja errores si la ruta es incorrecta.

---

## 🎯 Overall Validation Checklist

- [ ] La opción de branding aparece correctamente en el CLI.
- [ ] La selección de "Solo Logo", "Solo Outro", y "Logo + Outro" funciona.
- [ ] El logo se superpone correctamente sin afectar la calidad del video.
- [ ] El outro se concatena correctamente, manteniendo la sincronización de audio y video.
- [ ] La funcionalidad es compatible con los subtítulos quemados.
- [ ] La funcionalidad es compatible con el face tracking.
- [ ] El sistema no se detiene si faltan los archivos de assets, sino que advierte al usuario y continúa.
- [ ] Los archivos temporales (`_temp.mp4`) se eliminan correctamente después de la operación.

---

**Next Step:** ¡Implementación! Es hora de modificar el código en `src/video_exporter.py` y `cliper.py`.
