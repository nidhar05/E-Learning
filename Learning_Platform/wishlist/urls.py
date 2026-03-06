from django.urls import path
from .views import WishlistListCreateView

urlpatterns = [
    path('', WishlistListCreateView.as_view(), name='wishlist-list-create'),
]
