from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from domain_monitoring.core.config.settings import get_settings
from domain_monitoring.monitoring.router import router as monitoring_router
from domain_monitoring.auth.router import router as auth_router
from domain_monitoring.core.utils.log.logger import setup_logging
from domain_monitoring.web.routes.pages import router as web_router

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="My FastAPI App",
    description="My FastAPI App",
    lifespan=lifespan,
)
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)
app.include_router(web_router)
app.include_router(auth_router)
app.include_router(monitoring_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{settings.app_base_url}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(
        "domain_monitoring.main:app",
        host=settings.app_host,
        port=settings.app_port,
    )
