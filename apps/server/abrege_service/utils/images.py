from PIL import Image
from io import BytesIO
import base64


def pil_image_to_base64(image: Image.Image) -> str:
    buffered = BytesIO()
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
