from django.test import TestCase

from accounts.models import Shopper
from store.models import Product, Cart, Order
from django.urls import reverse

class ProductTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            price=100,
            quantity=20,
            description='test description',
        )

    def test_product_slug_is_automatically_generated(self):
        self.assertEqual(self.product.slug, 'test-product')

    def test_product_absolute_url(self):
        self.assertEqual(self.product.get_absolute_url(), reverse('product', kwargs={'slug': self.product.slug}))


class CartTest(TestCase):
    def setUp(self):
        user = Shopper.objects.create_user(
            email="test@gmail.com",
            password="12345"
        )
        product = Product.objects.create(
            name='Test'
        )
        self.cart =Cart.objects.create(
            user=user,
        )
        order = Order.objects.create(
            user=user,
            product=product,
        )
        self.cart.orders.add(order)
        self.cart.save()

    def test_order_changed_when_cart_when_cart_is_deleted(self):
        orders_pk = [order.pk for order in self.cart.orders.all()]
        self.cart.delete()
        for order_pk in orders_pk:
            order = Order.objects.get(pk=order_pk)
            self.assertTrue(order.ordered)