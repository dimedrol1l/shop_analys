from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from .models import Order
import re

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'index.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def search_orders(request):
    query = request.GET.get('posting_number', '').strip()
    results = []

    if query:
        # Validate posting_number format
        if re.match(r'^\d{8,10}-\d{4}-\d{1}$', query):
            results = Order.objects.filter(posting_number=query)
        else:
            results = None

    return render(request, 'orders/search.html', {'results': results, 'query': query})


@login_required
def api_keys(request):
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('api_keys')
    else:
        form = APIKeyForm()
    keys = APIKey.objects.all()
    return render(request, 'api_keys.html', {'form': form, 'keys': keys})

@login_required
def order_statistics(request):
    stats = Order.objects.values('customer_id').annotate(
        total_orders=Count('id'),
        received_orders=Count('id', filter=models.Q(status='received')),
        cancelled_orders=Count('id', filter=models.Q(status='cancelled')),
        returned_orders=Count('id', filter=models.Q(status='returned')),
    )
    return render(request, 'orders/statistics.html', {'stats': stats})
