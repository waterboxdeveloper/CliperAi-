#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del CleanupManager mejorado
Verifica que limpie TODOS los archivos residuales sin dejar caché

Uso: python tests/test_cleaner_exhaustive.py
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleanup_manager import CleanupManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_residual_files():
    """Crear archivos residuales para verificar que se limpien"""
    temp_dir = PROJECT_ROOT / "temp"
    output_dir = PROJECT_ROOT / "output"
    src_dir = PROJECT_ROOT / "src"
    tests_dir = PROJECT_ROOT / "tests"

    residuals = {
        'lock_files': [],
        'temp_mp4': [],
        'pycache': [],
        'ds_store': []
    }

    # 1. Crear archivos .lock
    lock_file = temp_dir / ".lock"
    lock_file.write_text("test lock")
    residuals['lock_files'].append(lock_file)

    # 2. Crear temp_*.mp4 residuales
    if output_dir.exists():
        for i in range(2):
            temp_mp4 = output_dir / f"temp_residual_{i}.mp4"
            temp_mp4.write_text("dummy mp4 residual")
            residuals['temp_mp4'].append(temp_mp4)

    # 3. Crear __pycache__ ficticio SOLO en src/ y tests/ (donde el cleaner lo busca)
    for subdir in [src_dir, tests_dir]:
        pycache = subdir / "__pycache__"
        pycache.mkdir(exist_ok=True)
        (pycache / "test.pyc").write_text("test")
        residuals['pycache'].append(pycache)

    # 4. Crear .DS_Store SOLO en output/ (donde el cleaner lo busca)
    if output_dir.exists():
        ds_store = output_dir / ".DS_Store"
        ds_store.write_text("test ds_store")
        residuals['ds_store'].append(ds_store)

    return residuals


def verify_cleanup(residuals):
    """Verificar que los archivos residuales fueron eliminados"""
    results = {
        'all_cleaned': True,
        'details': {}
    }

    for residual_type, files in residuals.items():
        cleaned = []
        remaining = []

        for file_path in files:
            if not file_path.exists():
                cleaned.append(str(file_path))
            else:
                remaining.append(str(file_path))

        results['details'][residual_type] = {
            'cleaned': len(cleaned),
            'remaining': len(remaining),
            'remaining_files': remaining
        }

        if remaining:
            results['all_cleaned'] = False

    return results


def main():
    print("\n" + "="*70)
    print("TEST: CleanupManager - Exhaustive Cleanup Verification")
    print("="*70 + "\n")

    # 1. Crear archivos residuales
    print("Step 1: Creating residual files...")
    residuals = create_residual_files()

    total_residuals = sum(len(v) for v in residuals.values())
    print(f"✓ Created {total_residuals} residual files")

    # 2. Mostrar archivos creados
    print("\nFiles created:")
    for residual_type, files in residuals.items():
        for file_path in files:
            if file_path.exists():
                print(f"  - {residual_type}: {file_path.relative_to(PROJECT_ROOT)}")

    # 3. Ejecutar cleanup
    print("\nStep 2: Running CleanupManager.delete_all_project_data()...")
    manager = CleanupManager()
    results = manager.delete_all_project_data(dry_run=False)

    print(f"\nCleanup results:")
    for dir_name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {dir_name}")

    # 4. Verificar limpieza
    print("\nStep 3: Verifying cleanup...")
    verification = verify_cleanup(residuals)

    print("\nVerification results:")
    for residual_type, details in verification['details'].items():
        print(f"\n  {residual_type}:")
        print(f"    - Cleaned: {details['cleaned']}")
        print(f"    - Remaining: {details['remaining']}")
        if details['remaining_files']:
            for remaining_file in details['remaining_files']:
                print(f"      ⚠️  {remaining_file}")

    # 5. Resultado final
    print("\n" + "="*70)
    if verification['all_cleaned']:
        print("✓ SUCCESS: All residual files were cleaned")
        print("="*70 + "\n")
        return True
    else:
        print("✗ FAILURE: Some residual files remain")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
