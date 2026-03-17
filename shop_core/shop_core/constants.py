"""Shared constants between services."""

# Webhook actions
ACTION_ORDER_STATUS_CHANGED = "order_status_changed"
ACTION_START_BROADCAST = "start_broadcast"

# Pagination
PRODUCTS_PER_PAGE = 8
CATEGORIES_PER_PAGE = 8

# Rate limiting for broadcasts (messages per second)
BROADCAST_RATE_LIMIT = 25

# Bot settings cache TTL (seconds)
SETTINGS_CACHE_TTL = 60
