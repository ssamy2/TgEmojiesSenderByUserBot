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


app.include_router(status_router)
app.include_router(join_router)
app.include_router(send_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
