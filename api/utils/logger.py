import logging

logger_abrege = logging.getLogger(name=__name__)
logger_abrege.setLevel(logging.DEBUG)
logger_abrege.propagate = False
logger_abrege.handlers = []
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger_abrege.addHandler(stream_handler)
logger_abrege.debug("Logger initialized")
