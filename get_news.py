import datetime

import dateutil

from custom_packages.yahoo_finance import YahooFinance

today = datetime.datetime.now()
# start = today.date() - dateutil.relativedelta.relativedelta(months=18)
start = "01-01-2019"
end = "01-07-2020"
tata_power = YahooFinance('HDFC.NS', result_range=None, start=start, end=end,
                          interval='1m', dropna='True').result
print(tata_power.values.tolist()[len(tata_power.values.tolist()) - 1][0])
price_list = []
count = 0
for i, j in tata_power.iterrows():
    temp_price_list = []
    dt_object1 = datetime.datetime.strptime(str(i), "%Y-%m-%d %H:%M:%S")
    my_time = dt_object1.time()
    my_datetime = datetime.datetime.combine(i, my_time)
    date = datetime.datetime.timestamp(my_datetime)
    temp_price_list.append(int(date) * 1000)
    temp_price_list.append(tata_power.values.tolist()[count][2])
    price_list.append(temp_price_list)
    count += 1
