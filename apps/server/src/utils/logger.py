import os
import logging
import logging.config
import traceback
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger as _logger
import sys

try:
    from pynvml import (
        nvmlInit,
    )

    nvmlInit()
    GPU_ENABLED = True
except Exception:
    GPU_ENABLED = False


def deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne récursivement deux dictionnaires
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value

    return result


def load_logging_config(config_path: str = "../../config/logging.yaml", environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Charge la configuration de logging depuis un fichier YAML

    Args:
        config_path: Chemin vers le fichier de configuration
        environment: Environnement spécifique (development, production, testing)

    Returns:
        Configuration de logging
    """
    # Calcul du chemin absolu depuis la position du fichier logger.py
    config_file = Path(__file__).parent / config_path

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e} - {traceback.format_exc()}")
        raise

    # Applique la configuration spécifique à l'environnement si fournie
    if environment and environment in config.get("environments", {}):
        env_config = config["environments"][environment]
        # Supprime la clé environments de la config de base pour éviter les conflits
        base_config = {k: v for k, v in config.items() if k != "environments"}
        # Merge profond de la configuration d'environnement
        config = deep_merge_dict(base_config, env_config)
    else:
        # Supprime la clé environments si pas d'environnement spécifique
        config = {k: v for k, v in config.items() if k != "environments"}

    return config


def setup_logger(name: str = "abrege", config_path: str = "../../config/logging.yaml") -> logging.Logger:
    """
    Configure et retourne un logger basé sur la configuration YAML

    Args:
        name: Nom du logger
        config_path: Chemin vers le fichier de configuration

    Returns:
        Logger configuré
    """
    # Détermine l'environnement depuis les variables d'environnement
    environment = os.getenv("ENVIRONMENT", "development")
    log_level = logging.DEBUG if environment == "development" else logging.INFO
    _logger.remove()  # Supprime les handlers par défaut de loguru
    _logger.add(sys.stdout, level=log_level, format="{message} {extra}")
    return _logger.bind(service=name)  # ty:ignore[invalid-return-type]


# Initialise le logger principal
service_name = os.getenv("SERVICE_NAME", "abrege")
logger_abrege = setup_logger(service_name)
