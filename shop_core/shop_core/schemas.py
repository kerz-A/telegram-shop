from __future__ import annotations

from pydantic import BaseModel

from shop_core.enums import OrderStatus


class OrderNotification(BaseModel):
    """Django → Bot: notify user about order status change."""

    order_id: int
    customer_telegram_id: int
    new_status: OrderStatus
    message: str | None = None


class BroadcastRequest(BaseModel):
    """Django → Bot: start a broadcast."""

    broadcast_id: int
    text: str
    image_path: str | None = None


class WebhookPayload(BaseModel):
    """Generic wrapper for webhook calls."""

    action: str  # "order_status_changed" | "start_broadcast"
    data: dict
