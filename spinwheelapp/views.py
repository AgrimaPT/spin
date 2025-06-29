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


from django.urls import reverse

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

    # Generate QR code URL
    # qr_url = request.build_absolute_uri(
    #     reverse('qr_entry_form', kwargs={'shop_code': shop.shop_code})
    # )

    host = 'https://lucky.newintro.in'  # Replace with domain if available
    qr_url = f"{host}{reverse('qr_entry_form', kwargs={'shop_code': shop.shop_code})}"

    
    # You can use a QR code generation service or generate locally
    # Using QRServer API (simple solution)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_url}"

    return render(request, 'update_profile.html', {'form': form,'qr_url': qr_url,
        'qr_code_url': qr_code_url,
        'shop': shop,})



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


# def entry_form(request):
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             try:
#                 shop = ShopProfile.objects.get(shop_code=data['shop_code'])
#             except ShopProfile.DoesNotExist:
#                 form.add_error('shop_code', 'Invalid shop code')
#                 return render(request, 'form.html', {'form': form})

#             request.session['entry_data'] = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': data['shop_code'],
#             }
#             return redirect('spin_page')
#     else:
#         form = SpinEntryForm()
#     return render(request, 'form.html', {'form': form})


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
#                 request.session.modified = True  # Ensure session is saved
#                 return redirect('spin_page')
#             except ShopProfile.DoesNotExist:
#                 form.add_error('shop_code', 'Invalid shop code')
#     else:
#         form = SpinEntryForm()
#     return render(request, 'form.html', {'form': form})


from django.shortcuts import get_object_or_404

# def qr_entry_form(request, shop_code):
#     # Verify shop exists
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             request.session['entry_data'] = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': shop_code,  # Use from URL, not form
#             }
#             request.session.modified = True
#             return redirect('spin_page')
#     else:
#         # Pre-populate form with shop code (hidden field)
#         initial = {'shop_code': shop_code}
#         form = SpinEntryForm(initial=initial)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#     })

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

# def qr_entry_form(request, shop_code):
#     # Verify shop exists
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             request.session['entry_data'] = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': shop_code,  # Use from URL, not form
#             }
#             request.session.modified = True
#             return redirect('spin_page')
#     else:
#         # Pre-populate form with shop code (hidden field)
#         initial = {'shop_code': shop_code}
#         form = SpinEntryForm(initial=initial)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#     })


# def qr_entry_form(request, shop_code):
#     # Verify shop exists
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
            
#             # Verify shop code matches (security check)
#             if data['shop_code'] != shop_code:
#                 messages.error(request, "Invalid shop code")
#                 return redirect('qr_entry_form', shop_code=shop_code)
            
#             # Create new session data (clear any existing first)
#             request.session['entry_data'] = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': shop_code,
#                 'verified': True  # Add verification flag
#             }
#             request.session.modified = True
            
#             return redirect('spin_page')
#     else:
#         # Pre-populate form with shop code (hidden field)
#         initial = {'shop_code': shop_code}
#         form = SpinEntryForm(initial=initial)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#     })

def qr_entry_form(request, shop_code):
    shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
    if request.method == 'POST':
        form = SpinEntryForm(request.POST)
        if form.is_valid():
            # Create new session dict to ensure all keys are set
            request.session['entry_data'] = {
                'name': form.cleaned_data['name'],
                'phone': form.cleaned_data['phone'],
                'shop_code': shop_code,
                'verified': True
            }
            # Force session save
            request.session.save()
            return redirect('spin_page')
    
    # GET request or invalid form
    form = SpinEntryForm(initial={'shop_code': shop_code})
    return render(request, 'form.html', {'form': form, 'shop': shop})

# def qr_entry_form(request, shop_code):
#     # Verify shop exists
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
            
#             # Verify shop code matches (security check)
#             if data['shop_code'] != shop_code:
#                 messages.error(request, "Invalid shop code")
#                 return redirect('qr_entry_form', shop_code=shop_code)
            
#             # Create new session data (clear any existing first)
#             request.session.pop('entry_data', None)  # Clear any existing entry
#             request.session['entry_data'] = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': shop_code,
#                 'verified': True  # Add verification flag
#             }
#             request.session.modified = True
            
#             # Debug print
#             print("Session data set:", request.session['entry_data'])
            
#             return redirect('spin_page')
#     else:
#         # Pre-populate form with shop code (hidden field)
#         initial = {'shop_code': shop_code}
#         form = SpinEntryForm(initial=initial)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#     })

# def qr_entry_form(request, shop_code):
#     shop = get_object_or_404(ShopProfile, shop_code=shop_code)
#     shop_settings = ShopSettings.objects.get(shop=shop)
    
#     if request.method == 'POST':
#         form = SpinEntryForm(request.POST)
#         if form.is_valid():
#             data = form.cleaned_data
#             entry_data = {
#                 'name': data['name'],
#                 'phone': data['phone'],
#                 'shop_code': shop_code,
#             }
#             if shop_settings.require_bill_number:
#                 entry_data['bill_number'] = data['bill_number']
            
#             request.session['entry_data'] = entry_data
#             request.session.modified = True
#             return redirect('spin_page')
#     else:
#         initial = {'shop_code': shop_code}
#         form = SpinEntryForm(initial=initial)
    
#     return render(request, 'form.html', {
#         'form': form,
#         'shop': shop,
#         'require_bill_number': shop_settings.require_bill_number
#     })

from math import ceil
from django.shortcuts import render, redirect
import random
from .models import Offer, ShopProfile, SpinEntry

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

# def spin_page(request):
#     entry_data = request.session.get('entry_data')
#     if not entry_data:
#         return redirect('qr_entry_form')

#     try:
#         shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
#     except ShopProfile.DoesNotExist:
#         return redirect('qr_entry_form',shop_code=entry_data.get('shop_code', ''))

#     offers = Offer.objects.filter(shop=shop)
#     if not offers.exists():
#         return redirect('qr_entry_form',shop_code=entry_data.get('shop_code', ''))

#     segments = build_segments(offers)
#     angle_per_segment = 360 / len(segments)

#     return render(request, 'spin.html', {
#         'segments': segments,
#         'angle_per_segment': angle_per_segment,
#     })


# def spin_page(request):
#     # Get session data with proper checks
#     entry_data = request.session.get('entry_data')
    
#     # Debug print
#     print("Session data in spin_page:", entry_data)
    
#     if not entry_data or not entry_data.get('verified'):
#         messages.error(request, "Please complete the entry form first")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     try:
#         shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
#     except ShopProfile.DoesNotExist:
#         messages.error(request, "Invalid shop")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     offers = Offer.objects.filter(shop=shop)
#     if not offers.exists():
#         messages.error(request, "No offers available for this shop")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     segments = build_segments(offers)
#     angle_per_segment = 360 / len(segments)

#     return render(request, 'spin.html', {
#         'segments': segments,
#         'angle_per_segment': angle_per_segment,
#         'shop': shop,
#     })

# def spin_page(request):
#     # Get session data with proper checks
#     entry_data = request.session.get('entry_data')
    
#     if not entry_data or not entry_data.get('verified'):
#         messages.error(request, "Please complete the entry form first")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     try:
#         shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
#     except ShopProfile.DoesNotExist:
#         messages.error(request, "Invalid shop")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     offers = Offer.objects.filter(shop=shop)
#     if not offers.exists():
#         messages.error(request, "No offers available for this shop")
#         return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
#     segments = build_segments(offers)
#     angle_per_segment = 360 / len(segments)

#     return render(request, 'spin.html', {
#         'segments': segments,
#         'angle_per_segment': angle_per_segment,
#         'shop': shop,
#     })


def spin_page(request):
    # print("Entering spin_page view")  # Debug
    # print("Session data:", request.session.get('entry_data'))  # Debug
    
    entry_data = request.session.get('entry_data')
    if not entry_data or not entry_data.get('verified'):
        print("Redirecting - missing session data or verification")  # Debug
        messages.error(request, "Please complete the entry form first")
        return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
    try:
        shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
    except ShopProfile.DoesNotExist:
        print("Redirecting - shop not found")  # Debug
        messages.error(request, "Invalid shop")
        return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
    offers = Offer.objects.filter(shop=shop)
    if not offers.exists():
        print("Redirecting - no offers found")  # Debug
        messages.error(request, "No offers available for this shop")
        return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
    
    segments = build_segments(offers)
    angle_per_segment = 360 / len(segments)

    print("Rendering spin page")  # Debug
    return render(request, 'spin.html', {
        'segments': segments,
        'angle_per_segment': angle_per_segment,
        'shop': shop,
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
# @login_required
# def settings_view(request):
#     try:
#         shop_profile = request.user.shopprofile
#     except ShopProfile.DoesNotExist:
#         # Create shop profile if it doesn't exist
#         shop_profile = ShopProfile.objects.create(
#             user=request.user,
#             shop_name='New Shop',
#             shop_code=f'SHOP{request.user.id:04d}'
#         )
    
#     # Get or create settings
#     settings, created = ShopSettings.objects.get_or_create(shop=shop_profile)
    
#     if request.method == 'POST':
#         spin_limit = request.POST.get('spin_limit', '0')
#         settings.spins_per_day = int(spin_limit)
#         settings.save()
#         messages.success(request, 'Settings updated successfully!')
#         return redirect('offer_list')
    
#     return render(request, 'settings.html', {
#         'spin_limit': settings.spins_per_day
#     })

@login_required
def settings_view(request):
    try:
        shop_profile = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        shop_profile = ShopProfile.objects.create(
            user=request.user,
            shop_name='New Shop',
            shop_code=f'SHOP{request.user.id:04d}'
        )
    
    settings, created = ShopSettings.objects.get_or_create(shop=shop_profile)
    
    if request.method == 'POST':
        settings.spins_per_day = int(request.POST.get('spin_limit', '0'))
        settings.require_bill_number = 'require_bill_number' in request.POST
        settings.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('offer_list')
    
    return render(request, 'settings.html', {
        'spin_limit': settings.spins_per_day,
        'shop_settings': settings
    })


from django.contrib import messages
from django.utils import timezone
from datetime import timedelta



# @login_required
# def process_spin(request):
#     if request.method == 'POST':
#         selected_offer_id = request.POST.get('selected_offer')
#         entry_data = request.session.get('entry_data')
        
#         try:
#             offer = Offer.objects.get(id=selected_offer_id)
#             shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
            
#             # Debug print before saving
#             print(f"Creating entry for {entry_data['name']}, phone: {entry_data['phone']}, offer: {offer.name}")
            
#             # Record the spin entry
#             SpinEntry.objects.create(
#                 name=entry_data['name'],
#                 phone=entry_data['phone'],
#                 offer=offer,
#                 shop=shop
#             )
            
#             # Debug print after saving
#             print("Entry created successfully!")
            
#             return redirect('spin_success')
            
#         except (Offer.DoesNotExist, ShopProfile.DoesNotExist, KeyError) as e:
#             print(f"Error creating spin entry: {str(e)}")
#             messages.error(request, "Invalid spin data")
#             return redirect('entry_form')


# def process_spin(request):
#     if request.method == 'POST':
#         selected_offer_id = request.POST.get('selected_offer')
#         entry_data = request.session.get('entry_data')
        
#         if not entry_data:
#             messages.error(request, "Session expired. Please fill the form again.")
#             return redirect('qr_entry_form')
            
#         try:
#             offer = Offer.objects.get(id=selected_offer_id)
#             shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
            
#             # Create the entry
#             entry = SpinEntry(
#                 name=entry_data['name'],
#                 phone=entry_data['phone'],
#                 offer=offer,
#                 shop=shop
#             )
            
#             # For authenticated users, set the user field
#             if request.user.is_authenticated:
#                 entry.user = request.user
                
#             entry.save()
            
#             # Clear session data after successful save
#             del request.session['entry_data']
#             request.session.modified = True
            
#             return redirect('spin_success')
            
#         except Offer.DoesNotExist:
#             messages.error(request, "Invalid offer selected")
#         except ShopProfile.DoesNotExist:
#             messages.error(request, "Shop not found")
#         except Exception as e:
#             messages.error(request, f"Error saving entry: {str(e)}")
#             print(f"Error saving spin entry: {str(e)}")  # Log the error
            
#         return redirect('qr_entry_form')



# def process_spin(request):
#     if request.method == 'POST':
#         selected_offer_id = request.POST.get('selected_offer')
#         entry_data = request.session.get('entry_data')
        
#         if not entry_data:
#             messages.error(request, "Session expired. Please fill the form again.")
#             return redirect('entry_form')
            
#         try:
#             offer = Offer.objects.get(id=selected_offer_id)
#             shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
            
#             entry = SpinEntry(
#                 name=entry_data['name'],
#                 phone=entry_data['phone'],
#                 bill_number=entry_data.get('bill_number'),  # Add this line
#                 offer=offer,
#                 shop=shop
#             )
            
#             if request.user.is_authenticated:
#                 entry.user = request.user
                
#             entry.save()
            
#             del request.session['entry_data']
#             request.session.modified = True
            
#             return redirect('spin_success')
            
#         except Offer.DoesNotExist:
#             messages.error(request, "Invalid offer selected")
#         except ShopProfile.DoesNotExist:
#             messages.error(request, "Shop not found")
#         except Exception as e:
#             messages.error(request, f"Error saving entry: {str(e)}")
            
#         return redirect('entry_form')


def process_spin(request):
    if request.method == 'POST':
        selected_offer_id = request.POST.get('selected_offer')
        entry_data = request.session.get('entry_data')
        
        if not entry_data:
            messages.error(request, "Session expired. Please fill the form again.")
            return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))
            
        try:
            offer = Offer.objects.get(id=selected_offer_id)
            shop = ShopProfile.objects.get(shop_code=entry_data['shop_code'])
            
            entry = SpinEntry(
                name=entry_data['name'],
                phone=entry_data['phone'],
                bill_number=entry_data.get('bill_number'),
                offer=offer,
                shop=shop
            )
            
            if request.user.is_authenticated:
                entry.user = request.user
                
            entry.save()
            
            del request.session['entry_data']
            request.session.modified = True
            
            return redirect('spin_success')  # Make sure this URL exists
            
        except Offer.DoesNotExist:
            messages.error(request, "Invalid offer selected")
        except ShopProfile.DoesNotExist:
            messages.error(request, "Shop not found")
        except Exception as e:
            messages.error(request, f"Error saving entry: {str(e)}")
            
        return redirect('qr_entry_form', shop_code=entry_data.get('shop_code', ''))

@login_required
def spin_entries(request):
    try:
        shop = request.user.shopprofile
    except ShopProfile.DoesNotExist:
        return redirect('offer_list')
    
    entries = SpinEntry.objects.filter(shop=shop).order_by('-timestamp')
    return render(request, 'spin_entries.html', {'entries': entries})

# @login_required
# def spin_entries(request, shop_code):
#     try:
#         shop = get_object_or_404(ShopProfile, code=shop_code)
#     except ShopProfile.DoesNotExist:
#         return redirect('offer_list')
    
#     entries = SpinEntry.objects.filter(shop=shop).order_by('-timestamp')
#     return render(request, 'spin_entries.html', {'entries': entries})