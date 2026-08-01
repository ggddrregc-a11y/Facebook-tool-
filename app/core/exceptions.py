class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FacebookAPIException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)


class AIProviderException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=503)


class AuthenticationException(AppException):
    def __init__(self, message: str = "غير مصرح"):
        super().__init__(message, status_code=401)


class NotFoundException(AppException):
    def __init__(self, message: str = "غير موجود"):
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class DuplicateCommentException(AppException):
    def __init__(self):
        super().__init__("تعليق مكرر", status_code=200)


class SpamCommentException(AppException):
    def __init__(self):
        super().__init__("تعليق مرفوض - سبام", status_code=200)
