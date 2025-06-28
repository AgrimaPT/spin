from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# If using default User model (recommended for simplicity)
# No need to create a custom Owner model unless needed
class ShopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    shop_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.shop_name
    
# @receiver(post_save, sender=User)
# def create_shop_profile(sender, instance, created, **kwargs):
#     if created:
#         ShopProfile.objects.create(
#             user=instance,
#             shop_name='New Shop',
#             shop_code=f'SHOP{instance.id:04d}'
#         )

    
class Offer(models.Model):
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#ffffff")
    percentage = models.FloatField(help_text="Probability percentage (e.g., 25.0)")
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class SpinEntry(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    bill_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.offer.name} ({self.timestamp.date()})"

class ShopSettings(models.Model):
    shop = models.OneToOneField(ShopProfile, on_delete=models.CASCADE)
    spins_per_day = models.IntegerField(
        default=1,
        choices=(
            (1, '1 spin per day'),
            (2, '2 spins per day'),
            (0, 'Unlimited spins')
        ),
        help_text="Maximum spins allowed per mobile number per day"
    )

    require_bill_number = models.BooleanField(
        default=False,
        help_text="Enable to require bill number for spin entries"
    )
    
    def __str__(self):
        return f"Settings for {self.shop.shop_name}"