import os
import datetime
import pandas as pd

from django.conf import settings

from utils.date_utils import BUSINESS_HOURS_START, BUSINESS_HOURS_END

"""
from utils.symbol_reader import *
s = SymbolReader("ACC")
"""


class SymbolReader:

    def __init__(self, symbol, date=None):
        self.symbol = symbol
        if not date:
            self.date = datetime.date.today().strftime("%Y-%m-%d")
        else:
            self.date = date.strftime("%Y-%m-%d")

        root = settings.MEDIA_ROOT
        self.file_name = "{symbol}_{date}.csv".format(symbol=self.symbol, date=self.date)

        self.dir = os.path.join(root, "symbol_data", symbol)

        if not os.path.exists(os.path.join(root, "symbol_data")):
            os.mkdir(os.path.join(root, "symbol_data"))
            # raise NotADirectoryError("{} Directory not found".format(os.path.join(root, "symbol_data")))
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
            # raise NotADirectoryError("{} Directory not found".format(self.dir))

        self.file_path = os.path.join(self.dir, self.file_name)

        # if not os.path.isfile(self.file_path):
        #     raise FileNotFoundError("{} data not found".format(self.symbol))

    def read(self, sample_rate: int = 0):
        if not os.path.isfile(self.file_path):
            return pd.DataFrame([])

        df = pd.read_csv(self.file_path)
        if df.empty:
            return df

        df['timestamp'] = df['timestamp'].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"))
        df['time'] = df['timestamp'].apply(lambda x: x.time())
        # limiting the results to business hours only.
        df = df[(df['time'] >= BUSINESS_HOURS_START) & (df['time'] <= BUSINESS_HOURS_END)]
        df.reset_index(inplace=True)
        if sample_rate:
            df = df[df.index % sample_rate == 0]
        return df
