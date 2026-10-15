from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import CreateView

from .models import OutOfStockError, Product, Purchase


def index(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'shop/index.html', context)


class PurchaseCreate(CreateView):
    model = Purchase
    fields = ['product', 'person', 'address']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = Product.objects.get(pk=self.kwargs['product_id'])
        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
        except OutOfStockError:
            form.add_error('product', 'Товар закончился, покупка невозможна')
            return self.render_to_response(self.get_context_data(form=form))
        return HttpResponse(f'Спасибо за покупку, {self.object.person}!')
