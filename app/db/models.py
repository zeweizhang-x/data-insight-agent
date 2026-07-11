from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    # users 表：保存用户基础画像信息，后续可用于人群分析、留存分析等。
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    register_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    # 一个用户可以有多笔订单、多个行为事件。
    orders = relationship("Order", back_populates="user")
    events = relationship("UserEvent", back_populates="user")


class Product(Base):
    # products 表：保存商品主数据，用于商品分析、品类分析和交易明细关联。
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    # 一个商品可以出现在多个订单明细和多个用户行为事件中。
    order_items = relationship("OrderItem", back_populates="product")
    events = relationship("UserEvent", back_populates="product")


class Order(Base):
    # orders 表：保存订单主信息，通常是一笔交易的汇总层。
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    order_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 一笔订单对应一个用户，并包含多条订单明细。
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    # order_items 表：保存订单里的商品明细，适合做商品粒度的销量和收入分析。
    __tablename__ = "order_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # 明细行关联到订单和商品。
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class UserEvent(Base):
    # user_events 表：保存用户行为日志，比如浏览、点击、加购等。
    __tablename__ = "user_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    # 用户行为通常会指向一个用户和一个商品。
    user = relationship("User", back_populates="events")
    product = relationship("Product", back_populates="events")
