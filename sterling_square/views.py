import os
import json
import pickle
import datetime
import requests
from threading import Thread
from kiteconnect import KiteConnect

from django.shortcuts import redirect
from django.http.response import HttpResponse

from django.conf import settings
from utils.AutoLogin import AutoLogin
# from utils.util_functions import read_zerodha_credentials
from accounts.models import ZerodhaCredentials
from accounts.tasks import sync_credentials
from .TickerSingleton import Singleton2


def init_singleton():
    Singleton2.get_instance("init")


def start_singleton(request):
    t = Thread(target=init_singleton)
    t.start()

    return HttpResponse("OK")


def initialize(request):
    sync_credentials.apply_async(eta=datetime.datetime.now())
    return HttpResponse("OK")


# t = Thread(target=init_singleton)
# t.start()

# t2 = Thread(target=init_singleton_web_socket)
# t2.start()


def auth_step_1(request):
    """
    Step 1 for Zerodha Authentication - To be only used by the backend server
    """
    print("Auth Step 1 ..... ")
    credentials = getattr(settings, "ZERODHA_CREDENTIALS")
    if not credentials:
        return HttpResponse("Invalid Credentials")

    api_key = credentials.get("api_key")
    if not api_key:
        return HttpResponse("Invalid Credentials")

    return redirect(
        "https://kite.zerodha.com/connect/login?v=3&api_key={}".format(api_key)
    )


def auth_step_2(request):
    """
    Step 2: Callback view for Authentication
    """
    request_token = request.GET.get("request_token")
    if not request_token:
        return HttpResponse("Authentication failed : {}".format("Invalid Request Token"))

    credentials = getattr(settings, "ZERODHA_CREDENTIALS")
    if not credentials:
        return HttpResponse("Invalid Credentials")

    api_key = credentials.get("api_key")
    if not api_key:
        return HttpResponse("Invalid Credentials")

    api_secret = credentials.get("api_secret")
    if not api_secret:
        return HttpResponse("Invalid Credentials")

    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token=request_token, api_secret=api_secret)

    if data:
        print("Retrieved the authentication data...")

    credentials_path = credentials.get("zerodha_creds_path")
    if not credentials_path:
        return HttpResponse("")

    # Save the Access Token in the pickle file
    if os.path.exists(credentials_path):
        os.remove(credentials_path)

    creds = ZerodhaCredentials.objects.all().order_by("id").first()
    login_time = data.get("login_time")
    if "login_time" in data:
        del data['login_time']
    if not creds:
        creds = ZerodhaCredentials(credentials=json.dumps(data), login_time=login_time)
        creds.save()
    else:
        creds.credentials = json.dumps(data)
        creds.login_time = login_time
        creds.updated = datetime.datetime.now()
        creds.save()

    with open(credentials_path, 'wb') as handle:
        pickle.dump(data, handle)

    print("Saved the Access Token ...")
    return redirect("/")
