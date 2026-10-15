from django.db import models


class OutOfStockError(Exception):
    """Товар закончился: продажа невозможна."""


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=0)

    # Вариант 8: каждые 10 проданных экземпляров повышают цену на 15%.
    price_step_units = 10
    price_up_percent = 5

    def in_stock(self):
        return self.quantity > 0

    def sold_units(self):
        return self.purchases.count()

    def register_sale(self):
        if not self.in_stock():
            raise OutOfStockError(f"Товар «{self.name}» закончился")

        self.quantity -= 1
        if (self.sold_units() + 1) % self.price_step_units == 0:
            self.price += self.price * self.price_up_percent // 100
        self.save()


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='purchases')
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.product.register_sale()
        super().save(*args, **kwargs)
