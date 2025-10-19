import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db
from app.api import health as health_api
from app.api import files as files_api
from app.api import ai as ai_api


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(
        title="Alphintra AI/ML Strategy Service",
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_api.router)
    app.include_router(files_api.router)
    app.include_router(ai_api.router)

    @app.get("/")
    def root():
        return {"service": settings.SERVICE_NAME, "version": settings.VERSION, "status": "operational"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
