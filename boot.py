# boot.py
import os, machine, sys, network, json
from ping import ping

## create a read config function
def read_config_file():
  try:
    with open("config.json", "r") as readfile:
        
      return json.load(readfile)
  except Exception as err:
    print(type(err))
    print(err.args)
    print(err)
    print("Unable to read config.json")

## now run that function
config = read_config_file()


network.hostname(config['mqtt']['CLIENT_NAME'])

sta_if = network.WLAN(network.STA_IF)
## setup an access point so we can connect if the other AP isnt available.
ap_if  = network.WLAN(network.AP_IF)
ap_if.config(ssid='esp_32_relay')
ap_if.active(True)

def connectWiFi():
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(config['ssid'], config['wifi_pw'])
        while not sta_if.isconnected():
          pass # wait till connection
    print('network config:', sta_if.ifconfig())
    
connectWiFi()

reboot   = """use machine.reset()"""
ls       = """use os.listdir('path')"""
ifconfig = """network config:""", sta_if.ifconfig()
webrepl  = """use import webrepl_setup"""
