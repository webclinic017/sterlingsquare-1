import json
import os
import dateutil
import requests
import threading
import datetime
from celery.task import task

@task(name="update_stock_scheduler")
def stock_scheduler():
    result = requests.get("http://localhost:8000/accounts/update-stock-data/")
    print("sssssssssss", result)


def get_new_history(symbol):
    import custom_packages.yfinance as yf
    today = datetime.datetime.now()

    # define the ticker symbol
    tickerSymbol = symbol + ".NS"

    # get data on this ticker
    tickerData = yf.Ticker(tickerSymbol)

    # get the historical prices for this ticker
    # print(tickerData.history)
    # print(tickerData.quarterly_earnings)

    past_3_months = today.date() - dateutil.relativedelta.relativedelta(
        months=18)
    sbin = tickerData.history(period='1d',
                              start=past_3_months.strftime('%Y-%m-%d'),
                              end=today.date().strftime('%Y-%m-%d'))

    count = 0
    price_list = []
    print("GOT TICKER HISTORYYYY            ", tickerSymbol)
    for i, j in sbin.iterrows():
        temp_price_list = []

        dt_object1 = datetime.datetime.strptime(str(i), "%Y-%m-%d %H:%M:%S")
        if not dt_object1 == datetime.datetime.now().date():
            my_time = dt_object1.time()
            my_datetime = datetime.datetime.combine(i, my_time)
            date = datetime.datetime.timestamp(my_datetime)

            temp_price_list.append(int(date) * 1000)
            temp_price_list.append(sbin.values.tolist()[count][2])
            price_list.append(temp_price_list)

        count += 1

        # print(j,"\n")
    try:
        prev_day_price = price_list[len(price_list) - 2][1]
        today_price = price_list[len(price_list) - 1][1]
        difference = float(today_price) - float(prev_day_price)
    except:
        difference = 0
    if difference < 0:
        color = "#ff9900"
    else:
        color = "#00ff39"
    from nsetools import Nse
    from yahoo_fin import stock_info as si
    nse = Nse()
    data = {}
    print("NSEEEEEEEEE            ", tickerSymbol)
    # print("_____________        ",nse.get_quote(symbol))
    try:
        # from func_timeout import func_timeout, FunctionTimedOut
        print("BEFOREEE GET QUOTE            ", tickerSymbol)
        stock_details = tickerData.info
        # stock_details = nse.get_quote(symbol)
        # def get_quote_val(symbol):
        #     stock_details = nse.get_quote(symbol)
        #     return stockdata
        # try:
        #     stock_details = func_timeout(30, get_quote_val, args=(symbol))
        # except Exception as e:
        #     print("TIMEOUT ERRORRRRR         ",e)
        #     try:
        #         stock_details = nse.get_quote(symbol)
        #     except Exception as e:
        #         print("AGAINNnnnNNNNn       TIMEOUT ERRORRRRR         ",e)
        print("AFTERRRRR GET QUOTE            ", tickerSymbol)
        try:
            base_price = stock_details.get("basePrice", "")
            companyName = stock_details.get("longName", "")
            lastPrice = si.get_live_price(symbol + ".NS")
        except Exception as e:
            print("GET QUOTE TIME OUT ERROR    :  ", e)
        # print (price_list)
        # symbol = "hdfc"
        js_resp = get_earnings(symbol)
        estimate_list = get_earnings_by_type(js_resp, 'epsEstimate',
                                             "earnings")
        print("ESTIMATEEEE LISTTTT          ", estimate_list)
        # estimate_list = get_earnings(symbol, 'epsEstimate', "earnings")
        actual_list = get_earnings_by_type(js_resp, 'epsActual', "earnings")
        company_info = get_earnings_by_type(js_resp, "", "company_info")
        data = {
            'stockname': companyName,
            'color': color,
            'base_price': base_price,
            'stockprice': lastPrice,
            'stocksymbol': symbol,
            'stock_price_list': price_list,
            'estimate_list': json.dumps(estimate_list),
            'actual_list': json.dumps(actual_list),
            'company_info': company_info,

        }
    except:
        data = {
            'stockname': '',
            'color': color,
            'base_price': '',
            'stockprice': '',
            'stocksymbol': symbol,
            'stock_price_list': price_list,
            'estimate_list': '',
            'actual_list': '',
            'company_info': '',

        }
    return data


def get_stock_details_json(symbol):
    """

    :param symbol:
    :return:
    """
    try:
        from yahoo_fin import stock_info as si
        from accounts.models import Position

        response = {}
        from accounts.models import StockNames
        stock_obj = StockNames.objects.get(symbol=symbol)

        try:
            data = stock_obj.history.history_json
            data = data['data']
        except:
            data = get_new_history(symbol)
        if not bool(data):
            data = get_new_history(symbol)
        data['symbol'] = symbol
        # 1day
        d_data = si.get_data(symbol + ".NS", interval="1d")
        d_price_list = d_data.values.tolist()
        prev_day_price = d_price_list[len(d_price_list) - 2][4]
        response['prev_day_price'] = prev_day_price
        # 1m
        today = datetime.datetime.now()
        start_date = today.date() - dateutil.relativedelta.relativedelta(
            months=2)
        prev_month = today.date() - dateutil.relativedelta.relativedelta(
            months=1)
        m_data = si.get_data(symbol + ".NS", start_date=start_date,
                             end_date=prev_month, interval="1d")
        m_price_list = m_data.values.tolist()
        prev_month_price = m_price_list[len(m_price_list) - 1][4]
        response['prev_month_price'] = prev_month_price
        # 3m
        start_date = today.date() - dateutil.relativedelta.relativedelta(
            months=4)
        prev_3month = today.date() - dateutil.relativedelta.relativedelta(
            months=3)
        three_m_data = si.get_data(symbol + ".NS", start_date=start_date,
                                   end_date=prev_3month, interval="1d")
        three_m_price_list = three_m_data.values.tolist()
        prev_3m_price = three_m_price_list[len(three_m_price_list) - 1][4]
        response['prev_3m_price'] = prev_3m_price
        # 6m
        start_date = today.date() - dateutil.relativedelta.relativedelta(
            months=7)
        prev_6month = today.date() - dateutil.relativedelta.relativedelta(
            months=6)
        six_m_data = si.get_data(symbol + ".NS", start_date=start_date,
                                 end_date=prev_6month, interval="1d")
        six_m_price_list = six_m_data.values.tolist()
        prev_6m_price = six_m_price_list[len(six_m_price_list) - 1][4]
        response['prev_6m_price'] = prev_6m_price
        # 1y
        start_date = today.date() - dateutil.relativedelta.relativedelta(
            years=1, months=1)
        prev_year = today.date() - dateutil.relativedelta.relativedelta(
            years=1)
        y_data = si.get_data(symbol + ".NS", start_date=start_date,
                             end_date=prev_year, interval="1d")
        y_price_list = y_data.values.tolist()
        prev_y_price = y_price_list[len(y_price_list) - 1][4]
        response['prev_y_price'] = prev_y_price
        from custom_packages.yahoo_finance import YahooFinance
        latest_price = YahooFinance(symbol + '.NS', result_range='1d',
                                    interval='1m', dropna='True').result

        count = 0
        for i, j in latest_price.iterrows():
            temp_price_list = []
            dt_object1 = datetime.datetime.strptime(str(i),
                                                    "%Y-%m-%d %H:%M:%S")
            my_time = dt_object1.time()
            my_datetime = datetime.datetime.combine(i, my_time)
            date = datetime.datetime.timestamp(my_datetime)
            temp_price_list.append(int(date) * 1000)
            temp_price_list.append(latest_price.values.tolist()[count][2])
            # latest_price_list.append(temp_price_list)
            data['stock_price_list'].append(temp_price_list)
            count += 1
        stock_price = round(si.get_live_price(symbol + ".NS"), 2)
        data['stockprice'] = stock_price
        print("PRICEEE   --     ", stock_price)
        try:

            for pos_obj in Position.objects.filter(ticker=symbol):
                share_num = int(pos_obj.transaction_details.size)
                pos_obj.unrealised_gainloss = num_quantize((float(
                    stock_price) - float(
                    pos_obj.transaction_details.price)) * share_num)
                pos_obj.save()
                print("GAIN LOSS  --SYMBOL  ", symbol,
                      pos_obj.unrealised_gainloss)
        except Exception as e:
            print("POSITION ERROR    ", e)
            pass
    except Exception as e:
        print("ERROR OCCUREDDDDD         ", e)
        data = {}
        response = {}

    return data, response


def stock_update():
    from accounts.models import StockHistory, StockNames
    from nsetools import Nse
    from yahoo_fin import stock_info as si

    nse = Nse()
    q = nse.get_stock_codes()
    for i in q:
        try:
            StockNames.objects.get_or_create(symbol=i, name=q[i])
        except:
            pass

    all_stocks = StockNames.objects.all()
    today = datetime.datetime.now()
    import threading

    for stock in all_stocks:
        try:
            def thread_process():
                is_latest = False
                try:
                    st_h = StockHistory.objects.get(stock=stock)
                    current_time = datetime.datetime.now().time()
                    if int(current_time.hour) >= 9 and int(
                            current_time.hour) < 15:
                        is_latest = False
                    elif int(current_time.hour) == 15:
                        if int(current_time.minute) <= 30:
                            is_latest = False

                            # if st_h.last_update == today.date():
                            #     is_latest = True
                except:
                    pass
                if stock.symbol != 'SYMBOL' and is_latest == False:
                    history = {}
                    symbol = stock.symbol
                    print("Pulling data for=====", symbol)
                    data, response = get_stock_details_json(symbol)
                    history['data'] = data
                    history['response'] = response

                    try:
                        st_h = StockHistory.objects.get(stock=stock)

                        st_h.history_json = history

                        st_h.last_update = today.date()
                        st_h.save()
                    except:
                        StockHistory.objects.create(stock=stock,
                                                    history_json=history,
                                                    last_update=today.date())

                    print("data pulled for==", symbol, "....", len(data))

            # process = threading.Thread(target=thread_process)
            # process.start()
            # pricess.join()
            thread_process()
        except:
            print("Errorrrr", stock.symbol)


def get_earnings(symbol):
    # token = tokens.TOKEN_EOD_HISTORICAL_DATA
    token = "5ec44b37b0dc93.60982867"
    url = "https://eodhistoricaldata.com/api/fundamentals/" \
          "{}.NSE?api_token={}".format(
        symbol, token)
    print("URL   ", url)
    a = requests.get(url)
    try:
        js = json.loads(a.text)
        return js
    except:
        return False


def get_earnings_by_type(js, key, type):
    if type == "company_info":
        # print ( js.get("General"))
        info = js.get("General").get("Description")
        officers = js.get("General").get("Officers")
        head_post = ""
        head_name = ""
        Headquarters = ""
        # if officers:
        #     head_post = officers.get("0").get("Title")
        #     head_name = js.get("General").get("Officers").get("0").get(
        #     "Name")
        Headquarters = js.get("General").get("Address")
        officer_list = []
        if officers:
            for i, j in js.get("General").get("Officers").items():
                officer_dict = {
                    'name': j.get("Name"),
                    'title': j.get("Title")
                }
                officer_list.append(officer_dict)
        market_cap = js.get("Highlights").get("MarketCapitalizationMln")
        details_dict = {
            'about': info,
            'head_post': head_post,
            'head_name': head_name,
            'officer_list': officer_list,
            'Headquarters': Headquarters,
            'market_cap': market_cap
        }
        result = details_dict
        # print (js.get("General"))
    elif type == "officers_list":
        officer_list = []
        officers = js.get("General").get("Officers")
        if officers:
            for i, j in js.get("General").get("Officers").items():
                officer_dict = {
                    'name': j.get("Name"),
                    'title': j.get("Title")
                }
                officer_list.append(officer_dict)
        result = officer_list
    elif type == "get_pe_ratio":
        result = js.get("Highlights").get("PERatio")
    elif type == "get_headquaters":
        result = js.get("General").get("Address")
    elif type == "about_company":
        try:
            info = js.get("General").get("Description")
            result = info
        except:
            result = False
    elif type == "get_employees":
        try:
            employees = js.get("General").get("FullTimeEmployees")
            result = employees
        except:
            result = False

    else:
        history = js.get("Earnings").get("History")
        # print ("HISTORY   ",history)
        earnings_list = []
        for i, j in history.items():
            if j.get("epsEstimate") and j.get("epsActual"):
                temp_arr = []
                temp_arr.append(str(i))
                temp_arr.append(j.get(key))
                # earnings_dict = {
                #     'date':i,
                #     # 'estimated':i.get("epsEstimate"),
                #     key:j.get(key),
                #     # 'actual':i.get("epsActual")
                # }
                earnings_list.append(temp_arr)
        result = earnings_list
    return result


# DEPRECATED: Migrated new version to main/tasks.py FUNCTION: update_stock_market_details()
@task(name="update_stock_market_details_scheduler")
def update_stock_market_details():
    import custom_packages.yfinance as yf
    from accounts.models import StockNames
    from accounts.models import StockInfo

    stocks = StockNames.objects.all()
    for stock in stocks:
        if str(stock.symbol) != "SYMBOL":

            tickerData = yf.Ticker(str(stock.symbol) + ".NS")
            # print ("____   ",tickerData.info)
            try:
                yf_info = tickerData.info
            except:
                yf_info = {}
            ear_resp = get_earnings(str(stock.symbol))

            try:

                stock_general_data, status = StockInfo.objects.get_or_create(
                    stock=stock)
                try:
                    # print(str(stock.symbol)+".NS", "       trailingPE   ",
                    # yf_info["trailingPE"])
                    stock_general_data.trailing_pe = yf_info["trailingPE"]
                except Exception as e:
                    print("TRAILING PE ERROR   ", e)
                    pass
                try:
                    # print(str(stock.symbol)+".NS", "       marketCap   ",
                    # yf_info["marketCap"])
                    stock_general_data.market_cap = yf_info["marketCap"]
                except Exception as e:
                    print("MARKET CAP ERROR   ", e)
                    pass
                try:
                    # print(str(stock.symbol)+".NS", "       priceToBook
                    # ", yf_info["priceToBook"])
                    stock_general_data.price_to_book = yf_info["priceToBook"]
                except Exception as e:
                    print("PRICE TO BOOK ERROR   ", e)
                    pass

                try:
                    stock_general_data.employees = yf_info["fullTimeEmployees"]
                except Exception as e:
                    print("EMPLOYEES ERROR   ", e)
                    try:
                        employees = get_earnings_by_type(ear_resp, "",
                                                         "get_employees")
                        if employees:
                            stock_general_data.employees = employees
                    except Exception as e:
                        print("EMPLOYEES ERROR  2 ", e)
                    pass

                try:
                    officers_list = []
                    officers_list = get_earnings_by_type(ear_resp, "",
                                                         "officers_list")
                    data = {
                        'officer_info': officers_list
                    }
                    print("OFFICER LIST DATA   ", data)
                    stock_general_data.officers = data
                except Exception as e:
                    print("OFFICER LIST ERROR   ", e)
                    pass
                try:
                    about_company = get_earnings_by_type(ear_resp, "",
                                                         "about_company")
                    if not about_company:
                        about_company = yf_info.get("longBusinessSummary")
                    print("COMPANY INFO   +")
                    stock_general_data.company_info = about_company
                except Exception as e:
                    print("COMPANY INFO ERROR   ", e)
                    pass

                try:
                    headquaters = get_earnings_by_type(ear_resp, "",
                                                       "get_headquaters")
                    stock_general_data.headquaters = headquaters
                except Exception as e:
                    print("HEADQUATERS  ERROR   ", e)
                    pass

                try:
                    pe_ratio = get_earnings_by_type(ear_resp, "",
                                                    "get_pe_ratio")
                    stock_general_data.pe_ratio = pe_ratio
                except Exception as e:
                    print("PE RATIO ERROR   ", e)
                    pass

                try:
                    stock_general_data.open_price = yf_info.get("open")
                except Exception as e:
                    print("YF OPEN PRICE ERROR   ", e)
                    pass

                try:
                    stock_general_data.low_today = yf_info.get("dayLow")
                except Exception as e:
                    print("YF LOW TODAY ERROR   ", e)
                    pass

                try:
                    stock_general_data.high_today = yf_info.get("dayHigh")
                except Exception as e:
                    print("YF HIGH TODAY ERROR   ", e)
                    pass
                try:
                    # print(str(stock.symbol)+".NS", "       priceToBook
                    # ", yf_info["priceToBook"])
                    stock_general_data.sector = yf_info["sector"]
                except Exception as e:
                    print("SECTOR ERROR   ", e)
                    pass
                stock_general_data.updated_at = datetime.datetime.now()
                stock_general_data.save()
                print(str(stock.symbol), ">>>>>>>Completed", )
            except Exception as e:
                print("UPDATE STOCK MARKET - ERROR FOR SYMBOL  :",
                      str(stock.symbol), "    ", e)


@task(name="update_stock_live_price_scheduler")
def update_live_price():
    today = datetime.datetime.now()
    from yahoo_fin import stock_info as si
    from accounts.models import StockHistory
    for st_h in StockHistory.objects.all():
        # st_h = StockHistory.objects.get(stock=stock)
        # if st_h.history_json:
        date = datetime.datetime.timestamp(datetime.datetime.now())
        try:
            live_price = si.get_live_price(st_h.stock.symbol + ".NS")

            # st_h.history_json = data
            if st_h.current_data:
                c_data = st_h.current_data
                c_data.append([date, live_price])
                st_h.current_data = c_data
            else:
                st_h.current_data = [[date, live_price]]
            st_h.last_update = today.date()
            st_h.save()

            print("Live Price updated for========", st_h.stock.symbol,
                  " ......       ", len(st_h.current_data))
        except Exception as e:
            print("Error for symbol     ", e)


# DEPRECATED : Migrated new version to main/tasks.py FUNCTION: update_transaction_table_2()
@task(name="update_transaction_table_scheduler")
def update_transaction_table():
    from accounts.models import Transaction, TransactionHistory
    from accounts.models import UserDetails
    from accounts.models import IdentityDetails

    from yahoo_fin import stock_info as si
    current_date = datetime.datetime.now()
    current_time = current_date.time()

    flag = 0
    if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
        flag = 1
    elif int(current_time.hour) == 15:
        if int(current_time.minute) <= 30:
            flag = 1
    if flag == 1:
        print("YYYYY")
        try:
            for transaction_obj in Transaction.objects.filter(
                    status="pending"):
                print("SYMBOLLLL", transaction_obj.stockticker.symbol)
                import threading
                def limit_order_purchase(transaction_obj):

                    user = UserDetails.objects.get(user=transaction_obj.user)
                    user_buyingpower = float(user.identity.buyingpower)

                    identity = IdentityDetails.objects.get(id=user.identity.id)

                    live_price = si.get_live_price(
                        transaction_obj.stockticker.symbol + ".NS")
                    print("live_price     ", num_quantize(float(live_price)))
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
                        from accounts.models import Position
                        position_obj, status = Position.objects.get_or_create(
                            userid=transaction_obj.user,
                            stockname=transaction_obj.stock,
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
                            from accounts.models import GainLossHistory
                            gl_history = GainLossHistory.objects.create(
                                userid=transaction_obj.user,
                                stock=transaction_obj.stock,
                                total_cash=total_cash)
                            gl_history.unrealised_gainloss = num_quantize(
                                (float(live_price) - float(
                                    position_obj.transaction_details.price)) *
                                int(transaction_obj.size))
                            gl_history.position_obj = position_obj
                            gl_history.save()
                            user_buyingpower -= total_cash
                            identity.buyingpower = user_buyingpower
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

                process = threading.Thread(target=limit_order_purchase,
                                           args=(transaction_obj,))
                process.start()
        except:
            pass
    else:
        for transaction_obj in Transaction.objects.filter(
                expires="Good for day", status="pending"):
            if current_date.date() != transaction_obj.time.date():
                transaction_obj.delete()


def num_quantize(value, n_point=2):
    """
    :param value:
    :param n_point:
    :return:
    """
    from decimal import localcontext, Decimal, ROUND_HALF_UP
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        if value:
            d_places = Decimal(10) ** -n_point
            # Round to two places
            value = Decimal(value).quantize(d_places)
        return value


@task(name="update_gainloss_table")
def update_gainloss_table():
    from accounts.models import GainLossHistory, TotalGainLoss
    from django.contrib.auth.models import User
    current_date = datetime.datetime.now()
    current_time = current_date.time()

    timeflag = 0
    if int(current_time.hour) > 18:
        timeflag = 1
    elif int(current_time.hour) < 9:
        timeflag = 1
    if timeflag == 1:
        for user_obj in User.objects.all():
            total_gl = 0
            flag = 0
            for gl_obj in user_obj.user_gl_history_rel.all():
                if gl_obj.is_calculated == False:
                    flag = 1
                    total_gl += float(gl_obj.unrealised_gainloss)
                    gl_obj.is_calculated = True
                    gl_obj.save()
            if flag == 1:
                total_gl_obj = TotalGainLoss.objects.create(
                    gainloss=total_gl, userid=user_obj,
                    created_at=datetime.datetime.now())

    from accounts.models import GainLossChartData
    for gl_chart_obj in GainLossChartData.objects.all():
        if gl_chart_obj.created_at.date() != current_date:
            gl_chart_obj.delete()


@task(name="update_pos_table_latest_price")
def update_pos_table_latest_price():
    from django.contrib.auth.models import User
    from accounts.models import GainLossChartData
    from yahoo_fin import stock_info as si
    current_date = datetime.datetime.now()
    current_time = current_date.time()
    flag = 0
    if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
        flag = 1
    elif int(current_time.hour) == 15:
        if int(current_time.minute) <= 30:
            flag = 1
    if flag == 1:
        for user_obj in User.objects.all():
            # current_cash = user_obj.user_details.all()[
            # 0].identity.buyingpower
            def update_position_table(user_obj):
                total_price = 0
                value_list = []
                for pos_obj in user_obj.userposition_rel.all():
                    live_price = si.get_live_price(
                        pos_obj.stockname.symbol + ".NS")
                    print("LIVE PRICEEEEE    ", num_quantize(live_price))
                    pos_obj.price = num_quantize(live_price)
                    pos_obj.save()

                    from accounts.views import update_position_and_gainloss
                    try:
                        update_position_and_gainloss(live_price,
                                                     pos_obj.stockname.symbol,
                                                     user_obj)
                    except:
                        pass
                    try:
                        total_price += float(live_price) * float(
                            pos_obj.transaction_details.size)
                    except:
                        pass
                date = datetime.datetime.timestamp(datetime.datetime.now())
                value_list.append([int(date) * 1000, float(total_price)])
                if not GainLossChartData.objects.filter(userid=user_obj):
                    # print("value_listvalue_list    ",value_list)
                    gl_obj = GainLossChartData.objects.create(userid=user_obj)
                    gl_obj.gainloss_data = value_list
                    gl_obj.save()
                else:
                    gl_obj = GainLossChartData.objects.get(userid=user_obj)
                    gl_obj.gainloss_data.append(
                        [int(date) * 1000, round(float(total_price), 2)])
                    gl_obj.save()

            if user_obj.userposition_rel.all():
                process = threading.Thread(target=update_position_table,
                                           args=(user_obj,))
                process.start()
                process.join()
