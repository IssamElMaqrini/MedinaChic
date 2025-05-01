from django.test import TestCase
from django.urls import reverse

from store.models import Product

class StoreTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            price=100,
            quantity=10,
            description='test description',
        )

    def test_product_are_shown_on_index_page(self):
        resp = self.client.get(reverse("index"))

        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.product.name, str(resp.content))