# -*- coding: utf-8 -*-
"""
Modulo de logging para Cliper.
Proporciona logging con formato consistente.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "cliper",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura y retorna un logger con formato personalizado.

    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta opcional para guardar logs en archivo

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formato del log
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Logger por defecto para el proyecto
default_logger = setup_logger()


def get_logger(name: str = "cliper") -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.

    Wrapper conveniente para setup_logger que usa valores por defecto.

    Args:
        name: Nombre del logger (generalmente __name__ del módulo)

    Returns:
        Logger configurado
    """
    return setup_logger(name)
