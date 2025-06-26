from django.shortcuts import render, redirect
from .forms import SpinEntryForm,ShopProfileForm
from .models import SpinEntry, Offer,ShopProfile,ShopSettings
import random
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from .utils import validate_offer_percentages


# def signup_view(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('login')
#     else:
#         form = UserCreationForm()
#     return render(request, 'signup.html', {'form': form})

from django.shortcuts import render, redirect
from .forms import ShopSignupForm
from .models import ShopProfile

def signup_view(request):
    if request.method == 'POST':
        form = ShopSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create shop profile
            ShopProfile.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                shop_code=f'SHOP{user.id:04d}'
            )
            
            # Log the user in
            login(request, user)
            return redirect('login')  # Replace with your desired redirect
    else:
        form = ShopSignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
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


@login_required
def update_shop_profile(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        shop = ShopProfile.objects.create(user=request.user, shop_name='New Shop', shop_code=f'SHOP{request.user.id:04d}')

    if request.method == 'POST':
        form = ShopProfileForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('offer_list')
    else:
        form = ShopProfileForm(instance=shop)

    return render(request, 'update_profile.html', {'form': form})



@login_required
def offer_list(request):
    user = request.user
    try:
        shop = user.shopprofile
    except ShopProfile.DoesNotExist:
        # Auto-create a shop profile if missing
        shop = ShopProfile.objects.create(
            user=user,
            shop_name='New Shop',
            shop_code=f'SHOP{user.id:04d}'
        )
    offers = Offer.objects.filter(shop=shop)
    return render(request, 'offer_list.html', {'offers': offers})


from django.core.exceptions import ValidationError
from django.contrib import messages

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


def entry_form(request):
    if request.method == 'POST':
        form = SpinEntryForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                shop = ShopProfile.objects.get(shop_code=data['shop_code'])
            except ShopProfile.DoesNotExist:
                form.add_error('shop_code', 'Invalid shop code')
                return render(request, 'form.html', {'form': form})

            request.session['entry_data'] = {
                'name': data['name'],
                'phone': data['phone'],
                'shop_code': data['shop_code'],
            }
            return redirect('spin_page')
    else:
        form = SpinEntryForm()
    return render(request, 'form.html', {'form': form})


# def entry_form(request):
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             try:
#                 shop = ShopProfile.objects.get(shop_code=data['shop_code'])
                
#                 # Store in session and ensure it persists
#                 request.session['entry_data'] = {
#                     'name': data['name'],
#                     'phone': data['phone'],
#                     'shop_code': data['shop_code'],
#                 }
#                 request.session.save()  # Explicitly save session
                
#                 return redirect('spin_page')
#             except ShopProfile.DoesNotExist:
#                 form.add_error('shop_code', 'Invalid shop code')
#     else:
#         form = SpinEntryForm()
#     return render(request, 'form.html', {'form': form})

import random



from math import ceil
from django.shortcuts import render, redirect
import random
from .models import Offer, ShopProfile, SpinEntry



from django.shortcuts import render, redirect
from .models import ShopProfile, Offer

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

def spin_page(request):
    entry_data = request.session.get('entry_data')
    if not entry_data:
        return redirect('entry_form')

    try:
        shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
    except ShopProfile.DoesNotExist:
        return redirect('entry_form')

    offers = Offer.objects.filter(shop=shop)
    if not offers.exists():
        return redirect('entry_form')

    segments = build_segments(offers)
    angle_per_segment = 360 / len(segments)

    return render(request, 'spin.html', {
        'segments': segments,
        'angle_per_segment': angle_per_segment,
    })


@login_required
def edit_offer(request, offer_id):
    offer = Offer.objects.get(id=offer_id, shop=request.user.shopprofile)

    if request.method == 'POST':
        old_percentage = offer.percentage  # Backup

        offer.name = request.POST.get('name')
        offer.color = request.POST.get('color')
        offer.percentage = float(request.POST.get('percentage', 0))
        offer.save()

        try:
            validate_offer_percentages(offer.shop)
            return redirect('offer_list')
        except ValidationError as e:
            offer.percentage = old_percentage  # Revert change
            offer.save()
            messages.error(request, str(e))

    return render(request, 'edit_offer.html', {'offer': offer})

@login_required
def settings_view(request):
    try:
        shop_profile = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        # Create shop profile if it doesn't exist
        shop_profile = ShopProfile.objects.create(
            user=request.user,
            shop_name='New Shop',
            shop_code=f'SHOP{request.user.id:04d}'
        )
    
    # Get or create settings
    settings, created = ShopSettings.objects.get_or_create(shop=shop_profile)
    
    if request.method == 'POST':
        spin_limit = request.POST.get('spin_limit', '0')
        settings.spins_per_day = int(spin_limit)
        settings.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('offer_list')
    
    return render(request, 'settings.html', {
        'spin_limit': settings.spins_per_day
    })


from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

# def spin_page(request):
#     entry_data = request.session.get('entry_data')
#     if not entry_data:
#         return redirect('entry_form')

#     try:
#         shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
#     except ShopProfile.DoesNotExist:
#         return redirect('entry_form')

#     # Check spin limit
#     phone = entry_data.get('phone')
#     if phone:
#         today = timezone.now().date()
#         spin_count = SpinEntry.objects.filter(
#             phone=phone,
#             shop=shop,
#             timestamp__date=today
#         ).count()
        
#         max_spins = shop.shopsettings.spins_per_day if hasattr(shop, 'shopsettings') else 1
        
#         if max_spins > 0 and spin_count >= max_spins:  # 0 means unlimited
#             messages.error(request, f"You've reached your daily spin limit of {max_spins} spins per number")
#             return redirect('entry_form')

#     offers = Offer.objects.filter(shop=shop)
#     if not offers.exists():
#         return redirect('entry_form')

#     segments = build_segments(offers)
#     angle_per_segment = 360 / len(segments)

#     return render(request, 'spin.html', {
#         'segments': segments,
#         'angle_per_segment': angle_per_segment,
#         'phone': phone,
#         'spin_count': spin_count if phone else 0,
#         'max_spins': max_spins if phone else 1
#     })

@login_required
def process_spin(request):
    if request.method == 'POST':
        selected_offer_id = request.POST.get('selected_offer')
        entry_data = request.session.get('entry_data')
        
        try:
            offer = Offer.objects.get(id=selected_offer_id)
            shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
            
            # Debug print before saving
            print(f"Creating entry for {entry_data['name']}, phone: {entry_data['phone']}, offer: {offer.name}")
            
            # Record the spin entry
            SpinEntry.objects.create(
                name=entry_data['name'],
                phone=entry_data['phone'],
                offer=offer,
                shop=shop
            )
            
            # Debug print after saving
            print("Entry created successfully!")
            
            return redirect('spin_success')
            
        except (Offer.DoesNotExist, ShopProfile.DoesNotExist, KeyError) as e:
            print(f"Error creating spin entry: {str(e)}")
            messages.error(request, "Invalid spin data")
            return redirect('entry_form')

@login_required
def spin_entries(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        return redirect('offer_list')
    
    entries = SpinEntry.objects.filter(shop=shop).order_by('-timestamp')
    return render(request, 'spin_entries.html', {'entries': entries})