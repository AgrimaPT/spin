from django.shortcuts import render, redirect
from .forms import SpinEntryForm,ShopProfileForm
from .models import SpinEntry, Offer,ShopProfile,ShopSettings,SocialVerification
import random
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from .utils import validate_offer_percentages
from django.shortcuts import render, redirect
from .forms import ShopSignupForm
from .models import ShopProfile
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib import messages
from math import ceil
from django.shortcuts import render, redirect
import random
from .models import Offer, ShopProfile, SpinEntry
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta





def signup_view(request):
    if request.method == 'POST':
        form = ShopSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create shop profile with new code format
            shop_name = form.cleaned_data['shop_name']
            shop_code = generate_unique_shop_code(shop_name)
            
            ShopProfile.objects.create(
                user=user,
                shop_name=shop_name,
                shop_code=shop_code
            )
            
            login(request, user)
            return redirect('login')  # Replace with your desired redirect
    else:
        form = ShopSignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('offer_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


from django.urls import reverse


def generate_unique_shop_code(shop_name, max_attempts=100):
    prefix = shop_name[:2].upper() if len(shop_name) >= 2 else 'SH'
    for _ in range(max_attempts):
        random_digits = ''.join(random.choices('0123456789', k=4))
        shop_code = f"{prefix}{random_digits}"
        if not ShopProfile.objects.filter(shop_code=shop_code).exists():
            return shop_code
    raise RuntimeError("Could not generate a unique shop code after multiple attempts")

@login_required
def update_shop_profile(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        # Better default naming
        default_name = f"{request.user.username}'s Shop"
        shop_code = generate_unique_shop_code(default_name)  # This will use the new format
        
        shop = ShopProfile.objects.create(
            user=request.user, 
            shop_name=default_name,
            shop_code=shop_code  # Using the new generated code
        )
        messages.info(request, "Please update your shop details")
        return redirect('update_shop_profile')

    if request.method == 'POST':
        form = ShopProfileForm(request.POST, instance=shop)
        if form.is_valid():
            # Regenerate shop code if shop name changed
            if 'shop_name' in form.changed_data:
                new_name = form.cleaned_data['shop_name']
                form.instance.shop_code = generate_unique_shop_code(new_name)
            form.save()
            messages.success(request, "Shop profile updated successfully!")
            return redirect('offer_list')
    else:
        form = ShopProfileForm(instance=shop)

    host = 'https://lucky.newintro.in'
    qr_url = f"{host}{reverse('qr_entry_form', kwargs={'shop_code': shop.shop_code})}"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_url}"

    return render(request, 'update_profile.html', {
        'form': form,
        'qr_url': qr_url,
        'qr_code_url': qr_code_url,
        'shop': shop,
    })




@login_required
def offer_list(request):
    user = request.user
    try:
        shop = user.shopprofile
    except ShopProfile.DoesNotExist:

        default_name = f"{user.username}'s Shop"
        shop_code = generate_unique_shop_code(default_name)
        # Auto-create a shop profile if missing
        shop = ShopProfile.objects.create(
            user=user,
            shop_name=default_name,
            shop_code=shop_code
        )
    offers = Offer.objects.filter(shop=shop)
    return render(request, 'offer_list.html', {'offers': offers})


@login_required
def add_offer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        percentage = float(request.POST.get('percentage', 0))
        shop = request.user.shopprofile

        # Simulate total if this offer were added
        current_total = sum(o.percentage for o in Offer.objects.filter(shop=shop))
        simulated_total = current_total + percentage

        if simulated_total > 100.0:
            messages.error(request, f"Total percentage would exceed 100% (current total: {current_total}%)")
        else:
            Offer.objects.create(shop=shop, name=name, color=color, percentage=percentage)
            return redirect('offer_list')

    return render(request, 'add_offer.html')


@login_required
def delete_offer(request, offer_id):
    Offer.objects.filter(id=offer_id).delete()
    return redirect('offer_list')




# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
#     # Get or create shop settings
#     shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number)
#         if form.is_valid():
#             entry_data = {
#                 'name': form.cleaned_data['name'],
#                 'phone': form.cleaned_data['phone'],
#                 'shop_code': shop_code,
#                 'verified': True
#             }
            
#             # Add bill_number if required and provided
#             if shop_settings.require_bill_number and 'bill_number' in form.cleaned_data:
#                 entry_data['bill_number'] = form.cleaned_data['bill_number']
            
#             request.session['entry_data'] = entry_data
#             request.session.save()
            
#             # Redirect to social verification if enabled, otherwise to spin page
#             # if shop_settings.require_social_verification:
#             #     return redirect('social_verification', shop_code=shop_code)
#             # return redirect('spin_page')
#             if shop_settings.require_social_verification:
#                 return redirect('social_verification', shop_code=shop_code)
#             else:
#                 # Create SpinEntry immediately
#                 spin_entry = SpinEntry.objects.create(
#                     name=entry_data['name'],
#                     phone=entry_data['phone'],
#                     shop=shop,
#                     bill_number=entry_data.get('bill_number', ''),
#                     offer=None  # Will be set after spinning
#                 )
#                 request.session['temp_spin_id'] = spin_entry.id
#                 request.session.modified = True
#                 return redirect('spin_page')

#         else:
#             messages.error(request, "Please correct the errors below")
#     else:
#         form = SpinEntryForm(initial={'shop_code': shop_code}, require_bill=shop_settings.require_bill_number)
    
#     return render(request, 'form.html', {  # Changed template name to match new design
#         'form': form,
#         'shop': shop,
#         'require_bill': shop_settings.require_bill_number,
#         'shop_settings': shop_settings,  # Pass the full settings object
#         'require_social_verification': shop_settings.require_social_verification  # Added for progress steps
#     })



# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number)
#         if form.is_valid():
#             entry_data = {
#                 'name': form.cleaned_data['name'],
#                 'phone': form.cleaned_data['phone'],
#                 'shop_code': shop_code,
#                 'verified': True
#             }
            
#             if shop_settings.require_bill_number and 'bill_number' in form.cleaned_data:
#                 entry_data['bill_number'] = form.cleaned_data['bill_number']
            
#             request.session['entry_data'] = entry_data
#             request.session.save()
            
#             # Create temporary entry (for both game types)
#             spin_entry = SpinEntry.objects.create(
#                 name=entry_data['name'],
#                 phone=entry_data['phone'],
#                 shop=shop,
#                 bill_number=entry_data.get('bill_number', ''),
#                 offer=None
#             )
#             request.session['temp_spin_id'] = spin_entry.id
            
#             # ALWAYS check social verification first if enabled
#             if shop_settings.require_social_verification:
#                 # Clear any existing verification flag
#                 if 'social_verified' in request.session:
#                     del request.session['social_verified']
#                 return redirect('social_verification', shop_code=shop_code)
            
#             # Only proceed directly to game if social verification is NOT required
#             if shop_settings.game_type == GameType.SPIN_WHEEL:
#                 return redirect('spin_page')
#             else:
#                 return redirect('scratch_card')

#         else:
#             messages.error(request, "Please correct the errors below")
#     else:
#         form = SpinEntryForm(initial={'shop_code': shop_code}, require_bill=shop_settings.require_bill_number)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings,
#         'require_bill': shop_settings.require_bill_number,
#         'require_social_verification': shop_settings.require_social_verification,
#         'game_type': shop_settings.get_game_type_display()
#     })


def qr_entry_form(request, shop_code):
    shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
    if request.method == 'POST':
        form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number, shop=shop)
        if form.is_valid():
            # Store the entry data in session
            request.session['entry_data'] = {
                'name': form.cleaned_data['name'],
                'phone': form.cleaned_data['phone'],
                'bill_number': form.cleaned_data.get('bill_number', '')
            }
            # Create the SpinEntry manually since we're using forms.Form
            spin_entry = SpinEntry(
                name=form.cleaned_data['name'],
                phone=form.cleaned_data['phone'],
                shop=shop,
                bill_number=form.cleaned_data['bill_number'] if shop_settings.require_bill_number else None
            )
            
            try:
                spin_entry.save()
                
                # Store the entry ID in session
                request.session['temp_spin_id'] = spin_entry.id
                request.session.save()
                
                # Handle social verification if required
                if shop_settings.require_social_verification:
                    if 'social_verified' in request.session:
                        del request.session['social_verified']
                    return redirect('social_verification', shop_code=shop_code)
                
                # Redirect to appropriate game
                if shop_settings.game_type == 'SW':
                    return redirect('spin_page')
                else:
                    return redirect('scratch_card')
                    
            except IntegrityError as e:
                if 'unique_bill_per_shop' in str(e):
                    messages.error(request, "This bill number has already been used for this shop")
                else:
                    messages.error(request, f"An error occurred while saving your entry: {str(e)}")
                return render(request, 'form.html', {
                    'form': form,
                    'shop': shop,
                    'shop_settings': shop_settings,
                })

        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = SpinEntryForm(initial={'shop_code': shop_code}, 
                           require_bill=shop_settings.require_bill_number,
                           shop=shop)
    
    return render(request, 'form.html', {
        'form': form,
        'shop': shop,
        'shop_settings': shop_settings,
        'require_bill': shop_settings.require_bill_number,
        'require_social_verification': shop_settings.require_social_verification,
        'game_type': shop_settings.get_game_type_display()
    })

# from django import forms
# from .models import SpinEntry

# class SpinEntryForm(forms.ModelForm):
#     class Meta:
#         model = SpinEntry
#         fields = ['name', 'phone', 'bill_number']
    
#     def __init__(self, *args, **kwargs):
#         self.require_bill = kwargs.pop('require_bill', False)
#         self.shop = kwargs.pop('shop', None)
#         super().__init__(*args, **kwargs)
        
#         if not self.require_bill:
#             self.fields['bill_number'].required = False
    
#     def clean_bill_number(self):
#         bill_number = self.cleaned_data.get('bill_number')
#         if self.require_bill and not bill_number:
#             raise forms.ValidationError("Bill number is required")
        
#         if bill_number and self.shop:
#             if SpinEntry.objects.filter(shop=self.shop, bill_number=bill_number).exists():
#                 raise forms.ValidationError("This bill number has already been used")
        
#         return bill_number

def build_segments(offers):
    total = len(offers)
    angle_step = 360 / total
    segments = []

    for i, offer in enumerate(offers):
        segments.append({
            'id': offer.id,
            'name': offer.name,
            'color': offer.color,
            'percentage': float(offer.percentage),  # Ensure this is a float
            'text_angle': i * angle_step + angle_step / 2,
        })

    return segments

@login_required
def spin_page(request):
    # Check if we have a temporary spin entry ID
    temp_spin_id = request.session.get('temp_spin_id')
    if not temp_spin_id:
        messages.error(request, "Session expired or invalid. Please start over.")
        return redirect('home')  # Or redirect to your entry form
    
    try:
        # Get the spin entry
        spin_entry = SpinEntry.objects.get(id=temp_spin_id)
        shop = spin_entry.shop
        shop_settings = ShopSettings.objects.get(shop=shop)
        
        # Check social verification if required
        if shop_settings.require_social_verification and not request.session.get('social_verified'):
            messages.info(request, "Please complete social verification first")
            return redirect('social_verification', shop_code=shop.shop_code)
            
    except SpinEntry.DoesNotExist:
        messages.error(request, "Invalid spin entry")
        return redirect('home')
    except ShopProfile.DoesNotExist:
        messages.error(request, "Invalid shop")
        return redirect('home')
    except ShopSettings.DoesNotExist:
        shop_settings = ShopSettings.objects.create(shop=shop)
    
    # Get offers for the shop
    offers = Offer.objects.filter(shop=shop)
    if not offers.exists():
        messages.error(request, "No offers available for this shop")
        return redirect('home')
    
    # Calculate segments
    total_segments = offers.count()
    angle_per_segment = 360 / total_segments
    
    segments = []
    for i, offer in enumerate(offers):
        text_angle = i * angle_per_segment + angle_per_segment / 2
        skew_y = 90 - angle_per_segment
        content_skew = angle_per_segment - 90
        content_rotate = angle_per_segment / 2
        
        segments.append({
            'id': offer.id,
            'name': offer.name,
            'color': offer.color,
            'percentage': float(offer.percentage),
            'text_angle': text_angle,
            'skew_y': skew_y,
            'content_skew': content_skew,
            'content_rotate': content_rotate,
        })

    entry_data = request.session.get('entry_data', {})

    return render(request, 'spin.html', {
        'segments': segments,
        'angle_per_segment': angle_per_segment,
        'shop': shop,
        'shop_settings': shop_settings,
        'entry_data': entry_data,
        'customer_name': entry_data.get('name', ''),
        'customer_phone': entry_data.get('phone', ''),
        'customer_bill': entry_data.get('bill_number', ''),
    })


@login_required
def edit_offer(request, offer_id):
    try:
        offer = Offer.objects.get(id=offer_id, shop=request.user.shopprofile)
    except Offer.DoesNotExist:
        raise Http404("Offer does not exist")

    shop = request.user.shopprofile
    other_offers = Offer.objects.filter(shop=shop).exclude(id=offer_id)
    current_total = sum(o.percentage for o in other_offers)
    max_allowed = 100.0 - current_total
    
    if request.method == 'POST':
        old_percentage = offer.percentage  # Backup
        new_percentage = float(request.POST.get('percentage', 0))
        
        # Only check if exceeding 100% (not requiring exact 100%)
        if (current_total + new_percentage) > 100.0:
            messages.error(request, 
                f"Total percentage would exceed 100% (current total without this offer: {current_total:.2f}%, "
                f"maximum allowed for this offer: {max_allowed:.2f}%"
            )
            return render(request, 'edit_offer.html', {
                'offer': offer,
                'current_total': current_total,
                'max_allowed': max_allowed
            })
        
        offer.name = request.POST.get('name')
        offer.color = request.POST.get('color')
        offer.percentage = new_percentage
        offer.save()
        return redirect('offer_list')

    return render(request, 'edit_offer.html', {
        'offer': offer,
        'current_total': current_total,
        'max_allowed': max_allowed
    })


@login_required
def settings_view(request):
    try:
        shop = request.user.shopprofile
        settings = ShopSettings.objects.get(shop=shop)
    except (ShopProfile.DoesNotExist, ShopSettings.DoesNotExist):
        messages.error(request, "Shop profile not found")
        return redirect('offer_list')

    if request.method == 'POST':
        try:
            game_type = request.POST.get('game_type', 'SW')  # Default to Spin Wheel
            settings.game_type = game_type
            settings.require_bill_number = 'require_bill_number' in request.POST
            settings.require_social_verification = 'require_social_verification' in request.POST
            settings.require_screenshot = 'require_screenshot' in request.POST
            settings.instagram_url = request.POST.get('instagram_url', '')
            settings.google_review_url = request.POST.get('google_review_url', '')
            
            if settings.require_social_verification:
                if not settings.instagram_url:
                    messages.error(request, "Instagram URL is required when social verification is enabled")
                    return redirect('settings')
                if not settings.google_review_url:
                    messages.error(request, "Google review URL is required when social verification is enabled")
                    return redirect('settings')
            
            settings.save()
            messages.success(request, "Settings updated successfully!")
            return redirect('settings')
            
        except Exception as e:
            messages.error(request, f"Error updating settings: {str(e)}")

    return render(request, 'settings.html', {
        'settings': settings,
        'social_media_required': settings.require_social_verification
    })



from django.db import transaction
import logging

logger = logging.getLogger(__name__)



# @transaction.atomic
# def process_spin(request):
#     if request.method == 'POST':
#         try:
#             # Get data from session
#             temp_spin_id = request.session.get('temp_spin_id')
#             if not temp_spin_id:
#                 messages.error(request, "Session expired. Please start over.")
#                 return redirect('qr_entry_form', shop_code='')
            
#             # Get selected offer
#             selected_offer_id = request.POST.get('selected_offer')
#             if not selected_offer_id:
#                 raise ValueError("No offer selected")
            
#             # Update the existing spin entry with the offer
#             spin_entry = SpinEntry.objects.get(id=temp_spin_id)
#             spin_entry.offer = Offer.objects.get(id=selected_offer_id)
#             spin_entry.save()

#             # Clean up session
#             del request.session['temp_spin_id']
#             if 'social_verified' in request.session:
#                 del request.session['social_verified']
#             request.session.modified = True
            
#             return redirect('spin_success')

#         except Exception as e:
#             logger.error(f"Error in process_spin: {str(e)}", exc_info=True)
#             messages.error(request, f"Error processing spin: {str(e)}")
#             return redirect('spin_page')


@transaction.atomic
def process_spin(request):
    if request.method == 'POST':
        try:
            # Get data from session
            temp_spin_id = request.session.get('temp_spin_id')
            if not temp_spin_id:
                messages.error(request, "Session expired. Please start over.")
                return redirect('qr_entry_form', shop_code='')  # or show a general fallback page
            
            # Get selected offer
            selected_offer_id = request.POST.get('selected_offer')
            if not selected_offer_id:
                raise ValueError("No offer selected")
            
            # Update the existing spin entry with the offer
            spin_entry = SpinEntry.objects.get(id=temp_spin_id)
            spin_entry.offer = Offer.objects.get(id=selected_offer_id)
            spin_entry.save()

            # Clean up session
            del request.session['temp_spin_id']
            if 'social_verified' in request.session:
                del request.session['social_verified']
            if 'entry_data' in request.session:
                del request.session['entry_data']
            request.session.modified = True

            # Redirect to QR form using shop_code
            return redirect('qr_entry_form', shop_code=spin_entry.shop.shop_code)

        except Exception as e:
            logger.error(f"Error in process_spin: {str(e)}", exc_info=True)
            messages.error(request, f"Error processing spin: {str(e)}")
            return redirect('spin_page')

        
@login_required
def spin_entries(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        return redirect('offer_list')
    
    entries = SpinEntry.objects.filter(shop=shop).order_by('-timestamp')
    return render(request, 'spin_entries.html', {'entries': entries,'shop': shop})



# from django.core.files.storage import FileSystemStorage
# from django.utils import timezone
# from datetime import timedelta

# from django.core.files.base import ContentFile
# import base64

# def social_verification(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     settings = get_object_or_404(ShopSettings, shop=shop)
    
#     # Get entry data from session
#     entry_data = request.session.get('entry_data', {})
#     if not entry_data or 'phone' not in entry_data:
#         messages.error(request, "Session expired. Please start over.")
#         return redirect('qr_entry_form', shop_code=shop_code)
    
#     # Check if already verified
#     if request.session.get('social_verified'):
#         return redirect('spin_page')

#     if request.method == 'POST':
#         try:
#             # Create temporary spin entry first
#             spin_entry = SpinEntry.objects.create(
#                 name=entry_data['name'],
#                 phone=entry_data['phone'],
#                 shop=shop,
#                 bill_number=entry_data.get('bill_number', ''),
#                 offer=None  # Will be set after spinning
#             )

#             # Handle file uploads if screenshot verification is required
#             if settings.require_screenshot:
#                 if not all(k in request.FILES for k in ['instagram_screenshot', 'google_screenshot']):
#                     messages.error(request, "Both screenshots are required")
#                     spin_entry.delete()  # Clean up the temporary entry
#                     return redirect('social_verification', shop_code=shop_code)
                
#                 fs = FileSystemStorage()
#                 # Save files to media storage immediately
#                 instagram_file = request.FILES['instagram_screenshot']
#                 google_file = request.FILES['google_screenshot']
                
#                 instagram_filename = fs.save(
#                     f'verifications/instagram_{spin_entry.id}_{instagram_file.name}', 
#                     instagram_file
#                 )
#                 google_filename = fs.save(
#                     f'verifications/google_{spin_entry.id}_{google_file.name}', 
#                     google_file
#                 )
                
#                 # Create verification record
#                 SocialVerification.objects.create(
#                     entry=spin_entry,
#                     instagram_screenshot=instagram_filename,
#                     google_review_screenshot=google_filename
#                 )

#             # Mark as verified in session and store spin entry ID
#             request.session['social_verified'] = True
#             request.session['temp_spin_id'] = spin_entry.id
#             request.session.modified = True
            
#             return redirect('spin_page')
            
#         except Exception as e:
#             messages.error(request, f"Error processing verification: {str(e)}")
#             return redirect('social_verification', shop_code=shop_code)
    
#     return render(request, 'social_verification.html', {
#         'shop': shop,
#         'settings': settings,
#         'require_screenshot': settings.require_screenshot
#     })


from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from .models import ShopProfile, ShopSettings, SpinEntry, SocialVerification, GameType
import random

def social_verification(request, shop_code):
    shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    settings = get_object_or_404(ShopSettings, shop=shop)
    
    # Get entry data from session
    entry_data = request.session.get('entry_data', {})
    if not entry_data or 'phone' not in entry_data:
        messages.error(request, "Session expired. Please start over.")
        return redirect('qr_entry_form', shop_code=shop_code)
    
    # Check if already verified
    if request.session.get('social_verified'):
        # Redirect to appropriate game based on settings
        if settings.game_type == GameType.SPIN_WHEEL:
            return redirect('spin_page')
        else:
            return redirect('scratch_card')

    if request.method == 'POST':
        try:
            # Create temporary entry (works for both game types)
            spin_entry = SpinEntry.objects.create(
                name=entry_data['name'],
                phone=entry_data['phone'],
                shop=shop,
                bill_number=entry_data.get('bill_number', ''),
                offer=None  # Will be set after game interaction
            )

            # Handle file uploads if screenshot verification is required
            if settings.require_screenshot:
                if not all(k in request.FILES for k in ['instagram_screenshot', 'google_screenshot']):
                    messages.error(request, "Both screenshots are required")
                    spin_entry.delete()  # Clean up the temporary entry
                    return redirect('social_verification', shop_code=shop_code)
                
                fs = FileSystemStorage()
                # Save files to media storage immediately
                instagram_file = request.FILES['instagram_screenshot']
                google_file = request.FILES['google_screenshot']
                
                instagram_filename = fs.save(
                    f'verifications/instagram_{spin_entry.id}_{instagram_file.name}', 
                    instagram_file
                )
                google_filename = fs.save(
                    f'verifications/google_{spin_entry.id}_{google_file.name}', 
                    google_file
                )
                
                # Create verification record
                SocialVerification.objects.create(
                    entry=spin_entry,
                    instagram_screenshot=instagram_filename,
                    google_review_screenshot=google_filename
                )

            # Mark as verified in session and store entry ID
            request.session['social_verified'] = True
            request.session['temp_spin_id'] = spin_entry.id
            request.session.modified = True
            
            # Redirect to appropriate game based on settings
            if settings.game_type == GameType.SPIN_WHEEL:
                return redirect('spin_page')
            else:
                return redirect('scratch_card')
            
        except Exception as e:
            messages.error(request, f"Error processing verification: {str(e)}")
            return redirect('social_verification', shop_code=shop_code)
    
    return render(request, 'social_verification.html', {
        'shop': shop,
        'settings': settings,
        'require_screenshot': settings.require_screenshot,
        'game_type': settings.get_game_type_display()  # Add to template context
    })

# views.py
from django.core import serializers
import json
from django.http import JsonResponse

def scratch_card(request):
    shop = request.user.shopprofile
    offers = Offer.objects.filter(shop=shop)
    
    # Get the temporary entry
    temp_spin_id = request.session.get('temp_spin_id')
    if not temp_spin_id:
        return redirect('qr_entry_form', shop_code=shop.shop_code)
    
    # Select a random offer (weighted by percentage)
    total_weight = sum(o.percentage for o in offers)
    rand = random.uniform(0, total_weight)
    current = 0
    selected_offer = None
    
    for offer in offers:
        current += offer.percentage
        if rand <= current:
            selected_offer = offer
            break
    
    if request.method == 'POST':
        # Update the entry with the selected offer
        SpinEntry.objects.filter(id=temp_spin_id).update(offer=selected_offer)
        
        # Clear session data
        if 'temp_spin_id' in request.session:
            del request.session['temp_spin_id']
        if 'entry_data' in request.session:
            del request.session['entry_data']
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return redirect('qr_entry_form', shop_code=shop.shop_code)
    
    return render(request, 'scratch_card.html', {
        'selected_offer': selected_offer,
        'shop': shop
    })