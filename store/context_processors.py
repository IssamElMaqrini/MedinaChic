from store.models import Cart

def cart_processor(request):
    """Add cart info to all templates"""
    cart_data = {
        'has_cart': False,
        'cart_count': 0
    }
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user, ordered=False).first()
            if cart:
                cart_data['has_cart'] = True
                cart_data['cart_count'] = cart.orders.count()
        except:
            pass
    
    return cart_data
