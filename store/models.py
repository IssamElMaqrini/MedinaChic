from django.db import models
from django.template.defaultfilters import slugify
from django.templatetags.static import static
from django.urls.base import reverse
from django.utils import timezone

from MedinaChic.settings import AUTH_USER_MODEL


class Product(models.Model):
    name = models.CharField(max_length=128)
    name_nl = models.CharField(max_length=128, blank=True, null=True)
    slug = models.SlugField(max_length=128, blank=True)
    CATEGORIES = [
        ('autre', 'Autre'),
        ('cuisine', 'Cuisine'),
        ('vetement', 'Vetement'),
        ('tissu', 'Tissu'),
        ('argile', 'Argile'),
        ('maroquineire', 'Maroquineire'),
        ('alimentaire', 'Alimentaire'),
        ('accessoire', 'Accessoire'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORIES, default='autre')
    price = models.FloatField(default=0.0)
    quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    description_nl = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to="products/", blank=True, null=True)
    stripe_id = models.CharField(max_length=90, blank=True)

    def __str__(self):
        return f"{self.name} ({self.quantity})"

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)

    def thumbnail_url(self):
        return self.thumbnail.url if self.thumbnail else static("img/logo-bleu.jpg")




class Order(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


class Cart(models.Model):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    orders = models.ManyToManyField(Order)
    ordered = models.BooleanField(default=False)
    ordered_date = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return f"Cart for {self.user.email}"

    def delete(self, *args, **kwargs):
        for order in self.orders.all():
            order.ordered = True
            order.ordered_date = timezone.now()
            order.save()

        self.orders.clear()
        super().delete(*args, **kwargs)


class OrderHistory(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_history')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField(default=0.0)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Order by {self.user.email} on {self.order_date.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name_plural = "Order Histories"
        ordering = ['-order_date']


class OrderHistoryItem(models.Model):
    order_history = models.ForeignKey(OrderHistory, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=128)
    product_price = models.FloatField()
    quantity = models.IntegerField()
    product_thumbnail = models.CharField(max_length=255, blank=True, default='')
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def subtotal(self):
        return self.product_price * self.quantity




