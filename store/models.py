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
    
    def get_available_quantity(self):
        """Retourne la quantité disponible en tenant compte des réservations actives"""
        from django.db.models import Sum
        
        # Quantités réservées (non expirées)
        reserved = Order.objects.filter(
            product=self,
            ordered=False,
            reserved_until__gt=timezone.now()
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        return self.quantity - reserved
    
    def get_average_rating(self):
        """Calcule la note moyenne du produit"""
        from django.db.models import Avg
        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'], 1) if result['avg_rating'] else 0
    
    def get_rating_count(self):
        """Retourne le nombre total d'avis"""
        return self.reviews.count()
    
    def get_rating_distribution(self):
        """Retourne la distribution des notes (nombre d'avis par étoile)"""
        distribution = {i: 0 for i in range(1, 6)}
        for review in self.reviews.all():
            distribution[review.rating] += 1
        return distribution
    
    def get_stars_display(self):
        """Retourne une représentation visuelle de la note moyenne"""
        avg = self.get_average_rating()
        full_stars = int(avg)
        half_star = 1 if (avg - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        return {
            'full': full_stars,
            'half': half_star,
            'empty': empty_stars,
            'average': avg
        }




class Order(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)
    reserved_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    def is_reservation_expired(self):
        """Vérifie si la réservation est expirée"""
        if self.reserved_until and timezone.now() > self.reserved_until:
            return True
        return False
    
    def reserve_stock(self, minutes=15):
        """Réserve le stock pour cette commande pendant X minutes"""
        self.reserved_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()
    
    def release_reservation(self):
        """Libère la réservation de stock"""
        self.reserved_until = None
        self.save()
    
    def get_available_stock(self):
        """Retourne le stock disponible en tenant compte des réservations actives"""
        from django.db.models import Sum
        
        # Stock total du produit
        total_stock = self.product.quantity
        
        # Quantités réservées par d'autres commandes (non expirées)
        reserved = Order.objects.filter(
            product=self.product,
            ordered=False,
            reserved_until__gt=timezone.now()
        ).exclude(id=self.id).aggregate(total=Sum('quantity'))['total'] or 0
        
        return total_stock - reserved


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
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_history')
    user_email = models.EmailField(max_length=254, blank=True)  # Pour garder l'email même après suppression
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
    product_slug = models.SlugField(max_length=128, blank=True, default='')  # Pour lier à un produit existant
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def subtotal(self):
        return self.product_price * self.quantity
    
    def get_product(self):
        """Retourne le produit associé si il existe encore"""
        try:
            return Product.objects.get(slug=self.product_slug)
        except Product.DoesNotExist:
            return None
    
    def has_review(self):
        """Vérifie si l'utilisateur a déjà laissé un avis pour ce produit"""
        if not self.product_slug:
            return False
        return ProductReview.objects.filter(
            user=self.order_history.user,
            product__slug=self.product_slug
        ).exists()
    
    def get_review(self):
        """Retourne l'avis de l'utilisateur pour ce produit si il existe"""
        if not self.product_slug:
            return None
        try:
            return ProductReview.objects.get(
                user=self.order_history.user,
                product__slug=self.product_slug
            )
        except ProductReview.DoesNotExist:
            return None


class ProductReview(models.Model):
    """Avis et note pour un produit"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Note de 1 à 5 étoiles")
    title = models.CharField(max_length=200, verbose_name="Titre de l'avis")
    comment = models.TextField(verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_purchase = models.BooleanField(default=False, verbose_name="Achat vérifié")
    
    class Meta:
        verbose_name = "Avis produit"
        verbose_name_plural = "Avis produits"
        ordering = ['-created_at']
        # Un utilisateur ne peut laisser qu'un seul avis par produit
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}/5)"
    
    def get_stars_display(self):
        """Retourne une représentation visuelle des étoiles"""
        return '★' * self.rating + '☆' * (5 - self.rating)




