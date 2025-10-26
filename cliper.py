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

# Rich para interfaz profesional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

# Mis módulos
try:
    from src.downloader import YoutubeDownloader
    from src.transcriber import Transcriber
    from src.clips_generator import ClipsGenerator
    from src.video_exporter import VideoExporter
    from src.utils import get_state_manager
    from config.content_presets import get_preset, list_presets, get_preset_description
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Ejecuta desde la raíz del proyecto: uv run cliper.py")
    sys.exit(1)

# Console de Rich
console = Console()


def mostrar_banner():
    """
    Banner principal de CLIPER
    """
    console.clear()

    logo = Text()
    logo.append("CLIPER", style="bold cyan")
    logo.append(" | Video Clipper\n", style="white")
    logo.append("Transform long videos into viral clips", style="dim")
    logo.justify = "center"

    footer = Text()
    footer.append("Developed by ", style="dim")
    footer.append("opino.tech", style="bold magenta")
    footer.append(" | Powered by ", style="dim")
    footer.append("AI", style="bold green")
    footer.append(" | ", style="dim")
    footer.append("CDMX", style="bold yellow")

    panel = Panel(
        logo,
        title="[bold white]Welcome[/bold white]",
        subtitle=footer,
        border_style="cyan",
        box=box.DOUBLE
    )

    console.print(panel)
    console.print()


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

    # Creo el menú
    menu_table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2)
    )

    menu_table.add_column("Option", style="bold cyan", width=8)
    menu_table.add_column("Description", style="white")

    if videos:
        menu_table.add_row("1", "Process a video")
        menu_table.add_row("2", "Download new video")
        menu_table.add_row("3", "Full Pipeline (auto)")
        menu_table.add_row("4", "Exit")
        opciones = ["1", "2", "3", "4"]
    else:
        menu_table.add_row("1", "Download new video")
        menu_table.add_row("2", "Exit")
        opciones = ["1", "2"]

    console.print(Panel(menu_table, title="[bold]Main Menu[/bold]", border_style="cyan"))
    console.print()

    opcion = Prompt.ask(
        "[bold cyan]Choose an option[/bold cyan]",
        choices=opciones,
        default=opciones[0]
    )

    return opcion


def opcion_descargar_video(downloader, state_manager):
    """
    Descargo un nuevo video de YouTube
    """
    console.clear()
    mostrar_banner()

    console.print(Panel(
        "[bold]Download New Video[/bold]\nProvide a YouTube URL to download",
        border_style="cyan"
    ))
    console.print()

    url = Prompt.ask("[cyan]YouTube URL[/cyan]").strip()

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

    console.print(presets_table)
    console.print()

    content_choice = Prompt.ask(
        "[cyan]Select content type[/cyan]",
        choices=[str(i) for i in range(1, len(presets) + 1)],
        default="3"  # Livestream es común
    )

    content_type = preset_keys[int(content_choice) - 1]
    preset = get_preset(content_type)

    console.print(f"\n[green]✓ Selected:[/green] {presets[content_type]}")
    console.print(f"[dim]{preset['use_case']}[/dim]")

    console.print()

    try:
        with console.status("[cyan]Downloading video...[/cyan]", spinner="dots"):
            path = downloader.download(url, quality="best")

        if path:
            # Registro el video en el state manager con metadata de contenido
            video_file = Path(path)
            video_id = video_file.stem

            state_manager.register_video(
                video_id,
                video_file.name,
                content_type=content_type,  # Guardamos el tipo de contenido
                preset=preset  # Y el preset completo
            )

            console.print(Panel(
                f"[green]✓ Video downloaded successfully[/green]\n\n"
                f"File: {video_file.name}\n"
                f"Location: {path}",
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))

            # Pregunto si quiere continuar con transcripción
            console.print()
            if Confirm.ask("[cyan]Would you like to transcribe this video now?[/cyan]"):
                # Creo el dict de video para pasarlo a la función
                video_dict = {
                    'filename': video_file.name,
                    'path': path,
                    'video_id': video_id
                }
                opcion_transcribir_video(video_dict, state_manager)
                return  # Retorno para que no pida ENTER dos veces
        else:
            console.print(Panel(
                "[red]Download failed. Check the logs above.[/red]",
                border_style="red"
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Download cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_procesar_video(videos: List[Dict], state_manager):
    """
    Proceso un video existente (transcribir, generar clips, etc.)
    """
    console.clear()
    mostrar_banner()

    console.print("[bold]Select a video to process:[/bold]\n")

    # Muestro los videos numerados
    for idx, video in enumerate(videos, 1):
        console.print(f"  {idx}. {video['filename']}")

    console.print()

    # Pido al usuario que elija
    seleccion = Prompt.ask(
        "[cyan]Video number[/cyan]",
        choices=[str(i) for i in range(1, len(videos) + 1)]
    )

    video_seleccionado = videos[int(seleccion) - 1]
    video_id = video_seleccionado['video_id']

    # Obtengo el estado del video
    state = state_manager.get_video_state(video_id)

    # Muestro opciones según el estado
    console.print(f"\n[bold]Processing: {video_seleccionado['filename']}[/bold]\n")

    # Muestro el estado actual
    if state:
        status_parts = []
        if state['transcribed']:
            status_parts.append("[green]✓ Transcribed[/green]")
        if state['clips_generated']:
            num_clips = len(state.get('clips', []))
            status_parts.append(f"[green]✓ {num_clips} clips generated[/green]")
        if state.get('clips_exported', False):
            num_exported = len(state.get('exported_clips', []))
            aspect = state.get('export_aspect_ratio', 'original')
            status_parts.append(f"[green]✓ {num_exported} clips exported ({aspect})[/green]")

        if status_parts:
            console.print("Status: " + " | ".join(status_parts))
            console.print()

    # Creo menú de acciones disponibles
    actions_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
    actions_table.add_column("Option", style="bold cyan", width=8)
    actions_table.add_column("Description", style="white")

    actions = []

    if state and state['transcribed']:
        actions.append(("1", "Re-transcribe video"))
        actions.append(("2", "Generate/Regenerate clips"))

        # Si ya tengo clips, ofrezco exportarlos
        if state.get('clips_generated', False):
            actions.append(("3", "Export clips to video files"))
            actions.append(("4", "Back to menu"))
        else:
            actions.append(("3", "Back to menu"))
    else:
        actions.append(("1", "Transcribe video"))
        actions.append(("2", "Back to menu"))

    for option, desc in actions:
        actions_table.add_row(option, desc)

    console.print(actions_table)
    console.print()

    choices = [opt for opt, _ in actions]
    action = Prompt.ask(
        "[bold cyan]Choose an action[/bold cyan]",
        choices=choices,
        default=choices[0]
    )

    # Ejecuto la acción elegida
    if state and state['transcribed']:
        if action == "1":
            opcion_transcribir_video(video_seleccionado, state_manager)
        elif action == "2":
            opcion_generar_clips(video_seleccionado, state_manager)
        elif action == "3":
            if state['clips_generated']:
                opcion_exportar_clips(video_seleccionado, state_manager)
            else:
                return
        elif action == "4":
            return
    else:
        if action == "1":
            opcion_transcribir_video(video_seleccionado, state_manager)
        elif action == "2":
            return


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

    model_options.add_row("tiny", "Fastest", "~1min for 1hr video")
    model_options.add_row("base", "Balanced", "~5min for 1hr video")
    model_options.add_row("small", "Accurate", "~10min for 1hr video")
    model_options.add_row("medium", "Very accurate", "~20min for 1hr video")

    console.print(model_options)
    console.print()

    model_size = Prompt.ask(
        "[cyan]Model size[/cyan]",
        choices=["tiny", "base", "small", "medium"],
        default=suggested_model  # Usa el modelo sugerido del preset
    )

    # Idioma
    console.print()
    language = Prompt.ask(
        "[cyan]Language (or 'auto' to detect)[/cyan]",
        default="auto"
    )

    if language.lower() == "auto":
        language = None  # WhisperX auto-detecta

    console.print()
    console.print("[yellow]⚠️  Transcription will take several minutes depending on video length[/yellow]")
    console.print("[dim]You can see the progress in the terminal[/dim]\n")

    if not Confirm.ask("[cyan]Start transcription?[/cyan]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    try:
        # Creo el transcriber
        console.print("\n[cyan]Loading Whisper model...[/cyan]")
        transcriber = Transcriber(model_size=model_size)

        # Transcribo
        console.print(f"[cyan]Transcribing {video['filename']}...[/cyan]\n")

        transcript_path = transcriber.transcribe(
            video_path=video_path,
            language=language,
            skip_if_exists=False  # Siempre regenero si el usuario lo pidió
        )

        if transcript_path:
            # Actualizo el estado
            state_manager.mark_transcribed(video_id, transcript_path)

            # Obtengo resumen de la transcripción
            summary = transcriber.get_transcript_summary(transcript_path)

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
            console.print(Panel(
                "[red]Transcription failed. Check the logs above.[/red]",
                border_style="red"
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Transcription cancelled by user[/yellow]")
    except Exception as e:
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

    console.print(duration_options)
    console.print()

    duration_choice = Prompt.ask(
        "[cyan]Clip duration preset[/cyan]",
        choices=["1", "2", "3", "4"],
        default="4"  # Default usa el preset del content type
    )

    # Mapeo de presets
    duration_presets = {
        "1": (30, 60),   # Short
        "2": (30, 90),   # Medium
        "3": (60, 180),  # Long
        "4": (suggested_min, suggested_max)  # Del content type
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
        # Creo el generador de clips
        console.print("\n[cyan]Initializing ClipsAI...[/cyan]")
        clips_gen = ClipsGenerator(
            min_clip_duration=min_duration,
            max_clip_duration=max_duration
        )

        # Genero los clips
        console.print(f"[cyan]Analyzing transcript and detecting clips...[/cyan]\n")

        clips = clips_gen.generate_clips(
            transcript_path=transcript_path,
            min_clips=3,
            max_clips=max_clips
        )

        if clips:
            # Guardo la metadata de los clips
            clips_metadata_path = clips_gen.save_clips_metadata(
                clips=clips,
                video_id=video_id
            )

            # Actualizo el estado
            state_manager.mark_clips_generated(video_id, clips, clips_metadata_path)

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
            console.print(Panel(
                "[red]Clip generation failed[/red]\n\n"
                "Possible reasons:\n"
                "• Video too short for specified duration range\n"
                "• No clear topic changes detected\n"
                "• Try adjusting min/max duration settings",
                border_style="red"
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Clip generation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check the logs for more details[/dim]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def opcion_exportar_clips(video: Dict, state_manager):
    """
    Exporto los clips a archivos de video físicos usando ffmpeg

    Este es el paso final donde convirtiendo los timestamps en videos reales.
    Puedo exportar con diferentes aspect ratios para redes sociales.
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

    aspect_options.add_row("1", "Original", "Keep video aspect ratio (usually 16:9)")
    aspect_options.add_row("2", "Vertical (9:16)", "For TikTok, Reels, Shorts")
    aspect_options.add_row("3", "Square (1:1)", "For Instagram posts")

    console.print(aspect_options)
    console.print()

    aspect_choice = Prompt.ask(
        "[cyan]Aspect ratio[/cyan]",
        choices=["1", "2", "3"],
        default="2"  # Default: vertical para redes sociales
    )

    # Mapeo de aspect ratios
    aspect_map = {
        "1": None,      # Original
        "2": "9:16",    # Vertical
        "3": "1:1"      # Square
    }

    aspect_ratio = aspect_map[aspect_choice]

    # Pregunto si quiere subtítulos
    console.print()
    add_subtitles = Confirm.ask(
        "[cyan]Add burned-in subtitles (English)?[/cyan]",
        default=True
    )

    subtitle_style = "default"
    if add_subtitles:
        console.print()
        console.print("[bold]Subtitle Style:[/bold]\n")

        style_options = Table(show_header=False, box=None, padding=(0, 2))
        style_options.add_column(style="cyan")
        style_options.add_column(style="white")
        style_options.add_column(style="dim")

        style_options.add_row("1", "Default (18px)", "White text, medium size")
        style_options.add_row("2", "Bold (22px)", "Bold white text")
        style_options.add_row("3", "Yellow (20px)", "Yellow text (classic)")
        style_options.add_row("4", "TikTok (20px)", "Centered top")
        style_options.add_row("5", "Small (10px)", "Very small, positioned higher")
        style_options.add_row("6", "Tiny (8px)", "Extra tiny, positioned higher")

        console.print(style_options)
        console.print()

        style_choice = Prompt.ask(
            "[cyan]Subtitle style[/cyan]",
            choices=["1", "2", "3", "4", "5", "6"],
            default="5"  # Default a Small ahora
        )

        style_map = {
            "1": "default",
            "2": "bold",
            "3": "yellow",
            "4": "tiktok",
            "5": "small",
            "6": "tiny"
        }

        subtitle_style = style_map[style_choice]

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

    # Confirmo antes de exportar
    console.print()
    console.print(f"[yellow]⚠️  About to export {len(clips_to_export)} clips[/yellow]")
    console.print(f"[dim]This may take a few minutes depending on video length[/dim]")
    console.print()

    if not Confirm.ask("[cyan]Continue with export?[/cyan]", default=True):
        console.print("[yellow]Export cancelled[/yellow]")
        Prompt.ask("\n[dim]Press ENTER to return[/dim]", default="")
        return

    try:
        console.print()

        # Creo el exporter
        exporter = VideoExporter(output_dir="output")

        # Obtengo el path de la transcripción para los subtítulos
        transcript_path = state.get('transcript_path') or state.get('transcription_path')

        # Exporto los clips
        exported_paths = exporter.export_clips(
            video_path=video_path,
            clips=clips_to_export,
            aspect_ratio=aspect_ratio,
            video_name=video_id,
            add_subtitles=add_subtitles,
            transcript_path=transcript_path,
            subtitle_style=subtitle_style
        )

        if exported_paths:
            # Obtengo la carpeta donde se guardaron (todos están en la misma)
            output_folder = Path(exported_paths[0]).parent

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

            # Marco como exportado en el state manager
            state_manager.mark_clips_exported(
                video_id,
                exported_paths,
                aspect_ratio=aspect_ratio
            )

        else:
            console.print(Panel(
                "[red]Export failed[/red]\n\n"
                "Check the logs for details about what went wrong.",
                border_style="red"
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Export cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Check the logs for more details[/dim]")

    console.print()
    Prompt.ask("[dim]Press ENTER to return to menu[/dim]", default="")


def main():
    """
    Función principal - loop del programa
    """
    mostrar_banner()

    # Inicializo componentes
    console.print("[cyan]Initializing CLIPER...[/cyan]\n")

    try:
        downloader = YoutubeDownloader()
        state_manager = get_state_manager()
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
                opcion_descargar_video(downloader, state_manager)
                videos = escanear_videos()  # Reescaneo
            elif opcion == "3":
                console.print("\n[yellow]Full Pipeline coming soon![/yellow]")
                Prompt.ask("\n[dim]Press ENTER to continue[/dim]", default="")
            elif opcion == "4":
                break
        else:
            if opcion == "1":
                opcion_descargar_video(downloader, state_manager)
                videos = escanear_videos()  # Reescaneo
            elif opcion == "2":
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
