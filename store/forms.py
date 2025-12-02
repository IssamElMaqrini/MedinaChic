from django import forms

from store.models import Order, ProductReview, ReturnRequest

class OrderForm(forms.ModelForm):
    quantity = forms.ChoiceField(choices=[(i, i) for i in range(1, 11)])
    delete = forms.BooleanField(initial=False, required=False, label="Delete")

    class Meta:
        model = Order
        fields = ['quantity']


    def save(self, *args, **kwargs):
        if self.cleaned_data['delete']:
            self.instance.delete()
            if self.instance.user.cart.orders.count() == 0:
                self.instance.user.cart.delete()
            return True

        return super().save(*args, **kwargs)


class ProductReviewForm(forms.ModelForm):
    """Formulaire pour ajouter ou modifier un avis sur un produit"""
    
    rating = forms.ChoiceField(
        choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
        label="Note"
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Résumez votre avis en quelques mots'
        }),
        label="Titre de votre avis"
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Partagez votre expérience avec ce produit...'
        }),
        label="Votre commentaire"
    )
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']


class StockUpdateForm(forms.Form):
    """Formulaire pour mettre à jour le stock d'un produit"""
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px;'
        }),
        label="Nouvelle quantité"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS personnalisées
        for field_name, field in self.fields.items():
            if field_name != 'rating':
                field.widget.attrs['class'] = 'form-control'


class ReturnRequestForm(forms.ModelForm):
    """Formulaire pour demander un retour de commande"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Veuillez expliquer la raison de votre demande de retour...'
        }),
        label="Raison du retour"
    )
    
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label="Photo du produit (optionnel)"
    )
    
    class Meta:
        model = ReturnRequest
        fields = ['reason', 'photo']
    
    def __init__(self, order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order
        
        # Ajouter dynamiquement des champs pour chaque article de la commande
        if order:
            for item in order.items.all():
                # Checkbox pour sélectionner l'article
                field_name = f'item_{item.id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    initial=True,
                    label=f"{item.product_name}"
                )
                
                # Champ pour la quantité à retourner
                quantity_field_name = f'quantity_{item.id}'
                self.fields[quantity_field_name] = forms.IntegerField(
                    required=False,
                    min_value=1,
                    max_value=item.quantity,
                    initial=item.quantity,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control form-control-sm',
                        'style': 'width: 80px;'
                    })
                )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier qu'au moins un article est sélectionné
        if self.order:
            selected_items = []
            for item in self.order.items.all():
                field_name = f'item_{item.id}'
                if cleaned_data.get(field_name):
                    selected_items.append(item)
            
            if not selected_items:
                raise forms.ValidationError("Vous devez sélectionner au moins un article à retourner.")
        
        return cleaned_data


class ReturnRequestResponseForm(forms.ModelForm):
    """Formulaire pour l'admin pour répondre à une demande de retour"""
    
    status = forms.ChoiceField(
        choices=[('approved', 'Approuver'), ('rejected', 'Refuser')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Décision"
    )
    
    admin_response = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Expliquez votre décision (obligatoire en cas de refus)...'
        }),
        label="Votre réponse"
    )
    
    class Meta:
        model = ReturnRequest
        fields = ['status', 'admin_response']
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        admin_response = cleaned_data.get('admin_response')
        
        # Si le statut est "refusé", la réponse est obligatoire
        if status == 'rejected' and not admin_response:
            raise forms.ValidationError("Vous devez expliquer pourquoi vous refusez cette demande de retour.")
        
        return cleaned_data