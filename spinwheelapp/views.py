from django.shortcuts import render, redirect
from .forms import SpinEntryForm,ShopProfileForm,ShopSettingsForm
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

from django.db import IntegrityError


import logging
logger = logging.getLogger(__name__)

# def signup_view(request):
#     if request.method == 'POST':
#         form = ShopSignupForm(request.POST)
#         if form.is_valid():
#             user = form.save()
            
#             # Create shop profile with new code format
#             shop_name = form.cleaned_data['shop_name']
#             shop_code = generate_unique_shop_code(shop_name)
            
#             ShopProfile.objects.create(
#                 user=user,
#                 shop_name=shop_name,
#                 shop_code=shop_code
#             )
            
#             login(request, user)
#             return redirect('login')  # Replace with your desired redirect
#     else:
#         form = ShopSignupForm()
#     return render(request, 'signup.html', {'form': form})

from django.db import transaction

def signup_view(request):
    if request.method == 'POST':
        form = ShopSignupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user first
                    user = form.save(commit=False)
                    user.save()  # This saves the user to get the ID
                    
                    # Create shop profile
                    shop_name = form.cleaned_data['shop_name']
                    whatsapp_number = form.cleaned_data['whatsapp_number']
                    shop_code = generate_unique_shop_code(shop_name)
                    
                    # Use get_or_create to prevent duplicates
                    ShopProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'shop_name': shop_name,
                            'shop_code': shop_code,
                            'whatsapp_number': whatsapp_number
                        }
                    )
                    
                    login(request, user)
                    return redirect('offer_list')
                    
            except IntegrityError:
                # Handle the case where user creation failed
                form.add_error(None, "An error occurred during registration. Please try again.")
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

# @login_required
# def update_shop_profile(request):
#     try:
#         shop = request.user.shopprofile
#     except ShopProfile.DoesNotExist:
#         # Better default naming
#         default_name = f"{request.user.username}'s Shop"
#         shop_code = generate_unique_shop_code(default_name)  # This will use the new format
        
#         shop = ShopProfile.objects.create(
#             user=request.user, 
#             shop_name=default_name,
#             shop_code=shop_code  # Using the new generated code
#         )
#         messages.info(request, "Please update your shop details")
#         return redirect('update_shop_profile')

#     if request.method == 'POST':
#         form = ShopProfileForm(request.POST, instance=shop)
#         if form.is_valid():
#             # Regenerate shop code if shop name changed
#             if 'shop_name' in form.changed_data:
#                 new_name = form.cleaned_data['shop_name']
#                 form.instance.shop_code = generate_unique_shop_code(new_name)
#             form.save()
#             messages.success(request, "Shop profile updated successfully!")
#             return redirect('offer_list')
#     else:
#         form = ShopProfileForm(instance=shop)

#     host = 'https://lucky.newintro.in'
#     qr_url = f"{host}{reverse('qr_entry_form', kwargs={'shop_code': shop.shop_code})}"
#     qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_url}"

#     return render(request, 'update_profile.html', {
#         'form': form,
#         'qr_url': qr_url,
#         'qr_code_url': qr_code_url,
#         'shop': shop,
#     })


@login_required
def update_shop_profile(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        default_name = f"{request.user.username}'s Shop"
        shop = ShopProfile.objects.create(
            user=request.user, 
            shop_name=default_name,
            shop_code=generate_unique_shop_code(default_name),
            whatsapp_number=''  # Initialize with empty string
        )
        messages.info(request, "Please complete your shop profile")
        return redirect('update_shop_profile')

    if request.method == 'POST':
        form = ShopProfileForm(request.POST, instance=shop)
        if form.is_valid():
            # Regenerate shop code if shop name changed
            if 'shop_name' in form.changed_data:
                form.instance.shop_code = generate_unique_shop_code(form.cleaned_data['shop_name'])
            form.save()
            messages.success(request, "Shop profile updated successfully!")
            return redirect('offer_list')
    else:
        form = ShopProfileForm(instance=shop)

    # Rest of your view remains the same...
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
#     shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number, shop=shop)
#         if form.is_valid():
#             # Store the entry data in session
#             request.session['entry_data'] = {
#                 'name': form.cleaned_data['name'],
#                 'phone': form.cleaned_data['phone'],
#                 'bill_number': form.cleaned_data.get('bill_number', '')
#             }
#             # Create the SpinEntry manually since we're using forms.Form
#             spin_entry = SpinEntry(
#                 name=form.cleaned_data['name'],
#                 phone=form.cleaned_data['phone'],
#                 shop=shop,
#                 bill_number=form.cleaned_data['bill_number'] if shop_settings.require_bill_number else None
#             )
            
#             try:
#                 spin_entry.save()
                
#                 # Store the entry ID in session
#                 request.session['temp_spin_id'] = spin_entry.id
#                 request.session.save()
                
#                 # Handle social verification if required
#                 if shop_settings.require_social_verification:
#                     if 'social_verified' in request.session:
#                         del request.session['social_verified']
#                     return redirect('social_verification', shop_code=shop_code)
                
#                 # Redirect to appropriate game
#                 if shop_settings.game_type == 'SW':
#                     return redirect('spin_page')
#                 else:
#                     return redirect('scratch_card')
                    
#             except IntegrityError as e:
#                 if 'unique_bill_per_shop' in str(e):
#                     messages.error(request, "This bill number has already been used for this shop")
#                 else:
#                     messages.error(request, f"An error occurred while saving your entry: {str(e)}")
#                 return render(request, 'form.html', {
#                     'form': form,
#                     'shop': shop,
#                     'shop_settings': shop_settings,
#                 })

#         else:
#             print("Form errors:", form.errors) 
#             messages.error(request, "Please correct the errors below")
#     else:
#         form = SpinEntryForm(initial={'shop_code': shop_code}, 
#                            require_bill=shop_settings.require_bill_number,
#                            shop=shop)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings,
#         'require_bill': shop_settings.require_bill_number,
#         'require_social_verification': shop_settings.require_social_verification,
#         'game_type': shop_settings.get_game_type_display()
#     })


# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number, shop=shop)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     spin_entry = SpinEntry(
#                         name=form.cleaned_data['name'],
#                         phone=form.cleaned_data['phone'],
#                         shop=shop,
#                         bill_number=form.cleaned_data.get('bill_number', '')
#                     )
#                     spin_entry.save()
                    
#                     # Store in session
#                     request.session['temp_spin_id'] = spin_entry.id
#                     request.session['entry_data'] = {
#                         'name': form.cleaned_data['name'],
#                         'phone': form.cleaned_data['phone'],
#                         'bill_number': form.cleaned_data.get('bill_number', '')
#                     }
#                     request.session['shop_code'] = shop_code
#                     request.session.save()  # Explicit save
                    
                    
#                     # Handle redirection based on settings
#                     if shop_settings.require_social_verification:
                       
#                         return redirect('social_verification', shop_code=shop_code)
                    
                    
#                     if shop_settings.game_type == 'SW':
#                         return redirect('spin_page')
#                     else:
#                         return redirect('scratch_card')
                        
#             except Exception as e:
                
#                 messages.error(request, f"Error processing your entry: {str(e)}")
        
#     else:
#         form = SpinEntryForm(initial={'shop_code': shop_code}, 
#                            require_bill=shop_settings.require_bill_number,
#                            shop=shop)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings
#     })

# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number, shop=shop)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     spin_entry = SpinEntry(
#                         name=form.cleaned_data['name'],
#                         phone=form.cleaned_data['phone'],
#                         shop=shop,
#                         bill_number=form.cleaned_data.get('bill_number', '')
#                     )
#                     spin_entry.save()
                    
#                     # Store in session
#                     request.session['temp_spin_id'] = spin_entry.id
#                     request.session['entry_data'] = {
#                         'name': form.cleaned_data['name'],
#                         'phone': form.cleaned_data['phone'],
#                         'bill_number': form.cleaned_data.get('bill_number', '')
#                     }
#                     request.session['shop_code'] = shop_code
#                     request.session.modified = True  # Explicitly mark as modified
                    
#                     print(f"Form valid - redirecting to game. Shop settings: {shop_settings.game_type}")
                    
#                     # Handle redirection based on settings
#                     if shop_settings.require_social_verification:
#                         return redirect('social_verification', shop_code=shop_code)
                    
#                     if shop_settings.game_type == 'SW':
#                         return redirect('spin_page')
#                     else:
#                         return redirect('scratch_card')
                        
#             except Exception as e:
#                 print(f"Error saving entry: {str(e)}")
#                 messages.error(request, f"Error processing your entry: {str(e)}")
#         else:
#             print(f"Form invalid. Errors: {form.errors}")  # Debug form errors
#             messages.error(request, "Please correct the form errors")
#     else:
#         form = SpinEntryForm(initial={'shop_code': shop_code}, 
#                            require_bill=shop_settings.require_bill_number,
#                            shop=shop)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings
#     })


# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings = ShopSettings.objects.get_or_create(shop=shop)[0]  # Ensures we get the object
    
#     if request.method == 'POST':
#         form = SpinEntryForm(
#             request.POST, 
#             require_bill=shop_settings.require_bill_number,
#             shop=shop
#         )
        
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # Create the spin entry
#                     spin_entry = SpinEntry(
#                         name=form.cleaned_data['name'],
#                         phone=form.cleaned_data['phone'],
#                         shop=shop,
#                         bill_number=form.cleaned_data.get('bill_number')  # Returns None if field was removed
#                     )
#                     spin_entry.save()
                    
#                     # Store in session
#                     request.session.update({
#                         'temp_spin_id': spin_entry.id,
#                         'entry_data': {
#                             'name': form.cleaned_data['name'],
#                             'phone': form.cleaned_data['phone'],
#                             'bill_number': spin_entry.bill_number  # Use the saved value
#                         },
#                         'shop_code': shop_code,
#                         'social_verified': False  # Initialize social verification status
#                     })
                    
#                     # Debug output
#                     # print(f"Created entry ID: {spin_entry.id}")
#                     # print(f"Bill number: {spin_entry.bill_number}")
                    
#                     # Handle redirection
#                     if shop_settings.require_social_verification:
#                         # print("Redirecting to social verification")
#                         return redirect('social_verification', shop_code=shop_code)
                    
#                     # print(f"Redirecting to game type: {shop_settings.game_type}")
#                     return redirect(
#                         'spin_page' if shop_settings.game_type == 'SW' 
#                         else 'scratch_card'
#                     )
                    
#             except IntegrityError as e:
#                 logger.error(f"Integrity error saving entry: {str(e)}")
#                 messages.error(request, "This entry appears to be a duplicate. Please check your details.")
#             except Exception as e:
#                 logger.error(f"Error saving entry: {str(e)}")
#                 messages.error(request, "An unexpected error occurred. Please try again.")
#         else:
#             logger.warning(f"Form invalid: {form.errors.as_json()}")
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{field.title()}: {error}")
#     else:
#         form = SpinEntryForm(
#             initial={'shop_code': shop_code},
#             require_bill=shop_settings.require_bill_number,
#             shop=shop
#         )
    
#     context = {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings,
#         'require_bill': shop_settings.require_bill_number,
#     }
#     return render(request, 'form.html', context)

# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings = ShopSettings.objects.get_or_create(shop=shop)[0]
    
#     if request.method == 'POST':
#         form = SpinEntryForm(
#             request.POST, 
#             require_bill=shop_settings.require_bill_number,
#             shop=shop
#         )
        
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     spin_entry = SpinEntry(
#                         name=form.cleaned_data['name'],
#                         phone=form.cleaned_data['phone'],
#                         shop=shop,
#                         bill_number=form.cleaned_data.get('bill_number')
#                     )
#                     spin_entry.save()
                    
#                     request.session.update({
#                         'temp_spin_id': spin_entry.id,
#                         'entry_data': {
#                             'name': form.cleaned_data['name'],
#                             'phone': form.cleaned_data['phone'],
#                             'bill_number': spin_entry.bill_number
#                         },
#                         'shop_code': shop_code,
#                         'social_verified': False
#                     })
                    
#                     # Check if any social verification is required
#                     if shop_settings.requires_social_verification():
#                         return redirect('social_verification', shop_code=shop_code)
                    
#                     return redirect_to_game(shop_settings.game_type)
                    
#             except IntegrityError as e:
#                 logger.error(f"Integrity error: {str(e)}")
#                 messages.error(request, "This entry appears to be a duplicate. Please check your details.")
#             except Exception as e:
#                 logger.error(f"Error saving entry: {str(e)}")
#                 messages.error(request, "An unexpected error occurred. Please try again.")
#         else:
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{field.title()}: {error}")
#     else:
#         form = SpinEntryForm(
#             initial={'shop_code': shop_code},
#             require_bill=shop_settings.require_bill_number,
#             shop=shop
#         )
    
#     context = {
#         'form': form,
#         'shop': shop,
#         'shop_settings': shop_settings,
#         'require_bill': shop_settings.require_bill_number,
#         'require_social_verification': shop_settings.requires_social_verification()
#     }
#     return render(request, 'form.html', context)

def qr_entry_form(request, shop_code):
    logger.info(f"Entering qr_entry_form for shop: {shop_code}")
    shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    shop_settings = ShopSettings.objects.get_or_create(shop=shop)[0]
    
    if request.method == 'POST':
        logger.info("POST request received")
        form = SpinEntryForm(request.POST, require_bill=shop_settings.require_bill_number, shop=shop)
        
        if form.is_valid():
            logger.info("Form is valid")
            try:
                with transaction.atomic():
                    spin_entry = SpinEntry(
                        name=form.cleaned_data['name'],
                        phone=form.cleaned_data['phone'],
                        shop=shop,
                        bill_number=form.cleaned_data.get('bill_number')
                    )
                    spin_entry.save()
                    logger.info(f"Created SpinEntry with ID: {spin_entry.id}")
                    
                    request.session.update({
                        'temp_spin_id': spin_entry.id,
                        'entry_data': {
                            'name': form.cleaned_data['name'],
                            'phone': form.cleaned_data['phone'],
                            'bill_number': spin_entry.bill_number
                        },
                        'shop_code': shop_code,
                        'social_verified': False
                    })
                    logger.info("Session updated with entry data")
                    
                    # Debug social verification requirements
                    logger.info(f"Social verification required: {shop_settings.requires_social_verification()}")
                    logger.info(f"Game type: {shop_settings.game_type}")
                    
                    if shop_settings.requires_social_verification():
                        logger.info("Redirecting to social verification")
                        return redirect('social_verification', shop_code=shop_code)
                    
                    logger.info("No social verification needed, redirecting to spin_page")
                    return redirect_to_game(shop_settings.game_type)
                    
            except Exception as e:
                logger.error(f"Error in form processing: {str(e)}", exc_info=True)
                messages.error(request, "An error occurred. Please try again.")
        else:
            logger.warning(f"Form invalid: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        logger.info("GET request received")
        form = SpinEntryForm(
            initial={'shop_code': shop_code},
            require_bill=shop_settings.require_bill_number,
            shop=shop
        )
    
    context = {
        'form': form,
        'shop': shop,
        'shop_settings': shop_settings,
        'require_bill': shop_settings.require_bill_number,
        'require_social_verification': shop_settings.requires_social_verification()
    }
    return render(request, 'form.html', context)

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

import json
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SpinEntry, Offer, ShopProfile, ShopSettings
from django.core.serializers.json import DjangoJSONEncoder



# def spin_page(request):
    
#     # Check if we have a temporary spin entry ID
#     temp_spin_id = request.session.get('temp_spin_id')
#     if not temp_spin_id:
        
#         shop_code = request.session.get('shop_code', '')
#         messages.error(request, "Session expired or invalid. Please start over.")
#         return redirect('qr_entry_form', shop_code=shop_code)
    
#     try:
        
#         # Get the spin entry with related objects
#         spin_entry = SpinEntry.objects.select_related('shop').get(id=temp_spin_id)
#         shop = spin_entry.shop
        
#         # Get or create shop settings
#         shop_settings, created = ShopSettings.objects.get_or_create(shop=shop)
        
#         # Check social verification if required
#         if shop_settings.require_social_verification:
#             if not request.session.get('social_verified'):
                
#                 messages.info(request, "Please complete social verification first")
#                 return redirect('social_verification', shop_code=shop.shop_code)
            
#         # Get offers for the shop
#         offers = Offer.objects.filter(shop=shop).order_by('id')
        
        
#         if not offers.exists():
            
#             messages.error(request, "No offers available for this shop")
#             return redirect('qr_entry_form', shop_code=shop.shop_code)
        
#         # Calculate segments and prepare data
#         total_segments = offers.count()
#         angle_per_segment = 360 / total_segments
        
#         segments = []
#         for i, offer in enumerate(offers):
#             segments.append({
#                 'id': str(offer.id),  # Ensure string for JSON
#                 'name': offer.name,
#                 'color': offer.color,
#                 'percentage': float(offer.percentage),
#                 'text_angle': float(i * angle_per_segment + (angle_per_segment / 2)),
#                 'start_angle': float(i * angle_per_segment),
#                 'end_angle': float((i + 1) * angle_per_segment),
#             })

#         # Get entry data from session
#         entry_data = request.session.get('entry_data', {})
        
#         # Prepare context
#         context = {
#             'segments': segments,
#             'segments_json': json.dumps(segments, cls=DjangoJSONEncoder),
#             'angle_per_segment': angle_per_segment,
#             'shop': shop,
#             'shop_settings': shop_settings,
#             'entry_data': entry_data,
#             'customer_name': entry_data.get('name', ''),
#             'customer_phone': entry_data.get('phone', ''),
#             'customer_bill': entry_data.get('bill_number', ''),
#             'short_id': spin_entry.short_id,
#         }

        
#         return render(request, 'spin.html', context)
            
#     except SpinEntry.DoesNotExist:
        
#         messages.error(request, "Invalid spin entry. Please try again.")
#         return redirect('qr_entry_form', shop_code=shop.shop_code)
#     except Exception as e:
        
#         messages.error(request, f"An error occurred: {str(e)}")
#         return redirect('qr_entry_form', shop_code=shop.shop_code)


def spin_page(request):
    logger.info("Entering spin_page view")
    temp_spin_id = request.session.get('temp_spin_id')
    if not temp_spin_id:
        logger.warning("No temp_spin_id in session")
        shop_code = request.session.get('shop_code', '')
        messages.error(request, "Session expired or invalid. Please start over.")
        return redirect('qr_entry_form', shop_code=shop_code)
    
    try:
        spin_entry = SpinEntry.objects.select_related('shop').get(id=temp_spin_id)
        shop = spin_entry.shop
        logger.info(f"Processing spin for shop: {shop.shop_code}")
        
        shop_settings = ShopSettings.objects.get(shop=shop)
        
        if shop_settings.requires_social_verification():
            logger.info("Checking social verification status")
            if not request.session.get('social_verified'):
                logger.warning("Social verification not completed")
                messages.info(request, "Please complete social verification first")
                return redirect('social_verification', shop_code=shop.shop_code)
        
        offers = Offer.objects.filter(shop=shop).order_by('id')
        if not offers.exists():
            logger.error("No offers available for this shop")
            messages.error(request, "No offers available for this shop")
            return redirect('qr_entry_form', shop_code=shop.shop_code)
        
        # Calculate segments and prepare data
        total_segments = offers.count()
        angle_per_segment = 360 / total_segments
        
        segments = []
        for i, offer in enumerate(offers):
            segments.append({
                'id': str(offer.id),
                'name': offer.name,
                'color': offer.color,
                'percentage': float(offer.percentage),
                'text_angle': float(i * angle_per_segment + (angle_per_segment / 2)),
                'start_angle': float(i * angle_per_segment),
                'end_angle': float((i + 1) * angle_per_segment),
            })

        # Get entry data from session
        entry_data = request.session.get('entry_data', {})
        
        # Prepare context
        context = {
            'segments': segments,
            'segments_json': json.dumps(segments, cls=DjangoJSONEncoder),
            'angle_per_segment': angle_per_segment,
            'shop': shop,
            'shop_settings': shop_settings,
            'entry_data': entry_data,
            'customer_name': entry_data.get('name', ''),
            'customer_phone': entry_data.get('phone', ''),
            'customer_bill': entry_data.get('bill_number', ''),
            'short_id': spin_entry.short_id,
        }

        logger.info("Rendering spin page with context")
        return render(request, 'spin.html', context)
            
    except SpinEntry.DoesNotExist:
        logger.error("SpinEntry not found")
        messages.error(request, "Invalid spin entry. Please try again.")
        return redirect('qr_entry_form', shop_code=shop.shop_code)
    except Exception as e:
        logger.error(f"Error in spin_page: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('qr_entry_form', shop_code=shop.shop_code)
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


# @login_required
# def settings_view(request):
#     try:
#         shop = request.user.shopprofile
#         settings = ShopSettings.objects.get(shop=shop)
#     except (ShopProfile.DoesNotExist, ShopSettings.DoesNotExist):
#         messages.error(request, "Shop profile not found")
#         return redirect('offer_list')

#     if request.method == 'POST':
#         try:
#             game_type = request.POST.get('game_type', 'SW')  # Default to Spin Wheel
#             settings.game_type = game_type
#             settings.require_bill_number = 'require_bill_number' in request.POST
#             settings.require_social_verification = 'require_social_verification' in request.POST
#             settings.require_screenshot = 'require_screenshot' in request.POST
#             settings.instagram_url = request.POST.get('instagram_url', '')
#             settings.google_review_url = request.POST.get('google_review_url', '')
            
#             if settings.require_social_verification:
#                 if not settings.instagram_url:
#                     messages.error(request, "Instagram URL is required when social verification is enabled")
#                     return redirect('settings')
#                 if not settings.google_review_url:
#                     messages.error(request, "Google review URL is required when social verification is enabled")
#                     return redirect('settings')
                
#             if not settings.require_bill_number:
#                 settings.allow_multiple_entries_per_phone = 'allow_multiple_entries_per_phone' in request.POST
#             else:
#                 # Reset to default (True) if bill number is required
#                 settings.allow_multiple_entries_per_phone = True
#             settings.save()
#             messages.success(request, "Settings updated successfully!")
#             return redirect('offer_list')
            
#         except Exception as e:
#             messages.error(request, f"Error updating settings: {str(e)}")

#     return render(request, 'settings.html', {
#         'settings': settings,
#         'social_media_required': settings.require_social_verification
#     })

# @login_required
# def settings_view(request):
#     try:
#         # Get or create shop profile
#         shop, shop_created = ShopProfile.objects.get_or_create(
#             user=request.user,
#             defaults={
#                 'shop_name': f"{request.user.username}'s Shop",
#                 'shop_code': ShopProfile.generate_unique_shop_code(f"{request.user.username}'s Shop"),
#                 'whatsapp_number': '0000000000'  # Default number
#             }
#         )
        
#         # Get or create settings
#         settings, settings_created = ShopSettings.objects.get_or_create(
#             shop=shop,
#             defaults={
#                 'game_type': 'SW',
#                 'require_bill_number': False,
#                 'require_social_verification': False,
#                 'allow_multiple_entries_per_phone': True
#             }
#         )
        
#     except Exception as e:
#         messages.error(request, f"Error accessing settings: {str(e)}")
#         return redirect('offer_list')

#     if request.method == 'POST':
#         form = ShopSettingsForm(request.POST, instance=settings)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Settings updated successfully!")
#             return redirect('offer_list')  # Stay on settings page after save
#         else:
#             messages.error(request, "Please correct the errors below")
#     else:
#         form = ShopSettingsForm(instance=settings)

#     return render(request, 'settings.html', {
#         'form': form,
#         'settings': settings
#     })

@login_required
def settings_view(request):
    try:
        shop = request.user.shopprofile
        settings = ShopSettings.objects.get_or_create(shop=shop)[0]
    except Exception as e:
        messages.error(request, f"Error accessing settings: {str(e)}")
        return redirect('offer_list')

    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully!")
            return redirect('offer_list')
        else:
            messages.error(request, "Please correct the errors below")
    else:
        form = ShopSettingsForm(instance=settings)

    return render(request, 'settings.html', {
        'form': form,
        'settings': settings
    })

from django.db import transaction
import logging

logger = logging.getLogger(__name__)

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

        
# @login_required
# def spin_entries(request):
#     try:
#         shop = request.user.shopprofile
#     except ShopProfile.DoesNotExist:
#         return redirect('offer_list')
    
#     entries = SpinEntry.objects.filter(shop=shop).order_by('-timestamp')
#     return render(request, 'spin_entries.html', {
#         'entries': entries,
#         'shop': shop
#     })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import ShopProfile, SpinEntry

@login_required
def spin_entries(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        return redirect('offer_list')

    filter_by = request.GET.get('filter', 'all')
    
    if filter_by == 'redeemed':
        entries = SpinEntry.objects.filter(shop=shop, is_redeemed=True)
    elif filter_by == 'not_redeemed':
        entries = SpinEntry.objects.filter(shop=shop, is_redeemed=False)
    else:
        entries = SpinEntry.objects.filter(shop=shop)

    entries = entries.order_by('-timestamp')

    return render(request, 'spin_entries.html', {
        'entries': entries,
        'shop': shop,
        'active_filter': filter_by
    })


from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from .models import ShopProfile, ShopSettings, SpinEntry, SocialVerification, GameType
import random


@require_POST
@login_required
def redeem_entry(request, entry_id):
    entry = get_object_or_404(SpinEntry, id=entry_id, shop=request.user.shopprofile)
    entry.is_redeemed = True
    entry.save()
    return redirect(request.META.get('HTTP_REFERER', 'spin_entries'))


# def social_verification(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     settings = get_object_or_404(ShopSettings, shop=shop)
    
#     # Check if already verified
#     if request.session.get('social_verified'):
#         if settings.game_type == 'SW':
#             return redirect('spin_page')
#         else:
#             return redirect('scratch_card')

#     # Get entry data from session
#     entry_data = request.session.get('entry_data', {})
#     if not entry_data or 'phone' not in entry_data:
#         messages.error(request, "Session expired. Please start over.")
#         return redirect('qr_entry_form', shop_code=shop_code)

#     if request.method == 'POST':
#         try:
#             # Check if we have a temporary spin entry already
#             temp_spin_id = request.session.get('temp_spin_id')
#             if temp_spin_id:
#                 try:
#                     spin_entry = SpinEntry.objects.get(id=temp_spin_id)
#                 except SpinEntry.DoesNotExist:
#                     spin_entry = None
#             else:
#                 spin_entry = None

#             # Create new entry if needed
#             if not spin_entry:
#                 spin_entry = SpinEntry.objects.create(
#                     name=entry_data['name'],
#                     phone=entry_data['phone'],
#                     shop=shop,
#                     bill_number=entry_data.get('bill_number', ''),
#                     offer=None
#                 )
#                 request.session['temp_spin_id'] = spin_entry.id

#             # Handle file uploads if screenshot verification is required
#             if settings.require_screenshot:
#                 if not all(k in request.FILES for k in ['instagram_screenshot', 'google_screenshot']):
#                     messages.error(request, "Both screenshots are required")
#                     return redirect('social_verification', shop_code=shop_code)
                
#                 fs = FileSystemStorage()
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

#             # Mark as verified in session
#             request.session['social_verified'] = True
#             request.session.modified = True
            
#             # Redirect to appropriate game
#             if settings.game_type == 'SW':
#                 return redirect('spin_page')
#             else:
#                 return redirect('scratch_card')
            
#         except Exception as e:
#             messages.error(request, f"Error processing verification: {str(e)}")
#             return redirect('social_verification', shop_code=shop_code)
    
#     return render(request, 'social_verification.html', {
#         'shop': shop,
#         'settings': settings,
#         'require_screenshot': settings.require_screenshot,
#         'game_type': settings.get_game_type_display()
#     })

# def social_verification(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     settings = get_object_or_404(ShopSettings, shop=shop)
    
#     # Check if already verified
#     if request.session.get('social_verified'):
#         return redirect_to_game(settings.game_type)

#     # Get entry data from session
#     entry_data = request.session.get('entry_data', {})
#     if not entry_data or 'phone' not in entry_data:
#         messages.error(request, "Session expired. Please start over.")
#         return redirect('qr_entry_form', shop_code=shop_code)

#     if request.method == 'POST':
#         try:
#             # Get or create spin entry
#             spin_entry = get_or_create_spin_entry(request, entry_data, shop)
            
#             # Initialize verification
#             verification = SocialVerification(entry=spin_entry)
            
#             # Handle Instagram verification if enabled
#             if settings.enable_instagram_verification:
#                 if settings.require_instagram_screenshot:
#                     if 'instagram_screenshot' not in request.FILES:
#                         messages.error(request, "Instagram screenshot is required")
#                         return redirect('social_verification', shop_code=shop_code)
#                     verification.instagram_screenshot = request.FILES['instagram_screenshot']
            
#             # Handle Google verification if enabled
#             if settings.enable_google_review:
#                 if settings.require_google_screenshot:
#                     if 'google_screenshot' not in request.FILES:
#                         messages.error(request, "Google review screenshot is required")
#                         return redirect('social_verification', shop_code=shop_code)
#                     verification.google_review_screenshot = request.FILES['google_screenshot']
            
#             verification.save()
            
#             # Mark as verified in session
#             request.session['social_verified'] = True
#             request.session.modified = True
            
#             return redirect_to_game(settings.game_type)
            
#         except Exception as e:
#             logger.error(f"Error in social_verification: {str(e)}")
#             messages.error(request, f"Error processing verification: {str(e)}")
#             return redirect('social_verification', shop_code=shop_code)
    
#     # Prepare context based on what verifications are required
#     context = {
#         'shop': shop,
#         'settings': settings,
#         'require_instagram': settings.enable_instagram_verification,
#         'require_instagram_screenshot': settings.require_instagram_screenshot,
#         'instagram_url': settings.instagram_url,
#         'require_google': settings.enable_google_review,
#         'require_google_screenshot': settings.require_google_screenshot,
#         'google_review_url': settings.google_review_url,
#         'game_type': settings.get_game_type_display()
#     }
#     return render(request, 'social_verification.html', context)


def social_verification(request, shop_code):
    logger.info(f"Entering social_verification for shop: {shop_code}")
    shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    settings = get_object_or_404(ShopSettings, shop=shop)
    
    if request.session.get('social_verified'):
        logger.info("Already verified, redirecting to spin_page")
        return redirect('spin_page')

    entry_data = request.session.get('entry_data', {})
    if not entry_data or 'phone' not in entry_data:
        logger.warning("Session data missing, redirecting to form")
        messages.error(request, "Session expired. Please start over.")
        return redirect('qr_entry_form', shop_code=shop_code)

    if request.method == 'POST':
        logger.info("POST request received for verification")
        try:
            spin_entry = get_or_create_spin_entry(request, entry_data, shop)
            logger.info(f"Using SpinEntry ID: {spin_entry.id}")
            
            verification = SocialVerification(entry=spin_entry)
            
            if settings.enable_instagram_verification and settings.require_instagram_screenshot:
                if 'instagram_screenshot' not in request.FILES:
                    logger.warning("Missing Instagram screenshot")
                    messages.error(request, "Instagram screenshot is required")
                    return redirect('social_verification', shop_code=shop_code)
                verification.instagram_screenshot = request.FILES['instagram_screenshot']
            
            if settings.enable_google_review and settings.require_google_screenshot:
                if 'google_screenshot' not in request.FILES:
                    logger.warning("Missing Google screenshot")
                    messages.error(request, "Google review screenshot is required")
                    return redirect('social_verification', shop_code=shop_code)
                verification.google_review_screenshot = request.FILES['google_screenshot']
            
            verification.save()
            logger.info("Verification saved")
            
            request.session['social_verified'] = True
            request.session.modified = True
            logger.info("Session marked as verified")
            
            logger.info(f"Redirecting to spin_page (game_type: {settings.game_type})")
            return redirect_to_game(settings.game_type)
            
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            messages.error(request, f"Error processing verification: {str(e)}")
            return redirect('social_verification', shop_code=shop_code)
    
    context = {
        'shop': shop,
        'settings': settings,
        'require_instagram': settings.enable_instagram_verification,
        'require_instagram_screenshot': settings.require_instagram_screenshot,
        'instagram_url': settings.instagram_url,
        'require_google': settings.enable_google_review,
        'require_google_screenshot': settings.require_google_screenshot,
        'google_review_url': settings.google_review_url,
        'game_type': settings.get_game_type_display()
    }
    return render(request, 'social_verification.html', context)


def redirect_to_game(game_type):
    """Helper function to redirect to appropriate game"""
    return redirect('spin_page' if game_type == 'SW' else 'scratch_card')

def get_or_create_spin_entry(request, entry_data, shop):
    """Helper function to get or create spin entry"""
    temp_spin_id = request.session.get('temp_spin_id')
    if temp_spin_id:
        try:
            return SpinEntry.objects.get(id=temp_spin_id)
        except SpinEntry.DoesNotExist:
            pass
    
    # Create new entry if needed
    spin_entry = SpinEntry.objects.create(
        name=entry_data['name'],
        phone=entry_data['phone'],
        shop=shop,
        bill_number=entry_data.get('bill_number', ''),
        offer=None
    )
    request.session['temp_spin_id'] = spin_entry.id
    return spin_entry

# views.py
from django.core import serializers
import json
from django.http import JsonResponse


# def scratch_card(request, shop_code=None):
#     if shop_code:
#         shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     else:
#         if not request.user.is_authenticated:
#             return redirect('login')
#         shop = request.user.shopprofile
    
#     # Get the temporary entry
#     temp_spin_id = request.session.get('temp_spin_id')
#     if not temp_spin_id:
#         return redirect('qr_entry_form', shop_code=shop.shop_code)
    
#     # Select a random offer (weighted by percentage)
#     offers = Offer.objects.filter(shop=shop)
#     total_weight = sum(o.percentage for o in offers)
#     rand = random.uniform(0, total_weight)
#     current = 0
#     selected_offer = None
    
#     for offer in offers:
#         current += offer.percentage
#         if rand <= current:
#             selected_offer = offer
#             break
    
#     if request.method == 'POST':
#         # Update the entry with the selected offer
#         SpinEntry.objects.filter(id=temp_spin_id).update(offer=selected_offer)
        
#         # Clear session data
#         if 'temp_spin_id' in request.session:
#             del request.session['temp_spin_id']
#         if 'entry_data' in request.session:
#             del request.session['entry_data']
        
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({'status': 'success'})
#         return redirect('qr_entry_form', shop_code=shop.shop_code)
    
#     # Pass customer data from session
#     entry_data = request.session.get('entry_data', {})
#     return render(request, 'scratch_card.html', {
#         'selected_offer': selected_offer,
#         'shop': shop,
#         'customer_name': entry_data.get('name', ''),
#         'customer_phone': entry_data.get('phone', ''),
#         'customer_bill': entry_data.get('bill_number', '')
#     })


# def scratch_card(request, shop_code=None):
#     if shop_code:
#         shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     else:
#         if not request.user.is_authenticated:
#             return redirect('login')
#         shop = request.user.shopprofile
    
#     # Get the temporary entry
#     temp_spin_id = request.session.get('temp_spin_id')
#     if not temp_spin_id:
#         return redirect('qr_entry_form', shop_code=shop.shop_code)
    
#     # Check if we've already selected an offer for this session
#     if 'selected_offer_id' not in request.session:
#         # Select a random offer (weighted by percentage) and store in session
#         offers = Offer.objects.filter(shop=shop)
#         total_weight = sum(o.percentage for o in offers)
#         rand = random.uniform(0, total_weight)
#         current = 0
#         selected_offer = None
        
#         for offer in offers:
#             current += offer.percentage
#             if rand <= current:
#                 selected_offer = offer
#                 break
        
#         # Store the selected offer ID in session to ensure consistency
#         request.session['selected_offer_id'] = selected_offer.id
#         request.session.modified = True
#     else:
#         # Use the previously selected offer
#         selected_offer = Offer.objects.get(id=request.session['selected_offer_id'])
    
#     if request.method == 'POST':
#         # Update the entry with the selected offer from session
#         SpinEntry.objects.filter(id=temp_spin_id).update(offer_id=request.session['selected_offer_id'])
        
#         # Clear session data
#         if 'temp_spin_id' in request.session:
#             del request.session['temp_spin_id']
#         if 'entry_data' in request.session:
#             del request.session['entry_data']
#         if 'selected_offer_id' in request.session:
#             del request.session['selected_offer_id']
        
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({'status': 'success'})
#         return redirect('qr_entry_form', shop_code=shop.shop_code)
    
#     # Pass customer data from session
#     entry_data = request.session.get('entry_data', {})
#     return render(request, 'scratch_card.html', {
#         'selected_offer': selected_offer,
#         'shop': shop,
#         'customer_name': entry_data.get('name', ''),
#         'customer_phone': entry_data.get('phone', ''),
#         'customer_bill': entry_data.get('bill_number', '')
#     })


def scratch_card(request, shop_code=None):
    if shop_code:
        shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    else:
        if not request.user.is_authenticated:
            return redirect('login')
        shop = request.user.shopprofile
    
    # Get the temporary entry
    temp_spin_id = request.session.get('temp_spin_id')
    if not temp_spin_id:
        return redirect('qr_entry_form', shop_code=shop.shop_code)
    
    # Get all offers for the shop
    offers = list(Offer.objects.filter(shop=shop))
    
    # Initialize or get the current batch from session
    if 'scratch_batch' not in request.session or 'scratch_count' not in request.session:
        # Create a new batch with exact distribution
        batch = []
        for offer in offers:
            count = int(offer.percentage)  # 50% = exactly 50 in batch of 100
            batch.extend([offer.id] * count)
        
        # Handle any remaining slots (due to floating points)
        remaining = 100 - len(batch)
        if remaining > 0:
            # Distribute remaining slots proportionally
            remaining_offers = sorted(offers, key=lambda x: x.percentage - int(x.percentage), reverse=True)
            for i in range(remaining):
                batch.append(remaining_offers[i % len(remaining_offers)].id)
        
        # Shuffle the batch
        random.shuffle(batch)
        request.session['scratch_batch'] = batch
        request.session['scratch_count'] = 0
        request.session.modified = True
    
    # Get the predetermined offer for this scratch
    batch_index = request.session['scratch_count'] % 100
    selected_offer_id = request.session['scratch_batch'][batch_index]
    selected_offer = next((o for o in offers if o.id == selected_offer_id), None)
    
    if request.method == 'POST':
        # Update the entry with the selected offer
        SpinEntry.objects.filter(id=temp_spin_id).update(offer=selected_offer)
        
        # Increment scratch count
        request.session['scratch_count'] += 1
        if request.session['scratch_count'] >= 100:
            # Reset after full batch
            del request.session['scratch_batch']
            del request.session['scratch_count']
        
        # Clear temporary session data
        if 'temp_spin_id' in request.session:
            del request.session['temp_spin_id']
        if 'entry_data' in request.session:
            del request.session['entry_data']
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return redirect('qr_entry_form', shop_code=shop.shop_code)
    
    # Pass customer data from session
    entry_data = request.session.get('entry_data', {})
    return render(request, 'scratch_card.html', {
        'selected_offer': selected_offer,
        'shop': shop,
        'customer_name': entry_data.get('name', ''),
        'customer_phone': entry_data.get('phone', ''),
        'customer_bill': entry_data.get('bill_number', '')
    })