from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from enum import Enum


class ErrorCode(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_NOT_AUTHORIZED = "SESSION_NOT_AUTHORIZED"
    FLOOD_WAIT = "FLOOD_WAIT"
    PHONE_CODE_EXPIRED = "PHONE_CODE_EXPIRED"
    PHONE_CODE_INVALID = "PHONE_CODE_INVALID"
    SESSION_PASSWORD_NEEDED = "SESSION_PASSWORD_NEEDED"
    PREMIUM_REQUIRED = "PREMIUM_REQUIRED"
    INVALID_TARGET = "INVALID_TARGET"
    SERVER_ERROR = "SERVER_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class APIError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details
            }
        }


class FloodWaitError(APIError):
    def __init__(self, retry_after: int):
        super().__init__(
            code=ErrorCode.FLOOD_WAIT,
            message=f"Flood wait required. Please retry after {retry_after} seconds.",
            status_code=420,
            details={"retry_after": retry_after}
        )


class UnauthorizedError(APIError):
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401
        )


class SessionNotFoundError(APIError):
    def __init__(self):
        super().__init__(
            code=ErrorCode.SESSION_NOT_FOUND,
            message="Telegram session not found. Please login first.",
            status_code=401
        )


class SessionNotAuthorizedError(APIError):
    def __init__(self):
        super().__init__(
            code=ErrorCode.SESSION_NOT_AUTHORIZED,
            message="Telegram session not authorized. Please complete login.",
            status_code=401
        )


class RateLimitError(APIError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=429,
            details={"retry_after": retry_after}
        )


def handle_telegram_error(e: Exception) -> APIError:
    error_str = str(e).lower()
    
    if "flood wait" in error_str:
        import re
        match = re.search(r'(\d+)', str(e))
        retry_after = int(match.group(1)) if match else 60
        return FloodWaitError(retry_after)
    
    if "phone_code_expired" in error_str:
        return APIError(
            code=ErrorCode.PHONE_CODE_EXPIRED,
            message="Verification code has expired. Please restart login.",
            status_code=400
        )
    
    if "phone_code_invalid" in error_str:
        return APIError(
            code=ErrorCode.PHONE_CODE_INVALID,
            message="Invalid verification code.",
            status_code=400
        )
    
    if "session password needed" in error_str:
        return APIError(
            code=ErrorCode.SESSION_PASSWORD_NEEDED,
            message="Two-step verification password required.",
            status_code=400
        )
    
    if "auth_key_unregistered" in error_str:
        return SessionNotFoundError()
    
    if "banned" in error_str or "forbidden" in error_str:
        return APIError(
            code=ErrorCode.FORBIDDEN,
            message="Access forbidden. Account may be banned.",
            status_code=403
        )
    
    return APIError(
        code=ErrorCode.SERVER_ERROR,
        message=f"Telegram API error: {str(e)}",
        status_code=500
    )


def http_exception_from_api_error(error: APIError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail=error.to_dict()
    )
