from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from faker import Faker

# 让脚本即使通过 `python scripts/generate_fake_data.py` 直接运行，
# 也能从项目根目录正确导入 `app` 包。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.models import Order, OrderItem, Product, User, UserEvent
from app.db.session import SessionLocal

fake = Faker("zh_CN")

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆"]
CATEGORIES = ["数码", "服饰", "美妆", "食品", "家居", "图书", "运动", "母婴"]
ORDER_STATUSES = ["created", "paid", "paid", "paid", "cancelled", "refunded"]
EVENT_TYPES = ["view", "cart", "favorite", "purchase"]


def money(value: float | int | Decimal) -> Decimal:
    # 统一把金额控制为两位小数，便于和 Numeric 字段匹配。
    return Decimal(str(value)).quantize(Decimal("0.01"))


def random_datetime(days_back: int = 365) -> datetime:
    # 生成一个最近一年内的随机时间，便于模拟真实业务数据分布。
    end = datetime.now()
    start = end - timedelta(days=days_back)
    return fake.date_time_between(start_date=start, end_date=end)


def clear_old_data(session) -> None:
    # 清理顺序必须先删子表，再删父表，避免外键冲突。
    session.query(UserEvent).delete(synchronize_session=False)
    session.query(OrderItem).delete(synchronize_session=False)
    session.query(Order).delete(synchronize_session=False)
    session.query(Product).delete(synchronize_session=False)
    session.query(User).delete(synchronize_session=False)
    session.commit()


def create_users(session, count: int) -> list[User]:
    users: list[User] = []
    for _ in range(count):
        users.append(
            User(
                username=fake.user_name(),
                gender=random.choice(["男", "女", "未知"]),
                age=random.randint(18, 60),
                city=random.choice(CITIES),
                register_time=random_datetime(),
            )
        )
    session.add_all(users)
    session.flush()
    return users


def create_products(session, count: int) -> list[Product]:
    products: list[Product] = []
    for _ in range(count):
        category = random.choice(CATEGORIES)
        base_price = random.uniform(9.9, 2999.0)
        products.append(
            Product(
                product_name=f"{category}{fake.word().capitalize()}",
                category=category,
                price=money(base_price),
                created_time=random_datetime(),
            )
        )
    session.add_all(products)
    session.flush()
    return products


def create_orders(session, users: list[User], products: list[Product], count: int) -> tuple[list[Order], list[OrderItem]]:
    orders: list[Order] = []
    order_items: list[OrderItem] = []

    for _ in range(count):
        user = random.choice(users)
        status = random.choice(ORDER_STATUSES)
        order = Order(
            user_id=user.user_id,
            order_time=random_datetime(),
            status=status,
            city=random.choice(CITIES),
            total_amount=money(0),
        )
        session.add(order)
        session.flush()

        chosen_products = random.sample(products, k=random.randint(1, 3))
        total_amount = Decimal("0.00")
        for product in chosen_products:
            quantity = random.randint(1, 5)
            unit_price = money(product.price)
            amount = money(unit_price * quantity)
            order_items.append(
                OrderItem(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                )
            )
            total_amount += amount

        order.total_amount = money(total_amount)
        orders.append(order)

    session.add_all(order_items)
    session.flush()
    return orders, order_items


def create_user_events(session, users: list[User], products: list[Product], count: int) -> list[UserEvent]:
    events: list[UserEvent] = []
    for _ in range(count):
        user = random.choice(users)
        product = random.choice(products)
        events.append(
            UserEvent(
                user_id=user.user_id,
                product_id=product.product_id,
                event_type=random.choices(EVENT_TYPES, weights=[55, 20, 15, 10], k=1)[0],
                event_time=random_datetime(),
            )
        )
    session.add_all(events)
    session.flush()
    return events


def main() -> None:
    # 随机种子不固定，保证每次生成的数据都不同，但仍然完全是模拟数据。
    Faker.seed()
    random.seed()

    session = SessionLocal()
    try:
        clear_old_data(session)

        users = create_users(session, 200)
        products = create_products(session, 80)
        orders, order_items = create_orders(session, users, products, 800)
        user_events = create_user_events(session, users, products, 3000)

        session.commit()

        print("Data generation finished.")
        print(f"users: {len(users)}")
        print(f"products: {len(products)}")
        print(f"orders: {len(orders)}")
        print(f"order_items: {len(order_items)}")
        print(f"user_events: {len(user_events)}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
