from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from alyx.base import BaseModel


class FoodConsumptionAmount(BaseModel):
    """
    Weighing of a subject's amount of food consumed.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The user who weighed the food"
    )
    housing_subject = models.ForeignKey(
        'misc.HousingSubject',
        help_text="Housing/subject information for this food weighing"
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    amount = models.FloatField(
        validators=[MinValueValidator(limit_value=0)],
        help_text="Weight in grams"
    )

    def __str__(self):
        return 'Amount of %.2f g for %s' % (self.amount,
                                            str(self.subject),
                                            )
