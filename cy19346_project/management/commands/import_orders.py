import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import APIKey, Order
from datetime import datetime, timedelta
import pytz


@login_required
def import_orders(request):
    user = request.user
    api_key_obj = APIKey.objects.filter(user=user).first()
    if not api_key_obj:
        messages.error(request, "Please add your API key first.")
        return redirect('api_keys')

    if request.method == 'POST':
        success = fetch_and_save_orders(api_key_obj)
        if success:
            messages.success(request, "Orders imported successfully.")
            # Устанавливаем флаг, чтобы кнопка больше не отображалась
            user.profile.import_completed = True
            user.profile.save()
            return redirect('index')
        else:
            messages.error(request, "Failed to import orders. Please try again.")

    return render(request, 'import_orders.html')


def fetch_and_save_orders(api_key_obj):
    url = "https://api-seller.ozon.ru/v2/posting/fbs/list"
    headers = {
        "Client-Id": api_key_obj.client_id,
        "Api-Key": api_key_obj.api_key,
        "Content-Type": "application/json"
    }
    today = datetime.utcnow()
    thirty_days_ago = today - timedelta(days=30)
    data = {
        "dir": "ASC",
        "filter": {
            "since": thirty_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "to": today.strftime('%Y-%m-%dT%H:%M:%SZ')
        },
        "limit": 100,
        "offset": 0,
        "with": {"analytics_data": True, "financial_data": True}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        orders = response.json().get('result', [])
        if orders:
            update_orders_in_db(orders, api_key_obj.user)
            return True
    return False


def update_orders_in_db(orders, user):
    utc = pytz.UTC
    for order in orders:
        for product in order['products']:
            Order.objects.update_or_create(
                order_id=order['order_id'],
                defaults={
                    'posting_number': order.get('posting_number', ''),
                    'status': order.get('status', ''),
                    'cancel_reason_id': order.get('cancel_reason_id', ''),
                    'created_at': utc.localize(datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%S%z')),
                    'in_process_at': utc.localize(datetime.strptime(order['in_process_at'], '%Y-%m-%dT%H:%M:%S%z')),
                    'shipment_date': utc.localize(datetime.strptime(order['shipment_date'], '%Y-%m-%dT%H:%M:%S%z')),
                    'sku': product['sku'],
                    'product_name': product.get('name', ''),
                    'quantity': product.get('quantity', 1),
                    'offer_id': product.get('offer_id', ''),
                    'price': product.get('price', 0),
                    'mandatory_mark': product.get('mandatory_mark', ''),
                    'barcodes': ', '.join(product.get('barcodes', [])),
                    'analytics_data': order.get('analytics_data', ''),
                    'financial_data': order.get('financial_data', ''),
                    'is_fraud': order.get('is_fraud', False),
                    'customer_id': order.get('customer_id', ''),
                    'order_date': utc.localize(datetime.strptime(order['order_date'], '%Y-%m-%dT%H:%M:%S%z')),
                    'user': user
                }
            )
