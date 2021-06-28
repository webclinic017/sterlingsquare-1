from django.core.management.base import BaseCommand
import datetime

from accounts.models import PortfolioValues, StockPrices


class Command(BaseCommand):
    """
    Management command to fill in the kite tokens
    """

    def handle(self, *args, **options):
        values = PortfolioValues.objects.all().order_by("timestamp")
        prices = StockPrices.objects.all().order_by("time_stamp")

        min_value = values.first().timestamp
        max_value = values.last().timestamp

        min_price = prices.first().time_stamp
        max_price = prices.last().time_stamp

        print("Min Time Stamp for Portfolio Values: ", min_value + datetime.timedelta(hours=5, minutes=30))
        print("Max Time Stamp for Portfolio Values: ", max_value + datetime.timedelta(hours=5, minutes=30))

        print("Min Time Stamp for Stock Prices: ", min_price + datetime.timedelta(hours=5, minutes=30))
        print("Max Time Stamp for Stock Prices: ", max_price + datetime.timedelta(hours=5, minutes=30))
