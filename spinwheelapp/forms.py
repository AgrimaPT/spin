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
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Full Name"
    )
    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Please enter a valid 10-digit Indian mobile number"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[6-9][0-9]{9}',
            'placeholder': '98XXXXXXXX'
        }),
        label="Mobile Number"
    )
    shop_code = forms.CharField(widget=forms.HiddenInput())
    bill_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bill Number'
        }),
        label="Bill Number"
    )

    def __init__(self, *args, **kwargs):
        self.require_bill = kwargs.pop('require_bill', False)
        self.shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)
        
        # Dynamically adjust bill number field based on shop requirements
        if self.require_bill:
            self.fields['bill_number'].required = True
            self.fields['bill_number'].widget.attrs['placeholder'] = 'Bill Number (Required)'
            self.fields['bill_number'].widget.attrs['required'] = 'required'
            self.fields['bill_number'].help_text = "Each bill number can only be used once"
        else:
            # Remove the field entirely if not required
            del self.fields['bill_number']

    def clean(self):
        cleaned_data = super().clean()
        shop_code = cleaned_data.get('shop_code')
        
        # Ensure shop exists
        if not self.shop and shop_code:
            self.shop = get_object_or_404(ShopProfile, shop_code=shop_code)
        
        return cleaned_data

    def clean_bill_number(self):
        if not self.require_bill:
            return None
            
        bill_number = self.cleaned_data.get('bill_number')
        
        if self.require_bill and not bill_number:
            raise forms.ValidationError("Bill number is required for this shop")
            
        if bill_number and self.shop:
            if SpinEntry.objects.filter(shop=self.shop, bill_number=bill_number).exists():
                raise forms.ValidationError("This bill number has already been used")
        
        return bill_number
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        if self.shop:
            shop_settings = getattr(self.shop, 'shopsettings', None)
            if shop_settings:
                if not shop_settings.require_bill_number and not shop_settings.allow_multiple_entries_per_phone:
                    today = timezone.now().date()
                    if SpinEntry.objects.filter(
                        shop=self.shop,
                        phone=phone,
                        timestamp__date=today
                    ).exists():
                        raise forms.ValidationError(
                            "You have already participated today. Only one entry per day is allowed."
                        )
        return phone

# class ShopProfileForm(forms.ModelForm):
#     class Meta:
#         model = ShopProfile
#         fields = ['shop_name', 'shop_code']

class ShopProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        max_length=12,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{12}$',
                message="Enter a valid WhatsApp number with country code"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'WhatsApp number'
        }),
        help_text="WhatsApp number"
    )
    
    class Meta:
        model = ShopProfile
        fields = ['shop_name', 'whatsapp_number']  # Include whatsapp_number
        widgets = {
            'shop_code': forms.TextInput(attrs={'readonly': 'readonly'})  # Keep shop_code read-only
        }


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = [
            'game_type',
            'require_bill_number',
            'allow_multiple_entries_per_phone',
            'enable_instagram_verification',
            'instagram_url',
            'require_instagram_screenshot',
            'enable_google_review',
            'google_review_url',
            'require_google_screenshot'
        ]
        widgets = {
            'game_type': forms.RadioSelect(),
            'instagram_url': forms.URLInput(attrs={
                'placeholder': 'https://instagram.com/yourpage',
                'class': 'form-control'
            }),
            'google_review_url': forms.URLInput(attrs={
                'placeholder': 'https://g.page/r/Cxyz/review',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize fields as not required (will be validated in clean())
        self.fields['instagram_url'].required = False
        self.fields['google_review_url'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # Instagram validation
        if cleaned_data.get('enable_instagram_verification'):
            if not cleaned_data.get('instagram_url'):
                self.add_error('instagram_url', "Instagram URL is required when Instagram verification is enabled")
            if not cleaned_data.get('require_instagram_screenshot'):
                cleaned_data['require_instagram_screenshot'] = False
        
        # Google validation
        if cleaned_data.get('enable_google_review'):
            if not cleaned_data.get('google_review_url'):
                self.add_error('google_review_url', "Google review URL is required when Google review verification is enabled")
            if not cleaned_data.get('require_google_screenshot'):
                cleaned_data['require_google_screenshot'] = False
        
        # Handle allow_multiple_entries_per_phone logic
        if cleaned_data.get('require_bill_number'):
            cleaned_data['allow_multiple_entries_per_phone'] = True

        return cleaned_data