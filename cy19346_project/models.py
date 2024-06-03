from django.db import models

class APIKey(models.Model):
    marketplace = models.CharField(max_length=50)
    api_key = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'api_keys'  # Укажите существующее имя таблицы


class Order(models.Model):
    order_id = models.BigIntegerField()
    order_number = models.CharField(max_length=255, null=True)
    posting_number = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255)
    cancel_reason_id = models.IntegerField(null=True)
    created_at = models.DateTimeField()
    in_process_at = models.DateTimeField()
    shipment_date = models.DateTimeField()
    sku = models.BigIntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    offer_id = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mandatory_mark = models.CharField(max_length=255, null=True)
    barcodes = models.TextField(null=True)
    analytics_data = models.TextField(null=True)
    financial_data = models.TextField(null=True)
    is_fraud = models.BooleanField(default=False)

    class Meta:
        db_table = 'orders'
