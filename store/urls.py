from django.urls import path
from store.views import index, product_detail, add_to_cart, cart, delete_cart, create_checkout_session, \
    checkout_success, checkout_cancelled, stripe_webhook, update_quantities, apropos, produits_par_categorie, product_detail_nl, apropos_nl, \
    cart_nl, produits_par_categorie_nl, api_products, order_history, order_history_nl, api_signup, \
    add_review, add_review_nl, delete_review, generate_invoice
from store.admin_views import admin_dashboard, admin_dashboard_nl

urlpatterns = [
    path('admin-dashboard/', admin_dashboard, name="admin-dashboard"),
    path('nl/admin-dashboard/', admin_dashboard_nl, name='admin-dashboard-nl'),
    path('cart/', cart, name="cart"),
    path('nl/cart/', cart_nl, name='cart-nl'),
    path('history/', order_history, name="order-history"),
    path('nl/history/', order_history_nl, name='order-history-nl'),
    path('invoice/<int:order_id>/', generate_invoice, name="generate-invoice"),
    path('apropos/', apropos, name="apropos"),
    path('nl/overons', apropos_nl, name="apropos-nl"),
    path('cart/update_quantities/', update_quantities, name="update-quantities"),
    path('stripe-webhook/', stripe_webhook, name="stripe-webhook"),
    path('cart/success', checkout_success, name="checkout-success"),
    path('cart/cancelled', checkout_cancelled, name="checkout-cancelled"),
    path('cart/create-checkout-session', create_checkout_session, name="create-checkout-session"),
    path('cart/delete/', delete_cart, name="delete-cart"),
    path('product/<str:slug>/', product_detail, name="product"),
    path('nl/product/<str:slug>/', product_detail_nl, name='product-nl'),
    path('product/<str:slug>/add-to-cart/', add_to_cart, name="add-to-cart"),
    path('product/<str:slug>/review/', add_review, name="add-review"),
    path('nl/product/<str:slug>/review/', add_review_nl, name="add-review-nl"),
    path('review/<int:review_id>/delete/', delete_review, name="delete-review"),
    path('categorie/<str:category>/', produits_par_categorie, name='products-by-category'),
    path('nl/categorie/<str:category>/', produits_par_categorie_nl, name='products-by-category-nl'),
    path('api/products/', api_products, name='api-products'),
    path('api/signup/', api_signup, name='api-signup'),
]