from django.db import models
from django.utils import timezone

class APIKey(models.Model):
    marketplace = models.CharField(max_length=50)
    api_key = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'api_keys'  # Укажите существующее имя таблицы


class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True)  # Уникальный идентификатор заказа
    posting_number = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=60, default='pending')
    cancel_reason_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Значение по умолчанию для даты создания
    in_process_at = models.DateTimeField(null=True, blank=True)
    shipment_date = models.DateTimeField(null=True, blank=True)
    sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    offer_id = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mandatory_mark = models.TextField(null=True, blank=True)
    barcodes = models.TextField(null=True, blank=True)
    analytics_data = models.TextField(null=True, blank=True)
    financial_data = models.TextField(null=True, blank=True)
    is_fraud = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=255, null=True, blank=True)  # Добавлен customer_id
    order_date = models.DateTimeField(null=True, blank=True)  # Добавлена дата заказа

    class Meta:
        db_table = 'orders'
