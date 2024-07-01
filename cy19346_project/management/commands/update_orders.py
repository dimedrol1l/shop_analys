from django.core.management.base import BaseCommand
from cy19346_project.models import Order, APIKey
import requests
from datetime import datetime, timedelta
import pytz

class Command(BaseCommand):
    help = 'Update orders from Ozon API'

    def handle(self, *args, **options):
        api_keys = APIKey.objects.all()
        for api_key_obj in api_keys:
            client_id = api_key_obj.client_id
            api_key = api_key_obj.api_key
            user = api_key_obj.user

            self.stdout.write(f"Client ID: {client_id}")
            self.stdout.write(f"API Key: {api_key}")

            orders = self.fetch_ozon_orders(client_id, api_key)
            if orders:
                self.update_orders_in_db(orders, user)
            else:
                self.stdout.write(self.style.WARNING("No orders found in the API response"))

    def fetch_ozon_orders(self, client_id, api_key):
        url = "https://api-seller.ozon.ru/v2/posting/fbs/list"
        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
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
            return response.json()
        else:
            self.stderr.write(f"Error: {response.status_code} - {response.text}")
            return None

    def update_orders_in_db(self, orders, user):
        utc = pytz.UTC
        for order in orders['result']:
            self.stdout.write(f"Processing order {order['order_id']}")
            for product in order['products']:
                self.stdout.write(f"Processing product {product['sku']} for order {order['order_id']}")
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
