"""Юнит-тесты бизнес-правила варианта 8 без обращения к базе данных.

Товар и покупка создаются несейвами, а `sold_units()` и `save()` подменяются
двойниками, поэтому проверяется только арифметика правила: списание остатка,
момент повышения цены, округление и запрет продажи без склада.
"""

from unittest import mock

from django.db.models import CASCADE, Model
from django.test import SimpleTestCase

from shop.models import OutOfStockError, Product, Purchase


def product(price=1000, quantity=25, sold_units=0):
    """Несохранённый товар с известным числом уже проданных экземпляров."""
    item = Product(name="Смартфон", price=price, quantity=quantity)
    item.sold_units = mock.Mock(return_value=sold_units)
    item.save = mock.Mock()
    return item


class RegisterSaleUnitTest(SimpleTestCase):
    def test_quantity_is_reduced_and_saved(self):
        item = product(quantity=25)
        item.register_sale()
        self.assertEqual(item.quantity, 24)
        item.save.assert_called_once_with()

    def test_price_is_unchanged_until_ninth_sale(self):
        for sold in range(9):
            item = product(sold_units=sold)
            item.register_sale()
            self.assertEqual(item.price, 1000, f"после {sold + 1}-й продажи")
            self.assertEqual(item.quantity, 24)

    def test_price_is_raised_on_tenth_sale(self):
        item = product(sold_units=9)
        item.register_sale()
        self.assertEqual(item.price, 1150)
        item.save.assert_called_once_with()

    def test_price_is_raised_again_on_twentieth_sale(self):
        item = product(price=1150, sold_units=19)
        item.register_sale()
        self.assertEqual(item.price, 1322)

    def test_price_increase_is_rounded_down(self):
        item = product(price=999, sold_units=9)
        item.register_sale()
        self.assertEqual(item.price, 1148)

    def test_rule_uses_step_and_percent_of_product(self):
        item = product(sold_units=2)
        item.price_step_units = 3
        item.price_up_percent = 50
        item.register_sale()
        self.assertEqual(item.price, 1500)

    def test_sale_without_stock_keeps_product_untouched(self):
        item = product(quantity=0)
        with self.assertRaises(OutOfStockError):
            item.register_sale()
        self.assertEqual(item.quantity, 0)
        self.assertEqual(item.price, 1000)
        item.save.assert_not_called()

    def test_out_of_stock_message_names_the_product(self):
        item = product(quantity=0)
        with self.assertRaises(OutOfStockError) as caught:
            item.register_sale()
        self.assertIn("Смартфон", str(caught.exception))


class PurchaseSaveUnitTest(SimpleTestCase):
    def purchase(self, item, pk=None):
        return Purchase(pk=pk, product=item, person="Иванов",
                        address="ул. Светлая, 1")

    def test_new_purchase_registers_one_sale(self):
        item = product()
        item.register_sale = mock.Mock()
        with mock.patch.object(Model, "save") as model_save:
            self.purchase(item).save()
        item.register_sale.assert_called_once_with()
        model_save.assert_called_once_with()

    def test_existing_purchase_is_not_counted_twice(self):
        item = product()
        item.register_sale = mock.Mock()
        with mock.patch.object(Model, "save"):
            self.purchase(item, pk=1).save()
        item.register_sale.assert_not_called()

    def test_purchase_is_linked_to_product_by_related_name(self):
        relation = Purchase._meta.get_field("product").remote_field
        self.assertEqual(relation.related_name, "purchases")
        self.assertEqual(relation.on_delete, CASCADE)
