from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from config import settings
from client_manager import client_manager
from schemas.requests import SendMessageRequest, SendMessageResponse
from utils.errors import handle_telegram_error, APIError


router = APIRouter(prefix="/api/v1", tags=["Send"])


async def verify_api_key(api_key: str) -> bool:
    if not settings.validate_api_key(api_key):
        raise HTTPException(status_code=401, detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}})
    return True


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    _: Annotated[bool, Depends(lambda x: verify_api_key(request.api_key))]
):
    await client_manager.initialize()
    
    try:
        result = await client_manager.send_message(
            target=request.target,
            text=request.message,
            parse_mode=request.parse_mode
        )
        return SendMessageResponse(**result)
    except APIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        error = handle_telegram_error(e)
        raise HTTPException(status_code=error.status_code, detail=error.to_dict())
