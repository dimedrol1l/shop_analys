import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from cy19346_project.models import Order, APIKey
import pytz

class Command(BaseCommand):
    help = 'Import orders from Ozon API'

    def fetch_ozon_orders(self, client_id, api_key):
        url = "https://api-seller.ozon.ru/v2/posting/fbs/list"
        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        today = datetime.utcnow()
        thirty_days_ago = today - timedelta(days=30)  # Изменим на более длинный период
        data = {
            "dir": "ASC",
            "filter": {
                "since": thirty_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "to": today.strftime('%Y-%m-%dT%H:%M:%SZ')
            },
            "limit": 100,  # Увеличим лимит
            "offset": 0,
            "translit": False,
            "with": {"analytics_data": True, "financial_data": True}
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
            self.stdout.write(f"Client ID: {client_id}")
            self.stdout.write(f"API Key: {api_key}")
            orders = self.fetch_ozon_orders(client_id, api_key)
            if orders:
                self.import_orders_to_db(orders)
        except APIKey.DoesNotExist:
            self.stderr.write("API Key for Ozon not found")

    def import_orders_to_db(self, orders):
        utc = pytz.UTC
        for order in orders['result']:
            for product in order['products']:
                order_instance = Order(
                    order_id=order['order_id'],
                    posting_number=order.get('posting_number'),
                    status=order.get('status'),
                    cancel_reason_id=order.get('cancel_reason_id'),
                    created_at=utc.localize(datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%SZ')),
                    in_process_at=utc.localize(datetime.strptime(order['in_process_at'], '%Y-%m-%dT%H:%M:%SZ')),
                    shipment_date=utc.localize(datetime.strptime(order['shipment_date'], '%Y-%m-%dT%H:%M:%SZ')),
                    sku=product['sku'],
                    product_name=product['name'],
                    quantity=product['quantity'],
                    offer_id=product.get('offer_id'),
                    price=product.get('price'),
                    mandatory_mark=','.join(product.get('mandatory_mark', [])),
                    barcodes=order.get('barcodes'),
                    analytics_data=str(order.get('analytics_data')),
                    financial_data=str(order.get('financial_data')),
                    is_fraud=False  # Example default value
                )
                self.stdout.write(f"Importing order {order['order_id']} - product {product['sku']}")
                order_instance.save()
