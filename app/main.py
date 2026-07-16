from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.api.routes.schema import router as schema_router
from app.core.logging import get_logger, setup_logging


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DataInsight Agent API started")
    yield

app = FastAPI(
    title="DataInsight Agent",
    description="A LLM-powered data analysis agent.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(schema_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {"message": "DataInsight Agent is running."}
