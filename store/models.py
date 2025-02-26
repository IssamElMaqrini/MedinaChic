from django.db import models
from django.urls.base import reverse


class Product(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    price = models.FloatField(default=0.0)
    quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.quantity})"

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})



