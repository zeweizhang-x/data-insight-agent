from __future__ import annotations


def build_text_to_sql_messages(question: str, schema_text: str) -> list[dict]:
    system_message = (
        "你是一个 PostgreSQL 数据分析 SQL 生成助手，专门服务于电商经营分析场景。"
        "你的任务是根据用户问题和给定 schema 生成可直接执行的 SQL。"
        "\n\n约束："
        "\n1. 只能生成 SELECT 查询。"
        "\n2. 不能生成 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作或结构变更语句。"
        "\n3. 只能使用给定 schema 中存在的表和字段，不要臆造表名或列名。"
        "\n4. 默认添加 LIMIT 100，除非用户明确要求更少的结果数量。"
        "\n5. 只输出 SQL 本身，不要解释，不要 Markdown 代码块，不要附加任何多余文字。"
    )

    user_message = (
        f"数据库 schema:\n{schema_text}\n\n"
        f"用户问题:\n{question}\n\n"
        "请基于以上 schema 生成满足问题的 PostgreSQL SQL。"
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
