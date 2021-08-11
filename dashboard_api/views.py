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


# from rest_framework.authentication import TokenAuthentication, BasicAuthentication
# from rest_framework.permissions import IsAuthenticated


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


import pyrebase
import json
import logging

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
import pandas as pd


class DashboardApiSectorWiseData(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class DashboardApiTesting(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
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
                print('data:', data)
                sym = []
                for entry in data:
                    sym.append(entry.tradingsymbol)
                print('asdada:', sym)

            print("------------------")

        return Response("ok", status=status.HTTP_200_OK)
