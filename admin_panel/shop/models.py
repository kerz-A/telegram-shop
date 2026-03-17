from django.db import models
from django.core.validators import MinValueValidator

from shop_core.enums import OrderStatus, BroadcastStatus


class Customer(models.Model):
    """Telegram user / shop customer."""

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, blank=True, default="")
    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        ordering = ["-created_at"]
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.first_name} (@{self.username})" if self.username else f"{self.first_name} [{self.telegram_id}]"


class Category(models.Model):
    """Product category with optional nesting."""

    name = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родительская категория",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        ordering = ["sort_order", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Product(models.Model):
    """Shop product."""

    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, default="", verbose_name="Описание")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Цена",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.name} — {self.price}₽"

    @property
    def first_image_url(self) -> str | None:
        img = self.images.first()
        return img.image.url if img else None


class ProductImage(models.Model):
    """Product photo (multiple per product)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
    )
    image = models.ImageField(upload_to="products/%Y/%m/", verbose_name="Изображение")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        db_table = "product_images"
        ordering = ["sort_order"]
        verbose_name = "Фото товара"
        verbose_name_plural = "Фото товаров"

    def __str__(self):
        return f"Фото #{self.sort_order} — {self.product.name}"


class CartItem(models.Model):
    """Shopping cart item (shared between bot and webapp)."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Клиент",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cart_items"
        unique_together = ["customer", "product"]
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Корзина"

    def __str__(self):
        return f"{self.customer} — {self.product.name} x{self.quantity}"

    @property
    def total(self):
        if self.product and self.quantity:
            return self.product.price * self.quantity
        return None


class Order(models.Model):
    """Customer order."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Клиент",
    )
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.label) for s in OrderStatus],
        default=OrderStatus.PENDING,
        verbose_name="Статус",
    )
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адрес доставки")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итого")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.pk} — {self.get_status_display()} — {self.total}₽"


class OrderItem(models.Model):
    """Single line item in an order (price frozen at order time)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Товар",
    )
    product_name = models.CharField(max_length=255, verbose_name="Название товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за шт.")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        db_table = "order_items"
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total(self):
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return None


class FAQ(models.Model):
    """Frequently asked questions for inline query."""

    question = models.CharField(max_length=512, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    popularity_score = models.PositiveIntegerField(default=0, verbose_name="Популярность")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "faq"
        ordering = ["-popularity_score"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def __str__(self):
        return self.question[:80]


class BotSettings(models.Model):
    """Singleton model for bot configuration managed via admin."""

    required_channels = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Каналы для обязательной подписки",
        help_text='Список username каналов, например: ["@channel1", "@channel2"]',
    )
    admin_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="ID админ-чата",
        help_text="Telegram ID группы для уведомлений о заказах",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bot_settings"
        verbose_name = "Настройки бота"
        verbose_name_plural = "Настройки бота"

    def __str__(self):
        return "Настройки бота"

    def save(self, *args, **kwargs):
        # Singleton pattern: always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Broadcast(models.Model):
    """Marketing broadcast message."""

    text = models.TextField(verbose_name="Текст рассылки")
    image = models.ImageField(
        upload_to="broadcasts/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Изображение",
    )
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.label) for s in BroadcastStatus],
        default=BroadcastStatus.DRAFT,
        verbose_name="Статус",
    )
    sent_count = models.PositiveIntegerField(default=0, verbose_name="Доставлено")
    error_count = models.PositiveIntegerField(default=0, verbose_name="Ошибок")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "broadcasts"
        ordering = ["-created_at"]
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

    def __str__(self):
        return f"Рассылка #{self.pk} — {self.get_status_display()}"
