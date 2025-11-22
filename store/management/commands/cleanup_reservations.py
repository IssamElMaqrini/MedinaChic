"""
Management command pour nettoyer les réservations de stock expirées.

Usage:
    python manage.py cleanup_reservations

Pour automatiser avec Windows Task Scheduler ou un cron job Unix:
    Exécuter cette commande toutes les 5-10 minutes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import Order, Cart


class Command(BaseCommand):
    help = 'Nettoie les réservations de stock expirées et ajuste les paniers'

    def handle(self, *args, **options):
        # Trouver les commandes avec réservations expirées
        expired_orders = Order.objects.filter(
            ordered=False,
            reserved_until__lt=timezone.now(),
            reserved_until__isnull=False
        )
        
        count_expired = expired_orders.count()
        
        if count_expired == 0:
            self.stdout.write(self.style.SUCCESS('Aucune réservation expirée trouvée.'))
            return
        
        carts_to_check = set()
        orders_adjusted = 0
        orders_deleted = 0
        
        for order in expired_orders:
            # Libérer la réservation
            order.reserved_until = None
            order.save()
            
            # Vérifier si le stock est toujours disponible
            if order.product.quantity < order.quantity:
                if order.product.quantity > 0:
                    # Ajuster la quantité
                    old_qty = order.quantity
                    order.quantity = order.product.quantity
                    order.save()
                    orders_adjusted += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Commande #{order.id} ajustée: {old_qty} → {order.quantity} '
                            f'pour {order.product.name}'
                        )
                    )
                else:
                    # Supprimer la commande
                    product_name = order.product.name
                    cart = order.user.cart
                    carts_to_check.add(cart.id)
                    order.delete()
                    orders_deleted += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Commande supprimée: {product_name} (rupture de stock)'
                        )
                    )
        
        # Supprimer les paniers vides
        carts_deleted = 0
        for cart_id in carts_to_check:
            try:
                cart = Cart.objects.get(id=cart_id)
                if cart.orders.count() == 0:
                    cart.delete()
                    carts_deleted += 1
            except Cart.DoesNotExist:
                pass
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nNettoyage terminé:\n'
                f'  - {count_expired} réservations expirées libérées\n'
                f'  - {orders_adjusted} commandes ajustées\n'
                f'  - {orders_deleted} commandes supprimées\n'
                f'  - {carts_deleted} paniers vides supprimés'
            )
        )
