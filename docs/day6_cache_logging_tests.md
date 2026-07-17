# Day 6 Cache And Logging Tests

## Goal

Verify Redis cache, trace logging, and system health checks.

Current workflow:

Question -> cache lookup -> Schema RAG -> LLM SQL -> validation -> execution -> repair -> cache save -> response.

## Test Cases

### 1. Text-to-SQL Cache Miss

Question:

```text
各城市已支付订单的GMV排名前5是多少？
Expected:
• First request returns cache_hit = false
• Response contains trace_id
• Response contains latency_ms
• Redis has text2sql:* key
2. Text-to-SQL Cache Hit
Repeat the same question.
Expected:
• Second request returns cache_hit = true
• latency_ms should usually be lower
• No new LLM generation should be needed
3. Schema Retrieval Cache
Request:
json
复制代码
{
  "question": "销售额最高的商品类目前5名是什么？",
  "top_k": 3
}
Expected:
• First request may return cache_hit = false
• Second request should return cache_hit = true
4. System Health
Endpoint:
text
复制代码
GET /system/health
Expected:
• api = true
• postgres = true
• redis = true
• status = ok
Fields To Observe
• trace_id
• latency_ms
• cache_hit
• schema_source
• retrieved_tables
• repaired
• repair_attempts
Known Limitations
• Cache invalidation is simple TTL-based.
• Cache key does not yet include schema document version.
• Cached results may become stale if database data changes.
• Logs are console-only and not yet persisted. 
