import requests
import time


while True:
    try:
        print("updating @ {}".format(time.clock()))
        page = requests.get('http://www.elevation-challenge.com/force_update')
    except:
        print("Didnt Update due to exeception")
    time.sleep(30*60)