from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from domain_monitoring.auth.router import router as auth_router
from domain_monitoring.core.config.settings import get_settings
from domain_monitoring.core.utils.log.logger import setup_logging

from domain_monitoring.monitoring.core.scheduler import DomainCheckScheduler
from domain_monitoring.web.routes.auth import router as web_router
from domain_monitoring.monitoring.router import router as monitoring_router
from domain_monitoring.core.config.settings import PROJECT_ROOT
from domain_monitoring.infrastructure.db.db_manager import get_db_manager

STATIC_DIR = PROJECT_ROOT / "web" / "static"

settings = get_settings()
db_manager = get_db_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    scheduler = DomainCheckScheduler(
        session_factory=db_manager.async_session_factory,
    )
    await scheduler.start()
    yield
    await scheduler.stop()


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


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(
        "domain_monitoring.main:app",
        port=settings.app_port,
        host=settings.app_host,
    )
