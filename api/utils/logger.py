import logging 
from uuid import uuid4
from pythonjsonlogger import jsonlogger

logger_abrege = logging.getLogger(str(uuid4()))
logger_abrege.setLevel(logging.DEBUG)

handler = logging.StreamHandler()

formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(pathname)s %(lineno)d %(message)s',
    rename_fields={
        'asctime': '@timestamp',
        'levelname': 'level',
        'pathname': 'file_path',
        'lineno': 'line',
        'message': 'msg'
    }
)
handler.setFormatter(formatter)
logger_abrege.addHandler(handler)

