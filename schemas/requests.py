from pydantic import BaseModel, Field
from typing import Optional, Literal


class StatusRequest(BaseModel):
    api_key: str = Field(..., description="API authentication key")


class StatusResponse(BaseModel):
    success: bool = True
    ready: bool
    authorized: bool
    premium: bool
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_id: Optional[int] = None


class JoinRequest(BaseModel):
    api_key: str = Field(..., description="API authentication key")
    link: str = Field(..., description="Invite link, username, or chat link")


class JoinResponse(BaseModel):
    success: bool
    chat_id: str
    title: str
    type: str


class SendMessageRequest(BaseModel):
    api_key: str = Field(..., description="API authentication key")
    target: str = Field(..., description="Channel username (with @) or group ID (like -1001234567890)")
    message: str = Field(..., description="Message text with optional formatting")
    parse_mode: Literal["markdown", "html", "none"] = Field(default="markdown", description="Text parsing mode")


class SendMessageResponse(BaseModel):
    success: bool
    message_id: int
    chat_id: str
    date: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
