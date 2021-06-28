from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect

from accounts.models import StockNames


class Command(BaseCommand):
    """
    Management command to fill in the kite tokens
    """

    def handle(self, *args, **options):
        stocks = StockNames.objects.filter(token__isnull=True).order_by("id")
        if stocks.count():
            print("Stocks to change ... ", stocks.count())
            cache = {}
            for stock in stocks:
                k = KiteConnect(api_key="")
                instruments = k.instruments("NSE")

                if stock.symbol in cache:
                    stock.token = str(i['instrument_token'])
                else:
                    for i in instruments:
                        cache[stock.symbol] = i['instrument_token']
                        if stock.symbol.upper() == i['tradingsymbol']:
                            stock.token = str(i['instrument_token'])
                stock.save()
        else:
            print("Message: Nothing to change")
