"""Тесты маршрутизации: сопоставление URL и построение адресов страницы
покупки. База данных для проверки адресации не нужна."""

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve, reverse

from shop import views


class UrlsTestCase(SimpleTestCase):
    def test_root_shows_catalog(self):
        match = resolve("/")
        self.assertIs(match.func, views.index)
        self.assertEqual(match.url_name, "index")

    def test_buy_route_passes_product_id_to_view(self):
        match = resolve("/buy/12/")
        self.assertEqual(match.url_name, "buy")
        self.assertEqual(match.kwargs, {"product_id": 12})

    def test_buy_url_is_built_from_product_id(self):
        self.assertEqual(reverse("buy", kwargs={"product_id": 3}), "/buy/3/")

    def test_non_numeric_product_id_does_not_match(self):
        with self.assertRaises(Resolver404):
            resolve("/buy/abc/")

    def test_missing_trailing_slash_does_not_match(self):
        with self.assertRaises(Resolver404):
            resolve("/buy/12")

    def test_unknown_page_does_not_match(self):
        with self.assertRaises(Resolver404):
            resolve("/basket/")
