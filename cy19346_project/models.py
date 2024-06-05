from django.db import models

class APIKey(models.Model):
    marketplace = models.CharField(max_length=50)
    api_key = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'api_keys'  # Укажите существующее имя таблицы

class Order(models.Model):
    order_id = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100, default='default_product')
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    order_date = models.DateTimeField(blank=True, null=True)
    posting_number = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')
    cancel_reason_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField()
    in_process_at = models.DateTimeField()
    shipment_date = models.DateTimeField()
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

    class Meta:
        db_table = 'orders'