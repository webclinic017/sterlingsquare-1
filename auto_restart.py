import os
import requests


if __name__ == '__main__':
    port = "4012"
    r = requests.get("https://sterling-square.softuvo.xyz/singleton")
    if r.status_code != 200:
        print("Restarting the server \n")
        # The server is crashed
        # Kill the port
        os.system("fuser -k {}".format(port))
        # Restart the server
        os.system("/var/www/html/SterlingSquare/venv/bin/python "
                  "/var/www/html/SterlingSquare/branches/milestone_1_new/Sterling-Square/manage.py "
                  "runserver 0.0.0.0:{}".format(port))
        r = requests.get("https://sterling-square.softuvo.xyz/singleton")
        print("Request Status Code : {} \n".format(r.status_code))
    else:
        print("Server already running ... \n")
