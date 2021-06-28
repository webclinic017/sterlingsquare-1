import os
import pickle
import datetime
import random
import json
from django.core.cache import cache
from django.db.models import Sum
from django.utils.timezone import make_aware
import requests
import pandas as pd
from threading import Thread
# import pandas as pd
#
# from accounts.tasks import StockPrices
from utils.date_utils import *
from accounts.models import Position, ZerodhaCredentials, PortfolioValues
from yahoo_fin import stock_info as si
from dateutil.relativedelta import relativedelta

from decimal import localcontext, Decimal, ROUND_HALF_UP

from django.conf import settings


def read_zerodha_credentials(model=False):
    """
    Function to read Zerodha Credentials from the Pickle file.
    """
    credentials = getattr(settings, "ZERODHA_CREDENTIALS")
    # if not credentials:
    #     return None
    #
    # path = credentials.get("zerodha_creds_path")
    # if not path:
    #     return None
    #
    # if not os.path.exists(path):
    #     return None
    #
    # with open(path, "rb") as fi:
    #     zerodha_credentials = pickle.load(fi)

    creds = ZerodhaCredentials.objects.all().order_by("id").first()
    if not creds:
        return None

    zerodha_credentials = json.loads(creds.credentials)
    zerodha_credentials['login_time'] = creds.login_time
    if not model:
        return zerodha_credentials
    return zerodha_credentials, creds


def read_zerodha_credentials_threaded(result, model=False):
    """
    Function to read Zerodha Credentials from the Pickle file.
    """
    credentials = getattr(settings, "ZERODHA_CREDENTIALS")
    # if not credentials:
    #     return None
    #
    # path = credentials.get("zerodha_creds_path")
    # if not path:
    #     return None
    #
    # if not os.path.exists(path):
    #     return None
    #
    # with open(path, "rb") as fi:
    #     zerodha_credentials = pickle.load(fi)

    creds = ZerodhaCredentials.objects.all().order_by("id").first()
    if not creds:
        return None

    zerodha_credentials = json.loads(creds.credentials)
    zerodha_credentials['login_time'] = creds.login_time
    if not model:
        result['zerodha'] = zerodha_credentials
    else:
        result['zerodha'] = zerodha_credentials, creds


def price_change(key, live_price, prev_price):
    """
    calculate price change
    """
    if not prev_price:
        return {}
    if not live_price:
        return {}
    response = {}
    difference = 0
    percentage = 0
    color = "#ff5000"
    btn_color = "#ff5000"
    scatter_s_color = "rgba(255, 80, 0, 0.58)"
    scatter_s_color_status = False
    live_price = float(live_price)
    if key == '1D':
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price / prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100
    if key == '1m':

        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '3m':

        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '6m':
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '1y':
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '5y':
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    difference = num_quantize(float(difference))
    percentage = num_quantize(float(percentage))
    if difference >= 0:
        difference = "+₹" + str(difference)
        percentage = "+" + str(percentage)
        # color = "#01ec36" #light green
        btn_color = "#28a745"
        color = "#00ff39"
        scatter_s_color = "rgba(40, 167, 69, 0.58)"
        scatter_s_color_status = True

    response['color'] = color
    response['btn_color'] = btn_color
    response['scatter_s_color'] = scatter_s_color
    response['scatter_s_color_status'] = scatter_s_color_status
    response['percentage'] = str(percentage)
    response['difference'] = str(difference)
    return response


def num_quantize(value, n_point=2):
    """
    :param value:
    :param n_point:
    :return:
    """
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        if value:
            d_places = Decimal(10) ** -n_point
            # Round to two places
            value = Decimal(value).quantize(d_places)
        return value


def init_singleton():
    # host = os.environ.get("STERLING_SQUARE_HOST")
    host = settings.APPLICATION_BASE_URL
    if not host:
        raise Exception("Host not provided")
    requests.get("{}/singleton".format(host))


def get_company_profile(symbol):
    """
    function to return the company profile.
    """
    if not symbol:
        raise ValueError("symbol is mandatory")

    api_key = settings.FINANCIAL_MODEL_GRP_API_KEY
    try:
        r = requests.get("https://financialmodelingprep.com/api/v3/profile/{}.NS?apikey={}".format(symbol, api_key))
        profile = r.json()
    except Exception as e:
        profile = [{}]

    market_cap = profile[0].get("mktCap")
    average_volume = profile[0].get("volAvg")
    currency = profile[0].get("currency")
    description = profile[0].get("description")
    industry = profile[0].get("industry")
    employees = profile[0].get("fullTimeEmployees")
    ceo = profile[0].get("ceo")
    city = profile[0].get("city")
    state = profile[0].get("state")
    country = profile[0].get("country")
    hq = city
    if state:
        hq += ", " + str(state).title()

    return {
        "market_cap": "{0:,.2f}".format(market_cap) if market_cap else u"\u2014",
        "average_volume": "{0:,.2f}".format(average_volume) if average_volume else u"\u2014",
        "currency": currency if currency else u"\u2014",
        "description": description if description else u"\u2014",
        "industry": industry if industry else u"\u2014",
        "employees": employees if employees else u"\u2014",
        "hq": hq if hq else u"\u2014",
        "founded": u"\u2014",
        "price_earning_ratio": u"\u2014",
        "dividend_yield": u"\u2014",
        "ceo": ceo if ceo else u"\u2014",
    }


def get_open_price(symbol, start, end, res, key):
    df = si.get_data(symbol, start_date=start, end_date=end)
    try:
        if df.empty:
            res[key] = 0.0
        else:
            df.dropna(inplace=True)
            res[key] = df[:1].to_dict("records")[0]['close']
    except:
        res[key] = 0.0


def get_previous_day_close_price(symbol, res, key):
    if key == "1d" and not is_market_opened_date():
        try:
            df = si.get_data(symbol).to_dict("records")[-2:]
            res[key] = df[0]['close']
        except Exception as eee:
            res[key] = 0.0
    else:
        start, end = get_day_range(get_previous_business_day())
        try:
            df = si.get_data(symbol, start_date=start, end_date=end)
            if df.empty:
                res[key] = 0.0
            else:
                df.dropna(inplace=True)
                res[key] = df[:1].to_dict("records")[0]['close']
        except Exception as eee:
            res[key] = 0.0


def get_all_open_prices(symbol):
    end, _ = get_day_range()

    start_1m = end - relativedelta(months=1)
    start_3m = end - relativedelta(months=3)
    start_6m = end - relativedelta(months=6)
    start_1y = end - relativedelta(years=1)
    start_5y = end - relativedelta(years=5)

    res = {}

    t_1d = Thread(
        target=get_previous_day_close_price, args=(symbol, res, "1d")
    )
    t_1m = Thread(
        target=get_open_price, args=(symbol, start_1m, end, res, "1m")
    )
    t_3m = Thread(
        target=get_open_price, args=(symbol, start_3m, end, res, "3m")
    )
    t_6m = Thread(
        target=get_open_price, args=(symbol, start_6m, end, res, "6m")
    )
    t_1y = Thread(
        target=get_open_price, args=(symbol, start_1y, end, res, "1y")
    )
    t_5y = Thread(
        target=get_open_price, args=(symbol, start_5y, end, res, "5y")
    )

    t_1d.start()
    t_1m.start()
    t_3m.start()
    t_6m.start()
    t_1y.start()
    t_5y.start()

    t_1d.join()
    t_1m.join()
    t_3m.join()
    t_6m.join()
    t_1y.join()
    t_5y.join()

    if '1m' not in res:
        get_open_price(symbol, start_1m, end, res, "1m")
    if '3m' not in res:
        get_open_price(symbol, start_1m, end, res, "3m")
    if '6m' not in res:
        get_open_price(symbol, start_1m, end, res, "6m")
    if '1y' not in res:
        get_open_price(symbol, start_1m, end, res, "1y")
    if '5y' not in res:
        get_open_price(symbol, start_1m, end, res, "5y")

    print(res)
    return res


def human_format(num):
    """
    Converts 1000 to 1K and 1,000,000 to 1.00M etc
    """
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'T'][magnitude])


def parse_tick_data(tick_data, token):
    """
    parse and return the live price
    """
    df = pd.DataFrame(tick_data)
    if not df.empty:
        df = df[df['instrument_token'] == token]
        if not df.empty:
            t = df.to_dict("records")
            return t[0]['last_price'], datetime.datetime.now()
        return None, None
    return None, None


def get_average_cost(user, symbol, price):
    """
    Calculate Avg cost of a symbol for a user
    """
    r = {}
    t = Thread(
        target=get_previous_day_close_price, args=(symbol+".NS", r, "cp")
    )
    t.start()

    positions = Position.objects.filter(userid=user).order_by("id")
    total_portfolio_units = positions.aggregate(units=Sum("size"))

    symbol_positions = positions.filter(stockname__symbol=symbol)

    total_amount, total_units, total_return = 0.0, 0.0, 0.0

    if total_portfolio_units:
        total_portfolio_units = total_portfolio_units.get("units", 0.0)
        if not total_portfolio_units:
            total_portfolio_units = 0.0
    else:
        total_portfolio_units = 0.0

    for position in symbol_positions:
        total_amount += (int(position.size) * float(position.transaction_details.price))
        total_units += int(position.size)

        if position.gl_history_position_rel.all():
            total_return += float(position.gl_history_position_rel.all()[0].unrealised_gainloss)

        # total_portfolio_units += position.size

    avg_cost = float(total_amount / total_units) if total_units else 0.0
    total_return_percent = float(total_return / total_amount) * 100 if total_amount else 0.0
    portfolio_diversity = float(total_units / total_portfolio_units) * 100.0 if total_portfolio_units else 0.0

    # Approach before Feb 8, 2021
    # today_return = (price - avg_cost)
    # today_return_percent = ((price - avg_cost) / avg_cost) * 100 if avg_cost else 0.0

    t.join()
    close_price = r.get('cp')
    today_return = (price - close_price)
    today_return_percent = (today_return / close_price) * 100.0 if close_price else 0.0
    today_return = today_return * total_units

    print(avg_cost, total_units, total_return, total_return_percent, today_return, \
           today_return_percent, portfolio_diversity)

    return avg_cost, total_units, total_return, total_return_percent, today_return, \
        today_return_percent, portfolio_diversity


def portfolio_open_value(user, interval="1D"):
    """
    function to return open value of the given user for a given interval.
    """
    try:
        end = datetime.datetime.now()
        if interval == "1D":
            if is_market_opened_date():
                # Is market opened today or going to open today
                if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
                    # is market opened now
                    start, end = get_day_range(get_previous_business_day())
                    values = PortfolioValues.objects.filter(
                        user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
                    ).order_by("timestamp")

                    live_values = PortfolioValues.objects.filter(
                        user=user, deletable=True
                    ).order_by("timestamp")
                else:
                    start, end = get_day_range(get_previous_business_day())
                    start_prev, end_prev = get_day_range(get_previous_business_day(get_previous_business_day()))

                    # live_values is the last entry of previous to previous day non-deletable field
                    values = PortfolioValues.objects.filter(
                        user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
                    ).order_by("timestamp")

                    # live_values is the last entry of previous day's non-deletable field
                    live_values = PortfolioValues.objects.filter(
                        user=user, timestamp__gte=start_prev, timestamp__lte=end_prev, deletable=False
                    ).order_by("timestamp")
            else:
                start, end = get_day_range(get_previous_business_day())
                start_prev, end_prev = get_day_range(get_previous_business_day(get_previous_business_day()))

                # live_values is the last entry of previous to previous day non-deletable field
                values = PortfolioValues.objects.filter(
                    user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
                ).order_by("timestamp")

                # live_values is the last entry of previous day's non-deletable field
                live_values = PortfolioValues.objects.filter(
                    user=user, timestamp__gte=start_prev, timestamp__lte=end_prev, deletable=False
                ).order_by("timestamp")
        elif interval == "1m":
            start = get_previous_business_day(end - relativedelta(months=1))
            start, end = get_day_range(start)
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")
        elif interval == "3m":
            start = get_previous_business_day(end - relativedelta(months=3))
            start, end = get_day_range(start)
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")
        elif interval == "6m":
            start = get_previous_business_day(end - relativedelta(months=6))
            start, end = get_day_range(start)
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")
        elif interval == "1y":
            start = get_previous_business_day(end - relativedelta(years=1))
            start, end = get_day_range(start)
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")
        elif interval == "5y":
            start = get_previous_business_day(end - relativedelta(years=5))
            start, end = get_day_range(start)
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")
        else:
            start, end = get_day_range(get_previous_business_day())
            values = PortfolioValues.objects.filter(
                user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
            ).order_by("timestamp")

            live_values = PortfolioValues.objects.filter(
                user=user, deletable=True
            ).order_by("timestamp")

        # if values.exists():
        #     last = values.last()
        #     latest_live = live_values.last()
        #     if latest_live:
        #         return last.portfolio_value, latest_live.portfolio_value
        #     return last.portfolio_value, 0.0
        # else:
        #     latest_live = live_values.last()
        #     if latest_live:
        #         return 0.0, latest_live.portfolio_value
        #     return 0.0, 0.0

        if values.exists():
            last = values.last()
            latest_live = live_values.last()
            if latest_live:
                return last.realized_gain_loss + last.unrealized_gain_loss, \
                       latest_live.realized_gain_loss + latest_live.unrealized_gain_loss
            return last.realized_gain_loss + last.unrealized_gain_loss, 0.0
        else:
            latest_live = live_values.last()
            if latest_live:
                return 0.0, latest_live.realized_gain_loss + latest_live.unrealized_gain_loss
            return 0.0, 0.0
    except Exception as e:
        return 0.0, 0.0


def portfolio_open_value_2(user, interval="1D"):
    try:
        end = datetime.datetime.now()
        if interval == "1D":
            if is_market_opened_date():
                # is market opened today or going to open today
                if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
                    # is market opened yet
                    start, end = get_day_range(get_previous_business_day())
                else:
                    # is the market is not opened yet, show previous day data
                    start, end = get_day_range(get_previous_business_day(get_previous_business_day()))
            else:
                start, end = get_day_range(get_previous_business_day(get_previous_business_day()))
        elif interval == "1m":
            start = get_previous_business_day(end - relativedelta(months=1))
            start, end = get_day_range(start)
        elif interval == "3m":
            start = get_previous_business_day(end - relativedelta(months=3))
            start, end = get_day_range(start)
        elif interval == "6m":
            start = get_previous_business_day(end - relativedelta(months=6))
            start, end = get_day_range(start)
        elif interval == "1y":
            start = get_previous_business_day(end - relativedelta(years=1))
            start, end = get_day_range(start)
        elif interval == "5y":
            start = get_previous_business_day(end - relativedelta(years=5))
            start, end = get_day_range(start)
        else:
            start, end = get_day_range(get_previous_business_day())

        values = PortfolioValues.objects.filter(
            user=user, timestamp__gte=start, timestamp__lte=end, deletable=False
        ).order_by("timestamp")

        live_values = PortfolioValues.objects.filter(
            user=user, deletable=True
        ).order_by("timestamp")

        if values.exists():
            last = values.last()
            latest_live = live_values.last()
            if latest_live:
                return last.portfolio_value, latest_live.portfolio_value
            return last.portfolio_value, 0.0
        else:
            latest_live = live_values.last()
            if latest_live:
                return 0.0, latest_live.portfolio_value
            return 0.0, 0.0
    except Exception as e:
        return 0.0, 0.0


# def portfolio_open_values(user):
#     """
#     Return all data that is returned by portfolio_open_value() for all the intervals at once. Optimised
#     from utils.util_functions import *
#     portfolio_open_values(1)
#     """
#     _, end = get_day_range(datetime.datetime.now())
#     # This requires a check for whether the market is opened or not
#     start_1d_prev, end_1d_prev = None, None
#     if is_market_opened_date():
#         # is market opened today or going to open today
#         if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
#             # is market opened yet
#             start_1d, end_1d = get_day_range(get_previous_business_day())
#         else:
#             # is the market is not opened yet, show previous day data
#             start_1d, end_1d = get_day_range(get_previous_business_day())
#             start_1d_prev, end_1d_prev = get_day_range(get_previous_business_day(get_previous_business_day()))
#     else:
#         start_1d, end_1d = get_day_range(get_previous_business_day())
#         start_1d_prev, end_1d_prev = get_day_range(get_previous_business_day(get_previous_business_day()))
#
#     start_1m, end_1m = get_day_range(get_previous_business_day(end - relativedelta(months=1)))
#     start_3m, end_3m = get_day_range(get_previous_business_day(end - relativedelta(months=3)))
#     start_6m, end_6m = get_day_range(get_previous_business_day(end - relativedelta(months=6)))
#     start_1y, end_1y = get_day_range(get_previous_business_day(end - relativedelta(years=1)))
#     start_5y, end_5y = get_day_range(get_previous_business_day(end - relativedelta(years=5)))
#
#     _, end = get_day_range(datetime.datetime.now())
#
#     df_5y = pd.DataFrame(
#         PortfolioValues.objects.filter(
#             user=user, timestamp__gte=make_aware(start_5y), timestamp__lte=make_aware(end)
#         ).order_by("timestamp").values()
#     )
#     if df_5y.empty:
#         return {
#             "1d": (0.0, 0.0), "1m": (0.0, 0.0),
#             "3m": (0.0, 0.0), "6m": (0.0, 0.0),
#             "1y": (0.0, 0.0), "5y": (0.0, 0.0)
#         }
#
#     df_5y.set_index(['timestamp'], inplace=True)
#
#     if is_market_opened_date():
#         if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
#             values = df_5y[
#                 (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
#                 (df_5y['deletable'] == False)
#             ]
#             live_values = df_5y[df_5y['deletable'] == True]
#         else:
#             values = df_5y[
#                 (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
#                 (df_5y['deletable'] == False)
#             ]
#             live_values = df_5y[
#                 (df_5y.index >= make_aware(start_1d_prev)) & (df_5y.index <= make_aware(end_1d_prev)) &
#                 (df_5y['deletable'] == False)
#             ]
#     else:
#         values = df_5y[
#             (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
#             (df_5y['deletable'] == False)
#         ]
#         live_values = df_5y[
#             (df_5y.index >= make_aware(start_1d_prev)) & (df_5y.index <= make_aware(end_1d_prev)) &
#             (df_5y['deletable'] == False)
#         ]
#
#     d1_value = 0.0
#     if not values.empty:
#         d1_value = values.iloc[-1]['realized_gain_loss'] + values.iloc[-1]['unrealized_gain_loss']
#
#     d1_live_value = 0.0
#     if not live_values.empty:
#         d1_live_value = live_values.iloc[-1]['realized_gain_loss'] + live_values.iloc[-1]['unrealized_gain_loss']
#
#     live_values = df_5y[df_5y['deletable'] == True]
#
#     latest = live_values.iloc[-1]
#     latest_live = latest['realized_gain_loss'] + latest['unrealized_gain_loss']
#
#     response = {
#         "1d": None, "1m": None,
#         "3m": None, "6m": None,
#         "1y": None, "5y": None
#     }
#
#     response['1d'] = (d1_value, d1_live_value)
#
#     df_5y_2 = df_5y[
#         (df_5y.index >= make_aware(start_5y)) & (df_5y.index <= make_aware(end_5y)) & (df_5y['deletable'] == False)
#     ]
#     if df_5y_2.empty:
#         response['5y'] = (0.0, latest_live)
#     else:
#         y5 = df_5y_2.iloc[-1]['realized_gain_loss'] + df_5y_2.iloc[-1]['unrealized_gain_loss']
#         response['5y'] = (y5, latest_live)
#
#     df_1y = df_5y[
#         (df_5y.index >= make_aware(start_1y)) & (df_5y.index <= make_aware(end_1y)) & (df_5y['deletable'] == False)
#     ]
#     if df_1y.empty:
#         response['1y'] = (0.0, latest_live)
#     else:
#         y1 = df_1y.iloc[-1]['realized_gain_loss'] + df_1y.iloc[-1]['unrealized_gain_loss']
#         response['1y'] = (y1, latest_live)
#
#     df_6m = df_1y[
#         (df_1y.index >= make_aware(start_6m)) & (df_1y.index <= make_aware(end_6m)) & (df_1y['deletable'] == False)
#     ]
#     if df_6m.empty:
#         response['6m'] = (0.0, latest_live)
#     else:
#         m6 = df_6m.iloc[-1]['realized_gain_loss'] + df_6m.iloc[-1]['unrealized_gain_loss']
#         response['6m'] = (m6, latest_live)
#
#     df_3m = df_6m[
#         (df_6m.index >= make_aware(start_3m)) & (df_6m.index <= make_aware(end_3m)) & (df_6m['deletable'] == False)
#     ]
#     if df_3m.empty:
#         response['3m'] = (0.0, latest_live)
#     else:
#         m3 = df_3m.iloc[-1]['realized_gain_loss'] + df_3m.iloc[-1]['unrealized_gain_loss']
#         response['3m'] = (m3, latest_live)
#
#     df_1m = df_3m[
#         (df_3m.index >= make_aware(start_1m)) & (df_3m.index <= make_aware(end_1m)) & (df_3m['deletable'] == False)
#     ]
#     if df_1m.empty:
#         response['1m'] = (0.0, latest_live)
#     else:
#         m1 = df_1m.iloc[-1]['realized_gain_loss'] + df_1m.iloc[-1]['unrealized_gain_loss']
#         response['1m'] = (m1, latest_live)
#
#     return response
#
#
# def portfolio_open_values_2(user):
#     """
#     Return all data that is returned by portfolio_open_value_2() for all the intervals at once. Optimised
#     from utils.util_functions import *
#     portfolio_open_values_2(1)
#     """
#     _, end = get_day_range(datetime.datetime.now())
#     # This requires a check for whether the market is opened or not
#     start_1d_prev, end_1d_prev = None, None
#     if is_market_opened_date():
#         # is market opened today or going to open today
#         if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
#             # is market opened yet
#             start_1d, end_1d = get_day_range(get_previous_business_day())
#         else:
#             # is the market is not opened yet, show previous day data
#             start_1d, end_1d = get_day_range(get_previous_business_day(get_previous_business_day()))
#     else:
#         start_1d, end_1d = get_day_range(get_previous_business_day(get_previous_business_day()))
#
#     start_1m, end_1m = get_day_range(get_previous_business_day(end - relativedelta(months=1)))
#     start_3m, end_3m = get_day_range(get_previous_business_day(end - relativedelta(months=3)))
#     start_6m, end_6m = get_day_range(get_previous_business_day(end - relativedelta(months=6)))
#     start_1y, end_1y = get_day_range(get_previous_business_day(end - relativedelta(years=1)))
#     start_5y, end_5y = get_day_range(get_previous_business_day(end - relativedelta(years=5)))
#
#     _, end = get_day_range(datetime.datetime.now())
#
#     all = PortfolioValues.objects.filter(
#         user=user, timestamp__gte=make_aware(start_5y),
#         timestamp__lte=make_aware(end),
#     ).order_by("timestamp")
#
#     df_5y = pd.DataFrame(all.values())
#     if df_5y.empty:
#         return {
#             "1d": (0.0, 0.0), "1m": (0.0, 0.0),
#             "3m": (0.0, 0.0), "6m": (0.0, 0.0),
#             "1y": (0.0, 0.0), "5y": (0.0, 0.0),
#         }
#
#     df_5y.sort_values('timestamp', inplace=True)
#     df_5y.set_index(['timestamp'], inplace=True)
#
#     # Calculating the live value ...
#     live_values = df_5y[df_5y['deletable'] == True]
#     live_value = 0
#     if not live_values.empty:
#         live_value = live_values.iloc[-1]['portfolio_value']
#
#     # Calculating the interval wise.
#     value_5y = 0.0
#     if not df_5y.empty:
#         df_5y_2 = df_5y[
#             (df_5y.index >= make_aware(start_5y)) & (df_5y.index <= make_aware(end_5y)) & (df_5y['deletable'] == False)
#         ]
#         if not df_5y_2.empty:
#             value_5y = df_5y_2.iloc[-1]['portfolio_value']
#
#     df_1y = df_5y[
#         (df_5y.index >= make_aware(start_1y)) & (df_5y.index <= make_aware(end_1y)) & (df_5y['deletable'] == False)
#     ]
#     value_1y = 0.0
#     if not df_1y.empty:
#         value_1y = df_1y.iloc[-1]['portfolio_value']
#
#     df_6m = df_1y[
#         (df_1y.index >= make_aware(start_6m)) & (df_1y.index <= make_aware(end_6m)) & (df_1y['deletable'] == False)
#     ]
#     value_6m = 0.0
#     if not df_6m.empty:
#         value_6m = df_6m.iloc[-1]['portfolio_value']
#
#     df_3m = df_6m[
#         (df_6m.index >= make_aware(start_3m)) & (df_6m.index <= make_aware(end_3m)) & (df_6m['deletable'] == False)
#     ]
#     value_3m = 0.0
#     if not df_3m.empty:
#         value_3m = df_3m.iloc[-1]['portfolio_value']
#
#     df_1m = df_3m[
#         (df_3m.index >= make_aware(start_1m)) & (df_3m.index <= make_aware(end_1m)) & (df_3m['deletable'] == False)
#     ]
#     value_1m = 0.0
#     if not df_1m.empty:
#         value_1m = df_1m.iloc[-1]['portfolio_value']
#
#     df_1d = df_1m[
#         (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) & (df_5y['deletable'] == False)
#     ]
#     value_1d = 0.0
#     if not df_1d.empty:
#         value_1d = df_1d.iloc[-1]['portfolio_value']
#
#     return {
#         "1d": (value_1d, live_value), "1m": (value_1m, live_value),
#         "3m": (value_3m, live_value), "6m": (value_6m, live_value),
#         "1y": (value_1y, live_value), "5y": (value_5y, live_value),
#     }


def portfolio_open_values(df_5y):
    """
    Return all data that is returned by portfolio_open_value() for all the intervals at once. Optimised
    from utils.util_functions import *
    portfolio_open_values(1)
    """
    if df_5y.empty:
        return {
            "1d": (0.0, 0.0), "1m": (0.0, 0.0),
            "3m": (0.0, 0.0), "6m": (0.0, 0.0),
            "1y": (0.0, 0.0), "5y": (0.0, 0.0)
        }
    df_5y.set_index(['timestamp'], inplace=True)

    _, end = get_day_range(datetime.datetime.now())
    # This requires a check for whether the market is opened or not
    start_1d_prev, end_1d_prev = None, None
    if is_market_opened_date():
        # is market opened today or going to open today
        if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
            # is market opened yet
            start_1d, end_1d = get_day_range(get_previous_business_day())
        else:
            # is the market is not opened yet, show previous day data
            start_1d, end_1d = get_day_range(get_previous_business_day())
            start_1d_prev, end_1d_prev = get_day_range(get_previous_business_day(get_previous_business_day()))
    else:
        start_1d, end_1d = get_day_range(get_previous_business_day())
        start_1d_prev, end_1d_prev = get_day_range(get_previous_business_day(get_previous_business_day()))

    start_1m, end_1m = get_day_range(get_previous_business_day(end - relativedelta(months=1)))
    start_3m, end_3m = get_day_range(get_previous_business_day(end - relativedelta(months=3)))
    start_6m, end_6m = get_day_range(get_previous_business_day(end - relativedelta(months=6)))
    start_1y, end_1y = get_day_range(get_previous_business_day(end - relativedelta(years=1)))
    start_5y, end_5y = get_day_range(get_previous_business_day(end - relativedelta(years=5)))

    _, end = get_day_range(datetime.datetime.now())

    if is_market_opened_date():
        if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
            values = df_5y[
                (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
                (df_5y['deletable'] == False)
            ]
            live_values = df_5y[df_5y['deletable'] == True]
        else:
            values = df_5y[
                (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
                (df_5y['deletable'] == False)
            ]
            live_values = df_5y[
                (df_5y.index >= make_aware(start_1d_prev)) & (df_5y.index <= make_aware(end_1d_prev)) &
                (df_5y['deletable'] == False)
            ]
    else:
        values = df_5y[
            (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) &
            (df_5y['deletable'] == False)
        ]
        live_values = df_5y[
            (df_5y.index >= make_aware(start_1d_prev)) & (df_5y.index <= make_aware(end_1d_prev)) &
            (df_5y['deletable'] == False)
        ]

    d1_value = 0.0
    if not values.empty:
        d1_value = values.iloc[-1]['realized_gain_loss'] + values.iloc[-1]['unrealized_gain_loss']

    d1_live_value = 0.0
    if not live_values.empty:
        d1_live_value = live_values.iloc[-1]['realized_gain_loss'] + live_values.iloc[-1]['unrealized_gain_loss']

    live_values = df_5y[df_5y['deletable'] == True]

    latest = live_values.iloc[-1]
    latest_live = latest['realized_gain_loss'] + latest['unrealized_gain_loss']

    response = {
        "1d": None, "1m": None,
        "3m": None, "6m": None,
        "1y": None, "5y": None
    }

    response['1d'] = (d1_value, d1_live_value)

    df_5y_2 = df_5y[
        (df_5y.index >= make_aware(start_5y)) & (df_5y.index <= make_aware(end_5y)) & (df_5y['deletable'] == False)
    ]
    if df_5y_2.empty:
        response['5y'] = (0.0, latest_live)
    else:
        y5 = df_5y_2.iloc[-1]['realized_gain_loss'] + df_5y_2.iloc[-1]['unrealized_gain_loss']
        response['5y'] = (y5, latest_live)

    df_1y = df_5y[
        (df_5y.index >= make_aware(start_1y)) & (df_5y.index <= make_aware(end_1y)) & (df_5y['deletable'] == False)
    ]
    if df_1y.empty:
        response['1y'] = (0.0, latest_live)
    else:
        y1 = df_1y.iloc[-1]['realized_gain_loss'] + df_1y.iloc[-1]['unrealized_gain_loss']
        response['1y'] = (y1, latest_live)

    df_6m = df_1y[
        (df_1y.index >= make_aware(start_6m)) & (df_1y.index <= make_aware(end_6m)) & (df_1y['deletable'] == False)
    ]
    if df_6m.empty:
        response['6m'] = (0.0, latest_live)
    else:
        m6 = df_6m.iloc[-1]['realized_gain_loss'] + df_6m.iloc[-1]['unrealized_gain_loss']
        response['6m'] = (m6, latest_live)

    df_3m = df_6m[
        (df_6m.index >= make_aware(start_3m)) & (df_6m.index <= make_aware(end_3m)) & (df_6m['deletable'] == False)
    ]
    if df_3m.empty:
        response['3m'] = (0.0, latest_live)
    else:
        m3 = df_3m.iloc[-1]['realized_gain_loss'] + df_3m.iloc[-1]['unrealized_gain_loss']
        response['3m'] = (m3, latest_live)

    df_1m = df_3m[
        (df_3m.index >= make_aware(start_1m)) & (df_3m.index <= make_aware(end_1m)) & (df_3m['deletable'] == False)
    ]
    if df_1m.empty:
        response['1m'] = (0.0, latest_live)
    else:
        m1 = df_1m.iloc[-1]['realized_gain_loss'] + df_1m.iloc[-1]['unrealized_gain_loss']
        response['1m'] = (m1, latest_live)

    return response


def portfolio_open_values_2(df_5y):
    """
    Return all data that is returned by portfolio_open_value_2() for all the intervals at once. Optimised
    from utils.util_functions import *
    portfolio_open_values_2(1)
    """
    if df_5y.empty:
        return {
            "1d": (0.0, 0.0), "1m": (0.0, 0.0),
            "3m": (0.0, 0.0), "6m": (0.0, 0.0),
            "1y": (0.0, 0.0), "5y": (0.0, 0.0),
        }

    df_5y.sort_values('timestamp', inplace=True)
    df_5y.set_index(['timestamp'], inplace=True)

    _, end = get_day_range(datetime.datetime.now())
    # This requires a check for whether the market is opened or not
    start_1d_prev, end_1d_prev = None, None
    if is_market_opened_date():
        # is market opened today or going to open today
        if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
            # is market opened yet
            start_1d, end_1d = get_day_range(get_previous_business_day())
        else:
            # is the market is not opened yet, show previous day data
            start_1d, end_1d = get_day_range(get_previous_business_day(get_previous_business_day()))
    else:
        start_1d, end_1d = get_day_range(get_previous_business_day(get_previous_business_day()))

    start_1m, end_1m = get_day_range(get_previous_business_day(end - relativedelta(months=1)))
    start_3m, end_3m = get_day_range(get_previous_business_day(end - relativedelta(months=3)))
    start_6m, end_6m = get_day_range(get_previous_business_day(end - relativedelta(months=6)))
    start_1y, end_1y = get_day_range(get_previous_business_day(end - relativedelta(years=1)))
    start_5y, end_5y = get_day_range(get_previous_business_day(end - relativedelta(years=5)))

    _, end = get_day_range(datetime.datetime.now())

    # Calculating the live value ...
    live_values = df_5y[df_5y['deletable'] == True]
    live_value = 0
    if not live_values.empty:
        live_value = live_values.iloc[-1]['portfolio_value']

    # Calculating the interval wise.
    value_5y = 0.0
    if not df_5y.empty:
        df_5y_2 = df_5y[
            (df_5y.index >= make_aware(start_5y)) & (df_5y.index <= make_aware(end_5y)) & (df_5y['deletable'] == False)
        ]
        if not df_5y_2.empty:
            value_5y = df_5y_2.iloc[-1]['portfolio_value']

    df_1y = df_5y[
        (df_5y.index >= make_aware(start_1y)) & (df_5y.index <= make_aware(end_1y)) & (df_5y['deletable'] == False)
    ]
    value_1y = 0.0
    if not df_1y.empty:
        value_1y = df_1y.iloc[-1]['portfolio_value']

    df_6m = df_1y[
        (df_1y.index >= make_aware(start_6m)) & (df_1y.index <= make_aware(end_6m)) & (df_1y['deletable'] == False)
    ]
    value_6m = 0.0
    if not df_6m.empty:
        value_6m = df_6m.iloc[-1]['portfolio_value']

    df_3m = df_6m[
        (df_6m.index >= make_aware(start_3m)) & (df_6m.index <= make_aware(end_3m)) & (df_6m['deletable'] == False)
    ]
    value_3m = 0.0
    if not df_3m.empty:
        value_3m = df_3m.iloc[-1]['portfolio_value']

    df_1m = df_3m[
        (df_3m.index >= make_aware(start_1m)) & (df_3m.index <= make_aware(end_1m)) & (df_3m['deletable'] == False)
    ]
    value_1m = 0.0
    if not df_1m.empty:
        value_1m = df_1m.iloc[-1]['portfolio_value']

    df_1d = df_1m[
        (df_5y.index >= make_aware(start_1d)) & (df_5y.index <= make_aware(end_1d)) & (df_5y['deletable'] == False)
    ]
    value_1d = 0.0
    if not df_1d.empty:
        value_1d = df_1d.iloc[-1]['portfolio_value']

    return {
        "1d": (value_1d, live_value), "1m": (value_1m, live_value),
        "3m": (value_3m, live_value), "6m": (value_6m, live_value),
        "1y": (value_1y, live_value), "5y": (value_5y, live_value),
    }


def get_last_price(symbol):
    """
    get last price of the symbol from yahoo finance.
    """
    if not symbol:
        return None

    last_price = cache.get(f"{symbol}_prev_price")
    last_price_exp = cache.get(f"{symbol}_prev_price_expiry")

    if last_price and datetime.datetime.now() < last_price_exp:
        return last_price

    try:
        market_opened = is_market_opened_date()
        if market_opened:
            start = get_previous_business_day()
        else:
            start = get_previous_business_day(get_previous_business_day())

        last = si.get_data(symbol+".NS", start_date=start, end_date=start)
        if last.empty:
            return None
        last = last.iloc[-1]['close']
        cache.set(f"{symbol}_prev_price", last)
        cache.set(
            f"{symbol}_prev_price_expiry", get_day_range(datetime.datetime.now() + datetime.timedelta(days=1))[0]
        )
        return last
    except:
        return None


def get_most_active():
    """
    Uses the NSE approach
    """
    try:
        # choosing random proxy from a list of proxies.
        # index = random.randint(0, len(settings.PROXIES) - 1)
        # proxy = settings.PROXIES[index]
        # print(proxy)
        # most_active = cache.get("most_active")
        # most_active_expiry = cache.get("most_active_expiry")
        # r = requests.get(
        #     "https://www1.nseindia.com/live_market/dynaContent/live_analysis/most_active/allTopValue1.json",
        #     headers={
        #         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
        #                       " Chrome/88.0.4324.182 Safari/537.36"
        #     },
        #     proxies=proxy
        # )
        # most_active = r.json().get("data", [])
        return []
    except Exception as e:
        return []


def get_last_price_from_file(symbol, date=None):
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    else:
        date = date.strftime("%Y-%m-%d")

    root = settings.MEDIA_ROOT
    dir = os.path.join(root, "symbol_data")
    full_dir = os.path.join(dir, symbol)
    if not os.path.exists(dir):
        return None
    if not os.path.exists(full_dir):
        return None
    full_path = os.path.join(full_dir, "{}_{}.csv".format(symbol, date))
    if not os.path.isfile(full_path):
        return None

    # reading just the last row
    df = pd.read_csv(full_path).tail(1)
    if df.empty:
        return None
    if "price" not in df.columns:
        return None
    return df.iloc[-1]['price']
