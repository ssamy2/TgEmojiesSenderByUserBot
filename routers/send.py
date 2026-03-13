from fastapi import APIRouter, HTTPException

from config import settings
from client_manager import client_manager
from schemas.requests import SendMessageRequest, SendMessageResponse
from utils.errors import handle_telegram_error, APIError


router = APIRouter(tags=["Send"])


@router.post("/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    print(f"\n[DEBUG] Received /send request for target: {request.target}")
    try:
        if not settings.validate_api_key(request.api_key):
            raise HTTPException(status_code=401, detail={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"}})
        
        await client_manager.initialize()
        
        result = await client_manager.send_message(
            target=request.target,
            text=request.message,
            parse_mode=request.parse_mode
        )
        return SendMessageResponse(**result)
    except APIError as e:
        print(f"\n\033[93m[API Error]: {e.message}\033[0m")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        import traceback
        print("\n\033[91m!!! ERROR IN SEND ROUTE !!!\033[0m")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}})
