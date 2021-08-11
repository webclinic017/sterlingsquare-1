import json
import copy
import datetime
import numpy as np
import threading
from django.db.models import Q
import pandas as pd
import random
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber, Rank
from django.db.models import F
from django.core.cache import cache
from dateutil.relativedelta import relativedelta

import dateutil
from django.db.models import Sum, F
from kiteconnect import KiteTicker, KiteConnect
from sterling_square.TickerSingleton import Singleton2
from utils.symbol_reader import SymbolReader
from threading import Thread

from pandas_datareader.tests.test_tiingo import symbols

from utils.Response import *

import requests
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from yahoo_fin import stock_info as si
from nsetools import Nse
from custom_packages.yahoo_finance import YahooFinance
from accounts.forms import CustomAuthForm, UserDetailsForm, IdentityDetailsForm
from sterling_square.celery_file import stock_update
from decimal import localcontext, Decimal, ROUND_HALF_UP
from django.core.paginator import PageNotAnInteger
from django.core.paginator import EmptyPage

from utils.date_utils import *
from accounts.models import *
from sterling_square import tokens
from utils.util_functions import *


class CustomLogin(auth_views.LoginView):
    """Login View."""

    redirect_authenticated_user = True
    form_class = CustomAuthForm

    def form_valid(self, form):
        login(self.request, form.get_user())

        return HttpResponseRedirect(self.get_success_url())


class LoginView(TemplateView):
    """
    Login page
    """
    template_name = 'login.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        response = {}
        loginform = CustomAuthForm(request, data=request.POST)
        if loginform.is_valid():
            try:
                user = User.objects.get(email=request.POST.get("username"))
                login(request, user)
                response['status'] = True
            except:
                response['status'] = False
        else:
            response['status'] = False
        return HttpResponse(json.dumps(response),
                            content_type="application/json")


class UpdateStockScheduler(TemplateView):
    """
    Login page
    """
    template_name = 'signup.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateStockScheduler, self).dispatch(request, *args,
                                                          **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateStockScheduler, self).get_context_data(**kwargs)
        stock_update()
        return context


class SignupView(TemplateView):
    """
    Login page
    """
    template_name = 'signup.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        response = {}
        userdetails_form = UserDetailsForm(request.POST)
        # basicdetails_form = BasicDetailsForm(request.POST)
        identitydetails_form = IdentityDetailsForm(request.POST)

        # ssn = str(request.POST.get("ssn1"))+str(request.POST.get(
        # "ssn2"))+str(request.POST.get("ssn3"))
        # dob = str(request.POST.get("dob_date"))+"-"+str(request.POST.get(
        # "dob_month"))+"-"+str(request.POST.get("dob_year"))
        # dob_obj = datetime.datetime.strptime(dob, '%d-%m-%Y')
        if userdetails_form.is_valid() and identitydetails_form.is_valid():
            user_save = userdetails_form.save(commit=False)
            user_save.email = request.POST.get("email")
            user_save.username = request.POST.get("email")
            # basic_detail_save = basicdetails_form.save()
            identity_save = identitydetails_form.save()
            # identity_save.ssn = ssn
            # identity_save.dob = dob_obj
            # basic_obj = BasicDetails.objects.get(id=basic_detail_save.id)
            identity_obj = IdentityDetails.objects.get(id=identity_save.id)
            # user_save.basic_info = basic_obj
            user_save.identity = identity_obj
            user_save.set_password(request.POST.get("password"))
            user_save.save()
            UserDetails.objects.create(user=user_save, identity=identity_obj)
        return HttpResponse(json.dumps(response),
                            content_type="application/json")


class DashboardView(TemplateView):
    template_name = 'dashboard.html'  # 'dashboard.html'

    def get(self, request, *args, **kwargs):
        start, end = get_day_range(business_hours_only=False)
        context = {
            "market_opened_today": 1 if is_market_opened_date() else 0,
            "market_opened_now": 1 if is_market_open_now() else 0,
            "min": int(start.timestamp() * 1000),
            "max": int(end.timestamp() * 1000),
            "intraday_change": price_change("1D", "", 0.0, 0.0),
            "open_values": {
                "1D": "0.0",
                "1m": "0.0",
                "3m": "0.0",
                "6m": "0.0",
                "1y": "0.0",
                "5y": "0.0",
            },
            "portfolio_values": {
                "1D": "0.0",
                "1m": "0.0",
                "3m": "0.0",
                "6m": "0.0",
                "1y": "0.0",
                "5y": "0.0",
            },
            "live": "0.0"
        }
        nse = Nse()
        if request.user.is_authenticated:

            # position_obj = request.user.userposition_rel.first()
            # if position_obj:
            #     stock_obj = StockNames.objects.get(symbol=position_obj.stockname.symbol)
            #     context = stock_obj.history.history_json['data']
            #     # response = stock_obj.history.history_json['response']
            #     context['has_position'] = True
            #     print("????????????????    ",position_obj.stockname.symbol )
            #     try:
            #         d_data = si.get_data(position_obj.stockname.symbol + ".NS", interval="1d")
            #         d_price_list = d_data.values.tolist()
            #         prev_day_price = d_price_list[len(d_price_list) - 2][4]
            #         context['prev_day_price'] = prev_day_price
            #     except:
            #         pass
            #     try:
            #         stockprice = context.get('stockprice')
            #     except:
            #         stockprice = round(si.get_live_price(stock_obj.symbol + ".NS"), 2)
            #         context['stockprice'] = stockprice
            #     context2 = get_position_details(request,stock_obj,position_obj,stockprice)
            #     context.update(context2)
            #     # response['prev_day_price'] = prev_day_price
            # else:
            #     context['stock_price_list'] = [0, 0]
            #     context['stockprice'] = 0
            value_list = []
            try:
                buyingpower = UserDetails.objects.get(
                    user=request.user).identity.buyingpower
            except:
                buyingpower = 0
            print("buyingpower   ", buyingpower)
            date = datetime.datetime.timestamp(datetime.datetime.now())
            choice_arr = []
            start_date = datetime.date(2019, 1, 1)
            end_date = datetime.date(2020, 8, 16)

            time_between_dates = end_date - start_date
            days_between_dates = time_between_dates.days
            distict_arr = []

            # TotalGainLoss.objects.all().delete()
            # for i in range(0,366):
            #     while True:
            #         random_number_of_days = random.randrange(days_between_dates)
            #         if not random_number_of_days in distict_arr:
            #             distict_arr.append(random_number_of_days)
            #             break
            #     random_date = start_date + datetime.timedelta(days=i)
            #     if len(TotalGainLoss.objects.filter(userid=request.user)) <366:
            #         # for j in range(0, 5):
            #         tgl_obj = TotalGainLoss.objects.create(userid=request.user)
            #         tgl_obj.gainloss = random.randint(0, 100)
            #         # start_date_time = datetime.datetime.combine(random_date, datetime.datetime.now().time())
            #         date_time = datetime.datetime.now() - dateutil.relativedelta.relativedelta(hours=random.randint(0, 5),minutes=random.randint(0, 59))
            #         tgl_obj.created_at = datetime.datetime.combine(random_date, datetime.datetime.now().time())
            #         print("??????////   ",datetime.datetime.now() - dateutil.relativedelta.relativedelta(hours=random.randint(0, 5),minutes=random.randint(0, 59)))
            #         tgl_obj.save()
            #     else:
            #         break
            # for pos_obj in Position.objects.filter(userid=request.user):
            #     date = datetime.datetime.timestamp(pos_obj.created_at)
            # stock_obj = StockNames.objects.get(symbol=pos_obj.stockname.symbol)
            # data = stock_obj.history.history_json['data']
            # response = stock_obj.history.history_json['response']
            # try:
            #     pos_stockprice = data['stockprice']
            # except:
            #     pos_stockprice = round(si.get_live_price(stock_obj.symbol + ".NS"), 2)
            # temp_price_list.append(int(date) * 1000)
            # value_list.append([int(date) * 1000,float(pos_obj.price)+float(buyingpower)])
            # print("value_listvalue_list    ",value_list)
            # try:
            current_date = datetime.datetime.now()
            current_time = current_date.time()
            timeflag = 0
            if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
                timeflag = 1
            elif int(current_time.hour) == 15:
                if int(current_time.minute) <= 30:
                    timeflag = 1
            if timeflag == 1:
                try:
                    # UNOPTIMISED
                    # gl_obj = GainLossChartData.objects.get(userid=request.user)
                    # value_list = [[x[0], float(x[1]) + float(buyingpower)] for
                    #               x in gl_obj.gainloss_data]

                    # OPTIMISED
                    value_list = []
                except:
                    # UNOPTIMISED
                    # value_list = []
                    # if TotalGainLoss.objects.filter(userid=request.user):
                    #     for t_gl_obj in TotalGainLoss.objects.filter(
                    #             userid=request.user):
                    #         # print("::::  ",t_gl_obj.gainloss)
                    #         tgl_date = datetime.datetime.timestamp(
                    #             t_gl_obj.created_at)
                    #         value_list.append([int(tgl_date) * 1000, float(
                    #             t_gl_obj.gainloss) + float(buyingpower)])

                    # OPTIMISED
                    value_list = []
            else:
                # UNOPTIMISED
                # if TotalGainLoss.objects.filter(userid=request.user):
                #     for t_gl_obj in TotalGainLoss.objects.filter(
                #             userid=request.user):
                #         # print("::::  ",t_gl_obj.gainloss)
                #         tgl_date = datetime.datetime.timestamp(
                #             t_gl_obj.created_at)
                #         value_list.append([int(tgl_date) * 1000,
                #                            float(t_gl_obj.gainloss) + float(
                #                                buyingpower)])

                # OPTIMISED
                value_list = []
            # print("><><><<<    ",value_list)
            # print("value_list--   ",value_list)
            # value_list = gl_obj.gainloss_data
            # except:
            #     value_list = []
            # if not GainLossChartData.objects.filter(userid=request.user):
            #     gl_obj = GainLossChartData.objects.create(userid=request.user)
            #     gl_obj.gainloss_data = value_list
            #     gl_obj.save()
            # else:
            #     gl_obj = GainLossChartData.objects.get(userid=request.user)
            #     current_date = datetime.datetime.now()
            #     if gl_obj.created_at.date() != current_date.date():
            #         gl_obj.delete()
            #         gl_obj = GainLossChartData.objects.create(userid=request.user)
            #         gl_obj.gainloss_data = value_list
            #         gl_obj.save()

            context['stock_price_lists'] = value_list
            context['current_amount'] = buyingpower

            value = PortfolioValues.objects.filter(user=request.user).order_by("-timestamp").first()
            if value:
                context['stockprice'] = num_quantize(value.portfolio_value)
            else:
                context['stockprice'] = 0.00

        else:
            context['stock_price_lists'] = [0, 0]
            context['stockprice'] = 0
        # try:
        #     context['stockprice'] = num_quantize(context['stockprice'])
        # except:
        #     print("{{{   0",stock_obj.symbol)
        #     try:
        #         context['stockprice'] = num_quantize(round(si.get_live_price(stock_obj.symbol + ".NS"), 2))
        #     except:
        #         context['stockprice'] = 0
        # update_live_price()

        if request.user.is_authenticated:
            # AFTER OPTIMISATION
            _, end = get_day_range(datetime.datetime.now())
            start_5y, end_5y = get_day_range(get_previous_business_day(end - relativedelta(years=5)))

            # Divided a single filter statement into two to leverage the power of db indexes.
            portfolio_qs_values = list(PortfolioValues.objects.filter(
                user=request.user
            ).filter(
                timestamp__gte=make_aware(start_5y),
                timestamp__lte=make_aware(end)
            ).order_by("timestamp").values())

            portfolio_qs_values_2 = pd.DataFrame(portfolio_qs_values)
            portfolio_qs_values_3 = copy.deepcopy(portfolio_qs_values_2)

            # AFTER OPTIMISATION - This was a useless query
            # top_searched = TopSearched.objects.filter(userid=request.user)
            # if len(top_searched) > 10:
            #     top_searched = top_searched[:10]
            # context['top_searched'] = top_searched

            # AFTER OPTIMISATION
            t = portfolio_open_values(portfolio_qs_values_2)
            context['live'] = t['1d'][1]
            context['intraday_change'] = \
                price_change(key="1D", symbol="", live_price=t['1d'][1], prev_price=t['1d'][0])
            context['open_values'] = {
                "1D": t['1d'][0],
                "1m": t['1m'][0],
                "3m": t['3m'][0],
                "6m": t['6m'][0],
                "1y": t['1y'][0],
                "5y": t['5y'][0],
            }

            # BEFORE OPTIMISATION
            # open_value, live_value = portfolio_open_value(request.user, "1D")
            # context['intraday_change'] = \
            #     price_change(key="1D", symbol="", live_price=live_value, prev_price=open_value)
            # print(live_value, open_value)
            # context['live'] = live_value
            # context['open_values'] = {
            #     "1D": open_value,
            #     "1m": portfolio_open_value(request.user, "1m")[0],
            #     "3m": portfolio_open_value(request.user, "3m")[0],
            #     "6m": portfolio_open_value(request.user, "6m")[0],
            #     "1y": portfolio_open_value(request.user, "1y")[0],
            #     "5y": portfolio_open_value(request.user, "5y")[0],
            # }

            # AFTER OPTIMISATION
            t2 = portfolio_open_values_2(portfolio_qs_values_3)
            context['portfolio_values'] = {
                "1D": portfolio_open_value_2(request.user)[0],
                "1m": t2['1m'][0],
                "3m": t2['3m'][0],
                "6m": t2['6m'][0],
                "1y": t2['1y'][0],
                "5y": t2['5y'][0],
            }

            # BEFORE OPTIMISATION
            # context['portfolio_values'] = {
            #     "1D": portfolio_open_value_2(request.user, "1D")[0],
            #     "1m": portfolio_open_value_2(request.user, "1m")[0],
            #     "3m": portfolio_open_value_2(request.user, "3m")[0],
            #     "6m": portfolio_open_value_2(request.user, "6m")[0],
            #     "1y": portfolio_open_value_2(request.user, "1y")[0],
            #     "5y": portfolio_open_value_2(request.user, "5y")[0],
            # }

        lenn = 0
        sym = ''
        # for i in StockHistory.objects.all():
        #     if len(i.current_data) > 5 and i.history_json['stock_price_list']:
        #         if lenn < len(i.current_data):
        #             lenn = len(i.current_data)
        #             sym = i.stock.symbol

        # import requests
        # go_to_url = "https://www1.nseindia.com/live_market/" \
        #             "dynaContent/live_analysis/gainers/niftyGainers1.json"
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
        #                   'AppleWebKit/537.36 (KHTML, like Gecko) '
        #                   'Chrome/56.0.2924.76 Safari/537.36',
        #     "Upgrade-Insecure-Requests": "1", "DNT": "1",
        #     "Accept": "text/html,application/xhtml+xml, "
        #               "application/xml;q=0.9,*/*;q=0.8",
        #     "Accept-Language": "en-US,en;q=0.5",
        #     "Accept-Encoding": "gzip, deflate"}
        # resp = requests.get(go_to_url, headers=headers)
        # print("RRRR   ", resp, resp.json())
        # context['top_gainers'] = resp.json()
        # print("............      ", nse.get_top_gainers()[:5])
        # context['top_gainers'] = nse.get_top_gainers()[:5]
        # from custom_packages.yahoo_finance import TG_DATA
        # context['top_gainers'] = nse.get_top_gainers()
        context['top_gainers'] = [
            {
                'symbol': 'ACC',
                'ltp': "$1,769.43",
                'netPrice': "5.00",
            },
            {
                'symbol': 'AAPL',
                'ltp': "$1,769.43",
                'netPrice': "5.00",
            },
            {
                'symbol': 'TSLA',
                'ltp': "$1,769.43",
                'netPrice': "5.00",
            },
            {
                'symbol': 'ATT',
                'ltp': "$1,769.43",
                'netPrice': "5.00",
            }
        ]
        return render(request, self.template_name, context)


class DashboardAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            response = {}
            ajxtype = request.GET.get("type")
            symbol = request.GET.get("symbol")

            if ajxtype == "get_stock_details":
                stock_obj = StockNames.objects.get(symbol=symbol)
                cc = StockHistory.objects.get(stock=stock_obj).history_json
                if StockHistory.objects.filter(stock=stock_obj):

                    data = stock_obj.history.history_json['data']
                    response = stock_obj.history.history_json['response']
                    # tttt = get_stock_details_json(symbol,request)

                    latest_price = YahooFinance(symbol + '.NS',
                                                result_range='1d',
                                                interval='1m',
                                                dropna='True').result
                    # price_list = latest_price.values.tolist()
                    current_time = datetime.datetime.now().time()
                    count = 0
                    for i, j in latest_price.iterrows():
                        temp_price_list = []
                        dt_object1 = datetime.datetime.strptime(str(i),
                                                                "%Y-%m-%d "
                                                                "%H:%M:%S")
                        my_time = dt_object1.time()
                        my_datetime = datetime.datetime.combine(i, my_time)
                        date = datetime.datetime.timestamp(my_datetime)

                        temp_price_list.append(int(date) * 1000)
                        temp_price_list.append(
                            latest_price.values.tolist()[count][2])
                        # print(temp_price_list)
                        # latest_price_list.append(temp_price_list)
                        # data['stock_price_list'].append(temp_price_list)

                    try:
                        stock_gen_info = StockInfo.objects.get(stock=stock_obj)
                    except:
                        stock_gen_info = {}
                    data['stock_gen_info'] = stock_gen_info
                    try:
                        TopSearched.objects.get(stock=stock_obj,
                                                userid=request.user)
                        data['added_to_watchlist'] = True
                    except:
                        data['added_to_watchlist'] = False
                    try:
                        t_s_obj = TopSearched.objects.get(stock=stock_obj,
                                                          userid=request.user)
                        t_s_obj.count += 1
                        t_s_obj.save()
                        # response['status'] = "removed"
                    except:
                        TopSearched.objects.get_or_create(stock=stock_obj,
                                                          userid=request.user)
                        # response['status'] = "added"
                    data['earnings_graph_data'] = False
                    # response = price_change('1D', symbol)
                    try:
                        if len(data['estimate_list']) > 0 and len(
                                data['actual_list']) > 0:
                            data['earnings_graph_data'] = True
                    except:
                        data['earnings_graph_data'] = False
                    response['status'] = "removed"
                    data['has_pos'] = "False"
                    data['stockname'] = stock_obj.name
                    if Position.objects.filter(userid=request.user,
                                               stockname=stock_obj):
                        data['has_pos'] = "True"
                    try:
                        data['stockprice'] = response['stockprice']
                    except:
                        data['stockprice'] = round(
                            si.get_live_price(stock_obj.symbol + ".NS"), 2)
                    response['line_chart_html'] = render_to_string(
                        'includes/dashboard_includes/line-chart-main.html',
                        data)
                    response['stock_market_settings_html'] = render_to_string(
                        'includes/dashboard_includes/'
                        'stock_market_settings.html',
                        data)
                    response['company_info_html'] = render_to_string(
                        'includes/dashboard_includes/company_info.html',
                        data)
                    response['scatter_plot_html'] = render_to_string(
                        'includes/dashboard_includes/'
                        'scatter-plot-chart-main.html',
                        data)
                    try:
                        response['color'] = data['color']
                    except:
                        response['color'] = "#038afe"
                    transaction_list = paginate_data(request)
                    # print(transaction_list,">???")
                    if transaction_list:
                        response['up_activity_html'] = render_to_string(
                            "includes/dashboard_includes/"
                            "upcoming_activity.html",
                            {
                                "transaction_list": transaction_list
                            })
                        response['tr_status'] = "True"
                    total_share = 0
                    try:
                        print(">>?><>>>>>>><")
                        position_obj = \
                            Position.objects.filter(userid=request.user,
                                                    stockname=stock_obj)[0]
                        try:
                            pos_stockprice = response['stockprice']
                        except:
                            pos_stockprice = round(
                                si.get_live_price(stock_obj.symbol + ".NS"), 2)
                        response2 = get_position_details(request, stock_obj,
                                                         position_obj,
                                                         pos_stockprice)
                        response['has_position'] = True
                        response2['stockprice'] = pos_stockprice
                        response['pos_table_details_html'] = render_to_string(
                            "includes/dashboard_includes/"
                            "position-table-details.html",
                            response2)
                        # response.update(response2)

                        for pos_stock in Position.objects.filter(
                                userid=request.user, stockname=stock_obj):
                            total_share += int(
                                pos_stock.transaction_details.size)

                        print("RESPONSE  ------------------------------ \n   ",
                              response['stock_num'])

                    except Exception as e:
                        print("GET STOCK DETAIL POS ERROR    ", e)
                    response['stock_num'] = total_share
                    response['has_history'] = "True"
                    # response['dashboard_html'] = render_to_string(
                    # 'dashboard.html',data)
                    # response['dashboard_html'] = render_to_string(
                    # 'dashboard.html',data)
                else:
                    response['has_history'] = "False"
            elif ajxtype == "get_stock_real_data":

                # tata_power = YahooFinance(symbol+'.NS', result_range="1d",
                # interval='1m', dropna='True').result
                current_time = datetime.datetime.now().time()
                print("???????????????????????????//", int(current_time.hour))
                if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
                    live_price = si.get_live_price(symbol + ".NS")
                    # live_price= tata_power.values.tolist()[len(
                    # tata_power.values.tolist()) - 1][0]
                    process = threading.Thread(
                        target=update_position_and_gainloss,
                        args=(live_price, symbol, request.user,))
                    process.start()
                    process.join()
                    response['data'] = float(str(num_quantize(live_price)))
                    response['status'] = True
                elif int(current_time.hour) == 15:
                    if int(current_time.minute) <= 30:
                        live_price = si.get_live_price(symbol + ".NS")
                        process = threading.Thread(
                            target=update_position_and_gainloss,
                            args=(live_price, symbol, request.user,))
                        process.start()
                        process.join()
                        # live_price = tata_power.values.tolist()[len(
                        # tata_power.values.tolist()) - 1][0]
                        response['data'] = float(str(num_quantize(live_price)))
                        response['status'] = True
                    else:
                        response['status'] = False
                else:
                    response['status'] = False
                # from custom_packages.yahoo_finance import YahooFinance
                # latest_price = YahooFinance(symbol + '.NS', result_range='1d',
                #                             interval='1m',
                #                             dropna='True').result
                # print(latest_price)
                # price_list = latest_price.values.tolist()
                # last_price = price_list[len(price_list) - 1][0]
                # random_num = [1775.95, 1779.30, 1776.42, 1775.23, 1775.95,
                #               1779.30, 1776.42, 1775.23]
                # response['data'] = random.choice(random_num)
                #
                # response['data'] = si.get_live_price(symbol + ".NS")
                # response['status'] = True
            elif ajxtype == "get_watched_stock_real_data":
                symbols = request.GET.getlist("symbols[]")
                prices = []
                for symbol in symbols:
                    live_price = si.get_live_price(symbol + ".NS")
                    monthly_data = si.get_data(symbol + ".NS", interval="1d")
                    # print("_____    ", monthly_data.values.tolist())
                    price_list = monthly_data.values.tolist()
                    prev_day_price = price_list[len(price_list) - 2][4]
                    difference = live_price - prev_day_price
                    # percentage = (live_price / prev_day_price) * 100

                    color = '#ff5000'
                    if float(difference) > 0:
                        color = '#01ec36'
                        difference = "+" + str(difference)
                    difference = num_quantize(float(difference))
                    difference = str(difference)
                    prices.append(
                        {'symbol': symbol, 'price': round(live_price, 2),
                         'difference': difference, 'color': color})
                response['data'] = prices

            elif ajxtype == "add-to-watchlist":
                symbol = request.GET.get("symbol")
                stock_obj = StockNames.objects.get(symbol=symbol)
                try:
                    TopSearched.objects.get(stock=stock_obj,
                                            userid=request.user).delete()
                    response['status'] = "removed"
                except:
                    TopSearched.objects.create(stock=stock_obj,
                                               userid=request.user)
                    response['status'] = "added"
                # top_search_obj.userid = request.user
                # top_search_obj.count += 1
                # top_search_obj.save()

            elif ajxtype == "price_change":
                key = request.GET.get("key")
                live_price = request.GET.get("live_price")
                prev_price = request.GET.get("prev_price")

                response = price_change(key, symbol, live_price, prev_price)

            elif ajxtype == "buy_stock":
                symbol = request.GET.get("symbol")
                expires = request.GET.get("expires")
                order_type = request.GET.get("order_type")
                share = request.GET.get("share")
                current_price = request.GET.get("current_price")
                limit_price = request.GET.get("limit_price")
                print(current_price, limit_price)
                stock = StockNames.objects.get(symbol=symbol)
                current_date = datetime.datetime.now()
                remove_date = datetime.datetime.now()

                if request.user.is_authenticated:
                    user = UserDetails.objects.get(user=request.user)
                    identity = IdentityDetails.objects.get(id=user.identity.id)
                    user_buyingpower = float(user.identity.buyingpower)

                    if expires == "1":
                        expires_val = "Good for day"

                    else:
                        expires_val = "Good till canceled"

                    if order_type == "market_order":
                        transaction_obj, status = \
                            Transaction.objects.get_or_create(
                                stockticker=stock,
                                ordertype=order_type, transaction_type="buy",
                                price=current_price, size=share,
                                userid=request.user,
                                expires=expires_val)

                    else:

                        transaction_obj = Transaction.objects.create(
                            stockticker=stock, ordertype=order_type, transaction_type="buy",
                            price=current_price, size=share,
                            userid=request.user, expires=expires_val)

                    if expires != "1":
                        transaction_obj.remove_date = current_date + \
                                                      datetime.timedelta(
                                                          days=90)

                        transaction_obj.save()

                    current_time = current_date.time()

                    flag = 0

                    print("current_time.hour  ", current_time.hour)

                    if int(current_time.hour) >= 9 and int(
                            current_time.hour) < 15:

                        flag = 1

                    elif int(current_time.hour) == 15:

                        if int(current_time.minute) <= 30:
                            flag = 1

                    # elif int(current_time.hour) > 15 or int(
                    # current_time.hour) < 9:
                    #     flag = 1

                    if order_type == "market_order":

                        if flag == 1:

                            transaction_obj.status = "executed"

                            position_obj, status = \
                                Position.objects.get_or_create(
                                    userid=request.user, stockname=stock,
                                    ticker=symbol,
                                    price=current_price,
                                    ordertype=order_type)

                            position_obj.transaction_details = transaction_obj

                            position_obj.save()

                            try:

                                history_obj = \
                                    TransactionHistory.objects.get_or_create(
                                        position_obj=position_obj,
                                        stock_number=share, status="buy")
                            except:
                                pass

                            # try:

                            total_cash = float(current_price) * int(share)

                            gl_history = GainLossHistory.objects.create(
                                userid=request.user, stock=stock,
                                total_cash=total_cash)

                            gl_history.unrealised_gainloss = num_quantize(

                                (float(current_price) - float(
                                    position_obj.transaction_details.price)) * int(
                                    share))

                            gl_history.position_obj = position_obj
                            gl_history.save()
                            user_buyingpower -= total_cash
                            identity.buyingpower = user_buyingpower
                            identity.save()
                        else:

                            transaction_obj.status = "pending"

                    elif order_type == "limit_order":

                        transaction_obj.limit_price = limit_price

                    transaction_obj.save()

            elif ajxtype == "table_paginate":
                transaction_list = paginate_data(request)
                if transaction_list:
                    response['up_activity_html'] = render_to_string(
                        "includes/dashboard_includes/upcoming_activity.html", {
                            "transaction_list": transaction_list
                        })
                    response['tr_status'] = "True"

            elif ajxtype == "delete_transaction_data":
                Transaction.objects.get(id=request.GET.get("id")).delete()
                # position_obj_list = []
                # for position_obj in Position.objects.filter(
                # userid=request.user):
                #     stock_obj = StockNames.objects.get(symbol=symbol)
                #     datas = stock_obj.history.history_json['data']
                #     data = {
                #         "date":position_obj.transaction_details.time,
                #         "ordertype":position_obj.ordertype,
                #         "size":position_obj.transaction_details.size,
                #         "price":position_obj.transaction_details.price,
                #         "current_price":datas.get("stock_price"),
                #         "gainloss":position_obj.unrealised_gainloss,
                #         "symbol":position_obj.ticker,
                #     }
                #     position_obj_list.append(data)

            elif ajxtype == "sell-stock":
                symbol = request.GET.get("symbol")
                share_num = int(request.GET.get("share_num"))
                current_price = si.get_live_price(symbol + ".NS")
                user_obj = UserDetails.objects.get(user=request.user)
                identity_obj = IdentityDetails.objects.get(
                    id=user_obj.identity.id)
                buyingpower = float(identity_obj.buyingpower)
                for pos_obj in Position.objects.filter(userid=request.user,
                                                       ticker=symbol).order_by(
                    "id"):
                    print("share_num    ", share_num)

                    stock_num = int(pos_obj.transaction_details.size)
                    print("stock_num    ", stock_num)

                    if stock_num == share_num:
                        stock_num -= share_num
                        pos_obj.transaction_details.size = stock_num
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
                            realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(share_num)
                            gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                            temp_var = num_quantize(gl_obj.realised_gainloss)
                            temp_var = temp_var + num_quantize(realised_gainloss)
                            gl_obj.realised_gainloss = temp_var
                            buyingpower += realised_gainloss
                            print(
                                ",,,,,,,,,,,,,,,,1111111111      buyingpower",
                                buyingpower,
                                num_quantize(realised_gainloss))
                            gl_obj.save()

                        except:
                            pass
                    elif stock_num > share_num:
                        # share_num = stock_num - share_num
                        stock_num -= share_num
                        pos_obj.transaction_details.size = stock_num
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
                            realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(share_num)
                            gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                            temp_var = num_quantize(gl_obj.realised_gainloss)
                            temp_var = temp_var + num_quantize(realised_gainloss)
                            gl_obj.realised_gainloss = temp_var
                            buyingpower += realised_gainloss
                            print(
                                ",,,,,,,,,,,,,,,,2222222222222    buyingpower",
                                buyingpower,
                                num_quantize(realised_gainloss))
                            gl_obj.save()
                        except Exception as e:
                            print("ERRORRRR  SELL STOCK  ", e)
                            pass
                        break
                    else:
                        share_num = share_num - stock_num
                        pos_obj.transaction_details.size = 0
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
                            realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(share_num)
                            gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                            temp_var = num_quantize(gl_obj.realised_gainloss)
                            temp_var = temp_var + num_quantize(realised_gainloss)
                            gl_obj.realised_gainloss = temp_var
                            buyingpower += realised_gainloss
                            print(
                                ",,,,,,,,,,,,,,,,33333333333      buyingpower",
                                buyingpower,
                                num_quantize(realised_gainloss))
                            gl_obj.save()
                        except:
                            pass
                    print("===========share_num    ", share_num)
                    print("===========stock_num    ", stock_num)
                    # pos_obj.save()
                    if int(pos_obj.transaction_details.size) == 0:
                        print("###########    REMAINING SHARE    ",
                              pos_obj.transaction_details.size)
                        pos_obj.delete()
                    print("BUYYYING POWERRRR   ", buyingpower)
                identity_obj.buyingpower = num_quantize(buyingpower)
                identity_obj.save()

            # elif ajxtype == "chart_sort_gainloss":
            #     sort_type = request.GET.get("sort_type")
            #     try:
            #         buyingpower = UserDetails.objects.get(
            #             user=request.user).identity.buyingpower
            #     except:
            #         buyingpower = 0
            #     value_list = []
            #     if sort_type == "1m":
            #         last_month = ""
            #         for t_gl_obj in TotalGainLoss.objects.filter(
            #                 userid=request.user,
            #                 created_at__lte=datetime.datetime.now(),
            #                 created_at__gte=last_month):
            #             print("::::  ", t_gl_obj.gainloss)
            #             tgl_date = datetime.datetime.timestamp(
            #                 t_gl_obj.created_at)
            #             value_list.append([int(tgl_date) * 1000,
            #                                float(t_gl_obj.gainloss) + float(
            #                                    buyingpower)])
            #     elif sort_type == "3m":
            #         pass
            #     elif sort_type == "6m":
            #         pass
            #     elif sort_type == "1y":
            #         pass
            #     else:
            #         pass
            return HttpResponse(json.dumps(response),
                                content_type="application/json")
        except Exception as e:
            pass


class DashboardHistoricalAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            interval = request.GET.get("interval", "1D")

            cached_values = cache.get(f"{request.user.id}_historical_{interval}")
            cached_values_expiry = cache.get(f"{request.user.id}_historical_{interval}_expiry")

            if interval != "1D":
                now = datetime.datetime.now()
                # Check if we have a valid cache data
                if cached_values and now < cached_values_expiry:
                    # if it's in range of 21:00:00 and 21:00:59, send non cached values, else, send cached values.
                    # This will ensure proper refreshing of cache when a non-deletable row is added for the user.
                    if now.hour != 21 and now.minute != 0:
                        _, live_gl = portfolio_open_value(request.user, interval)
                        cached_values['live_gl'] = live_gl
                        cached_values['cached'] = True
                        return ResponseOk(cached_values)

            deletable = False
            if interval == "1D":
                deletable = True
                if is_market_opened_date():
                    # is market opened today or going to open today
                    if datetime.datetime.now().time() >= datetime.time(hour=9, minute=30):
                        # Market is opened now
                        start, end = get_day_range(business_hours_only=True)
                    else:
                        # Market is not opened yet. So, display previous day data
                        start, end = get_day_range(get_previous_business_day(), business_hours_only=True)
                else:
                    start, end = get_day_range(get_previous_business_day(), business_hours_only=True)
            elif interval == "1m":
                # _, end = get_day_range(datetime.datetime.now())
                # start = end - relativedelta(months=1)
                _, end = get_day_range(datetime.datetime.now())
                start = end - relativedelta(months=1)
                _, end = get_day_range(get_previous_business_day())
            elif interval == "3m":
                # _, end = get_day_range(datetime.datetime.now())
                # start = end - relativedelta(months=3)
                _, end = get_day_range(datetime.datetime.now())
                start = end - relativedelta(months=3)
                _, end = get_day_range(get_previous_business_day())
            elif interval == "6m":
                # _, end = get_day_range(datetime.datetime.now())
                # start = end - relativedelta(months=6)
                _, end = get_day_range(datetime.datetime.now())
                start = end - relativedelta(months=6)
                _, end = get_day_range(get_previous_business_day())
            elif interval == "1y":
                # _, end = get_day_range(datetime.datetime.now())
                # start = end - relativedelta(years=1)
                _, end = get_day_range(datetime.datetime.now())
                start = end - relativedelta(years=1)
                _, end = get_day_range(get_previous_business_day())
            elif interval == "5y":
                # _, end = get_day_range(datetime.datetime.now())
                # start = end - relativedelta(years=5)
                _, end = get_day_range(datetime.datetime.now())
                start = end - relativedelta(years=5)
                _, end = get_day_range(get_previous_business_day())

            # For intraday get deletable values but for other interval get non-deleatable values.
            values = PortfolioValues.objects.filter(
                user=request.user, timestamp__gte=start, timestamp__lte=end, deletable=deletable
            ).order_by("timestamp")
            df = pd.DataFrame(values.values())

            if interval == "1D":
                # values = values.annotate(
                #     i=Window(expression=Rank(), order_by=F("timestamp").asc())
                # ).annotate(i2=F('i') - 1).values("timestamp", "portfolio_value", "i2")
                # df = pd.DataFrame(values.values())
                # print(df)
                if not df.empty:
                    df['gl'] = df['realized_gain_loss'] + df['unrealized_gain_loss']
            else:
                if not values.exists():
                    r = []
                    r2 = []
                    x = start.date()
                    while x <= end.date():
                        r.append([
                            datetime.datetime.combine(x, datetime.time.min).timestamp() * 1000, 0.0
                        ])
                        r2.append([
                            datetime.datetime.combine(x, datetime.time.min).timestamp() * 1000, 0.0
                        ])
                        x = x + datetime.timedelta(days=1)

                    return ResponseOk({
                        "data": r,      # portfolio
                        "data2": r2,
                        "greyed_out": True,
                        "empty": True,
                        "max": int(start.timestamp() * 1000),
                        "min": int(end.timestamp() * 1000)
                    })
                else:
                    df['timestamp2'] = df['timestamp'].apply(lambda x: x.date())
                    r = []
                    if start.date() != df.iloc[0]['timestamp2']:
                        # this means the data is available partially for this time range.
                        # So we'll start a loop to add the missing data by adding 0 to the portfolio value
                        x = start.date()
                        while x <= end.date():
                            d = df[df['timestamp2'] == x]
                            val, val2 = 0.0, 0.0
                            if not d.empty:
                                val = d.iloc[0]['portfolio_value']
                                val2 = d.iloc[0]['realized_gain_loss'] + d.iloc[0]['unrealized_gain_loss']

                            r.append({
                                "timestamp": datetime.datetime.combine(x, datetime.time.min),
                                "portfolio_value": val,
                                "gl": val2
                            })
                            x = x + datetime.timedelta(days=1)

                        df = pd.DataFrame(r)
                    # check for partial data.
                    pass

            if not df.empty:
                now = datetime.datetime.now()
                if now.hour in range(9, 10):
                    factor = 5
                elif now.hour in range(10, 12):
                    factor = 6
                else:
                    factor = 7

                if interval == "1D":
                    # Sampling the results in case of intraday results
                    df = df[df.index % factor == 0]

                df['timestamp'] = df['timestamp'].apply(lambda x: int(datetime.datetime.timestamp(x) * 1000))
                df2 = df[['timestamp', 'portfolio_value']]
                df3 = df[['timestamp', 'gl']]
                res = df2.values.tolist()
                res2 = df3.values.tolist()

                # Check if the data is partial or not
                if interval != "1D":
                    # save the data in the cache for non-intraday intervals.
                    cache.set(
                        f"{request.user.id}_historical_{interval}",
                        {
                            "data": res,
                            "data2": res2,
                            "max": int(start.timestamp() * 1000),
                            "min": int(end.timestamp() * 1000)
                        }
                    )
                    cache.set(
                        f"{request.user.id}_historical_{interval}_expiry",
                        get_day_range(datetime.datetime.now() + datetime.timedelta(days=1))[0]
                    )

                # if len(res) == 1:
                #     res.insert(0, [int(start.timestamp() * 1000), 0.0])
                #     res.append([int(end.timestamp() * 1000), 0.0])
            else:
                res = []
                res2 = []

            _, live_gl = portfolio_open_value(request.user, interval)

            return ResponseOk({
                "data": res,
                "data2": res2,
                "live_gl": live_gl,
                "cached": False,
                "max": int(start.timestamp() * 1000),
                "min": int(end.timestamp() * 1000)
            })
        except Exception as e:
            return ResponseBadRequest({
                "debug": str(e), "error": "Something went wrong"
            })


class PositionTablesDetailsView(TemplateView):
    template_name = 'table-stock-position-details.html'

    def get(self, request, *args, **kwargs):
        context = {}
        # position_obj_list = Position.objects.filter(
        #     userid=request.user
        # ).order_by("-id")
        # print("position_obj_list   ",position_obj_list)
        # context['position_list'] = position_obj_list
        try:
            context['current_amount'] = UserDetails.objects.get(
                user=request.user).identity.buyingpower
        except:
            context['current_amount'] = 0
        return render(request, self.template_name, context)


def get_stock_details_json(symbol, request):
    """
    :param symbol:
    :param request:
    :return:
    """
    response = {}
    stock_obj = StockNames.objects.get(symbol=symbol)

    data = stock_obj.history.history_json
    data['symbol'] = symbol
    data['stock_price_list'] = []
    # 1day
    d_data = si.get_data(symbol + ".NS", interval="1d")
    d_price_list = d_data.values.tolist()
    prev_day_price = d_price_list[len(d_price_list) - 2][4]
    response['prev_day_price'] = prev_day_price
    # 1m
    today = datetime.datetime.now()
    start_date = today.date() - dateutil.relativedelta.relativedelta(months=2)
    prev_month = today.date() - dateutil.relativedelta.relativedelta(months=1)
    m_data = si.get_data(symbol + ".NS", start_date=start_date,
                         end_date=prev_month, interval="1d")
    m_price_list = m_data.values.tolist()
    prev_month_price = m_price_list[len(m_price_list) - 1][4]
    response['prev_month_price'] = prev_month_price
    # 3m
    start_date = today.date() - dateutil.relativedelta.relativedelta(months=4)
    prev_3month = today.date() - dateutil.relativedelta.relativedelta(months=3)
    three_m_data = si.get_data(symbol + ".NS", start_date=start_date,
                               end_date=prev_3month, interval="1d")
    three_m_price_list = three_m_data.values.tolist()
    prev_3m_price = three_m_price_list[len(three_m_price_list) - 1][4]
    response['prev_3m_price'] = prev_3m_price
    # 6m
    start_date = today.date() - dateutil.relativedelta.relativedelta(months=7)
    prev_6month = today.date() - dateutil.relativedelta.relativedelta(months=6)
    six_m_data = si.get_data(symbol + ".NS", start_date=start_date,
                             end_date=prev_6month, interval="1d")
    six_m_price_list = six_m_data.values.tolist()
    prev_6m_price = six_m_price_list[len(six_m_price_list) - 1][4]
    response['prev_6m_price'] = prev_6m_price
    # 1y
    start_date = today.date() - dateutil.relativedelta.relativedelta(years=1,
                                                                     months=1)
    prev_year = today.date() - dateutil.relativedelta.relativedelta(years=1)
    y_data = si.get_data(symbol + ".NS", start_date=start_date,
                         end_date=prev_year, interval="1d")
    y_price_list = y_data.values.tolist()
    prev_y_price = y_price_list[len(y_price_list) - 1][4]
    response['prev_y_price'] = prev_y_price

    try:
        t_s_obj = TopSearched.objects.get(stock=stock_obj, userid=request.user)
        t_s_obj.count += 1
        t_s_obj.save()
        # response['status'] = "removed"
    except:
        TopSearched.objects.get_or_create(stock=stock_obj, userid=request.user)
        # response['status'] = "added"

    date = datetime.datetime.timestamp(datetime.datetime.now())

    latest_price = YahooFinance(symbol + '.NS', result_range='1d',
                                interval='1m', dropna='True').result
    # print(latest_price)
    # price_list = latest_price.values.tolist()

    count = 0
    for i, j in latest_price.iterrows():
        temp_price_list = []
        dt_object1 = datetime.datetime.strptime(str(i), "%Y-%m-%d %H:%M:%S")
        my_time = dt_object1.time()
        my_datetime = datetime.datetime.combine(i, my_time)
        date = datetime.datetime.timestamp(my_datetime)
        temp_price_list.append(int(date) * 1000)
        temp_price_list.append(latest_price.values.tolist()[count][2])
        # latest_price_list.append(temp_price_list)
        # data['stock_price_list'].append(temp_price_list)
        count += 1
    for t_gainloss in request.user.user_total_gl_rel.all():
        date = datetime.datetime.timestamp(t_gainloss.created_at)
        # temp_price_list.append(int(date) * 1000)
        data['stock_price_list'].append(
            [int(date) * 1000, float(t_gainloss.gainloss)])
    data['stockprice'] = num_quantize(si.get_live_price(symbol + ".NS"))
    print("STOCK PRICE  ----  ", data['stock_price_list'])
    return data, response


def price_change(key, symbol, live_price, prev_price):
    response = {}
    difference = 0
    percentage = 0
    color = "#ff5000"
    btn_color = "#ff5000"
    scatter_s_color = "rgba(255, 80, 0, 0.58)"
    scatter_s_color_status = False
    live_price = float(live_price)

    if not live_price or not prev_price:
        response['color'] = "#00ff39"
        response['btn_color'] = "#28a745"
        response['scatter_s_color'] = "rgba(40, 167, 69, 0.58)"
        response['scatter_s_color_status'] = True

        response['percentage'] = str(percentage)
        response['difference'] = str(difference)
        return response

    if key == '1D':
        # live_price = si.get_live_price(symbol + ".NS")
        # monthly_data = si.get_data(symbol + ".NS", interval="1d")
        # # print("_____    ", monthly_data.values.tolist())
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 2][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price / prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100
    if key == '1m':
        # live_price = si.get_live_price(symbol + ".NS")
        # today = datetime.datetime.now()
        # start_date = today.date() - dateutil.relativedelta.relativedelta(
        # months=2)
        # prev_month = today.date() - dateutil.relativedelta.relativedelta(
        # months=1)
        # monthly_data = si.get_data(symbol + ".NS", start_date=start_date,
        # end_date=prev_month, interval="1d")
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 1][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '3m':
        # live_price = si.get_live_price(symbol + ".NS")
        # today = datetime.datetime.now()
        # start_date = today.date() - dateutil.relativedelta.relativedelta(
        # months=4)
        # prev_month = today.date() - dateutil.relativedelta.relativedelta(
        # months=3)
        # # print("prev_month  ",prev_month)
        # monthly_data = si.get_data(symbol + ".NS", start_date=start_date,
        # end_date=prev_month, interval="1d")
        # # print("_____    ", monthly_data)
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 1][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '6m':
        # live_price = si.get_live_price(symbol + ".NS")
        # today = datetime.datetime.now()
        # start_date = today.date() - dateutil.relativedelta.relativedelta(
        # months=7)
        # prev_month = today.date() - dateutil.relativedelta.relativedelta(
        # months=6)
        # # print("prev_month  ",prev_month)
        # monthly_data = si.get_data(symbol + ".NS", start_date=start_date,
        # end_date=prev_month, interval="1d")
        # # print("_____    ", monthly_data)
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 1][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '1y':
        # live_price = si.get_live_price(symbol + ".NS")
        # today = datetime.datetime.now()
        # start_date = today.date() - dateutil.relativedelta.relativedelta(
        # years=1, months=1)
        # prev_month = today.date() - dateutil.relativedelta.relativedelta(
        # years=1)
        # # print("prev_month  ",prev_month,start_date)
        # monthly_data = si.get_data(symbol + ".NS", start_date=start_date,
        # end_date=prev_month, interval="1d")
        # # print("_____    ", monthly_data)
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 1][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    if key == '5y':
        # live_price = si.get_live_price(symbol + ".NS")
        # today = datetime.datetime.now()
        # start_date = today.date() - dateutil.relativedelta.relativedelta(
        # years=1, months=1)
        # prev_month = today.date() - dateutil.relativedelta.relativedelta(
        # years=1)
        # # print("prev_month  ",prev_month,start_date)
        # monthly_data = si.get_data(symbol + ".NS", start_date=start_date,
        # end_date=prev_month, interval="1d")
        # # print("_____    ", monthly_data)
        # price_list = monthly_data.values.tolist()
        # prev_day_price = price_list[len(price_list) - 1][4]
        live_price = num_quantize(live_price)
        prev_day_price = num_quantize(prev_price)
        difference = live_price - prev_day_price
        # percentage = (live_price/prev_day_price)
        percentage = ((live_price - prev_day_price) / prev_day_price) * 100

    difference = num_quantize(float(difference))
    percentage = num_quantize(float(percentage))
    if difference >= 0:
        difference = "+₹" + str(difference)
        # color = "#01ec36" #light green
        btn_color = "#28a745"
        color = "#00ff39"
        scatter_s_color = "rgba(40, 167, 69, 0.58)"
        scatter_s_color_status = True
        if percentage >= 0:
            percentage = "+" + str(abs(percentage))
        else:
            percentage = "-" + str(abs(percentage))

    response['color'] = color
    response['btn_color'] = btn_color
    response['scatter_s_color'] = scatter_s_color
    response['scatter_s_color_status'] = scatter_s_color_status
    response['percentage'] = str(percentage)
    response['difference'] = str(difference)
    if "₹" not in str(difference):
        if difference < 0:
            response['difference'] = "-₹" + str(abs(difference))
        else:
            response['difference'] = "₹" + str(difference)

    print(response)
    return response


def logout_user(request):
    logout(request)
    return redirect("/")


def get_earnings(symbol, key, type):
    token = tokens.TOKEN_EOD_HISTORICAL_DATA
    a = requests.get(
        "https://eodhistoricaldata.com/api/fundamentals/"
        "{}.NSE?api_token={}".format(
            symbol, token))
    js = json.loads(a.text)

    if type == "company_info":
        # print ( js.get("General"))
        info = js.get("General").get("Description")
        head_post = js.get("General").get("Officers").get("0").get("Title")
        head_name = js.get("General").get("Officers").get("0").get("Name")
        Headquarters = js.get("General").get("Address")
        officer_list = []
        for i, j in js.get("General").get("Officers").items():
            officer_dict = {
                'name': j.get("Name"),
                'title': j.get("Title")
            }
            officer_list.append(officer_dict)
        details_dict = {
            'about': info,
            'head_post': head_post,
            'head_name': head_name,
            'officer_list': officer_list,
            'Headquarters': Headquarters
        }
        result = details_dict
        # print (js.get("General"))
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


def paginate_data(request, stock_symbol=None):
    symbol = request.GET.get("symbol")
    if not request.GET.get("symbol"):
        symbol = stock_symbol
    stock_obj = StockNames.objects.get(symbol=symbol)
    user_list = Transaction.objects.filter(userid=request.user,
                                           stockticker=stock_obj,
                                           status="pending")
    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, 5)

    try:
        transaction_list = paginator.page(page)
    except PageNotAnInteger:
        transaction_list = paginator.page(1)
    except EmptyPage:
        transaction_list = paginator.page(paginator.num_pages)
    return transaction_list


def get_position_details(request, stock_obj, position_obj, stock_price):
    context = {}
    transaction_list = paginate_data(request, stock_symbol=stock_obj.symbol)
    if transaction_list:
        context['up_activity_html'] = render_to_string(
            "includes/dashboard_includes/upcoming_activity.html", {
                "transaction_list": transaction_list
            })
        context['tr_status'] = "True"
    # context['position_details'] = position_obj
    share_num = 0
    total_cost = 0
    data = {}
    for pos in Position.objects.filter(userid=request.user,
                                       stockname=position_obj.stockname):
        if pos.transaction_details:
            share_num += int(pos.transaction_details.size)
            total_cost += float(pos.transaction_details.price) * int(
                pos.transaction_details.size)
    if share_num > 0 and total_cost > 0:
        average_cost = float(total_cost / share_num)
        context['average_cost'] = str(num_quantize(average_cost))
        context['share_num'] = str(share_num)
        total_return = 0
        # print ("FILTERED   ",Position.objects.filter(userid=request.user,
        # stockname=stock_obj))
        try:
            for pos_obj in Position.objects.filter(userid=request.user,
                                                   stockname=stock_obj):
                # print("pos_obj.unrealised_gainloss   ",
                # pos_obj.unrealised_gainloss)
                if pos_obj.unrealised_gainloss:
                    total_return += float(pos_obj.unrealised_gainloss)
        except Exception as e:
            print("TOTAL RETURN ERROR    ", e)
            pass
        total_ret_perc = num_quantize((total_return / total_cost) * 100)
        # if total_return >= 0:
        #     total_return = "+"+str(total_return)
        #     total_ret_perc = "+"+str(total_ret_perc)
        # else:
        #     total_return = "-" + str(total_return)
        #     total_ret_perc = "-" + str(total_ret_perc)
        context['total_return'] = total_return
        context['total_return_percentage'] = total_ret_perc

        # context['pos_table_details_html'] = render_to_string(
        # "includes/dashboard_includes/position-table-details.html",data)
        # print("total_return   ",total_return)
        # context['today_return'] = num_quantize((float(stock_price) -
        # average_cost) / average_cost)
    # print("context   ",context)
    return context


def get_latest_gainloss(request):
    try:
        buyingpower = UserDetails.objects.get(
            user=request.user).identity.buyingpower
    except:
        buyingpower = 0
    total_gl = 0

    for position_obj in request.user.userposition_rel.all():
        # current_price = si.get_live_price(position_obj.stockname.symbol +
        # ".NS")
        # total_gl += float(gl_obj.unrealised_gainloss)
        # total_gl += num_quantize(
        #     (float(current_price) - float(
        #     position_obj.transaction_details.price)) * int(
        #         position_obj.transaction_details.size))
        total_gl += float(position_obj.price)
    # date = datetime.datetime.timestamp(datetime.datetime.now())
    # print("?>?>?>?    ", float(total_gl) + float(buyingpower))
    return num_quantize(float(total_gl) + float(buyingpower))


def update_position_and_gainloss(current_price, symbol, user):
    # total_price = 0
    # date = datetime.datetime.timestamp(datetime.datetime.now())
    # value_list = []
    for pos_obj in Position.objects.filter(stockname__symbol=symbol,
                                           userid=user):
        try:
            gl_history = GainLossHistory.objects.get(position_obj=pos_obj)
            gl_history.unrealised_gainloss = num_quantize(
                (float(current_price) - float(
                    pos_obj.transaction_details.price)) * int(
                    pos_obj.size))
            gl_history.save()
        except Exception as e:
            print("ERROR in update_position_and_gainloss FUNCTION", e)
            if "GainLossHistory matching query does not exist" in str(e):
                gl_history = GainLossHistory.objects.create(position_obj=pos_obj)
                gl_history.unrealised_gainloss = num_quantize(
                    (float(current_price) - float(
                        pos_obj.transaction_details.price)) * int(
                        pos_obj.size))
                gl_history.save()
        # total_price += num_quantize(float(pos_obj.price))
    # value_list.append([int(date) * 1000, float(total_price)])
    # if not GainLossChartData.objects.filter(userid=user):
    #     # print("value_listvalue_list    ",value_list)
    #     gl_obj = GainLossChartData.objects.create(userid=user)
    #     gl_obj.gainloss_data = value_list
    #     gl_obj.save()
    # else:
    #     gl_obj = GainLossChartData.objects.get(userid=user)
    #     gl_obj.gainloss_data.append([int(date) * 1000, float(total_price)])
    #     gl_obj.save()


class StockPageView(TemplateView):
    template_name = 'dashboardv1.html'

    def get(self, request, *args, **kwargs):
        zerodha = getattr(settings, "ZERODHA_CREDENTIALS")
        start, _ = get_day_range(business_hours_only=False)
        context = {
            "market_opened_today": 1 if is_market_opened_date() else 0,
            "market_opened_now": 1 if is_market_open_now() else 0,
            "min": int(start.timestamp() * 1000),
            "avg_cost": 0.0,
            "share_total": 0,
            "portfolio_diversity": 0.0,
            "market_value": 0.0,
            "total_return": 0.0,
            "total_return_percent": 0.0,
            "today_return": 0.0,
            "today_return_percent": 0.0,
            "added_to_watchlist": True
        }
        stock_symbol = self.kwargs['stock_symbol']
        symbol = stock_symbol.split(':')[1]
        exchange = stock_symbol.split(':')[0]
        context['symbol'] = symbol
        context['is_auth'] = 1 if request.user.is_authenticated else 0

        # the first stock of the day would be at last
        # the latest stock would be at first
        # UNOPTIMISED VERSION
        # stock = StockPrices.objects.filter(symbol__iexact=symbol).order_by("time_stamp").last()
        # initial = stock.first()

        s = Singleton2.get_instance("1")

        context['has_pos'] = False
        context['share_total'] = 0

        # First, read from cache, if it's available in the cache and is a valid entry, then do not read the db
        profile = cache.get(f'{symbol}_profile')
        profile_cache_updated = cache.get(f'{symbol}_profile_updated')

        if not profile or (datetime.datetime.now() - profile_cache_updated).total_seconds() >= 12 * 3600:
            try:
                profile = StockGeneralInfo.objects.filter(symbol=symbol).first()
            except Exception as erc:
                profile = None

            cache.set(f'{symbol}_profile', profile)
            cache.set(f'{symbol}_profile_updated', datetime.datetime.now())

        if request.user.is_authenticated:
            positions = Position.objects.filter(
                userid=request.user
            ).filter(
                stockname__symbol=symbol
            ).aggregate(
                count=Sum("size")
            )
            if not positions:
                positions = 0
            else:
                positions = positions.get("count", 0)

            if not positions:
                positions = 0

            context['has_pos'] = True if positions else 0
            context['share_total'] = positions

            # kws = KiteConnect(api_key=zerodha.get("api_key"))
            # try:
            #     instruments = kws.instruments(exchange=exchange)
            # except:
            #     instruments = kws.instruments(exchange=exchange)
            # for i in instruments:
            #     if i['tradingsymbol'].upper() == symbol.upper():
            #         context['token'] = i['instrument_token']
            #         break

            context['symbol'] = symbol
            stock_obj = StockNames.objects.get(symbol=symbol)
            context['token'] = stock_obj.token
            if is_market_opened_date():
                live_price, _ = parse_tick_data(s.tick_data, int(stock_obj.token))
            else:
                try:
                    df = si.get_data(symbol + ".NS").to_dict("records")[-2:]
                    live_price = df[1]['close']
                except Exception as eee:
                    print("eee ", eee)
                    live_price = None

            print("LIVE PRICE", live_price)
            print("LIVE PRICE", live_price)
            print("LIVE PRICE", live_price)
            print("LIVE PRICE", live_price)
            print("LIVE PRICE", live_price)

            if live_price:
                if positions:
                    avg_cost, _, total_return, total_return_percent, today_return, today_return_percent, \
                        portfolio_diversity = get_average_cost(request.user, symbol, live_price)
                    context['avg_cost'] = avg_cost
                    context['portfolio_diversity'] = portfolio_diversity
                    context['total_return'] = total_return
                    context['total_return_percent'] = total_return_percent
                    context['today_return'] = today_return
                    context['today_return_percent'] = today_return_percent

                r = {}
                get_previous_day_close_price(symbol + ".NS", r, "1d")
                context['market_value'] = float(context['share_total'] * live_price)
                print("435345345 345345", live_price, r['1d'])
                print("435345345 345345", live_price, r['1d'])
                print("435345345 345345", live_price, r['1d'])
                print("435345345 345345", live_price, r['1d'])
                context['intraday_change'] = price_change(
                    '1D', symbol, live_price=live_price, prev_price=r['1d']
                )

            # cc = StockHistory.objects.get(stock=stock_obj).history_json
            # print("eeeee eeee", StockHistory.objects.filter(stock=stock_obj).exists())

            # Unoptimised version
            # if StockHistory.objects.filter(stock=stock_obj):
            #
            #     data = stock_obj.history.history_json['data']
            #     response = stock_obj.history.history_json['response']
            #     # tttt = get_stock_details_json(symbol,request)
            #
            #     latest_price = YahooFinance(symbol + '.NS',
            #                                 result_range='1d',
            #                                 interval='1m',
            #                                 dropna='True').result
            #     # price_list = latest_price.values.tolist()
            #     current_time = datetime.datetime.now().time()
            #     count = 0
            #     stock_price_list = []
            #     for i, j in latest_price.iterrows():
            #         temp_price_list = []
            #         dt_object1 = datetime.datetime.strptime(str(i), "%Y-%m-%d %H:%M:%S")
            #         my_time = dt_object1.time()
            #         my_datetime = datetime.datetime.combine(i, my_time)
            #         date = datetime.datetime.timestamp(my_datetime)
            #
            #         temp_price_list.append(int(date) * 1000)
            #         temp_price_list.append(
            #             latest_price.values.tolist()[count][2])
            #         # print(temp_price_list)
            #         # latest_price_list.append(temp_price_list)
            #         data['stock_price_list'].append(temp_price_list)
            # else:
            #     data = {
            #         "stock_price_list": []
            #     }

            # Optimised version
            data = {
                "stock_price_list": []
            }
            context['stock_price_lists'] = data['stock_price_list']

            # position_obj = request.user.userposition_rel.first()
            # if position_obj:
            #     stock_obj = StockNames.objects.get(
            #         symbol=position_obj.stockname.symbol)
            #     context = stock_obj.history.history_json['data']
            #     # response = stock_obj.history.history_json['response']
            #     context['has_position'] = True
            #     print("????????????????    ", position_obj.stockname.symbol)
            #     try:
            #         d_data = si.get_data(position_obj.stockname.symbol + ".NS",
            #                              interval="1d")
            #         d_price_list = d_data.values.tolist()
            #         prev_day_price = d_price_list[len(d_price_list) - 2][4]
            #         context['prev_day_price'] = prev_day_price
            #     except:
            #         pass
            #     try:
            #         stockprice = context.get('stockprice')
            #     except:
            #         stockprice = round(
            #             si.get_live_price(stock_obj.symbol + ".NS"), 2)
            #         context['stockprice'] = stockprice
            #     context2 = get_position_details(request, stock_obj,
            #                                     position_obj, stockprice)
            #     context.update(context2)
            #     # response['prev_day_price'] = prev_day_price
            # else:
            #     context['stock_price_list'] = [0, 0]
            #     context['stockprice'] = 0
            value_list = []
            try:
                buying_power = UserDetails.objects.get(user=request.user).identity.buyingpower
            except:
                buying_power = 0
            print("buying_power ", buying_power)
            date = datetime.datetime.timestamp(datetime.datetime.now())
            choice_arr = []
            start_date = datetime.date(2019, 1, 1)
            end_date = datetime.date(2020, 8, 16)

            time_between_dates = end_date - start_date
            days_between_dates = time_between_dates.days
            distict_arr = []

            # TotalGainLoss.objects.all().delete()
            # for i in range(0, 366):
            #     while True:
            #         random_number_of_days = random.randrange(
            #             days_between_dates)
            #         if not random_number_of_days in distict_arr:
            #             distict_arr.append(random_number_of_days)
            #             break
            #     random_date = start_date + datetime.timedelta(days=i)
            #     if len(TotalGainLoss.objects.filter(
            #             userid=request.user)) < 366:
            #         # for j in range(0, 5):
            #         tgl_obj = TotalGainLoss.objects.create(
            #         userid=request.user)
            #         tgl_obj.gainloss = random.randint(0, 100)
            #         # start_date_time = datetime.datetime.combine(
            #         random_date, datetime.datetime.now().time())
            #         date_time = datetime.datetime.now() -
            #         dateutil.relativedelta.relativedelta(
            #             hours=random.randint(0, 5),
            #             minutes=random.randint(0, 59))
            #         tgl_obj.created_at = datetime.datetime.combine(
            #         random_date, datetime.datetime.now().time())
            #         print("??????////   ",
            #               datetime.datetime.now() -
            #               dateutil.relativedelta.relativedelta(
            #                   hours=random.randint(0, 5),
            #                   minutes=random.randint(0, 59)))
            #         tgl_obj.save()
            #     else:
            #         break
            # for pos_obj in Position.objects.filter(userid=request.user):
            #     date = datetime.datetime.timestamp(pos_obj.created_at)
            # stock_obj = StockNames.objects.get(
            # symbol=pos_obj.stockname.symbol)
            # data = stock_obj.history.history_json['data']
            # response = stock_obj.history.history_json['response']
            # try:
            #     pos_stockprice = data['stockprice']
            # except:
            #     pos_stockprice = round(
            #         si.get_live_price(stock_obj.symbol + ".NS"), 2)
            # temp_price_list.append(int(date) * 1000)
            # value_list.append(
            #     [int(date) * 1000, float(pos_obj.price) + float(
            #     buyingpower)])
            # print("value_listvalue_list    ", value_list)
            # try:
            current_date = datetime.datetime.now()
            current_time = current_date.time()
            timeflag = 0
            if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
                timeflag = 1
            elif int(current_time.hour) == 15:
                if int(current_time.minute) <= 30:
                    timeflag = 1
            if timeflag == 1:
                try:
                    # Unoptimised
                    # gl_obj = GainLossChartData.objects.get(userid=request.user)
                    # value_list = [[x[0], float(x[1]) + float(buying_power)] for
                    #               x in gl_obj.gainloss_data]

                    # optimised
                    value_list = []

                except:
                    # unoptimised
                    # value_list = []
                    # if TotalGainLoss.objects.filter(userid=request.user):
                    #     for t_gl_obj in TotalGainLoss.objects.filter(
                    #             userid=request.user):
                    #         # print("::::  ",t_gl_obj.gainloss)
                    #         tgl_date = datetime.datetime.timestamp(
                    #             t_gl_obj.created_at)
                    #         value_list.append([int(tgl_date) * 1000, float(
                    #             t_gl_obj.gainloss) + float(buying_power)])

                    # optimised
                    value_list = []
            else:
                # Unoptimised version
                # if TotalGainLoss.objects.filter(userid=request.user):
                #     for t_gl_obj in TotalGainLoss.objects.filter(
                #             userid=request.user):
                #         # print("::::  ",t_gl_obj.gainloss)
                #         tgl_date = datetime.datetime.timestamp(
                #             t_gl_obj.created_at)
                #         value_list.append([int(tgl_date) * 1000,
                #                            float(t_gl_obj.gainloss) + float(
                #                                buying_power)])

                # Optimised version
                value_list = []
            # print("><><><<<    ",value_list)
            # print("value_list--   ",value_list)
            # value_list = gl_obj.gainloss_data
            # except:
            #     value_list = []
            # if not GainLossChartData.objects.filter(userid=request.user):
            #     gl_obj = GainLossChartData.objects.create(
            #     userid=request.user)
            #     gl_obj.gainloss_data = value_list
            #     gl_obj.save()
            # else:
            #     gl_obj = GainLossChartData.objects.get(userid=request.user)
            #     current_date = datetime.datetime.now()
            #     if gl_obj.created_at.date() != current_date.date():
            #         gl_obj.delete()
            #         gl_obj = GainLossChartData.objects.create(
            #         userid=request.user)
            #         gl_obj.gainloss_data = value_list
            #         gl_obj.save()

            context['stock_price_list'] = value_list
            context['current_amount'] = buying_power
            # context['stockprice'] = value_list[-1][1] if value_list else 0.00
            context['stockprice'] = s.parse_tick_data(symbol)[0]

            # if stock:
            #     context['stockprice'] = stock.price
            # else:
            #     context['stockprice'] = s.parse_tick_data(symbol)[0]

        else:
            context['stock_price_list'] = [0, 0]
            context['stockprice'] = s.parse_tick_data(symbol)[0]

            # if stock:
            #     context['stockprice'] = stock.price
            # else:
            #     context['stockprice'] = s.parse_tick_data(symbol)[0]

        # try:
        #     context['stockprice'] = num_quantize(context['stockprice'])
        # except:
        #     print("{{{   0",stock_obj.symbol)
        #     try:
        #         context['stockprice'] = num_quantize(round(
        #         si.get_live_price(stock_obj.symbol + ".NS"), 2))
        #     except:
        #         context['stockprice'] = 0
        # update_live_price()
        nse = Nse()
        if request.user.is_authenticated:
            searched = TopSearched.objects.filter(
                userid=request.user
            ).filter(
                stock__symbol=symbol
            ).first()

            if not searched:
                context['added_to_watchlist'] = False
            else:
                context['added_to_watchlist'] = True

            # top_searched = TopSearched.objects.filter(userid=request.user)
            # if len(top_searched) > 10:
            #     top_searched = top_searched[:10]
            context['top_searched'] = []

        lenn = 0
        sym = ''
        # for i in StockHistory.objects.all():
        #     if len(i.current_data) > 5 and i.history_json['stock_price_list']:
        #         if lenn < len(i.current_data):
        #             lenn = len(i.current_data)
        #             sym = i.stock.symbol

        # import requests
        # go_to_url = "https://www1.nseindia.com/live_market/
        # dynaContent/live_analysis/gainers/niftyGainers1.json"
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64)
        #     AppleWebKit/537.36 (KHTML, like Gecko)
        #     Chrome/56.0.2924.76 Safari/537.36',
        #     "Upgrade-Insecure-Requests": "1", "DNT": "1",
        #     "Accept": "text/html,application/xhtml+xml,
        #     application/xml;q=0.9,*/*;q=0.8",
        #     "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip,
        #     deflate"}
        # resp = requests.get(go_to_url,headers=headers)
        # print("RRRR   ",resp,resp.json())
        # context['top_gainers'] = resp.json()
        # print("............      ",nse.get_top_gainers()[:5])
        # context['top_gainers'] = nse.get_top_gainers()[:5]
        # context['top_gainers'] = nse.get_top_gainers()
        # print("top_gainers ", context['top_gainers'])

        if profile and profile.market_cap is not None:
            market_cap = human_format(profile.market_cap)
        else:
            market_cap = u"\u2014"

        if profile and profile.average_volume is not None:
            average_volume = human_format(profile.average_volume)
        else:
            average_volume = u"\u2014"

        hq = u"\u2014"
        if profile and profile.country:
            if profile.city:
                hq = profile.city + ", " + profile.country
            else:
                hq = profile.country

        context['profile'] = {
            "description": profile.description if profile and profile.description else u"\u2014",
            "ceo": profile.ceo if profile and profile.ceo else u"\u2014",
            "employees": profile.employees if profile and profile.employees else u"\u2014",
            "city": profile.city if profile and profile.city else u"\u2014",
            "country": profile.country if profile and profile.country else u"\u2014",
            "hq": hq if hq else u"\u2014",
            "founded": profile.founded if profile and profile.founded else u"\u2014",
            "market_cap": market_cap if market_cap else u"\u2014",
            "price_earning_ratio": "{0:,.2f}".format(profile.price_earning_ratio) if profile and profile.price_earning_ratio else u"\u2014",
            "dividend_yield": "{0:,.2f}".format(profile.dividend_yield) if profile and profile.dividend_yield else u"\u2014",
            "average_volume": average_volume if average_volume else u"\u2014",
        }

        prices = get_all_open_prices(symbol+".NS")
        context['open_price_1d'] = prices['1d']
        context['open_price_1m'] = prices['1m']
        context['open_price_3m'] = prices['3m']
        context['open_price_6m'] = prices['6m']
        context['open_price_1y'] = prices['1y']
        context['open_price_5y'] = prices['5y']

        # if request.is_ajax():
        #     response = {}
        #     ajxtype = request.GET.get("type")
        #     symbol = request.GET.get("symbol")
        #
        #     if ajxtype == "get_stock_details":
        #         stock_obj = StockNames.objects.get(symbol=symbol)
        #         cc = StockHistory.objects.get(stock=stock_obj).history_json
        #         if StockHistory.objects.filter(stock=stock_obj):
        #
        #             data = stock_obj.history.history_json['data']
        #             response = stock_obj.history.history_json['response']
        #             # tttt = get_stock_details_json(symbol,request)
        #
        #             latest_price = YahooFinance(symbol + '.NS',
        #                                         result_range='1d',
        #                                         interval='1m',
        #                                         dropna='True').result
        #             # price_list = latest_price.values.tolist()
        #             current_time = datetime.datetime.now().time()
        #             count = 0
        #             for i, j in latest_price.iterrows():
        #                 temp_price_list = []
        #                 dt_object1 = datetime.datetime.strptime(str(i),
        #                                                         "%Y-%m-%d"
        #                                                         " %H:%M:%S")
        #                 my_time = dt_object1.time()
        #                 my_datetime = datetime.datetime.combine(i, my_time)
        #                 date = datetime.datetime.timestamp(my_datetime)
        #
        #                 temp_price_list.append(int(date) * 1000)
        #                 temp_price_list.append(
        #                     latest_price.values.tolist()[count][2])
        #                 # print(temp_price_list)
        #                 # latest_price_list.append(temp_price_list)
        #                 data['stock_price_list'].append(temp_price_list)
        #                 print(data['stock_price_list'])
        #
        #             try:
        #                 stock_gen_info = StockInfo.objects.get(stock=stock_obj)
        #                 print(stock_gen_info)
        #             except:
        #                 stock_gen_info = {}
        #             data['stock_gen_info'] = stock_gen_info
        #             try:
        #                 TopSearched.objects.get(stock=stock_obj,
        #                                         userid=request.user)
        #                 data['added_to_watchlist'] = True
        #             except:
        #                 data['added_to_watchlist'] = False
        #             try:
        #                 t_s_obj = TopSearched.objects.get(stock=stock_obj,
        #                                                   userid=request.user)
        #                 t_s_obj.count += 1
        #                 t_s_obj.save()
        #                 # response['status'] = "removed"
        #             except:
        #                 TopSearched.objects.get_or_create(stock=stock_obj,
        #                                                   userid=request.user)
        #                 # response['status'] = "added"
        #             data['earnings_graph_data'] = False
        #             # response = price_change('1D', symbol)
        #             try:
        #                 if len(data['estimate_list']) > 0 and len(
        #                         data['actual_list']) > 0:
        #                     data['earnings_graph_data'] = True
        #             except:
        #                 data['earnings_graph_data'] = False
        #             response['status'] = "removed"
        #             data['has_pos'] = "False"
        #             data['stockname'] = stock_obj.name
        #             if Position.objects.filter(userid=request.user,
        #                                        stockname=stock_obj):
        #                 data['has_pos'] = "True"
        #             try:
        #                 data['stockprice'] = response['stockprice']
        #             except:
        #                 data['stockprice'] = round(
        #                     si.get_live_price(stock_obj.symbol + ".NS"), 2)
        #             response['line_chart_html'] = render_to_string(
        #                 'includes/dashboard_includes/line-chart-main.html',
        #                 data)
        #             response['stock_market_settings_html'] = render_to_string(
        #                 'includes/dashboard_includes/'
        #                 'stock_market_settings.html',
        #                 data)
        #             response['company_info_html'] = render_to_string(
        #                 'includes/dashboard_includes/company_info.html',
        #                 data)
        #             response['scatter_plot_html'] = render_to_string(
        #                 'includes/dashboard_includes/'
        #                 'scatter-plot-chart-main.html',
        #                 data)
        #             try:
        #                 response['color'] = data['color']
        #             except:
        #                 response['color'] = "#038afe"
        #             transaction_list = paginate_data(request)
        #             # print(transaction_list,">???")
        #             if transaction_list:
        #                 response['up_activity_html'] = render_to_string(
        #                     "includes/dashboard_includes/u"
        #                     "pcoming_activity.html",
        #                     {
        #                         "transaction_list": transaction_list
        #                     })
        #                 response['tr_status'] = "True"
        #             total_share = 0
        #             try:
        #                 print(">>?><>>>>>>><")
        #                 position_obj = \
        #                 Position.objects.filter(userid=request.user,
        #                                         stockname=stock_obj)[0]
        #                 try:
        #                     pos_stockprice = response['stockprice']
        #                 except:
        #                     pos_stockprice = round(
        #                         si.get_live_price(stock_obj.symbol + ".NS"), 2)
        #                 response2 = get_position_details(request, stock_obj,
        #                                                  position_obj,
        #                                                  pos_stockprice)
        #                 response['has_position'] = True
        #                 response2['stockprice'] = pos_stockprice
        #                 response['pos_table_details_html'] = render_to_string(
        #                     "includes/dashboard_includes/"
        #                     "position-table-details.html",
        #                     response2)
        #                 # response.update(response2)
        #                 for pos_stock in Position.objects.filter(
        #                         userid=request.user, stockname=stock_obj):
        #                     total_share += int(
        #                         pos_stock.transaction_details.size)
        #
        #                 print("RESPONSE  ------------------------------ \n   ",
        #                       response['stock_num'])
        #
        #             except Exception as e:
        #                 print("GET STOCK DETAIL POS ERROR    ", e)
        #             response['stock_num'] = total_share
        #             response['has_history'] = "True"
        #             # response['dashboard_html'] = render_to_string(
        #             # 'dashboard.html',data)
        #             # response['dashboard_html'] = render_to_string(
        #             # 'dashboard.html',data)
        #         else:
        #             response['has_history'] = "False"
        #     elif ajxtype == "get_stock_real_data":
        #
        #         # tata_power = YahooFinance(symbol+'.NS', result_range="1d",
        #         # interval='1m', dropna='True').result
        #         current_time = datetime.datetime.now().time()
        #         print("???????????????????????????//", int(current_time.hour))
        #         if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
        #             live_price = si.get_live_price(symbol + ".NS")
        #             # live_price= tata_power.values.tolist()[len(
        #             # tata_power.values.tolist()) - 1][0]
        #             process = threading.Thread(
        #                 target=update_position_and_gainloss,
        #                 args=(live_price, symbol, request.user,))
        #             process.start()
        #             process.join()
        #             response['data'] = float(str(num_quantize(live_price)))
        #             response['status'] = True
        #         elif int(current_time.hour) == 15:
        #             if int(current_time.minute) <= 30:
        #                 live_price = si.get_live_price(symbol + ".NS")
        #                 process = threading.Thread(
        #                     target=update_position_and_gainloss,
        #                     args=(live_price, symbol, request.user,))
        #                 process.start()
        #                 process.join()
        #                 # live_price = tata_power.values.tolist()[len(
        #                 # tata_power.values.tolist()) - 1][0]
        #                 response['data'] = float(str(num_quantize(live_price)))
        #                 response['status'] = True
        #             else:
        #                 response['status'] = False
        #         else:
        #             response['status'] = False
        #         # from custom_packages.yahoo_finance import YahooFinance
        #         # latest_price = YahooFinance(symbol+'.NS',
        #         # result_range='1d', interval='1m', dropna='True').result
        #         # print(latest_price)
        #         # price_list = latest_price.values.tolist()
        #         # last_price = price_list[len(price_list)-1][0]
        #         # random_num = [1775.95,1779.30,1776.42,1775.23,1775. 95,
        #         # 1779.30,1776.42,1775.23]
        #         # response['data'] = random.choice(random_num)
        #         #
        #         # response['data'] = si.get_live_price(symbol + ".NS")
        #         # response['status'] = True
        #     elif ajxtype == "get_watched_stock_real_data":
        #         symbols = request.GET.getlist("symbols[]")
        #         prices = []
        #         for symbol in symbols:
        #             live_price = si.get_live_price(symbol + ".NS")
        #             monthly_data = si.get_data(symbol + ".NS", interval="1d")
        #             # print("_____    ", monthly_data.values.tolist())
        #             price_list = monthly_data.values.tolist()
        #             prev_day_price = price_list[len(price_list) - 2][4]
        #             difference = live_price - prev_day_price
        #             # percentage = (live_price / prev_day_price) * 100
        #
        #             color = '#ff5000'
        #             if float(difference) > 0:
        #                 color = '#01ec36'
        #                 difference = "+" + str(difference)
        #             difference = num_quantize(float(difference))
        #             difference = str(difference)
        #             prices.append(
        #                 {'symbol': symbol, 'price': round(live_price, 2),
        #                  'difference': difference, 'color': color})
        #         response['data'] = prices
        #
        #     elif ajxtype == "add-to-watchlist":
        #         symbol = request.GET.get("symbol")
        #         stock_obj = StockNames.objects.get(symbol=symbol)
        #         try:
        #             TopSearched.objects.get(stock=stock_obj,
        #                                     userid=request.user).delete()
        #             response['status'] = "removed"
        #         except:
        #             TopSearched.objects.create(stock=stock_obj,
        #                                        userid=request.user)
        #             response['status'] = "added"
        #         # top_search_obj.userid = request.user
        #         # top_search_obj.count += 1
        #         # top_search_obj.save()
        #
        #     elif ajxtype == "price_change":
        #         key = request.GET.get("key")
        #         live_price = request.GET.get("live_price")
        #         prev_price = request.GET.get("prev_price")
        #
        #         response = price_change(key, symbol, live_price, prev_price)
        #
        #
        #     elif ajxtype == "buy_stock":
        #
        #         symbol = request.GET.get("symbol")
        #
        #         expires = request.GET.get("expires")
        #
        #         order_type = request.GET.get("order_type")
        #
        #         share = request.GET.get("share")
        #
        #         current_price = request.GET.get("current_price")
        #
        #         limit_price = request.GET.get("limit_price")
        #
        #         stock = StockNames.objects.get(symbol=symbol)
        #
        #         current_date = datetime.datetime.now()
        #
        #         remove_date = datetime.datetime.now()
        #
        #         if request.user.is_authenticated:
        #
        #             user = UserDetails.objects.get(user=request.user)
        #
        #             identity = IdentityDetails.objects.get(id=user.identity.id)
        #
        #             user_buyingpower = float(user.identity.buyingpower)
        #
        #             if expires == "1":
        #
        #                 expires_val = "Good for day"
        #
        #             else:
        #
        #                 expires_val = "Good till canceled"
        #
        #             if order_type == "market_order":
        #
        #                 transaction_obj, status = \
        #                     Transaction.objects.get_or_create(
        #                         stockticker=stock,
        #                         ordertype=order_type,
        #
        #                         price=current_price, size=share,
        #
        #                         userid=request.user,
        #                         expires=expires_val)
        #
        #             else:
        #
        #                 transaction_obj = Transaction.objects.create(
        #                     stockticker=stock, ordertype=order_type,
        #                     price=current_price, size=share,
        #                     userid=request.user, expires=expires_val)
        #
        #             if expires != "1":
        #                 transaction_obj.remove_date = current_date + \
        #                                               datetime.timedelta(
        #                     days=90)
        #
        #                 transaction_obj.save()
        #
        #             current_time = current_date.time()
        #
        #             flag = 0
        #
        #             print("current_time.hour  ", current_time.hour)
        #
        #             if int(current_time.hour) >= 9 and int(
        #                     current_time.hour) < 15:
        #
        #                 flag = 1
        #
        #             elif int(current_time.hour) == 15:
        #
        #                 if int(current_time.minute) <= 30:
        #                     flag = 1
        #             #
        #             # elif int(current_time.hour) > 15 or int(
        #             #         current_time.hour) < 9:
        #             #
        #             #     flag = 1
        #
        #             if order_type == "market_order":
        #
        #                 if flag == 1:
        #
        #                     transaction_obj.status = "executed"
        #
        #                     position_obj, status = \
        #                         Position.objects.get_or_create(
        #                             userid=request.user, stockname=stock,
        #                             ticker=symbol,
        #                             price=current_price,
        #                             ordertype=order_type)
        #
        #                     position_obj.transaction_details = transaction_obj
        #
        #                     position_obj.save()
        #
        #                     try:
        #
        #                         history_obj = \
        #                             TransactionHistory.objects.get_or_create(
        #                                 position_obj=position_obj,
        #                                 stock_number=share, status="buy")
        #
        #                     except:
        #
        #                         pass
        #
        #                     # try:
        #
        #                     total_cash = float(current_price) * int(share)
        #
        #                     gl_history = GainLossHistory.objects.create(
        #                         userid=request.user, stock=stock,
        #                         total_cash=total_cash)
        #
        #                     gl_history.unrealised_gainloss = num_quantize(
        #
        #                         (float(current_price) - float(
        #                             position_obj.transaction_details.price)) *
        #                         int(share))
        #
        #                     gl_history.position_obj = position_obj
        #
        #                     gl_history.save()
        #
        #                     user_buyingpower -= total_cash
        #
        #                     identity.buyingpower = user_buyingpower
        #
        #                     identity.save()
        #
        #                     # except:
        #
        #                     #     pass
        #
        #                 else:
        #
        #                     transaction_obj.status = "pending"
        #
        #             elif order_type == "limit_order":
        #
        #                 transaction_obj.limit_price = limit_price
        #
        #             transaction_obj.save()
        #
        #     elif ajxtype == "table_paginate":
        #         transaction_list = paginate_data(request)
        #         if transaction_list:
        #             response['up_activity_html'] = render_to_string(
        #                 "includes/dashboard_includes/upcoming_activity.html", {
        #                     "transaction_list": transaction_list
        #                 })
        #             response['tr_status'] = "True"
        #
        #     elif ajxtype == "delete_transaction_data":
        #         Transaction.objects.get(id=request.GET.get("id")).delete()
        #         # position_obj_list = []
        #         # for position_obj in Position.objects.filter(
        #         # userid=request.user):
        #         #     stock_obj = StockNames.objects.get(symbol=symbol)
        #         #     datas = stock_obj.history.history_json['data']
        #         #     data = {
        #         #         "date":position_obj.transaction_details.time,
        #         #         "ordertype":position_obj.ordertype,
        #         #         "size":position_obj.transaction_details.size,
        #         #         "price":position_obj.transaction_details.price,
        #         #         "current_price":datas.get("stock_price"),
        #         #         "gainloss":position_obj.unrealised_gainloss,
        #         #         "symbol":position_obj.ticker,
        #         #     }
        #         #     position_obj_list.append(data)
        #
        #     elif ajxtype == "sell-stock":
        #         symbol = request.GET.get("symbol")
        #         share_num = int(request.GET.get("share_num"))
        #         current_price = si.get_live_price(symbol + ".NS")
        #         user_obj = UserDetails.objects.get(user=request.user)
        #         identity_obj = IdentityDetails.objects.get(
        #             id=user_obj.identity.id)
        #         buying_power = float(identity_obj.buyingpower)
        #         for pos_obj in Position.objects.filter(userid=request.user,
        #                                                ticker=symbol).order_by(
        #                 "id"):
        #             print("share_num    ", share_num)
        #
        #             stock_num = int(pos_obj.transaction_details.size)
        #             print("stock_num    ", stock_num)
        #
        #             if stock_num == share_num:
        #                 stock_num -= share_num
        #                 pos_obj.transaction_details.size = stock_num
        #                 pos_obj.transaction_details.save()
        #                 try:
        #                     history_obj = \
        #                         TransactionHistory.objects.get_or_create(
        #                             position_obj=pos_obj,
        #                             stock_number=share_num,
        #                             status="sell")
        #                 except:
        #                     pass
        #                 try:
        #                     realised_gainloss = (float(current_price) - float(
        #                         pos_obj.transaction_details.price)) * int(
        #                         share_num)
        #                     gl_obj = GainLossHistory.objects.get(
        #                         position_obj=pos_obj)
        #                     gl_obj.realised_gainloss = num_quantize(
        #                         realised_gainloss)
        #                     buying_power += realised_gainloss
        #                     print(
        #                         ",,,,,,,,,,,,,,,,1111111111       buyingpower",
        #                         buying_power,
        #                         num_quantize(realised_gainloss))
        #                     gl_obj.save()
        #
        #                 except:
        #                     pass
        #             elif stock_num > share_num:
        #                 # share_num = stock_num - share_num
        #                 stock_num -= share_num
        #                 pos_obj.transaction_details.size = stock_num
        #                 pos_obj.transaction_details.save()
        #                 try:
        #                     history_obj = \
        #                         TransactionHistory.objects.get_or_create(
        #                             position_obj=pos_obj,
        #                             stock_number=share_num,
        #                             status="sell")
        #                 except:
        #                     pass
        #                 try:
        #                     realised_gainloss = (float(current_price) - float(
        #                         pos_obj.transaction_details.price)) * int(
        #                         share_num)
        #                     gl_obj = GainLossHistory.objects.get(
        #                         position_obj=pos_obj)
        #                     gl_obj.realised_gainloss = num_quantize(
        #                         realised_gainloss)
        #                     buying_power += realised_gainloss
        #                     print(
        #                         ",,,,,,,,,,,,,,,,2222222222222    buyingpower",
        #                         buying_power,
        #                         num_quantize(realised_gainloss))
        #                     gl_obj.save()
        #                 except Exception as e:
        #                     print("ERRORRRR  SELL STOCK  ", e)
        #                     pass
        #                 break
        #             else:
        #                 share_num = share_num - stock_num
        #                 pos_obj.transaction_details.size = 0
        #                 pos_obj.transaction_details.save()
        #                 try:
        #                     history_obj = \
        #                         TransactionHistory.objects.get_or_create(
        #                             position_obj=pos_obj,
        #                             stock_number=stock_num,
        #                             status="sell")
        #                 except:
        #                     pass
        #                 try:
        #                     realised_gainloss = (float(current_price) - float(
        #                         pos_obj.transaction_details.price)) * int(
        #                         stock_num)
        #                     gl_obj = GainLossHistory.objects.get(
        #                         position_obj=pos_obj)
        #                     gl_obj.realised_gainloss = num_quantize(
        #                         realised_gainloss)
        #                     buying_power += realised_gainloss
        #                     print(
        #                         ",,,,,,,,,,,,,,,,33333333333      buyingpower",
        #                         buying_power,
        #                         num_quantize(realised_gainloss))
        #                     gl_obj.save()
        #                 except:
        #                     pass
        #             print("===========share_num    ", share_num)
        #             print("===========stock_num    ", stock_num)
        #             # pos_obj.save()
        #             if int(pos_obj.transaction_details.size) == 0:
        #                 print("###########    REMAINING SHARE    ",
        #                       pos_obj.transaction_details.size)
        #                 pos_obj.delete()
        #             print("BUYYYING POWERRRR   ", buying_power)
        #         identity_obj.buyingpower = num_quantize(buying_power)
        #         identity_obj.save()

        return render(request, self.template_name, context)


class StockPageAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = {}
        ajxtype = request.GET.get("type")
        symbol = request.GET.get("symbol")

        if ajxtype == "get_stock_details":
            stock_obj = StockNames.objects.get(symbol=symbol)
            cc = StockHistory.objects.get(stock=stock_obj).history_json
            if StockHistory.objects.filter(stock=stock_obj):

                data = stock_obj.history.history_json['data']
                response = stock_obj.history.history_json['response']
                # tttt = get_stock_details_json(symbol,request)

                latest_price = YahooFinance(symbol + '.NS',
                                            result_range='1d',
                                            interval='1m',
                                            dropna='True').result
                # price_list = latest_price.values.tolist()
                current_time = datetime.datetime.now().time()
                count = 0
                for i, j in latest_price.iterrows():
                    temp_price_list = []
                    dt_object1 = datetime.datetime.strptime(str(i),
                                                            "%Y-%m-%d"
                                                            " %H:%M:%S")
                    my_time = dt_object1.time()
                    my_datetime = datetime.datetime.combine(i, my_time)
                    date = datetime.datetime.timestamp(my_datetime)

                    temp_price_list.append(int(date) * 1000)
                    temp_price_list.append(
                        latest_price.values.tolist()[count][2])
                    # print(temp_price_list)
                    # latest_price_list.append(temp_price_list)
                    data['stock_price_list'].append(temp_price_list)
                    print(data['stock_price_list'])

                try:
                    stock_gen_info = StockInfo.objects.get(stock=stock_obj)
                    print(stock_gen_info)
                except:
                    stock_gen_info = {}
                data['stock_gen_info'] = stock_gen_info
                try:
                    TopSearched.objects.get(stock=stock_obj,
                                            userid=request.user)
                    data['added_to_watchlist'] = True
                except:
                    data['added_to_watchlist'] = False
                try:
                    t_s_obj = TopSearched.objects.get(stock=stock_obj,
                                                      userid=request.user)
                    t_s_obj.count += 1
                    t_s_obj.save()
                    # response['status'] = "removed"
                except:
                    TopSearched.objects.get_or_create(stock=stock_obj,
                                                      userid=request.user)
                    # response['status'] = "added"
                data['earnings_graph_data'] = False
                # response = price_change('1D', symbol)
                try:
                    if len(data['estimate_list']) > 0 and len(
                            data['actual_list']) > 0:
                        data['earnings_graph_data'] = True
                except:
                    data['earnings_graph_data'] = False
                response['status'] = "removed"
                data['has_pos'] = "False"
                data['stockname'] = stock_obj.name
                if Position.objects.filter(userid=request.user,
                                           stockname=stock_obj):
                    data['has_pos'] = "True"
                try:
                    data['stockprice'] = response['stockprice']
                except:
                    data['stockprice'] = round(
                        si.get_live_price(stock_obj.symbol + ".NS"), 2)
                response['line_chart_html'] = render_to_string(
                    'includes/dashboard_includes/line-chart-main.html',
                    data)
                response['stock_market_settings_html'] = render_to_string(
                    'includes/dashboard_includes/'
                    'stock_market_settings.html',
                    data)
                response['company_info_html'] = render_to_string(
                    'includes/dashboard_includes/company_info.html',
                    data)
                response['scatter_plot_html'] = render_to_string(
                    'includes/dashboard_includes/'
                    'scatter-plot-chart-main.html',
                    data)
                try:
                    response['color'] = data['color']
                except:
                    response['color'] = "#038afe"
                transaction_list = paginate_data(request)
                # print(transaction_list,">???")
                if transaction_list:
                    response['up_activity_html'] = render_to_string(
                        "includes/dashboard_includes/u"
                        "pcoming_activity.html",
                        {
                            "transaction_list": transaction_list
                        })
                    response['tr_status'] = "True"
                total_share = 0
                try:
                    print(">>?><>>>>>>><")
                    position_obj = \
                        Position.objects.filter(userid=request.user,
                                                stockname=stock_obj)[0]
                    try:
                        pos_stockprice = response['stockprice']
                    except:
                        pos_stockprice = round(
                            si.get_live_price(stock_obj.symbol + ".NS"), 2)
                    response2 = get_position_details(request, stock_obj,
                                                     position_obj,
                                                     pos_stockprice)
                    response['has_position'] = True
                    response2['stockprice'] = pos_stockprice
                    response['pos_table_details_html'] = render_to_string(
                        "includes/dashboard_includes/"
                        "position-table-details.html",
                        response2)
                    # response.update(response2)
                    for pos_stock in Position.objects.filter(
                            userid=request.user, stockname=stock_obj):
                        total_share += int(
                            pos_stock.transaction_details.size)

                    print("RESPONSE  ------------------------------ \n   ",
                          response['stock_num'])

                except Exception as e:
                    print("GET STOCK DETAIL POS ERROR    ", e)
                response['stock_num'] = total_share
                response['has_history'] = "True"
                # response['dashboard_html'] = render_to_string(
                # 'dashboard.html',data)
                # response['dashboard_html'] = render_to_string(
                # 'dashboard.html',data)
            else:
                response['has_history'] = "False"
        elif ajxtype == "get_stock_real_data":

            # tata_power = YahooFinance(symbol+'.NS', result_range="1d",
            # interval='1m', dropna='True').result
            current_time = datetime.datetime.now().time()
            print("???????????????????????????//", int(current_time.hour))
            if 9 <= int(current_time.hour) < 15:
                live_price = si.get_live_price(symbol + ".NS")
                print("live price ", live_price)
                # live_price= tata_power.values.tolist()[len(
                # tata_power.values.tolist()) - 1][0]
                process = threading.Thread(
                    target=update_position_and_gainloss,
                    args=(live_price, symbol, request.user,))
                process.start()
                process.join()
                response['data'] = float(str(num_quantize(live_price)))
                response['status'] = True
            elif int(current_time.hour) == 15:
                if int(current_time.minute) <= 30:
                    live_price = si.get_live_price(symbol + ".NS")
                    process = threading.Thread(
                        target=update_position_and_gainloss,
                        args=(live_price, symbol, request.user,))
                    process.start()
                    process.join()
                    # live_price = tata_power.values.tolist()[len(
                    # tata_power.values.tolist()) - 1][0]
                    response['data'] = float(str(num_quantize(live_price)))
                    response['status'] = True
                else:
                    response['status'] = False
            else:
                response['status'] = False
            # from custom_packages.yahoo_finance import YahooFinance
            # latest_price = YahooFinance(symbol+'.NS',
            # result_range='1d', interval='1m', dropna='True').result
            # print(latest_price)
            # price_list = latest_price.values.tolist()
            # last_price = price_list[len(price_list)-1][0]
            # random_num = [1775.95,1779.30,1776.42,1775.23,1775. 95,
            # 1779.30,1776.42,1775.23]
            # response['data'] = random.choice(random_num)
            #
            # response['data'] = si.get_live_price(symbol + ".NS")
            # response['status'] = True
        elif ajxtype == "get_watched_stock_real_data":
            symbols = request.GET.getlist("symbols[]")
            prices = []
            for symbol in symbols:
                live_price = si.get_live_price(symbol + ".NS")
                monthly_data = si.get_data(symbol + ".NS", interval="1d")
                # print("_____    ", monthly_data.values.tolist())
                price_list = monthly_data.values.tolist()
                prev_day_price = price_list[len(price_list) - 2][4]
                difference = live_price - prev_day_price
                # percentage = (live_price / prev_day_price) * 100

                color = '#ff5000'
                if float(difference) > 0:
                    color = '#01ec36'
                    difference = "+" + str(difference)
                difference = num_quantize(float(difference))
                difference = str(difference)
                prices.append(
                    {'symbol': symbol, 'price': round(live_price, 2),
                     'difference': difference, 'color': color})
            response['data'] = prices

        elif ajxtype == "add-to-watchlist":
            symbol = request.GET.get("symbol")
            stock_obj = StockNames.objects.get(symbol=symbol)
            # Remove Cache for Watchlist so it refreshes with the latest data on refresh.
            cache.delete(f"watchlist_{request.user.id}")
            cache.delete(f"watchlist_exp_{request.user.id}")
            try:
                TopSearched.objects.get(stock=stock_obj,
                                        userid=request.user).delete()
                response['status'] = "removed"
            except:
                TopSearched.objects.create(stock=stock_obj,
                                           userid=request.user)
                response['status'] = "added"
            # top_search_obj.userid = request.user
            # top_search_obj.count += 1
            # top_search_obj.save()

        elif ajxtype == "price_change":
            key = request.GET.get("key")
            live_price = request.GET.get("live_price")
            prev_price = request.GET.get("prev_price")

            response = price_change(key, symbol, live_price, prev_price)

        elif ajxtype == "buy_stock":

            symbol = request.GET.get("symbol")

            expires = request.GET.get("expires")

            order_type = request.GET.get("order_type")

            share = request.GET.get("share")

            current_price = request.GET.get("current_price")

            limit_price = request.GET.get("limit_price")

            stock = StockNames.objects.get(symbol=symbol)

            current_date = datetime.datetime.now()

            remove_date = datetime.datetime.now()

            if request.user.is_authenticated:

                user = UserDetails.objects.get(user=request.user)

                identity = IdentityDetails.objects.get(id=user.identity.id)

                user_buyingpower = float(user.identity.buyingpower)

                if expires == "1":

                    expires_val = "Good for day"

                else:

                    expires_val = "Good till canceled"

                if order_type == "market_order":
                    # Old Approach
                    # transaction_obj, status = \
                    #     Transaction.objects.get_or_create(
                    #         stockticker=stock,
                    #         ordertype=order_type,
                    #
                    #         price=current_price, size=share,
                    #
                    #         userid=request.user,
                    #         expires=expires_val, transaction_type="buy"
                    #     )

                    transaction_obj = \
                        Transaction.objects.create(
                            stockticker=stock,
                            ordertype=order_type,

                            price=current_price, size=share,

                            userid=request.user,
                            expires=expires_val, transaction_type="buy"
                        )

                else:

                    transaction_obj = Transaction.objects.create(
                        stockticker=stock, ordertype=order_type,
                        price=current_price, size=share,
                        userid=request.user, expires=expires_val,
                        transaction_type="buy"
                    )

                transaction_obj.save()

                if expires != "1":
                    transaction_obj.remove_date = current_date + \
                                                  datetime.timedelta(
                                                      days=90)

                    transaction_obj.save()

                current_time = current_date.time()

                flag = 0

                print("current_time.hour  ", current_time.hour)

                if int(current_time.hour) >= 9 and int(
                        current_time.hour) < 15:

                    flag = 1

                elif int(current_time.hour) == 15:

                    if int(current_time.minute) <= 30:
                        flag = 1
                #
                # elif int(current_time.hour) > 15 or int(
                #         current_time.hour) < 9:
                #
                #     flag = 1

                if order_type == "market_order":

                    if flag == 1:

                        transaction_obj.status = "executed"
                        # Old Approach
                        # position_obj, status = \
                        #     Position.objects.get_or_create(
                        #     userid = request.user, stockname = stock,
                        #     ticker = symbol,
                        #     price = current_price,
                        #     ordertype = order_type
                        # )

                        position_obj = \
                            Position.objects.create(
                                userid=request.user, stockname=stock,
                                ticker=symbol,
                                price=current_price,
                                ordertype=order_type
                            )

                        position_obj.transaction_details = transaction_obj
                        position_obj.size = transaction_obj.size
                        position_obj.save()

                        try:

                            history_obj = \
                                TransactionHistory.objects.get_or_create(
                                    position_obj=position_obj,
                                    stock_number=share, status="buy")

                        except:

                            pass

                        # try:

                        total_cash = float(current_price) * int(share)

                        gl_history = GainLossHistory.objects.create(
                            userid=request.user, stock=stock,
                            total_cash=total_cash)

                        gl_history.unrealised_gainloss = num_quantize(

                            (float(current_price) - float(
                                position_obj.transaction_details.price)) *
                            int(share))

                        gl_history.position_obj = position_obj

                        gl_history.save()

                        user_buyingpower -= total_cash

                        identity.buyingpower = user_buyingpower

                        identity.save()

                        # except:

                        #     pass

                    else:

                        transaction_obj.status = "pending"

                elif order_type == "limit_order":

                    transaction_obj.limit_price = limit_price

                transaction_obj.save()

        elif ajxtype == "table_paginate":
            transaction_list = paginate_data(request)
            if transaction_list:
                response['up_activity_html'] = render_to_string(
                    "includes/dashboard_includes/upcoming_activity.html", {
                        "transaction_list": transaction_list
                    })
                response['tr_status'] = "True"

        elif ajxtype == "delete_transaction_data":
            Transaction.objects.get(id=request.GET.get("id")).delete()
            # position_obj_list = []
            # for position_obj in Position.objects.filter(
            # userid=request.user):
            #     stock_obj = StockNames.objects.get(symbol=symbol)
            #     datas = stock_obj.history.history_json['data']
            #     data = {
            #         "date":position_obj.transaction_details.time,
            #         "ordertype":position_obj.ordertype,
            #         "size":position_obj.transaction_details.size,
            #         "price":position_obj.transaction_details.price,
            #         "current_price":datas.get("stock_price"),
            #         "gainloss":position_obj.unrealised_gainloss,
            #         "symbol":position_obj.ticker,
            #     }
            #     position_obj_list.append(data)

        elif ajxtype == "sell-stock":
            print("sell stock ... ", 1)
            symbol = request.GET.get("symbol")
            expires = request.GET.get("expires")
            order_type = request.GET.get("order_type")
            share_num = request.GET.get("share_num")
            if share_num:
                share_num = int(share_num)
            current_price = request.GET.get("current_price")
            limit_price = request.GET.get("limit_price")
            stock = StockNames.objects.get(symbol=symbol)
            current_date = datetime.datetime.now()
            remove_date = datetime.datetime.now()

            if request.user.is_authenticated:
                user = UserDetails.objects.get(user=request.user)
                identity = IdentityDetails.objects.get(id=user.identity.id)
                user_buyingpower = float(user.identity.buyingpower)

                if expires == "1":
                    expires_val = "Good for day"
                else:
                    expires_val = "Good till canceled"

                if order_type == "market_order":
                    transaction_obj, status = \
                        Transaction.objects.get_or_create(
                            stockticker=stock,
                            ordertype=order_type, transaction_type="sell",
                            price=current_price, size=share_num,
                            userid=request.user,
                            expires=expires_val)

                    # market orders get executed on instantaneously
                    # transaction_obj = \
                    #     Transaction.objects.create(
                    #         stockticker=stock,
                    #         ordertype=order_type, transaction_type="sell",
                    #         price=current_price, size=share_num,
                    #         userid=request.user,
                    #         expires=expires_val
                    #     )

                else:
                    transaction_obj = Transaction.objects.create(
                        stockticker=stock, ordertype=order_type, transaction_type="sell",
                        price=current_price, size=share_num,
                        userid=request.user, expires=expires_val
                    )

                transaction_obj.save()

                if expires != "1":
                    transaction_obj.remove_date = current_date + datetime.timedelta(days=90)
                    transaction_obj.save()

                current_time = current_date.time()
                flag = 0
                print("current_time.hour  ", current_time.hour)

                if 9 <= int(current_time.hour) < 15:
                    flag = 1

                elif int(current_time.hour) == 15:
                    if int(current_time.minute) <= 30:
                        flag = 1

                print("flag ", flag)
                #
                # elif int(current_time.hour) > 15 or int(
                #         current_time.hour) < 9:
                #
                #     flag = 1

                if order_type == "market_order":
                    print('market order ... ')
                    if flag == 1:
                        # Start Sell process for Market Orders .. if the market is opened
                        user_obj = UserDetails.objects.get(user=request.user)
                        identity_obj = IdentityDetails.objects.get(id=user_obj.identity.id)
                        buying_power = float(identity_obj.buyingpower)

                        # Old approach - First In First Out
                        # positions = Position.objects.filter(userid=request.user, ticker=symbol).order_by("id")
                        # New approach - Last In First Out
                        positions = Position.objects.filter(userid=request.user, ticker=symbol).order_by("-id")
                        print("position ... ", positions.count())

                        for pos_obj in positions:
                            stock_num = int(pos_obj.size)
                            s = Singleton2.get_instance("sell-mkt-order")
                            print("itertion ... ", stock_num, share_num)

                            print("BEFORE =========== ", pos_obj.size)

                            if stock_num == share_num:
                                stock_num -= share_num
                                # pos_obj.transaction_details.size = stock_num
                                pos_obj.size = stock_num
                                pos_obj.save()

                                print("AFTER =========== ", pos_obj.size)
                                # pos_obj.transaction_details.save()
                                try:
                                    history_obj = \
                                        TransactionHistory.objects.get_or_create(
                                            position_obj=pos_obj,
                                            stock_number=share_num,
                                            status="sell")
                                except:
                                    pass
                                try:
                                    realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(share_num)
                                    gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                                    temp_var = num_quantize(gl_obj.realised_gainloss)
                                    temp_var = temp_var + num_quantize(realised_gainloss)
                                    gl_obj.realised_gainloss = temp_var
                                    # Incorrect Approach
                                    # buying_power += realised_gainloss
                                    # Correct Approach
                                    live_price, _ = s.parse_tick_data(pos_obj.ticker)
                                    buying_power += (share_num * live_price)
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
                                pos_obj.size = stock_num
                                pos_obj.save()
                                print("AFTER =========== ", pos_obj.size)
                                # pos_obj.transaction_details.save()
                                try:
                                    history_obj = \
                                        TransactionHistory.objects.get_or_create(
                                            position_obj=pos_obj,
                                            stock_number=share_num,
                                            status="sell")
                                except:
                                    pass
                                try:
                                    realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(share_num)
                                    gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                                    temp_var = num_quantize(gl_obj.realised_gainloss)
                                    temp_var = temp_var + num_quantize(realised_gainloss)
                                    gl_obj.realised_gainloss = temp_var

                                    # Incorrect Approach
                                    # buying_power += realised_gainloss
                                    # Correct Approach
                                    live_price, _ = s.parse_tick_data(pos_obj.ticker)
                                    buying_power += (share_num * live_price)
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
                                position_size_result = 0
                                pos_obj.size = 0
                                pos_obj.save()
                                print("AFTER =========== ", pos_obj.size)
                                # pos_obj.transaction_details.save()
                                try:
                                    history_obj = \
                                        TransactionHistory.objects.get_or_create(
                                            position_obj=pos_obj,
                                            stock_number=stock_num,
                                            status="sell")
                                except:
                                    pass
                                try:
                                    realised_gainloss = (float(current_price) - float(pos_obj.transaction_details.price)) * int(stock_num)
                                    gl_obj = GainLossHistory.objects.get(position_obj=pos_obj)
                                    temp_var = num_quantize(gl_obj.realised_gainloss)
                                    temp_var = temp_var + num_quantize(realised_gainloss)
                                    gl_obj.realised_gainloss = temp_var

                                    # Incorrect Approach
                                    # buying_power += realised_gainloss
                                    # Correct Approach
                                    live_price, _ = s.parse_tick_data(pos_obj.ticker)
                                    buying_power += (share_num * live_price)
                                    print(
                                        ",,,,,,,,,,,,,,,,33333333333      buyingpower",
                                        buying_power,
                                        num_quantize(realised_gainloss))
                                    gl_obj.save()
                                except:
                                    pass

                            if int(pos_obj.size) == 0:
                                print("###########    REMAINING SHARE    ", pos_obj.size)
                                pos_obj.delete()
                            print("BUYYYING POWERRRR   ", buying_power)
                        identity_obj.buyingpower = num_quantize(buying_power)
                        identity_obj.save()

                        transaction_obj.status = "executed"
                        transaction_obj.save()
                    else:
                        transaction_obj.status = "pending"
                elif order_type == "limit_order":
                    transaction_obj.limit_price = limit_price
                transaction_obj.save()

        return HttpResponse(json.dumps(response), content_type="application/json")


class MarketValuesAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        try:
            start = datetime.datetime.now()
            s = Singleton2.get_instance("3")
            stock = StockNames.objects.filter(symbol=symbol).first()
            price, _ = parse_tick_data(s.tick_data, int(stock.token))
            if not price:
                price = si.get_live_price("{}.NS".format(symbol))
            avg_cost, total_units, total_return, total_return_percent, today_return, \
                today_return_percent, portfolio_diversity = get_average_cost(request.user, symbol, price)
            return ResponseOk({
                "values": {
                    "market_value": num_quantize(price * total_units),
                    "share_total": num_quantize(total_units),
                    "live_price": num_quantize(price),
                    "avg_cost": num_quantize(avg_cost),
                    "cost": num_quantize(avg_cost*total_units),
                    "total_units": num_quantize(total_units),
                    "total_return": num_quantize(total_return),
                    "total_return_percent": num_quantize(total_return_percent),
                    "today_return": num_quantize(today_return),
                    "today_return_percent": num_quantize(today_return_percent),
                    "portfolio_diversity": num_quantize(portfolio_diversity),
                }
            })
        except Exception as e:
            return ResponseBadRequest(str(e))


# Uses the Postgres to fetch the historical Data from.
# class StockPageHistoricalAPI(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request):
#         response = {}
#         symbol = request.GET.get("symbol")
#         interval = request.GET.get("interval")
#         if not symbol:
#             return ResponseBadRequest("Symbol not provided")
#         if interval not in ['1D', '1m', '3m', '6m', '1y', '5y']:
#             return ResponseBadRequest("Valid values of Interval 1D, 1m, 3m, 6m, 1y, 5y")
#         start, end = None, None
#         if interval == "1m":
#             end = datetime.datetime.now().date()
#             # start = end - datetime.timedelta(days=30)
#             start = end - relativedelta(months=1)
#         elif interval == "3m":
#             end = datetime.datetime.now().date()
#             # start = end - datetime.timedelta(days=30 * 3)
#             start = end - relativedelta(months=3)
#         elif interval == "6m":
#             end = datetime.datetime.now().date()
#             # start = end - datetime.timedelta(days=30 * 6)
#             start = end - relativedelta(months=6)
#         elif interval == "1y":
#             end = datetime.datetime.now().date()
#             # start = end - datetime.timedelta(days=365)
#             start = end - relativedelta(years=1)
#         elif interval == "5y":
#             end = datetime.datetime.now().date()
#             start = end - relativedelta(years=5)
#         else:
#             # Start = 09:00AM
#             # start = datetime.datetime.combine(datetime.date.today(), datetime.time(9, 0, 0))
#             # hour, minute = datetime.datetime.now().hour, datetime.datetime.now().minute
#             # end = datetime.datetime.now()
#             if is_market_opened_date():
#                 # If market opened today, show today's data only for the market timing only.
#                 start, end = get_day_range(business_hours_only=True)
#             else:
#                 # If market closed today, show previous business day data only for the market timing only.
#                 start, end = get_day_range(get_previous_business_day(), business_hours_only=True)
#             # end = datetime.datetime.combine(datetime.date.today(), datetime.time(hour, minute))
#
#         if interval in ["1m", "3m", "6m", "1y", "5y"]:
#             try:
#                 # not having .NS would yield incorrect results.
#                 if interval != "5y":
#                     df = si.get_data(symbol+".NS", start_date=start, end_date=end)
#                 else:
#                     df = si.get_data(symbol + ".NS", start_date=start, end_date=end, interval="1wk")
#                 if df.empty:
#                     return ResponseBadRequest("No data found")
#                 df.dropna(inplace=True)
#
#                 # format data according to the HighGraph API requirements
#                 df['time_stamps'] = df.index
#
#                 time_stamps = df['time_stamps'].values.tolist()
#                 time_stamps = [int(x / 1000000) for x in time_stamps]
#
#                 prices = df['close'].values.tolist()
#                 prices = [num_quantize(x) for x in prices]
#                 res = list(zip(time_stamps, prices))      # Stitches two lists together to form list of tuples
#                 # json.dumps will convert list of tuples to list of lists.
#                 return ResponseOk({
#                     "data": res, "open_value": res[0][1],
#                     "min": int(datetime.datetime.combine(start, datetime.time.min).timestamp()),
#                     "max": int(datetime.datetime.combine(end, datetime.time.max).timestamp()),
#                 })
#             except Exception as e:
#                 print(e)
#                 return ResponseBadRequest("Ticker '{}' not found or unlisted".format(symbol))
#         else:
#
#             now = datetime.datetime.now()
#             hour, minutes = now.hour, now.minute
#
#             # prices = StockPrices.objects.filter(symbol__iexact=symbol).order_by("time_stamp").\
#             #     values("time_stamp", "price")
#
#             prices = StockPrices.objects.filter(
#                 symbol__iexact=symbol,
#                 time_stamp__gte=start, time_stamp__lte=end,
#             ).order_by("time_stamp").annotate(
#                 i=Window(expression=Rank(), order_by=F("time_stamp").asc())
#             ).annotate(i2=F('i') - 1).values("time_stamp", "price", "i2")
#             print("prices ")
#
#             # If nothing is returned till the market is opened, return the previous day data to avoid the code
#             if prices.count() == 0:
#                 start, end = get_day_range(get_previous_business_day(), business_hours_only=True)
#                 prices = StockPrices.objects.filter(
#                     symbol__iexact=symbol,
#                     time_stamp__gte=start, time_stamp__lte=end,
#                 ).order_by("time_stamp").annotate(
#                     i=Window(expression=Rank(), order_by=F("time_stamp").asc())
#                 ).annotate(i2=F('i') - 1).values("time_stamp", "price", "i2")
#
#             df = pd.DataFrame(prices)
#             if not df.empty:
#                 if now.hour in range(9, 10):
#                     factor = 3
#                 elif now.hour in range(10, 12):
#                     factor = 5
#                 else:
#                     factor = 7
#                 # Getting every 7 rows
#                 df = df[df['i2'] % factor == 0]
#                 print("after sampling factor ", factor)
#                 # df = df.sample(frac=(10-factor) * 0.01)
#                 # df.sort_values("time_stamp", inplace=True)
#                 # print(df)
#                 # converting utc to ist
#                 # df['time_stamp'] = df['time_stamp'].apply(lambda x: x + datetime.timedelta(hours=5, minutes=30))
#                 df['time_stamp'] = df['time_stamp'].apply(lambda x: int(datetime.datetime.timestamp(x)*1000))
#                 print("after mapping")
#                 # df['price'] = df['price'].apply(lambda x: num_quantize(x))
#                 df = df[['time_stamp', 'price']]
#                 print("after column slicing")
#
#                 res = df.values.tolist()
#                 print("converting to list")
#                 open_value = res[0][1]
#                 print("open value ", open_value)
#             else:
#                 res = []
#                 open_value = None
#             print("sending response ", len(res))
#             return ResponseOk({
#                 "data": res, "count": len(res), "open_value": open_value,
#                 # "values": values, "intra_price_change": price_ch
#             })


# Uses the File based Data Store to save the data
class StockPageHistoricalAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        response = {}
        symbol = request.GET.get("symbol")
        interval = request.GET.get("interval")
        if not symbol:
            return ResponseBadRequest("Symbol not provided")
        if interval not in ['1D', '1m', '3m', '6m', '1y', '5y']:
            return ResponseBadRequest("Valid values of Interval 1D, 1m, 3m, 6m, 1y, 5y")
        start, end = None, None
        if interval == "1m":
            end = datetime.datetime.now().date()
            # start = end - datetime.timedelta(days=30)
            start = end - relativedelta(months=1)
        elif interval == "3m":
            end = datetime.datetime.now().date()
            # start = end - datetime.timedelta(days=30 * 3)
            start = end - relativedelta(months=3)
        elif interval == "6m":
            end = datetime.datetime.now().date()
            # start = end - datetime.timedelta(days=30 * 6)
            start = end - relativedelta(months=6)
        elif interval == "1y":
            end = datetime.datetime.now().date()
            # start = end - datetime.timedelta(days=365)
            start = end - relativedelta(years=1)
        elif interval == "5y":
            end = datetime.datetime.now().date()
            start = end - relativedelta(years=5)
        else:
            # Start = 09:00AM
            # start = datetime.datetime.combine(datetime.date.today(), datetime.time(9, 0, 0))
            # hour, minute = datetime.datetime.now().hour, datetime.datetime.now().minute
            # end = datetime.datetime.now()
            if is_market_opened_date():
                # If market opened today, show today's data only for the market timing only.
                start, end = get_day_range(business_hours_only=True)
            else:
                # If market closed today, show previous business day data only for the market timing only.
                start, end = get_day_range(get_previous_business_day(), business_hours_only=True)
            # end = datetime.datetime.combine(datetime.date.today(), datetime.time(hour, minute))

        if interval in ["1m", "3m", "6m", "1y", "5y"]:
            try:
                res = cache.get(f"{symbol}_historical_{interval}")
                expiry = cache.get(f"{symbol}_historical_{interval}_expiry")
                cached = True

                if not res or datetime.datetime.now() >= expiry:
                    cached = False
                    # not having .NS would yield incorrect results.
                    if interval != "5y":
                        df = si.get_data(symbol+".NS", start_date=start, end_date=end)
                    else:
                        df = si.get_data(symbol + ".NS", start_date=start, end_date=end, interval="1wk")
                    if df.empty:
                        return ResponseBadRequest("No data found")
                    df.dropna(inplace=True)

                    # format data according to the HighGraph API requirements
                    df['time_stamps'] = df.index

                    time_stamps = df['time_stamps'].values.tolist()
                    time_stamps = [int(x / 1000000) for x in time_stamps]

                    prices = df['close'].values.tolist()
                    prices = [num_quantize(x) for x in prices]
                    res = list(zip(time_stamps, prices))      # Stitches two lists together to form list of tuples

                    expiry = get_day_range(
                        datetime.datetime.now() + datetime.timedelta(days=1)
                    )[0]
                    cache.set(f"{symbol}_historical_{interval}", res)
                    cache.set(f"{symbol}_historical_{interval}_expiry", expiry)
                # json.dumps will convert list of tuples to list of lists.
                return ResponseOk({
                    "data": res, "open_value": res[0][1], "cached": cached,
                    "min": int(datetime.datetime.combine(start, datetime.time.min).timestamp()),
                    "max": int(datetime.datetime.combine(end, datetime.time.max).timestamp()),
                })
            except Exception as e:
                print(e)
                return ResponseBadRequest("Ticker '{}' not found or unlisted".format(symbol))
        else:

            now = datetime.datetime.now()

            if now.hour in range(9, 10):
                sampling_rate = 3
            elif now.hour in range(10, 12):
                sampling_rate = 5
            else:
                sampling_rate = 7

            print(sampling_rate)
            reader = SymbolReader(symbol)
            df = reader.read(sampling_rate)
            if df.empty:
                reader = SymbolReader(
                    symbol, get_day_range(get_previous_business_day(), business_hours_only=True)[0]
                )
                df = reader.read(sampling_rate)

            if not df.empty:
                df['timestamp'] = df['timestamp'].apply(lambda x: int(datetime.datetime.timestamp(x)*1000))
                df = df[['timestamp', 'price']]
                res = df.values.tolist()
                open_value = res[0][1]
            else:
                res = []
                open_value = None
            return ResponseOk({
                "data": res, "count": len(res), "open_value": open_value,
                # "values": values, "intra_price_change": price_ch
            })


# class StockSearchView(View):
#
#     def get(self, request, *args, **kwargs):
#         try:
#             response = {}
#             all_stocks = StockNames.objects.all()
#             search_q = str(request.GET.get("symbol")).lower()
#             stock_list = []
#             for i in all_stocks:
#                 if search_q in i.symbol.lower() or search_q in i.name.lower():
#                     if i.symbol != "SYMBOL" and i.name != "NAME OF COMPANY":
#                         stock_dict = {
#                             "symbol": i.symbol,
#                             "name": i.name
#                         }
#                         stock_list.append(stock_dict)
#                         # limit += 1
#                 if len(stock_list) > 10:
#                     stock_list = stock_list[:10]
#                 response['stock_list'] = stock_list
#
#             return HttpResponse(json.dumps(response),
#                                 content_type="application/json")
#         except Exception as e:
#             print(e, "Error -----------------------------")


class StockSearchView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            response = {}
            search_q = str(request.GET.get("symbol")).lower()

            all_stocks = list(
                StockNames.objects.filter(
                    Q(symbol__icontains=search_q) |
                    Q(name__icontains=search_q)
                )[:10].values()
            )
            df = pd.DataFrame(all_stocks)
            if not df.empty:
                df = df[['symbol', 'name']]

            response['stock_list'] = df.to_dict("records")
            return ResponseOk(response)
        except Exception as e:
            return ResponseOk({"stock_list": []})


class GetLatestGainLossView(View):

    def get(self, request, *args, **kwargs):
        response = {}
        current_date = datetime.datetime.now()
        current_time = current_date.time()
        flag = 0
        if int(current_time.hour) >= 9 and int(current_time.hour) < 15:
            flag = 1
        elif int(current_time.hour) == 15:
            if int(current_time.minute) <= 30:
                flag = 1
        if flag == 1:
            try:
                buyingpower = UserDetails.objects.get(
                    user=request.user).identity.buyingpower
            except:
                buyingpower = 0

            try:
                gl_data = GainLossChartData.objects.get(
                    userid=request.user).gainloss_data
                response['gainloss_val'] = round(
                    float(num_quantize(
                        float(gl_data[-1][1]) + float(buyingpower))), 2)
                response['gl_status'] = True
            except:
                response['gainloss_val'] = 0.00
                response['gl_status'] = False
        else:
            response['gl_status'] = False
        return HttpResponse(json.dumps(response),
                            content_type="application/json")


class PositionTableAPI(APIView):

    def unreal_gain_loss(self, pos_obj):
        if pos_obj.gl_history_position_rel.all():
            gainloss = pos_obj.gl_history_position_rel.all()[0].unrealised_gainloss
        else:
            gainloss = 0.00
        # if float(value) > 0:
        #     value = "+"+value
        # else:
        #     value = "-" + value
        return gainloss

    def live_price(self, stock):
        s = Singleton2.get_instance("3")
        price = 0.00
        # stock = StockNames.objects.filter(symbol=symbol).first()
        price, _ = parse_tick_data(s.tick_data, int(stock.token))
        if not price:
            price = si.get_live_price("{}.NS".format(stock.symbol))
        return price

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return ResponseOk({
                "data": [], "recordsTotal": 0, "recordsFiltered": 0, "count": 0
            })
        column = request.GET.get('order[0][column]', '4')
        dir = request.GET.get('order[0][dir]', 'desc')
        s = Singleton2.get_instance("instance")

        position_list = []
        positions = Position.objects.filter(userid=request.user)
        aggregate = positions.distinct('ticker')

        position_list = cache.get(f"positions_{request.user.id}")
        positions_list_expiry = cache.get(f"positions_exp_{request.user.id}")

        if position_list is None or datetime.datetime.now() >= positions_list_expiry:

            position_list = []
            for ticker in aggregate:
                symbol = ticker.ticker
                live_price, _ = s.parse_tick_data(symbol)
                avg_cost, total_units, total_return, total_return_percent, today_return, \
                    today_return_percent, portfolio_diversity = get_average_cost(request.user, symbol, live_price)

                position_list.append({
                    'symbol': symbol,
                    'name': ticker.transaction_details.stockticker.name,
                    'size': total_units,
                    'amount': num_quantize(total_units * live_price),
                    'live_price': num_quantize(live_price),
                    'avg_cost': num_quantize(avg_cost),
                    'unrealised_gain_loss': num_quantize(total_return),
                })

            cache.set(f"positions_{request.user.id}", position_list)
            # Set cache expiry to 10 seconds from now
            cache.set(f"positions_exp_{request.user.id}", datetime.datetime.now() + datetime.timedelta(seconds=10))

        df = pd.DataFrame(position_list)
        if not df.empty:
            sort_map = {
                '0': 'name',
                '1': 'symbol',
                '2': 'size',
                '3': 'live_price',
                '4': 'unrealised_gain_loss',
                '5': 'amount',
            }
            field = sort_map.get(str(column))
            print(column, field, dir)
            if field:
                if dir == 'desc':
                    df.sort_values(field, ascending=False, inplace=True)
                else:
                    df.sort_values(field, inplace=True)
            else:
                df.sort_values('unrealised_gain_loss', ascending=False, inplace=True)

        response = {
            "data": df.to_dict('records'), "recordsTotal": len(position_list), "recordsFiltered": len(position_list),
            "count": len(position_list)
        }
        return ResponseOk(response)
        # return HttpResponse(json.dumps(response), content_type="application/json")


class GetStocksAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            positions = Position.objects.filter(userid=request.user)
            aggregate = positions.values("ticker").annotate(shares=Sum("size")).order_by("-shares")
            s = Singleton2.get_instance("")
            df = pd.DataFrame(aggregate)

            res = df.to_dict("records")
            start, end = get_day_range(get_previous_business_day())
            for x in res:
                x['live_price'] = s.parse_tick_data(x['ticker'])[0]
                x['initial'] = get_all_open_prices(x['ticker'] + ".NS")['1d']
                # x['initial'] = si.get_data(
                #     x['ticker']+".NS", end_date=end, start_date=start
                # ).to_dict("records")[-1].get("close", 0.0)
                x['delta'] = x['live_price'] - x['initial']

                x['percentage'] = num_quantize((x['delta'] / x['initial']) * 100) if x['initial'] else 0.0
                x['delta'] = num_quantize(x['delta'])
                x['initial'] = num_quantize(x['initial'])
                x['live_price'] = num_quantize(x['live_price'])

                if x['delta'] == -0.0:
                    x['delta'] = 0.0
                if x['percentage'] == -0.0:
                    x['percentage'] = 0.0

                if x['delta'] < 0:
                    x['color'] = "#ff5000"
                    x['color_text'] = "red"
                else:
                    x['color'] = "#00ff39"
                    x['color_text'] = "green"

            # _, end = get_day_range(get_previous_business_day())
            # if not df.empty:
            #     df['live_price'] = df['ticker'].apply(lambda symbol: s.parse_tick_data(symbol)[0])
            #     df['temp'] = df['ticker'].apply(
            #         lambda symbol: si.get_data(symbol+".NS", end_date=end).to_dict("records")[-1]
            #     )
            #     df['initial'] = df['temp'].apply(lambda x: x.get("close"))
            #     df['delta'] = df['live_price'] - df['initial']
            #     df['percentage'] = (df['delta'] / df['initial']) * 100.0
            #     del df['temp']
            #     del df['initial']

            return ResponseOk({
                "data": res
            })
        except Exception as e:
            return ResponseBadRequest({
                "debug": str(e)
            })


class GetWatchListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            symbols = cache.get(f"watchlist_{request.user.id}")
            symbols_exp = cache.get(f"watchlist_exp_{request.user.id}")
            cached = True

            if not symbols or datetime.datetime.now() >= symbols_exp:
                cached = False
                watchlist = TopSearched.objects.filter(userid=request.user).order_by("-id")
                symbols = list(watchlist.values("stock__symbol"))

                cache.set(f"watchlist_{request.user.id}", symbols)
                cache.set(f"watchlist_exp_{request.user.id}", datetime.datetime.now() + datetime.timedelta(seconds=10))

            s = Singleton2.get_instance("")
            result = []
            start, end = get_day_range(get_previous_business_day())
            for w in symbols:
                symbol = w.get("stock__symbol")
                live_price = s.parse_tick_data(symbol)[0]
                x = {
                    'ticker': symbol,
                    'live_price': live_price,
                }
                if not live_price:
                    live_price = si.get_live_price(x['ticker'] + ".NS")
                    x['live_price'] = live_price

                x['initial'] = get_all_open_prices(x['ticker'] + ".NS")['1d']
                if np.isnan(x['initial']):
                    x['initial'] = 0.0

                x['delta'] = x['live_price'] - x['initial']

                x['percentage'] = num_quantize((x['delta'] / x['initial']) * 100) if x['initial'] else 0.0
                x['delta'] = num_quantize(x['delta'])
                x['initial'] = num_quantize(x['initial'])
                x['live_price'] = num_quantize(x['live_price'])

                if x['delta'] == -0.0:
                    x['delta'] = 0.0
                if x['percentage'] == -0.0:
                    x['percentage'] = 0.0

                if x['delta'] < 0:
                    x['color'] = "#ff5000"
                    x['color_text'] = "red"
                else:
                    x['color'] = "#00ff39"
                    x['color_text'] = "green"
                result.append(x)
            return ResponseOk({"data": result, "cached": cached})
        except Exception as e:
            return ResponseBadRequest({"debug": str(e)})


class GetUpcomingActivityAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        try:
            transactions = Transaction.objects.filter(
                userid=request.user.id, status="pending", stockticker__symbol__iexact=symbol
            ).order_by("-id")
            count = transactions.count()
            result = []

            # Dummy data
            # for transaction in range(0, 3):
            #     result.append({
            #         'id': 1,
            #         'symbol': "ACC",
            #         'time': datetime.datetime.now(),
            #         'size': 1230,
            #         'status': "limit_order",
            #         'order_type': "limit_order",
            #         'limit_price': 1233,
            #         'transaction_type': "sell",
            #     })

            for transaction in transactions:
                result.append({
                    'id': transaction.id,
                    'symbol': transaction.stockticker.symbol,
                    'time': transaction.time,
                    'expires': transaction.expires,
                    'size': transaction.size,
                    'status': transaction.status.replace("_", " ").title(),
                    'order_type': transaction.ordertype.replace("_", " ").title(),
                    'limit_price': transaction.limit_price,
                    'transaction_type': transaction.transaction_type.replace("_", " ").title(),
                })
            return ResponseOk({
                "upcoming": result,
                "count": len(result)
            })
        except Exception as e:
            return ResponseBadRequest({"debug": str(e)})


def include_symbol(symbol):
    if StockNames.objects.filter(symbol__iexact=symbol).exists():
        return 1
    return 0


class GetTopGainers(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        try:
            s = Singleton2.get_instance("")

            root = settings.MEDIA_ROOT
            full_path = os.path.join(root, "most_active.csv")

            if not os.path.exists(full_path):
                res = []
            else:
                df = pd.read_csv(full_path)
                if not df.empty:
                    # price, change=percent, url, symbol=symbol
                    # df['price'] = df['symbol'].apply(lambda x: num_quantize(s.parse_tick_data(x)[0]))
                    df['change'] = df['change'].apply(lambda x: num_quantize(x))
                    # del df['percent']
                    # del df['Unnamed: 0']
                    # del df['percent_abs']
                    df['url'] = df['symbol'].apply(lambda x: f"/accounts/dashboard/stocks/NSE:{x}/")
                    res = df.to_dict("records")
                else:
                    res = []
            return ResponseOk({
                "cached": True,
                "active": res,
                "count": len(res)
            })

            # active = cache.get("most_active")
            # active_exp = cache.get("most_active_expiry")
            # cached = True
            # if not active or datetime.datetime.now() >= active_exp:
            #     cached = False
            #     active = get_most_active()
            #     for a in active:
            #         a['price'] = float(a['ltp'].replace(",", ""))
            #         a['change'] = float(a['netPrice'].replace(",", ""))
            #         a['url'] = f"/accounts/dashboard/stocks/NSE:{a['symbol']}/"
            #
            #         del a['ltp'], a['netPrice'], a['series'], a['openPrice'], a['highPrice'], a['lowPrice'], \
            #             a['previousPrice'], a['tradedQuantity'], a['turnoverInLakhs'], a['lastCorpAnnouncementDate'], \
            #             a['lastCorpAnnouncement']
            #
            #     cache.set("most_active", active)
            #     cache.set("most_active_expiry", datetime.datetime.now() + datetime.timedelta(hours=6))
            #
            # # if not active.empty:
            # #     active = active[["symbol", "ltp", "netPrice"]]
            # #     active['price'] = active['ltp'].apply(lambda x: float(x.replace(",", "")))
            # #     active['change'] = active['netPrice'].apply(lambda x: float(x.replace(",", "")))
            # #     active['url'] = active['symbol'].apply(lambda x: "/accounts/dashboard/stocks/NSE:{}/".format(x))
            # #     # active['include'] = active['Symbol'].apply(lambda x: include_symbol(x))
            # #     # active = active[active['include'] == 1]
            # #     del active['netPrice']
            # #     del active['ltp']
            # #     res = active.to_dict("records")
            # # else:
            # #     res = []
            # return ResponseOk({
            #     "cached": cached,
            #     "active": active,
            #     "count": len(active)
            # })
        except Exception as e:
            return ResponseBadRequest(str(e))

class UpdateBuyingPower(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        buyingpower = request.data.get("buyingpower")

        is_num = False
        try:
            num = float(buyingpower)
            is_num = True
        except:
            pass

        if is_num:
            identity_instance = UserDetails.objects.get(
                                    user=request.user).identity
            identity_instance.buyingpower = buyingpower
            identity_instance.save()
            return Response("Buying power updated!")
        else:
            return Response("Please enter valid number!")
