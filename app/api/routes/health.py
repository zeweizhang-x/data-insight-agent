from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    # 健康检查接口通常用于确认服务是否正常启动。
    return {"status": "ok"}
