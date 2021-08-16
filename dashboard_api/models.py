from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from stock_react_api.core.models import *
from django.contrib.postgres.fields import ArrayField,JSONField

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    for creating token
    Parameters
    ----------
    sender
    instance
    created
    kwargs
    Returns
    -------
    """
    if created:
        Token.objects.create(user=instance)


class PortfolioPerformance(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default="")
    portfolio_id = models.ForeignKey(portfolio, on_delete=models.CASCADE, default="")
    date = models.DateField(null=True, blank=True)
    total_cost = models.FloatField(null=True, blank=True)
    total_quantity = models.FloatField(null=True, blank=True)
    total_value = models.FloatField(null=True, blank=True)
    daily_return = models.FloatField(null=True, blank=True)
    cummeletive_return = models.FloatField(null=True, blank=True)
    symbols = ArrayField(base_field=models.CharField(max_length=3000, null=True, blank=True), null=True, blank=True)
    stock_value= JSONField(null=True, blank=True)

