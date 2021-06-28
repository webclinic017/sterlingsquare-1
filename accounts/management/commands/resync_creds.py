from django.core.management.base import BaseCommand

import traceback
from utils.AutoLogin import AutoLogin
from utils.util_functions import read_zerodha_credentials


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            print("Refreshing the Credentials ..... ")
            login = AutoLogin()
            login.perform_login(auto_close=True)
            print("Refreshed Credentials ...... ")

            _, creds = read_zerodha_credentials(True)
            print("Login Time: {}".format(creds.login_time))
        except Exception as e:
            print(traceback.format_exc())
            print("Error Refreshing the Credentials ... {}".format(str(e)))
