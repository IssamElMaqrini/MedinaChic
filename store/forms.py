from django import forms

from store.models import Order, ProductReview

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS personnalisées
        for field_name, field in self.fields.items():
            if field_name != 'rating':
                field.widget.attrs['class'] = 'form-control'