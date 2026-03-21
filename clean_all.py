#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLIPER - Clean All Artifacts Script
Borra TODOS los artifacts: downloads, transcripts, clips, outputs, cache, state.

Usage:
  uv run clean_all.py          (interactive, pide confirmación)
  uv run clean_all.py --force  (no-interactive, borra sin preguntar)
"""

import sys
from src.cleanup_manager import CleanupManager
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# Verificar si fue llamado con --force
force_mode = "--force" in sys.argv

# Banner
msg = Text("🗑️  NUCLEAR CLEANUP - Fresh Start", style="bold red")
msg.justify = "center"
console.print(Panel(msg, border_style="red"))

cleaner = CleanupManager()

console.print("\n[bold]This will delete:[/bold]")
console.print("  • [cyan]downloads/[/cyan]          (videos descargados)")
console.print("  • [cyan]temp/[/cyan]               (transcripts + clips JSON)")
console.print("  • [cyan]output/[/cyan]             (clips exportados)")
console.print("  • [cyan]project_state.json[/cyan]  (historial de procesamiento)")
console.print("  • [yellow]Cache & residuals[/yellow]   (pycache, lock files, temp mp4s)")

# Modo interactivo o force
if force_mode:
    console.print("\n[yellow][--force mode] Proceeding without confirmation...[/yellow]\n")
    confirm = "yes"
else:
    confirm = input("\n⚠️  Continue? (type 'yes' to confirm, or use --force to skip): ")

if confirm.lower() == "yes":
    console.print("\n[bold yellow]Processing...[/bold yellow]\n")
    results = cleaner.delete_all_project_data(dry_run=False)

    console.print("\n[bold green]✅ Cleanup Complete:[/bold green]")
    for key, success in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status} {key}")

    console.print("\n[bold cyan]Project is now clean. Ready for fresh start![/bold cyan]\n")
else:
    console.print("\n[yellow]Cleanup cancelled.[/yellow]\n")
