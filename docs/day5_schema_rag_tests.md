# Day 5 Schema RAG Tests

## Goal

Verify that Text-to-SQL uses retrieved schema documents instead of always using the full database schema.

Current flow:

Question -> Schema Retrieval -> Prompt with relevant schema -> LLM SQL -> SQL validation -> execution -> repair on failure.

## Test Cases

### 1. City GMV Ranking

Question:

```text
各城市已支付订单的GMV排名前5是多少？
Expected retrieved tables:

orders
Expected SQL behavior:

Uses orders
Filters status = 'paid'
Sums total_amount
Groups by city
2. Product Category Sales Ranking
Question:

text
销售额最高的商品类目前5名是什么？
Expected retrieved tables:

order_items
products
Expected SQL behavior:

Joins order_items and products
Groups by products.category
Sums order_items.amount
3. User City Distribution
Question:

text
每个城市的用户数量是多少？
Expected retrieved tables:

users
Expected SQL behavior:

Uses users
Groups by city
Counts users
4. Product View Ranking
Question:

text
浏览量最高的商品前10名是什么？
Expected retrieved tables:

user_events
products
Expected SQL behavior:

Filters event_type = 'view'
Joins user_events and products
Counts view events
Fields To Observe
schema_source
retrieved_tables
original_sql
sql
repaired
repair_attempts
columns
rows
Known Limitations
Retrieval quality depends on schema documentation and embedding model.
top_k is fixed to 3 in the Text-to-SQL workflow.
Metric definitions are still simple.
No reranker is used yet. 

