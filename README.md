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
- `/query/validate-sql`（开发调试接口）
- `/system/cache/stats`（开发调试接口）
- Day 3 Text-to-SQL MVP
  - LLM client
  - Text-to-SQL prompt
  - SQL 提取与基础校验
  - `/query/text-to-sql`
- Day 4 Text-to-SQL 安全与修复增强
  - 使用 `sqlglot` 增强 SQL 安全校验
  - 限制只允许 `SELECT` / `WITH`
  - 限制业务表白名单
  - SQL 执行失败时自动修复一次
  - `/query/text-to-sql` 返回 `original_sql`、`sql`、`repaired`、`repair_attempts`
  - `/query/validate-sql` 作为开发调试接口
- Day 5 Schema RAG
  - schema 文档 `docs/schema/ecommerce_schema.md`
  - embedding client
  - Chroma 本地向量库
  - schema indexing 脚本
  - `/schema/search` 接口
  - `/query/text-to-sql` 优先使用 Schema RAG，失败时 fallback 到 full schema

## 本地启动方式

### 1. 配置环境变量
在 `.env` 中补充 LLM 配置：
```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-openai-compatible-base-url/v1
LLM_MODEL=your-model-name
EMBEDDING_MODEL=your-embedding-model-name
CHROMA_PERSIST_DIR=.chroma
```

### 2. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 3. 启动 Docker Compose
```bash
docker compose up -d
```

### 4. 初始化数据库
```bash
python -m app.db.init_db
```

### 5. 生成模拟数据
```bash
python scripts/generate_fake_data.py
```

### 6. 启动 FastAPI
```bash
uvicorn app.main:app --reload
```

启动后可以访问：
- 接口文档：`http://127.0.0.1:8000/docs`
- 健康检查：`GET /health`
- Schema 查看：`GET /schema/list`
- 原始 SQL 查询：`POST /query/raw-sql`
- SQL 校验调试：`POST /query/validate-sql`
- 系统缓存统计调试：`GET /system/cache/stats`
- Text-to-SQL：`POST /query/text-to-sql`
- Schema 搜索：`POST /schema/search`

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

## `/query/text-to-sql` 示例请求
```bash
curl -X POST "http://127.0.0.1:8000/query/text-to-sql" \
  -H "Content-Type: application/json" \
  -d '{"question":"查询最近 7 天订单金额最高的前 10 个用户"}'
```

流程说明：
`question -> schema retrieval -> prompt -> LLM SQL -> validation -> execution -> repair`

示例返回结构包含：
- `question`
- `schema_source`
- `retrieved_tables`
- `schema_retrieval_error`（仅 fallback 时返回）
- `original_sql`
- `sql`
- `repaired`
- `repair_attempts`
- `columns`
- `rows`

## `/schema/search` 示例请求
```bash
curl -X POST "http://127.0.0.1:8000/schema/search" \
  -H "Content-Type: application/json" \
  -d '{"question":"查询订单金额最高的用户相关表结构", "top_k": 3}'
```

示例返回结构包含：
- `question`
- `top_k`
- `documents`
- `schema_text`

## Schema RAG 构建命令
```bash
python scripts/index_schema_docs.py
```

## `/query/validate-sql` 开发调试接口
该接口只做 SQL 提取、基础校验和 LIMIT 归一化，不会执行 SQL。

示例请求：
```bash
curl -X POST "http://127.0.0.1:8000/query/validate-sql" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT * FROM users"}'
```

示例返回：
```json
{
  "valid": true,
  "sql": "SELECT * FROM users LIMIT 100;"
}
```

## `/system/cache/stats` 开发调试接口
该接口用于查看当前 Redis 中的缓存键数量，使用 `scan_iter` 统计，不会抛出 500。

示例请求：
```bash
curl -X GET "http://127.0.0.1:8000/system/cache/stats"
```

示例返回：
```json
{
  "redis": true,
  "text2sql_cache_keys": 12,
  "schema_retrieval_cache_keys": 8
}
```

## 当前限制
- 只支持一次修复
- 只使用简单的 `top_k` 检索
- 还没有 reranker
- 还没有评测集
- schema 文档还需要持续完善
- 指标口径仍然比较简单
- 复杂 Join 可能失败
- 安全校验不是生产级权限系统

## 配置说明
项目通过 `.env` 读取配置
