import time
import logging
import requests
from kiteconnect import KiteTicker, KiteConnect

logging.basicConfig(level=logging.DEBUG)

# Initialise
kws = KiteConnect(api_key="fact6majxka99prm")
# # print(kws.instruments())
# login_url = kws.login_url()
# print(login_url)


# oLIZJeLR87r3DWZhKDjuLpA2gttNHa4e

data = kws.generate_session("sZ4Uxdwu7sYgdDF2iOrC5MlHbNphHRzp",
                          api_secret="zubxck8rxwnghgfd3e8rhxs49tqxzijr")
print(data)
kws.set_access_token(data["access_token"])
