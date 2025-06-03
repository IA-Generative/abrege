import os
import socket
import logging
import psutil
import traceback
from datetime import datetime
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


logger_abrege = logging.getLogger(name=__name__)
logger_abrege.setLevel(logging.DEBUG)
logger_abrege.propagate = False
logger_abrege.handlers = []
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ECSJsonFormatter())
logger_abrege.addHandler(stream_handler)
logger_abrege.debug("Logger initialized")
