import pychrome
from selenium import webdriver
from datetime import time

options = webdriver.ChromeOptions()
# options.add_argument("user-data-dir=/Users/davidshivaji/Library/Application Support/Google/Chrome/Profile 7")
options.add_argument("--remote-debugging-port=8000")
chromedriver = webdriver.Chrome(chrome_options=options)

def outputstart(**kwargs):
    print("start ", kwargs)

driver = chromedriver

dev_tools = pychrome.Browser(url="http://localhost:8000")
tab = dev_tools.list_tab()[0]
tab.start()

url = 'https://google.com'

start = time.time()
driver.get(url)
tab.call_method("Network.emulateNetworkConditions",
            offline=False,
            latency=100,
            downloadThroughput=93750,
            uploadThroughput=31250,
            connectionType="wifi")

tab.call_method("Network.enable", _timeout=20)
tab.set_listener("Network.requestWillBeSent", outputstart)