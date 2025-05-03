from django.urls import path
from store.views import index, product_detail, add_to_cart, cart, delete_cart, create_checkout_session, \
    checkout_success, stripe_webhook, update_quantities, apropos, produits_par_categorie, product_detail_nl, apropos_nl, \
    cart_nl, produits_par_categorie_nl, api_products

urlpatterns = [
    path('cart/', cart, name="cart"),
    path('nl/cart/', cart_nl, name='cart-nl'),
    path('apropos/', apropos, name="apropos"),
    path('nl/overons', apropos_nl, name="apropos-nl"),
    path('cart/update_quantities/', update_quantities, name="update-quantities"),
    path('stripe-webhook/', stripe_webhook, name="stripe-webhook"),
    path('cart/success', checkout_success, name="checkout-success"),
    path('cart/create-checkout-session', create_checkout_session, name="create-checkout-session"),
    path('cart/delete/', delete_cart, name="delete-cart"),
    path('product/<str:slug>/', product_detail, name="product"),
    path('nl/product/<str:slug>/', product_detail_nl, name='product-nl'),
    path('product/<str:slug>/add-to-cart/', add_to_cart, name="add-to-cart"),
    path('categorie/<str:category>/', produits_par_categorie, name='products-by-category'),
    path('nl/categorie/<str:category>/', produits_par_categorie_nl, name='products-by-category-nl'),
    path('api/products/', api_products, name='api-products'),
]