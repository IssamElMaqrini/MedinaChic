from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
import json
from collections import defaultdict

from store.models import Product, OrderHistory, OrderHistoryItem
from accounts.models import DeletedUser
from store.forms import StockUpdateForm


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """Tableau de bord administrateur pour la gestion des stocks et commandes"""
    
    # Gestion de la mise à jour du stock
    if request.method == 'POST' and 'update_stock' in request.POST:
        product_id = request.POST.get('product_id')
        new_quantity = request.POST.get('quantity')
        
        try:
            product = Product.objects.get(id=product_id)
            product.quantity = int(new_quantity)
            product.save()
            messages.success(request, f"Stock de '{product.name}' mis à jour à {new_quantity} unités.")
        except Product.DoesNotExist:
            messages.error(request, "Produit introuvable.")
        except ValueError:
            messages.error(request, "Quantité invalide.")
        
        return redirect('admin-dashboard')
    
    # Filtres pour les commandes
    period_filter = request.GET.get('period', 'all')
    
    # Récupérer toutes les commandes
    orders = OrderHistory.objects.all().order_by('-order_date')
    
    # Appliquer les filtres de période
    if period_filter == 'today':
        orders = orders.filter(order_date__date=timezone.now().date())
    elif period_filter == 'week':
        orders = orders.filter(order_date__gte=timezone.now() - timedelta(days=7))
    elif period_filter == 'month':
        orders = orders.filter(order_date__gte=timezone.now() - timedelta(days=30))
    
    # Produits en rupture de stock
    out_of_stock = Product.objects.filter(quantity=0).order_by('name')
    
    # Produits avec stock faible (moins de 5 unités)
    low_stock = Product.objects.filter(quantity__gt=0, quantity__lte=5).order_by('quantity', 'name')
    
    # Statistiques
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    
    # Comptes supprimés
    deleted_users = DeletedUser.objects.all().order_by('-deleted_at')
    
    # Pour chaque compte supprimé, récupérer son historique de commandes
    deleted_users_with_orders = []
    for deleted_user in deleted_users:
        # Chercher les commandes avec l'email du compte supprimé
        user_orders = OrderHistory.objects.filter(
            user_email=deleted_user.email
        ).order_by('-order_date')
        
        deleted_users_with_orders.append({
            'deleted_user': deleted_user,
            'orders': user_orders,
            'total_spent': user_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        })
    
    # Données pour les graphiques (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Évolution du chiffre d'affaires
    revenue_data = defaultdict(float)
    revenue_orders = OrderHistory.objects.filter(order_date__gte=thirty_days_ago).order_by('order_date')
    for order in revenue_orders:
        date_key = order.order_date.strftime('%Y-%m-%d')
        revenue_data[date_key] += order.total_amount
    
    # Préparer les données pour Chart.js (CA total)
    revenue_labels = []
    revenue_values = []
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        revenue_labels.append((timezone.now() - timedelta(days=29-i)).strftime('%d/%m'))
        revenue_values.append(revenue_data.get(date, 0))
    
    # Liste des produits pour le sélecteur
    products_list = Product.objects.all().order_by('name')
    
    # Données de ventes par produit (pour le produit sélectionné via GET)
    selected_product_id = request.GET.get('product_id')
    product_sales_labels = []
    product_sales_values = []
    selected_product = None
    
    if selected_product_id:
        try:
            selected_product = Product.objects.get(id=selected_product_id)
            # Récupérer les ventes du produit sur 30 jours
            sales_data = defaultdict(int)
            product_items = OrderHistoryItem.objects.filter(
                product_slug=selected_product.slug,
                order_history__order_date__gte=thirty_days_ago
            ).select_related('order_history')
            
            for item in product_items:
                date_key = item.order_history.order_date.strftime('%Y-%m-%d')
                sales_data[date_key] += item.quantity
            
            for i in range(30):
                date = (timezone.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
                product_sales_labels.append((timezone.now() - timedelta(days=29-i)).strftime('%d/%m'))
                product_sales_values.append(sales_data.get(date, 0))
        except Product.DoesNotExist:
            pass
    
    # Top produits les mieux vendus (sur tous les temps)
    best_selling_products = OrderHistoryItem.objects.values(
        'product_slug', 'product_name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('quantity') * Sum('product_price') / Count('id')
    ).order_by('-total_quantity')[:10]
    
    # Enrichir avec les infos du produit actuel (stock, etc.)
    best_sellers_list = []
    for item in best_selling_products:
        try:
            product = Product.objects.get(slug=item['product_slug'])
            best_sellers_list.append({
                'name': item['product_name'],
                'total_sold': item['total_quantity'],
                'current_stock': product.quantity,
                'price': product.price,
                'slug': product.slug,
            })
        except Product.DoesNotExist:
            # Produit supprimé, on garde quand même les stats
            best_sellers_list.append({
                'name': item['product_name'],
                'total_sold': item['total_quantity'],
                'current_stock': 'N/A',
                'price': 'N/A',
                'slug': None,
            })
    
    context = {
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'orders': orders[:50],  # Limiter à 50 commandes récentes
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'period_filter': period_filter,
        'deleted_users_with_orders': deleted_users_with_orders,
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_values': json.dumps(revenue_values),
        'products_list': products_list,
        'selected_product': selected_product,
        'product_sales_labels': json.dumps(product_sales_labels),
        'product_sales_values': json.dumps(product_sales_values),
        'best_selling_products': best_sellers_list,
    }
    
    return render(request, 'store/admin_dashboard.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard_nl(request):
    """Version néerlandaise du tableau de bord administrateur"""
    
    # Gestion de la mise à jour du stock
    if request.method == 'POST' and 'update_stock' in request.POST:
        product_id = request.POST.get('product_id')
        new_quantity = request.POST.get('quantity')
        
        try:
            product = Product.objects.get(id=product_id)
            product.quantity = int(new_quantity)
            product.save()
            messages.success(request, f"Voorraad van '{product.name}' bijgewerkt naar {new_quantity} eenheden.")
        except Product.DoesNotExist:
            messages.error(request, "Product niet gevonden.")
        except ValueError:
            messages.error(request, "Ongeldige hoeveelheid.")
        
        return redirect('admin-dashboard-nl')
    
    # Filtres pour les commandes
    period_filter = request.GET.get('period', 'all')
    
    # Récupérer toutes les commandes
    orders = OrderHistory.objects.all().order_by('-order_date')
    
    # Appliquer les filtres de période
    if period_filter == 'today':
        orders = orders.filter(order_date__date=timezone.now().date())
    elif period_filter == 'week':
        orders = orders.filter(order_date__gte=timezone.now() - timedelta(days=7))
    elif period_filter == 'month':
        orders = orders.filter(order_date__gte=timezone.now() - timedelta(days=30))
    
    # Produits en rupture de stock
    out_of_stock = Product.objects.filter(quantity=0).order_by('name')
    
    # Produits avec stock faible (moins de 5 unités)
    low_stock = Product.objects.filter(quantity__gt=0, quantity__lte=5).order_by('quantity', 'name')
    
    # Statistiques
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    
    # Comptes supprimés
    deleted_users = DeletedUser.objects.all().order_by('-deleted_at')
    
    # Pour chaque compte supprimé, récupérer son historique de commandes
    deleted_users_with_orders = []
    for deleted_user in deleted_users:
        # Chercher les commandes avec l'email du compte supprimé
        user_orders = OrderHistory.objects.filter(
            user_email=deleted_user.email
        ).order_by('-order_date')
        
        deleted_users_with_orders.append({
            'deleted_user': deleted_user,
            'orders': user_orders,
            'total_spent': user_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        })
    
    # Données pour les graphiques (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Évolution du chiffre d'affaires
    revenue_data = defaultdict(float)
    revenue_orders = OrderHistory.objects.filter(order_date__gte=thirty_days_ago).order_by('order_date')
    for order in revenue_orders:
        date_key = order.order_date.strftime('%Y-%m-%d')
        revenue_data[date_key] += order.total_amount
    
    # Préparer les données pour Chart.js (CA total)
    revenue_labels = []
    revenue_values = []
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        revenue_labels.append((timezone.now() - timedelta(days=29-i)).strftime('%d/%m'))
        revenue_values.append(revenue_data.get(date, 0))
    
    # Liste des produits pour le sélecteur
    products_list = Product.objects.all().order_by('name')
    
    # Données de ventes par produit (pour le produit sélectionné via GET)
    selected_product_id = request.GET.get('product_id')
    product_sales_labels = []
    product_sales_values = []
    selected_product = None
    
    if selected_product_id:
        try:
            selected_product = Product.objects.get(id=selected_product_id)
            # Récupérer les ventes du produit sur 30 jours
            sales_data = defaultdict(int)
            product_items = OrderHistoryItem.objects.filter(
                product_slug=selected_product.slug,
                order_history__order_date__gte=thirty_days_ago
            ).select_related('order_history')
            
            for item in product_items:
                date_key = item.order_history.order_date.strftime('%Y-%m-%d')
                sales_data[date_key] += item.quantity
            
            for i in range(30):
                date = (timezone.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
                product_sales_labels.append((timezone.now() - timedelta(days=29-i)).strftime('%d/%m'))
                product_sales_values.append(sales_data.get(date, 0))
        except Product.DoesNotExist:
            pass
    
    # Top produits les mieux vendus (sur tous les temps)
    best_selling_products = OrderHistoryItem.objects.values(
        'product_slug', 'product_name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('quantity') * Sum('product_price') / Count('id')
    ).order_by('-total_quantity')[:10]
    
    # Enrichir avec les infos du produit actuel (stock, etc.)
    best_sellers_list = []
    for item in best_selling_products:
        try:
            product = Product.objects.get(slug=item['product_slug'])
            best_sellers_list.append({
                'name': item['product_name'],
                'total_sold': item['total_quantity'],
                'current_stock': product.quantity,
                'price': product.price,
                'slug': product.slug,
            })
        except Product.DoesNotExist:
            # Produit supprimé, on garde quand même les stats
            best_sellers_list.append({
                'name': item['product_name'],
                'total_sold': item['total_quantity'],
                'current_stock': 'N/A',
                'price': 'N/A',
                'slug': None,
            })
    
    context = {
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'orders': orders[:50],  # Limiter à 50 commandes récentes
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'period_filter': period_filter,
        'deleted_users_with_orders': deleted_users_with_orders,
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_values': json.dumps(revenue_values),
        'products_list': products_list,
        'selected_product': selected_product,
        'product_sales_labels': json.dumps(product_sales_labels),
        'product_sales_values': json.dumps(product_sales_values),
        'best_selling_products': best_sellers_list,
        'lang': 'nl'
    }
    
    return render(request, 'store/admin_dashboard_nl.html', context)
