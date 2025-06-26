from django.contrib import admin
from .models import ShopProfile, Offer, SpinEntry,ShopSettings

admin.site.register(ShopProfile)
admin.site.register(Offer)
admin.site.register(SpinEntry)
@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('shop', 'spins_per_day')
    list_filter = ('spins_per_day',)