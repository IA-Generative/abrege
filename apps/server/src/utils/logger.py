import os
import socket
import logging
import logging.config
import psutil
import traceback
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from pythonjsonlogger import jsonlogger

try:
    from pynvml import (
        nvmlInit,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetUtilizationRates,
        nvmlDeviceGetPowerUsage,
        nvmlDeviceGetTemperature,
        NVML_TEMPERATURE_GPU,
    )

    nvmlInit()
    GPU_ENABLED = True
except Exception:
    GPU_ENABLED = False


class ECSJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        # ECS base fields
        log_record["@timestamp"] = datetime.now().isoformat() + "Z"
        log_record["log.level"] = record.levelname.lower()
        log_record["message"] = record.getMessage()
        log_record["log.logger"] = record.name
        log_record["log.origin.file.name"] = record.pathname
        log_record["log.origin.line"] = record.lineno
        log_record["log.origin.function"] = record.funcName
        log_record["process.pid"] = record.process
        log_record["process.thread.name"] = record.threadName
        log_record["user.name"] = psutil.Process().username()
        log_record["host.name"] = socket.gethostname()

        # Kubernetes fields via Downward API
        log_record["kubernetes.pod.name"] = os.getenv("POD_NAME")
        log_record["kubernetes.namespace"] = os.getenv("POD_NAMESPACE")
        log_record["kubernetes.node.name"] = os.getenv("NODE_NAME")

        # Resource usage
        p = psutil.Process()
        log_record["resource.cpu.percent"] = psutil.cpu_percent(interval=None)
        log_record["resource.memory.rss"] = p.memory_info().rss
        log_record["resource.memory.vms"] = p.memory_info().vms
        log_record["resource.memory.percent"] = p.memory_percent()

        # Temperature (if available)
        try:
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                log_record["resource.temp.cpu"] = temps["coretemp"][0].current
        except Exception:
            pass

        # GPU info
        if GPU_ENABLED:
            try:
                handle = nvmlDeviceGetHandleByIndex(0)
                util = nvmlDeviceGetUtilizationRates(handle)
                power = nvmlDeviceGetPowerUsage(handle)
                temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
                log_record["resource.gpu.utilization"] = util.gpu
                log_record["resource.gpu.power_watt"] = power / 1000
                log_record["resource.gpu.temp"] = temp
            except Exception:
                pass

        # Exception info
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_record["error.type"] = exc_type.__name__
            log_record["error.message"] = str(exc_value)
            log_record["error.stack_trace"] = "".join(traceback.format_exception(*record.exc_info))

        super().add_fields(log_record, record, message_dict)


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

    try:
        # Charge et applique la configuration
        config = load_logging_config(config_path, environment)
        logging.config.dictConfig(config)

        logger = logging.getLogger(name)
        logger.debug(f"Logger '{name}' initialisé pour l'environnement '{environment}'")

        return logger

    except Exception as e:
        # Fallback sur une configuration basique en cas d'erreur
        print(f"Erreur lors de la configuration du logger: {e} - {traceback.format_exc()}")
        print("Utilisation de la configuration par défaut")

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(name)


# Initialise le logger principal
service_name = os.getenv("SERVICE_NAME", "abrege")
logger_abrege = setup_logger(service_name)
