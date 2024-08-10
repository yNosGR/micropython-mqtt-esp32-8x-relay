# Using MicroPython uMQTT.simple on the ESP32_Relay_8x board
## Quick Setup instructions
- Install Micropython on your board, I used Thonny
- Install umqtt
```
import mip
mip.install("umqtt.simple")
```
- Copy `sample.config.json` to `config.json`, then edit `config.json` to match your environment. Be sure to use a [a json linter](https://jsonformatter.curiousconcept.com/) to verify your json is clean.
- Use Thonny (or whatever tool you use) to copy `boot.py`, `main.py`, `ping.py`,`config.json` onto the board.
- Reboot your node and have fun, it should now be hitting your mqtt broker and getting/setting your relays!

## What mqtt paths does it check?
Since I am using this in with NodeRed in my off grid cabin, I will use those paths in my examples.
- To change the `pin` of the zeroth relay, write the pin number to `cabin/esp32Num1/relay_write/0/pin`
- To change the `name` of the zeroth relay, write the new string to `cabin/esp32Num1/relay_write/0/name`
- To change the `state` of the zeroth relay, write the new state to `cabin/esp32Num1/relay_write/0/change_state` - this can be false/true/False/True/0/1
## What paths does it write to?
- 'Relay0`'s state is written to `cabin/esp32Num1/relay_state/0/current_state`
- 'Relay0`'s name is written to `cabin/esp32Num1/relay_state/0/name`
- 'Relay0`'s pin number is written to `cabin/esp32Num1/relay_state/0/pin`
## What else does it do?
Currently it also has a pin setup for DS1820 temp sensors. It will scan the bus and write out the temp to `cabin/temp/DEVICESERIALNUMBER`. I currently have 2, `indoor` and `outdoor`.
## To Do
store the `DEVICESERIALNUMBER` and `name` for the temp sensors to make identification easier. 

