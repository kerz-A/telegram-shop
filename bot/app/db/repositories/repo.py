"""
Async repository layer for bot DB operations.
All queries go through here — no direct session usage in handlers.
"""

from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.app.db.models import (
    BotSettings,
    Broadcast,
    CartItem,
    Category,
    Customer,
    FAQ,
    Order,
    OrderItem,
    Product,
)
from shop_core.enums import OrderStatus


# ─── Customer ───────────────────────────────────────────────────────


class CustomerRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
    ) -> tuple[Customer, bool]:
        result = await self.session.execute(
            select(Customer).where(Customer.telegram_id == telegram_id)
        )
        customer = result.scalar_one_or_none()
        if customer:
            # Update profile fields
            customer.first_name = first_name or customer.first_name
            customer.last_name = last_name or customer.last_name
            customer.username = username or customer.username
            await self.session.commit()
            return customer, False

        customer = Customer(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        self.session.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer, True

    async def set_phone(self, telegram_id: int, phone: str) -> None:
        await self.session.execute(
            update(Customer)
            .where(Customer.telegram_id == telegram_id)
            .values(phone=phone)
        )
        await self.session.commit()

    async def get_all_ids(self) -> list[int]:
        """Get telegram_ids of real users only (those who shared their phone)."""
        result = await self.session.execute(
            select(Customer.telegram_id).where(Customer.phone != "")
        )
        return list(result.scalars().all())


# ─── Category ───────────────────────────────────────────────────────


class CategoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_root_categories(self) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active == True, Category.parent_id == None)  # noqa: E711, E712
            .order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def get_subcategories(self, parent_id: int) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active == True, Category.parent_id == parent_id)  # noqa: E712
            .order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()


# ─── Product ────────────────────────────────────────────────────────


class ProductRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_category(
        self, category_id: int, offset: int = 0, limit: int = 8
    ) -> tuple[list[Product], int]:
        # Total count
        count_q = select(func.count(Product.id)).where(
            Product.is_active == True, Product.category_id == category_id  # noqa: E712
        )
        total = (await self.session.execute(count_q)).scalar_one()

        # Items
        result = await self.session.execute(
            select(Product)
            .where(Product.is_active == True, Product.category_id == category_id)  # noqa: E712
            .options(selectinload(Product.images))
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id, Product.is_active == True)  # noqa: E712
            .options(selectinload(Product.images), selectinload(Product.category))
        )
        return result.scalar_one_or_none()


# ─── Cart ───────────────────────────────────────────────────────────


class CartRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_items(self, customer_id: int) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.customer_id == customer_id)
            .options(selectinload(CartItem.product).selectinload(Product.images))
        )
        return list(result.scalars().all())

    async def add_or_update(
        self, customer_id: int, product_id: int, delta: int = 1
    ) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.customer_id == customer_id,
                CartItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()

        if item:
            item.quantity = max(1, item.quantity + delta)
            await self.session.commit()
            return item

        if delta > 0:
            item = CartItem(
                customer_id=customer_id, product_id=product_id, quantity=delta
            )
            self.session.add(item)
            await self.session.commit()
            await self.session.refresh(item)
            return item
        return None

    async def set_quantity(
        self, customer_id: int, product_id: int, quantity: int
    ) -> None:
        if quantity <= 0:
            await self.remove_item(customer_id, product_id)
            return
        await self.session.execute(
            update(CartItem)
            .where(
                CartItem.customer_id == customer_id,
                CartItem.product_id == product_id,
            )
            .values(quantity=quantity)
        )
        await self.session.commit()

    async def remove_item(self, customer_id: int, product_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(
                CartItem.customer_id == customer_id,
                CartItem.product_id == product_id,
            )
        )
        await self.session.commit()

    async def clear(self, customer_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(CartItem.customer_id == customer_id)
        )
        await self.session.commit()

    async def get_total(self, customer_id: int) -> Decimal:
        items = await self.get_items(customer_id)
        return sum(item.product.price * item.quantity for item in items)


# ─── Order ──────────────────────────────────────────────────────────


class OrderRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_from_cart(
        self,
        customer: Customer,
        full_name: str,
        address: str,
        cart_items: list[CartItem],
    ) -> Order:
        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order(
            customer_id=customer.id,
            status=OrderStatus.AWAITING_PAYMENT,
            full_name=full_name,
            phone=customer.phone,
            address=address,
            total=total,
        )
        self.session.add(order)
        await self.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
            self.session.add(order_item)

        # Clear cart
        await self.session.execute(
            delete(CartItem).where(CartItem.customer_id == customer.id)
        )
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.customer))
        )
        return result.scalar_one_or_none()

    async def update_status(self, order_id: int, status: OrderStatus) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order:
            order.status = status.value
            await self.session.commit()
            await self.session.refresh(order)
        return order

    async def get_active_orders(self) -> list[Order]:
        active_statuses = [
            OrderStatus.PENDING,
            OrderStatus.AWAITING_PAYMENT,
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
        ]
        result = await self.session.execute(
            select(Order)
            .where(Order.status.in_([s.value for s in active_statuses]))
            .options(selectinload(Order.customer), selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())


# ─── FAQ ────────────────────────────────────────────────────────────


class FAQRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, query: str, limit: int = 10) -> list[FAQ]:
        stmt = select(FAQ).where(FAQ.is_active == True)  # noqa: E712
        if query:
            stmt = stmt.where(FAQ.question.ilike(f"%{query}%"))
        else:
            stmt = stmt.order_by(FAQ.popularity_score.desc())
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def increment_popularity(self, faq_id: int) -> None:
        await self.session.execute(
            update(FAQ).where(FAQ.id == faq_id).values(popularity_score=FAQ.popularity_score + 1)
        )
        await self.session.commit()


# ─── Bot Settings ───────────────────────────────────────────────────


class SettingsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> BotSettings | None:
        result = await self.session.execute(
            select(BotSettings).where(BotSettings.id == 1)
        )
        return result.scalar_one_or_none()


# ─── Broadcast ──────────────────────────────────────────────────────


class BroadcastRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, broadcast_id: int) -> Broadcast | None:
        result = await self.session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, broadcast_id: int, status: str) -> None:
        await self.session.execute(
            update(Broadcast).where(Broadcast.id == broadcast_id).values(status=status)
        )
        await self.session.commit()

    async def increment_sent(self, broadcast_id: int) -> None:
        await self.session.execute(
            update(Broadcast)
            .where(Broadcast.id == broadcast_id)
            .values(sent_count=Broadcast.sent_count + 1)
        )
        await self.session.commit()

    async def increment_error(self, broadcast_id: int) -> None:
        await self.session.execute(
            update(Broadcast)
            .where(Broadcast.id == broadcast_id)
            .values(error_count=Broadcast.error_count + 1)
        )
        await self.session.commit()
