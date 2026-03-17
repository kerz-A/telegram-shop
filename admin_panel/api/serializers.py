from rest_framework import serializers

from shop.models import (
    CartItem,
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
    ProductImage,
)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "sort_order"]


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "children", "product_count"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "category_name", "first_image"]

    def get_first_image(self, obj):
        img = obj.images.first()
        if img:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(img.image.url)
            return img.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail view."""

    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price",
            "category", "category_name", "images", "created_at",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "total"]


class CartItemUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)


class OrderItemSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "price", "quantity", "total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "status", "status_display", "full_name",
            "phone", "address", "total", "items", "created_at",
        ]


class CreateOrderSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    address = serializers.CharField()

    def validate(self, attrs):
        customer = self.context.get("customer")
        if not customer:
            raise serializers.ValidationError("Customer not found")
        if not customer.cart_items.exists():
            raise serializers.ValidationError("Корзина пуста")
        return attrs


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["telegram_id", "username", "first_name", "phone"]
        read_only_fields = ["telegram_id"]
