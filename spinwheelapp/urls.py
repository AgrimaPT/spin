from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('shop/update/', views.update_shop_profile, name='update_shop_profile'),
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/add/', views.add_offer, name='add_offer'),
    path('offers/delete/<int:offer_id>/', views.delete_offer, name='delete_offer'),
    # path('', views.entry_form, name='entry_form'),         # Form page
    # path('spin/<str:shop_code>/', views.qr_entry_form, name='qr_entry_form'),
    # path('spin/', views.spin_page, name='spin_page'),       

    path('entry/<str:shop_code>/', views.qr_entry_form, name='qr_entry_form'),
    
    # Spin page URL (modified to accept shop_code)
    path('spin/', views.spin_page, name='spin_page'),

    path('offers/<int:offer_id>/edit/', views.edit_offer, name='edit_offer'),
    path('settings/', views.settings_view, name='settings'),
    path('process-spin/', views.process_spin, name='process_spin'),
    path('spin-entries/', views.spin_entries, name='spin_entries'),
    #path('<str:shop_code>/spin-entries/', views.spin_entries, name='spin_entries'),
    path('verify/<str:shop_code>/', views.social_verification, name='social_verification'),
    # urls.py

    path('scratch-card/', views.scratch_card, name='scratch_card'),
    # path('scratch-card/success/', views.scratch_card_success, name='scratch_card_success'),
    path('redeem-entry/<int:entry_id>/', views.redeem_entry, name='redeem_entry'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
