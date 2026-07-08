# DataInsight Agent
基于 LLM + RAG + Text-to-SQL 的智能数据分析系统。

## 当前进度
- 初始化 FastAPI 项目
- 配置 Python 虚拟环境
- 配置 Docker Compose
- 启动 PostgreSQL 和 Redis
- 实现 `/health` 健康检查接口

## 启动方式
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
接口文档：
http://127.0.0.1:8000/docs
