from django.urls import path

from . import consumer
from threading import Thread
#
# def blah():
#     c = consumer.Consumer.as_asgi()
#
#     # start_kitesocket(113921, c)
#     Thread(target=start_kitesocket, args=(113921,c)).start()


websocket_urlpatterns = [
    # path('ws/wbs/<str:symbol>', consumer.ConsumerV2.as_asgi()),
    path('ws/wbs2/<str:symbol>', consumer.ConsumerV3.as_asgi()),
    path('ws/portfolio/', consumer.LatestPortfolioValueConsumer.as_asgi()),
    # path('ws/price_change/<str:symbol>', consumer.PriceChangeConsumer.as_asgi()),
    # path('ws/wbs/<str:symbol>', consumer.Consumer.as_asgi())
]



