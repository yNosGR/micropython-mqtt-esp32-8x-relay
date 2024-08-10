import machine, onewire, ds18x20, time, json
from umqtt.simple import MQTTClient
from machine import Pin
## Get and set the watchdog
from machine import WDT
wdt = WDT(timeout = 10000)
wdt.feed() 

#CLIENT_NAME = 'esp32.temp' 
#server = 'solar.local'
#ClientID = "esp32.temp"
#topic = "cabin/temp"

#user = "solar"
#password = "solar"

def write_config_file(config):
  try:
    json_object = json.dumps(config)
    print(json_object)
    with open("config.json", "w") as outfile:
      outfile.write(json_object)
  except:
    print("unable to read config.json")

def read_config_file():
  try:
    with open("config.json", "r") as readfile:
        
      return json.load(readfile)
  except Exception as err:
    print(type(err))
    print(err.args)
    print(err)
    print("Unable to read config.json")


def connectMQTT():
    config = read_config_file()
    print('Connected to MQTT Broker "%s"' % (config['mqtt']['server']))
    client = MQTTClient(config['mqtt']['ClientID'], config['mqtt']['server'], config['mqtt']['port'], config['mqtt']['user'], config['mqtt']['password'])
    client.connect()
    return client

def reconnectMQTT():
    config = read_config_file()
    print('Failed to connect to MQTT broker, Reconnecting...')
    time.sleep(5)
    client.reconnect()

def set_relay_data():
    config = read_config_file()
    for relay in config['relays']['relay_data']:
      current_state = str(eval('relay'+relay+'.value()'))
      client.publish(config['mqtt']['topic']+config['relays']['mqttPath']+config['relays']['mqttPubTopic']+str(relay)+'/current_state', current_state, qos=0)
      client.publish(config['mqtt']['topic']+config['relays']['mqttPath']+config['relays']['mqttPubTopic']+str(relay)+'/pin', str(config['relays']['relay_data'][relay]['pin']), qos=0)
      client.publish(config['mqtt']['topic']+config['relays']['mqttPath']+config['relays']['mqttPubTopic']+str(relay)+'/name', config['relays']['relay_data'][relay]['name'], qos=0)

def sub_callback(topic,msg):
    config = read_config_file()
    decoded_topic = topic.decode()
    decoded_msg   = msg.decode()
    relay         = decoded_topic.split("/")[3]
    endpoint      = decoded_topic.split("/")[4]
    
    if endpoint == "change_state":
      ## some apps send bool as true/false, but we want it as 1/0
      if decoded_msg.lower() == "false":
        decoded_msg = "0"
      elif decoded_msg.lower() == "true":
        decoded_msg = "1"
      try:
        msg_int = int(decoded_msg)
      except:
        print("change state must only be an int, 0 or 1. What we picked off the queue: type:"+str(type(decoded_msg))+" value:"+str(decoded_msg))
      
      if (msg_int == 0 or msg_int == 1) and config['relays']['relay_data'][relay]['state'] is not msg_int:
        try:
          print('setting relay'+relay+" value to "+str(msg_int))
          exec('relay'+relay+".value("+str(msg_int)+")")
          config['relays']['relay_data'][relay]['state'] = msg_int
          write_config_file(config)
        except:
          print("msg_int:"+str(msg_int))
          print("change_state must be a 0 or 1. we got:"+str(msg_int))
          
    if endpoint == "pin":
      ## sanity checks
      try:
        msg_int = int(decoded_msg)
      except:
        print("pin must only be an int. What we picked off the queue: type:"+str(type(decoded_msg))+" value:"+str(decoded_msg))
      
      ## check to see if the pin def has changed, if so, update config.
      if config['relays']['relay_data'][relay]['pin'] == msg_int:
        print("Someone tried to change relay"+relay+"'s pin to the same thing that it already is:"+str(msg_int))
        ## exit the function 
        return
      else:
        print("Someone changed relay "+relay+" from "+str(config['relays']['relay_data'][relay]['pin'])+" to "+str(msg_int))
        for relay in config['relays']['relay_data']:
          if config['relays']['relay_data'][relay]['pin'] == msg_int:
            print('pin in use by relay '+relay+", ignoring change")
            break
        print("Pin isnt in use, updating config")
        config['relays']['relay_data'][relay]['pin'] = msg_int
        write_config_file(config)
        
    if endpoint == "name":
      if decoded_msg == config['relays']['relay_data'][relay]['name']:
        print("Someone tried to change the name of "+config['relays']['relay_data'][relay]['name']+", but it was already set to that")
      else:
        print("We got a new name for relay"+relay+" it was "+config['relays']['relay_data'][relay]['name']+" and we are changing it to "+ decoded_msg)
        config['relays']['relay_data'][relay]['name'] = decoded_msg
        write_config_file(config)
        
try:
    client = connectMQTT()
except OSError as e:
    reconnectMQTT()

config = read_config_file()

## set the subscription callback
client.set_callback(sub_callback)
## subscribe to the write path
client.subscribe(config['mqtt']['topic']+config['relays']['mqttPath']+config['relays']['mqttSubTopic']+'#')
print('subscribed to '+config['mqtt']['topic']+config['relays']['mqttPath']+config['relays']['mqttSubTopic']+'#')

## setup the dallas semi one wire pin
ds_pin = machine.Pin(config['temp_sensor']['pinNumber'])
## tell the ds18x20 driver what pin we want it to look at
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
## scan for sensors
roms = ds_sensor.scan()

print('Found DS devices: ', roms)

wdt.feed()

## set the relays as outputs
for relay in config['relays']['relay_data']:
  try:
    exec('relay'+relay + '= Pin('+str(config['relays']['relay_data'][relay]['pin'])+', Pin.OUT)')
    exec('relay'+relay+".value("+str(config['relays']['relay_data'][relay]['state'])+")")
  except Exception as err:
    print(type(err))
    print(err.args)
    print(err)
    print("Unable to set relay "+relay+" as an input using pin "+str(config['relays']['relay_data'][relay]['pin']))


while True:
  #time.sleep_ms(750)
  ## First, let's get the temps
  for rom in roms:
    b=rom
    hex_address = str(b[0])+str(b[1])+str(b[2])+str(b[3])+str(b[4])+str(b[5])+str(b[6])+str(b[7])
    try:
      msg="err"
      ds_sensor.convert_temp()
      time.sleep_ms(1000)
      msg = str(ds_sensor.read_temp(rom))
    except:
        print("Unable to poll sensor")
    try:
      print('send message %s on topic %s' % (msg, config['mqtt']['topic']+config['temp_sensor']['mqttPath']+hex_address))
      client.publish(config['mqtt']['topic']+config['temp_sensor']['mqttPath']+hex_address, msg, qos=0)
    except Exception as err:
        print(type(err))
        print(err.args)
        print(err)
        print("Unable to publish mqtt")
  ## Now let's update the status of the relays in mqtt
  set_relay_data()
  ## any messages will trigger sub_callback()
  client.check_msg()
  ## reset the timer on the watchdog.
  wdt.feed()
  time.sleep(config["time_between_runs"])
  
