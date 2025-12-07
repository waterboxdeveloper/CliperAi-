# Step 03: CLI Integration

**Goal:** Añadir prompts interactivos en `cliper.py` para que el usuario pueda habilitar y configurar el branding automático.

---

## 📋 CLI Design

La interfaz debe ser consistente con las opciones existentes, utilizando `rich` para los prompts. Las nuevas opciones aparecerán en el flujo de exportación de clips.

**Flujo de Usuario Propuesto (Solo Logo):**
```
... (después de seleccionar aspect ratio) ...

[cyan]Add logo overlay to clips?[/cyan] (y/N): y

[dim]Configure advanced logo settings (path, position, scale)?[/dim] (y/N): y
Path to logo file [assets/logo.png]:
Logo position [top-right]: top-left
Logo scale (e.g., 0.1 for 10% of height) [0.1]:
```

---

## ✅ Tasks

### Task 3.1: Localizar el Punto de Integración en `cliper.py`

**File:** `/cliper.py`
**Function:** `opcion_exportar_clips()`

**Action:** Localizar la sección donde se le pregunta al usuario por la configuración de exportación.

- [x] Identificado el punto exacto para insertar los nuevos prompts en `opcion_exportar_clips()` (después de la configuración de face tracking).

---


### Task 3.2: Añadir Prompts Interactivos para Branding

**File:** `/cliper.py`

**Action:** Inserta el bloque de código para manejar la configuración del branding.
**Nota:** Se implementó una versión simplificada solo para el logo, como se solicitó.

```python
# ... después de la lógica de face tracking ...

console.print()
add_logo = Confirm.ask("[cyan]Add logo overlay to clips?[/cyan]", default=False)

logo_path = "assets/logo.svg"
logo_position = "top-right"
logo_scale = 0.1

if add_logo:
    console.print(f"[green]✓[/green] Logo overlay enabled.")
    
    advanced_branding = Confirm.ask(
        "\n[dim]Configure advanced logo settings (path, position, scale)?[/dim]",
        default=False
    )
    if advanced_branding:
        logo_path = Prompt.ask("Path to logo file", default=logo_path)
        logo_position = Prompt.ask(
            "Logo position",
            choices=["top-right", "top-left", "bottom-right", "bottom-left"],
            default=logo_position
        )
        logo_scale_str = Prompt.ask("Logo scale (e.g., 0.1 for 10% of height)", default=str(logo_scale))
        try:
            logo_scale = float(logo_scale_str)
        except ValueError:
            console.print(f"[yellow]Invalid scale, using default: {logo_scale}[/yellow]")
```
- [x] Añadido el prompt para seleccionar la superposición del logo.
- [x] La variable `add_logo` se establece correctamente.
- [x] Añadido un prompt opcional para configurar ajustes avanzados del logo.
- [ ] La lógica para `add_outro` está pendiente.

---


### Task 3.3: Pasar los Parámetros a `exporter.export_clips()`

**File:** `/cliper.py`

**Action:** Modifica la llamada a `exporter.export_clips()` para incluir los nuevos parámetros de branding.

**Llamada actualizada:**
```python
exported_paths = exporter.export_clips(
    # ...
    # BRANDING (NUEVO)
    add_logo=add_logo,
    logo_path=logo_path,
    logo_position=logo_position,
    logo_scale=logo_scale,
    # add_outro y outros_path están pendientes
)
```

- [x] `add_logo` se pasa a `export_clips`.
- [x] `logo_path` se pasa a `export_clips`.
- [x] `logo_position` se pasa a `export_clips`.
- [x] `logo_scale` se pasa a `export_clips`.
- [ ] `add_outro` y `outros_path` están pendientes.

---

## 🎯 Validation Checklist

- [x] Los nuevos prompts de branding para el logo aparecen en el flujo de exportación de `cliper.py`.
- [x] El usuario tiene la opción de especificar rutas y ajustes personalizados para el logo.
- [x] Los nuevos parámetros del logo se pasan correctamente a la función `exporter.export_clips()`.
- [x] El código en `cliper.py` es sintácticamente correcto.
- [ ] La integración del outro está pendiente.

---

**Next Step:** `04-testing.md` →

```