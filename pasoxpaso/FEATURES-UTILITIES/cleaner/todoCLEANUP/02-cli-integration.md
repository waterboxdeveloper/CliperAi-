# Step 02: CLI Integration

**Goal:** Integrar CleanupManager en cliper.py para exponer funcionalidad al usuario

---

## 📋 Tasks

### Task 2.1: Agregar opción "Cleanup" al menú principal

- [ ] Modificar menú principal en `cliper.py`
- [ ] Agregar opción 3: "Cleanup project data"

**Ubicación:** `cliper.py` - Función `main()`

**Código a modificar:**

```python
# cliper.py (alrededor de línea 30-50)

def main():
    """Punto de entrada principal del CLI"""

    # ... código existente ...

    while True:
        console.print("\n[bold cyan]CLIPER - AI Video Clip Generator[/bold cyan]")
        console.print("1. Process new video")
        console.print("2. Export clips from existing")
        console.print("3. Cleanup project data")  # [NUEVO]
        console.print("4. Exit")  # Cambiar número

        choice = Prompt.ask(
            "Select option",
            choices=["1", "2", "3", "4"],  # Agregar "3"
            default="1"
        )

        if choice == "1":
            process_new_video()
        elif choice == "2":
            export_existing_clips()
        elif choice == "3":
            cleanup_project_data()  # [NUEVA FUNCIÓN]
        elif choice == "4":
            console.print("[green]Goodbye![/green]")
            break
```

---

### Task 2.2: Implementar función `cleanup_project_data()`

- [ ] Crear función interactiva de cleanup
- [ ] Mostrar videos disponibles
- [ ] Permitir selección granular de artifacts

**Código:**

```python
# cliper.py - Agregar al final del archivo

from src.cleanup_manager import CleanupManager

def cleanup_project_data():
    """
    Flujo interactivo para limpiar artifacts del proyecto

    DECISIÓN: Interactivo con confirmación obligatoria
    RAZÓN: Operación destructiva - prevenir eliminaciones accidentales
    """
    console = Console()
    cleanup_manager = CleanupManager()

    state = StateManager().get_state()

    if not state:
        console.print("[yellow]No project data to clean (state is empty)[/yellow]")
        return

    # Mostrar artifacts disponibles
    console.print("\n[bold]Cleanable Project Data:[/bold]\n")
    cleanup_manager.display_cleanable_artifacts()

    # Opciones de cleanup
    console.print("\n[bold]Cleanup Options:[/bold]")
    console.print("1. Clean specific video")
    console.print("2. Clean all outputs only (keep transcripts)")
    console.print("3. Clean entire project (fresh start)")
    console.print("4. Back to main menu")

    choice = Prompt.ask(
        "Select cleanup option",
        choices=["1", "2", "3", "4"],
        default="4"
    )

    if choice == "1":
        cleanup_specific_video(cleanup_manager, state)
    elif choice == "2":
        cleanup_outputs_only(cleanup_manager, state)
    elif choice == "3":
        cleanup_entire_project(cleanup_manager)
    elif choice == "4":
        return


def cleanup_specific_video(cleanup_manager: CleanupManager, state: dict):
    """Cleanup de un video específico con selección granular"""
    console = Console()

    # Listar videos disponibles
    video_keys = list(state.keys())

    console.print("\n[bold]Available videos:[/bold]")
    for idx, video_key in enumerate(video_keys, 1):
        console.print(f"{idx}. {video_key}")
    console.print(f"{len(video_keys) + 1}. Cancel")

    video_idx = Prompt.ask(
        "Select video to clean",
        choices=[str(i) for i in range(1, len(video_keys) + 2)],
        default=str(len(video_keys) + 1)
    )

    if int(video_idx) == len(video_keys) + 1:
        return  # Cancelar

    selected_video_key = video_keys[int(video_idx) - 1]

    # Mostrar artifacts de ese video
    artifacts = cleanup_manager.get_video_artifacts(selected_video_key)

    console.print(f"\n[bold]Artifacts for '{selected_video_key}':[/bold]")

    artifact_options = []
    for artifact_type, info in artifacts.items():
        if info['exists']:
            size_mb = info['size'] / 1024 / 1024
            console.print(f"  - {artifact_type}: {size_mb:.2f} MB")
            artifact_options.append(artifact_type)

    if not artifact_options:
        console.print("[yellow]No artifacts to clean for this video[/yellow]")
        return

    # Selección granular
    console.print("\n[bold]What to clean?[/bold]")
    console.print("1. All artifacts")
    console.print("2. Select specific artifacts")
    console.print("3. Cancel")

    granular_choice = Prompt.ask(
        "Choose",
        choices=["1", "2", "3"],
        default="3"
    )

    if granular_choice == "3":
        return

    if granular_choice == "1":
        to_delete = artifact_options
    else:
        # Selección manual (simplificado - en producción usar Confirm por cada tipo)
        to_delete = []
        for artifact_type in artifact_options:
            delete_it = Confirm.ask(f"Delete {artifact_type}?", default=False)
            if delete_it:
                to_delete.append(artifact_type)

    if not to_delete:
        console.print("[yellow]Nothing selected to delete[/yellow]")
        return

    # Calcular total a eliminar
    total_size = sum(
        artifacts[t]['size']
        for t in to_delete
        if t in artifacts
    )
    total_mb = total_size / 1024 / 1024

    # CONFIRMACIÓN FINAL
    console.print(f"\n[bold red]⚠️  This will DELETE {len(to_delete)} items ({total_mb:.2f} MB)[/bold red]")
    for t in to_delete:
        console.print(f"  - {t}")

    if not Confirm.ask("\nContinue?", default=False):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    # Ejecutar cleanup
    console.print("\n[bold]Cleaning...[/bold]")
    results = cleanup_manager.delete_video_artifacts(selected_video_key, to_delete)

    # Mostrar resultados
    success_count = sum(1 for r in results.values() if r)
    console.print(f"\n[green]✓ Deleted {success_count}/{len(to_delete)} items ({total_mb:.2f} MB freed)[/green]")


def cleanup_outputs_only(cleanup_manager: CleanupManager, state: dict):
    """Elimina SOLO los outputs exportados (conserva transcripts)"""
    console = Console()

    # Calcular total de outputs
    total_output_size = 0
    total_clips = 0

    for video_key in state.keys():
        artifacts = cleanup_manager.get_video_artifacts(video_key)
        output_info = artifacts.get('output', {})

        if output_info.get('exists'):
            total_output_size += output_info.get('size', 0)
            total_clips += output_info.get('clip_count', 0)

    if total_output_size == 0:
        console.print("[yellow]No exported clips to clean[/yellow]")
        return

    size_mb = total_output_size / 1024 / 1024

    console.print(f"\n[bold]This will delete ALL exported clips:[/bold]")
    console.print(f"  - Videos: {len(state)} videos")
    console.print(f"  - Clips: {total_clips} clips")
    console.print(f"  - Size: {size_mb:.2f} MB")
    console.print("\n[dim]Transcripts and source videos will be preserved[/dim]")

    if not Confirm.ask("\nContinue?", default=False):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    # Eliminar outputs de cada video
    deleted_count = 0
    for video_key in state.keys():
        results = cleanup_manager.delete_video_artifacts(video_key, ['output'])
        if results.get('output'):
            deleted_count += 1

    console.print(f"\n[green]✓ Deleted outputs from {deleted_count} videos ({size_mb:.2f} MB freed)[/green]")


def cleanup_entire_project(cleanup_manager: CleanupManager):
    """Fresh start - elimina TODO el proyecto"""
    console = Console()

    console.print("\n[bold red]⚠️  WARNING: This will DELETE ALL project data:[/bold red]")
    console.print("  - All downloaded videos")
    console.print("  - All transcripts")
    console.print("  - All detected clips")
    console.print("  - All exported clips")
    console.print("  - Project state\n")

    # Confirmación EXTREMA - requiere escribir "DELETE ALL"
    confirmation = Prompt.ask(
        "[bold]Type 'DELETE ALL' to confirm[/bold]",
        default="cancel"
    )

    if confirmation != "DELETE ALL":
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    console.print("\n[bold]Cleaning entire project...[/bold]")

    results = cleanup_manager.delete_all_project_data()

    if all(results.values()):
        console.print("\n[green]✓ Project cleaned successfully[/green]")
        console.print("[dim]Fresh start ready. Run CLIPER to begin.[/dim]")
    else:
        console.print("\n[yellow]⚠ Some items could not be deleted[/yellow]")
        for item, success in results.items():
            status = "✓" if success else "✗"
            console.print(f"  {status} {item}")
```

---

### Task 2.3: Agregar flags de CLI para uso no-interactivo

- [ ] Agregar argparse support para `--cleanup-all`, `--cleanup-outputs`
- [ ] Permitir `--yes` para skip confirmación (CI/CD use case)
- [ ] Permitir `--dry-run`

**Código (al inicio de cliper.py):**

```python
import argparse

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CLIPER - AI Video Clip Generator")

    # Cleanup flags
    parser.add_argument(
        '--cleanup-all',
        action='store_true',
        help='Clean all project data (requires --yes or interactive confirmation)'
    )

    parser.add_argument(
        '--cleanup-outputs',
        action='store_true',
        help='Clean only exported clips (keep transcripts)'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts (dangerous!)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate cleanup without deleting files'
    )

    return parser.parse_args()


def main():
    """Punto de entrada principal"""
    args = parse_args()

    # Si se pasaron flags de cleanup, ejecutar y salir
    if args.cleanup_all or args.cleanup_outputs:
        cleanup_manager = CleanupManager()

        if args.cleanup_all:
            # Confirmación si no hay --yes
            if not args.yes:
                console = Console()
                console.print("[bold red]⚠️  This will DELETE ALL project data[/bold red]")
                if not Confirm.ask("Continue?", default=False):
                    console.print("[yellow]Cancelled[/yellow]")
                    return

            cleanup_manager.delete_all_project_data(dry_run=args.dry_run)

        elif args.cleanup_outputs:
            if not args.yes:
                console = Console()
                console.print("[bold]This will delete all exported clips[/bold]")
                if not Confirm.ask("Continue?", default=False):
                    console.print("[yellow]Cancelled[/yellow]")
                    return

            state = StateManager().get_state()
            for video_key in state.keys():
                cleanup_manager.delete_video_artifacts(
                    video_key,
                    ['output'],
                    dry_run=args.dry_run
                )

        return  # Salir después de cleanup

    # Flujo interactivo normal
    # ... resto del código main existente ...
```

---

## ✅ Validation Checklist

- [ ] Menú principal muestra opción "Cleanup project data"
- [ ] Función `cleanup_project_data()` muestra artifacts con Rich table
- [ ] Cleanup de video específico permite selección granular
- [ ] Cleanup de outputs-only funciona correctamente
- [ ] Cleanup total requiere confirmación "DELETE ALL"
- [ ] Flags CLI funcionan: `--cleanup-all`, `--cleanup-outputs`
- [ ] Flag `--yes` skip confirmación (úsalo con cuidado)
- [ ] Flag `--dry-run` simula sin eliminar

---

## 🧪 Manual Testing

**Test interactivo:**
```bash
uv run python cliper.py
# Seleccionar opción 3
# Probar cada sub-opción
```

**Test con flags:**
```bash
# Dry run de cleanup total
uv run python cliper.py --cleanup-all --dry-run

# Cleanup outputs sin confirmación (CI mode)
uv run python cliper.py --cleanup-outputs --yes
```

---

**Next:** `03-testing.md` - Testing automatizado de CleanupManager
