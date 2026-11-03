"""Тест контракта стартовых фикстур: каталог из `products.yaml` пригоден для
демонстрации правила варианта 8 (цена и остаток заданы, покупка списывает
экземпляр)."""

from django.test import TestCase

from shop.models import Product, Purchase


class StartFixtureTestCase(TestCase):
    fixtures = ["products.yaml"]

    def test_catalog_of_four_products_is_loaded(self):
        self.assertEqual(Product.objects.count(), 4)

    def test_every_product_has_price_and_stock(self):
        for item in Product.objects.all():
            self.assertGreater(item.price, 0, f"у «{item.name}» нет цены")
            self.assertGreater(item.quantity, 0, f"«{item.name}» не в наличии")

    def test_product_names_are_unique(self):
        names = list(Product.objects.values_list("name", flat=True))
        self.assertEqual(len(names), len(set(names)))

    def test_purchasing_fixture_product_reduces_its_stock(self):
        headphones = Product.objects.get(name="Наушники")
        Purchase.objects.create(product=headphones, person="Иванов",
                                address="ул. Светлая, 1")
        headphones.refresh_from_db()
        self.assertEqual(headphones.quantity, 30 - 1)

    def test_tenth_sale_of_fixture_product_raises_its_price(self):
        monitor = Product.objects.get(name="Монитор")
        Product.objects.filter(pk=monitor.pk).update(quantity=10)
        monitor.refresh_from_db()
        for index in range(10):
            Purchase.objects.create(
                product=monitor, person=f"Покупатель {index}",
                address="ул. Светлая, 1")
        monitor.refresh_from_db()
        self.assertEqual(monitor.price, 23000)
        self.assertEqual(monitor.quantity, 0)
