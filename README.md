# DataInsight Agent

一个面向电商分析场景的 FastAPI 项目，目标是逐步构建支持数据库查询、数据探索和后续 LLM 分析能力的数据分析服务。

## 当前技术栈
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Docker Compose

## 当前已完成
- 项目结构
- PostgreSQL 连接
- 电商业务表
- 模拟数据生成
- `/health`
- `/schema/list`
- `/query/raw-sql`

## 本地启动方式

### 1. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 2. 启动 Docker Compose
```bash
docker compose up -d
```

### 3. 初始化数据库
```bash
python -m app.db.init_db
```

### 4. 生成模拟数据
```bash
python scripts/generate_fake_data.py
```

### 5. 启动 FastAPI
```bash
uvicorn app.main:app --reload
```

启动后可以访问：
- 接口文档：`http://127.0.0.1:8000/docs`
- 健康检查：`GET /health`
- Schema 查看：`GET /schema/list`
- 原始 SQL 查询：`POST /query/raw-sql`

## 示例 SQL 查询
```sql
SELECT * FROM users LIMIT 5;
```

```sql
SELECT category, COUNT(*) AS product_count
FROM products
GROUP BY category
ORDER BY product_count DESC;
```

```sql
SELECT user_id, COUNT(*) AS order_count, SUM(total_amount) AS total_spent
FROM orders
WHERE status = 'paid'
GROUP BY user_id
ORDER BY total_spent DESC
LIMIT 10;
```

## 配置说明
项目通过 `.env` 读取配置，请不要把真实 API Key 写进代码或提交到仓库。
建议使用如下占位形式：

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://your-api-base/v1
LLM_MODEL=your_model_name
```
