from django.core.exceptions import ValidationError
from .models import Offer

def validate_offer_percentages(shop):
    total = sum(offer.percentage for offer in Offer.objects.filter(shop=shop))
    if round(total, 2) != 100.0:
        raise ValidationError(f'Total offer percentage for this shop must be 100%. Current total: {total:.2f}%')


# myapp/utils.py
