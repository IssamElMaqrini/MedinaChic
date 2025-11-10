from pprint import pprint

import stripe
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
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
    products = Product.objects.all()

    return render(request, 'store/index.html', {'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail.html', context={'product': product})

def add_to_cart(request, slug):
    user: Shopper = request.user
    user.add_to_cart(slug=slug)

    return redirect(reverse('product', kwargs={'slug': slug}))


@login_required
def cart(request):
    orders = Order.objects.filter(user=request.user)
    if orders.count() == 0:
        return redirect('index')
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(queryset=orders)
    return render(request, 'store/cart.html', context={"forms": formset})

def update_quantities(request):
    OrderFormSet = modelformset_factory(Order, form=OrderForm, extra=0)
    formset = OrderFormSet(request.POST, queryset=Order.objects.filter(user=request.user))
    if formset.is_valid():
        formset.save()

    return redirect('cart')

def create_checkout_session(request):
    cart = request.user.cart

    line_items = [{"price": order.product.stripe_id,
                   "quantity": order.quantity}for order in cart.orders.all()]

    checkout_data = {
        "line_items": line_items,
        "mode": 'payment',
        "locale": 'fr',
        "shipping_address_collection": {"allowed_countries": ["BE"]},
        "success_url": request.build_absolute_uri(reverse('checkout-success')),
        "cancel_url": 'http://127.0.0.1:8000/',
    }

    if request.user.stripe_id:
        checkout_data["customer"] = request.user.stripe_id
    else:
        checkout_data["customer_email"] = request.user.email

    session = stripe.checkout.Session.create(**checkout_data)
    return redirect(session.url, code=303)

def checkout_success(request):
    return render(request, 'store/success.html')

def delete_cart(request):
    if cart := request.user.cart:
        cart.delete()

    return redirect('index')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = "whsec_e306f9c396be9a79003338f10bcdb0977cec6abb8114ab52afacd198e1202314"
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

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
    user.stripe_id=data['customer']
    user.cart.delete()
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


def apropos(request):
    return render(request, 'store/apropos.html')


def produits_par_categorie(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'store/index.html', {'products': products, 'selected_category': category})

def index_nl(request):
    products = Product.objects.all()
    return render(request, 'store/index_nl.html', {'products': products, 'lang': 'nl'})

def product_detail_nl(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/detail_nl.html', context={'product': product, 'lang': 'nl'})

def apropos_nl(request):
    return render(request, 'store/apropos_nl.html')

@login_required
def cart_nl(request):
    orders = Order.objects.filter(user=request.user)
    if orders.count() == 0:
        return redirect('index-nl')  # redirige vers la page d'accueil NL si panier vide

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