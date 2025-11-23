
from django.urls import path
from .views import (
    ProductListCreate,
    ProductDetail,
    ActiveCartView,
    CheckoutStub,
    OrdersView,
    OrderDetailView
)
urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/<uuid:pk>/', ProductDetail.as_view()),
    path('carts/active/', ActiveCartView.as_view()),
    path('carts/checkout/', CheckoutStub.as_view()),
    path("orders/", OrdersView.as_view(), name="orders-list-create"),
    path("orders/<uuid:pk>/", OrderDetailView.as_view(), name="orders-detail"),
]
