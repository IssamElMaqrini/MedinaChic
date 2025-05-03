from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'name_nl', 'slug', 'category', 'price', 'quantity', 'description', 'description_nl', 'thumbnail_url']
