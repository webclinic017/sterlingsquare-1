from django.shortcuts import render
from .serializers import HistoryDataSerializer, FileSerializer, StockSerializer, PortfolioSerializer
from rest_framework import generics
# from tickerstore.store import TickerStore
from datetime import date
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

import pandas as pd
from .models import InstrumentList
from stock_react_api.core.models import my_stocks, portfolio, User
from django.contrib.auth.decorators import login_required
import yfinance as yf
from rest_framework.views import APIView
import json
import pyrebase
from django.core import serializers
from django.forms.models import model_to_dict
from django.http import JsonResponse


class HistoryDataView(generics.CreateAPIView):
    # Get historical data of a stock
    serializer_class = HistoryDataSerializer

    def post(self, request):
        symbol = request.data.get('symbol')
        symbol = symbol + ".NS"
        start = request.data.get('start')
        end = request.data.get('end')
        interval = request.data.get('interval_in_days')
        interval = str(interval) + 'd'
        print(start)
        tickerData = yf.Ticker(symbol)
        data = tickerData.history(period=interval, start=start, end=end)
        json = data.to_json()
        print(data)
        return Response(json)


class FileUploadViewSet(generics.CreateAPIView):
    # Create a new portfolio with a file attached and portfolio_name
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = FileSerializer

    def create(self, request):
        serializer_class = FileSerializer(data=request.data)
        portfolio_count = portfolio.objects.filter(user=request.user).count()
        if 'file' not in request.FILES or not serializer_class.is_valid():
            # If file not present
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            if portfolio_count < 3:
                portfolio_name = request.data['portfolio_name']
                df = pd.read_excel(request.FILES['file'])
                # print('test:', list(df.columns))
                if list(df.columns) == ['tradingsymbol', 'buy_price', 'quantity']:
                    data = handle_uploaded_file(df, request.user, portfolio_name)
                    return Response(status=status.HTTP_201_CREATED, data=data)
                # elif list(df.columns) != ['tradingsymbol', 'buy_price', 'quantity']:
                #     return Response(
                #         "Upload file column name should be exact as i.e 'tradingsymbol' in first column, 'buy_price' in second column and 'quantity' in third column ",
                #         status=status.HTTP_200_OK)
                else:
                    return Response("Upload file is not in proper format please refer from sample file",
                                    status=status.HTTP_200_OK)

            else:
                message = "You already have 3 active portfolios. Inorder to create new please delete previous portfolio."
                return Response(message, status=status.HTTP_200_OK)


class FileUploadErrViewSet(generics.CreateAPIView):
    # Check for error while creating a new portfolio with a file attached and portfolio_name
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = FileSerializer

    def create(self, request):
        serializer_class = FileSerializer(data=request.data)
        portfolio_count = portfolio.objects.filter(user=request.user).count()
        if 'file' not in request.FILES or not serializer_class.is_valid():
            # If file not present
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            if portfolio_count < 3:
                portfolio_name = request.data['portfolio_name']
                df = pd.read_excel(request.FILES['file'])
                # print('test:', list(df.columns))
                if list(df.columns) == ['tradingsymbol', 'buy_price', 'quantity']:
                    data = handle_uploaded_file_err(df, request.user, portfolio_name)
                    return Response(status=status.HTTP_200_OK, data=data)
                # elif list(df.columns) != ['tradingsymbol', 'buy_price', 'quantity']:
                #     return Response(
                #         "Upload file column name should be exact as i.e 'tradingsymbol' in first column, 'buy_price' in second column and 'quantity' in third column ",
                #         status=status.HTTP_200_OK)
                else:
                    return Response("Upload file is not in proper format please refer from sample file",
                                    status=status.HTTP_200_OK)

            else:
                message = "You already have 3 active portfolios. Inorder to create new please delete previous portfolio."
                return Response(message, status=status.HTTP_201_CREATED)


class MyPortfolio(viewsets.GenericViewSet,
                  mixins.ListModelMixin, mixins.CreateModelMixin, ):
    # Get all the portfolio of current user
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = portfolio.objects.all()
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        print(self.queryset)
        return self.queryset.filter(user=self.request.user).order_by('-name')


class Dashboard_mystocks(generics.CreateAPIView):
    # Get stock data of requested portfolio of current user or delete requested portfolio (depending upon action).
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = my_stocks.objects.all()
    serializer_class = StockSerializer

    def post(self, request):
        print("REQUEST:", request.data)
        my_portfolio = portfolio.objects.filter(user=self.request.user, name=request.data['portfolio_name']).first()
        print("PORTFOLIO: ", my_portfolio)
        if my_portfolio:
            if (request.data['action'] == 'view'):
                # filter stocks of requested portfolio
                data = self.queryset.filter(portfolio=my_portfolio).order_by('-name')
                print("DATA: ", data)
                new_list = []
                # Storing stocks in dictionary
                for entry in data:
                    print(entry.instrument_token)
                    temp = {'portfolio': entry.portfolio.id, 'instrument_token': entry.instrument_token,
                            'tradingsymbol': entry.tradingsymbol, 'name': entry.name,
                            'buy_price': entry.buy_price, 'quantity': entry.quantity}
                    new_list.append(temp)
                print(new_list)
                return Response(data=new_list)
            elif (request.data['action'] == 'delete'):
                # deleting requested portfolio
                my_portfolio.delete()
                # curr_user = self.request.user
                # curr_user.active_portfolio = curr_user.active_portfolio - 1
                # curr_user.save()
                data = "Portfolio " + request.data['portfolio_name'] + " deleted successfully"
                return Response(status=status.HTTP_201_CREATED, data=data)
            else:
                # If action is neither "view" nor "delete"
                data = "Invalid action. Only [delete] and [view] action allowed."
                return Response(status=status.HTTP_201_CREATED, data=data)
        else:
            # If portfolio don't exist
            data = "Requested portfolio don't exist."
            return Response(status=status.HTTP_201_CREATED, data=data)


def handle_uploaded_file(df, user, portfolio_name):
    config = {
        "apiKey": "AIzaSyCU9JP2yixeKjw3NE30Pb0I0D0UQjV94gA",
        "authDomain": "kiteconnect-stock.firebaseapp.com",
        "databaseURL": "https://kiteconnect-stock-default-rtdb.firebaseio.com",
        "projectId": "kiteconnect-stock",
        "storageBucket": "kiteconnect-stock.appspot.com",
        "messagingSenderId": "981866107803",
        "appId": "1:981866107803:web:568ffc6b464656a6f4c73e",
        "measurementId": "G-9BRWTZYS5C"
    }

    firebase = pyrebase.initialize_app(config)
    authe = firebase.auth()
    database = firebase.database()
    curr_user = user
    # portfolio_name is required
    if portfolio_name != '' and portfolio_name:
        if portfolio.objects.filter(name=portfolio_name, user=user).first():
            # If already exist
            return "Portfolio with name " + str(portfolio_name) + " already exist"
    else:
        return "Portfolio name is required"
    # create new portfolio
    my_portfolio = portfolio.objects.create(name=portfolio_name, user=user)
    # curr_user.active_portfolio = curr_user.active_portfolio + 1
    # curr_user.save()
    # print(curr_user.active_portfolio)
    my_portfolio.save()
    data = df
    err = []
    t = 0
    # validating excel enteries for correct TickerSymbol and saving it to database with corresponding instrument token appended
    for index, row in data.iterrows():
        stock_token = InstrumentList.objects.filter(tradingsymbol=row['tradingsymbol']).first()
        print(stock_token)
        # If tradingSymol exist
        if (stock_token):
            # Quantity must not be negative
            if (row['quantity'] >= 0):
                token = stock_token.instrument_token
                name = stock_token.name
                if pd.notna(row['buy_price']):
                    buy_price = row['buy_price']
                else:
                    # If buy price not present then save it's last_price
                    buy_price = database.child("Stock").child(token).child('last_price').get().val()
                    print(buy_price)
                stock = my_stocks.objects.create(portfolio=my_portfolio, instrument_token=token, name=name,
                                                 buy_price=buy_price, quantity=row['quantity'],
                                                 tradingsymbol=row['tradingsymbol'])
                stock.save()
            else:
                err.append(row['tradingsymbol'] + " (Invalid Quantity)")
                t = t + 1
        else:
            err.append(row['tradingsymbol'] + " (Invalid Tranding Symbol)")
            t = t + 1

    return str(t) + " stocks failed: " + str(err)


def handle_uploaded_file_err(df, user, portfolio_name):
    # Handling errors in file enteries
    data = df
    err = []
    t = 0
    print(portfolio_name)
    if portfolio_name != '' and portfolio_name:
        if portfolio.objects.filter(name=portfolio_name, user=user).first():
            return "Portfolio with name " + str(portfolio_name) + " already exist"
    else:
        return "Portfolio name is required"
    for index, row in data.iterrows():
        stock_token = InstrumentList.objects.filter(tradingsymbol=row['tradingsymbol']).first()
        print(stock_token)
        if (stock_token):
            if (row['quantity'] < 0):
                err.append(row['tradingsymbol'] + " (Invalid Quantity)")
                t = t + 1
        else:
            err.append(row['tradingsymbol'] + " (Invalid Tranding Symbol)")
            t = t + 1

    return str(len(data) - t) + " entries valid. | " + str(t) + " entries invalid: " + str(err)


def home(request):
    return render(request, 'kiteconnectapp/dashboard.html', context={})


class AddInstrumentToken(APIView):
    def post(self, request):
        # used for uploading NSE stock data to Instrument List
        # data = pd.read_excel('NSE_data.xlsx')
        try:
            data = pd.read_excel(request.FILES['file'])

            for index, row in data.iterrows():
                InstrumentList.objects.create(instrument_token=row['instrument_token'],
                                              exchange_token=row['exchange_token'],
                                              tradingsymbol=row['tradingsymbol'], name=row['name'])
                # print(index)
                temp = [{"message": "successfully uploaded"}]
            return Response(temp, status=status.HTTP_200_OK)
        except:
            temp = [{"message": "error"}]
            return Response(temp, status=status.HTTP_404_NOT_FOUND)
