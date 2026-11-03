"""Тесты представлений на уровне контекста и шаблона: какие данные попадают
на страницу и как реагирует форма покупки на некорректный ввод."""

from django.test import Client, TestCase

from shop.models import Product, Purchase


class IndexContextTestCase(TestCase):
    def setUp(self):
        self.phone = Product.objects.create(name="Смартфон", price=1000,
                                            quantity=3)
        self.monitor = Product.objects.create(name="Монитор", price=500,
                                              quantity=0)
        self.response = Client().get("/")

    def test_catalog_template_is_rendered(self):
        self.assertIn("shop/index.html",
                      [t.name for t in self.response.templates])

    def test_context_contains_every_product(self):
        names = sorted(p.name for p in self.response.context["products"])
        self.assertEqual(names, ["Монитор", "Смартфон"])

    def test_sold_out_product_is_still_shown_without_link(self):
        self.assertContains(self.response, "Монитор")
        self.assertContains(self.response, "нет в наличии")
        self.assertNotContains(self.response,
                               f"/buy/{self.monitor.id}")

    def test_product_in_stock_is_linked_to_purchase_page(self):
        self.assertContains(self.response, f"/buy/{self.phone.id}")


class PurchasePageContextTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name="Ноутбук", price=60000,
                                              quantity=2)

    def test_buy_page_shows_the_product_from_the_address(self):
        response = self.client.get(f"/buy/{self.product.id}/")
        self.assertIn("shop/purchase_form.html",
                      [t.name for t in response.templates])
        self.assertEqual(response.context["product"].pk, self.product.pk)
        self.assertIn("form", response.context)

    def test_buy_page_of_missing_product_returns_404(self):
        response = self.client.get("/buy/999999/")
        self.assertEqual(response.status_code, 404)

    def test_purchase_of_missing_product_returns_404(self):
        response = self.client.post(
            "/buy/999999/",
            {"product": 999999, "person": "Иванов",
             "address": "ул. Светлая, 1"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_valid_form_answers_with_plain_text(self):
        response = self.client.post(
            f"/buy/{self.product.id}/",
            {"product": self.product.pk, "person": "Петров",
             "address": "ул. Ленина, 5"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"),
                         "Спасибо за покупку, Петров!")
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

    def test_incomplete_form_is_redisplayed_with_errors(self):
        response = self.client.post(
            f"/buy/{self.product.id}/",
            {"product": self.product.pk, "person": "", "address": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn("person", response.context["form"].errors)
        self.assertContains(response, "This field is required")

    def test_incomplete_form_does_not_change_stock(self):
        self.client.post(f"/buy/{self.product.id}/",
                         {"product": self.product.pk, "person": "",
                          "address": ""})
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 2)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_repost_after_the_last_unit_sold_keeps_stock_at_zero(self):
        for name in ("Первый", "Второй"):
            self.client.post(
                f"/buy/{self.product.id}/",
                {"product": self.product.pk, "person": name,
                 "address": "ул. Ленина, 5"})
        response = self.client.post(
            f"/buy/{self.product.id}/",
            {"product": self.product.pk, "person": "Третий",
             "address": "ул. Ленина, 5"})
        self.assertContains(response, "Товар закончился, покупка невозможна")
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 0)
        self.assertEqual(Purchase.objects.count(), 2)
