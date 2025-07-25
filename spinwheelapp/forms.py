from django import forms
from .models import SpinEntry
from .models import ShopProfile,ShopSettings,GameType  # your actual shop model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

# class ShopSignupForm(UserCreationForm):
#     shop_name = forms.CharField(max_length=100, required=True)
    
#     class Meta:
#         model = User
#         fields = ('username', 'shop_name', 'password1', 'password2')

class ShopSignupForm(UserCreationForm):
    shop_name = forms.CharField(max_length=100, required=True)
    whatsapp_number = forms.CharField(
        max_length=10,
        required=True,
        
        validators=[
            RegexValidator(
                regex=r'^[0-9]+$',
                message="Enter a valid phone number"
            )
        ],
        help_text="WhatsApp number ",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[0-9]{10}'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'shop_name', 'whatsapp_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            shop_name = self.cleaned_data['shop_name']
            whatsapp_number = self.cleaned_data['whatsapp_number']
            shop_code = ShopProfile.generate_unique_shop_code(shop_name)
            ShopProfile.objects.create(
                user=user,
                shop_name=shop_name,
                shop_code=shop_code,
                whatsapp_number=whatsapp_number
            )
        return user
    
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
                        "This bill number has already been used."
                    )
        return bill_number
    
    
    

# class ShopProfileForm(forms.ModelForm):
#     class Meta:
#         model = ShopProfile
#         fields = ['shop_name', 'shop_code']

class ShopProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        max_length=10,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{10}$',
                message="Enter a valid 10-digit WhatsApp number without country code"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit WhatsApp number'
        }),
        help_text="10-digit number"
    )
    
    class Meta:
        model = ShopProfile
        fields = ['shop_name', 'whatsapp_number', 'shop_code']  # Include whatsapp_number
        widgets = {
            'shop_code': forms.TextInput(attrs={'readonly': 'readonly'})  # Keep shop_code read-only
        }


# class ShopSettingsForm(forms.ModelForm):
#     class Meta:
#         model = ShopSettings
#         fields = ['game_type', 'require_bill_number', 'require_social_verification', 
#                  'require_screenshot', 'instagram_url', 'google_review_url']
#         widgets = {
#             'game_type': forms.RadioSelect(choices=GameType.choices)
#         }

class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ['game_type', 'require_bill_number', 'require_social_verification',
                 'require_screenshot', 'instagram_url', 'google_review_url',
                 'allow_multiple_entries_per_phone']
        widgets = {
            'game_type': forms.RadioSelect(),
        }

    def clean(self):
        cleaned_data = super().clean()
        require_social = cleaned_data.get('require_social_verification')
        instagram_url = cleaned_data.get('instagram_url')
        google_review_url = cleaned_data.get('google_review_url')
        require_bill = cleaned_data.get('require_bill_number')

        # Social verification validation
        if require_social:
            if not instagram_url:
                self.add_error('instagram_url', "Instagram URL is required when social verification is enabled")
            if not google_review_url:
                self.add_error('google_review_url', "Google review URL is required when social verification is enabled")

        # Handle allow_multiple_entries_per_phone logic
        if require_bill:
            cleaned_data['allow_multiple_entries_per_phone'] = True

        return cleaned_data