"""Custom exceptions for OCR SDK."""


class AbregeSDKError(Exception):
    """Base exception for Abrege SDK."""

    pass


class AbregeAPIError(AbregeSDKError):
    """Exception raised when API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class AbregeTimeoutError(AbregeSDKError):
    """Exception raised when a request times out."""

    pass


class AbregeAuthenticationError(AbregeSDKError):
    """Exception raised when authentication fails."""

    pass


class AbregeValidationError(AbregeSDKError):
    """Exception raised when validation fails."""

    pass
