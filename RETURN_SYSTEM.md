# Système de Retour de Commandes

## Description

Ce système permet aux utilisateurs de demander le retour d'une commande déjà effectuée. L'administrateur peut ensuite approuver ou refuser la demande, avec possibilité d'expliquer le refus.

## Fonctionnalités

### 1. Pour les Utilisateurs

#### Demande de Retour
- Sur la page "Mes commandes", un bouton "Demander un retour" est disponible pour chaque commande
- L'utilisateur remplit un formulaire contenant :
  - **Raison du retour** (champ texte obligatoire)
  - **Photo du produit** (optionnel, pour justifier la demande)
- Une seule demande de retour en attente est autorisée par commande
- L'utilisateur reçoit une confirmation après l'envoi

#### Suivi de la Demande
- Badge "Retour en attente" affiché sur la commande tant que la demande n'est pas traitée
- L'utilisateur peut consulter le statut de sa demande
- Notification de la décision de l'admin (approuvée/refusée)
- En cas de refus, la raison est visible

### 2. Pour les Administrateurs

#### Tableau de Bord des Retours
- Accès via `/store/admin-return-requests/` (FR) ou `/store/nl/admin-return-requests/` (NL)
- Vue d'ensemble de toutes les demandes de retour
- Filtres par statut :
  - **En attente** (pending)
  - **Approuvées** (approved)
  - **Refusées** (rejected)
- Compteurs pour chaque statut

#### Traitement des Demandes
- Consultation des détails :
  - Informations de la commande
  - Raison du retour
  - Photo (si fournie)
  - Informations utilisateur
- Décision à prendre :
  - **Approuver** : accepter le retour
  - **Refuser** : rejeter le retour (réponse obligatoire)
- Champ de réponse pour expliquer la décision (obligatoire en cas de refus)

## Architecture Technique

### Modèle de Données

```python
class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Refusée'),
    ]
    
    order = models.ForeignKey(OrderHistory, related_name='return_requests')
    user = models.ForeignKey(AUTH_USER_MODEL)
    reason = models.TextField()
    photo = models.ImageField(upload_to="returns/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Formulaires

1. **ReturnRequestForm** : Pour les utilisateurs
   - Champs : `reason`, `photo`
   - Validation : reason obligatoire

2. **ReturnRequestResponseForm** : Pour les admins
   - Champs : `status`, `admin_response`
   - Validation : admin_response obligatoire si status='rejected'

### Fichiers Modifiés/Créés

#### Modèles et Logique
1. **store/models.py** : Ajout du modèle `ReturnRequest`
2. **store/forms.py** : 
   - `ReturnRequestForm` (utilisateurs)
   - `ReturnRequestResponseForm` (admins)
3. **store/views.py** :
   - `create_return_request()` / `create_return_request_nl()`
   - `view_return_request()` / `view_return_request_nl()`
4. **store/admin_views.py** :
   - `admin_return_requests()` / `admin_return_requests_nl()`
   - `admin_process_return()` / `admin_process_return_nl()`
5. **store/admin.py** : `ReturnRequestAdmin` pour l'interface Django admin
6. **store/urls.py** : Routes pour toutes les nouvelles vues

#### Templates Utilisateurs
1. **store/templates/store/return_request_form.html** (FR)
2. **store/templates/store/return_request_form_nl.html** (NL)
3. **store/templates/store/return_request_detail.html** (FR)
4. **store/templates/store/return_request_detail_nl.html** (NL)
5. **store/templates/store/order_history.html** : Bouton retour ajouté
6. **store/templates/store/order_history_nl.html** : Bouton retour ajouté

#### Templates Admin
1. **store/templates/store/admin_return_requests.html** (FR)
2. **store/templates/store/admin_return_requests_nl.html** (NL)
3. **store/templates/store/admin_process_return.html** (FR)
4. **store/templates/store/admin_process_return_nl.html** (NL)

### Routes URL

#### Utilisateurs
- `/store/return-request/<order_id>/` : Créer une demande (FR)
- `/store/nl/return-request/<order_id>/` : Créer une demande (NL)
- `/store/view-return-request/<request_id>/` : Voir détails (FR)
- `/store/nl/view-return-request/<request_id>/` : Voir détails (NL)

#### Admin
- `/store/admin-return-requests/` : Liste des demandes (FR)
- `/store/nl/admin-return-requests/` : Liste des demandes (NL)
- `/store/admin-process-return/<request_id>/` : Traiter une demande (FR)
- `/store/nl/admin-process-return/<request_id>/` : Traiter une demande (NL)

## Design

### Style Visuel
- **Couleurs du site** :
  - Rouge : `#872D37`
  - Or : `#C78C3A`
- **Boutons** :
  - Bouton retour : `btn-warning` avec icône
  - Badge "en attente" : `badge bg-info`
  - Bouton soumettre : dégradé rouge/or
- **Formulaires** :
  - Bordures focus : rouge du site
  - Résumé de commande : fond dégradé translucide
  - Labels : rouge foncé, gras

### Interface Admin
- **Filtres** : Par statut (tous/en attente/approuvées/refusées)
- **Compteurs** : Nombre de demandes par statut
- **Actions** : Bouton "Traiter" pour chaque demande
- **Formulaire** : Radio buttons pour approuver/refuser

## Utilisation

### Pour un Utilisateur

1. Aller sur "Mes commandes"
2. Cliquer sur "Demander un retour" pour la commande concernée
3. Remplir la raison du retour
4. (Optionnel) Ajouter une photo
5. Soumettre la demande
6. Attendre la réponse de l'admin
7. Consulter la décision et la réponse de l'admin

### Pour l'Administrateur

1. Accéder au dashboard admin
2. Cliquer sur "Demandes de retour" dans le menu
3. Consulter la liste des demandes (filtre sur "En attente" recommandé)
4. Cliquer sur "Traiter" pour une demande spécifique
5. Examiner :
   - La commande concernée
   - La raison du retour
   - La photo (si fournie)
6. Choisir "Approuver" ou "Refuser"
7. Si refus, expliquer obligatoirement la raison
8. Valider la décision
9. L'utilisateur sera notifié

## Sécurité

- **Authentification** : Toutes les vues nécessitent `@login_required`
- **Autorisation Admin** : Vues admin protégées par `@user_passes_test(lambda u: u.is_superuser)`
- **Vérification propriété** : Un utilisateur ne peut demander le retour que de ses propres commandes
- **Limite** : Une seule demande en attente par commande
- **Validation** : Raison de refus obligatoire côté formulaire

## Points Importants

1. **Une demande par commande** : Si une demande est en attente, le bouton est remplacé par un badge "En attente"
2. **Photo optionnelle** : Aide à traiter la demande mais n'est pas obligatoire
3. **Réponse admin obligatoire** : Seulement en cas de refus pour expliquer la décision
4. **Historique** : Toutes les demandes sont conservées (avec dates de création/modification)
5. **Upload photos** : Stockées dans `/media/returns/`

## Améliorations Futures Possibles

- Notifications email automatiques à l'utilisateur
- Tracking du statut en temps réel
- Discussion entre utilisateur et admin via la demande
- Statistiques sur les raisons de retour les plus fréquentes
- Délai maximum pour demander un retour (ex: 14 jours après commande)
- Workflow complet de remboursement intégré
- Export CSV/PDF des demandes de retour
- Photos multiples pour une même demande
