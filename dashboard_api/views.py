from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
# from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from accounts.models import *
from .dashboard_api_serializer import *
from rest_framework.permissions import AllowAny
from stock_react_api.core.models import *
from .models import *
from datetime import timedelta
from datetime import datetime
import pyrebase
import json
import logging
import pandas as pd
import statistics
from dateutil.relativedelta import relativedelta


class DashboardApiLogin(APIView):
    def post(self, request):
        """
        login with email and password
        Parameters
        ----------
        request
        Returns
        -------
        """
        if User.objects.filter(email=request.data['email']):
            try:
                check = User.objects.get(email=request.data['email'])
                if check_password(request.data["password"], check.password):
                    token = Token.objects.get(user=User.objects.get(email=request.data["email"]))
                    return Response({"token": str(token)}, status=status.HTTP_200_OK)
                else:
                    temp = [{"message": "Incorrect Password"}]
                    return Response(temp, status=status.HTTP_404_NOT_FOUND)
            except:
                temp = [{"message": "Incorrect Email or Password"}]
                return Response(temp, status=status.HTTP_404_NOT_FOUND)

        else:
            temp = [{"message": "Incorrect Email"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


class DashboardApiGetRealisedUnrealisedGainLoss(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        get realised and unrealised gain loss of user
        Parameters
        ----------
        request
        format
        Returns
        -------
        """
        try:
            auth = request.headers.get('Authorization')
            token = Token.objects.get(key=auth.replace("Token ", ""))
            result = GainLossHistory.objects.filter(userid=token.user_id)
            serializer = GainLossHistorySerializer(result, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            temp = [{"message": "data not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


class DashboardApiGetBuyingPower(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        get buying power of user
        Parameters
        ----------
        request
        format
        Returns
        -------
        """
        try:
            try:
                auth = request.headers.get('Authorization')
                token = Token.objects.get(key=auth.replace("Token ", ""))
                res = UserDetails.objects.get(user=token.user_id)
                result = IdentityDetails.objects.filter(id=res.id)
                serializer = IdentityDetailsSerializer(result, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except:
                temp = [{"message": "data not found"}]
                return Response(temp, status=status.HTTP_404_NOT_FOUND)
        except:
            temp = [{"message": "not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


# class DashboardApiPortfolioPerformanceStock(APIView):
#     # permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         auth = request.headers.get('Authorization')
#         token = Token.objects.get(key=auth.replace("Token ", ""))
#         user_id = token.user_id
#         portfolio_name = request.data['portfolio_name']
#         my_portfolio = portfolio.objects.filter(user=user_id, name=portfolio_name).first()
#         data = my_stocks.objects.filter(portfolio=my_portfolio).order_by('-name')
#         new_list = []
#         # for entry in data:
#         #     new_list.append(entry.instrument_token)
#         # print('test:', new_list)
#         config = {
#             "apiKey": "AIzaSyCU9JP2yixeKjw3NE30Pb0I0D0UQjV94gA",
#             "authDomain": "kiteconnect-stock.firebaseapp.com",
#             "databaseURL": "https://kiteconnect-stock-default-rtdb.firebaseio.com",
#             "projectId": "kiteconnect-stock",
#             "storageBucket": "kiteconnect-stock.appspot.com",
#             "messagingSenderId": "981866107803",
#             "appId": "1:981866107803:web:568ffc6b464656a6f4c73e"
#             # measurementId: "G-9BRWTZYS5C"
#         }
#
#         firebase = pyrebase.initialize_app(config)
#         logging.basicConfig(level=logging.DEBUG)
#         sym=[]
#         total_qty=[]
#         t_current_day_close_price=[]
#         t_previous_day_close_price=[]
#         for entry in data:
#             sym.append(entry.tradingsymbol)
#             quantity=entry.quantity
#             current_day_close_price=firebase.database().child("Stock").child(entry.instrument_token).child("last_price").get().val()
#             previous_day_close_price=firebase.database().child("Stock").child(entry.instrument_token).child("close").get().val()
#             t_current_day_close_price.append(quantity*current_day_close_price)
#             t_previous_day_close_price.append(quantity*previous_day_close_price)
#
#         print('test:', sym)
#         print('test1:', total_qty)
#         print('test2:', t_current_day_close_price)
#         print('test3:', t_previous_day_close_price)
#
#         current_portfolio_value = sum(t_current_day_close_price)
#         previous_day_portfolio_value =  sum(t_previous_day_close_price)
#         portfolio_performance = (current_portfolio_value - previous_day_portfolio_value)/previous_day_portfolio_value
#         print('portfolio_performance:',portfolio_performance*100)
#         return Response("new_list")
from django.db.models import Count


class DashboardApiSectorWiseData(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        get sector wise percentage value of portfolio
        """
        try:
            auth = request.headers.get('Authorization')
            token = Token.objects.get(key=auth.replace("Token ", ""))
            user_id = token.user_id
            portfolio_name = request.data['portfolio_name']
            my_portfolio = portfolio.objects.filter(user=user_id, name=portfolio_name).first()
            data = my_stocks.objects.filter(portfolio=my_portfolio).order_by('-name')

            config = {
                "apiKey": "AIzaSyCU9JP2yixeKjw3NE30Pb0I0D0UQjV94gA",
                "authDomain": "kiteconnect-stock.firebaseapp.com",
                "databaseURL": "https://kiteconnect-stock-default-rtdb.firebaseio.com",
                "projectId": "kiteconnect-stock",
                "storageBucket": "kiteconnect-stock.appspot.com",
                "messagingSenderId": "981866107803",
                "appId": "1:981866107803:web:568ffc6b464656a6f4c73e"
            }
            firebase = pyrebase.initialize_app(config)
            logging.basicConfig(level=logging.DEBUG)
            sym = []
            t_current_day_last_price = []
            dataa = {}
            data_qty = {}
            for entry in data:
                sym.append(entry.tradingsymbol)
                quantity = entry.quantity
                current_day_last_price = firebase.database().child("Stock").child(entry.instrument_token).child(
                    "last_price").get().val()
                t_current_day_last_price.append(round((quantity * current_day_last_price), 2))
                dataa[entry.tradingsymbol] = current_day_last_price
                data_qty[entry.tradingsymbol] = quantity
            # print('test:', sym)
            df = pd.DataFrame.from_records(StockGeneralInfo.objects.filter(symbol__in=sym).values('sector', 'symbol'))
            # print('try:', df)
            group = df.groupby('sector')
            df2 = group.apply(lambda x: x['symbol'].unique())
            js = df2.to_json(orient='index')
            res = json.loads(js)
            # print('try:', res)
            req_data = {}
            for key, value in res.items():
                s = 0
                for i in value:
                    # print('val:',i)
                    dt = dataa[str(i)] * data_qty[str(i)]
                    s = s + dt
                    # print('vasssssl:', dt)
                sector_percent = (s / sum(t_current_day_last_price)) * 100
                req_data[key] = round(sector_percent, 2)
            return Response(req_data, status=status.HTTP_200_OK)
        except:
            temp = [{"message": "data not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


# class DashboardApiTesting(APIView):
#     # permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         config = {
#             "apiKey": "AIzaSyCU9JP2yixeKjw3NE30Pb0I0D0UQjV94gA",
#             "authDomain": "kiteconnect-stock.firebaseapp.com",
#             "databaseURL": "https://kiteconnect-stock-default-rtdb.firebaseio.com",
#             "projectId": "kiteconnect-stock",
#             "storageBucket": "kiteconnect-stock.appspot.com",
#             "messagingSenderId": "981866107803",
#             "appId": "1:981866107803:web:568ffc6b464656a6f4c73e"
#         }
#         firebase = pyrebase.initialize_app(config)
#         logging.basicConfig(level=logging.DEBUG)
#
#         user = User.objects.all().values_list('id', flat=True)
#         for i in user:
#             my_portfolio = portfolio.objects.filter(user=i).values_list('id', flat=True)
#             for j in my_portfolio:
#                 data = my_stocks.objects.filter(portfolio=j).order_by('-name')
#                 print('data:', data)
#                 sym = []
#                 t_quantity = []
#                 t_cost = []
#                 t_value = []
#                 for entry in data:
#                     sym.append(entry.tradingsymbol)
#                     update_date = firebase.database().child("last_updated").get().val().split(' ')[0]
#                     quantity = entry.quantity
#                     t_quantity.append((quantity))
#                     current_day_last_price = firebase.database().child("Stock").child(entry.instrument_token).child(
#                         "last_price").get().val()
#                     t_value.append(round((quantity * current_day_last_price), 2))
#                     print('sada:', float(entry.buy_price) * quantity)
#                     t_cost.append(round((float(entry.buy_price)) * quantity, 2))
#                 print('asdada:', t_cost)
#                 total_value = sum(t_value)
#                 total_cost = sum(t_cost)
#                 total_quantity = sum(t_quantity)
#                 yesterday_date = datetime.strptime(update_date, '%Y-%m-%d').date() - timedelta(days=1)
#                 if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=yesterday_date):
#                     try:
#                         prev_data = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j, date=yesterday_date)
#                         prev_tot_val = prev_data.total_value
#                         print('aaaaaaaaa:',prev_tot_val)
#                         prev_daily_return = prev_data.daily_return
#                         print('ggggggggg:',((float(total_value) - float(prev_tot_val)) / float(prev_tot_val)))
#                         daily_return = ((float(total_value) - float(prev_tot_val)) / float(prev_tot_val)) * 100
#                         cummeletive_return = daily_return + prev_daily_return
#                     except:
#                         pass
#                 else:
#                     daily_return = 0
#                     cummeletive_return = 0
#
#                 if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=update_date):
#                     data = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j, date=update_date)
#                     data.total_cost = total_cost
#                     data.total_value = total_value
#                     data.total_quantity = total_quantity
#                     data.daily_return = round(daily_return,2)
#                     data.cummeletive_return = round(cummeletive_return,2)
#                     data.save()
#                 else:
#                     performance = PortfolioPerformance(user_id_id=i, portfolio_id_id=j, total_cost=total_cost,
#                                                        total_value=total_value, total_quantity=total_quantity,
#                                                        date=update_date, daily_return=round(daily_return,2),
#                                                        cummeletive_return=round(cummeletive_return,2))
#                     performance.save()
#
#             print("------------------")
#
#         return Response("ok", status=status.HTTP_200_OK)


def DailyUpdatePortfolioPerformanceData():
# class DailyUpdatePortfolioPerformanceData(APIView):
#
#     def post(self, request):
    """
    daily update performance table data for all users
    """
    try:
        try:
            config = {
                "apiKey": "AIzaSyCU9JP2yixeKjw3NE30Pb0I0D0UQjV94gA",
                "authDomain": "kiteconnect-stock.firebaseapp.com",
                "databaseURL": "https://kiteconnect-stock-default-rtdb.firebaseio.com",
                "projectId": "kiteconnect-stock",
                "storageBucket": "kiteconnect-stock.appspot.com",
                "messagingSenderId": "981866107803",
                "appId": "1:981866107803:web:568ffc6b464656a6f4c73e"
            }
            firebase = pyrebase.initialize_app(config)
            logging.basicConfig(level=logging.DEBUG)

            user = User.objects.all().values_list('id', flat=True)
            for i in user:
                my_portfolio = portfolio.objects.filter(user=i).values_list('id', flat=True)
                for j in my_portfolio:
                    data = my_stocks.objects.filter(portfolio=j).order_by('-name')
                    # print('data:', data)
                    sym = []
                    t_quantity = []
                    t_cost = []
                    t_value = []
                    stock_val = {}

                    # update_date = firebase.database().child("last_updated").get().val().split(' ')[0]
                    update_date = "2020-08-23"

                    if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=update_date):
                        data_del = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j, date=update_date)
                        data_del.delete()
                    else:
                        pass
                    for entry in data:
                        sym.append(entry.tradingsymbol)

                        quantity = entry.quantity
                        t_quantity.append((quantity))
                        current_day_last_price = firebase.database().child("Stock").child(entry.instrument_token).child(
                            "last_price").get().val()
                        t_value.append(round((quantity * current_day_last_price), 2))
                        # print('sada:', float(entry.buy_price) * quantity)
                        t_cost.append(round((float(entry.buy_price)) * quantity, 2))
                        stock_val[entry.tradingsymbol] = round((quantity * current_day_last_price), 2)

                    # total_value = sum(t_value)
                    total_value = 53525
                    # total_cost = sum(t_cost)
                    total_cost = 53100
                    # total_quantity = sum(t_quantity)
                    total_quantity = 55
                    yesterday_date = datetime.strptime(update_date, '%Y-%m-%d').date() - timedelta(days=1)


                    # print('asdsas:',lat_entry_data)
                    if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j):
                        lat_entry_data = \
                        PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j).order_by('-date')[0]
                        dte_date = lat_entry_data.date

                    else:
                        dte_date = None
                        pass
                    # if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=yesterday_date):
                    if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=dte_date):
                        try:
                            # prev_data = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j,
                            #                                              date=yesterday_date)
                            prev_data = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j,
                                                                         date=lat_entry_data.date)
                            prev_tot_val = prev_data.total_value

                            prev_daily_return = prev_data.daily_return
                            prev_cummeletive_return = prev_data.cummeletive_return

                            prev_sym = prev_data.symbols
                            dict_val = prev_data.stock_value
                            symm = ['AKSHARCHEM', 'AKASH', 'AJANTPHARM', 'AIAENG', 'AAVAS', 'AARVI', 'AARTIDRUGS']
                            if set(prev_sym) == set(symm):  # symm i.e sym
                                daily_return = ((float(total_value) - float(prev_tot_val)) / float(prev_tot_val)) * 100

                            else:
                                t_diff_sym = []
                                diff_sym = set(prev_sym).difference(symm)
                                for dt in list(diff_sym):
                                    val_data = dict_val.get(dt)
                                    t_diff_sym.append(val_data)
                                daily_return = ((float(total_value) - (float(prev_tot_val) - 25210)) / (
                                        float(prev_tot_val) - 25210)) * 100
                                # daily_return=((float(total_value) - (float(prev_tot_val)-sum(t_diff_sym))) / (float(prev_tot_val)-sum(t_diff_sym))) * 100

                            cummeletive_return = daily_return + prev_cummeletive_return
                        except:
                            pass
                    else:
                        daily_return = 0
                        cummeletive_return = 0

                    if PortfolioPerformance.objects.filter(user_id_id=i, portfolio_id_id=j, date=update_date):
                        data_dl = PortfolioPerformance.objects.get(user_id_id=i, portfolio_id_id=j, date=update_date)
                        data_dl.delete()
                        performance = PortfolioPerformance(user_id_id=i, portfolio_id_id=j, total_cost=total_cost,
                                                           total_value=total_value, total_quantity=total_quantity,
                                                           date=update_date, daily_return=round(daily_return, 2),
                                                           cummeletive_return=round(cummeletive_return, 2), symbols=sym,
                                                           stock_value=stock_val)
                        performance.save()
                        # print('asdadadsasdasdsa:',data.symbols)
                        # data.total_cost = total_cost
                        # data.total_value = total_value
                        # data.total_quantity = total_quantity
                        # data.symbols = sym
                        # data.stock_value = stock_val
                        # data.daily_return = round(daily_return, 2)
                        # data.cummeletive_return = round(cummeletive_return, 2)
                        # data.save()
                    else:
                        performance = PortfolioPerformance(user_id_id=i, portfolio_id_id=j, total_cost=total_cost,
                                                           total_value=total_value, total_quantity=total_quantity,
                                                           date=update_date, daily_return=round(daily_return, 2),
                                                           cummeletive_return=round(cummeletive_return, 2), symbols=sym,
                                                           stock_value=stock_val)
                        performance.save()

            print("-----success-------------")

            # return Response("success", status=status.HTTP_200_OK)
            return "success"
        except Exception as e:
            print("-----error1-------------", e)
            pass
    # except:
    except Exception as e:
        print("-----error2-------------",e)
        # return Response("error", status=status.HTTP_200_OK)
        return "error"


class DashboardApiGetPortfolioStatistics(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        api for portfolio statistics data
        """
        try:
            auth = request.headers.get('Authorization')
            token = Token.objects.get(key=auth.replace("Token ", ""))
            user_id = token.user_id
            portfolio_name = request.data['portfolio_name']

            my_portfolio = portfolio.objects.get(user=user_id, name=portfolio_name)

            time_period = request.data['time_period']
            if time_period == "1d":
                dte = datetime.today() - relativedelta(days=1)
                pass
            elif time_period == "1w":
                dte = datetime.today() - relativedelta(days=7)
                pass
            elif time_period == "1m":
                dte = datetime.today() - relativedelta(months=1)
                pass
            elif time_period == "6m":
                dte = datetime.today() - relativedelta(months=6)
                pass
            elif time_period == "1y":
                dte = datetime.today() - relativedelta(years=1)
                pass
            elif time_period == "2y":
                dte = datetime.today() - relativedelta(years=2)
                pass
            elif time_period == "3y":
                dte = datetime.today() - relativedelta(years=3)
                pass
            else:
                return Response("enter proper time_period format", status=status.HTTP_404_NOT_FOUND)

            items = PortfolioPerformance.objects.filter(user_id_id=user_id, portfolio_id_id=my_portfolio, date__gte=dte)

            t_daily_return = []
            for i in items:
                t_daily_return.append(i.daily_return)
            x = statistics.mean(t_daily_return)

            return Response(
                {"time_period": time_period, "mean": round(x, 2), "stdev": round(statistics.stdev(t_daily_return), 2)},
                status=status.HTTP_200_OK)
        except:
            temp = [{"message": "data not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)


class DashboardApiGetPortfolioPerformance(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        api for portfolio performance data
        """
        try:
            auth = request.headers.get('Authorization')
            token = Token.objects.get(key=auth.replace("Token ", ""))
            user_id = token.user_id
            portfolio_name = request.data['portfolio_name']

            my_portfolio = portfolio.objects.get(user=user_id, name=portfolio_name)

            time_period = request.data['time_period']
            if time_period == "1d":
                dte = datetime.today() - relativedelta(days=1)
                pass
            elif time_period == "1w":
                dte = datetime.today() - relativedelta(days=7)
                pass
            elif time_period == "1m":
                dte = datetime.today() - relativedelta(months=1)
                pass
            elif time_period == "6m":
                dte = datetime.today() - relativedelta(months=6)
                pass
            elif time_period == "1y":
                dte = datetime.today() - relativedelta(years=1)
                pass
            elif time_period == "2y":
                dte = datetime.today() - relativedelta(years=2)
                pass
            elif time_period == "3y":
                dte = datetime.today() - relativedelta(years=3)
                pass
            else:
                return Response("enter proper time_period format", status=status.HTTP_404_NOT_FOUND)

            items = PortfolioPerformance.objects.filter(user_id_id=user_id, portfolio_id_id=my_portfolio,
                                                        date__gte=dte).order_by('-date')
            dta = {}
            for i in items:
                dta[str(i.date)] = i.cummeletive_return

            return Response(dta, status=status.HTTP_200_OK)
        except:
            temp = [{"message": "data not found"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)
