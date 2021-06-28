import os

from django.conf import settings

import pandas as pd
from accounts.models import ZerodhaCredentials

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AutoLogin:

    # CHROME_DRIVER_PATH = os.environ.get("CHROMEDRIVER")
    # API_KEY = os.environ.get("STERLING_SQUARE_API_KEY")
    # API_SECRET = os.environ.get("STERLING_SQUARE_API_SECRET")
    #
    # USER_ID = os.environ.get("STERLING_SQUARE_USER_ID")
    # USER_PASS = os.environ.get("STERLING_SQUARE_PASS")
    # USER_PIN = os.environ.get("STERLING_SQUARE_PIN")

    CHROME_DRIVER_PATH = settings.CHROME_DRIVER
    API_KEY = settings.ZERODHA_CREDENTIALS.get("api_key")
    API_SECRET = settings.ZERODHA_CREDENTIALS.get("api_secret")

    USER_ID = settings.ZERODHA_CREDENTIALS.get("user_id")
    USER_PASS = settings.ZERODHA_CREDENTIALS.get("user_pass")
    USER_PIN = settings.ZERODHA_CREDENTIALS.get("user_pin")

    # APPLICATION_HOST = os.environ.get("STERLING_SQUARE_HOST")
    APPLICATION_HOST = settings.APPLICATION_BASE_URL

    # LOGIN_URL = "https://kite.zerodha.com/connect/login?v=3&api_key={}".format(API_KEY)
    LOGIN_URL = "{}/auth/step_1".format(APPLICATION_HOST, API_KEY)

    def __init__(self):
        self.validate()
        print("++"*2)
        print(settings.CHROME_DRIVER, self.CHROME_DRIVER_PATH)
        print("++"*2)

        self.chrome_options = Options()
        # self.chrome_options.add_argument("--headless")
        # if "localhost" in self.APPLICATION_HOST or "127.0.0.1" in self.APPLICATION_HOST:
        #     pass
        # else:
        #     self.chrome_options.add_argument("--no-sandbox")
        # self.chrome_options.add_argument("--disable-gpu")
        # self.chrome_options.add_argument("--window-size=1366x768")
        # self.chrome_options.add_argument('--disable-dev-shm-usage')
        # self.chrome_options.add_argument(
        #     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        # )
        # print(self.LOGIN_URL)
        self.driver = None

    def validate(self):
        if not self.CHROME_DRIVER_PATH:
            # Error to raise when chromedriver path is not provided
            raise ValueError("Environment Variable 'CHROMEDRIVER' not provided.")

        if not self.API_KEY:
            # Error to raise when kite.trades API key is not provided path is not provided
            raise ValueError("Environment Variable 'STERLING_SQUARE_API_KEY' not provided.")

        if not self.USER_ID:
            # Error to raise when kite.zerodha.com user id is not provided path is not provided
            raise ValueError("Environment Variable 'STERLING_SQUARE_USER_ID' not provided.")

        if not self.USER_PASS:
            # Error to raise when kite.zerodha.com user id is not provided path is not provided
            raise ValueError("Environment Variable 'STERLING_SQUARE_PASS' not provided.")

        if not self.USER_PIN:
            # Error to raise when kite.zerodha.com user id is not provided path is not provided
            raise ValueError("Environment Variable 'STERLING_SQUARE_PIN' not provided.")

        if not self.LOGIN_URL or "None" in self.LOGIN_URL:
            raise ValueError("Invalid Login URL: {}".format(self.LOGIN_URL))

    def perform_login(self, auto_close=False):
        try:
            print("++"*30)
            print(self.CHROME_DRIVER_PATH)
            print(self.APPLICATION_HOST)
            print("++"*30)
            if "localhost" in self.APPLICATION_HOST or "127.0.0.1" in self.APPLICATION_HOST:
                self.driver = webdriver.Chrome(self.CHROME_DRIVER_PATH, options=self.chrome_options)
            else:
                self.driver = webdriver.Remote(self.CHROME_DRIVER_PATH, options=self.chrome_options)
            self.driver.delete_all_cookies()
            self.driver.get(self.LOGIN_URL)

            print("Waiting for Step 1 ...")
            # Wait for the userid Input field
            WebDriverWait(driver=self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.ID, 'userid')
                )
            )
            print("Starting Step 1 ... ")
            user_id = self.driver.find_element_by_id("userid")
            user_id.send_keys(self.USER_ID)

            password = self.driver.find_element_by_id("password")
            password.send_keys(self.USER_PASS)

            first_button = self.driver.find_element_by_class_name("button-orange")
            first_button.click()

            print("Step 1 Done ...")
            print("Waiting for Step 2 ...")

            # Wait for the pin Input field
            WebDriverWait(driver=self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.ID, 'pin')
                )
            )
            print("Starting Step 2 ... ")

            pin = self.driver.find_element_by_id('pin')
            pin.send_keys(self.USER_PIN)

            second_click = self.driver.find_element_by_class_name('button-orange')
            second_click.click()

            print("Step 2 Done ...")
            WebDriverWait(driver=self.driver, timeout=50).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, 'nav-outer')
                )
            )
            if auto_close:
                self.close()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print("PERFORM LOGIN EXCEPTION ", e)

            creds = ZerodhaCredentials.objects.all()
            if creds.exists():
                print(pd.DataFrame(creds.values()))

            self.close()

    def close(self):
        if self.driver:
            self.driver.quit()
