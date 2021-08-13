import pandas as pd
from sterling_square import celery_app

from utils.AutoLogin import AutoLogin
from .models import StockPrices
from utils.util_functions import init_singleton
from utils.date_utils import *

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect

from accounts.models import StockNames
from utils.util_functions import read_zerodha_credentials

@celery_app.task()
def initialize_singleton():
    init_singleton()
    print("Injected Singleton in API context")


@celery_app.task()
def sync_credentials():
    print("Syncing Zerodha Credentials ....")
    auto_login = AutoLogin()
    auto_login.perform_login(auto_close=True)
    print("Syncing the credentials ....")


@celery_app.task()
def clear_old_stock_data():
    print("Clearing Previous Data ...")
    # Check if the market is opened today.
    market_opened_today = is_market_opened_date()
    print("Market opened today? {}".format(market_opened_today))
    if market_opened_today:
        # If market is opened today, delete the older data to accomodate the new records.
        # Delete the previous business day data.
        start, _ = get_day_range()

        # Delete every data less than today's date
        stocks = StockPrices.objects.filter(time_stamp__lt=start)

        # prev_start, prev_end = get_day_range(get_previous_business_day())
        # print("Previous Date : {}".format(prev_start.date()))
        #
        # stocks = StockPrices.objects.filter(
        #     time_stamp__gte=prev_start, time_stamp__lte=prev_end
        # )
        total = stocks.count()
        stocks.delete()

        print("Cleared Previous Day Data. Records Deleted: {}".format(total))
        return total
    else:
        # Do not delete previous business day data.
        print("Didn't Clear Previous Day Data. Records Deleted: 0")
        return 0


@celery_app.task()
def clear_old_stock_data_2():
    print("Clearing Previous Data ... File based delete ...")
    # Check if the market is opened today.
    market_opened_today = is_market_opened_date()
    print("Market opened today? {}".format(market_opened_today))
    if market_opened_today:
        # If market is opened today, delete the older data to accommodate the new records.
        # Delete the previous business day data.
        start, _ = get_day_range()
        root = os.path.join(settings.MEDIA_ROOT, "symbol_data")

        total = 0
        directories = sorted(os.listdir(root))
        for x in directories:
            dir_path = os.path.join(root, x)
            files = os.listdir(dir_path)

            dt = str(datetime.datetime.now().date())
            exempted_file = "{}_{}.csv".format(x, dt)
            for file in files:
                if file != exempted_file:
                    os.remove(os.path.join(dir_path, file))
                    total += 1

        print("Cleared Previous Day Data. Records Deleted: {}".format(total))
        return total
    else:
        # Do not delete previous business day data.
        print("Didn't Clear Previous Day Data. Records Deleted: 0")
        return 0


@celery_app.task()
def load_symbols():
    print("Loading Symbols ....")
    try:
        credentials = read_zerodha_credentials()
        api_key = credentials.get("api_key")

        if not api_key:
            print("Kite API Key unavailable")
            exit(0)

        url = "https://www1.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        if df.empty:
            print("Nothing read from the NSE Site")
            exit(0)

        # df = df[["SYMBOL", "NAME OF COMPANY", " ISIN NUMBER"]]

        loop = True
        retry = 1
        while loop:
            try:
                print("Retry 1")
                kc = KiteConnect(api_key=api_key)
                loop = False
                retry += 1
            except:
                pass

        instruments = kc.instruments("NSE")
        instruments_mapping = {}
        for instrument in instruments:
            instruments_mapping[instrument['tradingsymbol']] = instrument['instrument_token']

        df['token'] = df["SYMBOL"].apply(lambda x: int(instruments_mapping.get(x, 0.0)))
        # df = df[df['token'] > 0]      # only getting symbols with a instrument token

        invalid_token, new_symbols, updated_symbols = 0, 0, 0
        for r in df.to_dict("records"):
            symbol = r['SYMBOL']  # symbol
            company = r['NAME OF COMPANY']  # name
            isin = r[' ISIN NUMBER']  # isin
            token = r['token']  # token

            series = r[' SERIES']
            date_of_listing = r[' DATE OF LISTING']
            date_of_listing_parsed = None
            if date_of_listing:
                try:
                    date_of_listing_parsed = make_aware(
                        datetime.datetime.strptime(
                            date_of_listing.title(), "%d-%b-%Y"
                        )
                    )
                except:
                    pass

            paid_up = r[' PAID UP VALUE']
            market = r[' MARKET LOT']
            face_value = r[' FACE VALUE']

            if token != 0:
                symbol_obj = StockNames.objects.filter(symbol__iexact=symbol)
                if symbol_obj.exists():
                    # Update the information
                    # print("Exists: {}".format(symbol))
                    obj = symbol_obj.first()
                    obj.name = company
                    obj.isin = isin
                    obj.token = token
                    obj.series = series
                    if date_of_listing_parsed:
                        obj.date_of_listing = date_of_listing_parsed
                    obj.paid_up = paid_up
                    obj.market = market
                    obj.face_value = face_value
                    obj.save()
                    updated_symbols += 1
                else:
                    # Create a new record
                    # print("Does not Exists: {}".format(symbol))
                    StockNames.objects.create(
                        symbol=symbol,
                        name=company,
                        isin=isin,
                        token=token,
                        series=series,
                        date_of_listing=date_of_listing_parsed,
                        paid_up=paid_up,
                        market=market,
                        face_value=face_value,
                    )
                    new_symbols += 1
            else:
                invalid_token += 1

        print("Updated: {}, New: {}, Token: {}".format(updated_symbols, new_symbols, invalid_token))
    except Exception as e:
        print("Error ", str(e))
        exit(0)
