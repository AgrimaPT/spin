from django import forms
from .models import SpinEntry
from .models import ShopProfile  # your actual shop model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ShopSignupForm(UserCreationForm):
    shop_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'shop_name', 'password1', 'password2')

# class SpinEntryForm(forms.Form):
#     name = forms.CharField()
#     phone = forms.CharField()
#     shop_code = forms.CharField(label="Enter Shop Code")

class SpinEntryForm(forms.Form):
    name = forms.CharField()
    phone = forms.CharField()
    shop_code = forms.CharField(
        widget=forms.HiddenInput()  # Make it hidden since we get it from QR
    )
    # bill_number = forms.CharField(required=False, label="Bill Number (Optional)")

class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = ShopProfile
        fields = ['shop_name', 'shop_code']