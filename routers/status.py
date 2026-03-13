from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from config import settings
from client_manager import client_manager
from schemas.requests import StatusRequest, StatusResponse
from utils.errors import handle_telegram_error, APIError


router = APIRouter(tags=["Status"])


async def verify_api_key(api_key: str) -> bool:
    if not settings.validate_api_key(api_key):
        raise HTTPException(status_code=401, detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}})
    return True


@router.get("/status", response_model=StatusResponse)
async def get_status(api_key: Annotated[str, Depends(lambda: None)]):
    await client_manager.initialize()
    
    try:
        status = await client_manager.get_status()
        
        return StatusResponse(
            success=True,
            ready=status.ready,
            authorized=status.authorized,
            premium=status.premium,
            username=status.username,
            first_name=status.first_name,
            last_name=status.last_name,
            user_id=status.user_id
        )
    except APIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        error = handle_telegram_error(e)
        raise HTTPException(status_code=error.status_code, detail=error.to_dict())
