from django import forms
from .models import SpinEntry
from .models import ShopProfile  # your actual shop model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.validators import RegexValidator

class ShopSignupForm(UserCreationForm):
    shop_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'shop_name', 'password1', 'password2')

class SpinEntryForm(forms.Form):
    name = forms.CharField()
    phone = forms.CharField()
    shop_code = forms.CharField(label="Enter Shop Code")

class SpinEntryForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid  mobile number"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
           
            'pattern': '[6-9][0-9]{9}'
        })
    )
    shop_code = forms.CharField(widget=forms.HiddenInput())
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # Additional validation if needed
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be 10 digits")
        return phone

# # Add this to your forms.py
# COUNTRY_CODE_CHOICES = [
#     ('+91', 'India (+91)'),
#     ('+1', 'USA/Canada (+1)'),
#     ('+44', 'UK (+44)'),
#     ('+971', 'UAE (+971)'),
#     # Add more country codes as needed
# ]

# class SpinEntryForm(forms.Form):
#     name = forms.CharField(
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
#     )
#     country_code = forms.ChoiceField(
#         choices=COUNTRY_CODE_CHOICES,
#         initial='+91',
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     phone = forms.CharField(
#         validators=[
#             RegexValidator(
#                 regex=r'^[6-9]\d{9}$',
#                 message="Please enter a valid 10-digit Indian mobile number"
#             )
#         ],
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': '9876543210',
#             'pattern': '[6-9][0-9]{9}',
#             'title': '10-digit Indian mobile number'
#         })
#     )
#     shop_code = forms.CharField(
#         widget=forms.HiddenInput()
#     )
#     # bill_number = forms.CharField(
#     #     required=False,
#     #     widget=forms.TextInput(attrs={
#     #         'class': 'form-control',
#     #         'placeholder': 'Bill Number (Optional)'
#     #     })
#     # )

   
    

class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = ShopProfile
        fields = ['shop_name', 'shop_code']

class SpinEntryForm(forms.ModelForm):
    class Meta:
        model = SpinEntry
        fields = ['name', 'phone', 'bill_number']
        
    def __init__(self, *args, **kwargs):
        require_bill = kwargs.pop('require_bill', False)
        super(SpinEntryForm, self).__init__(*args, **kwargs)
        
        if not require_bill:
            self.fields.pop('bill_number', None)
        else:
            self.fields['bill_number'].required = True