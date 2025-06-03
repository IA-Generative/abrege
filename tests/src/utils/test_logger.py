import logging
import json
import io
import re
import pytest
from src.utils.logger import ECSJsonFormatter


@pytest.fixture
def log_output():
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = ECSJsonFormatter()
    handler.setFormatter(formatter)

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    return logger, log_stream


def test_ecs_json_formatter_basic(log_output):
    logger, log_stream = log_output

    logger.info("Test ECS formatter", extra={"custom": "value"})

    log_stream.seek(0)
    log_line = log_stream.readline()
    log_data = json.loads(log_line)

    # Champs ECS de base
    assert "@timestamp" in log_data
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}", log_data["@timestamp"])
    assert log_data["log.level"] == "info"
    assert log_data["message"] == "Test ECS formatter"
    assert log_data["log.logger"] == "test_logger"

    # Champs de ressources
    assert "resource.cpu.percent" in log_data
    assert "resource.memory.rss" in log_data
    assert "host.name" in log_data
    assert "process.pid" in log_data

    # Champs Kubernetes (None si non injecté)
    assert "kubernetes.pod.name" in log_data

    # Champs custom
    assert log_data.get("custom") == "value"
