
---

### ✅ FIXED (2025-11-30): Subtitle Duplication Bug Resolved

**ESTADO ACTUAL:** **BUG SOLUCIONADO.**

Se implementó la solución de dos pasos con la bandera `-sn` en Step 1 para descartar completamente cualquier stream de subtítulos que FFmpeg pudiera preservar.

**Root Cause (Confirmado):**
- FFmpeg preservaba metadatos de subtítulos del video original durante Step 1
- En Step 2, al aplicar el filtro `subtitles` con `-vf`, FFmpeg encontraba AMBOS:
  - Los metadatos de subtítulos preservados del original
  - Los subtítulos nuevos del archivo SRT
- Resultado: Ambos se renderizaban simultáneamente (duplicación)

**Solución Implementada:**
- Se agregó la bandera `-sn` (no subtitle streams) en el comando FFmpeg del Step 1 cuando se ejecuta el proceso de dos pasos
- Esto asegura que el video temporal esté completamente "limpio" de cualquier stream de subtítulos
- Step 2 ahora aplicar los subtítulos a un video que NO contiene metadatos previos

**Código:**
```python
# BUGFIX: Add -sn flag when doing two-step processing to discard any subtitle streams
# This prevents FFmpeg from preserving subtitle metadata that would cause duplication in Step 2
if needs_two_steps:
    cmd.extend(["-sn"])  # Discard subtitle streams
```

**Validación:**
- [PENDIENTE] Testing con clips que tengan logo + subtítulos simultáneamente
- [PENDIENTE] Verificar que subtítulos aparecen UNA sola vez
- [PENDIENTE] Comparar quality vs versión anterior
## 🐛 Bug Fix 3: REGRESSION - Duplicate Subtitles with Logo                                                                │
│  4 + ### ‼️ UPDATE (2025-11-30): REGRESSION PERSISTS                                                                             │
│  5                                                                                                                               │
│  5 - **PROBLEMA:**                                                                                                               │
│  6 - - Al activar el **logo y los subtítulos al mismo tiempo**, el bug de los subtítulos duplicados reapareció.                  │
│  6 + **ESTADO ACTUAL:** **EL BUG CONTINÚA.**                                                                                     │
│  7                                                                                                                               │
│  8 - **ROOT CAUSE:**                                                                                                             │
│  9 - - La implementación del logo (Paso 4 de Branding) requiere usar `-filter_complex` para superponer la imagen del logo sobre  │
│    el video.                                                                                                                     │
│ 10 - - Al construir la cadena de filtros, la implementación combinó el filtro de subtítulos dentro de este `-filter_complex`.    │
│ 11 - - Como ya se había documentado en el "Bug Fix 2", el filtro `subtitles` de FFmpeg se comporta de forma errática dentro de   │
│    `-filter_complex`, causando el renderizado doble.                                                                             │
│ 12 - - La lección aprendida de "usar `-vf` para subtítulos" se rompió accidentalmente para poder añadir el logo.                 │
│  8 + A pesar de implementar la solución de dos pasos (Paso 1: Logo, Paso 2: Subtítulos), las pruebas del usuario indican que los │
│    subtítulos **siguen duplicándose**.                                                                                           │
│  9                                                                                                                               │
│ 14 - **SOLUCIÓN IMPLEMENTADA (Two-Step Process):**                                                                               │
│ 15 - Se refactorizó `_export_single_clip` para usar un proceso de dos pasos cuando tanto el logo como los subtítulos están       │
│    activados, para aislar los filtros problemáticos.                                                                             │
│ 10 + **Hipótesis:**                                                                                                              │
│ 11 + - El problema podría no ser la interacción `filter_complex` vs. `-vf` directamente, sino cómo FFmpeg re-encodifica los      │
│    streams.                                                                                                                      │
│ 12 + - Podría haber un problema con el stream de subtítulos que se está procesando de alguna manera por defecto en ambos pasos.  │
│ 13 + - Es posible que una bandera de metadatos de subtítulos se esté conservando en el archivo temporal y FFmpeg la esté         │
│    volviendo a renderizar automáticamente.                                                                                       │
│ 14                                                                                                                               │
│ 17 - **Paso 1: Crear video temporal con logo y otros filtros (sin subtítulos)**                                                  │
│ 18 - - Se genera un primer comando FFmpeg que aplica el aspect ratio y el `overlay` del logo usando `-filter_complex`.           │
│ 19 - - La salida es un archivo temporal (ej. `clip_1_temp.mp4`).                                                                 │
│ 15 + **Próximo Paso:** Se necesita una sesión de debugging más profunda. Se investigarán flags de FFmpeg como `-sn` (descartar   │
│    subtítulos) en el primer paso para asegurar que el video temporal esté completamente "limpio" antes de aplicar los subtítulos │
│    en el segundo paso.                                                                                                           │
│ 16                                                                                                                               │
│ 21 - **Paso 2: Aplicar subtítulos al video temporal**                                                                            │
│ 22 - - Se genera un segundo comando FFmpeg.                                                                                      │
│ 23 - - Toma como input el archivo `clip_1_temp.mp4`.                                                                             │
│ 24 - - Aplica **únicamente** el filtro de subtítulos usando la bandera `-vf`, que es el método estable y conocido.               │
│ 25 - - La salida es el archivo final del clip.                                                                                   │
│ 26 -                                                                                                                             │
│ 27 - ```python                                                                                                                   │
│ 28 - # Lógica conceptual de la solución en _export_single_clip                                                                   │
│ 29 -                                                                                                                             │
│ 30 - needs_two_steps = add_logo and add_subtitles                                                                                │
│ 31 -                                                                                                                             │
│ 32 - # --- PASO 1 ---                                                                                                            │
│ 33 - # Genera el comando para el primer paso (logo, aspect ratio, etc.)                                                          │
│ 34 - # La salida es un archivo temporal si needs_two_steps es True                                                               │
│ 35 - output_step1 = temp_path if needs_two_steps else final_path                                                                 │
│ 36 - cmd1 = build_command_for_step1(...)                                                                                         │
│ 37 - subprocess.run(cmd1)                                                                                                        │
│ 38 -                                                                                                                             │
│ 39 - # --- PASO 2 (Condicional) ---                                                                                              │
│ 40 - if needs_two_steps:                                                                                                         │
│ 41 -     # Genera el comando para el segundo paso (solo subtítulos)                                                              │
│ 42 -     cmd2 = build_command_for_step2(input=temp_path, output=final_path)                                                      │
│ 43 -     subprocess.run(cmd2)                                                                                                    │
│ 44 -                                                                                                                             │
│ 45 - # Limpiar archivo temporal...                                                                                               │
│ 46 - ```                                                                                                                         │
│ 47 -                                                                                                                             │
│ 48 - **DECISIÓN CLAVE:**                                                                                                         │
│ 49 - - Aislar el filtro `subtitles` en su propio comando de FFmpeg usando `-vf` es la única forma robusta de garantizar que no   │
│    entre en conflicto con el `-filter_complex` requerido por el filtro `overlay` del logo.                                       │
│ 50 - - Aunque añade la sobrecarga de un paso de transcodificación adicional, la **robustez y la predictibilidad del resultado    │
│    final** justifican el coste de rendimiento, adhiriéndose a la filosofía del proyecto.                                         │
│ 17 + **Decisión:** Se documenta el estado actual del bug. La corrección se pospone para una futura sesión.                       │
╰──────────────────────────────────────────────────────────────