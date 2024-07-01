from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .forms import APIKeyForm, SignUpForm
from .models import APIKey, Order, Profile
import re
import requests
from datetime import datetime, timedelta
import pytz
import json
import logging


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'index.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('api_keys')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('index')


@login_required
def api_keys(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            api_key = form.save(commit=False)
            api_key.user = user
            existing_key = APIKey.objects.filter(user=user, marketplace=api_key.marketplace).first()
            if existing_key:
                existing_key.client_id = api_key.client_id
                existing_key.api_key = api_key.api_key
                existing_key.save()
            else:
                api_key.save()
            messages.success(request, "API Key saved successfully.")
            return redirect('api_keys')
    else:
        form = APIKeyForm()
    return render(request, 'api_keys.html', {'form': form})


@login_required
def edit_api_key(request, pk):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    api_key = get_object_or_404(APIKey, pk=pk, user=user)
    if request.method == 'POST':
        form = APIKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            form.save()
            messages.success(request, "API Key updated successfully.")
            return redirect('api_keys')
    else:
        form = APIKeyForm(instance=api_key)
    return render(request, 'edit_api_key.html', {'form': form})


@login_required
def delete_api_key(request, pk):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    api_key = get_object_or_404(APIKey, pk=pk, user=request.user)
    if request.method == 'POST':
        api_key.delete()
        messages.success(request, "API Key deleted successfully.")
        return redirect('api_keys')
    return render(request, 'confirm_delete.html', {'object': api_key})


@login_required
def search_orders(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    api_key_obj = APIKey.objects.filter(user=user).first()
    if not api_key_obj:
        return redirect('api_keys')

    query = request.GET.get('posting_number', '').strip()
    results = []

    if query:
        if re.match(r'^\d{8,10}-\d{4}-\d{1}$', query):
            results = Order.objects.filter(posting_number=query, user=user)
        else:
            results = None

    return render(request, 'orders/search.html', {'results': results, 'query': query})


# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('order_statistics.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@login_required
def order_statistics(request):
    user = request.user
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)

    if not end_date:
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)

    logger.info(f"Start date: {start_date}, End date: {end_date}")

    orders = Order.objects.filter(
        user=user,
        created_at__range=[start_date, end_date]
    )

    logger.info(f"Orders found: {orders.count()}")

    payment_stats = {}
    for order in orders:
        try:
            logger.info(f"Processing order {order.order_id}")
            logger.info(f"Analytics data raw: {order.analytics_data}")

            analytics_data_str = order.analytics_data.strip()
            if analytics_data_str.startswith("{") and analytics_data_str.endswith("}"):
                analytics_data_str = analytics_data_str.replace("'", '"')
                analytics_data_str = re.sub(r'\bNone\b', 'null', analytics_data_str)
                analytics_data_str = re.sub(r'(\w+):', r'"\1":', analytics_data_str)
                analytics_data_str = re.sub(r':\s*(\w+)', r': "\1"', analytics_data_str)

                analytics_data = json.loads(analytics_data_str)
                logger.info(f"Analytics data parsed: {analytics_data}")

                payment_type = analytics_data.get('payment_type_group_name', 'Unknown').strip()
                if not payment_type or payment_type == ' ':
                    payment_type = 'Unknown'
                logger.info(f"Payment type: {payment_type}")

                if payment_type not in payment_stats:
                    payment_stats[payment_type] = {
                        'total_orders': 0,
                        'delivered_orders': 0,
                        'cancelled_orders': 0,
                        'returned_orders': 0
                    }

                payment_stats[payment_type]['total_orders'] += 1
                if order.status == 'delivered':
                    payment_stats[payment_type]['delivered_orders'] += 1
                elif order.status == 'cancelled':
                    payment_stats[payment_type]['cancelled_orders'] += 1
                elif order.status == 'returned':
                    payment_stats[payment_type]['returned_orders'] += 1
            else:
                raise json.JSONDecodeError("Invalid JSON format", analytics_data_str, 0)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for order {order.order_id}: {e}")
            continue

    logger.info(f"Payment stats: {payment_stats}")

    # Добавление итоговой строки
    total_stats = {
        'total_orders': 0,
        'delivered_orders': 0,
        'cancelled_orders': 0,
        'returned_orders': 0
    }

    for stats in payment_stats.values():
        total_stats['total_orders'] += stats['total_orders']
        total_stats['delivered_orders'] += stats['delivered_orders']
        total_stats['cancelled_orders'] += stats['cancelled_orders']
        total_stats['returned_orders'] += stats['returned_orders']

    payment_stats['Total'] = total_stats

    return render(request, 'orders/statistics.html', {
        'stats': payment_stats,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    })

@login_required
def import_orders(request):
    user = request.user

    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)

    api_key_obj = APIKey.objects.filter(user=user).first()
    if not api_key_obj:
        messages.error(request, "Please add your API key first.")
        return redirect('api_keys')

    if request.method == 'POST':
        success, error_message = fetch_and_save_orders(api_key_obj)
        if success:
            messages.success(request, "Orders imported successfully.")
            user.profile.import_completed = True
            user.profile.save()
        else:
            messages.error(request, error_message)

    return render(request, 'orders/import_orders.html', {'import_completed': user.profile.import_completed})


@login_required
def reset_import(request):
    user = request.user
    if hasattr(user, 'profile'):
        user.profile.import_completed = False
        user.profile.save()
    return redirect('index')


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
            return True, None
        else:
            return False, "No orders found or the API key/client ID might be incorrect."
    elif response.status_code == 403:
        return False, "Invalid API Key or Client ID. Please check your credentials."
    return False, f"Failed to fetch orders. Error code: {response.status_code}"


def update_orders_in_db(orders, user):
    for order in orders:
        for product in order['products']:
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            in_process_at = datetime.fromisoformat(order['in_process_at'].replace('Z', '+00:00'))
            shipment_date = datetime.fromisoformat(order['shipment_date'].replace('Z', '+00:00'))
            order_date = datetime.fromisoformat(order.get('order_date', order['created_at']).replace('Z', '+00:00'))

            # Проверка и преобразование только наивных дат
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(in_process_at):
                in_process_at = timezone.make_aware(in_process_at)
            if timezone.is_naive(shipment_date):
                shipment_date = timezone.make_aware(shipment_date)
            if timezone.is_naive(order_date):
                order_date = timezone.make_aware(order_date)

            Order.objects.update_or_create(
                order_id=order['order_id'],
                defaults={
                    'posting_number': order.get('posting_number', ''),
                    'status': order.get('status', ''),
                    'cancel_reason_id': order.get('cancel_reason_id', ''),
                    'created_at': created_at,
                    'in_process_at': in_process_at,
                    'shipment_date': shipment_date,
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
                    'order_date': order_date,
                    'user': user
                }
            )