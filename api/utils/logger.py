import logging

logger_app = logging.getLogger(name=__name__)
logger_app.setLevel(logging.DEBUG)
logger_app.propagate = False
logger_app.handlers = []
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger_app.addHandler(stream_handler)
logger_app.debug("Logger initialized")
