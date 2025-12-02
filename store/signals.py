from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Product, StockAlert


@receiver(post_save, sender=Product)
def check_stock_alerts(sender, instance, **kwargs):
    """
    Signal qui se déclenche quand un produit est mis à jour.
    Si le stock passe de 0 à >0, notifie tous les utilisateurs en attente.
    """
    if instance.quantity > 0:
        # Récupérer toutes les alertes non notifiées pour ce produit
        alerts = StockAlert.objects.filter(
            product=instance,
            notified=False
        )
        
        if alerts.exists():
            # Marquer les alertes comme notifiées
            alerts.update(
                notified=True,
                notified_at=timezone.now()
            )
