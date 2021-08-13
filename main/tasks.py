import time
import datetime
import pickle
import bs4
import threading
import copy
from django.core.cache import cache
from yahoo_fin import stock_info as si
from sterling_square import celery_app

from accounts.views import update_position_and_gainloss

from accounts.models import *
from utils.util_functions import *
from sterling_square.TickerSingleton import SingletonCelery, SingletonPortfolio, SingletonStockPrices


@celery_app.task()
def initialize_celery_singleton():
    SingletonCelery.get_instance("update")


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


@celery_app.task()
def save_stock_information():
    print("SingletonStockPrices init .... ")
    s = SingletonStockPrices.get_instance("")
    if not s.thread.is_alive():
        print("SingletonStockPrices refresh init ... ")
        s.refresh_credentials()


@celery_app.task()
def get_holidays():
    year = datetime.datetime.now().year
    print("Fetching holidays for the Year: {}".format(year))

    BASE_URL = "https://zerodha.com/z-connect/traders-zone/holidays/"
    ROUTE = "trading-holidays-{}-nse-bse-mcx"

    url = BASE_URL + ROUTE.format(year)

    r = requests.get(url)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text, 'lxml')

        tables = soup.findAll("table")
        df = None
        for table in tables:
            df = pd.read_html(str(table))[0]
            break

        if df is not None and not df.empty:
            print("Holidays ... ")
            print(df)
            holidays = df.to_dict("records")

            new = 0
            for holiday in holidays:
                name = holiday.get("Holidays")
                date = datetime.datetime.strptime(holiday.get("Date"), "%B %d, %Y")

                exists = Holidays.objects.filter(date=date).exists()
                if not exists:
                    h = Holidays(holiday=name, date=date)
                    h.save()
                    new += 1
            print("New Records ... {}".format(new))


@celery_app.task()
def save_market_opened_object():
    start, _ = get_day_range()
    is_holiday = Holidays.objects.filter(date=start).exists()

    target = {
        "is_market_opened_date": is_weekday(start) and not is_holiday
    }

    root = settings.MEDIA_ROOT
    file_name = "market_opened_today.pickle"
    full_path = os.path.join(root, file_name)

    if os.path.exists(full_path):
        os.remove(full_path)

    with open(full_path, "wb") as fi:
        pickle.dump(target, fi)

# BEFORE March 24, 2021
# def get_financial_model_group_data_and_store(stock: StockGeneralInfo, new: bool, api_key: str):
#     """
#     :param stock: StockGeneralInfo Object
#     :param new: new=True represents a new record
#     :param api_key:
#     """
#     print(f"Symbol: {stock.symbol}")
#     r = {}
#     t1 = Thread(
#         target=get_profile, args=(stock.symbol, api_key, r)
#     )
#     t2 = Thread(
#         target=get_ratios, args=(stock.symbol, api_key, r)
#     )
#     t3 = Thread(
#         target=get_quotes, args=(stock.symbol, api_key, r)
#     )
#     t1.start()
#     t2.start()
#     t3.start()
#
#     t1.join()
#     t2.join()
#     t3.join()
#
#     profile = r['profile']
#     ratios = r['ratio']
#     quote = r['quote']
#
#     err = len(profile) == 0 or len(ratios) == 0 or len(quote) == 0
#
#     market_cap = profile.get("mktCap")
#     average_volume = profile.get("volAvg")
#     currency = profile.get("currency")
#     description = profile.get("description")
#     if description and "founded in " in description:
#         founded = int(description.split("founded in ")[-1][:4])
#     else:
#         founded = None
#
#     industry = profile.get("industry")
#     sector = profile.get("sector")
#     address = profile.get("address")
#     ipo_date = profile.get("ipoDate")
#     if ipo_date:
#         ipo_date = datetime.datetime.strptime(ipo_date, "%Y-%m-%d")
#         ipo_date = make_aware(datetime.datetime(ipo_date.year, ipo_date.month, ipo_date.day))
#     employees = profile.get("fullTimeEmployees")
#     ceo = profile.get("ceo")
#     city = profile.get("city")
#     state = profile.get("state")
#     country = profile.get("country")
#
#     # RATIO fields
#     price_earning_ratio = ratios.get("priceEarningsRatio")
#     dividend_yield = ratios.get("dividendYield")
#
#     # QUOTE fields
#     high_today = quote.get("dayHigh")
#     low_today = quote.get("dayLow")
#     open_price = quote.get("open")
#     volume = quote.get("volume")
#     yearly_high = quote.get("yearHigh")
#     yearly_low = quote.get("yearLow")
#
#     if not employees:
#         employees = None
#
#     # if error occurred while collecting the data, do not update the exisitng data at all.
#     if not err:
#         stock.market_cap = market_cap
#         stock.average_volume = average_volume
#         stock.currency = currency
#         stock.founded = founded
#         stock.industry = industry
#         stock.sector = sector
#         stock.address = address
#         stock.description = description
#         stock.ipo_date = ipo_date
#         stock.employees = employees
#         stock.ceo = ceo
#         stock.city = city
#         stock.state = state
#         stock.country = country
#
#         stock.price_earning_ratio = price_earning_ratio
#         stock.dividend_yield = dividend_yield
#
#         stock.high_today = high_today
#         stock.low_today = low_today
#         stock.open_price = open_price
#         stock.volume = volume
#         stock.yearly_high = yearly_high
#         stock.yearly_low = yearly_low
#
#         if new:
#             stock.created = make_aware(datetime.datetime.now())
#             # created += 1
#         else:
#             pass
#             # updated += 1
#         stock.updated = make_aware(datetime.datetime.now())
#         stock.save()
#     else:
#         # Set updated to None, to get the data in the next cycle.
#         stock.updated = None
#         stock.save()


def get_financial_model_group_data_and_store(stock: StockGeneralInfo, new: bool, api_key: str):
    """
    :param stock: StockGeneralInfo Object
    :param new: new=True represents a new record
    :param api_key:
    """
    r = {}

    # has_profile = True if object has description text else False
    has_profile = True
    if not stock.description or not stock.updated \
            or (make_aware(datetime.datetime.now()) - stock.updated).total_seconds() >= 30 * 24 * 3600:
        has_profile = False

    print(
        f"Symbol: {stock.symbol} description_is_None: {stock.description is None} last_updated: {stock.updated} "
        f"has_profile: {has_profile}"
    )

    t1 = None
    if not has_profile:
        t1 = Thread(
            target=get_profile, args=(stock.symbol, api_key, r)
        )
    t2 = Thread(
        target=get_ratios, args=(stock.symbol, api_key, r)
    )
    t3 = Thread(
        target=get_quotes, args=(stock.symbol, api_key, r)
    )

    if not has_profile:
        t1.start()
    t2.start()
    t3.start()

    if not has_profile:
        t1.join()
    t2.join()
    t3.join()

    profile = r.get('profile', {})
    ratios = r.get('ratio', {})
    quote = r.get('quote', {})

    if has_profile:
        err = len(ratios) == 0 or len(quote) == 0
    else:
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
    else:
        ipo_date = None
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
    if not has_profile:
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
        stock.updated = make_aware(datetime.datetime.now())
        stock.save()

    if ratios:
        stock.price_earning_ratio = price_earning_ratio
        stock.dividend_yield = dividend_yield

    if quote:
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
    # stock.updated = make_aware(datetime.datetime.now())
    stock.save()


@celery_app.task()
def update_stock_market_details_3():
    try:
        print("update_stock_market_details_2")
        names = StockNames.objects.filter().order_by("id")
        api_key = settings.FINANCIAL_MODEL_GRP_API_KEY

        for name in names:
            stock = StockGeneralInfo.objects.filter(symbol__iexact=name.symbol).order_by("id")
            new, exists = False, True
            if stock.exists():
                stock = stock.first()
            else:
                new = True
                exists = False
                stock = StockGeneralInfo(symbol=name.symbol)
                stock.save()

            get_financial_model_group_data_and_store(stock, new, api_key)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print("Exception ", e)
        # if exists:
        #     if not stock.updated:
        #         # if the object exists but it was never updated, update it now.
        #         get_financial_model_group_data_and_store(stock, new, api_key)
        #     else:
        #         interval = 30 * 24 * 3600   # 30 days
        #         if (make_aware(datetime.datetime.now()) - stock.updated).total_seconds() >= interval:
        #             # if a symbol was last updated at least more than 30 days ago, update it now.
        #             get_financial_model_group_data_and_store(stock, new, api_key)
        #         else:
        #             # Do nothing if the info was last updated something between a month.
        #             pass
        # else:
        #     # if the object doesn't already exist, create one and save the fetched data.
        #     get_financial_model_group_data_and_store(stock, new, api_key)


@celery_app.task()
def update_transaction_table_2():
    print("update_transaction_table_2 - Start")
    # threading.Thread(
    #     target=SingletonCelery.get_instance, args=("update",)
    # ).start()
    # time.sleep(2)
    # stocks = StockNames.objects.all().order_by("id")

    current_date = datetime.datetime.now()
    current_time = current_date.time()

    flag = 0
    # change 18 to 15. 18 is used for testing purpose only, 15 should be the actual value.
    if 9 <= int(current_time.hour) < 15:
        flag = 1
    elif int(current_time.hour) == 15:
        if int(current_time.minute) <= 30:
            flag = 1

    print("update_transaction_table_2 - FLAG : {}".format(flag))
    if flag == 1:
        try:
            all_transactions = Transaction.objects.filter(status="pending")
            print("update_transaction_table_2 - Pending Transactions : {}".format(all_transactions.count()))

            if all_transactions.count() > 0:
                ticker = SingletonCelery.get_instance("update")
                index = 1
                for transaction in all_transactions:
                    stock = StockNames.objects.get(symbol__iexact=transaction.stockticker.symbol)
                    price, tx = parse_tick_data(ticker.tick_data, int(stock.token))

                    def limit_order_purchase(transaction_obj, live_price):
                        user = UserDetails.objects.get(user=transaction_obj.userid)
                        user_buying_power = float(user.identity.buyingpower)

                        identity = IdentityDetails.objects.get(id=user.identity.id)

                        # live_price = si.get_live_price(
                        #     transaction_obj.stockticker.symbol + ".NS"
                        # )
                        print("live_price ", num_quantize(float(live_price)))
                        status_flag = 0
                        if transaction_obj.ordertype == "market_order":
                            status_flag = 1
                        elif transaction_obj.ordertype == "limit_order" and \
                                num_quantize(
                                    float(live_price)) <= num_quantize(
                            float(transaction_obj.price)):
                            status_flag = 1

                        if status_flag == 1:
                            transaction_obj.status = "executed"
                            transaction_obj.save()
                            position_obj, status = Position.objects.get_or_create(
                                userid=transaction_obj.userid,
                                stockname=transaction_obj.stockticker,
                                ticker=transaction_obj.stockticker.symbol,
                                price=live_price,
                                ordertype=transaction_obj.ordertype)
                            position_obj.transaction_details = transaction_obj
                            position_obj.save()
                            try:
                                history_obj = \
                                    TransactionHistory.objects.get_or_create(
                                        position_obj=position_obj,
                                        stock_number=transaction_obj.size)
                            except:
                                pass
                            try:
                                total_cash = float(live_price) * int(
                                    transaction_obj.size)
                                gl_history = GainLossHistory.objects.create(
                                    userid=transaction_obj.userid,
                                    stock=transaction_obj.stock,
                                    total_cash=total_cash
                                )
                                gl_history.unrealised_gainloss = num_quantize(
                                    (float(live_price) - float(position_obj.transaction_details.price)) *
                                    int(transaction_obj.size)
                                )
                                gl_history.position_obj = position_obj
                                gl_history.save()
                                user_buying_power -= total_cash
                                identity.buyingpower = user_buying_power
                                identity.save()
                            except:
                                pass
                        else:
                            if transaction_obj.remove_date and \
                                    transaction_obj.expires == "Good till " \
                                                               "canceled":
                                if current_date.date() == \
                                        transaction_obj.remove_date.date():
                                    transaction_obj.delete()
                        print("Status====", transaction_obj.status)

                    def limit_order_purchase_2(transaction_obj, live_price):
                        user = UserDetails.objects.get(user=transaction_obj.userid)
                        user_buying_power = float(user.identity.buyingpower)

                        identity = IdentityDetails.objects.get(id=user.identity.id)

                        # live_price = si.get_live_price(
                        #     transaction_obj.stockticker.symbol + ".NS"
                        # )
                        print("live_price ", num_quantize(float(live_price)))
                        status_flag = 0
                        if transaction_obj.ordertype == "market_order":
                            status_flag = 1
                        elif transaction_obj.ordertype == "limit_order" and \
                                num_quantize(
                                    float(live_price)) <= num_quantize(
                            float(transaction_obj.limit_price)):
                            status_flag = 1

                        print("limit_order_purchase_flag {}".format(status_flag))

                        if status_flag == 1:
                            transaction_obj.status = "executed"
                            transaction_obj.save()

                            position_obj = Position(
                                userid=transaction_obj.userid,
                                stockname=transaction_obj.stockticker,
                                ticker=transaction_obj.stockticker.symbol,
                                price=live_price,
                                ordertype=transaction_obj.ordertype
                            )
                            # position_obj, status = Position.objects.get_or_create(
                            #     userid=transaction_obj.userid,
                            #     stockname=transaction_obj.stockticker,
                            #     ticker=transaction_obj.stockticker.symbol,
                            #     price=live_price,
                            #     ordertype=transaction_obj.ordertype)
                            position_obj.transaction_details = transaction_obj
                            position_obj.size = transaction_obj.size
                            position_obj.save()
                            try:
                                history_obj = \
                                    TransactionHistory.objects.get_or_create(
                                        position_obj=position_obj,
                                        stock_number=transaction_obj.size)
                            except:
                                pass
                            try:
                                total_cash = float(live_price) * int(
                                    transaction_obj.size)
                                gl_history = GainLossHistory.objects.create(
                                    userid=transaction_obj.userid,
                                    stock=transaction_obj.stock,
                                    total_cash=total_cash
                                )
                                gl_history.unrealised_gainloss = num_quantize(
                                    (float(live_price) - float(position_obj.transaction_details.price)) *
                                    int(transaction_obj.size)
                                )
                                gl_history.position_obj = position_obj
                                gl_history.save()
                                user_buying_power -= total_cash
                                identity.buyingpower = user_buying_power
                                identity.save()
                            except:
                                pass
                        else:
                            if transaction_obj.remove_date and \
                                    transaction_obj.expires == "Good till " \
                                                               "canceled":
                                if current_date.date() == \
                                        transaction_obj.remove_date.date():
                                    transaction_obj.delete()
                        print("Status====", transaction_obj.status)

                    def limit_order_sell(transaction_obj, current_price):
                        """Limit Order Sell"""
                        now = datetime.datetime.now()
                        status_flag = 0
                        if transaction_obj.ordertype == "market_order":
                            status_flag = 0
                        elif transaction_obj.ordertype == "limit_order" and \
                                num_quantize(float(current_price)) >= \
                                    num_quantize(float(transaction_obj.limit_price)):
                            # if limit order and current price >= limit price
                            status_flag = 0
                            # check for market is opened or not
                            if 9 <= int(now.hour) < 15:
                                status_flag = 1
                            elif int(now.hour) == 15:
                                if int(now.minute) <= 30:
                                    status_flag = 1
                            # print("limit order can be executed ... {} {}".format(float(current_price),
                            #                                                      float(transaction_obj.price)))

                        # print("current price : {}".format(current_price))
                        # print("limit price : {}".format(transaction_obj.price))
                        # print("sell execution status_flag:  {}".format(status_flag))
                        # If all the conditions are true, status flag = 1
                        if status_flag == 1:
                            # execute the current transaction object
                            transaction_obj.status = "executed"
                            transaction_obj.save()

                            symbol = transaction_obj.stockticker.symbol
                            share_num = transaction_obj.size
                            user = transaction_obj.userid
                            user_obj = UserDetails.objects.get(user=user)
                            identity_obj = IdentityDetails.objects.get(id=user_obj.identity.id)
                            buying_power = float(identity_obj.buyingpower)

                            # Old Approach - First in Last Out
                            # positions = Position.objects.filter(userid=user, ticker=symbol).order_by("id")
                            # New Approach - Last in First Out
                            positions = Position.objects.filter(userid=user, ticker=symbol).order_by("-id")

                            for pos_obj in positions:
                                print("position id : {}".format(pos_obj.id))
                                print("existing stock num in this position (stock_num) : {}".format(
                                    pos_obj.transaction_details.size
                                ))
                                print("shares on sale (share_num) : {}".format(
                                    share_num
                                ))
                                stock_num = int(pos_obj.size)

                                if stock_num == share_num:
                                    stock_num -= share_num
                                    # pos_obj.transaction_details.size = stock_num
                                    pos_obj.size = int(stock_num)
                                    pos_obj.save()
                                    pos_obj.transaction_details.save()
                                    try:
                                        history_obj = \
                                            TransactionHistory.objects.get_or_create(
                                                position_obj=pos_obj,
                                                stock_number=share_num,
                                                status="sell")
                                    except:
                                        pass
                                    try:
                                        realised_gainloss = (float(current_price) - float(
                                            pos_obj.transaction_details.price)) * int(
                                            share_num)
                                        gl_obj = GainLossHistory.objects.get(
                                            position_obj=pos_obj)
                                        gl_obj.realised_gainloss += num_quantize(
                                            realised_gainloss)
                                        # Incorrect Approach
                                        # buying_power += realised_gainloss
                                        # Correct Approach
                                        buying_power += (share_num * current_price)
                                        print(
                                            ",,,,,,,,,,,,,,,,1111111111       buyingpower",
                                            buying_power,
                                            num_quantize(realised_gainloss))
                                        gl_obj.save()

                                    except:
                                        pass
                                elif stock_num > share_num:
                                    # share_num = stock_num - share_num
                                    stock_num -= share_num
                                    # pos_obj.transaction_details.size = stock_num
                                    pos_obj.size = int(stock_num)
                                    pos_obj.save()
                                    pos_obj.transaction_details.save()
                                    try:
                                        history_obj = \
                                            TransactionHistory.objects.get_or_create(
                                                position_obj=pos_obj,
                                                stock_number=share_num,
                                                status="sell")
                                    except:
                                        pass
                                    try:
                                        realised_gainloss = (float(current_price) - float(
                                            pos_obj.transaction_details.price)) * int(
                                            share_num)
                                        gl_obj = GainLossHistory.objects.get(
                                            position_obj=pos_obj)
                                        gl_obj.realised_gainloss += num_quantize(
                                            realised_gainloss)
                                        # Incorrect Approach
                                        # buying_power += realised_gainloss
                                        # Correct Approach
                                        buying_power += (share_num * current_price)
                                        print(
                                            ",,,,,,,,,,,,,,,,2222222222222    buyingpower",
                                            buying_power,
                                            num_quantize(realised_gainloss))
                                        gl_obj.save()
                                    except Exception as e:
                                        print("ERRORRRR  SELL STOCK  ", e)
                                        pass
                                    break
                                else:
                                    share_num = share_num - stock_num
                                    # pos_obj.transaction_details.size = 0
                                    pos_obj.size = 0
                                    pos_obj.save()
                                    pos_obj.transaction_details.save()
                                    try:
                                        history_obj = \
                                            TransactionHistory.objects.get_or_create(
                                                position_obj=pos_obj,
                                                stock_number=stock_num,
                                                status="sell")
                                    except:
                                        pass
                                    try:
                                        realised_gainloss = (float(current_price) - float(
                                            pos_obj.transaction_details.price)) * int(
                                            stock_num)
                                        gl_obj = GainLossHistory.objects.get(
                                            position_obj=pos_obj)
                                        gl_obj.realised_gainloss += num_quantize(
                                            realised_gainloss)
                                        # Incorrect Approach
                                        # buying_power += realised_gainloss
                                        # Correct Approach
                                        buying_power += (share_num * current_price)
                                        print(
                                            ",,,,,,,,,,,,,,,,33333333333      buyingpower",
                                            buying_power,
                                            num_quantize(realised_gainloss))
                                        gl_obj.save()
                                    except:
                                        pass

                                # pos_obj.save()
                                if int(pos_obj.transaction_details.size) == 0:
                                    print("###########    REMAINING SHARE    ",
                                          pos_obj.transaction_details.size)
                                    pos_obj.delete()
                                print("BUYYYING POWERRRR   ", buying_power)
                            identity_obj.buyingpower = num_quantize(buying_power)
                            identity_obj.save()
                        else:
                            if transaction_obj.remove_date and \
                                    transaction_obj.expires == "Good till " \
                                                               "canceled":
                                if current_date.date() == \
                                        transaction_obj.remove_date.date():
                                    transaction_obj.delete()

                    if transaction.transaction_type == "buy":
                        process = threading.Thread(
                            target=limit_order_purchase_2,
                            args=(transaction, price)
                        )
                        process.start()
                    else:
                        process = threading.Thread(
                            target=limit_order_sell,
                            args=(transaction, price)
                        )
                        process.start()

                    print("update_transaction_table_2 - Started progress for {} / {}".format(
                        index, all_transactions.count()
                    ))
                    index += 1
        except:
            pass
    else:
        # Get today's "Good for day" transactions and delete them
        good_for_day_transactions = Transaction.objects.filter(
            expires="Good for day", status="pending",
            time__year=current_date.year, time__month=current_date.month, time__day=current_date.day
        )
        print("update_transaction_table_2 - Good for Day Transactions : {}".format(good_for_day_transactions.count()))
        count = 0
        for transaction in good_for_day_transactions:
            # Old Logic
            # if current_date.date() != transaction.time.date():
            #     transaction.delete()
            #     count += 1

            # New Logic
            transaction.delete()
            count += 1


@celery_app.task()
def update_pos_table_latest_price_2():
    current_date = datetime.datetime.now()
    current_time = current_date.time()
    flag = 0

    if 9 <= int(current_time.hour) < 15:
        flag = 1
    elif int(current_time.hour) == 15:
        if int(current_time.minute) <= 30:
            flag = 1

    if flag == 1:
        users = User.objects.all()
        for user_obj in users:

            def update_position_table(user):
                total_price = 0
                value_list = []
                s = SingletonCelery.get_instance("1")
                for pos_obj in user.userposition_rel.all():
                    # TODO: change the live price access method
                    live_price, _ = s.parse_tick_data(pos_obj.stockname.symbol)
                    if live_price is not None:
                        # live_price = si.get_live_price(pos_obj.stockname.symbol + ".NS")
                        pos_obj.price = num_quantize(live_price)
                        pos_obj.save()

                        try:
                            update_position_and_gainloss(
                                live_price, pos_obj.stockname.symbol, user
                            )
                        except:
                            pass
                        try:
                            total_price += float(live_price) * float(pos_obj.size)
                        except:
                            pass
                date = datetime.datetime.timestamp(datetime.datetime.now())
                value_list.append([int(date) * 1000, float(total_price)])
                if not GainLossChartData.objects.filter(userid=user):
                    # print("value_listvalue_list    ",value_list)
                    gl_obj = GainLossChartData.objects.create(userid=user)
                    gl_obj.gainloss_data = value_list
                    gl_obj.save()
                else:
                    gl_obj = GainLossChartData.objects.get(userid=user)
                    gl_obj.gainloss_data.append(
                        [int(date) * 1000, round(float(total_price), 2)])
                    gl_obj.save()

            if user_obj.userposition_rel.all():
                process = threading.Thread(
                    target=update_position_table, args=(user_obj,)
                )
                process.start()
                process.join()


@celery_app.task()
def clear_portfolio_history():
    is_market_opened = is_market_opened_date()
    if is_market_opened:
        start, _ = get_day_range()
        # This will delete every old deletable intra day data.
        query_set = PortfolioValues.objects.filter(
            timestamp__lte=start,
            deletable=True
        )
        count = query_set.count()
        query_set.delete()
        print("Market is opened today .. Deleted {} Old Records".format(count))
    else:
        print("Market is closed today .. Deleting nothing")


@celery_app.task()
def save_portfolio_history():
    # returns None if Singleton is not initialised
    # s = SingletonPortfolio.build("")
    # print("SAVE PORTFOLIO HISTORY: Loop is running .. {}".format(s.thread.isAlive()))
    # if not s.thread.is_alive():
    #     print("Refreshing ... ")
    #     s.refresh_credentials()

    now = datetime.datetime.now()
    print("save_portfolio_history - STARTING {}".format(now))
    singleton = SingletonCelery.get_instance("")

    flag = 0

    r = {}
    t = Thread(
        target=is_market_opened_date_threaded, args=(None, r)
    )
    t.start()
    t.join()

    if r['is_market_opened'] and now.hour in range(9, 18):
        flag = 1

    # flag will be 2 for every time between 21:00 till 21:02
    if r['is_market_opened'] and \
            datetime.time(hour=21, minute=0, second=0) <= now.time() <= \
            datetime.time(hour=21, minute=2, second=0):
        flag = 2

    users_processed = 0

    if flag in [1, 2]:
        try:
            users = User.objects.all()
            # is_market_opened = is_market_opened_date()
            # if there is no weekend or a holiday, save the data as usual
            # else, do not save the data, this will save us some space on the db.
            for user in users:
                users_processed += 1
                positions = Position.objects.filter(userid=user)
                aggregate = {}

                # Calculate aggregates for each ticker
                for position in positions:
                    if position.ticker in aggregate:
                        aggregate[position.ticker]['size'] += position.size
                        aggregate[position.ticker]['unrealised_gl'] += \
                            float(position.gl_history_position_rel.all()[0].unrealised_gainloss)
                        aggregate[position.ticker]['realised_gl'] += \
                            float(position.gl_history_position_rel.all()[0].realised_gainloss)
                    else:
                        aggregate[position.ticker] = {
                            "size": position.size,
                            "unrealised_gl": float(
                                position.gl_history_position_rel.all()[0].unrealised_gainloss),
                            "realised_gl": float(position.gl_history_position_rel.all()[0].realised_gainloss),
                        }

                buying_power = float(user.user_details.identity.buyingpower)
                amt, unrealised_gl, realised_gl = 0, 0, 0
                # DB entries will be made only for users who have at least 1 ticker in the portfolio
                # calculate aggregate for the user using all the tickers
                for ticker in aggregate:
                    live_price, _ = singleton.parse_tick_data(ticker)
                    amt += live_price * aggregate[ticker]['size']
                    unrealised_gl += aggregate[ticker]['unrealised_gl']
                    realised_gl += aggregate[ticker]['realised_gl']

                # portfolio_value = amt + unrealised_gl + realised_gl + buying_power
                portfolio_value = amt + buying_power

                if flag == 1:
                    # always create the non-deletable graph.
                    PortfolioValues.objects.create(
                        user=user,
                        timestamp=now,
                        portfolio_value=portfolio_value,
                        cash_balance=0,
                        realized_gain_loss=realised_gl,
                        unrealized_gain_loss=unrealised_gl,
                        amount=amt,
                        deletable=True
                    )
                elif flag == 2:
                    # checking if a non-deletable record for today exists or not for the given user
                    exists = PortfolioValues.objects.filter(
                        user=user, deletable=False,
                        timestamp__year=now.year, timestamp__month=now.month, timestamp__day=now.day
                    ).exists()
                    # if a non-deletable record does not exist, create the record.
                    if not exists:
                        PortfolioValues.objects.create(
                            user=user,
                            timestamp=now,
                            portfolio_value=portfolio_value,
                            cash_balance=0,
                            realized_gain_loss=realised_gl,
                            unrealized_gain_loss=unrealised_gl,
                            amount=amt,
                            deletable=False
                        )
        except Exception as e:
            pass

    print("save_portfolio_history - USERS PROCESSED - {}".format(users_processed))


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


@celery_app.task()
def calculate_most_active():
    """
    Task to calculate the most active
    from main.tasks import calculate_most_active
    calculate_most_active.apply()
    """

    root = settings.MEDIA_ROOT
    full_path = os.path.join(root, "most_active.csv")

    cache.set("most_active_calculation_running", True)
    start = datetime.datetime.now()
    s = SingletonCelery.get_instance("2")
    print("TICK DATA LENGTH {}".format(len(s.tick_data)))

    tick_data = None
    while not tick_data:
        time.sleep(1)
        print("Retrying for Ticker Data from Zerodha Web Socket ....")
        tick_data = copy.deepcopy(s.tick_data)

    set_to_cache = False
    if s.tick_data:
        tick_data = copy.deepcopy(s.tick_data)
        t = []
        for i, row in enumerate(tick_data):
            row['symbol'] = s.stock_map.get(row['instrument_token'], None)
            row['yf'] = get_last_price(row['symbol'])

            if row['yf']:
                row['delta'] = row['last_price'] - row['yf']
                row['percent'] = ((row['delta'] / row['yf']) * 100)
                row['percent_abs'] = abs(row['percent'])
                t.append({
                    "symbol": row['symbol'],
                    "percent": row['percent'],
                    "percent_abs": row['percent_abs'],
                    "delta": row['delta'],
                })
            else:
                row['delta'] = None
                row['percent'] = None
                row['percent_abs'] = None

            print(f"========== {i + 1} {row['symbol']}, {row['last_price']} {row['yf']} "
                  f"{row['delta']}, {row['percent']}")

        del tick_data
        df = pd.DataFrame(t)
        print(df.head())
        print("DF Length ", len(df))
        if not df.empty:
            df.sort_values('percent_abs', ascending=False, inplace=True)
            print("Sorted")
            df = df.iloc[:10]   # Get Top 10
            print("Sliced to 10 elements")
            if os.path.exists(full_path):
                os.remove(full_path)
            # save to csv
            df.to_csv(full_path)
            cache.set("most_active_expiry", datetime.datetime.now() + datetime.timedelta(hours=1))
            print("Data Set to Cache ... ", os.path.exists(full_path))
            set_to_cache = True

    end = datetime.datetime.now()
    duration = (end - start).total_seconds()
    print(f"Duration .... {duration} Set to Cache {set_to_cache}")
    cache.set("most_active_calculation_running", False)


@celery_app.task()
def get_most_active():
    from bs4 import BeautifulSoup
    import requests

    url = 'https://in.finance.yahoo.com/most-active'

    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 '
                      '(KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.content, 'lxml')

    data = []
    for item in soup.select('.simpTblRow'):
        symbol = item.select('[aria-label=Symbol]')[0].get_text()
        if symbol.endswith(".NS") and StockNames.objects.filter(symbol=symbol.replace(".NS", "")).exists():
            name = item.select('[aria-label=Name]')[0].get_text()
            price = item.select('[aria-label*=Price]')[0].get_text()
            change = item.select('[aria-label=Change]')[0].get_text()
            change_pcnt = item.select('[aria-label="% change"]')[0].get_text()

            data.append({
                "symbol": symbol.replace(".NS", ""),
                "name": name,
                "price": price,
                "change": float(change_pcnt.replace(" ", "").replace("%", "").replace(",", ""))
            })

    root = settings.MEDIA_ROOT
    full_path = os.path.join(root, "most_active.csv")

    df = pd.DataFrame(data)
    if os.path.exists(full_path):
        os.remove(full_path)
    # save to csv
    df.to_csv(full_path, index=False)
    print("Symbols Written : {}".format(len(df)))
    return len(df)
