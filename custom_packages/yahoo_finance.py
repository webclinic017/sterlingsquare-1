import pandas as pd
import time  as _time
import requests


class YahooFinance:
    def __init__(self, ticker, result_range='1mo', start=None, end=None,
                 interval='15m', dropna=True):
        """
        Return the stock data of the specified range and interval
        Note - Either Use result_range parameter or use start and end
        Note - Intraday data cannot extend last 60 days
        :param ticker:  Trading Symbol of the stock should correspond with yahoo website
        :param result_range: Valid Ranges "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        :param start: Starting Date
        :param end: End Date
        :param interval:Valid Intervals - Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        :return:
        """
        if result_range is None:
            # print("start   ", _time.strptime(start, '%d-%m-%Y'))
            start = int(_time.mktime(_time.strptime(start, '%d-%m-%Y')))

            end = int(_time.mktime(_time.strptime(end, '%d-%m-%Y')))
            # defining a params dict for the parameters to be sent to the API
            params = {'period1': start, 'period2': end, 'interval': interval}

        else:
            params = {'range': result_range, 'interval': interval}

        # sending get request and saving the response as response object
        url = "https://query1.finance.yahoo.com/v8/finance/chart/{}".format(
            ticker)
        r = requests.get(url=url, params=params)
        data = r.json()
        # Getting data from json
        error = data['chart']['error']
        if error:
            raise ValueError(error['description'])
        self._result = self._parsing_json(data)
        if dropna:
            self._result.dropna(inplace=True)

    @property
    def result(self):
        return self._result

    def _parsing_json(self, data):
        timestamps = data['chart']['result'][0]['timestamp']
        # Formatting date from epoch to local time
        timestamps = [
            _time.strftime('%a, %d %b %Y %H:%M:%S', _time.localtime(x)) for x
            in timestamps]
        volumes = data['chart']['result'][0]['indicators']['quote'][0][
            'volume']
        opens = data['chart']['result'][0]['indicators']['quote'][0]['open']
        opens = self._round_of_list(opens)
        closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
        closes = self._round_of_list(closes)
        lows = data['chart']['result'][0]['indicators']['quote'][0]['low']
        lows = self._round_of_list(lows)
        highs = data['chart']['result'][0]['indicators']['quote'][0]['high']
        highs = self._round_of_list(highs)
        df_dict = {'Open': opens, 'High': highs, 'Low': lows, 'Close': closes,
                   'Volume': volumes}
        df = pd.DataFrame(df_dict, index=timestamps)
        df.index = pd.to_datetime(df.index)
        return df

    def _round_of_list(self, xlist):
        temp_list = []
        for x in xlist:
            if isinstance(x, float):
                temp_list.append(round(x, 2))
            else:
                temp_list.append(pd.np.nan)
        return temp_list

    def to_csv(self, file_name):
        self.result.to_csv(file_name)


TG_DATA = [{'symbol': 'WIPRO', 'series': 'EQ', 'openPrice': 282.5,
            'highPrice': 298.45, 'lowPrice': 282.5, 'ltp': 292.55,
            'previousPrice': 284.55, 'netPrice': 2.81,
            'tradedQuantity': 41937351.0, 'turnoverInLakhs': 123216.13,
            'lastCorpAnnouncementDate': '08-Jul-2020',
            'lastCorpAnnouncement': 'Annual General Meeting'},
           {'symbol': 'SBIN', 'series': 'EQ', 'openPrice': 198.55,
            'highPrice': 203.85, 'lowPrice': 197.0, 'ltp': 203.7,
            'previousPrice': 198.15, 'netPrice': 2.8,
            'tradedQuantity': 48488142.0, 'turnoverInLakhs': 96922.95,
            'lastCorpAnnouncementDate': '15-Jun-2018',
            'lastCorpAnnouncement': 'Annual General Meeting/ Change In Registrar And Transfer Agent'},
           {'symbol': 'TECHM', 'series': 'EQ', 'openPrice': 749.4,
            'highPrice': 770.6, 'lowPrice': 747.5, 'ltp': 763.7,
            'previousPrice': 750.0, 'netPrice': 1.83,
            'tradedQuantity': 4918291.0, 'turnoverInLakhs': 37487.21,
            'lastCorpAnnouncementDate': '23-Jul-2020',
            'lastCorpAnnouncement': 'Annual General Meeting/Dividend - Rs 5 Per Share'},
           {'symbol': 'TCS', 'series': 'EQ', 'openPrice': 2330.95,
            'highPrice': 2383.0, 'lowPrice': 2330.15, 'ltp': 2370.3,
            'previousPrice': 2331.15, 'netPrice': 1.68,
            'tradedQuantity': 4145429.0, 'turnoverInLakhs': 98141.37,
            'lastCorpAnnouncementDate': '16-Jul-2020',
            'lastCorpAnnouncement': 'Interim Dividend - Rs    5 Per Share'},
           {'symbol': 'HEROMOTOCO', 'series': 'EQ', 'openPrice': 2949.15,
            'highPrice': 3007.7, 'lowPrice': 2948.75, 'ltp': 2990.9,
            'previousPrice': 2948.75, 'netPrice': 1.43,
            'tradedQuantity': 1525239.0, 'turnoverInLakhs': 45534.33,
            'lastCorpAnnouncementDate': '30-Jul-2020',
            'lastCorpAnnouncement': 'Annual General Meeting/Dividend - Rs 25 Per Share'}]
