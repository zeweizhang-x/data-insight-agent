from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

# 读取统一配置，避免把数据库地址写死在代码里。
settings = get_settings()

# engine 是 SQLAlchemy 和数据库之间的“连接工厂”。
# 它负责维护连接池，并把数据库 URL 交给 SQLAlchemy。
engine = create_engine(settings.DATABASE_URL, future=True)

# SessionLocal 是 Session 的工厂。
# 每次调用 SessionLocal()，都会创建一个独立的数据库会话对象。
# autocommit=False：事务不会自动提交，避免误操作。
# autoflush=False：在显式需要前，不自动把变更写入数据库。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 是所有 ORM 模型的基类。
# 之后你定义的数据表模型都需要继承它，SQLAlchemy 才能识别。
Base = declarative_base()


def get_db() -> Generator:
    # FastAPI 会通过 Depends(get_db) 注入这里生成的 session。
    # 使用 try/finally 能确保 session 在请求结束后一定被关闭。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
