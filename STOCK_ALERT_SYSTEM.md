# Système de Notification de Retour en Stock

## Description

Ce système permet aux utilisateurs connectés de s'inscrire pour recevoir une notification automatique lorsqu'un produit en rupture de stock redevient disponible.

## Fonctionnalités

### 1. Inscription aux Alertes

- Sur la page d'un produit en rupture de stock, un bouton "Me notifier du retour en stock" (FR) / "Breng me op de hoogte bij terugkeer in voorraad" (NL) est affiché
- L'utilisateur doit être connecté pour s'inscrire
- Un utilisateur ne peut avoir qu'une seule alerte active par produit
- Si une alerte existante a déjà été notifiée, elle est réactivée automatiquement

### 2. Détection Automatique

- Un signal Django (`post_save`) surveille les modifications du modèle `Product`
- Quand le stock d'un produit passe de 0 à une valeur positive, toutes les alertes actives sont marquées comme "notifiées"
- Le système enregistre l'horodatage de la notification

### 3. Affichage des Popups

- À chaque chargement de page, un script JavaScript vérifie s'il y a des alertes en attente pour l'utilisateur connecté
- Si des alertes sont trouvées, des popups modales Bootstrap s'affichent automatiquement
- Chaque popup contient :
  - L'image du produit
  - Le nom du produit
  - Un message de confirmation
  - Un bouton pour accéder directement à la page du produit
- Les alertes sont supprimées après avoir été affichées (pour ne pas les montrer plusieurs fois)

### 4. Vérification en Temps Réel

- Le script vérifie également les nouvelles alertes toutes les 30 secondes
- Permet d'afficher les notifications même si l'utilisateur reste sur la même page

## Architecture Technique

### Modèle de Données

```python
class StockAlert(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
```

- **Contrainte unique** : `unique_together = ['product', 'user']`
  - Un utilisateur ne peut avoir qu'une seule alerte par produit

### Fichiers Modifiés

1. **store/models.py** : Ajout du modèle `StockAlert`
2. **store/signals.py** : Signal pour détecter les mises à jour de stock
3. **store/apps.py** : Enregistrement du signal
4. **store/views.py** : 
   - `subscribe_stock_alert()` : Inscription aux alertes (FR)
   - `subscribe_stock_alert_nl()` : Inscription aux alertes (NL)
   - `check_stock_alerts()` : API pour récupérer les alertes (FR)
   - `check_stock_alerts_nl()` : API pour récupérer les alertes (NL)
5. **store/urls.py** : Routes pour les nouvelles vues
6. **store/admin.py** : Interface d'administration pour gérer les alertes
7. **store/templates/store/detail.html** : Bouton d'inscription (FR)
8. **store/templates/store/detail_nl.html** : Bouton d'inscription (NL)
9. **templates/base.html** : Script JavaScript de vérification et popup (FR)
10. **templates/base_nl.html** : Script JavaScript de vérification et popup (NL)

### Routes URL

- `/store/product/<slug>/stock-alert/` : S'inscrire à une alerte (FR)
- `/store/nl/product/<slug>/stock-alert/` : S'inscrire à une alerte (NL)
- `/store/check-stock-alerts/` : API pour vérifier les alertes (FR)
- `/store/nl/check-stock-alerts/` : API pour vérifier les alertes (NL)

## Utilisation

### Pour les Utilisateurs

1. Visitez la page d'un produit en rupture de stock
2. Cliquez sur le bouton "Me notifier du retour en stock"
3. Un message de confirmation s'affiche
4. Lorsque l'admin met à jour le stock du produit, un popup apparaîtra automatiquement lors de votre prochaine navigation sur le site

### Pour les Administrateurs

1. Connectez-vous à l'interface d'administration Django
2. Accédez à la section "Alertes de stock"
3. Vous pouvez voir toutes les alertes actives et leur statut
4. Lorsque vous mettez à jour le stock d'un produit (via l'admin), les alertes sont automatiquement déclenchées

## Design

- Les boutons d'alerte utilisent la classe Bootstrap `btn-outline-warning` avec une icône de cloche
- Les popups utilisent les couleurs du site :
  - En-tête : dégradé rouge/or (`#872D37` → `#C78C3A`)
  - Bouton principal : même dégradé
- Les popups sont centrées et responsive

## Points Techniques Importants

1. **Sécurité** : Toutes les vues nécessitent une authentification (`@login_required`)
2. **Performance** : Les requêtes utilisent `select_related('product')` pour optimiser les requêtes SQL
3. **UX** : Les alertes sont supprimées après affichage pour éviter les doublons
4. **Compatibilité** : Fonctionne sur les versions FR et NL du site
5. **Temps réel** : Vérification automatique toutes les 30 secondes

## Améliorations Futures Possibles

- Envoyer des emails en plus des notifications popup
- Ajouter un panneau dans le profil utilisateur pour gérer toutes ses alertes
- Statistiques sur les alertes les plus demandées
- Notifications push via service workers
- Limite du nombre d'alertes par utilisateur
