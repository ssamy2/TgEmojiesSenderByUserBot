from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import settings
from routers import status_router, join_router, send_router
from client_manager import client_manager
from utils.errors import APIError, ErrorCode


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Telegram Premium Sender API - Send messages with premium emoji support",
    lifespan=lifespan
)

import traceback
from fastapi.exceptions import RequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("\n\033[91m!!! INTERNAL SERVER ERROR !!!\033[0m")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "SERVER_ERROR", "message": str(exc)}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"code": "VALIDATION_ERROR", "details": exc.errors()}}
    )

@app.on_event("startup")
async def startup_event():
    print("Registered Routes:")
    for route in app.routes:
        print(f"Path: {route.path}, Methods: {getattr(route, 'methods', 'N/A')}")


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.get("/")
async def root():
    return {
        "success": True,
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(status_router, prefix="/api/v1")
app.include_router(join_router, prefix="/api/v1")
app.include_router(send_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
