from django.db.models import Count, Q
from rest_framework import generics, status, views
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from api.auth import TelegramWebAppAuthentication
from shop.models import CartItem, Category, Order, OrderItem, Product, Customer
from shop_core.enums import OrderStatus

from api.serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    CategorySerializer,
    CreateOrderSerializer,
    CustomerProfileSerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class TelegramAuthMixin:
    """Require Telegram WebApp authentication."""

    authentication_classes = [TelegramWebAppAuthentication]

    @property
    def customer(self):
        user = self.request.user
        if not isinstance(user, Customer):
            raise NotAuthenticated("Требуется авторизация через Telegram Mini App")
        return user


# ─── Categories ─────────────────────────────────────────────────────


class CategoryListView(generics.ListAPIView):
    """Public: list root categories with product counts."""

    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = []
    pagination_class = None  # Return plain array, not paginated

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True, parent__isnull=True)
            .annotate(product_count=Count("products", filter=Q(products__is_active=True)))
            .order_by("sort_order", "name")
        )


# ─── Products ───────────────────────────────────────────────────────


class ProductListView(generics.ListAPIView):
    """Public: list products with optional category and search filters."""

    serializer_class = ProductListSerializer
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(
                Q(category_id=category_id) | Q(category__parent_id=category_id)
            )

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs


class ProductDetailView(generics.RetrieveAPIView):
    """Public: product detail with all images."""

    serializer_class = ProductDetailSerializer
    authentication_classes = []
    permission_classes = []
    queryset = Product.objects.filter(is_active=True).prefetch_related("images")


# ─── Cart ───────────────────────────────────────────────────────────


class CartView(TelegramAuthMixin, views.APIView):
    """Get cart contents or update cart."""

    def get(self, request):
        items = CartItem.objects.filter(customer=self.customer).select_related(
            "product", "product__category"
        ).prefetch_related("product__images")
        serializer = CartItemSerializer(items, many=True, context={"request": request})

        total = sum(item.total for item in items)
        return Response({"items": serializer.data, "total": str(total)})

    def post(self, request):
        """Add/update item in cart. quantity=0 removes item."""
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        if quantity == 0:
            CartItem.objects.filter(customer=self.customer, product=product).delete()
            return Response({"status": "removed"})

        cart_item, created = CartItem.objects.update_or_create(
            customer=self.customer,
            product=product,
            defaults={"quantity": quantity},
        )
        return Response(
            CartItemSerializer(cart_item, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        """Clear entire cart."""
        CartItem.objects.filter(customer=self.customer).delete()
        return Response({"status": "cleared"})


# ─── Orders ─────────────────────────────────────────────────────────


class OrderListView(TelegramAuthMixin, generics.ListAPIView):
    """List customer's orders."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(customer=self.customer).prefetch_related("items")


class OrderCreateView(TelegramAuthMixin, views.APIView):
    """Create order from cart contents."""

    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data, context={"customer": self.customer}
        )
        serializer.is_valid(raise_exception=True)

        cart_items = CartItem.objects.filter(
            customer=self.customer
        ).select_related("product")

        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            customer=self.customer,
            full_name=serializer.validated_data["full_name"],
            phone=self.customer.phone,
            address=serializer.validated_data["address"],
            total=total,
            status=OrderStatus.AWAITING_PAYMENT,
        )

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)

        # Clear cart
        cart_items.delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# ─── Profile ────────────────────────────────────────────────────────


class ProfileView(TelegramAuthMixin, views.APIView):
    """Get current customer profile."""

    def get(self, request):
        serializer = CustomerProfileSerializer(self.customer)
        return Response(serializer.data)
