from .marker_client import MarkerAPIClient
from ..config.marker_api import MarkerAPISettings

marker_api_setting = MarkerAPISettings()

client_marker = MarkerAPIClient(base_url=marker_api_setting.MARKER_API_BASE_URL)
