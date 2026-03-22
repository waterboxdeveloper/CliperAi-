# -*- coding: utf-8 -*-
"""
CLIPER - CLI Principal Unificado
Developed by opino.tech | Powered by AI | CDMX

Este es el punto de entrada principal del proyecto.
Orquesta todo el pipeline: download → transcribe → generate clips → resize
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================================
# SUPPRESS VERBOSE LOGS FROM HEAVY LIBRARIES (BEFORE imports)
# ============================================================================
import logging
import warnings
import os

# Suprimir warnings globalmente
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suprimir stdout/stderr de librerías durante startup
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # TensorFlow
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("torchvision").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("nltk").setLevel(logging.ERROR)
logging.getLogger("pyannote").setLevel(logging.ERROR)
logging.getLogger("whisperx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("numba").setLevel(logging.ERROR)

# Redirigir stderr a /dev/null temporalmente
import io
sys.stderr = io.StringIO()
# ============================================================================

# Rich para interfaz profesional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
from rich.layout import Layout
import time

# Mis módulos
try:
    from src.downloader import YoutubeDownloader
    from src.transcriber import Transcriber
    from src.clips_generator import ClipsGenerator
    from src.video_exporter import VideoExporter
    from src.copys_generator import generate_copys_for_video
    from src.cleanup_manager import CleanupManager
    from src.local_importer import LocalVideoImporter
    from src.utils import get_state_manager
    from src.utils.logger import setup_logger
    from config.content_presets import get_preset, list_presets, get_preset_description
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Ejecuta desde la raíz del proyecto: uv run cliper.py")
    sys.exit(1)

# ============================================================================
# RESTORE stderr after imports (warnings already suppressed)
# ============================================================================
sys.stderr = sys.__stderr__
# ============================================================================

# Console de Rich
console = Console()

# Logger global (será inicializado en main())
logger = None


def mostrar_banner():
    """
    Banner principal profesional de CLIPER
    """
    console.clear()

    # Banner superior con gradiente visual
    console.print()

    # Título principal con estilo
    title = Text()
    title.append("╔", style="bold cyan")
    title.append("════════════════════════════════════════════════════════════", style="cyan")
    title.append("╗", style="bold cyan")
    title.justify = "center"
    console.print(title)

    logo = Text()
    logo.append("║  ", style="cyan")
    logo.append("🎬 CLIPER", style="bold cyan")
    logo.append(" | Video Clipper  ", style="bold white")
    logo.append("║", style="cyan")
    logo.justify = "center"
    console.print(logo)

    subtitle = Text()
    subtitle.append("║  ", style="cyan")
    subtitle.append("Transform long videos into viral clips", style="bold yellow")
    subtitle.append("  ║", style="cyan")
    subtitle.justify = "center"
    console.print(subtitle)

    # Línea de separación
    separator = Text()
    separator.append("╠", style="bold cyan")
    separator.append("════════════════════════════════════════════════════════════", style="cyan")
    separator.append("╣", style="bold cyan")
    separator.justify = "center"
    console.print(separator)

    # Información
    info = Text()
    info.append("║  ", style="cyan")
    info.append("Developed by ", style="dim")
    info.append("opino.tech", style="bold magenta")
    info.append("  |  ", style="dim")
    info.append("Powered by ", style="dim")
    info.append("AI", style="bold green")
    info.append("  |  ", style="dim")
    info.append("CDMX", style="bold yellow")
    info.append("  ║", style="cyan")
    info.justify = "center"
    console.print(info)

    footer_line = Text()
    footer_line.append("╚", style="bold cyan")
    footer_line.append("════════════════════════════════════════════════════════════", style="cyan")
    footer_line.append("╝", style="bold cyan")
    footer_line.justify = "center"
    console.print(footer_line)
    console.print()


class OperationProgress:
    """
    Sistema profesional de Progress + Logs para operaciones largas

    Layout:
    ┌─ PROGRESS (izquierda 60%) ─┬─ LOGS (derecha 40%) ─┐
    │ Bar + info                  │ Panel scrollable     │
    └─────────────────────────────┴──────────────────────┘
    """

    def __init__(self, operation_name: str, total_steps: int = 100):
        self.operation_name = operation_name
        self.total_steps = total_steps
        self.logs = []
        self.max_logs = 12
        self.current_step = 0
        self.start_time = time.time()

    def add_log(self, message: str, level: str = "INFO"):
        """Agregar log con timestamp"""
        timestamp = time.strftime("%H:%M:%S")

        # Mapeo de levels a emojis
        level_emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✓",
            "WARNING": "⚠️",
            "ERROR": "✗",
            "PROGRESS": "⏳"
        }

        emoji = level_emoji.get(level, "•")
        log_text = f"[dim][{timestamp}][/dim] {emoji} {message}"

        self.logs.append(log_text)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def render_progress_panel(self, current_detail: str = "", time_remaining: str = ""):
        """Renderiza el panel de progress (lado izquierdo)"""
        percentage = (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0

        # Barra de progreso manual (más control)
        bar_length = 30
        filled = int(bar_length * self.current_step / self.total_steps) if self.total_steps > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        # Elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed)}s"

        progress_text = f"""
[bold cyan]⏳ {self.operation_name}[/bold cyan]

[bold white][{bar}][/bold white]
[cyan]{percentage:>6.1f}%[/cyan]

[dim]Current:[/dim] {current_detail}
[dim]Elapsed:[/dim] {elapsed_str}
[dim]ETA:[/dim] {time_remaining or '—'}
"""

        return Panel(
            progress_text.strip(),
            title="[bold white]Progress[/bold white]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )

    def render_logs_panel(self):
        """Renderiza el panel de logs (lado derecho)"""
        logs_text = "\n".join(self.logs) if self.logs else "[dim]Waiting for activity...[/dim]"

        return Panel(
            logs_text,
            title="[bold white]Logs[/bold white]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 1)
        )

    def show(self, current_detail: str = "", time_remaining: str = ""):
        """Mostrar layout actual (progress + logs lado a lado)"""
        console.clear()
        mostrar_banner()

        # Crear layout de dos columnas
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=60),
            Layout(name="right", ratio=40)
        )

        # Left: Progress
        layout["left"].update(self.render_progress_panel(current_detail, time_remaining))

        # Right: Logs
        layout["right"].update(self.render_logs_panel())

        console.print(layout)

    def update(self, step: int, detail: str = "", time_remaining: str = ""):
        """Actualizar progreso y mostrar"""
        self.current_step = min(step, self.total_steps)
        self.show(detail, time_remaining)


def escanear_videos() -> List[Dict[str, str]]:
    """
    Escaneo la carpeta downloads/ para encontrar videos MP4

    Retorno lista de dicts con info de cada video:
    [
        {
            "filename": "video.mp4",
            "path": "downloads/video.mp4",
            "video_id": "video_abc123"  # ID único basado en nombre
        }
    ]
    """
    downloads_dir = Path("downloads")

    if not downloads_dir.exists():
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return []

    # Busco todos los archivos .mp4
    videos = []
    for video_file in downloads_dir.glob("*.mp4"):
        # Genero un ID único para el video (el nombre sin extensión)
        video_id = video_file.stem  # "AI CDMX Live Stream_gjPVlCHU9OM"

        videos.append({
            "filename": video_file.name,
            "path": str(video_file),
            "video_id": video_id
        })

    return videos


def mostrar_videos_disponibles(videos: List[Dict], state_manager) -> Optional[Table]:
    """
    Muestro una tabla con los videos disponibles y su estado

    Retorno la tabla (o None si no hay videos)
    """
    if not videos:
        return None

    # Creo la tabla
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        border_style="cyan"
    )

    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Video Name", style="white")
    table.add_column("Status", style="green")

    # Agrego cada video a la tabla
    for idx, video in enumerate(videos, 1):
        video_id = video['video_id']

        # Obtengo el estado del video
        state = state_manager.get_video_state(video_id)

        if state:
            # Construyo el status basado en el progreso
            status_parts = []
            if state['transcribed']:
                status_parts.append("[green]Transcribed ✓[/green]")
            if state['clips_generated']:
                status_parts.append(f"[green]{len(state['clips'])} clips[/green]")

            if not status_parts:
                status = "[yellow]Downloaded[/yellow]"
            else:
                status = " | ".join(status_parts)
        else:
            status = "[yellow]Downloaded[/yellow]"

        # Nombre corto (trunco si es muy largo)
        display_name = video['filename']
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."

        table.add_row(str(idx), display_name, status)

    return table


def menu_principal(videos: List[Dict], state_manager) -> str:
    """
    Muestro el menú principal y retorno la opción elegida
    """
    # Si hay videos, muestro la tabla
    if videos:
        console.print("[bold]Available Videos:[/bold]\n")
        table = mostrar_videos_disponibles(videos, state_manager)
        if table:
            console.print(table)
            console.print()

    # Creo el menú mejorado
    menu_table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 3)
    )

    menu_table.add_column("", style="bold cyan", width=4)
    menu_table.add_column("Opción", style="bold white", width=25)
    menu_table.add_column("Descripción", style="dim")

    if videos:
        menu_table.add_row("[bold cyan][1][/bold cyan]", "Procesar un video", "Transcribir, clips, copys, exportar")
        menu_table.add_row("[bold cyan][2][/bold cyan]", "Agregar video", "YouTube o descargar desde ~/Downloads")
        menu_table.add_row("[bold cyan][3][/bold cyan]", "Limpiar proyecto", "Liberar espacio y limpiar cache")
        menu_table.add_row("[bold cyan][4][/bold cyan]", "Pipeline completo", "Automatizar todo el flujo")
        menu_table.add_row("[bold red][5][/bold red]", "Salir", "Cerrar CLIPER")
        opciones = ["1", "2", "3", "4", "5"]
    else:
        menu_table.add_row("[bold cyan][1][/bold cyan]", "Agregar video", "YouTube o descargar desde ~/Downloads")
        menu_table.add_row("[bold cyan][2][/bold cyan]", "Limpiar proyecto", "Liberar espacio y limpiar cache")
        menu_table.add_row("[bold red][3][/bold red]", "Salir", "Cerrar CLIPER")
        opciones = ["1", "2", "3"]

    # Nota: El último número siempre es "Salir" en menú principal
    # Esta es la única excepción (no es "Volver" porque es el nivel más alto)

    console.print(Panel(
        menu_table,
        title="[bold cyan]━━ MENÚ PRINCIPAL ━━[/bold cyan]",
        border_style="cyan",
        padding=(1, 1)
    ))
    console.print()

    opcion = Prompt.ask(
        "[bold cyan]Elige una opción[/bold cyan]",
        choices=opciones,
        default=opciones[0]
    )

    return opcion


def opcion_agregar_video(downloader, state_manager):
    """
    Agrega un video al proyecto desde YouTube o carpeta local (~/Downloads/)
    """
    console.clear()
    mostrar_banner()

    console.print(Panel(
        "[bold]Agregar Video[/bold]\nYouTube o importar desde ~/Downloads/",
        border_style="cyan"
    ))
    console.print()

    # Submenú: elegir fuente
    menu_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    menu_table.add_column("Opción", style="bold cyan", width=8)
    menu_table.add_column("Descripción", style="white")

    menu_table.add_row("1", "Descargar desde YouTube")
    menu_table.add_row("2", "Importar desde ~/Downloads/")
    menu_table.add_row("3", "Volver al menú anterior")

    console.print(menu_table)
    console.print()

    opcion = Prompt.ask(
        "[bold cyan]¿De dónde?[/bold cyan]",
        choices=["1", "2", "3"],
        default="3"
    )

    if opcion == "1":
        _agregar_video_youtube(downloader, state_manager)
    elif opcion == "2":
        _agregar_video_local(state_manager)
    # opcion == "3": volver (solo return)


def _agregar_video_youtube(downloader, state_manager):
    """
    Descargo un nuevo video de YouTube
    """
    console.print()

    console.print(Panel(
        "[bold]Descargar de YouTube[/bold]\nProporciona la URL del video",
        border_style="cyan"
    ))
    console.print()

    url = Prompt.ask("[cyan]URL de YouTube[/cyan]").strip()

    if not url:
        console.print("[red]Error: No URL provided[/red]")
        Prompt.ask("\n[dim]Press ENTER to continue[/dim]", default="")
        return

    # Pregunto por el tipo de contenido
    console.print()
    console.print("[bold]Content Type[/bold]")
    console.print("[dim]This helps optimize transcription and clip generation[/dim]\n")

    presets = list_presets()
    presets_table = Table(show_header=False, box=None, padding=(0, 2))
    presets_table.add_column(style="cyan", width=6)
    presets_table.add_column(style="white")
    presets_table.add_column(style="dim")

    preset_keys = list(presets.keys())
    for idx, (key, name) in enumerate(presets.items(), 1):
        description = get_preset_description(key)
        presets_table.add_row(str(idx), name, description)

    # Agregar opción de volver
    volver_option = len(presets) + 1
    presets_table.add_row(str(volver_option), "Volver al menú anterior", "")

    console.print(presets_table)
    console.print()

    content_choice = Prompt.ask(
        "[cyan]Selecciona tipo de contenido[/cyan]",
        choices=[str(i) for i in range(1, volver_option + 1)],
        default="3"  # Livestream es común
    )

    # Si elige volver
    if int(content_choice) == volver_option:
        return

    content_type = preset_keys[int(content_choice) - 1]
    preset = get_preset(content_type)

    console.print(f"\n[green]✓ Seleccionado:[/green] {presets[content_type]}")
    console.print(f"[dim]{preset['use_case']}[/dim]")

    console.print()

    try:
        # Crear progress tracker
        progress = OperationProgress("Downloading video from YouTube", total_steps=100)
        progress.add_log("Initializing YouTube downloader", "INFO")
        progress.update(5, "Fetching video info...")

        progress.add_log("Getting video metadata...", "PROGRESS")
        progress.update(15, "Getting video metadata...")

        progress.add_log("Selecting best quality", "PROGRESS")
        progress.update(25, "Selecting quality...")

        progress.add_log("Starting download", "PROGRESS")
        progress.update(35, "Downloading...")

        path = downloader.download(url, quality="best")

        if path:
            progress.add_log("Download complete", "SUCCESS")
            progress.update(90, "Processing metadata...")

            # Registro el video en el state manager con metadata de contenido
            video_file = Path(path)
            video_id = video_file.stem

            progress.add_log(f"Registering video: {video_file.name}", "PROGRESS")
            progress.update(95, "Registering in state...")

            state_manager.register_video(
                video_id,
                video_file.name,
                content_type=content_type,  # Guardamos el tipo de contenido
                preset=preset  # Y el preset completo
            )

            progress.add_log("Video registered successfully", "SUCCESS")
            progress.update(100, "Complete! ✓")
            progress.show()

            console.print()
            console.print(Panel(
                f"[green]✓ Video descargado exitosamente[/green]\n\n"
                f"Archivo: {video_file.name}\n"
                f"Ubicación: {path}",
                title="[bold green]Éxito[/bold green]",
                border_style="green"
            ))

            # Pregunto si quiere continuar con transcripción
            console.print()
            if Confirm.ask("[cyan]¿Deseas transcribir este video ahora?[/cyan]"):
                # Creo el dict de video para pasarlo a la función
                video_dict = {
                    'filename': video_file.name,
                    'path': path,
                    'video_id': video_id
                }
                opcion_transcribir_video(video_dict, state_manager)
                return  # Retorno para que no pida ENTER dos veces
        else:
            progress.add_log("Download failed - no file returned", "ERROR")
            progress.update(100, "Failed ✗")
            progress.show()

            console.print()
            console.print(Panel(
                "[red]La descarga falló. Verifica los logs arriba.[/red]",
                border_style="red"
            ))

    except KeyboardInterrupt:
        progress.add_log("Download cancelled by user", "WARNING")
        progress.update(100, "Cancelled ✗")
        progress.show()
        console.print("\n[yellow]Descarga cancelada por el usuario[/yellow]")
    except Exception as e:
        progress.add_log(f"Error: {str(e)}", "ERROR")
        progress.update(100, f"Error ✗")
        progress.show()
        console.print(f"\n[red]Error: {e}[/red]")

    # Solo mostrar opción de volver si el usuario no fue ya a transcribir
    # (si fue a transcribir, la función regresa antes de acá)
    console.print()
    Prompt.ask("[dim]Presiona ENTER para volver[/dim]", default="")


def _agregar_video_local(state_manager):
    """
    Importa un video desde ~/Downloads/

    FLUJO:
    1. Detectar archivos .mp4 y .mov en ~/Downloads/
    2. Mostrar lista numerada
    3. Usuario selecciona por número
    4. Copiar a project downloads/
    5. Registrar en state
    """
    console.print()

    importer = LocalVideoImporter()

    # Listar videos disponibles
    available_videos = importer.list_available_videos(limit=15)

    if not available_videos:
        console.print(Panel(
            "[yellow]No hay videos en ~/Downloads/[/yellow]\n\n"
            "Coloca archivos .mp4 o .mov en tu carpeta Downloads",
            border_style="yellow"
        ))
        console.print()
        Prompt.ask("[dim]Presiona ENTER para volver[/dim]", default="")
        return

    # Actualizar para último número = volver
    # (se hace en el menú de selección abajo)

    # Mostrar tabla de videos
    console.print("[bold]Videos disponibles en ~/Downloads/:[/bold]\n")

    videos_table = Table(show_header=False, box=None, padding=(0, 2))
    videos_table.add_column(style="cyan", width=6)
    videos_table.add_column(style="white")
    videos_table.add_column(style="dim", justify="right")

    for idx, video in enumerate(available_videos, 1):
        size_display = f"{video['size_mb']:.0f} MB" if video['size_mb'] < 1024 else f"{video['size_mb'] / 1024:.1f} GB"
        videos_table.add_row(str(idx), video['name'], size_display)

    videos_table.add_row(str(len(available_videos) + 1), "[dim]Cancelar[/dim]", "")

    console.print(videos_table)
    console.print()

    # Usuario elige
    choice = Prompt.ask(
        "[bold cyan]Selecciona video[/bold cyan]",
        choices=[str(i) for i in range(1, len(available_videos) + 2)],
        default=str(len(available_videos) + 1)
    )

    choice_idx = int(choice) - 1

    # Validar selección
    if choice_idx == len(available_videos):
        console.print("[yellow]Cancelado[/yellow]")
        return

    selected_video = available_videos[choice_idx]

    # Importar
    console.print()
    with console.status(f"[cyan]Importando {selected_video['name']}...[/cyan]", spinner="dots"):
        result = importer.import_video(selected_video['path'], state_manager)

    if result:
        video_file = Path(result)
        video_id = video_file.stem

        console.print(Panel(
            f"[green]✓ Video importado exitosamente[/green]\n\n"
            f"Archivo: {video_file.name}\n"
            f"Ubicación: {result}",
            title="[bold green]Éxito[/bold green]",
            border_style="green"
        ))

        # Pregunto si quiere transcribir
        console.print()
        if Confirm.ask("[cyan]¿Deseas transcribir este video ahora?[/cyan]"):
            video_dict = {
                'filename': video_file.name,
                'path': result,
                'video_id': video_id
            }
            opcion_transcribir_video(video_dict, state_manager)
            return
    else:
        console.print(Panel(
            "[red]Error al importar el video[/red]\n\n"
            "Verifica los logs para más detalles",
            border_style="red"
        ))

    console.print()
    Prompt.ask("[dim]Presiona ENTER para volver[/dim]", default="")


def opcion_procesar_video(videos: List[Dict], state_manager):
    """
    Proceso un video existente (transcribir, generar clips, etc.)
    """
    console.clear()
    mostrar_banner()

    console.print("[bold]Selecciona un video para procesar:[/bold]\n")

    # Muestro los videos numerados
    for idx, video in enumerate(videos, 1):
        console.print(f"  {idx}. {video['filename']}")

    console.print()

    # PATRÓN: Último número siempre es "Volver"
    num_videos = len(videos)
    console.print(f"  {num_videos + 1}. Volver al menú anterior")
    console.print()

    # Pido al usuario que elija
    seleccion = Prompt.ask(
        "[cyan]Número de video[/cyan]",
        choices=[str(i) for i in range(1, num_videos + 2)],
        default=str(num_videos + 1)
    )

    # Si selecciona "Volver"
    if int(seleccion) == num_videos + 1:
        return

    video_seleccionado = videos[int(seleccion) - 1]
    video_id = video_seleccionado['video_id']

    # Loop infinito para refrescar el menu después de cada acción
    while True:
        # Obtengo el estado del video (refrescado en cada iteración)
        state = state_manager.get_video_state(video_id)

        # Limpio la pantalla y muestro banner
        console.clear()
        mostrar_banner()

        # Muestro opciones según el estado
        console.print(f"\n[bold]Procesando: {video_seleccionado['filename']}[/bold]\n")

        # Muestro el estado actual
        if state:
            status_parts = []
            if state['transcribed']:
                status_parts.append("[green]✓ Transcrito[/green]")
            if state['clips_generated']:
                num_clips = len(state.get('clips', []))
                status_parts.append(f"[green]✓ {num_clips} clips generados[/green]")
            if state.get('clips_exported', False):
                num_exported = len(state.get('exported_clips', []))
                aspect = state.get('export_aspect_ratio', 'original')
                status_parts.append(f"[green]✓ {num_exported} clips exportados ({aspect})[/green]")

            if status_parts:
                console.print("Estado: " + " | ".join(status_parts))
                console.print()

        # Creo menú de acciones disponibles
        actions_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
        actions_table.add_column("Opción", style="bold cyan", width=8)
        actions_table.add_column("Descripción", style="white")

        actions = []

        if state and state['transcribed']:
            actions.append(("1", "Re-transcribir video"))
            actions.append(("2", "Generar/Regenerar clips"))

            # Si ya tengo clips, ofrezco más opciones
            if state.get('clips_generated', False):
                actions.append(("3", "Generar copys IA (clasificación + subtítulos)"))
                actions.append(("4", "Exportar clips a archivos de video"))

        else:
            actions.append(("1", "Transcribir video"))

        # PATRÓN: Último número siempre es "Volver al menú anterior"
        next_option_num = len(actions) + 1
        actions.append((str(next_option_num), "Volver al menú anterior"))

        for option, desc in actions:
            actions_table.add_row(option, desc)

        console.print(actions_table)
        console.print()

        choices = [opt for opt, _ in actions]
        action = Prompt.ask(
            "[bold cyan]Elige una acción[/bold cyan]",
            choices=choices,
            default=str(next_option_num)  # Default = volver
        )

        # Validar si es "Volver"
        if action == str(next_option_num):
            break  # Salir del loop y volver al menú anterior

        # Ejecuto la acción elegida
        if state and state['transcribed']:
            if action == "1":
                opcion_transcribir_video(video_seleccionado, state_manager)
            elif action == "2":
                opcion_generar_clips(video_seleccionado, state_manager)
            elif action == "3":
                if state['clips_generated']:
                    opcion_generar_copies(video_seleccionado, state_manager)
            elif action == "4":
                if state['clips_generated']:
                    opcion_exportar_clips(video_seleccionado, state_manager)
            # El loop continúa para refrescar el menú
        else:
            if action == "1":
                opcion_transcribir_video(video_seleccionado, state_manager)
            # El loop continúa para refrescar el menú


def opcion_transcribir_video(video: Dict, state_manager):
    """
    Transcribo un video usando WhisperX

    Este es el paso clave que convierte el audio en texto con timestamps.
    Estos timestamps me permiten después detectar dónde cortar los clips.
    """
    console.clear()
    mostrar_banner()

    video_path = video['path']
    video_id = video['video_id']

    # Obtengo el preset si existe
    state = state_manager.get_video_state(video_id)
    preset = state.get('preset', {}) if state else {}
    content_type = state.get('content_type', 'tutorial') if state else 'tutorial'

    # Si no hay preset guardado, cargo el default
    if not preset:
        preset = get_preset(content_type)

    transcription_config = preset.get('transcription', {})
    suggested_model = transcription_config.get('model_size', 'base')

    console.print(Panel(
        f"[bold]Transcribe Video[/bold]\n\n"
        f"Video: {video['filename']}\n"
        f"Content Type: {content_type.title()}\n"
        f"Using: WhisperX (optimized for Apple Silicon)",
        border_style="cyan"
    ))
    console.print()

    # Pregunto por la configuración (con sugerencia del preset)
    console.print("[bold]Transcription Settings:[/bold]")
    console.print(f"[dim]Suggested for {content_type}: {suggested_model}[/dim]\n")

    # Selección de modelo
    model_options = Table(show_header=False, box=None, padding=(0, 2))
    model_options.add_column(style="cyan")
    model_options.add_column(style="white")
    model_options.add_column(style="dim")

    model_options.add_row("1", "tiny", "Fastest - ~1min for 1hr video")
    model_options.add_row("2", "base", "Balanced - ~5min for 1hr video")
    model_options.add_row("3", "small", "Accurate - ~10min for 1hr video")
    model_options.add_row("4", "medium", "Very accurate - ~20min for 1hr video")
    model_options.add_row("5", "Volver al menú anterior", "")

    console.print(model_options)
    console.print()

    # Mapeo de modelo a opción numérica (para el default)
    model_to_option = {
        "tiny": "1",
        "base": "2",
        "small": "3",
        "medium": "4"
    }
    default_option = model_to_option.get(suggested_model, "2")  # Default a "base" (opción 2)

    model_choice = Prompt.ask(
        "[cyan]Tamaño del modelo[/cyan]",
        choices=["1", "2", "3", "4", "5"],
        default=default_option
    )

    # Si elige volver
    if model_choice == "5":
        return

    # Mapeo de opción numérica a modelo
    option_to_model = {
        "1": "tiny",
        "2": "base",
        "3": "small",
        "4": "medium"
    }
    model_size = option_to_model[model_choice]

    # Idioma
    console.print()
    language = Prompt.ask(
        "[cyan]Language (or 'auto' to detect)[/cyan]",
        default="auto"
    )

    # Mapeo de nombres comunes a códigos ISO (WhisperX espera códigos ISO)
    LANGUAGE_MAP = {
        "spanish": "es",
        "español": "es",
        "english": "en",
        "inglés": "en",
        "portuguese": "pt",
        "português": "pt",
        "french": "fr",
        "francés": "fr",
        "german": "de",
        "alemán": "de",
        "italian": "it",
        "italiano": "it",
        "auto": None
    }

    # Normalizar idioma
    lang_lower = language.lower().strip()
    if lang_lower in LANGUAGE_MAP:
        language = LANGUAGE_MAP[lang_lower]
    elif lang_lower == "auto":
        language = None  # WhisperX auto-detecta

    console.print()
    console.print("[yellow]⚠️  Transcription will take several minutes depending on video length[/yellow]")
    console.print("[dim]You can see the progress in the terminal[/dim]\n")

    if not Confirm.ask("[cyan]Start transcription?[/cyan]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    try:
        # Progress tracker para transcripción
        progress = OperationProgress("Transcribing with WhisperX", total_steps=100)
        progress.add_log(f"Video: {video['filename']}", "INFO")
        progress.add_log(f"Model size: {model_size}", "INFO")
        progress.update(5, "Loading model...")

        # Creo el transcriber
        progress.add_log("Initializing Whisper model...", "PROGRESS")
        progress.update(10, "Loading Whisper model...")
        transcriber = Transcriber(model_size=model_size)

        progress.add_log(f"Model loaded: {model_size}", "SUCCESS")
        progress.update(20, "Model loaded")

        # Transcribo
        progress.add_log("Starting transcription...", "PROGRESS")
        progress.update(25, "Transcribing audio...")

        transcript_path = transcriber.transcribe(
            video_path=video_path,
            language=language,
            skip_if_exists=False  # Siempre regenero si el usuario lo pidió
        )

        if transcript_path:
            progress.add_log("Transcription complete", "SUCCESS")
            progress.update(80, "Processing results...")

            # Actualizo el estado
            progress.add_log("Updating state manager...", "PROGRESS")
            progress.update(85, "Saving state...")
            state_manager.mark_transcribed(video_id, transcript_path)

            # Obtengo resumen de la transcripción
            progress.add_log("Generating summary...", "PROGRESS")
            progress.update(90, "Generating summary...")
            summary = transcriber.get_transcript_summary(transcript_path)

            progress.add_log(f"Summary: {summary['num_segments']} segments, {summary['total_words']} words", "SUCCESS")
            progress.update(100, "Complete! ✓")
            progress.show()

            console.print()
            console.print(Panel(
                f"[green]✓ Transcription completed![/green]\n\n"
                f"Language: {summary['language']}\n"
                f"Duration: {summary['total_duration']:.1f} seconds\n"
                f"Segments: {summary['num_segments']}\n"
                f"Words: {summary['total_words']}\n\n"
                f"Saved to: {transcript_path}",
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))

            console.print()
            console.print("[dim]Preview:[/dim]")
            console.print(f"[dim]{summary['first_text']}[/dim]")

        else:
            progress.add_log("Transcription failed - no output", "ERROR")
            progress.update(100, "Failed ✗")
            progress.show()

            console.print()
            console.print(Panel(
                "[red]Transcription failed. Check the logs above.[/red]",
                border_style="red"
            ))

    except KeyboardInterrupt:
        progress.add_log("Transcription cancelled by user", "WARNING")
        progress.update(100, "Cancelled ✗")
        progress.show()
        console.print("\n[yellow]Transcription cancelled by user[/yellow]")
    except Exception as e:
        progress.add_log(f"Error: {str(e)}", "ERROR")
        progress.update(100, "Error ✗")
        progress.show()
        console.print(f"\n[red]Error: {e}[/red]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_generar_clips(video: Dict, state_manager):
    """
    Genero clips automáticamente detectando cambios de tema

    Este es el paso donde ClipsAI analiza la transcripción y detecta
    los mejores puntos de corte para crear clips virales.
    """
    console.clear()
    mostrar_banner()

    video_path = video['path']
    video_id = video['video_id']

    # Verifico que tenga transcripción
    state = state_manager.get_video_state(video_id)

    if not state or not state.get('transcribed'):
        console.print(Panel(
            "[red]Error: This video hasn't been transcribed yet[/red]\n\n"
            "You need to transcribe the video first before generating clips.",
            border_style="red"
        ))
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    transcript_path = state.get('transcript_path') or state.get('transcription_path')

    # Obtengo el preset para clips
    preset = state.get('preset', {})
    content_type = state.get('content_type', 'tutorial')

    if not preset:
        preset = get_preset(content_type)

    clips_config = preset.get('clips', {})
    suggested_min = clips_config.get('min_duration', 30)
    suggested_max = clips_config.get('max_duration', 90)

    console.print(Panel(
        f"[bold]Generate Clips[/bold]\n\n"
        f"Video: {video['filename']}\n"
        f"Content Type: {content_type.title()}\n"
        f"Using: ClipsAI (AI-powered clip detection)",
        border_style="cyan"
    ))
    console.print()

    # Pregunto por la configuración (con sugerencia del preset)
    console.print("[bold]Clip Generation Settings:[/bold]")
    console.print(f"[dim]Suggested for {content_type}: {suggested_min}-{suggested_max}s clips[/dim]\n")

    # Determino qué opción corresponde a la sugerencia
    if suggested_max <= 60:
        suggested_choice = "1"
    elif suggested_max <= 90:
        suggested_choice = "2"
    else:
        suggested_choice = "3"

    # Duración de clips
    duration_options = Table(show_header=False, box=None, padding=(0, 2))
    duration_options.add_column(style="cyan")
    duration_options.add_column(style="white")
    duration_options.add_column(style="dim")

    duration_options.add_row("1", "Short clips", "30-60s (TikTok/Shorts)")
    duration_options.add_row("2", "Medium clips", "30-90s (Reels/Stories)")
    duration_options.add_row("3", "Long clips", "60-180s (YouTube)")
    duration_options.add_row("4", "Custom", f"Use preset: {suggested_min}-{suggested_max}s")
    duration_options.add_row("5", "Volver al menú anterior", "")

    console.print(duration_options)
    console.print()

    duration_choice = Prompt.ask(
        "[cyan]Preset de duración de clips[/cyan]",
        choices=["1", "2", "3", "4", "5"],
        default="4"  # Default usa el preset del content type
    )

    # Si elige volver
    if duration_choice == "5":
        return

    # Mapeo de presets
    duration_presets = {
        "1": (30, 60),   # Short
        "2": (30, 90),   # Medium
        "3": (60, 180),  # Long
        "4": (suggested_min, suggested_max)  # Del content type
        # "5": Volver (manejado arriba)
    }

    min_duration, max_duration = duration_presets[duration_choice]

    # Calculo estimado de clips (basado en la transcripción)
    try:
        import json
        with open(transcript_path, 'r') as f:
            transcript_data = json.load(f)
            segments = transcript_data.get('segments', [])
            if segments:
                total_duration = segments[-1].get('end', 0)
                estimated_clips = int(total_duration / max_duration)

                console.print()
                console.print(f"[dim]Video duration: {total_duration/60:.1f} minutes[/dim]")
                console.print(f"[dim]Estimated clips with {max_duration}s duration: ~{estimated_clips}[/dim]")
    except:
        pass  # Si falla, no es crítico

    # Número de clips
    console.print()
    num_clips = Prompt.ask(
        "[cyan]Maximum number of clips to generate[/cyan]",
        default="100"  # Aumentado para videos largos (livestreams, conferencias)
    )

    try:
        max_clips = int(num_clips)
    except ValueError:
        max_clips = 10

    console.print()
    console.print("[yellow]⚠️  Clip generation uses AI and may take 1-2 minutes[/yellow]")
    console.print("[dim]ClipsAI will analyze the transcript and detect topic changes[/dim]\n")

    if not Confirm.ask("[cyan]Start clip generation?[/cyan]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    try:
        # Progress tracker para clip generation
        progress = OperationProgress("Generating clips with ClipsAI", total_steps=100)
        progress.add_log(f"Video: {video['filename']}", "INFO")
        progress.add_log(f"Duration range: {min_duration}-{max_duration}s", "INFO")
        progress.add_log(f"Max clips: {max_clips}", "INFO")
        progress.update(5, "Initializing...")

        # Creo el generador de clips
        progress.add_log("Initializing ClipsAI engine...", "PROGRESS")
        progress.update(10, "Loading ClipsAI...")

        clips_gen = ClipsGenerator(
            min_clip_duration=min_duration,
            max_clip_duration=max_duration
        )

        progress.add_log("ClipsAI loaded successfully", "SUCCESS")
        progress.update(15, "ClipsAI ready")

        # Genero los clips
        progress.add_log("Analyzing transcript for topic changes...", "PROGRESS")
        progress.update(20, "Analyzing transcript...")

        clips = clips_gen.generate_clips(
            transcript_path=transcript_path,
            min_clips=3,
            max_clips=max_clips
        )

        if clips:
            progress.add_log(f"Detected {len(clips)} clips", "SUCCESS")
            progress.update(60, "Saving metadata...")

            # Guardo la metadata de los clips
            progress.add_log("Saving clips metadata...", "PROGRESS")
            progress.update(70, "Saving metadata...")

            clips_metadata_path = clips_gen.save_clips_metadata(
                clips=clips,
                video_id=video_id
            )

            progress.add_log("Metadata saved", "SUCCESS")
            progress.update(80, "Updating state...")

            # Actualizo el estado
            progress.add_log("Updating state manager...", "PROGRESS")
            progress.update(85, "Updating state...")
            state_manager.mark_clips_generated(video_id, clips, clips_metadata_path)

            progress.add_log("Clip generation complete", "SUCCESS")
            progress.update(100, "Complete! ✓")
            progress.show()

            console.print()
            console.print(Panel(
                f"[green]✓ Clips generated successfully![/green]\n\n"
                f"Number of clips: {len(clips)}\n"
                f"Duration range: {min_duration}s - {max_duration}s\n\n"
                f"Metadata saved to: {clips_metadata_path}",
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))

            # Muestro preview de los clips
            console.print()
            console.print("[bold]Generated Clips:[/bold]\n")

            clips_table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
                border_style="cyan"
            )

            clips_table.add_column("#", style="cyan", width=4)
            clips_table.add_column("Duration", style="white", width=10)
            clips_table.add_column("Time Range", style="dim", width=15)
            clips_table.add_column("Preview", style="white")

            for clip in clips[:10]:  # Muestro máximo 10 en la tabla
                clip_id = clip['clip_id']
                duration = f"{clip['duration']:.1f}s"
                start = clip['start_time']
                end = clip['end_time']
                time_range = f"{int(start//60):02d}:{int(start%60):02d} - {int(end//60):02d}:{int(end%60):02d}"

                # Preview (trunco si es muy largo)
                preview = clip['text_preview']
                if len(preview) > 50:
                    preview = preview[:47] + "..."

                clips_table.add_row(
                    str(clip_id),
                    duration,
                    time_range,
                    preview
                )

            console.print(clips_table)

            if len(clips) > 10:
                console.print(f"\n[dim]... and {len(clips) - 10} more clips[/dim]")

        else:
            progress.add_log("Clip generation failed - no clips detected", "ERROR")
            progress.update(100, "Failed ✗")
            progress.show()

            console.print()
            console.print(Panel(
                "[red]Clip generation failed[/red]\n\n"
                "Possible reasons:\n"
                "• Video too short for specified duration range\n"
                "• No clear topic changes detected\n"
                "• Try adjusting min/max duration settings",
                border_style="red"
            ))

    except KeyboardInterrupt:
        progress.add_log("Clip generation cancelled by user", "WARNING")
        progress.update(100, "Cancelled ✗")
        progress.show()
        console.print("\n[yellow]Clip generation cancelled by user[/yellow]")
    except Exception as e:
        progress.add_log(f"Error: {str(e)}", "ERROR")
        progress.update(100, "Error ✗")
        progress.show()
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check the logs for more details[/dim]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_generar_copies(video: Dict, state_manager):
    """
    Genero copies automáticamente usando LangGraph + Gemini

    Este paso clasifica cada clip automáticamente (viral/educational/storytelling)
    y genera el caption optimizado para cada uno usando AI.
    """
    console.clear()
    mostrar_banner()

    video_id = video['video_id']

    # Verifico que tenga clips generados
    state = state_manager.get_video_state(video_id)

    if not state or not state.get('clips_generated'):
        console.print(Panel(
            "[red]Error: This video doesn't have clips yet[/red]\n\n"
            "You need to generate clips first before creating AI copies.",
            border_style="red"
        ))
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    clips = state.get('clips', [])

    console.print(Panel(
        f"[bold]Generate AI Copies[/bold]\n\n"
        f"Video: {video['filename']}\n"
        f"Clips: {len(clips)}\n\n"
        f"This will:\n"
        f"  1. Auto-classify each clip (viral/educational/storytelling)\n"
        f"  2. Generate optimized captions with hashtags\n"
        f"  3. Save to output/{video_id}/copys/clips_copys.json",
        border_style="cyan"
    ))
    console.print()

    # Selección de modelo
    console.print("[bold]Selección de Modelo:[/bold]\n")

    model_table = Table(show_header=False, box=None, padding=(0, 2))
    model_table.add_column(style="cyan")
    model_table.add_column(style="white")
    model_table.add_column(style="dim")

    model_table.add_row("1", "Gemini 2.5 Flash", "Tu modelo (recomendado)")
    model_table.add_row("2", "Gemini 1.5 Pro", "Alternativa")
    model_table.add_row("3", "Volver al menú anterior", "")

    console.print(model_table)
    console.print()

    model_choice = Prompt.ask(
        "[cyan]Elige modelo[/cyan]",
        choices=["1", "2", "3"],
        default="1"
    )

    # Si elige volver
    if model_choice == "3":
        return

    # Intentar diferentes nombres de modelo para Gemini 2.5 Flash
    model_map = {
        "1": "gemini-2.5-flash",  # Nombre probable
        "2": "gemini-1.5-pro"
    }

    model = model_map[model_choice]

    console.print()
    console.print("[yellow]⚠️  This will use Gemini API (requires GOOGLE_API_KEY)[/yellow]")
    console.print(f"[dim]Estimated time: ~1-2 minutes for {len(clips)} clips[/dim]\n")

    if not Confirm.ask("[cyan]Start AI copy generation?[/cyan]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    try:
        # Progress tracker para copy generation
        progress = OperationProgress("Generating AI copies with LangGraph + Gemini", total_steps=100)
        progress.add_log(f"Video: {video['filename']}", "INFO")
        progress.add_log(f"Model: {model}", "INFO")
        progress.update(5, "Initializing LangGraph pipeline...")

        if logger:
            logger.info(f"Starting copy generation for video_id={video_id}, model={model}")

        progress.add_log("Loading clips from metadata...", "PROGRESS")
        progress.update(10, "Loading clips...")

        # Generar copies
        progress.add_log("Starting copy generation pipeline...", "PROGRESS")
        progress.update(15, "Generating copies...")

        result = generate_copys_for_video(
            video_id=video_id,
            model=model
        )

        # Integrar logs del resultado en el progress
        if result.get('logs'):
            for log_msg in result['logs']:
                # Determinar el nivel basado en el contenido del log
                if '❌' in log_msg or 'Error' in log_msg:
                    progress.add_log(log_msg, "ERROR")
                elif '⚠️' in log_msg:
                    progress.add_log(log_msg, "WARNING")
                elif '✅' in log_msg:
                    progress.add_log(log_msg, "SUCCESS")
                else:
                    progress.add_log(log_msg, "PROGRESS")

        console.print()

        if result['success']:
            # Determinar si es éxito total o parcial
            total_generated = result['metrics']['total_copies']
            total_classified = result['metrics'].get('total_classified', total_generated)
            is_partial = total_generated < total_classified

            progress.add_log(f"Copy generation complete: {total_generated}/{total_classified}", "SUCCESS")
            progress.update(85, "Finalizing...")

            if is_partial:
                progress.add_log("Partial success - some copies failed validation", "WARNING")
                title_text = "[bold yellow]Partial Success[/bold yellow]"
                border_color = "yellow"
                status_line = f"[yellow]⚠️  Generación parcial: {total_generated}/{total_classified} copies[/yellow]"
            else:
                title_text = "[bold green]Success[/bold green]"
                border_color = "green"
                status_line = f"[green]✓ AI copies generated successfully![/green]"

            progress.update(100, "Complete! ✓")
            progress.show()

            console.print()
            console.print(Panel(
                f"{status_line}\n\n"
                f"Total copies: {total_generated}\n"
                f"Engagement score: {result['metrics']['average_engagement']}/10\n"
                f"Viral potential: {result['metrics']['average_viral_potential']}/10\n\n"
                f"Distribution:\n"
                f"  • Viral: {result['metrics']['distribution']['viral']} clips\n"
                f"  • Educational: {result['metrics']['distribution']['educational']} clips\n"
                f"  • Storytelling: {result['metrics']['distribution']['storytelling']} clips\n\n"
                f"Saved to: {result['output_file']}",
                title=title_text,
                border_style=border_color
            ))

        else:
            progress.add_log(f"Copy generation failed: {result.get('error', 'Unknown error')}", "ERROR")
            progress.update(100, "Failed ✗")
            progress.show()

            console.print()
            console.print(Panel(
                f"[red]Copy generation failed[/red]\n\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"Check the logs above for details.\n\n"
                f"Possible causes:\n"
                f"• GOOGLE_API_KEY not set\n"
                f"• Model not available with your API key\n"
                f"• API quota exceeded\n"
                f"• Network issues",
                border_style="red"
            ))

    except KeyboardInterrupt:
        progress.add_log("Copy generation cancelled by user", "WARNING")
        progress.update(100, "Cancelled ✗")
        progress.show()
        console.print("\n[yellow]Copy generation cancelled by user[/yellow]")
        if logger:
            logger.warning("Copy generation cancelled by user")
    except Exception as e:
        progress.add_log(f"Error: {str(e)}", "ERROR")
        progress.update(100, "Error ✗")
        progress.show()
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check that GOOGLE_API_KEY is set in your environment[/dim]")
        if logger:
            logger.exception(f"Exception during copy generation: {e}")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_exportar_clips(video: Dict, state_manager):
    """
    Exporto los clips a archivos de video físicos usando ffmpeg

    Este es el paso final donde convirtiendo los timestamps en videos reales.
    Puedo exportar con diferentes aspect ratios para redes sociales.

    Si existen clasificaciones (clips_copys.json), pregunta si organizar por estilo.
    """
    console.clear()
    mostrar_banner()

    video_path = video['path']
    video_id = video['video_id']

    # Verifico que tenga clips generados
    state = state_manager.get_video_state(video_id)

    if not state or not state.get('clips_generated'):
        console.print(Panel(
            "[red]Error: This video doesn't have clips yet[/red]\n\n"
            "You need to generate clips first before exporting.",
            border_style="red"
        ))
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    clips = state.get('clips', [])

    if not clips:
        console.print(Panel(
            "[red]Error: No clips found[/red]",
            border_style="red"
        ))
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    # Verificar si existen clasificaciones
    copys_file = Path("output") / video_id / "copys" / "clips_copys.json"
    has_classifications = copys_file.exists()
    clip_styles = None
    organize_by_style = False

    if has_classifications:
        # Cargar clasificaciones
        try:
            import json
            with open(copys_file, 'r', encoding='utf-8') as f:
                copys_data = json.load(f)

            # Extraer clasificaciones de clips
            classifications = copys_data.get('classification_metadata', {}).get('classifications', [])

            if classifications:
                clip_styles = {c['clip_id']: c['style'] for c in classifications}

                # Mostrar distribución
                distribution = copys_data.get('classification_metadata', {}).get('distribution', {})
                viral_count = distribution.get('viral', 0)
                educational_count = distribution.get('educational', 0)
                storytelling_count = distribution.get('storytelling', 0)

                console.print(Panel(
                    f"[green]✓ Clips already classified![/green]\n\n"
                    f"Distribution:\n"
                    f"  • Viral: {viral_count} clips\n"
                    f"  • Educational: {educational_count} clips\n"
                    f"  • Storytelling: {storytelling_count} clips",
                    title="[bold green]Auto-Classification Detected[/bold green]",
                    border_style="green"
                ))
                console.print()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load classifications: {e}[/yellow]\n")

    console.print(Panel(
        f"[bold]Export Clips to Video Files[/bold]\n\n"
        f"Video: {video['filename']}\n"
        f"Clips to export: {len(clips)}\n"
        f"Using: ffmpeg (optimized cutting)",
        border_style="cyan"
    ))
    console.print()

    # Pregunto por aspect ratio
    console.print("[bold]Export Settings:[/bold]\n")

    aspect_options = Table(show_header=False, box=None, padding=(0, 2))
    aspect_options.add_column(style="cyan")
    aspect_options.add_column(style="white")
    aspect_options.add_column(style="dim")

    aspect_options.add_row("1", "Original", "Mantener relación original (usualmente 16:9)")
    aspect_options.add_row("2", "Vertical (9:16)", "Para TikTok, Reels, Shorts")
    aspect_options.add_row("3", "Cuadrado (1:1)", "Para posts de Instagram")
    aspect_options.add_row("4", "Volver al menú anterior", "")

    console.print(aspect_options)
    console.print()

    aspect_choice = Prompt.ask(
        "[cyan]Relación de aspecto[/cyan]",
        choices=["1", "2", "3", "4"],
        default="2"  # Default: vertical para redes sociales
    )

    # Si elige volver
    if aspect_choice == "4":
        return

    # Mapeo de aspect ratios
    aspect_map = {
        "1": None,      # Original
        "2": "9:16",    # Vertical
        "3": "1:1"      # Square
    }

    aspect_ratio = aspect_map[aspect_choice]

    # PASO 3: Face tracking configuration
    enable_face_tracking = False
    face_tracking_strategy = "keep_in_frame"
    face_tracking_sample_rate = 3

    if aspect_ratio == "9:16":  # Solo relevante para videos verticales
        console.print()
        enable_face_tracking = Confirm.ask(
            "[cyan]Enable intelligent face tracking for dynamic reframing?[/cyan]",
            default=False
        )

        if enable_face_tracking:
            console.print("\n[bold]Face Tracking Strategy:[/bold]")
            console.print("  [cyan]1.[/cyan] keep_in_frame (recommended) - Minimal movement, professional look")
            console.print("  [cyan]2.[/cyan] centered - Always center on face (can be jittery)")
            console.print("  [cyan]3.[/cyan] Volver al menú anterior")

            style_choice = Prompt.ask(
                "\n[cyan]Choice[/cyan]",
                choices=["1", "2", "3"],
                default="1"
            )

            # Si elige volver
            if style_choice == "3":
                return

            face_tracking_strategy = "keep_in_frame" if style_choice == "1" else "centered"

            # Advanced settings (opcional)
            console.print()
            advanced = Confirm.ask(
                "[dim]Configure advanced settings (frame sampling)?[/dim]",
                default=False
            )

            if advanced:
                sample_rate_input = Prompt.ask(
                    "Frame sample rate (process every N frames)",
                    default="3"
                )
                try:
                    face_tracking_sample_rate = int(sample_rate_input)
                except ValueError:
                    console.print("[yellow]Invalid input, using default: 3[/yellow]")
                    face_tracking_sample_rate = 3

            # Visual confirmation
            console.print()
            console.print("[green]✓[/green] Face tracking enabled:")
            console.print(f"  Strategy: [cyan]{face_tracking_strategy}[/cyan]")
            console.print(f"  Sample rate: every [cyan]{face_tracking_sample_rate}[/cyan] frame(s)")

    # --- Branding (Logo Only) ---
    console.print()
    add_logo = Confirm.ask("[cyan]Add logo overlay to clips?[/cyan]", default=False)

    logo_path = "assets/logo.png"
    logo_position = "top-left"  # Changed default from top-right to top-left
    logo_scale = 0.07  # Changed default from 0.1 to 0.07 (medium)

    if add_logo:
        console.print(f"[green]✓[/green] Logo overlay enabled.")

        advanced_branding = Confirm.ask(
            "\n[dim]Configure logo position & size?[/dim]",
            default=False
        )
        if advanced_branding:
            logo_path = Prompt.ask("Path to logo file", default=logo_path)

            console.print("\n[bold]Logo Position:[/bold]\n")
            position_table = Table(show_header=False, box=None, padding=(0, 2))
            position_table.add_column(style="cyan")
            position_table.add_column(style="white")
            position_table.add_column(style="dim")

            position_table.add_row("1", "Top Left (default)", "Adjusted for TikTok")
            position_table.add_row("2", "Top Right", "Classic corner")
            position_table.add_row("3", "Bottom Left", "Footer position")
            position_table.add_row("4", "Bottom Right", "Footer corner")
            position_table.add_row("5", "Volver al menú anterior", "")

            console.print(position_table)
            console.print()

            position_choice = Prompt.ask(
                "[cyan]Logo position[/cyan]",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )

            if position_choice == "5":
                logo_position = "top-left"  # Reset to default if cancelled
            else:
                position_map = {
                    "1": "top-left",
                    "2": "top-right",
                    "3": "bottom-left",
                    "4": "bottom-right"
                }
                logo_position = position_map[position_choice]

            # Logo size selection (predefined options)
            console.print("\n[bold]Logo Size:[/bold]\n")
            size_table = Table(show_header=False, box=None, padding=(0, 2))
            size_table.add_column(style="cyan")
            size_table.add_column(style="white")
            size_table.add_column(style="dim")

            size_table.add_row("1", "Medium", "7% of frame height (default)")
            size_table.add_row("2", "Large", "10% of frame height")

            console.print(size_table)
            console.print()

            size_choice = Prompt.ask(
                "[cyan]Logo size[/cyan]",
                choices=["1", "2"],
                default="1"
            )

            size_map = {
                "1": 0.07,
                "2": 0.10
            }
            logo_scale = size_map[size_choice]

    # Pregunto si quiere subtítulos
    console.print()
    add_subtitles = Confirm.ask(
        "[cyan]Add burned-in subtitles?[/cyan]",
        default=True
    )

    subtitle_style = "bottom"  # Default position
    if add_subtitles:
        console.print()
        console.print("[bold]Subtitle Position (8px yellow):[/bold]\n")

        style_options = Table(show_header=False, box=None, padding=(0, 2))
        style_options.add_column(style="cyan")
        style_options.add_column(style="white")
        style_options.add_column(style="dim")

        style_options.add_row("1", "Bottom", "Waist level (default)")
        style_options.add_row("2", "Middle", "Center of frame")
        style_options.add_row("3", "Very High", "Top of frame")
        style_options.add_row("4", "Volver al menú anterior", "")

        console.print(style_options)
        console.print()

        style_choice = Prompt.ask(
            "[cyan]Subtitle position[/cyan]",
            choices=["1", "2", "3", "4"],
            default="1"
        )

        # Si elige volver
        if style_choice == "4":
            return

        style_map = {
            "1": "bottom",
            "2": "middle",
            "3": "very_high"
        }

        subtitle_style = style_map[style_choice]

    # Pregunto si quiere organizar por estilo (si hay clasificaciones)
    if clip_styles:
        console.print()
        organize_by_style = Confirm.ask(
            "[cyan]Organize clips by style in separate folders? (viral/educational/storytelling)[/cyan]",
            default=True
        )

        if organize_by_style:
            console.print("[green]✓ Clips will be organized in subfolders by style[/green]")
        else:
            console.print("[dim]All clips will be exported to the same folder[/dim]")

    # Pregunto si quiere exportar todos o solo algunos
    console.print()
    export_all = Confirm.ask(
        f"[cyan]Export all {len(clips)} clips?[/cyan]",
        default=True
    )

    clips_to_export = clips

    if not export_all:
        console.print()
        max_clips = Prompt.ask(
            "[cyan]How many clips to export (from the beginning)?[/cyan]",
            default="10"
        )
        try:
            clips_to_export = clips[:int(max_clips)]
        except ValueError:
            clips_to_export = clips[:10]

    # === REVIEW CONFIGURACIÓN ANTES DE EXPORTAR ===
    aspect_ratio_display = {None: "Original", "9:16": "Vertical (9:16)", "1:1": "Cuadrado (1:1)"}

    while True:
        console.clear()
        mostrar_banner()

        console.print(Panel(
            "[bold cyan]📋 EXPORT CONFIGURATION REVIEW[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        # Resumen de configuraciones
        config_table = Table(show_header=False, box=None, padding=(0, 2))
        config_table.add_column(style="dim", width=20)
        config_table.add_column(style="white")

        config_table.add_row("Aspect ratio:", aspect_ratio_display.get(aspect_ratio, "Unknown"))

        if aspect_ratio == "9:16":
            face_tracking_status = f"✓ {face_tracking_strategy}" if enable_face_tracking else "Deshabilitado"
            config_table.add_row("Face tracking:", face_tracking_status)

        logo_status = "✓ " + logo_position if add_logo else "Deshabilitado"
        config_table.add_row("Logo:", logo_status)

        subtitle_status = f"✓ {subtitle_style}" if add_subtitles else "Deshabilitado"
        config_table.add_row("Subtitles:", subtitle_status)

        config_table.add_row("Clips to export:", f"{len(clips_to_export)} de {len(clips)}")

        console.print(config_table)
        console.print()

        # Opciones: cambiar, exportar, o cancelar
        console.print("[bold]¿Qué deseas hacer?[/bold]\n")
        console.print("  [cyan][Y][/cyan] Cambiar algo")
        console.print("  [cyan][N][/cyan] Proceder al export")
        console.print("  [cyan][C][/cyan] Cancelar y volver al menú anterior\n")

        action = Prompt.ask(
            "[cyan]Opción[/cyan]",
            choices=["y", "n", "c"],
            default="n"
        ).lower()

        if action == "c":
            # Cancelar sin guardar - volver al menú anterior
            console.print("[yellow]Export cancelled - volviendo al menú anterior[/yellow]")
            Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
            return

        elif action == "n":
            # Proceder al export
            console.print()
            console.print(f"[yellow]⚠️  About to export {len(clips_to_export)} clips[/yellow]")
            console.print(f"[dim]This may take a few minutes depending on video length[/dim]")
            console.print()

            if not Confirm.ask("[cyan]Continue with export?[/cyan]", default=True):
                console.print("[yellow]Export cancelled[/yellow]")
                Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
                return

            break  # Salir del loop de review y proceder a exportar

        # Si action == "y", continúa al menú de edición (abajo)
        if action != "y":
            continue  # Volver al inicio del while si presionó algo que no sea "y"

        # Menú de edición de configuraciones
        console.print()
        console.print("[bold]¿Qué cambiar?[/bold]\n")

        edit_options = Table(show_header=False, box=None, padding=(0, 2))
        edit_options.add_column(style="cyan")
        edit_options.add_column(style="white")

        edit_options.add_row("1", "Aspect ratio")

        if aspect_ratio == "9:16":
            edit_options.add_row("2", "Face tracking")
            edit_options.add_row("3", "Logo")
            edit_options.add_row("4", "Subtitles")
            edit_options.add_row("5", "Clips a exportar")
            edit_options.add_row("6", "Volver a resumen")
            edit_choices = ["1", "2", "3", "4", "5", "6"]
        else:
            edit_options.add_row("2", "Logo")
            edit_options.add_row("3", "Subtitles")
            edit_options.add_row("4", "Clips a exportar")
            edit_options.add_row("5", "Volver a resumen")
            edit_choices = ["1", "2", "3", "4", "5"]

        console.print(edit_options)
        console.print()

        edit_choice = Prompt.ask(
            "[cyan]Opción[/cyan]",
            choices=edit_choices,
            default=edit_choices[-1]
        )

        # Procesar ediciones
        if edit_choice == "1":
            # Editar aspect ratio
            console.clear()
            mostrar_banner()
            console.print(f"\n[bold]Procesando: {video['filename']}[/bold]\n")
            console.print("[bold]Cambiar Aspect Ratio:[/bold]\n")

            aspect_options_edit = Table(show_header=False, box=None, padding=(0, 2))
            aspect_options_edit.add_column(style="cyan")
            aspect_options_edit.add_column(style="white")
            aspect_options_edit.add_column(style="dim")

            aspect_options_edit.add_row("1", "Original", "16:9 o según fuente")
            aspect_options_edit.add_row("2", "Vertical", "9:16 (TikTok, Reels, Shorts)")
            aspect_options_edit.add_row("3", "Cuadrado", "1:1 (Instagram)")

            console.print(aspect_options_edit)
            console.print()

            new_aspect = Prompt.ask(
                "[cyan]Selecciona[/cyan]",
                choices=["1", "2", "3"],
                default="2" if aspect_ratio == "9:16" else ("1" if aspect_ratio is None else "3")
            )

            aspect_map_edit = {"1": None, "2": "9:16", "3": "1:1"}
            aspect_ratio = aspect_map_edit[new_aspect]

            # Reset face tracking si cambió a no-vertical
            if aspect_ratio != "9:16":
                enable_face_tracking = False

        elif edit_choice == "2" and aspect_ratio == "9:16":
            # Editar face tracking
            console.clear()
            mostrar_banner()
            console.print(f"\n[bold]Procesando: {video['filename']}[/bold]\n")
            console.print("[bold]Face Tracking Settings:[/bold]\n")
            console.print("  [cyan]1.[/cyan] Habilitar (keep_in_frame)")
            console.print("  [cyan]2.[/cyan] Habilitar (centered)")
            console.print("  [cyan]3.[/cyan] Deshabilitar\n")

            ft_choice = Prompt.ask(
                "[cyan]Selecciona[/cyan]",
                choices=["1", "2", "3"],
                default="1" if enable_face_tracking else "3"
            )

            if ft_choice == "1":
                enable_face_tracking = True
                face_tracking_strategy = "keep_in_frame"
            elif ft_choice == "2":
                enable_face_tracking = True
                face_tracking_strategy = "centered"
            else:
                enable_face_tracking = False

        elif (edit_choice == "2" and aspect_ratio != "9:16") or (edit_choice == "3" and aspect_ratio == "9:16"):
            # Editar logo
            console.clear()
            mostrar_banner()
            console.print(f"\n[bold]Procesando: {video['filename']}[/bold]\n")
            console.print("[bold]Logo Settings:[/bold]\n")

            add_logo = Confirm.ask("[cyan]Add logo overlay?[/cyan]", default=add_logo)

            if add_logo:
                console.print("\n[bold]Logo Position:[/bold]\n")
                logo_pos_table = Table(show_header=False, box=None, padding=(0, 2))
                logo_pos_table.add_column(style="cyan")
                logo_pos_table.add_column(style="white")

                logo_pos_table.add_row("1", "Top Left (default, TikTok adjusted)")
                logo_pos_table.add_row("2", "Top Right")
                logo_pos_table.add_row("3", "Bottom Left")
                logo_pos_table.add_row("4", "Bottom Right")

                console.print(logo_pos_table)
                console.print()

                pos_choice = Prompt.ask(
                    "[cyan]Logo position[/cyan]",
                    choices=["1", "2", "3", "4"],
                    default="1"
                )

                logo_map = {"1": "top-left", "2": "top-right", "3": "bottom-left", "4": "bottom-right"}
                logo_position = logo_map[pos_choice]

                console.print("\n[bold]Logo Size:[/bold]\n")
                logo_size_table = Table(show_header=False, box=None, padding=(0, 2))
                logo_size_table.add_column(style="cyan")
                logo_size_table.add_column(style="white")

                logo_size_table.add_row("1", "Medium (7%)")
                logo_size_table.add_row("2", "Large (10%)")

                console.print(logo_size_table)
                console.print()

                size_choice = Prompt.ask(
                    "[cyan]Logo size[/cyan]",
                    choices=["1", "2"],
                    default="1"
                )

                logo_scale_map = {"1": 0.07, "2": 0.10}
                logo_scale = logo_scale_map[size_choice]

        elif (edit_choice == "3" and aspect_ratio != "9:16") or (edit_choice == "4" and aspect_ratio == "9:16"):
            # Editar subtítulos
            console.clear()
            mostrar_banner()
            console.print(f"\n[bold]Procesando: {video['filename']}[/bold]\n")
            console.print("[bold]Subtitle Settings:[/bold]\n")

            add_subtitles = Confirm.ask("[cyan]Add subtitles?[/cyan]", default=add_subtitles)

            if add_subtitles:
                console.print()
                style_options_edit = Table(show_header=False, box=None, padding=(0, 2))
                style_options_edit.add_column(style="cyan")
                style_options_edit.add_column(style="white")

                styles = [("Bottom", "8px yellow, waist level"),
                         ("Middle", "8px yellow, center frame"),
                         ("Very High", "8px yellow, top frame")]
                for i, (name, desc) in enumerate(styles, 1):
                    style_options_edit.add_row(str(i), f"{name} - {desc}")

                console.print(style_options_edit)
                console.print()

                style_choice_edit = Prompt.ask(
                    "[cyan]Subtitle position[/cyan]",
                    choices=["1", "2", "3"],
                    default="1"
                )

                style_map_edit = {
                    "1": "bottom", "2": "middle", "3": "very_high"
                }
                subtitle_style = style_map_edit[style_choice_edit]

        else:  # Volver a resumen (última opción)
            continue  # Volver al inicio del while loop

    try:
        console.print()

        # Creo el exporter
        exporter = VideoExporter(output_dir="output")

        # Obtengo el path de la transcripción para los subtítulos
        transcript_path = state.get('transcript_path') or state.get('transcription_path')

        # Progress tracker para export
        progress = OperationProgress("Exporting clips to video files", total_steps=100)
        progress.add_log(f"Video: {video['filename']}", "INFO")
        progress.add_log(f"Clips to export: {len(clips_to_export)}", "INFO")
        progress.add_log(f"Aspect ratio: {aspect_ratio if aspect_ratio else 'Original'}", "INFO")
        progress.add_log(f"Face tracking: {'Enabled' if enable_face_tracking else 'Disabled'}", "INFO")
        progress.add_log(f"Subtitles: {'Enabled' if add_subtitles else 'Disabled'}", "INFO")
        progress.update(5, "Initializing exporter...")

        # Mensaje informativo sobre el proceso de export
        if enable_face_tracking:
            progress.add_log("Face tracking enabled - processing will take longer", "WARNING")
            progress.update(10, "Loading face detection model...")
        else:
            progress.add_log("Using static crop (no face tracking)", "INFO")
            progress.update(10, "Preparing FFmpeg...")

        progress.add_log("Starting clip export...", "PROGRESS")
        progress.update(15, "Exporting clips...")

        # Exporto los clips
        exported_paths = exporter.export_clips(
            video_path=video_path,
            clips=clips_to_export,
            aspect_ratio=aspect_ratio,
            video_name=video_id,
            add_subtitles=add_subtitles,
            transcript_path=transcript_path,
            subtitle_style=subtitle_style,
            organize_by_style=organize_by_style,
            clip_styles=clip_styles,
            # PASO 3: Face tracking parameters
            enable_face_tracking=enable_face_tracking,
            face_tracking_strategy=face_tracking_strategy,
            face_tracking_sample_rate=face_tracking_sample_rate,
            # PASO 4: Branding parameters
            add_logo=add_logo,
            logo_path=logo_path,
            logo_position=logo_position,
            logo_scale=logo_scale
        )

        if exported_paths:
            progress.add_log(f"All {len(exported_paths)} clips exported successfully", "SUCCESS")
            progress.update(85, "Updating state...")

            # Obtengo la carpeta donde se guardaron (todos están en la misma)
            output_folder = Path(exported_paths[0]).parent

            progress.add_log(f"Location: {output_folder}", "INFO")
            progress.update(90, "Finalizing...")

            # Marco como exportado en el state manager
            progress.add_log("Marking as exported in state manager...", "PROGRESS")
            progress.update(95, "Saving state...")

            state_manager.mark_clips_exported(
                video_id,
                exported_paths,
                aspect_ratio=aspect_ratio
            )

            progress.add_log("Export complete", "SUCCESS")
            progress.update(100, "Complete! ✓")
            progress.show()

            console.print()
            console.print(Panel(
                f"[green]✓ Export completed![/green]\n\n"
                f"Clips exported: {len(exported_paths)}\n"
                f"Location: {output_folder}/\n"
                f"Aspect ratio: {aspect_ratio if aspect_ratio else 'Original'}",
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))

            # Muestro algunos nombres de archivo
            console.print()
            console.print("[dim]Sample clips:[/dim]")
            for path in exported_paths[:5]:
                filename = Path(path).name
                console.print(f"[dim]  • {filename}[/dim]")

            if len(exported_paths) > 5:
                console.print(f"[dim]  ... and {len(exported_paths) - 5} more[/dim]")

        else:
            progress.add_log("Export failed - no clips exported", "ERROR")
            progress.update(100, "Failed ✗")
            progress.show()

            console.print()
            console.print(Panel(
                "[red]Export failed[/red]\n\n"
                "Check the logs for details about what went wrong.",
                border_style="red"
            ))

    except KeyboardInterrupt:
        progress.add_log("Export cancelled by user", "WARNING")
        progress.update(100, "Cancelled ✗")
        progress.show()
        console.print("\n[yellow]Export cancelled by user[/yellow]")
    except Exception as e:
        progress.add_log(f"Error: {str(e)}", "ERROR")
        progress.update(100, "Error ✗")
        progress.show()
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check the logs for more details[/dim]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_cleanup_project():
    """
    Flujo interactivo para limpiar artifacts del proyecto

    DECISIÓN: 2 opciones principales claras
    - Opción 1: Keep downloads + transcripts (re-procesamiento rápido)
    - Opción 2: Fresh start (eliminar TODO)
    RAZÓN: Operación destructiva - prevenir eliminaciones accidentales
    """
    console.clear()
    mostrar_banner()

    console.print(Panel(
        "[bold]Limpiar Datos del Proyecto[/bold]\nGestiona y elimina artifacts del proyecto",
        border_style="cyan"
    ))
    console.print()

    cleanup_manager = CleanupManager()
    state_manager = get_state_manager()
    state = state_manager.get_all_videos()

    if not state:
        console.print("[yellow]Sin datos para limpiar (estado vacío)[/yellow]")
        console.print()
        Prompt.ask("[dim]Presiona ENTER para volver al menú[/dim]", default="")
        return

    # Mostrar resumen de espacio usado
    cleanup_manager.display_space_summary()
    console.print()
    cleanup_manager.display_cleanable_artifacts()
    console.print()

    # Opciones de cleanup simplificadas
    menu_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    menu_table.add_column("Opción", style="bold cyan", width=8)
    menu_table.add_column("Descripción", style="white")

    menu_table.add_row("1", "Mantener descargas & transcripciones (re-procesar)")
    menu_table.add_row("   ", "  └─ Elimina: metadata clips, outputs, logs, caché")
    menu_table.add_row("2", "Inicio limpio (eliminar todo)")
    menu_table.add_row("   ", "  └─ Elimina: TODOS los artifacts")
    menu_table.add_row("3", "Volver al menú anterior")

    console.print(Panel(menu_table, title="[bold]Opciones de Limpieza[/bold]", border_style="cyan"))
    console.print()

    choice = Prompt.ask(
        "[bold cyan]Elige opción de limpieza[/bold cyan]",
        choices=["1", "2", "3"],
        default="3"
    )

    if choice == "1":
        cleanup_keep_downloads_and_transcripts(cleanup_manager, state)
        # Mostrar opción de volver después de completar
        console.print()
        Prompt.ask("[dim]Presiona ENTER para volver[/dim]", default="")
    elif choice == "2":
        cleanup_entire_project(cleanup_manager)
        # Mostrar opción de volver después de completar
        console.print()
        Prompt.ask("[dim]Presiona ENTER para volver[/dim]", default="")
    # choice == "3": volver directamente (sin confirmación)


def cleanup_keep_downloads_and_transcripts(cleanup_manager: CleanupManager, state: dict):
    """
    Opción 1: Mantiene descargas + transcripts, elimina TODO lo demás

    CASO DE USO:
    - Ya tienes videos descargados y transcritos
    - Quieres cambiar prompts/modelos y re-procesar
    - No quieres re-descargar videos (ahorra tiempo y ancho de banda)

    ELIMINA:
    - Clips metadata (clips_metadata.json)
    - Exported clips (output/)
    - Old logs (> 7 días)
    - Cache (__pycache__, lock files, .DS_Store)

    MANTIENE:
    - Downloaded videos (downloads/)
    - Transcripts (temp/*_transcript.json)
    """
    console.print()

    # Calcular tamaño que se liberará
    totals = cleanup_manager.get_total_sizes()
    will_delete = (
        totals['total_clips_metadata'] +
        totals['total_output']
    )
    will_keep = (
        totals['total_downloads'] +
        totals['total_transcripts']
    )

    def format_size(size_bytes):
        mb = size_bytes / 1024 / 1024
        if mb < 0.1:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{mb:.1f} MB"

    console.print("[bold yellow]⚠️  Modo Re-procesar: Mantener Descargas & Transcripciones[/bold yellow]\n")

    console.print("[bold]Se MANTIENE:[/bold]")
    console.print(f"  ✓ Videos descargados: {format_size(totals['total_downloads'])}")
    console.print(f"  ✓ Transcripciones: {format_size(totals['total_transcripts'])}")
    console.print(f"  ✓ Total: {format_size(will_keep)}\n")

    console.print("[bold red]Se ELIMINA:[/bold red]")
    console.print(f"  ✗ Metadata clips: {format_size(totals['total_clips_metadata'])}")
    console.print(f"  ✗ Clips exportados: {format_size(totals['total_output'])}")
    console.print(f"  ✗ Logs antiguos (> 7 días)")
    console.print(f"  ✗ Cache y residuales")
    console.print(f"  ✗ Total a eliminar: {format_size(will_delete)}\n")

    if not Confirm.ask("¿Continuar con limpieza de re-procesamiento?", default=False):
        console.print("[yellow]Limpieza cancelada[/yellow]")
        return

    console.print("\n[bold]Limpiando...[/bold]")
    results = cleanup_manager.delete_all_except_downloads_and_transcripts()

    success_count = sum(1 for r in results.values() if r)
    console.print(f"\n[green]✓ Limpieza de re-procesamiento completada[/green]")
    console.print(f"[green]Espacio liberado: {format_size(will_delete)}[/green]")
    console.print(f"[dim]Ahora puedes re-procesar clips con diferentes configuraciones[/dim]")


def cleanup_specific_video(cleanup_manager: CleanupManager, state: dict):
    """Cleanup de un video específico con selección granular"""
    console.print()

    # Listar videos disponibles
    video_keys = list(state.keys())

    console.print("[bold]Available videos:[/bold]\n")

    videos_table = Table(show_header=False, box=None, padding=(0, 2))
    videos_table.add_column(style="cyan", width=6)
    videos_table.add_column(style="white")

    for idx, video_key in enumerate(video_keys, 1):
        # Nombre corto del video
        video_name = video_key[:50] + "..." if len(video_key) > 50 else video_key
        videos_table.add_row(str(idx), video_name)

    videos_table.add_row(str(len(video_keys) + 1), "[dim]Cancel[/dim]")

    console.print(videos_table)
    console.print()

    video_idx = Prompt.ask(
        "[cyan]Select video to clean[/cyan]",
        choices=[str(i) for i in range(1, len(video_keys) + 2)],
        default=str(len(video_keys) + 1)
    )

    if int(video_idx) == len(video_keys) + 1:
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    selected_video_key = video_keys[int(video_idx) - 1]

    # Mostrar artifacts de ese video
    artifacts = cleanup_manager.get_video_artifacts(selected_video_key)

    console.print(f"\n[bold]Artifacts for '{selected_video_key[:50]}':[/bold]\n")

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
    console.print()
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    menu_table.add_column(style="cyan", width=6)
    menu_table.add_column(style="white")

    menu_table.add_row("1", "All artifacts")
    menu_table.add_row("2", "Select specific artifacts")
    menu_table.add_row("3", "Cancel")

    console.print(menu_table)
    console.print()

    granular_choice = Prompt.ask(
        "[cyan]What to clean?[/cyan]",
        choices=["1", "2", "3"],
        default="3"
    )

    if granular_choice == "3":
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    if granular_choice == "1":
        to_delete = artifact_options
    else:
        # Selección manual
        console.print()
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
    console.print(f"\n[bold red]This will DELETE {len(to_delete)} items ({total_mb:.2f} MB)[/bold red]")
    for t in to_delete:
        console.print(f"  - {t}")
    console.print()

    if not Confirm.ask("Continue?", default=False):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    # Ejecutar cleanup
    console.print("\n[bold]Cleaning...[/bold]")
    results = cleanup_manager.delete_video_artifacts(selected_video_key, to_delete)

    # Mostrar resultados
    success_count = sum(1 for r in results.values() if r)
    console.print(f"\n[green]Deleted {success_count}/{len(to_delete)} items ({total_mb:.2f} MB freed)[/green]")


def cleanup_outputs_only(cleanup_manager: CleanupManager, state: dict):
    """Elimina SOLO los outputs exportados (conserva transcripts)"""
    console.print()

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

    console.print("[bold]This will delete ALL exported clips:[/bold]")
    console.print(f"  - Videos: {len(state)} videos")
    console.print(f"  - Clips: {total_clips} clips")
    console.print(f"  - Size: {size_mb:.2f} MB")
    console.print("\n[dim]Transcripts and source videos will be preserved[/dim]\n")

    if not Confirm.ask("Continue?", default=False):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    # Eliminar outputs de cada video
    console.print("\n[bold]Cleaning outputs...[/bold]")
    deleted_count = 0
    for video_key in state.keys():
        results = cleanup_manager.delete_video_artifacts(video_key, ['output'])
        if results.get('output'):
            deleted_count += 1

    console.print(f"\n[green]Deleted outputs from {deleted_count} videos ({size_mb:.2f} MB freed)[/green]")


def cleanup_entire_project(cleanup_manager: CleanupManager):
    """
    Opción 2: Fresh start - elimina TODO el proyecto

    CASO DE USO:
    - Clean slate - empezar de cero
    - Troubleshooting - eliminar todo y reintentar
    - Cambio de proyecto - limpiar completamente antes de nuevo proyecto
    """
    console.print()

    totals = cleanup_manager.get_total_sizes()

    def format_size(size_bytes):
        mb = size_bytes / 1024 / 1024
        if mb < 0.1:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{mb:.1f} MB"

    console.print("[bold red]🔥 INICIO LIMPIO: Eliminar Todo[/bold red]\n")

    console.print("[bold red]Esto eliminará TODOS los datos del proyecto:[/bold red]")
    console.print(f"  ✗ Videos descargados: {format_size(totals['total_downloads'])}")
    console.print(f"  ✗ Transcripciones: {format_size(totals['total_transcripts'])}")
    console.print(f"  ✗ Metadata de clips: {format_size(totals['total_clips_metadata'])}")
    console.print(f"  ✗ Clips exportados: {format_size(totals['total_output'])}")
    console.print(f"  ✗ Estado del proyecto (json)")
    console.print(f"  ✗ Cache y logs\n")

    console.print(f"[bold red]Espacio a liberar: {format_size(totals['total_all'])}[/bold red]\n")

    # Confirmación simple - Y/N con default N
    if not Confirm.ask("[bold red]¿Estás seguro?[/bold red]", default=False):
        console.print("[yellow]Limpieza cancelada[/yellow]")
        return

    console.print("\n[bold]Limpiando proyecto completo...[/bold]")

    results = cleanup_manager.delete_all_project_data()

    if all(results.values()):
        console.print("\n[green]✓ Proyecto limpiado exitosamente[/green]")
        console.print(f"[green]Espacio liberado: {format_size(totals['total_all'])}[/green]")
        console.print("[dim]Inicio limpio. Ejecuta CLIPER para comenzar.[/dim]")
    else:
        console.print("\n[yellow]Algunos elementos no pudieron eliminarse[/yellow]")
        for item, success in results.items():
            status = "✓" if success else "✗"
            console.print(f"  {status} {item}")


def main():
    """
    Función principal - loop del programa
    """
    global logger
    import logging
    import warnings

    mostrar_banner()

    # Inicializo logging a archivo (silenciosamente - solo archivo, sin consola)
    log_filename = f"logs/cliper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_logger(name="cliper", log_file=log_filename, console_output=False)

    # Logs de inicialización solo a archivo (sin mostrar en consola)
    logger.info("="*80)
    logger.info("CLIPER started")
    logger.info("="*80)

    # Inicializo componentes
    console.print("[cyan]Initializing CLIPER...[/cyan]\n")

    try:
        downloader = YoutubeDownloader()
        state_manager = get_state_manager()
        logger.info("System initialized successfully")
        logger.info("Downloader ready")
        console.print("[green]✓ System ready[/green]\n")
    except Exception as e:
        console.print(Panel(
            f"[red]Initialization error: {e}[/red]",
            border_style="red"
        ))
        sys.exit(1)

    # Escaneo videos existentes
    console.print("[cyan]Scanning downloads/ folder...[/cyan]")
    videos = escanear_videos()

    # Registro videos que no están en el state
    for video in videos:
        if not state_manager.get_video_state(video['video_id']):
            state_manager.register_video(video['video_id'], video['filename'])

    if videos:
        console.print(f"[green]Found {len(videos)} video(s)[/green]\n")
    else:
        console.print("[yellow]No videos found[/yellow]\n")

    # Loop principal
    while True:
        opcion = menu_principal(videos, state_manager)

        # Mapeo de opciones (depende de si hay videos)
        if videos:
            if opcion == "1":
                opcion_procesar_video(videos, state_manager)
            elif opcion == "2":
                opcion_agregar_video(downloader, state_manager)
                videos = escanear_videos()  # Reescaneo
            elif opcion == "3":
                opcion_cleanup_project()
                videos = escanear_videos()  # Reescaneo (pueden haberse eliminado)
            elif opcion == "4":
                console.print("\n[yellow]Full Pipeline coming soon![/yellow]")
                Prompt.ask("\n[dim]Press ENTER to continue[/dim]", default="")
            elif opcion == "5":
                break
        else:
            if opcion == "1":
                opcion_agregar_video(downloader, state_manager)
                videos = escanear_videos()  # Reescaneo
            elif opcion == "2":
                opcion_cleanup_project()
                videos = escanear_videos()  # Reescaneo
            elif opcion == "3":
                break

        console.clear()
        mostrar_banner()

    # Despedida
    console.clear()
    mostrar_banner()

    goodbye = Text()
    goodbye.append("\nThank you for using CLIPER!\n", style="bold green")
    goodbye.append("Keep creating amazing content\n", style="dim")
    goodbye.justify = "center"

    console.print(Panel(
        goodbye,
        title="[bold]Goodbye![/bold]",
        border_style="cyan"
    ))
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Program interrupted. Goodbye![/yellow]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        console.print("[dim]Check the logs for more details[/dim]\n")
        sys.exit(1)
