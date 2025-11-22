# Système d'Avis et de Notes Produits

## Vue d'ensemble

Ce système permet aux utilisateurs qui ont acheté un produit de laisser un avis et une note (1 à 5 étoiles). Les avis sont affichés sur les pages de détail des produits avec une moyenne des notes et une distribution visuelle.

## Fonctionnalités Implémentées

### 1. **Modèle ProductReview**
- Note de 1 à 5 étoiles
- Titre de l'avis (200 caractères max)
- Commentaire détaillé
- Badge "Achat vérifié" pour les achats confirmés
- Dates de création et modification
- **Contrainte unique** : Un utilisateur ne peut laisser qu'un seul avis par produit

### 2. **Ajout d'Avis depuis "Mes Commandes"**
- Bouton "⭐ Donner un avis" pour chaque produit acheté
- Bouton "✏️ Modifier l'avis" si un avis existe déjà
- Vérification automatique que l'utilisateur a acheté le produit
- Formulaire intuitif avec sélection d'étoiles interactive

### 3. **Affichage des Avis sur les Pages Produit**
- **Résumé** : Note moyenne + nombre d'avis
- **Distribution** : Graphique en barres montrant la répartition des notes
- **Liste des avis** : Tous les avis avec dates et badges "Achat vérifié"
- **Actions utilisateur** : Modifier ou supprimer ses propres avis

### 4. **Méthodes du Modèle Product**
- `get_average_rating()` : Calcule la note moyenne
- `get_rating_count()` : Nombre total d'avis
- `get_rating_distribution()` : Distribution des notes par étoile
- `get_stars_display()` : Affichage visuel des étoiles (pleines/demi/vides)

### 5. **Protection et Sécurité**
- Seuls les acheteurs peuvent laisser un avis
- Un utilisateur ne peut modifier/supprimer que ses propres avis
- Vérification de l'achat via `OrderHistoryItem`

## Structure de la Base de Données

### ProductReview
```python
- id (PK)
- product (FK → Product)
- user (FK → User)
- rating (Integer: 1-5)
- title (String: 200 chars)
- comment (Text)
- verified_purchase (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

### OrderHistoryItem (mise à jour)
```python
- product_slug (String) # NOUVEAU - Pour lier aux produits après achat
```

## URLs Ajoutées

| URL | Nom | Description | Authentification |
|-----|-----|-------------|-----------------|
| `/store/product/<slug>/review/` | `add-review` | Ajouter/modifier un avis (FR) | Requise |
| `/store/nl/product/<slug>/review/` | `add-review-nl` | Ajouter/modifier un avis (NL) | Requise |
| `/store/review/<id>/delete/` | `delete-review` | Supprimer un avis | Requise |

## Templates

### Nouveaux Templates
1. **add_review.html** : Formulaire d'ajout/modification d'avis (FR)
2. **add_review_nl.html** : Formulaire d'ajout/modification d'avis (NL)

### Templates Modifiés
1. **order_history.html** : Ajout des boutons d'avis
2. **order_history_nl.html** : Ajout des boutons d'avis (NL)
3. **detail.html** : Section complète des avis clients
4. **detail_nl.html** : Section complète des avis clients (NL)

## Formulaire ProductReviewForm

Champs :
- **rating** : Radio buttons stylisés en étoiles
- **title** : Input text pour le titre
- **comment** : Textarea pour le commentaire détaillé

Validation :
- Tous les champs sont requis
- Rating entre 1 et 5
- Titre max 200 caractères

## Interface Utilisateur

### Page "Mes Commandes"
```
┌─────────────────────────────────────────────┐
│ Commande du 22/11/2025 à 14:30             │
│ Total: 45.99€                               │
├─────────────────────────────────────────────┤
│ [Image] Produit A    15.99€  x2    31.98€  │
│         [⭐ Donner un avis]                  │
│                                              │
│ [Image] Produit B    14.01€  x1    14.01€  │
│         [✏️ Modifier l'avis]                │
└─────────────────────────────────────────────┘
```

### Page Détail Produit

#### Résumé des Notes
```
┌─────────────────────────────────────┐
│    4.5                               │
│   ★★★★⯨                             │
│   23 avis                            │
│                                      │
│  5★ ████████████████░░ 16           │
│  4★ ████████░░░░░░░░░░  5           │
│  3★ ██░░░░░░░░░░░░░░░░  2           │
│  2★ ░░░░░░░░░░░░░░░░░░  0           │
│  1★ ░░░░░░░░░░░░░░░░░░  0           │
└─────────────────────────────────────┘
```

#### Liste des Avis
```
★★★★★
Excellent produit !
✓ Achat vérifié

Très satisfait de mon achat, la qualité est au rendez-vous...

john@example.com    22/11/2025
[✏️ Modifier] [🗑️ Supprimer]  (si c'est votre avis)
─────────────────────────────────────
```

### Formulaire d'Avis
```
┌─────────────────────────────────────┐
│  Donner votre avis                  │
│                                      │
│  [Image] Produit A    15.99€        │
├─────────────────────────────────────┤
│  Note *                              │
│  ☆ ☆ ☆ ☆ ☆  (cliquable)            │
│                                      │
│  Titre de votre avis *               │
│  [________________________]         │
│                                      │
│  Votre commentaire *                 │
│  [________________________]         │
│  [________________________]         │
│  [________________________]         │
│                                      │
│  [Annuler]      [Publier l'avis]   │
└─────────────────────────────────────┘
```

## CSS Personnalisé

### Étoiles Interactives
- Hover effect : étoiles se remplissent au survol
- Couleur : #C78C3A (doré)
- Taille : 2rem pour le formulaire
- Animation de transition smooth

### Barres de Progression
- Hauteur : 20px
- Couleur : #C78C3A
- Bordures arrondies
- Responsive

## Traductions

### Français
- "Avis clients"
- "Donner un avis"
- "Modifier l'avis"
- "Achat vérifié"
- "Aucun avis pour le moment"

### Nederlands
- "Klantbeoordelingen"
- "Geef beoordeling"
- "Beoordeling wijzigen"
- "Geverifieerde aankoop"
- "Nog geen beoordelingen"

## Admin Django

### Interface d'Administration
```python
@admin.register(ProductReview)
class ProductReviewAdmin:
    - Liste : produit, utilisateur, note, titre, date
    - Filtres : note, achat vérifié, date
    - Recherche : nom produit, email, titre, commentaire
    - Hiérarchie par date
    - Fieldsets organisés
```

## Filtres Template

### store_filters.py
```python
@register.filter
def get_item(dictionary, key):
    """Accéder aux éléments d'un dictionnaire dans les templates"""
    return dictionary.get(int(key))
```

Utilisation :
```django
{{ distribution|get_item:rating }}
```

## Flux Utilisateur

### 1. Après Achat
```
Achat → OrderHistory créé → OrderHistoryItem.product_slug sauvegardé
```

### 2. Consultation de "Mes Commandes"
```
User clique "Mes commandes"
  → Affichage des commandes
  → Pour chaque produit :
      - Si avis existe : [✏️ Modifier l'avis]
      - Sinon : [⭐ Donner un avis]
```

### 3. Ajout d'Avis
```
User clique [⭐ Donner un avis]
  → Vérification de l'achat (has_purchased)
  → Si OK : Formulaire
  → User remplit : Note + Titre + Commentaire
  → Soumission
  → Validation
  → ProductReview créé (verified_purchase=True)
  → Redirection vers page produit
  → Message de succès
```

### 4. Consultation d'un Produit
```
User visite page produit
  → Calcul note moyenne
  → Calcul distribution
  → Affichage section "Avis clients"
  → Liste tous les avis (ordre chronologique inversé)
  → Si c'est son avis : boutons Modifier/Supprimer visibles
```

### 5. Modification d'Avis
```
User clique [✏️ Modifier]
  → Formulaire pré-rempli
  → User modifie
  → Soumission
  → ProductReview.updated_at mis à jour
  → Message de succès
```

### 6. Suppression d'Avis
```
User clique [🗑️ Supprimer]
  → Confirmation JavaScript
  → Si OK : ProductReview supprimé
  → Redirection vers page produit
  → Message de succès
```

## Messages Utilisateur

### Succès (vert)
- "Merci pour votre avis !"
- "Votre avis a été mis à jour avec succès."
- "Votre avis a été supprimé."

### Erreur (rouge)
- "Vous devez avoir acheté ce produit pour laisser un avis."

## Sécurité

### Vérifications
1. **Authentification** : `@login_required` sur toutes les vues d'avis
2. **Achat vérifié** : Vérification via `OrderHistoryItem.objects.filter()`
3. **Propriétaire** : User ne peut modifier que ses propres avis
4. **Unicité** : Contrainte DB `unique_together=['product', 'user']`

### Protection CSRF
- Tous les formulaires incluent `{% csrf_token %}`

## Performance

### Optimisations
- Utilisation de `aggregate()` pour les calculs
- Requêtes optimisées avec `select_related()` si nécessaire
- Index sur `created_at` pour tri rapide

### Cache (recommandé pour production)
```python
# Dans views.py - à implémenter si nécessaire
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache 15 minutes
def product_detail(request, slug):
    ...
```

## Tests Recommandés

1. **Test création avis** : Utilisateur authentifié + achat vérifié
2. **Test unicité** : Impossible de créer 2 avis pour même produit
3. **Test sécurité** : Impossible de laisser avis sans achat
4. **Test modification** : Uniquement par le propriétaire
5. **Test suppression** : Uniquement par le propriétaire
6. **Test calculs** : Note moyenne correcte
7. **Test distribution** : Pourcentages corrects

## Migration

### Migration 0014
```
+ Add field product_slug to orderhistoryitem
+ Create model ProductReview
```

**Note importante** : Les anciens OrderHistoryItem n'ont pas de `product_slug`. Ils ne pourront pas avoir d'avis associés (comportement normal).

## Améliorations Futures Possibles

1. **Réponses aux avis** : Permettre au vendeur de répondre
2. **Photos** : Ajouter des images aux avis
3. **Votes utiles** : "Cet avis vous a-t-il été utile ?"
4. **Tri** : Trier par pertinence, date, note
5. **Filtres** : Filtrer par nombre d'étoiles
6. **Modération** : Système de modération des avis
7. **Notifications** : Email au vendeur lors d'un nouvel avis
8. **Statistiques** : Dashboard avec stats d'avis par produit

## Fichiers Créés/Modifiés

### Nouveaux Fichiers
- `store/templates/store/add_review.html`
- `store/templates/store/add_review_nl.html`
- `store/templatetags/__init__.py`
- `store/templatetags/store_filters.py`
- `REVIEWS_SYSTEM.md` (ce fichier)

### Fichiers Modifiés
- `store/models.py` : +ProductReview, +méthodes Product, +méthodes OrderHistoryItem
- `store/forms.py` : +ProductReviewForm
- `store/views.py` : +add_review, +add_review_nl, +delete_review, modifications checkout
- `store/urls.py` : +3 URLs
- `store/admin.py` : +ProductReviewAdmin
- `store/templates/store/detail.html` : +section avis
- `store/templates/store/detail_nl.html` : +section avis
- `store/templates/store/order_history.html` : +boutons avis
- `store/templates/store/order_history_nl.html` : +boutons avis

## Dépendances

Aucune nouvelle dépendance externe. Utilise uniquement :
- Django core
- Bootstrap 5 (déjà présent)
- Django template filters

## Conclusion

Le système d'avis est maintenant complètement intégré au projet MedinaChic. Il offre une expérience utilisateur fluide, type Amazon, avec :
- ✅ Vérification d'achat
- ✅ Interface intuitive
- ✅ Bilingue (FR/NL)
- ✅ Sécurisé
- ✅ Responsive
- ✅ Administration facile
