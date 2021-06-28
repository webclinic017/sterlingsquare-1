import datetime
from pandas.tseries.offsets import BDay
from pandas import Timestamp

import os
import pickle
from django.conf import settings

from accounts.models import Holidays


BUSINESS_HOURS_START = datetime.time(hour=9, minute=15)
BUSINESS_HOURS_END = datetime.time(hour=15, minute=30)


def get_day_range(inp=None, business_hours_only=False):
    """
    Get datetime range for a given date.
    :params business_hours_only: if True, returns the range for business hours only
    """
    if not inp:
        inp = datetime.datetime.now()

    if not business_hours_only:
        min, max = datetime.datetime.combine(inp.date(), datetime.time.min), \
                   datetime.datetime.combine(inp.date(), datetime.time.max)
    else:
        min, max = datetime.datetime.combine(inp.date(), BUSINESS_HOURS_START), \
                   datetime.datetime.combine(inp.date(), BUSINESS_HOURS_END)
    return min, max


def get_previous_business_day(inp=None):
    """
    function to get previous business day
    """
    if not inp:
        inp = datetime.datetime.now()
    return (inp - BDay(1)).to_pydatetime()


def is_weekday(inp=None):
    """
    Function to check if the given datetime object is weekday or not.
    """
    if not inp:
        inp = datetime.datetime.now()
    inp = Timestamp(inp)
    day = inp.isoweekday()
    return False if day in [6, 7] else True


def is_market_opened_date(inp=None):
    """
    function to check is the market was opened on a given DATE
    """

    # UNOPTIMISED VERSION
    start, _ = get_day_range(inp)
    is_holiday = Holidays.objects.filter(date=start).exists()
    return is_weekday(start) and not is_holiday

    # OPTIMISED VERSION
    # start, _ = get_day_range(inp)
    # if inp:
    #     # If an input is provided, Use DB only
    #     is_holiday = Holidays.objects.filter(date=start).exists()
    # else:
    #     # If an input is not provided, Check if file exists
    #     file_path = os.path.join(settings.MEDIA_ROOT, "market_opened_today.pickle")
    #     if not os.path.exists(file_path):
    #         # If file doesn't exists, Use DB only
    #         is_holiday = Holidays.objects.filter(date=start).exists()
    #     else:
    #         # If file doesn't exists, check if the object is valid or not
    #         obj = {}
    #         with open(file_path, 'rb') as fi:
    #             obj = pickle.load(fi)
    #
    #         if not obj:
    #             # If object is not valid, use DB only
    #             is_holiday = Holidays.objects.filter(date=start).exists()
    #         else:
    #             if obj.get("is_market_opened_date"):
    #                 # If object is valid, use the file value
    #                 return obj.get("is_market_opened_date")
    #             else:
    #                 # If object is not valid, use DB only
    #                 is_holiday = Holidays.objects.filter(date=start).exists()
    # return is_weekday(start) and not is_holiday


def is_market_opened_date_threaded(inp=None, res=None):
    """
    function to check is the market was opened on a given DATE - Threaded - to be used inside a BG thread
    """
    start, _ = get_day_range(inp)
    is_holiday = Holidays.objects.filter(date=start).exists()
    res['is_market_opened'] = is_weekday(start) and not is_holiday


def is_market_open_now(inp=None):
    """
    is market open at the given time
    """
    # if not inp:
    #     inp = datetime.datetime.now()

    is_market_opened_today = is_market_opened_date(inp)
    # if today is weekend or a public holiday, return False because market never opened today or will open today
    if not is_market_opened_today:
        return False

    if not inp:
        inp = datetime.datetime.now()
    # return True, if time is in the range of business hours start and business hours end
    return BUSINESS_HOURS_START <= inp.time() <= BUSINESS_HOURS_END
