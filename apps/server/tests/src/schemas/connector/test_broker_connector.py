import celery
import pytest
from kombu.exceptions import OperationalError

from src.connector.broker_connector import BrokerConnector
from src.schemas.health import HealtStatus


class FakeConnection:
    def __init__(self, error=None):
        self.error = error
        self.released = False

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.released = True
        return False

    def ensure_connection(self, **kwargs):
        if self.error is not None:
            raise self.error


class FakeCeleryApp:
    def __init__(self, error=None):
        self.connection = FakeConnection(error)

    def connection_for_write(self):
        return self.connection


def test_broker_health_healthy():
    app = FakeCeleryApp()
    health = BrokerConnector(celery_app=app).get_health()

    assert health.name == "broker"
    assert health.status == HealtStatus.HEALTHY
    assert health.version == celery.__version__
    assert app.connection.released, "la connexion doit etre liberee apres la sonde"


def test_broker_health_reports_noauth():
    """Le cas de l'incident : le broker rejette la publication faute d'authentification."""
    app = FakeCeleryApp(OperationalError("Authentication required."))
    health = BrokerConnector(celery_app=app).get_health()

    assert health.status == HealtStatus.UNHEALTHY
    assert "Authentication required." in health.extras["error"]
    assert app.connection.released


@pytest.mark.parametrize("error", [RuntimeError("boom"), OSError("socket down")])
def test_broker_health_never_raises(error):
    """Une sonde de sante ne doit jamais propager d'exception."""
    health = BrokerConnector(celery_app=FakeCeleryApp(error)).get_health()

    assert health.status == HealtStatus.UNHEALTHY
