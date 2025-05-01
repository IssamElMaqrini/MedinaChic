from django.test import TestCase
from accounts.models import Shopper
from store.models import Product

class UserTests(TestCase):
    def setUp(self):
        Product.objects.create(
            name='Test Product',
            price=100,
            quantity=10,
            description='test description'
        )
        self.user: Shopper = Shopper.objects.create_user(
            email="test@email.com",
            password="1234"
        )

    def test_add_to_cart(self):
        self.user.add_to_cart(slug="test-product")
        self.assertEqual(self.user.cart.orders.count(),1)
        self.assertEqual(self.user.cart.orders.first().product.slug, "test-product")
        self.user.add_to_cart(slug="test-product")
        self.assertEqual(self.user.cart.orders.count(), 1)
        self.assertEqual(self.user.cart.orders.first().quantity, 2)



