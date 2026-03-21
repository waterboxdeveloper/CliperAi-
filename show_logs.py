#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mostrar los logs más recientes de CLIPER
"""

import sys
from pathlib import Path
from datetime import datetime

def main():
    logs_dir = Path("logs")

    if not logs_dir.exists():
        print("Error: logs/ folder does not exist")
        return

    # Obtener todos los archivos .log
    log_files = sorted(logs_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        print("No log files found in logs/")
        return

    # Mostrar los 3 más recientes
    print(f"\n📋 Most recent log files:\n")
    for i, log_file in enumerate(log_files[:3], 1):
        size = log_file.stat().st_size
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"  {i}. {log_file.name} ({size} bytes) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "="*80)

    # Mostrar el contenido del más reciente
    latest_log = log_files[0]
    print(f"\n📄 Content of {latest_log.name}:\n")

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    main()
