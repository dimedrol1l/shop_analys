import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from cy19346_project.models import Order, APIKey
import pytz

class Command(BaseCommand):
    help = 'Imports orders into the database'

    def handle(self, *args, **options):
        api_key_instance = APIKey.objects.filter(marketplace="Ozon").first()
        if not api_key_instance:
            self.stdout.write(self.style.ERROR('API Key for Ozon not found'))
            return

        headers = {
            'Client-Id': api_key_instance.client_id,
            'Api-Key': api_key_instance.api_key,
        }

        url = 'https://api-seller.ozon.ru/v2/posting/fbs/list'

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
            "with": {
                "analytics_data": True,
                "financial_data": True
            }
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            orders = response.json().get('result', [])
            if orders:
                self.import_orders_to_db(orders)
            else:
                self.stdout.write(self.style.WARNING("No orders found in the API response"))
        else:
            self.stderr.write(f"Ошибка: {response.status_code} - {response.text}")

    def import_orders_to_db(self, orders):
        utc = pytz.UTC
        for order in orders:
            for product in order['products']:
                order_instance, created = Order.objects.update_or_create(
                    order_id=order['order_id'],
                    defaults={
                        'posting_number': order.get('posting_number', ''),
                        'status': order.get('status', ''),
                        'cancel_reason_id': order.get('cancel_reason_id', ''),
                        'created_at': utc.localize(datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%SZ')),
                        'in_process_at': utc.localize(datetime.strptime(order['in_process_at'], '%Y-%m-%dT%H:%M:%SZ')),
                        'shipment_date': utc.localize(datetime.strptime(order['shipment_date'], '%Y-%m-%dT%H:%M:%SZ')),
                        'sku': product['sku'],
                        'product_name': product['name'],
                        'quantity': product['quantity'],
                        'offer_id': product.get('offer_id', ''),
                        'price': product.get('price', 0),
                        'mandatory_mark': ','.join(product.get('mandatory_mark', [])),
                        'barcodes': order.get('barcodes', ''),
                        'analytics_data': str(order.get('analytics_data', '')),
                        'financial_data': str(order.get('financial_data', '')),
                        'is_fraud': False,  # Example default value
                        'customer_id': order.get('customer_id', ''),
                        'order_date': utc.localize(datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%SZ'))
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created new order {order['order_id']} - product {product['sku']}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Updated order {order['order_id']} - product {product['sku']}"))
