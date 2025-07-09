from typing import List
from PIL import Image
from pdf2image import pdfinfo_from_path, convert_from_path
from collections.abc import Sequence


class LazyPdfImageList(Sequence):
    """
    Liste paresseuse (lazy) d’images extraites d’un PDF. Chaque image est chargée à la demande.
    Se comporte comme une vraie liste : indexation, slicing, itération, len().
    """

    def __init__(self, pdf_path, dpi=200, fmt="jpeg"):
        self.pdf_path = pdf_path
        self.dpi = dpi
        self.fmt = fmt
        self._total_pages = None

    def __len__(self):
        if self._total_pages is None:
            info = pdfinfo_from_path(self.pdf_path)
            self._total_pages = info["Pages"]
        return self._total_pages

    def __getitem__(self, index) -> List[Image.Image]:
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if not isinstance(index, int):
            raise TypeError("Index must be int or slice")
        if index < 0:
            index += len(self)
        if not (0 <= index < len(self)):
            raise IndexError("Page index out of range")
        return self._load_page(index)

    def _load_page(self, index: int) -> Image.Image:
        images = convert_from_path(
            self.pdf_path,
            dpi=self.dpi,
            fmt=self.fmt,
            first_page=index + 1,
            last_page=index + 1,
        )
        return images[0]  # PIL Image

    def __repr__(self):
        return f"<LazyPdfImageList pages={len(self)} path='{self.pdf_path}'>"
