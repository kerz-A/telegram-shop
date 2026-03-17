from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        labels = {
            "pending": "⏳ Ожидает",
            "awaiting_payment": "💳 Ожидает оплаты",
            "paid": "✅ Оплачен",
            "processing": "📦 Собирается",
            "shipped": "🚚 Отправлен",
            "delivered": "🎉 Доставлен",
            "cancelled": "❌ Отменён",
        }
        return labels.get(self.value, self.value)


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SENDING = "sending"
    SENT = "sent"

    @property
    def label(self) -> str:
        labels = {
            "draft": "Черновик",
            "ready": "Готово к отправке",
            "sending": "Отправляется",
            "sent": "Отправлено",
        }
        return labels.get(self.value, self.value)
