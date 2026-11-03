"""Тесты валидации полей моделей и формы оформления покупки.

Проверки полей `Product` не требуют базы данных, поэтому вынесены в
`SimpleTestCase`; форма с внешним ключом на товар обращается к queryset, значит
её тесты остаются в `TestCase`.
"""

from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.test import SimpleTestCase, TestCase

from shop.models import Product, Purchase

PurchaseForm = modelform_factory(Purchase,
                                 fields=["product", "person", "address"])


def product(**kwargs):
    params = {"name": "Смартфон", "price": 1000, "quantity": 5}
    params.update(kwargs)
    return Product(**params)


class ProductFieldValidationTest(SimpleTestCase):
    def test_correct_product_passes_validation(self):
        product().full_clean()

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            product(price=-1).full_clean()
        self.assertIn("price", caught.exception.message_dict)

    def test_price_has_to_be_a_number(self):
        with self.assertRaises(ValidationError) as caught:
            product(price="не число").full_clean()
        self.assertIn("price", caught.exception.message_dict)

    def test_negative_stock_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            product(quantity=-2).full_clean()
        self.assertIn("quantity", caught.exception.message_dict)

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            product(name="").full_clean()
        self.assertIn("name", caught.exception.message_dict)

    def test_name_longer_than_field_limit_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            product(name="x" * 201).full_clean()
        self.assertIn("name", caught.exception.message_dict)

    def test_missing_quantity_is_rejected(self):
        with self.assertRaises(ValidationError) as caught:
            product(quantity=None).full_clean()
        self.assertIn("quantity", caught.exception.message_dict)


class PurchaseFormValidationTest(TestCase):
    def setUp(self):
        self.item = Product.objects.create(name="Наушники", price=3000,
                                           quantity=4)

    def form(self, **overrides):
        data = {"product": self.item.pk, "person": "Иванов",
                "address": "ул. Светлая, 1"}
        data.update(overrides)
        return PurchaseForm(data)

    def test_complete_form_is_valid(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_person_is_required(self):
        self.assertIn("person", self.form(person="").errors)

    def test_address_is_required(self):
        self.assertIn("address", self.form(address="").errors)

    def test_product_is_required(self):
        self.assertIn("product", self.form(product="").errors)

    def test_unknown_product_is_rejected(self):
        self.assertIn("product", self.form(product=999999).errors)

    def test_date_is_filled_by_the_model_not_by_the_form(self):
        self.assertNotIn("date", PurchaseForm().fields)
        self.assertTrue(Purchase._meta.get_field("date").auto_now_add)
