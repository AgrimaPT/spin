from django import forms
from .models import SpinEntry
from .models import ShopProfile,ShopSettings,GameType  # your actual shop model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.validators import RegexValidator

class ShopSignupForm(UserCreationForm):
    shop_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'shop_name', 'password1', 'password2')


# class SpinEntryForm(forms.Form):
#     name = forms.CharField(
#         widget=forms.TextInput(attrs={'class': 'form-control'})
#     )
#     phone = forms.CharField(
#         validators=[
#             RegexValidator(
#                 regex=r'^[6-9]\d{9}$',
#                 message="Please enter a valid 10-digit mobile number"
#             )
#         ],
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'pattern': '[6-9][0-9]{9}'
#         })
#     )
#     shop_code = forms.CharField(widget=forms.HiddenInput())
#     bill_number = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Bill Number (Optional)'
#         })
#     )

#     def __init__(self, *args, **kwargs):
#         require_bill = kwargs.pop('require_bill', False)
#         super(SpinEntryForm, self).__init__(*args, **kwargs)
        
#         if require_bill:
#             self.fields['bill_number'].required = True
#             self.fields['bill_number'].widget.attrs['placeholder'] = 'Bill Number (Required)'


class SpinEntryForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit mobile number"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[6-9][0-9]{9}'
        })
    )
    shop_code = forms.CharField(widget=forms.HiddenInput())
    bill_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bill Number (Optional)'
        })
    )

    def __init__(self, *args, **kwargs):
        self.require_bill = kwargs.pop('require_bill', False)
        self.shop = kwargs.pop('shop', None)
        super(SpinEntryForm, self).__init__(*args, **kwargs)
        
        if self.require_bill:
            self.fields['bill_number'].required = True
            self.fields['bill_number'].widget.attrs['placeholder'] = 'Bill Number (Required)'
            self.fields['bill_number'].help_text = "Each bill number can only be used once"

    def clean_bill_number(self):
        bill_number = self.cleaned_data.get('bill_number')
        shop_code = self.cleaned_data.get('shop_code')
        
        if self.require_bill and bill_number:
            if not self.shop and shop_code:
                self.shop = ShopProfile.objects.filter(shop_code=shop_code).first()
            
            if self.shop:
                if SpinEntry.objects.filter(shop=self.shop, bill_number=bill_number).exists():
                    raise forms.ValidationError(
                        "This bill number has already been used for a spin in this shop. "
                        "Please use a different bill number."
                    )
        return bill_number
    

class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = ShopProfile
        fields = ['shop_name', 'shop_code']

# class SpinEntryForm(forms.ModelForm):
#     class Meta:
#         model = SpinEntry
#         fields = ['name', 'phone', 'bill_number']
        
#     def __init__(self, *args, **kwargs):
#         require_bill = kwargs.pop('require_bill', False)
#         super(SpinEntryForm, self).__init__(*args, **kwargs)
        
#         if not require_bill:
#             self.fields.pop('bill_number', None)
#         else:
#             self.fields['bill_number'].required = True


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ['game_type', 'require_bill_number', 'require_social_verification', 
                 'require_screenshot', 'instagram_url', 'google_review_url']
        widgets = {
            'game_type': forms.RadioSelect(choices=GameType.choices)
        }