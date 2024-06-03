from django.shortcuts import render
from django.http import HttpResponse
from .models import Order


def index(request):
    return render(request, 'index.html')


def search_orders(request):
    customer_id = request.GET.get('customer_id')
    orders = Order.objects.filter(order_id=customer_id)
    return render(request, 'orders/search.html', {'orders': orders})

