import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import urllib.parse as urlparse
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from django.conf import settings

from kiteconnect import KiteConnect

class AutoLogin:
    CHROME_DRIVER_PATH = settings.CHROME_DRIVER
    API_KEY = settings.ZERODHA_CREDENTIALS.get("api_key")
    API_SECRET = settings.ZERODHA_CREDENTIALS.get("api_secret")
    USER_ID = settings.ZERODHA_CREDENTIALS.get("user_id")
    USER_PASS = settings.ZERODHA_CREDENTIALS.get("user_pass")
    USER_PIN = settings.ZERODHA_CREDENTIALS.get("user_pin")

    def __init__(self):
        self.validate()
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1366x768")
        self.chrome_options.add_argument('--disable-dev-shm-usage')

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

    def open_driver(self, url):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        browser = webdriver.Remote(self.CHROME_DRIVER_PATH, options=chrome_options)
        browser.get(url)
        time.sleep(5)
        return browser

    def update_credentials(self, data):
        from accounts.models import ZerodhaCredentials
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
            creds.save()

    def perform_login(self, **kwargs):
        try:
            print("---------------AutoLogin--------------")
            print("--Started--")
            kite = KiteConnect(self.API_KEY, self.API_SECRET)
            url = kite.login_url()
            browser=self.open_driver(url)
            print("--Running--")
            wait = WebDriverWait(browser, 10)
            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))\
                            .send_keys(self.USER_ID)

            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))\
                .send_keys(self.USER_PASS)

            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))\
                .submit()

            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))).click()
            time.sleep(5)
            browser.find_element_by_xpath('//input[@type="password"]').send_keys(self.USER_PIN)

            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))).submit()
            wait.until(EC.url_contains('status=success'))

            tokenurl = browser.current_url
            parsed = urlparse.urlparse(tokenurl)
            request_token=urlparse.parse_qs(parsed.query)['request_token'][0]
            print("--Closed--")
            browser.close()

            data = kite.generate_session(request_token, api_secret=self.API_SECRET)
            self.update_credentials(data)

        except Exception as e:
            print(e)