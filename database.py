from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import Date, Float, ForeignKey, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

DB_PATH = Path(__file__).with_name("kobi_agent.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Auth / Users
# ---------------------------------------------------------------------------

class User(Base):
    """Application user with a role of either 'admin' or 'customer'."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="customer")


# ---------------------------------------------------------------------------
# Business domain models
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="orders")
    product: Mapped[Product] = relationship(back_populates="orders")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_session() -> Session:
    return Session(engine)


def init_db(drop_existing: bool = False) -> None:
    if drop_existing and DB_PATH.exists():
        DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Auth helpers  (passlib is used so we avoid storing plain-text passwords)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    import bcrypt  # type: ignore
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    import bcrypt  # type: ignore
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def get_user_by_username(username: str) -> User | None:
    with get_session() as session:
        return session.scalars(select(User).where(User.username == username)).first()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed_db() -> None:
    with get_session() as session:
        # --- seed users only when table is empty ---
        has_users = session.execute(select(User.id).limit(1)).first() is not None
        if not has_users:
            users = [
                User(
                    username="admin",
                    hashed_password=hash_password("admin"),
                    role="admin",
                ),
                User(
                    username="customer",
                    hashed_password=hash_password("customer"),
                    role="customer",
                ),
            ]
            session.add_all(users)
            session.commit()

        # --- seed business data only when products table is empty ---
        has_products = session.execute(select(Product.id).limit(1)).first() is not None
        if has_products:
            return

        products = [
            Product(name="Kahve", stock_quantity=8, price=129.90),
            Product(name="Çay", stock_quantity=35, price=79.50),
            Product(name="Zeytinyağı", stock_quantity=4, price=299.00),
            Product(name="Bal", stock_quantity=12, price=249.90),
            Product(name="Pekmez", stock_quantity=0, price=159.00),
        ]
        customers = [
            Customer(name="Ayşe Yılmaz", phone="0555 000 00 01", email="ayse@example.com"),
            Customer(name="Mehmet Demir", phone="0555 000 00 02", email="mehmet@example.com"),
            Customer(name="Zeynep Kaya", phone="0555 000 00 03", email="zeynep@example.com"),
            Customer(name="Ali Çetin", phone="0555 000 00 04", email="ali@example.com"),
            Customer(name="Elif Şahin", phone="0555 000 00 05", email="elif@example.com"),
        ]

        session.add_all(products)
        session.add_all(customers)
        session.commit()

        product_by_name = {p.name: p for p in session.scalars(select(Product)).all()}
        customer_by_email = {c.email: c for c in session.scalars(select(Customer)).all()}

        today = date.today()
        orders = [
            Order(
                customer_id=customer_by_email["ayse@example.com"].id,
                product_id=product_by_name["Kahve"].id,
                status="Hazırlanıyor",
                order_date=today,
            ),
            Order(
                customer_id=customer_by_email["mehmet@example.com"].id,
                product_id=product_by_name["Çay"].id,
                status="Kargoya Verildi",
                order_date=today - timedelta(days=1),
            ),
            Order(
                customer_id=customer_by_email["zeynep@example.com"].id,
                product_id=product_by_name["Zeytinyağı"].id,
                status="Teslim Edildi",
                order_date=today - timedelta(days=3),
            ),
            Order(
                customer_id=customer_by_email["ali@example.com"].id,
                product_id=product_by_name["Bal"].id,
                status="Kargoya Verildi",
                order_date=today,
            ),
            Order(
                customer_id=customer_by_email["elif@example.com"].id,
                product_id=product_by_name["Pekmez"].id,
                status="Hazırlanıyor",
                order_date=today - timedelta(days=2),
            ),
        ]
        session.add_all(orders)
        session.commit()


# ---------------------------------------------------------------------------
# Agent tool functions  (called by ai_agent.py)
# ---------------------------------------------------------------------------

def get_order_status(order_id: int) -> dict[str, Any]:
    with get_session() as session:
        order = session.get(Order, order_id)
        if not order:
            return {"found": False, "order_id": order_id}

        session.refresh(order)
        return {
            "found": True,
            "order_id": order.id,
            "status": order.status,
            "order_date": order.order_date.isoformat(),
            "customer": {"id": order.customer.id, "name": order.customer.name},
            "product": {"id": order.product.id, "name": order.product.name},
        }


def check_critical_stock(threshold: int = 10) -> list[dict[str, Any]]:
    with get_session() as session:
        rows = session.scalars(select(Product).where(Product.stock_quantity < threshold)).all()
        return [
            {"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity, "price": p.price}
            for p in rows
        ]


def get_product_info(product_name: str) -> dict[str, Any]:
    normalized = product_name.strip().lower()
    with get_session() as session:
        product = session.scalars(
            select(Product).where(func.lower(Product.name) == normalized)
        ).first()
        if not product:
            product = session.scalars(select(Product).where(Product.name.ilike(f"%{normalized}%"))).first()
        if not product:
            return {"found": False, "product_name": product_name}
        return {
            "found": True,
            "id": product.id,
            "name": product.name,
            "stock_quantity": product.stock_quantity,
            "price": product.price,
        }


# ---------------------------------------------------------------------------
# Dashboard aggregate helpers
# ---------------------------------------------------------------------------

def get_dashboard_metrics() -> dict[str, Any]:
    """Return high-level KPIs for the admin dashboard."""
    with get_session() as session:
        total_products = session.execute(select(func.count(Product.id))).scalar_one()
        total_orders = session.execute(select(func.count(Order.id))).scalar_one()
        low_stock = session.scalars(
            select(Product).where(Product.stock_quantity < 10)
        ).all()

        recent_orders = session.scalars(
            select(Order).order_by(Order.order_date.desc()).limit(5)
        ).all()

        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "low_stock": [
                {"name": p.name, "stock_quantity": p.stock_quantity}
                for p in low_stock
            ],
            "recent_orders": [
                {
                    "id": o.id,
                    "customer": o.customer.name,
                    "product": o.product.name,
                    "status": o.status,
                    "order_date": o.order_date.isoformat(),
                }
                for o in recent_orders
            ],
        }


def _main() -> None:
    init_db()
    seed_db()
    print(f"DB ready: {DB_PATH}")
    print("Seed complete. Sample order ids: 1..5")


if __name__ == "__main__":
    _main()
