from app.db.session import Base, engine

# 导入 models 的目的是让所有 ORM 类在执行 create_all 之前完成注册。
# 如果不导入，Base.metadata 里可能没有任何表信息。
import app.db.models  # noqa: F401


def init_db() -> None:
    # 这里仅创建不存在的表，不会删除或重建已有表。
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    # 允许通过 `python -m app.db.init_db` 直接执行初始化。
    init_db()
