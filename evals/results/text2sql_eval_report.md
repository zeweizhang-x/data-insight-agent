# Text-to-SQL Eval Report

- Source: `/home/zzw/projects/data-insight-agent/evals/results/text2sql_eval_results.jsonl`

## Overall Metrics

| metric | value |
| --- | --- |
| total | 5 |
| success_count | 5 |
| success_rate | 100.00% |
| execution_success_count | 5 |
| table_recall_pass_count | 5 |
| required_keywords_pass_count | 5 |
| forbidden_keywords_pass_count | 5 |
| repaired_count | 0 |
| cache_hit_count | 0 |
| average_latency_ms | 15714.18 |

## Category Metrics

| category | total | success_count | success_rate |
| --- | --- | --- | --- |
| aggregation | 1 | 1 | 100.00% |
| single_table | 4 | 4 | 100.00% |

## Failure Cases

_No failure cases._

## Bad Case Type Counts

| bad_case_type | count |
| --- | --- |
| schema_retrieval_error | 0 |
| sql_generation_error | 0 |
| sql_execution_error | 0 |
| safety_error | 0 |
| other | 0 |

## Bad Case Suggestions

| type | count | suggestion |
| --- | --- | --- |
| schema_retrieval_error | 0 | 预期表未召回，优先检查 schema 文档、embedding 和 top_k 检索覆盖。 |
| sql_generation_error | 0 | 关键 SQL 片段缺失，优先检查 prompt、schema 上下文和模型输出质量。 |
| sql_execution_error | 0 | SQL 执行失败，优先检查 SQL 合法性、表字段名和修复逻辑。 |
| safety_error | 0 | 危险 SQL 未被拦截，优先加强安全校验与禁止词/禁止操作规则。 |
| other | 0 | 无法归类或需要人工复核的 bad case。 |
