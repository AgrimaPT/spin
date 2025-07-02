from django.contrib import admin
from .models import ShopProfile, Offer, SpinEntry,ShopSettings,SocialVerification

admin.site.register(ShopProfile)
admin.site.register(Offer)
admin.site.register(SpinEntry)
admin.site.register(ShopSettings)
admin.site.register(SocialVerification)

