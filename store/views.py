from pprint import pprint
from sqlite3 import IntegrityError

import stripe
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from accounts.views import User
from .models import Product
from .serializers import ProductSerializer

from MedinaChic import settings
from accounts.models import Shopper, ShippingAddress
from store.forms import OrderForm
from store.models import Product, Cart, Order
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer


stripe.api_key = settings.STRIPE_API_KEY
def index(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Search in product name, description, and category
        products = Product.objects.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(category__icontains=search_query)
        )
    else:
        products = Product.objects.all()

    return render(request, 'store/index.html', {
        'products': products,
        'search_query': search_query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail.html', context={'product': product})

def add_to_cart(request, slug):
    from django.contrib import messages
    
    user: Shopper = request.user
    product = get_object_or_404(Product, slug=slug)
    
    # Vérifier le stock avant d'ajouter au panier
    if product.quantity <= 0:
        messages.warning(request, f"Le produit '{product.name}' n'est plus disponible en stock.")
        return redirect(reverse('product', kwargs={'slug': slug}))
    
    cart = user.add_to_cart(slug=slug)
    
    if cart is None:
        messages.warning(request, f"Impossible d'ajouter plus de '{product.name}' au panier. Stock insuffisant.")
        return redirect(reverse('product', kwargs={'slug': slug}))
    
    messages.success(request, f"'{product.name}' a été ajouté à votre panier.")
    
    # Get the referer to redirect back, or go to index
    referer = request.META.get('HTTP_REFERER', reverse('index'))
    
    # If coming from index or category page, go back there
    if 'categorie' in referer or referer.endswith('/'):
        return redirect(referer)
    
    # Otherwise go to product page
    return redirect(reverse('product', kwargs={'slug': slug}))


@login_required
def cart(request):
    from django.contrib import messages
    
    # Nettoyer les réservations expirées globalement
    cleanup_expired_reservations()
    
    orders = Order.objects.filter(user=request.user, ordered=False)
    
    # Vérifier et ajuster le stock pour les commandes de l'utilisateur
    stock_adjusted = False
    for order in orders:
        available = order.get_available_stock()
        if order.quantity > available:
            if available > 0:
                order.quantity = available
                order.save()
                messages.warning(request, f"Quantité de '{order.product.name}' ajustée à {available} (stock limité).")
                stock_adjusted = True
            else:
                product_name = order.product.name
                order.delete()
                messages.error(request, f"'{product_name}' retiré du panier (rupture de stock).")
                stock_adjusted = True
    
    # Recharger les commandes après ajustements
    orders = Order.objects.filter(user=request.user, ordered=False)
    
    if orders.count() == 0:
        if stock_adjusted:
            messages.info(request, "Votre panier est maintenant vide.")
        return redirect('index')
    
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(queryset=orders)
    return render(request, 'store/cart.html', context={"forms": formset})

def update_quantities(request):
    from django.contrib import messages
    
    print("DEBUG: update_quantities appelée")
    print(f"DEBUG: POST data = {request.POST}")
    
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(request.POST, queryset=Order.objects.filter(user=request.user, ordered=False))
    
    print(f"DEBUG: Formset is_valid = {formset.is_valid()}")
    if not formset.is_valid():
        print(f"DEBUG: Formset errors = {formset.errors}")
    
    if formset.is_valid():
        print(f"DEBUG: Nombre de formulaires = {len(formset)}")
        for form in formset:
            print(f"DEBUG: Form data = {form.cleaned_data}")
            if form.cleaned_data.get('delete'):
                # Si suppression, libérer la réservation
                if form.instance.reserved_until:
                    form.instance.release_reservation()
                continue
            
            order = form.instance
            new_quantity = form.cleaned_data.get('quantity')
            print(f"DEBUG: Produit={order.product.name}, Ancienne quantité={order.quantity}, Nouvelle quantité={new_quantity}")
            
            # Nettoyer les réservations expirées pour ce produit
            Order.objects.filter(
                product=order.product,
                ordered=False,
                reserved_until__lt=timezone.now()
            ).update(reserved_until=None)
            
            # Vérifier le stock disponible
            available = order.get_available_stock()
            
            if new_quantity > available:
                messages.error(
                    request,
                    f"Stock insuffisant pour '{order.product.name}'. "
                    f"Disponible: {available}, Demandé: {new_quantity}"
                )
                # Ajuster à la quantité disponible maximale
                if available > 0:
                    order.quantity = available
                    order.save()
                    messages.warning(request, f"Quantité ajustée à {available} pour '{order.product.name}'.")
                else:
                    order.delete()
                    messages.warning(request, f"'{order.product.name}' retiré du panier (rupture de stock).")
            else:
                # Explicitly set quantity and save
                order.quantity = new_quantity
                order.save()
                messages.success(request, f"Quantité mise à jour pour '{order.product.name}'.")
        
        # Vérifier si le panier est vide
        if request.user.cart.orders.count() == 0:
            request.user.cart.delete()
            return redirect('index')
    
    return redirect('cart')

def create_checkout_session(request):
    from django.contrib import messages
    
    cart = request.user.cart
    
    # Nettoyer les réservations expirées
    Order.objects.filter(
        ordered=False,
        reserved_until__lt=timezone.now()
    ).update(reserved_until=None)
    
    # Vérification finale du stock et réservation
    stock_errors = []
    for order in cart.orders.all():
        available = order.get_available_stock()
        
        if order.quantity > available:
            if available > 0:
                # Ajuster la quantité
                order.quantity = available
                order.save()
                stock_errors.append(
                    f"'{order.product.name}': quantité réduite à {available}"
                )
            else:
                # Supprimer du panier
                product_name = order.product.name
                order.delete()
                stock_errors.append(
                    f"'{product_name}' retiré du panier (rupture de stock)"
                )
    
    # Si des ajustements ont été faits, informer l'utilisateur
    if stock_errors:
        for error in stock_errors:
            messages.warning(request, error)
        
        # Vérifier si le panier est maintenant vide
        if cart.orders.count() == 0:
            cart.delete()
            messages.error(request, "Votre panier est vide suite à des ruptures de stock.")
            return redirect('index')
        
        messages.info(request, "Veuillez vérifier votre panier avant de continuer.")
        return redirect('cart')
    
    # Réserver le stock pour 15 minutes
    for order in cart.orders.all():
        order.reserve_stock(minutes=15)
    
    line_items = [{"price": order.product.stripe_id,
                   "quantity": order.quantity}for order in cart.orders.all()]

    checkout_data = {
        "line_items": line_items,
        "mode": 'payment',
        "locale": 'fr',
        "shipping_address_collection": {"allowed_countries": ["BE"]},
        "success_url": request.build_absolute_uri(reverse('checkout-success')) + '?session_id={CHECKOUT_SESSION_ID}',
        "cancel_url": request.build_absolute_uri(reverse('checkout-cancelled')),
    }

    if request.user.stripe_id:
        checkout_data["customer"] = request.user.stripe_id
    else:
        checkout_data["customer_email"] = request.user.email

    session = stripe.checkout.Session.create(**checkout_data)
    return redirect(session.url, code=303)

@login_required
def checkout_cancelled(request):
    """Gérer l'annulation du paiement et libérer les réservations"""
    from django.contrib import messages
    
    try:
        cart = request.user.cart
        # Libérer toutes les réservations
        for order in cart.orders.all():
            order.release_reservation()
        
        messages.info(request, "Paiement annulé. Vos articles sont toujours dans le panier.")
    except Cart.DoesNotExist:
        pass
    
    return redirect('cart')

def checkout_success(request):
    # Save order history when user returns after successful payment
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            if cart and cart.orders.exists():
                from store.models import OrderHistory, OrderHistoryItem
                
                # Calculate total
                total = sum(order.product.price * order.quantity for order in cart.orders.all())
                
                # Create order history
                order_history = OrderHistory.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    total_amount=total,
                    stripe_session_id=request.GET.get('session_id', '')
                )
                
                # Save each item
                for order in cart.orders.all():
                    # Get the thumbnail URL or path
                    thumbnail_url = order.product.thumbnail.url if order.product.thumbnail else ''
                    
                    OrderHistoryItem.objects.create(
                        order_history=order_history,
                        product_name=order.product.name,
                        product_price=order.product.price,
                        quantity=order.quantity,
                        product_thumbnail=thumbnail_url,
                        product_slug=order.product.slug
                    )
                    
                    # Update product stock
                    product = order.product
                    product.quantity = max(0, product.quantity - order.quantity)
                    product.save()
                
                # Delete cart after saving history
                cart.delete()
        except Cart.DoesNotExist:
            pass
    
    return render(request, 'store/success.html')

def delete_cart(request):
    if cart := request.user.cart:
        cart.delete()

    return redirect('index')

@login_required
def delete_cart_item(request, order_id):
    """Supprimer un article individuel du panier"""
    from django.contrib import messages
    
    try:
        order = Order.objects.get(id=order_id, user=request.user, ordered=False)
        product_name = order.product.name
        
        # Libérer la réservation si elle existe
        if order.reserved_until:
            order.release_reservation()
        
        # Supprimer l'ordre
        order.delete()
        messages.success(request, f"'{product_name}' a été retiré de votre panier.")
        
        # Vérifier si le panier est vide
        try:
            cart = request.user.cart
            if cart.orders.count() == 0:
                cart.delete()
                messages.info(request, "Votre panier est maintenant vide.")
                return redirect('index')
        except Cart.DoesNotExist:
            return redirect('index')
            
    except Order.DoesNotExist:
        messages.error(request, "Cet article n'existe pas dans votre panier.")
    
    return redirect('cart')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse("Invalid signature", status=400)

    if event['type'] == 'checkout.session.completed':
        data = event['data']['object']
        try:
            user = get_object_or_404(Shopper, email=data['customer_details']['email'])

        except KeyError:
            return HttpResponse("invalid customer email", status=404)
        complete_order(data=data, user=user)
        save_shipping_address(data=data, user=user)
        return HttpResponse(status=200)

    return HttpResponse(status=200)

def complete_order(data, user):
    # Save order history before deleting cart
    from store.models import OrderHistory, OrderHistoryItem
    
    try:
        cart = user.cart
        if cart and cart.orders.exists():
            # Calculate total
            total = sum(order.product.price * order.quantity for order in cart.orders.all())
            
            # Create order history
            order_history = OrderHistory.objects.create(
                user=user,
                user_email=user.email,
                total_amount=total,
                stripe_session_id=data.get('id', '')
            )
            
            # Save each item
            for order in cart.orders.all():
                # Get the thumbnail URL or path
                thumbnail_url = order.product.thumbnail.url if order.product.thumbnail else ''
                
                OrderHistoryItem.objects.create(
                    order_history=order_history,
                    product_name=order.product.name,
                    product_price=order.product.price,
                    quantity=order.quantity,
                    product_thumbnail=thumbnail_url,
                    product_slug=order.product.slug
                )
                
                # Update product stock
                product = order.product
                product.quantity = max(0, product.quantity - order.quantity)
                product.save()
            
            # Delete cart after saving history
            cart.delete()
    except Cart.DoesNotExist:
        # No cart exists, skip order history
        pass
    
    # Update user's stripe ID
    user.stripe_id = data['customer']
    user.save()
    return HttpResponse(status=200)

def save_shipping_address(data, user):
    try:
        address = data['shipping']["address"]
        name = data['shipping']["name"]
        city=address["city"]
        country=address["country"]
        line1=address["line1"]
        line2=address["line2"]
        zip_code=address["postal_code"]
    except KeyError:
        return HttpResponse(status=400)

    ShippingAddress.objects.get_or_create(user=user,
                                          name=name,
                                          city=city,
                                          country=country.lower(),
                                          address=line1,
                                          address2=line2 or "",
                                          zip_code=zip_code)

    return HttpResponse(status=200)


def cleanup_expired_reservations():
    """Nettoie les réservations expirées et supprime les commandes si nécessaire"""
    from django.db.models import Q
    
    # Trouver les commandes avec réservations expirées
    expired_orders = Order.objects.filter(
        ordered=False,
        reserved_until__lt=timezone.now()
    )
    
    carts_to_check = set()
    
    for order in expired_orders:
        # Libérer la réservation
        order.reserved_until = None
        order.save()
        
        # Vérifier si le stock est toujours disponible
        if order.product.quantity < order.quantity:
            if order.product.quantity > 0:
                # Ajuster la quantité
                order.quantity = order.product.quantity
                order.save()
            else:
                # Supprimer la commande
                cart = order.user.cart
                carts_to_check.add(cart.id)
                order.delete()
    
    # Supprimer les paniers vides
    for cart_id in carts_to_check:
        try:
            cart = Cart.objects.get(id=cart_id)
            if cart.orders.count() == 0:
                cart.delete()
        except Cart.DoesNotExist:
            pass

def apropos(request):
    return render(request, 'store/apropos.html')


@login_required
@login_required
def order_history(request):
    from store.models import OrderHistory
    orders = OrderHistory.objects.filter(user=request.user).prefetch_related('return_requests', 'items')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required
def order_history_nl(request):
    from store.models import OrderHistory
    orders = OrderHistory.objects.filter(user=request.user).prefetch_related('return_requests', 'items')
    return render(request, 'store/order_history_nl.html', {'orders': orders})


@login_required
def generate_invoice(request, order_id):
    """Génère une facture PDF pour une commande"""
    from store.models import OrderHistory
    from store.invoice import generate_invoice_pdf
    
    # Récupérer la commande
    order = get_object_or_404(OrderHistory, id=order_id, user=request.user)
    
    # Générer et retourner le PDF
    return generate_invoice_pdf(order)


def produits_par_categorie(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'store/index.html', {'products': products, 'selected_category': category})

def index_nl(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Search in product name, description (including NL versions), and category
        products = Product.objects.filter(
            models.Q(name__icontains=search_query) |
            models.Q(name_nl__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(description_nl__icontains=search_query) |
            models.Q(category__icontains=search_query)
        )
    else:
        products = Product.objects.all()

    return render(request, 'store/index_nl.html', {
        'products': products,
        'lang': 'nl',
        'search_query': search_query
    })

def product_detail_nl(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail_nl.html', context={'product': product, 'lang': 'nl'})

def apropos_nl(request):
    return render(request, 'store/apropos_nl.html')

@login_required
def cart_nl(request):
    from django.contrib import messages
    
    # Nettoyer les réservations expirées globalement
    cleanup_expired_reservations()
    
    orders = Order.objects.filter(user=request.user, ordered=False)
    
    # Vérifier et ajuster le stock pour les commandes de l'utilisateur
    stock_adjusted = False
    for order in orders:
        available = order.get_available_stock()
        if order.quantity > available:
            if available > 0:
                order.quantity = available
                order.save()
                messages.warning(request, f"Hoeveelheid van '{order.product.name}' aangepast naar {available} (beperkte voorraad).")
                stock_adjusted = True
            else:
                product_name = order.product.name
                order.delete()
                messages.error(request, f"'{product_name}' verwijderd uit winkelwagen (niet op voorraad).")
                stock_adjusted = True
    
    # Recharger les commandes après ajustements
    orders = Order.objects.filter(user=request.user, ordered=False)
    
    if orders.count() == 0:
        if stock_adjusted:
            messages.info(request, "Uw winkelwagen is nu leeg.")
        return redirect('index-nl')

    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(queryset=orders)

    return render(request, 'store/cart_nl.html', context={"forms": formset})


def produits_par_categorie_nl(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'store/index_nl.html', {'products': products, 'selected_category': category})


@api_view(['GET'])
def api_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def api_add_product(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def api_signup(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email et mot de passe sont requis."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Cette adresse email est déjà utilisée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(email=email, password=password)
        return Response(
            {"message": "Utilisateur créé avec succès.", "email": user.email},
            status=status.HTTP_201_CREATED
        )

    except IntegrityError:
        return Response(
            {"error": "Erreur d'intégrité. L'utilisateur existe déjà."},
            status=status.HTTP_400_BAD_REQUEST
        )


@login_required
def add_review(request, slug):
    """Ajouter ou modifier un avis pour un produit acheté"""
    from django.contrib import messages
    from store.forms import ProductReviewForm
    from store.models import ProductReview, OrderHistoryItem
    
    product = get_object_or_404(Product, slug=slug)
    
    # Vérifier que l'utilisateur a bien acheté ce produit
    has_purchased = OrderHistoryItem.objects.filter(
        order_history__user=request.user,
        product_slug=slug
    ).exists()
    
    if not has_purchased:
        messages.error(request, "Vous devez avoir acheté ce produit pour laisser un avis.")
        return redirect('product', slug=slug)
    
    # Vérifier si l'utilisateur a déjà un avis
    try:
        review = ProductReview.objects.get(product=product, user=request.user)
        is_edit = True
    except ProductReview.DoesNotExist:
        review = None
        is_edit = False
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified_purchase = True
            review.save()
            
            if is_edit:
                messages.success(request, "Votre avis a été mis à jour avec succès.")
            else:
                messages.success(request, "Merci pour votre avis !")
            
            return redirect('product', slug=slug)
    else:
        form = ProductReviewForm(instance=review)
    
    context = {
        'form': form,
        'product': product,
        'is_edit': is_edit
    }
    
    return render(request, 'store/add_review.html', context)


@login_required
def add_review_nl(request, slug):
    """Version néerlandaise de add_review"""
    from django.contrib import messages
    from store.forms import ProductReviewForm
    from store.models import ProductReview, OrderHistoryItem
    
    product = get_object_or_404(Product, slug=slug)
    
    # Vérifier que l'utilisateur a bien acheté ce produit
    has_purchased = OrderHistoryItem.objects.filter(
        order_history__user=request.user,
        product_slug=slug
    ).exists()
    
    if not has_purchased:
        messages.error(request, "U moet dit product gekocht hebben om een beoordeling achter te laten.")
        return redirect('product-nl', slug=slug)
    
    # Vérifier si l'utilisateur a déjà un avis
    try:
        review = ProductReview.objects.get(product=product, user=request.user)
        is_edit = True
    except ProductReview.DoesNotExist:
        review = None
        is_edit = False
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified_purchase = True
            review.save()
            
            if is_edit:
                messages.success(request, "Uw beoordeling is succesvol bijgewerkt.")
            else:
                messages.success(request, "Bedankt voor uw beoordeling!")
            
            return redirect('product-nl', slug=slug)
    else:
        form = ProductReviewForm(instance=review)
    
    context = {
        'form': form,
        'product': product,
        'is_edit': is_edit,
        'lang': 'nl'
    }
    
    return render(request, 'store/add_review_nl.html', context)


@login_required
def delete_review(request, review_id):
    """Supprimer un avis"""
    from django.contrib import messages
    from store.models import ProductReview
    
    review = get_object_or_404(ProductReview, id=review_id, user=request.user)
    product_slug = review.product.slug
    review.delete()
    
    messages.success(request, "Votre avis a été supprimé.")
    return redirect('product', slug=product_slug)


@login_required
def subscribe_stock_alert(request, slug):
    """S'inscrire pour recevoir une alerte de retour en stock"""
    from django.contrib import messages
    from store.models import StockAlert
    
    product = get_object_or_404(Product, slug=slug)
    
    # Vérifier si l'utilisateur a déjà une alerte pour ce produit
    alert, created = StockAlert.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f"Vous serez notifié(e) quand '{product.name}' sera de nouveau en stock !")
    else:
        if alert.notified:
            # Réactiver l'alerte si elle a déjà été notifiée
            alert.notified = False
            alert.save()
            messages.success(request, f"Votre alerte pour '{product.name}' a été réactivée !")
        else:
            messages.info(request, f"Vous êtes déjà inscrit(e) pour être notifié(e) du retour en stock de '{product.name}'.")
    
    return redirect('product', slug=slug)


@login_required
def subscribe_stock_alert_nl(request, slug):
    """S'inscrire pour recevoir une alerte de retour en stock (version NL)"""
    from django.contrib import messages
    from store.models import StockAlert
    
    product = get_object_or_404(Product, slug=slug)
    
    # Vérifier si l'utilisateur a déjà une alerte pour ce produit
    alert, created = StockAlert.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f"U wordt op de hoogte gebracht wanneer '{product.name_nl or product.name}' weer op voorraad is!")
    else:
        if alert.notified:
            # Réactiver l'alerte si elle a déjà été notifiée
            alert.notified = False
            alert.save()
            messages.success(request, f"Uw waarschuwing voor '{product.name_nl or product.name}' is opnieuw geactiveerd!")
        else:
            messages.info(request, f"U bent al ingeschreven om op de hoogte te worden gebracht wanneer '{product.name_nl or product.name}' weer op voorraad is.")
    
    return redirect('product-nl', slug=slug)


@login_required
def check_stock_alerts(request):
    """Vérifier s'il y a des alertes de stock notifiées pour l'utilisateur"""
    from django.http import JsonResponse
    from store.models import StockAlert
    
    alerts = StockAlert.objects.filter(
        user=request.user,
        notified=True
    ).select_related('product')
    
    notifications = []
    for alert in alerts:
        notifications.append({
            'id': alert.id,
            'product_name': alert.product.name,
            'product_slug': alert.product.slug,
            'product_thumbnail': alert.product.thumbnail.url if alert.product.thumbnail else None,
            'notified_at': alert.notified_at.strftime('%Y-%m-%d %H:%M:%S') if alert.notified_at else None
        })
        
        # Supprimer l'alerte après l'avoir récupérée (pour ne pas afficher plusieurs fois)
        alert.delete()
    
    return JsonResponse({'alerts': notifications})


@login_required
def check_stock_alerts_nl(request):
    """Vérifier s'il y a des alertes de stock notifiées pour l'utilisateur (version NL)"""
    from django.http import JsonResponse
    from store.models import StockAlert
    
    alerts = StockAlert.objects.filter(
        user=request.user,
        notified=True
    ).select_related('product')
    
    notifications = []
    for alert in alerts:
        notifications.append({
            'id': alert.id,
            'product_name': alert.product.name_nl or alert.product.name,
            'product_slug': alert.product.slug,
            'product_thumbnail': alert.product.thumbnail.url if alert.product.thumbnail else None,
            'notified_at': alert.notified_at.strftime('%Y-%m-%d %H:%M:%S') if alert.notified_at else None
        })
        
        # Supprimer l'alerte après l'avoir récupérée (pour ne pas afficher plusieurs fois)
        alert.delete()
    
    return JsonResponse({'alerts': notifications})


@login_required
def create_return_request(request, order_id):
    """Créer une demande de retour pour une commande"""
    from django.contrib import messages
    from store.models import OrderHistory, ReturnRequest, ReturnRequestItem
    from store.forms import ReturnRequestForm
    
    order = get_object_or_404(OrderHistory, id=order_id, user=request.user)
    
    # Vérifier s'il n'y a pas déjà une demande en attente
    if order.return_requests.filter(status='pending').exists():
        messages.warning(request, "Vous avez déjà une demande de retour en attente pour cette commande.")
        return redirect('order-history')
    
    if request.method == 'POST':
        form = ReturnRequestForm(order=order, data=request.POST, files=request.FILES)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.order = order
            return_request.save()
            
            # Créer les ReturnRequestItem pour chaque article sélectionné
            for item in order.items.all():
                field_name = f'item_{item.id}'
                quantity_field_name = f'quantity_{item.id}'
                
                if form.cleaned_data.get(field_name):
                    quantity = form.cleaned_data.get(quantity_field_name, item.quantity)
                    ReturnRequestItem.objects.create(
                        return_request=return_request,
                        order_item=item,
                        quantity=quantity
                    )
            
            messages.success(request, "Votre demande de retour a été envoyée. L'administrateur vous répondra bientôt.")
            return redirect('order-history')
    else:
        form = ReturnRequestForm(order=order)
    
    return render(request, 'store/return_request_form.html', {
        'form': form,
        'order': order
    })


@login_required
def create_return_request_nl(request, order_id):
    """Créer une demande de retour pour une commande (version NL)"""
    from django.contrib import messages
    from store.models import OrderHistory, ReturnRequest, ReturnRequestItem
    from store.forms import ReturnRequestForm
    
    order = get_object_or_404(OrderHistory, id=order_id, user=request.user)
    
    # Vérifier s'il n'y a pas déjà une demande en attente
    if order.return_requests.filter(status='pending').exists():
        messages.warning(request, "U heeft al een retourverzoek in behandeling voor deze bestelling.")
        return redirect('order-history-nl')
    
    if request.method == 'POST':
        form = ReturnRequestForm(order=order, data=request.POST, files=request.FILES)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.order = order
            return_request.save()
            
            # Créer les ReturnRequestItem pour chaque article sélectionné
            for item in order.items.all():
                field_name = f'item_{item.id}'
                quantity_field_name = f'quantity_{item.id}'
                
                if form.cleaned_data.get(field_name):
                    quantity = form.cleaned_data.get(quantity_field_name, item.quantity)
                    ReturnRequestItem.objects.create(
                        return_request=return_request,
                        order_item=item,
                        quantity=quantity
                    )
            
            messages.success(request, "Uw retourverzoek is verzonden. De beheerder zal binnenkort antwoorden.")
            return redirect('order-history-nl')
    else:
        form = ReturnRequestForm(order=order)
    
    return render(request, 'store/return_request_form_nl.html', {
        'form': form,
        'order': order
    })


@login_required
def view_return_request(request, request_id):
    """Voir les détails d'une demande de retour"""
    from store.models import ReturnRequest
    
    return_request = get_object_or_404(ReturnRequest, id=request_id, user=request.user)
    
    return render(request, 'store/return_request_detail.html', {
        'return_request': return_request
    })


@login_required
def view_return_request_nl(request, request_id):
    """Voir les détails d'une demande de retour (version NL)"""
    from store.models import ReturnRequest
    
    return_request = get_object_or_404(ReturnRequest, id=request_id, user=request.user)
    
    return render(request, 'store/return_request_detail_nl.html', {
        'return_request': return_request
    })


@login_required
def notifications(request):
    """Afficher les notifications de l'utilisateur"""
    from store.models import Notification
    
    # Récupérer toutes les notifications de l'utilisateur
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Marquer comme lues si demandé
    if request.method == 'POST' and 'mark_read' in request.POST:
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('notifications')
    
    # Marquer toutes comme lues
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        user_notifications.update(is_read=True)
        return redirect('notifications')
    
    # Compter les non lues
    unread_count = user_notifications.filter(is_read=False).count()
    
    return render(request, 'store/notifications.html', {
        'notifications': user_notifications,
        'unread_count': unread_count
    })


@login_required
def notifications_nl(request):
    """Afficher les notifications de l'utilisateur (version NL)"""
    from store.models import Notification
    
    # Récupérer toutes les notifications de l'utilisateur
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Marquer comme lues si demandé
    if request.method == 'POST' and 'mark_read' in request.POST:
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('notifications-nl')
    
    # Marquer toutes comme lues
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        user_notifications.update(is_read=True)
        return redirect('notifications-nl')
    
    # Compter les non lues
    unread_count = user_notifications.filter(is_read=False).count()
    
    return render(request, 'store/notifications_nl.html', {
        'notifications': user_notifications,
        'unread_count': unread_count
    })