from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import urls, redirect, auth
from app.database.bootstrap import initialize_database
from app.middleware.error_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Link Forge", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    app.include_router(urls.router)
    app.include_router(redirect.router)
    app.include_router(auth.router)
    register_exception_handlers(app)

    return app



app = create_app()

