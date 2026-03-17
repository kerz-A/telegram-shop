import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telegram_id", models.BigIntegerField(db_index=True, unique=True)),
                ("username", models.CharField(blank=True, default="", max_length=255)),
                ("first_name", models.CharField(blank=True, default="", max_length=255)),
                ("last_name", models.CharField(blank=True, default="", max_length=255)),
                ("phone", models.CharField(blank=True, default="", max_length=20)),
                ("is_admin", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Клиент",
                "verbose_name_plural": "Клиенты",
                "db_table": "customers",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="shop.category",
                        verbose_name="Родительская категория",
                    ),
                ),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "db_table": "categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("description", models.TextField(blank=True, default="", verbose_name="Описание")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.01)],
                        verbose_name="Цена",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="shop.category",
                        verbose_name="Категория",
                    ),
                ),
            ],
            options={
                "verbose_name": "Товар",
                "verbose_name_plural": "Товары",
                "db_table": "products",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="products/%Y/%m/", verbose_name="Изображение")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="shop.product",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Фото товара",
                "verbose_name_plural": "Фото товаров",
                "db_table": "product_images",
                "ordering": ["sort_order"],
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="shop.customer",
                        verbose_name="Клиент",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="shop.product",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Позиция корзины",
                "verbose_name_plural": "Корзина",
                "db_table": "cart_items",
                "unique_together": {("customer", "product")},
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "⏳ Ожидает"),
                            ("awaiting_payment", "💳 Ожидает оплаты"),
                            ("paid", "✅ Оплачен"),
                            ("processing", "📦 Собирается"),
                            ("shipped", "🚚 Отправлен"),
                            ("delivered", "🎉 Доставлен"),
                            ("cancelled", "❌ Отменён"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("full_name", models.CharField(max_length=255, verbose_name="ФИО")),
                ("phone", models.CharField(max_length=20, verbose_name="Телефон")),
                ("address", models.TextField(verbose_name="Адрес доставки")),
                ("total", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Итого")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="shop.customer",
                        verbose_name="Клиент",
                    ),
                ),
            ],
            options={
                "verbose_name": "Заказ",
                "verbose_name_plural": "Заказы",
                "db_table": "orders",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=255, verbose_name="Название товара")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Цена за шт.")),
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="shop.order",
                        verbose_name="Заказ",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="shop.product",
                        verbose_name="Товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "Позиция заказа",
                "verbose_name_plural": "Позиции заказа",
                "db_table": "order_items",
            },
        ),
        migrations.CreateModel(
            name="FAQ",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.CharField(max_length=512, verbose_name="Вопрос")),
                ("answer", models.TextField(verbose_name="Ответ")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("popularity_score", models.PositiveIntegerField(default=0, verbose_name="Популярность")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "FAQ",
                "verbose_name_plural": "FAQ",
                "db_table": "faq",
                "ordering": ["-popularity_score"],
            },
        ),
        migrations.CreateModel(
            name="BotSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "required_channels",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='Список username каналов, например: ["@channel1", "@channel2"]',
                        verbose_name="Каналы для обязательной подписки",
                    ),
                ),
                (
                    "admin_chat_id",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Telegram ID группы для уведомлений о заказах",
                        null=True,
                        verbose_name="ID админ-чата",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Настройки бота",
                "verbose_name_plural": "Настройки бота",
                "db_table": "bot_settings",
            },
        ),
        migrations.CreateModel(
            name="Broadcast",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="Текст рассылки")),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="broadcasts/%Y/%m/", verbose_name="Изображение"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Черновик"),
                            ("ready", "Готово к отправке"),
                            ("sending", "Отправляется"),
                            ("sent", "Отправлено"),
                        ],
                        default="draft",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("sent_count", models.PositiveIntegerField(default=0, verbose_name="Доставлено")),
                ("error_count", models.PositiveIntegerField(default=0, verbose_name="Ошибок")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Рассылка",
                "verbose_name_plural": "Рассылки",
                "db_table": "broadcasts",
                "ordering": ["-created_at"],
            },
        ),
    ]
