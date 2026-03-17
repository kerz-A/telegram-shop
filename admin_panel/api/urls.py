from django.urls import path

from api.views import (
    CartView,
    CategoryListView,
    OrderCreateView,
    OrderListView,
    ProductDetailView,
    ProductListView,
    ProfileView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("cart/", CartView.as_view(), name="cart"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
