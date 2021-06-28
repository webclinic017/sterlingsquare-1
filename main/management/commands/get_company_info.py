import bs4
import datetime
import requests
import pandas as pd
from threading import Thread

from django.conf import settings
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from main.tasks import update_stock_market_details_3
from accounts.models import StockNames, StockGeneralInfo


def get_profile(symbol, api_key, r):
    try:
        re = requests.get("https://financialmodelingprep.com/api/v3/profile/{}.NS?apikey={}".format(symbol, api_key))
        if isinstance(re.json(), list):
            if len(re.json()) > 0:
                r['profile'] = re.json()[0]
            else:
                r['profile'] = {}
        else:
            r['profile'] = {}
    except Exception as e:
        r['profile'] = {}


def get_ratios(symbol, api_key, r):
    try:
        re = requests.get(
            "https://financialmodelingprep.com/api/v3/ratios/{}.NS?limit=1&apikey={}&period=quarter"\
                .format(symbol, api_key)
        )
        if isinstance(re.json(), list):
            if len(re.json()) > 0:
                r['ratio'] = re.json()[0]
            else:
                r['ratio'] = {}
        else:
            r['ratio'] = {}
    except Exception as e:
        r['ratio'] = {}


def get_quotes(symbol, api_key, r):
    try:
        re = requests.get(
            "https://financialmodelingprep.com/api/v3/quote/{}.NS?apikey={}".format(symbol, api_key)
        )
        if isinstance(re.json(), list):
            if len(re.json()) > 0:
                r['quote'] = re.json()[0]
            else:
                r['quote'] = {}
        else:
            r['quote'] = {}
    except Exception as e:
        r['quote'] = {}


def get_financial_model_group_data_and_store(stock: StockGeneralInfo, new: bool, api_key: str):
    """
    :param stock: StockGeneralInfo Object
    :param new: new=True represents a new record
    :param api_key:
    """
    print(f"Symbol: {stock.symbol}")
    r = {}
    t1 = Thread(
        target=get_profile, args=(stock.symbol, api_key, r)
    )
    t2 = Thread(
        target=get_ratios, args=(stock.symbol, api_key, r)
    )
    t3 = Thread(
        target=get_quotes, args=(stock.symbol, api_key, r)
    )
    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    profile = r['profile']
    ratios = r['ratio']
    quote = r['quote']

    err = len(profile) == 0 or len(ratios) == 0 or len(quote) == 0

    market_cap = profile.get("mktCap")
    average_volume = profile.get("volAvg")
    currency = profile.get("currency")
    description = profile.get("description")
    if description and "founded in " in description:
        founded = int(description.split("founded in ")[-1][:4])
    else:
        founded = None

    industry = profile.get("industry")
    sector = profile.get("sector")
    address = profile.get("address")
    ipo_date = profile.get("ipoDate")
    if ipo_date:
        ipo_date = datetime.datetime.strptime(ipo_date, "%Y-%m-%d")
        ipo_date = make_aware(datetime.datetime(ipo_date.year, ipo_date.month, ipo_date.day))
    employees = profile.get("fullTimeEmployees")
    ceo = profile.get("ceo")
    city = profile.get("city")
    state = profile.get("state")
    country = profile.get("country")

    # RATIO fields
    price_earning_ratio = ratios.get("priceEarningsRatio")
    dividend_yield = ratios.get("dividendYield")

    # QUOTE fields
    high_today = quote.get("dayHigh")
    low_today = quote.get("dayLow")
    open_price = quote.get("open")
    volume = quote.get("volume")
    yearly_high = quote.get("yearHigh")
    yearly_low = quote.get("yearLow")

    if not employees:
        employees = None

    # if error occurred while collecting the data, do not update the exisitng data at all.
    if not err:
        stock.market_cap = market_cap
        stock.average_volume = average_volume
        stock.currency = currency
        stock.founded = founded
        stock.industry = industry
        stock.sector = sector
        stock.address = address
        stock.description = description
        stock.ipo_date = ipo_date
        stock.employees = employees
        stock.ceo = ceo
        stock.city = city
        stock.state = state
        stock.country = country

        stock.price_earning_ratio = price_earning_ratio
        stock.dividend_yield = dividend_yield

        stock.high_today = high_today
        stock.low_today = low_today
        stock.open_price = open_price
        stock.volume = volume
        stock.yearly_high = yearly_high
        stock.yearly_low = yearly_low

        if new:
            stock.created = make_aware(datetime.datetime.now())
            # created += 1
        else:
            pass
            # updated += 1
        stock.updated = make_aware(datetime.datetime.now())
        stock.save()
    else:
        # Set updated to None, to get the data in the next cycle.
        stock.updated = None
        stock.save()


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Running Async Task: ")
        update_stock_market_details_3.apply()
        # names = StockNames.objects.filter().order_by("id")
        # api_key = settings.FINANCIAL_MODEL_GRP_API_KEY
        #
        # for name in names:
        #     stock = StockGeneralInfo.objects.filter(symbol__iexact=name.symbol).order_by("id")
        #     new, exists = False, True
        #     if stock.exists():
        #         stock = stock.first()
        #     else:
        #         new = True
        #         exists = False
        #         stock = StockGeneralInfo(symbol=name.symbol)
        #         stock.save()
        #
        #     if exists:
        #         if not stock.updated:
        #             # if the object exists but it was never updated, update it now.
        #             get_financial_model_group_data_and_store(stock, new, api_key)
        #         else:
        #             interval = 30 * 24 * 3600  # 30 days
        #             if (make_aware(datetime.datetime.now()) - stock.updated).total_seconds() >= interval:
        #                 # if a symbol was last updated at least more than 30 days ago, update it now.
        #                 get_financial_model_group_data_and_store(stock, new, api_key)
        #             else:
        #                 # Do nothing if the info was last updated something between a month.
        #                 pass
        #     else:
        #         # if the object doesn't already exist, create one and save the fetched data.
        #         get_financial_model_group_data_and_store(stock, new, api_key)
