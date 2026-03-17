from aiogram.filters.callback_data import CallbackData


class CategoryCB(CallbackData, prefix="cat"):
    action: str  # "show" | "back"
    id: int = 0
    page: int = 0


class ProductCB(CallbackData, prefix="prod"):
    action: str  # "show" | "list"
    id: int = 0
    cat_id: int = 0
    page: int = 0


class CartCB(CallbackData, prefix="cart"):
    action: str  # "add" | "plus" | "minus" | "remove" | "clear" | "show"
    product_id: int = 0


class OrderCB(CallbackData, prefix="order"):
    action: str  # "confirm" | "paid" | "cancel"
    order_id: int = 0


class AdminOrderCB(CallbackData, prefix="adm_ord"):
    action: str  # status values: paid, processing, shipped, delivered, cancelled
    order_id: int = 0


class PaginationCB(CallbackData, prefix="page"):
    target: str  # "products" | "categories"
    id: int = 0
    page: int = 0
