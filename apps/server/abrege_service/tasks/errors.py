class OCRError(Exception):
    """Base class for OCR-related errors."""

    pass


class RetryableOCRError(OCRError):
    """Indicates an OCR error that may be resolved by retrying the operation."""

    pass
