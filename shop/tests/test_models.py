from datetime import datetime

from django.test import TestCase

from shop.models import Product, Purchase


class ProductTestCase(TestCase):
    def setUp(self):
        Product.objects.create(name="book", price="740", quantity=10)
        Product.objects.create(name="pencil", price="50", quantity=10)

    def test_correctness_types(self):
        self.assertIsInstance(Product.objects.get(name="book").name, str)
        self.assertIsInstance(Product.objects.get(name="book").price, int)
        self.assertIsInstance(Product.objects.get(name="pencil").name, str)
        self.assertIsInstance(Product.objects.get(name="pencil").price, int)

    def test_correctness_data(self):
        self.assertTrue(Product.objects.get(name="book").price == 740)
        self.assertTrue(Product.objects.get(name="pencil").price == 50)


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.product_book = Product.objects.create(name="book", price="740",
                                                   quantity=10)
        self.datetime = datetime.now()
        Purchase.objects.create(product=self.product_book,
                                person="Ivanov",
                                address="Svetlaya St.")

    def purchase(self):
        return Purchase.objects.get(product=self.product_book)

    def test_correctness_types(self):
        self.assertIsInstance(self.purchase().person, str)
        self.assertIsInstance(self.purchase().address, str)
        self.assertIsInstance(self.purchase().date, datetime)

    def test_correctness_data(self):
        self.assertEqual(self.purchase().person, "Ivanov")
        self.assertEqual(self.purchase().address, "Svetlaya St.")
        self.assertEqual(self.purchase().date.replace(microsecond=0),
                         self.datetime.replace(microsecond=0))
