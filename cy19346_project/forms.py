# cy19346_project/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import APIKey
class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',)


class APIKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ['marketplace', 'client_id', 'api_key']


