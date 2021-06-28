import bs4
import datetime
import requests
import pandas as pd

from django.core.management.base import BaseCommand

from accounts.models import Holidays


class Command(BaseCommand):

    BASE_URL = "https://zerodha.com/z-connect/traders-zone/holidays/"
    ROUTE = "trading-holidays-{}-nse-bse-mcx"

    def handle(self, *args, **options):
        year = datetime.datetime.now().year
        print("Fetching holidays for the Year: {}".format(year))

        url = self.BASE_URL + self.ROUTE.format(year)

        r = requests.get(url)
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.text, 'lxml')

            tables = soup.findAll("table")
            df = None
            for table in tables:
                df = pd.read_html(str(table))[0]
                break

            if df is not None and not df.empty:
                print("Holidays ... ")
                print(df)
                holidays = df.to_dict("records")

                new = 0
                for holiday in holidays:
                    name = holiday.get("Holidays")
                    date = datetime.datetime.strptime(holiday.get("Date"), "%B %d, %Y")

                    exists = Holidays.objects.filter(date=date).exists()
                    if not exists:
                        h = Holidays(holiday=name, date=date)
                        h.save()
                        new += 1
                print("New Records ... {}".format(new))
