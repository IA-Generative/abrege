from abrege_service.schemas import IMAGE_CONTENT_TYPES
from abrege_service.modules.base import BaseService


class ImageService(BaseService):
    def __init__(self, content_type_allowed=IMAGE_CONTENT_TYPES):
        super().__init__(content_type_allowed)
