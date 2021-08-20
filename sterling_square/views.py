import datetime
from threading import Thread

from django.http.response import HttpResponse

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