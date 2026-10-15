from django.test import TestCase, Client
from shop.models import Product, Purchase
from shop.views import PurchaseCreate


class PurchaseCreateTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_webpage_accessibility(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class PurchaseViewTestCase(TestCase):
    """Покупка через веб-интерфейс: учёт количества и рост цены."""

    def setUp(self):
        self.client = Client()
        self.phone = Product.objects.create(name="Смартфон", price=1000,
                                            quantity=2)
        self.monitor = Product.objects.create(name="Монитор", price=500,
                                              quantity=0)

    def post_purchase(self, product, person="Иванов"):
        return self.client.post(f'/buy/{product.id}/',
                                {'product': product.id,
                                 'person': person,
                                 'address': 'ул. Светлая, 1'})

    def test_index_shows_quantity_column(self):
        response = self.client.get('/')
        self.assertContains(response, 'В наличии')
        self.assertContains(response, 'Смартфон')
        self.assertContains(response, 'нет в наличии')

    def test_index_links_only_available_products(self):
        response = self.client.get('/')
        self.assertContains(response, f'/buy/{self.phone.id}')
        self.assertNotContains(response, f'/buy/{self.monitor.id}')

    def test_buy_page_of_available_product_shows_form(self):
        response = self.client.get(f'/buy/{self.phone.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Смартфон')
        self.assertContains(response, 'Введите свое имя')

    def test_buy_page_of_sold_out_product_has_no_form(self):
        response = self.client.get(f'/buy/{self.monitor.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Товар закончился')
        self.assertNotContains(response, 'Введите свое имя')

    def test_post_purchase_thanks_and_reduces_stock(self):
        response = self.post_purchase(self.phone)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спасибо за покупку, Иванов!')
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.quantity, 1)
        self.assertEqual(
            Purchase.objects.filter(product=self.phone).count(), 1)

    def test_post_purchase_of_sold_out_product_is_rejected(self):
        response = self.post_purchase(self.monitor)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Товар закончился, покупка невозможна')
        self.assertEqual(
            Purchase.objects.filter(product=self.monitor).count(), 0)

    def test_ten_web_purchases_raise_price(self):
        notebook = Product.objects.create(name="Ноутбук", price=1000,
                                          quantity=10)
        for i in range(10):
            response = self.post_purchase(notebook, f"Покупатель {i}")
            self.assertContains(response, 'Спасибо за покупку')
        notebook.refresh_from_db()
        self.assertEqual(notebook.price, 1150)
        self.assertEqual(notebook.quantity, 0)
        self.assertEqual(notebook.sold_units(), 10)

    def test_purchase_create_view_configuration(self):
        self.assertEqual(PurchaseCreate.model, Purchase)
        self.assertEqual(PurchaseCreate.fields, ['product', 'person',
                                                 'address'])
