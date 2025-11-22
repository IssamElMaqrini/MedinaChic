# Système de Gestion de Stock avec Réservations

## Fonctionnalités Implémentées

### 1. Vérification de Stock lors de l'Ajout au Panier
- Le système vérifie automatiquement la disponibilité du stock avant d'ajouter un produit
- Messages d'avertissement si le produit est en rupture de stock
- Bouton "Ajouter au panier" désactivé si le stock est à 0

### 2. Validation de Stock lors de la Modification des Quantités
- Lorsqu'un utilisateur modifie la quantité dans son panier, le système vérifie le stock disponible
- Les quantités sont automatiquement ajustées si le stock est insuffisant
- Les produits sont retirés du panier si le stock est à 0
- Messages informatifs pour chaque ajustement

### 3. Réservation de Stock pendant le Paiement (15 minutes)
- Dès qu'un utilisateur clique sur "Procéder au paiement", le stock est réservé pour 15 minutes
- Pendant cette période, d'autres clients ne peuvent pas acheter la quantité réservée
- La réservation est automatiquement libérée si :
  - L'utilisateur annule le paiement
  - Les 15 minutes expirent sans achat
  - Le paiement est complété avec succès

### 4. Validation Finale avant Paiement
- Juste avant de créer la session Stripe, le système vérifie une dernière fois le stock
- Si le stock a changé depuis l'ajout au panier :
  - Les quantités sont ajustées automatiquement
  - Les produits épuisés sont retirés du panier
  - L'utilisateur est redirigé vers son panier avec des messages explicatifs

### 5. Nettoyage Automatique des Réservations Expirées
- Le système nettoie automatiquement les réservations expirées à chaque consultation du panier
- Une commande de gestion est disponible pour un nettoyage périodique via cron/scheduler

## Nouveaux Champs de Modèle

### Order
- `reserved_until` (DateTimeField) : Timestamp de fin de réservation

## Nouvelles Méthodes

### Model Order
- `is_reservation_expired()` : Vérifie si la réservation est expirée
- `reserve_stock(minutes=15)` : Réserve le stock pour X minutes
- `release_reservation()` : Libère la réservation
- `get_available_stock()` : Retourne le stock disponible en tenant compte des réservations actives

### Model Product
- `get_available_quantity()` : Retourne la quantité disponible après réservations

## Nouvelles Vues

### checkout_cancelled
- URL : `/store/cart/cancelled`
- Gère l'annulation du paiement Stripe
- Libère les réservations de stock

### cleanup_expired_reservations (fonction utilitaire)
- Nettoie les réservations expirées
- Ajuste ou supprime les commandes selon le stock disponible
- Appelée automatiquement lors de l'affichage du panier

## Commande de Gestion

### cleanup_reservations
```bash
python manage.py cleanup_reservations
```
- Nettoie toutes les réservations expirées dans la base de données
- Recommandé de l'exécuter toutes les 5-10 minutes via un scheduler

**Configuration Windows Task Scheduler :**
1. Ouvrir "Planificateur de tâches"
2. Créer une tâche de base
3. Déclencheur : "Répéter toutes les 10 minutes"
4. Action : Démarrer un programme
   - Programme : `C:\Users\EL Maqrini\Documents\projetDjango\MedinaChic\.venv\Scripts\python.exe`
   - Arguments : `manage.py cleanup_reservations`
   - Répertoire de démarrage : `C:\Users\EL Maqrini\Documents\projetDjango\MedinaChic`

## Messages Utilisateur

### Messages de Succès (vert)
- "'{product_name}' a été ajouté à votre panier."
- "Quantité mise à jour pour '{product_name}'."

### Messages d'Avertissement (orange)
- "Le produit '{product_name}' n'est plus disponible en stock."
- "Impossible d'ajouter plus de '{product_name}' au panier. Stock insuffisant."
- "Quantité de '{product_name}' ajustée à {available} (stock limité)."
- "'{product_name}' retiré du panier (rupture de stock)."

### Messages d'Erreur (rouge)
- "Stock insuffisant pour '{product_name}'. Disponible: {available}, Demandé: {requested}"
- "Votre panier est vide suite à des ruptures de stock."

### Messages d'Information (bleu)
- "Paiement annulé. Vos articles sont toujours dans le panier."
- "Veuillez vérifier votre panier avant de continuer."
- Lors du paiement : "Lors du paiement, vos articles seront réservés pendant 15 minutes."

## Flux de Fonctionnement

### Scénario 1 : Ajout au panier
1. Utilisateur clique sur "Ajouter au panier"
2. Système vérifie le stock disponible (total - réservations actives)
3. Si stock disponible : ajout au panier + message de succès
4. Si stock insuffisant : message d'avertissement

### Scénario 2 : Modification de quantité dans le panier
1. Utilisateur change la quantité et clique sur "Mettre à jour"
2. Système nettoie les réservations expirées
3. Système calcule le stock disponible
4. Si stock suffisant : mise à jour + message de succès
5. Si stock insuffisant : ajustement automatique + message d'avertissement
6. Si stock = 0 : suppression du produit + message

### Scénario 3 : Procéder au paiement
1. Utilisateur clique sur "Procéder au paiement"
2. Système nettoie les réservations expirées
3. Validation finale du stock pour tous les articles
4. Ajustements automatiques si nécessaire
5. Si panier valide : réservation du stock pour 15 minutes
6. Redirection vers Stripe

### Scénario 4 : Paiement annulé
1. Utilisateur clique sur "Annuler" sur Stripe
2. Redirection vers `/store/cart/cancelled`
3. Libération de toutes les réservations
4. Redirection vers le panier avec message

### Scénario 5 : Réservation expirée
1. 15 minutes passent sans paiement
2. Lors de la prochaine consultation du panier (ou via cron) :
   - Réservations libérées
   - Stock recalculé
   - Ajustements automatiques si nécessaire

## Tests Recommandés

1. **Test de stock insuffisant** : Essayer d'ajouter une quantité supérieure au stock
2. **Test de réservation** : Deux utilisateurs essayant d'acheter le même produit simultanément
3. **Test d'expiration** : Commencer un paiement, attendre 15+ minutes, puis vérifier le panier
4. **Test d'annulation** : Commencer un paiement puis annuler sur Stripe
5. **Test de modification** : Modifier les quantités avec un stock limité

## Notes Techniques

- Les réservations utilisent `timezone.now()` pour être timezone-aware
- Le système utilise Django's messages framework pour les notifications
- Les réservations sont vérifiées à plusieurs points critiques du parcours utilisateur
- La commande de nettoyage peut être exécutée en parallèle sans risque de conflit
