from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import urls, redirect, auth, analytics
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.middleware.rate_limit import limiter
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
    app.include_router(analytics.router)
    register_exception_handlers(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    return app



app = create_app()

