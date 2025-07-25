from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
from django.core.validators import RegexValidator
import shortuuid

class ShopProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    shop_code = models.CharField(max_length=10, unique=True)
    whatsapp_number = models.CharField(
        max_length=10,default="8848647616",
        validators=[RegexValidator(r'^[0-9]+$', 'Enter a valid phone number')],
        help_text="WhatsApp number with country code (e.g. 919876543210)"
    )

    def save(self, *args, **kwargs):
        if not self.shop_code:  # Only for new instances
            self.shop_code = self.generate_unique_shop_code(self.shop_name)
        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_shop_code(cls, shop_name, max_attempts=100):
        prefix = shop_name[:2].upper() if len(shop_name) >= 2 else 'SH'
        for _ in range(max_attempts):
            random_digits = ''.join(random.choices('0123456789', k=4))
            shop_code = f"{prefix}{random_digits}"
            if not cls.objects.filter(shop_code=shop_code).exists():
                return shop_code
        raise RuntimeError("Could not generate a unique shop code after multiple attempts")
    
    def __str__(self):
        return f"{self.shop_name } x {self.shop_code}"

    
class Offer(models.Model):
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)
    color = models.CharField(max_length=7, default="#ffffff")
    percentage = models.FloatField(help_text="Probability percentage (e.g., 25.0)")
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class SpinEntry(models.Model):
    short_id = models.CharField(max_length=8, unique=True, editable=False, null=True, blank=True)

    name = models.CharField(max_length=100)
    
    # offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, null=True, blank=True)
    shop = models.ForeignKey(ShopProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    bill_number = models.CharField(max_length=50, blank=True, null=True,default=None )
    is_redeemed = models.BooleanField(default=False)

    phone = models.CharField(max_length=10, validators=[
        RegexValidator(
            regex=r'^[6-9]\d{9}$',
            message="Enter a valid  phone number"
        )
    ])

    def save(self, *args, **kwargs):
        if not self.short_id:
            self.short_id = shortuuid.ShortUUID().random(length=8)  # e.g., "AbC12XyZ"
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['shop', 'bill_number'],
                name='unique_bill_per_shop',
                condition=models.Q(bill_number__isnull=False) & ~models.Q(bill_number=''),
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.offer.name if self.offer else 'No Offer'} ({self.timestamp.date()})"

class GameType(models.TextChoices):
    SPIN_WHEEL = 'SW', 'Spin Wheel'
    SCRATCH_CARD = 'SC', 'Scratch Card'




class ShopSettings(models.Model):
    shop = models.OneToOneField(ShopProfile, on_delete=models.CASCADE)

    require_bill_number = models.BooleanField(
        default=False,
        help_text="Enable to require bill number for spin entries"
    )

    require_social_verification = models.BooleanField(
        default=False,
        help_text="Enable to require social media verification before spinning"
    )
    require_screenshot = models.BooleanField(
        default=False,
        help_text="Enable to require screenshot proof for social verification"
    )
    instagram_url = models.URLField(blank=True, null=True)
    google_review_url = models.URLField(blank=True, null=True)

    game_type = models.CharField(
        max_length=2,
        choices=GameType.choices,
        default=GameType.SPIN_WHEEL
    )

    allow_multiple_entries_per_phone = models.BooleanField(
        default=True,
        help_text="Allow the same phone number to spin multiple times per day (only applicable when bill number is not required)"
    )
    
    def __str__(self):
        return f"Settings for {self.shop.shop_name}-{self.shop.shop_code}"
    

from django.core.validators import FileExtensionValidator

class SocialVerification(models.Model):
    entry = models.OneToOneField(SpinEntry, on_delete=models.CASCADE, related_name='social_verification')
    instagram_screenshot = models.ImageField(
        upload_to='verifications/instagram/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Upload screenshot of Instagram follow"
    )
    google_review_screenshot = models.ImageField(
        upload_to='verifications/google/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Upload screenshot of Google review"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Verification for {self.entry.name}"
    def __str__(self):
        if not self.entry:
            return "Verification (no associated entry)"
        return f"Verification for {self.entry.name if self.entry.name else 'Unknown User'}"