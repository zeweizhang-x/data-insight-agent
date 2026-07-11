from sqlalchemy import inspect

from app.db.session import engine

# 只展示业务表，避免把系统表也暴露出去。
BUSINESS_TABLES = ["users", "products", "orders", "order_items", "user_events"]


def get_database_schema() -> list[dict]:
    inspector = inspect(engine)
    available_tables = set(inspector.get_table_names())

    schema_list: list[dict] = []
    for table_name in BUSINESS_TABLES:
        if table_name not in available_tables:
            continue

        columns = []
        for column in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                }
            )

        schema_list.append(
            {
                "table_name": table_name,
                "columns": columns,
            }
        )

    return schema_list
