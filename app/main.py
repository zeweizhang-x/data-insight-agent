from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(
    title="DataInsight Agent",
    description="A LLM-powered data analysis agent.",
    version="0.1.0",
)

# 把健康检查路由挂到主应用上。
app.include_router(health_router)


@app.get("/")
def root():
    # 根路径保留给快速确认服务是否启动成功。
    return {"message": "DataInsight Agent is running."}
