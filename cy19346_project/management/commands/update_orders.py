# /Users/mihailsavic/PycharmProjects/cy19346/cy19346/cy19346_project/management/commands/update_orders.py
import requests
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from cy19346_project.models import Order, APIKey


class Command(BaseCommand):
    help = 'Update orders from Ozon API'

    def fetch_ozon_orders(self, client_id, api_key):
        url = "https://api-seller.ozon.ru/v2/posting/fbs/list"
        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        data = {
            "dir": "ASC",
            "filter": {
                "since": yesterday.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "to": today.strftime('%Y-%m-%dT%H:%M:%SZ')
            },
            "limit": 50,
            "offset": 0,
            "translit": False,
            "with": {"analytics_data": False, "financial_data": False}
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            self.stderr.write(f"Ошибка: {response.status_code} - {response.text}")
            return None

    def handle(self, *args, **options):
        try:
            api_key_obj = APIKey.objects.get(marketplace='Ozon')
            client_id = api_key_obj.client_id
            api_key = api_key_obj.api_key
            orders = self.fetch_ozon_orders(client_id, api_key)
            if orders:
                self.update_orders_in_db(orders)
        except APIKey.DoesNotExist:
            self.stderr.write("API Key for Ozon not found")

    def update_orders_in_db(self, orders):
        for order in orders['result']:
            for product in order['products']:
                created_at = datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                in_process_at = datetime.strptime(order['in_process_at'], '%Y-%m-%dT%H:%M:%SZ').replace(
                    tzinfo=timezone.utc)
                shipment_date = datetime.strptime(order['shipment_date'], '%Y-%m-%dT%H:%M:%SZ').replace(
                    tzinfo=timezone.utc)

                order_instance, created = Order.objects.update_or_create(
                    order_id=order['order_id'],
                    sku=product['sku'],
                    defaults={
                        'order_number': order.get('order_number'),
                        'posting_number': order.get('posting_number'),
                        'status': order.get('status'),
                        'cancel_reason_id': order.get('cancel_reason_id'),
                        'created_at': created_at,
                        'in_process_at': in_process_at,
                        'shipment_date': shipment_date,
                        'product_name': product['name'],
                        'quantity': product['quantity'],
                        'offer_id': product.get('offer_id'),
                        'price': product.get('price'),
                        'mandatory_mark': ','.join(product.get('mandatory_mark', [])),
                        'barcodes': order.get('barcodes'),
                        'analytics_data': str(order.get('analytics_data')),
                        'financial_data': str(order.get('financial_data'))
                    }
                )
                if created:
                    self.stdout.write(f"Created order {order['order_id']} - product {product['sku']}")
                else:
                    self.stdout.write(f"Updated order {order['order_id']} - product {product['sku']}")
