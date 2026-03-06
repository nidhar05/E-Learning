from django.shortcuts import render
from rest_framework import generics
from .models import Wishlist
from .serializers import WishlistSerializer

class WishlistListCreateView(generics.ListCreateAPIView):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer