import json
import time

from kiteconnect import KiteTicker, KiteConnect
import datetime
from dateutil.relativedelta import relativedelta
from yahoo_fin import stock_info as si
from accounts.models import *
from threading import Thread
import asyncio
import pandas as pd
from sterling_square.TickerSingleton import Singleton2
from accounts.tasks import initialize_singleton
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.consumer import AsyncConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils.timezone import make_aware
from utils.date_utils import get_day_range, is_market_open_now, BUSINESS_HOURS_START, BUSINESS_HOURS_END
from utils.util_functions import read_zerodha_credentials, price_change, num_quantize, parse_tick_data
import nest_asyncio


# def parse_tick_data(tick_data, token):
#     """
#     parse and return the live price
#     """
#     df = pd.DataFrame(tick_data)
#     if not df.empty:
#         df = df[df['instrument_token'] == token]
#         if not df.empty:
#             t = df.to_dict("records")
#             return t[0]['last_price'], datetime.datetime.now()
#         return None, None
#     return None, None


# Original Version
class Consumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.symbol = self.scope['url_route']['kwargs']['symbol']
            await self.accept()
            kws = KiteConnect(api_key="fact6majxka99prm")
            instruments = kws.instruments(exchange='NSE')
            for i in instruments:
                if i['tradingsymbol'].upper() == self.symbol.upper():
                    self.token = i['instrument_token']
                    break
            # self.token=5633
            # await self.accept()
            await self.channel_layer.group_add(self.symbol, self.channel_name)
            # self.start_kitesocket()
            Thread(target=self.start_kitesocket).start()
            # await self.receive(text_data="message")
        except Exception as e:
            print(e)

    async def disconnect(self, close_code):
        print('here')
        await self.close()
        if self.kws is not None:
            self.kws.on_close()
        pass

    def receive(self, text_data):
        try:
            "Handle incoming WebSocket data"
            nest_asyncio.apply()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send(json.dumps({
                "close": str(text_data[0]['last_price']), "date": str(
                    datetime.datetime.now())}), ))
        except Exception as e:
            print("error is", e)

    async def live_rate(self, text):
        print("in")
        await self.send(json.dumps({
            "close": str(text[0]['last_price']), "date": str(
                datetime.datetime.now())}))

    def start_kitesocket(self):
        print("called...")
        global tokens
        self.kws = KiteTicker(api_key='fact6majxka99prm',
                              access_token='o05yxWXtSr3mluChU6zctvSd75Yqi9QN')
        tokens = [self.token]
        print(tokens)
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error

        self.kws.connect(threaded=True)
        count = 0
        while True:
            count += 1
            if (count % 2 == 0):
                if self.kws.is_connected():
                    self.kws.set_mode(self.kws.MODE_FULL, tokens)
                else:
                    if self.kws.is_connected():
                        self.kws.set_mode(self.kws.MODE_FULL, tokens)
                time.sleep(1)

    # def send_message_ws(self,message):
    #     self.receive(message)

    def on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        try:
            print("tick")
            self.receive(ticks)
        except Exception as e:
            print(e)

    def on_connect(self, ws, response):
        global tokens
        ws.subscribe(tokens)

        ws.set_mode(ws.MODE_FULL, tokens)

    def on_close(self, ws):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        print("called onclose")
        ws.stop()
        # self.kws.stop()

    def on_error(self, ws, code, reason):
        print('inside the error block')
        print(reason)
        ws.stop()
        self.close()


class ConsumerV2(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(ConsumerV2, self).__init__(*args, **kwargs)

        self.symbol = None
        self.kws = None

        self.token = []

        self.credentials = getattr(settings, "ZERODHA_CREDENTIALS")
        if not self.credentials:
            self.send(text_data=json.dumps({"error": "Invalid Credentials"}))
            self.disconnect("403")

        self.api_key = self.credentials.get("api_key")
        if not self.api_key:
            self.send(text_data=json.dumps({"error": "Invalid Credentials"}))
            self.disconnect("403")

        self.zerodha_creds = read_zerodha_credentials()
        if not self.zerodha_creds:
            self.send(text_data=json.dumps({"error": "Invalid Credentials"}))
            self.disconnect("403")

        self.access_token = self.zerodha_creds.get("access_token")
        if not self.access_token:
            self.send(text_data=json.dumps({"error": "Invalid Credentials"}))
            self.disconnect("403")

    async def connect(self):
        try:
            self.symbol = self.scope['url_route']['kwargs']['symbol']
            await self.accept()
            kws = KiteConnect(api_key=self.api_key)
            instruments = kws.instruments(exchange='NSE')
            for i in instruments:
                if i['tradingsymbol'].upper() == self.symbol.upper():
                    self.token = i['instrument_token']
                    break
            # self.token=5633
            # await self.accept()
            await self.channel_layer.group_add(self.symbol, self.channel_name)
            # self.start_kitesocket()
            Thread(target=self.start_kitesocket).start()
            # await self.receive(text_data="message")
        except Exception as e:
            print(e)

    async def disconnect(self, close_code):
        print('here')
        await self.close()
        if self.kws:
            self.kws.close()
        # if self.kws is not None:
        #     self.kws.on_close
        pass

    def receive(self, text_data=None, bytes_data=None):
        try:
            "Handle incoming WebSocket data"
            nest_asyncio.apply()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send(
                    json.dumps({
                        "close": str(text_data[0]['last_price']),
                        "date": str(datetime.datetime.now())
                    }),
                )
            )
        except Exception as e:
            print("error is", e)

    async def live_rate(self, text):
        print("in")
        await self.send(json.dumps({
            "close": str(text[0]['last_price']),
            "date": str(datetime.datetime.now())
        }))

    def start_kitesocket(self):
        print("Starting Kite Socket ...")
        global tokens
        self.kws = KiteTicker(api_key=self.api_key, access_token=self.access_token)
        tokens = [self.token]
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error

        self.kws.connect(threaded=True)
        count = 0
        while True:
            count += 1
            if count % 2 == 0:
                if self.kws.is_connected():
                    self.kws.set_mode(self.kws.MODE_FULL, tokens)
                else:
                    if self.kws.is_connected():
                        self.kws.set_mode(self.kws.MODE_FULL, tokens)
                time.sleep(1)

    # def send_message_ws(self,message):
    #     self.receive(message)

    def on_ticks(self, ws, ticks):
        # Callback to receive ticks.
        try:
            print("tick")
            self.receive(ticks)
        except Exception as e:
            print(e)

    def on_connect(self, ws, response):
        global tokens
        ws.subscribe(tokens)

        ws.set_mode(ws.MODE_FULL, tokens)

    def on_close(self, ws):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        print("called onclose")
        ws.stop()
        self.kws.stop()

    def on_error(self, ws, code, reason):
        print('inside the error block')
        print(reason)
        ws.stop()
        self.close()


class ConsumerV3(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(ConsumerV3, self).__init__(*args, **kwargs)
        self.ticker = Singleton2.get_instance("consumer_v3")
        self.symbol = None
        self.token = None
        self.stop = None

    async def connect(self):
        print("connected")
        await self.accept()
        self.channel_layer.group_add(self.symbol, self.channel_name)
        Thread(target=self.live_rates).start()
        # await self.send(json.dumps({"message": "connected"}))

    def receive(self, text_data=None, bytes_data=None):
        # Send the message from main thread from background thread.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.send(
                text_data=text_data,
            )
        )
        # await self.send(text_data)

    async def message(self, message=None):
        try:
            # nest_asyncio.apply()
            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # result = loop.run_until_complete(
            #     self.send(
            #         json.dumps(text_data),
            #     )
            # )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.send(
                    text_data=message,
                )
            )
            # await self.receive(
            #     text_data=message,
            # )
        except Exception as e:
            print("error is", e)

    def live_rates(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        self.token = self.ticker.stock_map_2.get(self.symbol)
        i = 0
        while True:
            # self.send(text_data=json.dumps(self.ticker.stock_map))
            # await self.send(text_data=json.dumps({'mgs': 1}))

            df = pd.DataFrame(self.ticker.tick_data)
            # if i % 5 == 0:
            #     print(df)
            if not df.empty:
                df = df[df['instrument_token'] == self.token]
                if not df.empty:
                    t = df.to_dict("records")
                    self.receive(json.dumps({
                        "symbol": self.symbol,
                        "token": self.token,
                        "price": t[0]['last_price'],
                        "timestamp": int(datetime.datetime.timestamp(datetime.datetime.now())*1000),
                        # Returns if market is opened now
                        "is_market_open_now": is_market_open_now(),
                    }))
            i += 1
            time.sleep(1)
            if self.stop:
                break
        # self.receive(text_data=json.dumps({"meg": 2}))

    async def disconnect(self, code):
        self.stop = True
        print("disconnect ", code)

    async def close(self, code=None):
        self.stop = True
        print("closed", code)


class LatestPortfolioValueConsumer(WebsocketConsumer):

    last = None
    user = None
    connected_on = None
    break_connection = False
    thread = None

    def receive(self, text_data=None, bytes_data=None):
        last = json.loads(text_data).get("last")
        if last:
            self.last = make_aware(
                datetime.datetime.combine(
                    datetime.datetime.now().date(),
                    datetime.datetime.strptime(last, "%H:%M:%S").time()
                )
            )

    def initialize_connection(self):
        while True:
            if self.break_connection:
                break

            market_open_now = is_market_open_now()
            # print("self.last", self.last)
            if self.last:
                values = PortfolioValues.objects.filter(
                    # return only deletable values in the web socket
                    user=self.user, deletable=True, timestamp__gt=self.last,
                    # Data sampled during business hours is only returned via websockets
                    # timestamp__hour__lte=BUSINESS_HOURS_END.hour, timestamp__minute__lte=BUSINESS_HOURS_END.minute
                ).order_by("timestamp")
                if values.exists():
                    self.last = values.last().timestamp

                    portfolio_value = values.last().portfolio_value
                    portfolio_value_2 = values.last().realized_gain_loss + values.last().unrealized_gain_loss
                    values = values.values("timestamp", "portfolio_value", "realized_gain_loss", "unrealized_gain_loss")
                    df = pd.DataFrame(values)
                    df['gl'] = df['realized_gain_loss'] + df['unrealized_gain_loss']
                    df['timestamp'] = df['timestamp'].apply(lambda x: int(x.timestamp() * 1000))
                    df = df[['timestamp', 'portfolio_value', 'gl']]

                    result = {
                        "count": len(df),
                        "gl_value": portfolio_value_2,
                        "portfolio_value": portfolio_value,
                        "data_points": df.values.tolist(),
                        "is_market_open_now": market_open_now
                    }
                    self.send(json.dumps(result))
                else:
                    self.send(json.dumps({
                        "count": 0,
                        "is_market_open_now": market_open_now
                    }))
            else:
                self.send(json.dumps({
                    "count": 0,
                    "is_market_open_now": market_open_now
                }))
                # if an idle connection has been made for more than 2 minutes, close the websocket connection
                # if (now - self.connected_on).total_seconds() >= 2 * 60:
                #     print("closing the idle connection")
                #     self.break_connection = True
                #     break

            time.sleep(15)

        # if a loop is exited, break the connection
        # if self.break_connection:
        #     self.close()

    def disconnect(self, code):
        self.break_connection = True
        super(LatestPortfolioValueConsumer, self).disconnect(code)

    def close(self, code=None):
        self.break_connection = True
        super(LatestPortfolioValueConsumer, self).close()

    def connect(self):
        self.user = self.scope.get("user")
        self.connected_on = datetime.datetime.now()
        if self.user.is_authenticated:
            self.accept()
            self.thread = Thread(target=self.initialize_connection)
            self.thread.start()
        else:
            self.close()
