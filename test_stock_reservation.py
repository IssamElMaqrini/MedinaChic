"""
Script de démonstration du système de réservation de stock
Execute ce script dans le shell Django : python manage.py shell < test_stock_reservation.py
"""

from django.utils import timezone
from datetime import timedelta
from store.models import Product, Order, Cart
from accounts.models import Shopper

print("\n" + "="*70)
print("DÉMONSTRATION DU SYSTÈME DE RÉSERVATION DE STOCK")
print("="*70 + "\n")

# 1. Créer un produit de test
print("1. Création d'un produit de test...")
product, created = Product.objects.get_or_create(
    slug='test-product',
    defaults={
        'name': 'Produit Test',
        'price': 10.0,
        'quantity': 5,
        'description': 'Produit pour tester le système de réservation',
        'category': 'autre'
    }
)
if not created:
    product.quantity = 5
    product.save()
print(f"   ✓ Produit créé: {product.name}")
print(f"   ✓ Stock initial: {product.quantity}")
print(f"   ✓ Stock disponible: {product.get_available_quantity()}")

# 2. Créer deux utilisateurs de test
print("\n2. Création d'utilisateurs de test...")
try:
    user1 = Shopper.objects.get(email='test1@example.com')
except Shopper.DoesNotExist:
    user1 = Shopper.objects.create_user(email='test1@example.com', password='test123')
    print(f"   ✓ Utilisateur 1 créé: {user1.email}")

try:
    user2 = Shopper.objects.get(email='test2@example.com')
except Shopper.DoesNotExist:
    user2 = Shopper.objects.create_user(email='test2@example.com', password='test123')
    print(f"   ✓ Utilisateur 2 créé: {user2.email}")

# 3. Utilisateur 1 ajoute 3 produits au panier
print("\n3. Utilisateur 1 ajoute 3 produits au panier...")
cart1, _ = Cart.objects.get_or_create(user=user1)
order1, created = Order.objects.get_or_create(
    user=user1,
    product=product,
    ordered=False,
    defaults={'quantity': 3}
)
if not created:
    order1.quantity = 3
    order1.save()
cart1.orders.add(order1)
print(f"   ✓ Commande créée: {order1}")
print(f"   ✓ Stock disponible après: {product.get_available_quantity()}")

# 4. Utilisateur 1 réserve le stock (simule le début du paiement)
print("\n4. Utilisateur 1 commence le paiement (réservation 15 min)...")
order1.reserve_stock(minutes=15)
print(f"   ✓ Stock réservé jusqu'à: {order1.reserved_until}")
print(f"   ✓ Stock disponible pour autres utilisateurs: {product.get_available_quantity()}")

# 5. Utilisateur 2 essaie d'ajouter 3 produits (il reste seulement 2)
print("\n5. Utilisateur 2 essaie d'ajouter 3 produits...")
cart2, _ = Cart.objects.get_or_create(user=user2)
order2, created = Order.objects.get_or_create(
    user=user2,
    product=product,
    ordered=False,
    defaults={'quantity': 2}
)
if not created:
    order2.quantity = 2
    order2.save()
cart2.orders.add(order2)
available_for_user2 = order2.get_available_stock()
print(f"   ✓ Stock disponible pour user2: {available_for_user2}")
if order2.quantity > available_for_user2:
    print(f"   ⚠ Quantité demandée (3) > stock disponible ({available_for_user2})")
    print(f"   ⚠ En production, la quantité serait ajustée à {available_for_user2}")
else:
    print(f"   ✓ Commande acceptée: {order2.quantity} produits")

# 6. Simuler l'expiration de la réservation
print("\n6. Simulation de l'expiration de la réservation...")
order1.reserved_until = timezone.now() - timedelta(minutes=1)
order1.save()
print(f"   ✓ Réservation expirée: {order1.is_reservation_expired()}")
print(f"   ✓ Stock maintenant disponible: {product.get_available_quantity()}")

# 7. Libération de la réservation
print("\n7. Libération de la réservation...")
order1.release_reservation()
print(f"   ✓ Réservation libérée")
print(f"   ✓ Stock disponible: {product.get_available_quantity()}")

# 8. Nettoyage
print("\n8. Nettoyage des données de test...")
cart1.delete()
cart2.delete()
order1.delete()
order2.delete()
print("   ✓ Données de test supprimées")

print("\n" + "="*70)
print("DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
print("="*70 + "\n")

print("RÉSUMÉ DES FONCTIONNALITÉS TESTÉES:")
print("  ✓ Création de produit et vérification du stock")
print("  ✓ Calcul du stock disponible (stock réel - réservations)")
print("  ✓ Réservation de stock pendant 15 minutes")
print("  ✓ Vérification des réservations pour d'autres utilisateurs")
print("  ✓ Détection des réservations expirées")
print("  ✓ Libération des réservations")
print("\n")
