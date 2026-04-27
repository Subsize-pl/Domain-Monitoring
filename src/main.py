from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.router import router as auth_router
from core.utils.log.logger import setup_logging
from web.routes.pages import router as web_router


async def create_db_and_tables():
    from infrastructure.db.db_manager import db_manager
    from infrastructure.db import Base

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await create_db_and_tables()

    from core.utils.log.logger import get_logger

    logger = get_logger("lifespan")
    logger.error(logger.level)
    yield


app = FastAPI(
    title="My FastAPI App",
    description="My FastAPI App",
    lifespan=lifespan,
)
app.mount(
    "/static",
    StaticFiles(directory="web/static"),
    name="static",
)

app.include_router(web_router)
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
