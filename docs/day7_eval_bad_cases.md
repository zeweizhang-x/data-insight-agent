# Day 7 Evaluation And Bad Case Analysis

## Goal

Build a repeatable evaluation workflow 
for
 the Text-to-SQL system.

Current workflow:

Evaluation cases -> Text-to-SQL service -> SQL validation -> execution -> result logging -> report generation.

## Metrics

- Execution success rate
- Table recall pass rate
- Required SQL keyword pass rate
- Forbidden SQL keyword pass rate
- Repair count
- Cache hit count
- Average latency

## Bad Case Types

### 1. Schema Retrieval Error

The expected table is not retrieved by Schema RAG.

Example:

```text
Question: 销售额最高的商品类目前5名是什么？
Expected tables: order_items, products
Retrieved tables: products, orders
Possible fixes:
• Improve schema documentation
• Add table relationship descriptions
• Increase top_k
• Add reranker
2. SQL Generation Error
The SQL does not contain required business logic.
Example:
text
复制代码
Question: 各城市已支付订单的GMV排名前5是多少？
Expected: status = 'paid', sum(total_amount)
Generated SQL misses status filter
Possible fixes:
• Improve metric definitions
• Add examples to prompt
• Add business glossary
3. SQL Execution Error
The SQL fails to execute.
Common causes:
• Wrong column name
• Wrong table alias
• Invalid PostgreSQL function
• Bad join condition
Possible fixes:
• Use SQL repair prompt
• Add database error feedback
• Improve schema text
4. Safety Error
Dangerous SQL is not blocked.
Examples:
sql
复制代码
DROP TABLE
 orders;
DELETE FROM
 users;
Possible fixes:
• Strengthen sqlglot validation
• Add table whitelist
• Add statement type whitelist
• Add permission layer
5. Metric Definition Error
The SQL executes but business meaning is wrong.
Example:
text
复制代码
GMV should use paid orders, but SQL sums all orders.
Possible fixes:
• Add metric definition docs
• Add few-shot examples
• Add evaluation cases for metric correctness
Day 7 Notes
Record actual failed cases from evals/results/text2sql_eval_report.md
 here after each evaluation run.
