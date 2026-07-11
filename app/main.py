from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.schema import router as schema_router

app = FastAPI(
    title="DataInsight Agent",
    description="A LLM-powered data analysis agent.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(schema_router)


@app.get("/")
def root():
    return {"message": "DataInsight Agent is running."}
