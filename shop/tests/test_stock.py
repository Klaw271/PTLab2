from django.test import TestCase

from shop.models import OutOfStockError, Product, Purchase


def buy(product, person="Покупатель"):
    return Purchase.objects.create(product=product, person=person,
                                   address="ул. Светлая, 1")


class StockTestCase(TestCase):
    """Вариант 8: магазин электроники с ограниченным количеством товара."""

    def setUp(self):
        self.phone = Product.objects.create(name="Смартфон", price=1000,
                                            quantity=25)
        self.headphones = Product.objects.create(name="Наушники", price=999,
                                                 quantity=12)

    def test_correctness_types(self):
        self.assertIsInstance(self.phone.quantity, int)
        self.assertIsInstance(self.phone.in_stock(), bool)

    def test_sale_reduces_quantity(self):
        buy(self.phone)
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.quantity, 24)

    def test_price_unchanged_before_ten_sales(self):
        for i in range(9):
            buy(self.phone, f"Покупатель {i}")
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.price, 1000)
        self.assertEqual(self.phone.quantity, 16)

    def test_price_increases_after_ten_sales(self):
        for i in range(10):
            buy(self.phone, f"Покупатель {i}")
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.price, 1150)

    def test_price_increases_again_after_twenty_sales(self):
        for i in range(20):
            buy(self.phone, f"Покупатель {i}")
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.price, 1322)
        self.assertEqual(self.phone.quantity, 5)

    def test_price_increase_is_integer_rounded_down(self):
        for i in range(10):
            buy(self.headphones, f"Покупатель {i}")
        self.headphones.refresh_from_db()
        self.assertEqual(self.headphones.price, 1148)

    def test_only_sold_product_becomes_dearer(self):
        for i in range(10):
            buy(self.phone, f"Покупатель {i}")
        self.headphones.refresh_from_db()
        self.assertEqual(self.headphones.price, 999)

    def test_sold_units_counts_purchases(self):
        for i in range(3):
            buy(self.phone, f"Покупатель {i}")
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.sold_units(), 3)

    def test_sale_without_stock_is_impossible(self):
        monitor = Product.objects.create(name="Монитор", price=500, quantity=0)
        with self.assertRaises(OutOfStockError):
            buy(monitor)
        self.assertEqual(Purchase.objects.filter(product=monitor).count(), 0)
        monitor.refresh_from_db()
        self.assertEqual(monitor.quantity, 0)

    def test_last_unit_sold_then_product_ends(self):
        monitor = Product.objects.create(name="Монитор", price=500, quantity=1)
        buy(monitor)
        monitor.refresh_from_db()
        self.assertEqual(monitor.quantity, 0)
        self.assertFalse(monitor.in_stock())
        with self.assertRaises(OutOfStockError):
            buy(monitor)
