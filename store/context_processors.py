from store.models import Cart, Notification

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


def notifications_processor(request):
    """Add unread notifications count to all templates"""
    notifications_data = {
        'unread_notifications_count': 0
    }
    
    if request.user.is_authenticated:
        try:
            notifications_data['unread_notifications_count'] = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        except:
            pass
    
    return notifications_data
