from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from cy19346_project import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('', views.index, name='index'),
    path('search/', views.search_orders, name='search_orders'),
    path('api_keys/', views.api_keys, name='api_keys'),
    path('api_keys/edit/<int:pk>/', views.edit_api_key, name='edit_api_key'),
    path('api_keys/delete/<int:pk>/', views.delete_api_key, name='delete_api_key'),
    path('order_statistics/', views.order_statistics, name='order_statistics'),
    path('import_orders/', views.import_orders, name='import_orders'),
    path('reset_import/', views.reset_import, name='reset_import'),
]
