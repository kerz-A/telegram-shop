"""
Telegram WebApp initData validation.
See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qs, unquote

from django.conf import settings
from rest_framework import authentication, exceptions

from shop.models import Customer

logger = logging.getLogger(__name__)

# initData is valid for 1 hour
INIT_DATA_EXPIRY_SECONDS = 3600


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Validate Telegram WebApp initData string.
    Returns parsed user data if valid, None otherwise.
    """
    try:
        parsed = parse_qs(init_data, keep_blank_values=True)

        # Extract hash
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Check auth_date expiry
        auth_date_str = parsed.get("auth_date", [None])[0]
        if not auth_date_str:
            return None

        auth_date = int(auth_date_str)
        if time.time() - auth_date > INIT_DATA_EXPIRY_SECONDS:
            logger.warning("initData expired: auth_date=%s", auth_date)
            return None

        # Build data-check-string: sorted key=value pairs excluding hash
        data_check_pairs = []
        for key in sorted(parsed.keys()):
            if key == "hash":
                continue
            value = parsed[key][0]
            data_check_pairs.append(f"{key}={value}")

        data_check_string = "\n".join(data_check_pairs)

        # Compute HMAC
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            logger.warning("initData hash mismatch")
            return None

        # Parse user data
        user_data_str = parsed.get("user", [None])[0]
        if not user_data_str:
            return None

        return json.loads(unquote(user_data_str))

    except Exception as e:
        logger.error("initData validation error: %s", e)
        return None


class TelegramWebAppAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication backend.
    Expects header: Authorization: tma <initData>
    """

    def authenticate_header(self, request):
        """Return string to trigger 401 instead of 403 for unauthenticated."""
        return "tma"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("tma "):
            return None

        init_data = auth_header[4:]
        user_data = validate_init_data(init_data, settings.BOT_TOKEN)
        if user_data is None:
            raise exceptions.AuthenticationFailed("Invalid Telegram initData")

        telegram_id = user_data.get("id")
        if not telegram_id:
            raise exceptions.AuthenticationFailed("No user id in initData")

        try:
            customer = Customer.objects.get(telegram_id=telegram_id)
        except Customer.DoesNotExist:
            customer = Customer.objects.create(
                telegram_id=telegram_id,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                username=user_data.get("username", ""),
            )

        return (customer, None)
