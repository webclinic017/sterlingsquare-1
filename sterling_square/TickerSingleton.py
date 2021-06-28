import json
import datetime
import time
import asyncio
import logging
import nest_asyncio
import pandas as pd
from threading import Thread
from django.conf import settings
import websocket
import struct

from kiteconnect import KiteConnect

from accounts.models import *
from utils.util_functions import read_zerodha_credentials, read_zerodha_credentials_threaded
from django.utils.timezone import make_aware
from utils.date_utils import *
from utils.util_functions import get_last_price_from_file
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# Tuning Knob to tune Refresh Zerodha Credentials inside the Singleton Classes
CREDS_REFRESH_TIMEOUT_SECONDS = 10 * 60     # 10 minutes.

# def save_portfolio_values(ticker_data):
#     s = SingletonPortfolio.get_instance("")
#     s.parse_tick_data("SYMBOL", ticker_data)
#
#     try:
#         users = User.objects.all()
#         is_market_opened = is_market_opened_date()
#         # if there is no weekend or a holiday, save the data as usual
#         # else, do not save the data, this will save us some space on the db.
#         if is_market_opened:
#             for user in users:
#                 positions = Position.objects.filter(userid=user)
#                 aggregate = {}
#
#                 for position in positions:
#                     if position.ticker in aggregate:
#                         aggregate[position.ticker]['size'] += position.size
#                         aggregate[position.ticker]['unrealised_gl'] += \
#                             float(position.gl_history_position_rel.all()[0].unrealised_gainloss)
#                         aggregate[position.ticker]['realised_gl'] += \
#                             float(position.gl_history_position_rel.all()[0].realised_gainloss)
#                     else:
#                         aggregate[position.ticker] = {
#                             "size": position.size,
#                             "unrealised_gl": float(position.gl_history_position_rel.all()[0].unrealised_gainloss),
#                             "realised_gl": float(position.gl_history_position_rel.all()[0].realised_gainloss),
#                         }
#
#                 buying_power = float(user.user_details.identity.buyingpower)
#                 amt, unrealised_gl, realised_gl = 0, 0, 0
#                 # DB entries will be made only for users who have at least 1 ticker in the portfolio
#                 for ticker in aggregate:
#                     live_price, _ = s.parse_tick_data(ticker, ticker_data)
#                     amt += live_price * aggregate[ticker]['size']
#                     unrealised_gl += aggregate[ticker]['unrealised_gl']
#                     realised_gl += aggregate[ticker]['realised_gl']
#
#                 portfolio_value = amt + unrealised_gl + realised_gl + buying_power
#
#                 now = datetime.datetime.now()
#                 # data will be stored after every 5 second between 9:00AM till 5:00PM
#                 if now.hour in range(9, 17):
#                     PortfolioValues.objects.create(
#                         user=user,
#                         timestamp=now,
#                         portfolio_value=portfolio_value,
#                         cash_balance=0,
#                         realized_gain_loss=realised_gl,
#                         unrealized_gain_loss=unrealised_gl,
#                         amount=amt,
#                         deletable=True
#                     )
#
#                 # Save one more record at 9:00PM. This cannot be deleted and will be used for historical data
#                 if now.hour == 21 and now.minute == 0 and now.second == 0:
#                     PortfolioValues.objects.create(
#                         user=user,
#                         timestamp=now,
#                         portfolio_value=portfolio_value,
#                         cash_balance=0,
#                         realized_gain_loss=realised_gl,
#                         unrealized_gain_loss=unrealised_gl,
#                         amount=amt,
#                         deletable=False
#                     )
#     except Exception as e:
#         pass


def save_rt_price(token, symbol, price, timestamp):
    """
    Threaded function to write the realtime price to db.
    """
    # print("thread_rt_price")
    rt_price = StockPrices(
        time_stamp=make_aware(timestamp), price=price, token=token, symbol=symbol
    )
    rt_price.save()
    # print("saved ... ")


def save_rt_price_2(token, symbol, price, timestamp):
    """
    Threaded function to write the realtime price to a CSV.
    """
    # print(f"SAVING DATA TO FILE FOR SYMBOL : {symbol}, {token}")
    root = settings.MEDIA_ROOT
    file_name = "{symbol}_{date}.csv".format(symbol=symbol, date=timestamp.strftime("%Y-%m-%d"))
    dir = os.path.join(root, "symbol_data", symbol)

    if not os.path.exists(os.path.join(root, "symbol_data")):
        os.mkdir(os.path.join(root, "symbol_data"))
    if not os.path.exists(dir):
        os.mkdir(dir)

    path = os.path.join(dir, file_name)
    if not os.path.isfile(path):
        with open(path, "a") as f:
            f.write("timestamp,symbol,token,price\n")
            f.write(f"{timestamp},{symbol},{token},{price}\n")
    else:
        with open(path, "a") as f:
            f.write(f"{timestamp},{symbol},{token},{price}\n")


def get_stock_names(result):
    try:
        result['stocks'] = pd.DataFrame(list(StockNames.objects.all().order_by("id").values("symbol")))
    except Exception as e:
        print("EXction ", e)
        result['stocks'] = pd.DataFrame([])


def _unpack_int(bin, start, end, byte_format="I"):
    """Unpack binary data as unsgined interger."""
    return struct.unpack(">" + byte_format, bin[start:end])[0]


def _split_packets(bin):
    """Split the data to individual packets of ticks."""
    # Ignore heartbeat data.
    if len(bin) < 2:
        return []

    number_of_packets = _unpack_int(bin, 0, 2, byte_format="H")
    packets = []

    j = 2
    for i in range(number_of_packets):
        packet_length = _unpack_int(bin, j, j + 2, byte_format="H")
        packets.append(bin[j + 2: j + 2 + packet_length])
        j = j + 2 + packet_length

    return packets


def _parse_binary(bin):
    MODE_FULL = "full"
    MODE_QUOTE = "quote"
    MODE_LTP = "ltp"
    EXCHANGE_MAP = {
        "nse": 1,
        "nfo": 2,
        "cds": 3,
        "bse": 4,
        "bfo": 5,
        "bsecds": 6,
        "mcx": 7,
        "mcxsx": 8,
        "indices": 9
    }
    """Parse binary data to a (list of) ticks structure."""
    packets = _split_packets(bin)  # split data to individual ticks packet
    data = []

    for packet in packets:
        instrument_token = _unpack_int(packet, 0, 4)
        segment = instrument_token & 0xff  # Retrive segment constant from instrument_token

        divisor = 10000000.0 if segment == EXCHANGE_MAP["cds"] else 100.0

        # All indices are not tradable
        tradable = False if segment == EXCHANGE_MAP["indices"] else True

        # LTP packets
        if len(packet) == 8:
            data.append({
                "tradable": tradable,
                "mode": MODE_LTP,
                "instrument_token": instrument_token,
                "last_price": _unpack_int(packet, 4, 8) / divisor
            })
        # Indices quote and full mode
        elif len(packet) == 28 or len(packet) == 32:
            mode = MODE_QUOTE if len(packet) == 28 else MODE_FULL

            d = {
                "tradable": tradable,
                "mode": mode,
                "instrument_token": instrument_token,
                "last_price": _unpack_int(packet, 4, 8) / divisor,
                "ohlc": {
                    "high": _unpack_int(packet, 8, 12) / divisor,
                    "low": _unpack_int(packet, 12, 16) / divisor,
                    "open": _unpack_int(packet, 16, 20) / divisor,
                    "close": _unpack_int(packet, 20, 24) / divisor
                }
            }

            # Compute the change price using close price and last price
            d["change"] = 0
            if(d["ohlc"]["close"] != 0):
                d["change"] = (d["last_price"] - d["ohlc"]["close"]) * 100 / d["ohlc"]["close"]

            # Full mode with timestamp
            if len(packet) == 32:
                try:
                    timestamp = datetime.fromtimestamp(_unpack_int(packet, 28, 32))
                except Exception:
                    timestamp = None

                d["timestamp"] = timestamp

            data.append(d)
        # Quote and full mode
        elif len(packet) == 44 or len(packet) == 184:
            mode = MODE_QUOTE if len(packet) == 44 else MODE_FULL

            d = {
                "tradable": tradable,
                "mode": mode,
                "instrument_token": instrument_token,
                "last_price": _unpack_int(packet, 4, 8) / divisor,
                "last_quantity": _unpack_int(packet, 8, 12),
                "average_price": _unpack_int(packet, 12, 16) / divisor,
                "volume": _unpack_int(packet, 16, 20),
                "buy_quantity": _unpack_int(packet, 20, 24),
                "sell_quantity": _unpack_int(packet, 24, 28),
                "ohlc": {
                    "open": _unpack_int(packet, 28, 32) / divisor,
                    "high": _unpack_int(packet, 32, 36) / divisor,
                    "low": _unpack_int(packet, 36, 40) / divisor,
                    "close": _unpack_int(packet, 40, 44) / divisor
                }
            }

            # Compute the change price using close price and last price
            d["change"] = 0
            if(d["ohlc"]["close"] != 0):
                d["change"] = (d["last_price"] - d["ohlc"]["close"]) * 100 / d["ohlc"]["close"]

            # Parse full mode
            if len(packet) == 184:
                try:
                    last_trade_time = datetime.fromtimestamp(_unpack_int(packet, 44, 48))
                except Exception:
                    last_trade_time = None

                try:
                    timestamp = datetime.fromtimestamp(_unpack_int(packet, 60, 64))
                except Exception:
                    timestamp = None

                d["last_trade_time"] = last_trade_time
                d["oi"] = _unpack_int(packet, 48, 52)
                d["oi_day_high"] = _unpack_int(packet, 52, 56)
                d["oi_day_low"] = _unpack_int(packet, 56, 60)
                d["timestamp"] = timestamp

                # Market depth entries.
                depth = {
                    "buy": [],
                    "sell": []
                }

                # Compile the market depth lists.
                for i, p in enumerate(range(64, len(packet), 12)):
                    depth["sell" if i >= 5 else "buy"].append({
                        "quantity": _unpack_int(packet, p, p + 4),
                        "price": _unpack_int(packet, p + 4, p + 8) / divisor,
                        "orders": _unpack_int(packet, p + 8, p + 10, byte_format="H")
                    })

                d["depth"] = depth

            data.append(d)

    return data


# This version does not use KiteTicker class. Much more flexible as compared to KiteTicker class on error
# Stores the Tick Data temporarily and Writes the Information to the Database as well
class Singleton2:
    __instance = None

    REFRESH_TIMEOUT_SECONDS = CREDS_REFRESH_TIMEOUT_SECONDS
    # REFRESH_TIMEOUT_SECONDS = 3 * 3600  # equals to 3 hours
    # REFRESH_TIMEOUT_SECONDS = 10      # equals to 10 seconds

    @staticmethod
    def get_instance(key):
        """ Static access method. """
        if Singleton2.__instance is None:
            Singleton2()
        return Singleton2.__instance

    def __init__(self):
        """ Virtually private constructor. """
        print("Initializing Singleton2 ... ")

        self.initialized = None

        self.symbol = None
        self.stock_map_2 = {}
        self.tick_data = None

        self.token = []

        self.credentials = None
        self.api_key = None
        self.zerodha_creds = None
        self.access_token = None

        result = {}
        t = Thread(target=get_stock_names, args=(result,), daemon=True)
        t.start()
        t.join()
        stocks = result['stocks']
        if stocks.empty:
            raise Exception("Empty Stock List ...")

        self.stocks = stocks['symbol'].values.tolist()
        self.stock_map = {}
        self.last_time_stamp = None

        self.kite = None
        self.ticker = None
        # self.stop_loop = False
        self.error = False

        t2 = Thread(
            target=is_market_opened_date_threaded,
            args=(datetime.datetime.now(), result,), daemon=True
        )
        t2.start()
        t2.join()
        self.market_opened = result['is_market_opened']

        if Singleton2.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Singleton2.__instance = self
            self.read_credentials()
            self.get_all_symbols()
            self.initialized = datetime.datetime.now()
            self.init_ticker()
            print("Initialized Singleton2 ...")

    def parse_tick_data(self, symbol):
        try:
            df = pd.DataFrame(self.tick_data)
            if not df.empty:
                token = self.stock_map_2.get(symbol, None)
                if not token:
                    return None, None
                df = df[df['instrument_token'] == int(token)]
                if not df.empty:
                    t = df.to_dict("records")
                    return t[0]['last_price'], datetime.datetime.now()
                return get_last_price_from_file(symbol), None
            return get_last_price_from_file(symbol), None
        except Exception as e:
            print("parse tick data exception ", e)
            return get_last_price_from_file(symbol), None

    def refresh_credentials(self):
        self.initialized = datetime.datetime.now()
        self.read_credentials()
        print("Read the creds ... ")
        # self.get_all_symbols()
        self.init_ticker()
        print("initialized the ticker ... ")

    def read_credentials(self):
        self.credentials = getattr(settings, "ZERODHA_CREDENTIALS")
        if not self.credentials:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.api_key = self.credentials.get("api_key")
        if not self.api_key:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        r = {}
        t = Thread(
            target=read_zerodha_credentials_threaded, args=(r, False), daemon=True
        )
        t.start()
        t.join()
        print(r['zerodha'])
        self.zerodha_creds = r['zerodha']
        if not self.zerodha_creds:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.access_token = self.zerodha_creds.get("access_token")
        if not self.access_token:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

    def init_ticker(self):
        if not self.initialized:
            self.initialized = datetime.datetime.now()
        # global tokens
        try:
            def on_message(ws, message):
                ws.send(json.dumps({"a": "subscribe", "v": self.token}))
                if self.initialized is None:
                    self.initialized = datetime.datetime.now()

                try:
                    self.receive(_parse_binary(message))

                    now = datetime.datetime.now()
                    hour, minute, second = now.hour, now.minute, now.second

                    # specifically run the refresh command at 08:58:00AM to 08:58:03AM
                    refresh = hour == 8 and minute == 58 and second in range(0, 3)
                    refresh = (now - self.initialized).total_seconds() >= self.REFRESH_TIMEOUT_SECONDS or refresh

                    if refresh:
                        print("Refreshing the ticker object .. ")
                        self.read_credentials()
                        # close the connection safely.
                        ws.close()
                        # Refresh the datetime again
                        self.initialized = None
                        self.init_ticker()

                except Exception as e:
                    print(e)

            def on_error(ws):
                self.error = True
                ws.close()
                print("On Error: (closed) ", self)

            def on_open(ws):
                ws.send(json.dumps({"a": "subscribe", "v": self.token}))
                print("ticker ... connected .... ")

            self.ticker = websocket.WebSocketApp(
                "wss://ws.kite.trade?api_key={}&access_token={}".format(
                    self.api_key, self.access_token
                ),
                on_message=on_message,
                on_error=on_error,
                on_open=on_open
            )
            print("starting ticker ... ")
            Thread(target=self.ticker.run_forever, daemon=True).start()
        except Exception as e:
            print('EXCEPTION .. init ticker ... singleton 2 ', e)

    def receive(self, text_data=None):
        now = datetime.datetime.now()
        # True depicts that the market is opened today.
        res = {}
        # When hour is in range 8AM to 7PM and minute is zero and second in range 0, 6
        if is_weekday() and now.hour in range(8, 19) and now.minute == 0 and now.second in range(0, 6):
            t2 = Thread(
                target=is_market_opened_date_threaded,
                args=(now, res,), daemon=True
            )
            t2.start()
            t2.join()
            self.market_opened = res['is_market_opened']

        # print("receive market_opened today :: ", self.market_opened, is_weekday())

        try:
            # Send this data on the weekends as well because frontend requires it to calculate return values.
            if text_data:
                self.tick_data = text_data
            # Writing the data to the DB every approximately 4.3 seconds (delay ranges from 4.3 to 5.5 seconds)

            # if self.last_time_stamp is None or (now - self.last_time_stamp).total_seconds() >= 4.3:
            # if now.second % 5 == 0:
            #     for tick in text_data:
            #         symbol = self.stock_map.get(tick['instrument_token'])
            #         last_price = tick['last_price']
            #         self.last_time_stamp = now
            #         # Writing the values to the database in the background thread without holding the main thread
            #         if self.market_opened:
            #             # Do not save data on the Weekends and Holidays
            #             t = Thread(
            #                 target=save_rt_price,
            #                 args=(tick['instrument_token'], symbol, last_price, now),
            #                 daemon=True
            #             )
            #             t.start()

        except Exception as e:
            print("error is", e)

    def get_all_symbols(self, exchange="NSE"):
        try:
            instruments = []
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                instruments = self.kite.instruments(exchange=exchange)
            except Exception as e:
                # Retry fetching he
                print("Retrying getting symbols ... ", e)
                self.get_all_symbols(exchange)

            for i in instruments:
                if i['tradingsymbol'].upper() in self.stocks:
                    if i['instrument_token'] not in self.token:
                        self.token.append(i['instrument_token'])
                    self.stock_map[i['instrument_token']] = i['tradingsymbol'].upper()
                    self.stock_map_2[i['tradingsymbol'].upper()] = i['instrument_token']
        except Exception as ex:
            print("exception ... ", ex)

        # try:
        #     self.kite = KiteConnect(api_key=self.api_key)
        #     instruments = self.kite.instruments(exchange=exchange)
        #     for i in instruments:
        #         if i['tradingsymbol'].upper() in self.stocks:
        #             if i['instrument_token'] not in self.token:
        #                 self.token.append(i['instrument_token'])
        #             self.stock_map[i['instrument_token']] = i['tradingsymbol'].upper()
        #             self.stock_map_2[i['tradingsymbol'].upper()] = i['instrument_token']
        # except Exception as e:
        #     print("exception ", e)


# This version does not use KiteTicker class. Much more flexible as compared to KiteTicker class on error
# Stores the Tick Data temporarily and DOESN'T Write the Information to the Database as well
class SingletonCelery:
    __instance = None

    REFRESH_TIMEOUT_SECONDS = CREDS_REFRESH_TIMEOUT_SECONDS
    # REFRESH_TIMEOUT_SECONDS = 3 * 3600  # equals to 3 hours
    # REFRESH_TIMEOUT_SECONDS = 10  # equals to 10 seconds

    @staticmethod
    def get_instance(key):
        """ Static access method. """
        if SingletonCelery.__instance is None:
            SingletonCelery()
        return SingletonCelery.__instance

    def __init__(self):
        """ Virtually private constructor. """
        print("Initialized Singleton Celery ... ")

        self.thread = None
        self.initialized = None

        self.symbol = None
        self.stock_map_2 = {}
        self.tick_data = None

        self.token = []

        self.credentials = None
        self.api_key = None
        self.zerodha_creds = None
        self.access_token = None

        result = {}
        t = Thread(target=get_stock_names, args=(result,), daemon=True)
        t.start()
        t.join()
        stocks = result['stocks']
        if stocks.empty:
            raise Exception("Empty Stock List ...")

        self.stocks = stocks['symbol'].values.tolist()
        self.stock_map = {}
        self.last_time_stamp = None

        self.kite = None
        self.ticker = None
        # self.stop_loop = False
        self.error = False

        t2 = Thread(
            target=is_market_opened_date_threaded,
            args=(datetime.datetime.now(), result,), daemon=True
        )
        t2.start()
        t2.join()
        self.market_opened = result['is_market_opened']

        if SingletonCelery.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            SingletonCelery.__instance = self
            self.read_credentials()
            self.get_all_symbols()
            self.initialized = datetime.datetime.now()
            self.init_ticker()

    def parse_tick_data(self, symbol, tick_data=None):
        if not tick_data:
            tick_data = self.tick_data
        try:
            df = pd.DataFrame(tick_data)
            if not df.empty:
                token = self.stock_map_2.get(symbol, None)
                if not token:
                    return None, None
                df = df[df['instrument_token'] == int(token)]
                if not df.empty:
                    t = df.to_dict("records")
                    return t[0]['last_price'], datetime.datetime.now()
                return get_last_price_from_file(symbol), None
            return get_last_price_from_file(symbol), None
        except Exception as e:
            print("parse tick data exception ", e)
            return get_last_price_from_file(symbol), None

    def refresh_credentials(self):
        self.initialized = datetime.datetime.now()
        self.read_credentials()
        print("Read the creds ... ")
        # self.get_all_symbols()
        self.init_ticker()
        print("initialized the ticker ... ")

    def read_credentials(self):
        self.credentials = getattr(settings, "ZERODHA_CREDENTIALS")
        if not self.credentials:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.api_key = self.credentials.get("api_key")
        if not self.api_key:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.zerodha_creds = read_zerodha_credentials()
        if not self.zerodha_creds:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.access_token = self.zerodha_creds.get("access_token")
        if not self.access_token:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

    def init_ticker(self):
        if not self.initialized:
            self.initialized = datetime.datetime.now()
        # global tokens
        try:
            def on_message(ws, message):
                ws.send(json.dumps({"a": "subscribe", "v": self.token}))
                if self.initialized is None:
                    self.initialized = datetime.datetime.now()

                try:
                    self.receive(_parse_binary(message))
                    # time.sleep(0.001)

                    if (datetime.datetime.now() - self.initialized).total_seconds() >= self.REFRESH_TIMEOUT_SECONDS:
                        print("Refreshing the ticker object .. ")
                        self.read_credentials()
                        # close the connection safely.
                        ws.close()
                        # Refresh the datetime again
                        self.initialized = None
                        self.init_ticker()

                except Exception as e:
                    print(e)

            def on_error(ws):
                self.error = True
                ws.close()
                print("On Error: (closed) ", self)

            def on_open(ws):
                ws.send(json.dumps({"a": "subscribe", "v": self.token}))

            self.ticker = websocket.WebSocketApp(
                "wss://ws.kite.trade?api_key={}&access_token={}".format(
                    self.api_key, self.access_token
                ),
                on_message=on_message,
                on_error=on_error,
                on_open=on_open
            )
            self.thread = Thread(target=self.ticker.run_forever, daemon=True)
            self.thread.start()
        except Exception as e:
            pass

    def receive(self, text_data=None):
        now = datetime.datetime.now()
        # True depicts that the market is opened today.
        res = {}
        # When hour is in range 8AM to 7PM and minute is zero and second in range 0, 6
        if is_weekday() and now.hour in range(8, 19) and now.minute == 0 and now.second in range(0, 6):
            t2 = Thread(
                target=is_market_opened_date_threaded,
                args=(now, res,), daemon=True
            )
            t2.start()
            t2.join()
            self.market_opened = res['is_market_opened']

        try:
            # Send this data on the weekends as well because frontend requires it to calculate return values.
            if text_data:
                self.tick_data = text_data
            else:
                print(".... celery didn't receive tick data")

        except Exception as e:
            print("error is", e)

    def get_all_symbols(self, exchange="NSE"):
        try:
            instruments = []
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                instruments = self.kite.instruments(exchange=exchange)
            except Exception as e:
                # Retry fetching he
                self.get_all_symbols(exchange)

            for i in instruments:
                if i['tradingsymbol'].upper() in self.stocks:
                    if i['instrument_token'] not in self.token:
                        self.token.append(i['instrument_token'])
                    self.stock_map[i['instrument_token']] = i['tradingsymbol'].upper()
                    self.stock_map_2[i['tradingsymbol'].upper()] = i['instrument_token']
        except Exception as ex:
            print("exception ... ", ex)

    def close(self):
        # Close the WS connection
        self.ticker.close()
        # if the thread is alive, kill it.
        while self.thread and self.thread.isAlive():
            time.sleep(0.5)
        SingletonCelery.__instance = None
        print("closed.")


# This Singleton class is a wrapper on the SingletonCelery class.
# This class basically writes the portfolio data in the database.
class SingletonPortfolio:
    __instance = None

    REFRESH_TIMEOUT_SECONDS = CREDS_REFRESH_TIMEOUT_SECONDS
    # REFRESH_TIMEOUT_SECONDS = 3 * 3600  # equals to 3 hours

    # REFRESH_TIMEOUT_SECONDS = 10  # equals to 10 seconds

    @staticmethod
    def build(key):
        """ Static access method. """
        if SingletonPortfolio.__instance is None:
            SingletonPortfolio()
        return SingletonPortfolio.__instance

    @staticmethod
    def get_instance():
        return SingletonPortfolio.__instance

    def __init__(self):
        """ Virtually private constructor. """
        print("Initialized Singleton Portfolio ... ")
        self.closed = False
        self.running = False
        self.thread = False
        self.initialized = None

        self.symbol = None
        self.stock_map_2 = {}
        self.tick_data = None

        self.token = []

        self.credentials = None
        self.api_key = None
        self.zerodha_creds = None
        self.access_token = None

        result = {}
        t = Thread(target=get_stock_names, args=(result,), daemon=True)
        t.start()
        t.join()
        stocks = result['stocks']
        if stocks.empty:
            raise Exception("Empty Stock List ...")

        self.stocks = stocks['symbol'].values.tolist()
        self.stock_map = {}
        self.last_time_stamp = None

        self.kite = None
        self.ticker = None
        # self.stop_loop = False
        self.error = False

        t2 = Thread(
            target=is_market_opened_date_threaded,
            args=(datetime.datetime.now(), result,), daemon=True
        )
        t2.start()
        t2.join()
        self.market_opened = result['is_market_opened']

        if SingletonPortfolio.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            SingletonPortfolio.__instance = self
            # self.read_credentials()
            # self.get_all_symbols()
            self.initialized = datetime.datetime.now()
            self.thread = Thread(target=self.init_ticker, daemon=True)
            self.thread.start()

    def parse_tick_data(self, symbol, tick_data=None):
        if not tick_data:
            tick_data = self.tick_data
        try:
            df = pd.DataFrame(tick_data)
            if not df.empty:
                token = self.stock_map_2.get(symbol, None)
                if not token:
                    return None, None
                df = df[df['instrument_token'] == int(token)]
                if not df.empty:
                    t = df.to_dict("records")
                    return t[0]['last_price'], datetime.datetime.now()
                return get_last_price_from_file(symbol), None
            return get_last_price_from_file(symbol), None
        except Exception as e:
            print("parse tick data exception ", e)
            return get_last_price_from_file(symbol), None

    def refresh_credentials(self):
        self.initialized = datetime.datetime.now()
        self.thread = Thread(target=self.init_ticker, daemon=True)
        self.thread.start()

    def read_credentials(self):
        self.credentials = getattr(settings, "ZERODHA_CREDENTIALS")
        if not self.credentials:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.api_key = self.credentials.get("api_key")
        if not self.api_key:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.zerodha_creds = read_zerodha_credentials()
        if not self.zerodha_creds:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.access_token = self.zerodha_creds.get("access_token")
        if not self.access_token:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

    def init_ticker(self):
        if not self.initialized:
            self.initialized = datetime.datetime.now()

        singleton = SingletonCelery.get_instance("")
        started = datetime.datetime.now()
        logger.info("Portfolio Ticker Initialising ... ")
        while True:
            users_processed = 0
            self.running = True
            if self.closed:
                break
            print("Ticker Running .... ")
            # check if the market is opened
            # if the market is opened, read the data
            now = datetime.datetime.now()
            flag = 0

            r = {}
            t = Thread(
                target=is_market_opened_date_threaded, args=(None, r), daemon=True
            )
            t.start()
            t.join()

            if r['is_market_opened'] and now.hour in range(9, 18) and now.second % 5 == 0:
                flag = 1

            if r['is_market_opened'] and \
                    datetime.time(hour=21, minute=0, second=0) <= now.time() <= \
                    datetime.time(hour=21, minute=0, second=10):
                flag = 2

            logger.info("Flag ... {}".format(flag))

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
            logger.info("Flag: {} Users Processed in this iteration: {}".format(flag, users_processed))
            time.sleep(1)
        end = (datetime.datetime.now() - started).total_seconds()
        logger.info("Loop ended after {} seconds".format(end))

    def close(self):
        self.closed = True
        SingletonPortfolio.__instance = None
        while self.thread and self.thread.isAlive():
            time.sleep(0.5)
        print("Singleton Portfolio thread killed ... ")


class SingletonStockPrices:
    __instance = None

    REFRESH_TIMEOUT_SECONDS = CREDS_REFRESH_TIMEOUT_SECONDS
    # REFRESH_TIMEOUT_SECONDS = 3 * 3600  # equals to 3 hours

    # REFRESH_TIMEOUT_SECONDS = 10  # equals to 10 seconds

    @staticmethod
    def get_instance(key):
        """ Static access method. """
        if SingletonStockPrices.__instance is None:
            SingletonStockPrices()
        return SingletonStockPrices.__instance

    def __init__(self):
        """ Virtually private constructor. """
        print("Initialized Singleton Stock Prices ... ")

        self.thread = None
        self.initialized = None

        self.symbol = None
        self.stock_map_2 = {}
        self.tick_data = None

        self.token = []

        self.credentials = None
        self.api_key = None
        self.zerodha_creds = None
        self.access_token = None

        result = {}
        t = Thread(target=get_stock_names, args=(result,), daemon=True)
        t.start()
        t.join()
        stocks = result['stocks']
        if stocks.empty:
            raise Exception("Empty Stock List ...")

        self.stocks = stocks['symbol'].values.tolist()
        self.stock_map = {}
        self.last_time_stamp = None

        self.kite = None
        self.ticker = None
        # self.stop_loop = False
        self.error = False

        t2 = Thread(
            target=is_market_opened_date_threaded,
            args=(datetime.datetime.now(), result,), daemon=True
        )
        t2.start()
        t2.join()
        self.market_opened = result['is_market_opened']

        if SingletonStockPrices.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            SingletonStockPrices.__instance = self
            self.read_credentials()
            self.get_all_symbols()
            self.initialized = datetime.datetime.now()
            self.thread = Thread(
                target=self.init_ticker, daemon=True
            )
            self.thread.start()

    def parse_tick_data(self, symbol, tick_data=None):
        if not tick_data:
            tick_data = self.tick_data
        try:
            df = pd.DataFrame(tick_data)
            if not df.empty:
                token = self.stock_map_2.get(symbol, None)
                if not token:
                    return None, None
                df = df[df['instrument_token'] == int(token)]
                if not df.empty:
                    t = df.to_dict("records")
                    return t[0]['last_price'], datetime.datetime.now()
                return get_last_price_from_file(symbol), None
            return get_last_price_from_file(symbol), None
        except Exception as e:
            print("parse tick data exception ", e)
            return get_last_price_from_file(symbol), None

    def refresh_credentials(self):
        self.initialized = datetime.datetime.now()
        self.read_credentials()
        print("Read the creds ... ")
        # self.get_all_symbols()
        # self.init_ticker()
        self.thread = Thread(
            target=self.init_ticker, daemon=True
        )
        self.thread.start()
        print("initialized the ticker ... ")

    def read_credentials(self):
        self.credentials = getattr(settings, "ZERODHA_CREDENTIALS")
        if not self.credentials:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.api_key = self.credentials.get("api_key")
        if not self.api_key:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.zerodha_creds = read_zerodha_credentials()
        if not self.zerodha_creds:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

        self.access_token = self.zerodha_creds.get("access_token")
        if not self.access_token:
            raise Exception(json.dumps({"error": "Invalid Credentials"}))

    def init_ticker(self):
        if not self.initialized:
            self.initialized = datetime.datetime.now()
        while True:
            singleton = SingletonCelery.get_instance("")
            now = datetime.datetime.now()
            if now.second % 5 == 0:
                tick_data = singleton.tick_data
                if tick_data:
                    for tick in tick_data:
                        symbol = self.stock_map.get(tick['instrument_token'])
                        last_price = tick['last_price']
                        self.last_time_stamp = now
                        # Writing the values to the database in the background thread without holding the main thread
                        if self.market_opened and 9 <= now.hour <= 17:
                            # Do not save data on the Weekends and Holidays
                            # t = Thread(
                            #     target=save_rt_price,
                            #     args=(tick['instrument_token'], symbol, last_price, now),
                            #     daemon=True
                            # )
                            # t.start()
                            save_rt_price_2(tick['instrument_token'], symbol, last_price, now)
            time.sleep(1)

    def get_all_symbols(self, exchange="NSE"):
        try:
            instruments = []
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                instruments = self.kite.instruments(exchange=exchange)
            except Exception as e:
                # Retry fetching he
                self.get_all_symbols(exchange)

            for i in instruments:
                if i['tradingsymbol'].upper() in self.stocks:
                    if i['instrument_token'] not in self.token:
                        self.token.append(i['instrument_token'])
                    self.stock_map[i['instrument_token']] = i['tradingsymbol'].upper()
                    self.stock_map_2[i['tradingsymbol'].upper()] = i['instrument_token']
        except Exception as ex:
            print("exception ... ", ex)

    def close(self):
        # Close the WS connection
        self.ticker.close()
        # if the thread is alive, kill it.
        while self.thread and self.thread.isAlive():
            time.sleep(0.5)
        SingletonStockPrices.__instance = None
        print("closed.")


# A test class.
class SingletonTest:
    """
    Singleton Close Demo
    """

    __instance = None

    @staticmethod
    def get_instance():
        if SingletonTest.__instance is None:
            SingletonTest()
        return SingletonTest.__instance

    @staticmethod
    def get_ins():
        return SingletonTest.__instance

    def __init__(self):
        self.close_instance = False
        self.thread = None
        self.closed = False

        if SingletonTest.__instance is not None:
            raise Exception("SingleTest is a Singleton class")
        else:
            SingletonTest.__instance = self
            self.thread = Thread(target=self.init_ticker, daemon=True)
            self.thread.start()

    def init_ticker(self):
        while True:
            if self.close_instance:
                break
            now = datetime.datetime.now()
            if now.second % 5 == 0:
                print("tick")
            time.sleep(1)

    def close(self):
        self.closed = True
        self.close_instance = True
        # Wait until the thread is alive.
        while self.thread and self.thread.isAlive():
            time.sleep(0.5)
        print("thread is killed .. ")
        SingletonTest.__instance = None
        print("closed")
