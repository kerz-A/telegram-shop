from pathlib import Path

from aiogram.types import FSInputFile, InputMediaPhoto

from bot.app.db.models import Product

# Media root inside container (shared volume with Django)
MEDIA_ROOT = Path("/app/admin_panel/media")


def build_product_media_group(product: Product) -> list[InputMediaPhoto]:
    """
    Build a MediaGroup from product images.
    First photo gets the caption with product details.
    """
    images = sorted(product.images, key=lambda img: img.sort_order)
    if not images:
        return []

    caption = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"💰 <b>{product.price}₽</b>"
    )

    media_group = []
    for i, img in enumerate(images):
        photo_path = MEDIA_ROOT / img.image
        if not photo_path.exists():
            continue

        media_group.append(
            InputMediaPhoto(
                media=FSInputFile(photo_path),
                caption=caption if i == 0 else None,
                parse_mode="HTML" if i == 0 else None,
            )
        )

    return media_group
