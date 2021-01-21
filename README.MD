# Blueberry Python SDK

Connect to Blueberry brain sensing pod from Linux, MacOS, RasbperryPi, and Windows.

## Install

You should have Python 3.6/3.7/3.8 installed and the corresponding pip package installed.

Go ahead and `git clone` this repo (or your fork/copy of it): https://github.com/blueberryxtech/BlueberryPython. Move into the directory you just cloned (`cd BlueberryGlassesServer`).  

Now we need to setup a virtual environment and install dependencies.   

If in Linux/Raspberry Pi, run `sudo apt-get install libatlas-base-dev`.    

Setup and activate virtualenv:
```
pip3 install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
```

Install packages:
```
pip3 install -r requirements.txt
```

Good to go!

## Tested

Ubuntu 20, MacOS, Raspberry Pi 3B+.
Should work in Windows 10. Not tested.

## Scripts

Blueberry.py - connect, see data, and save data to a file  
bby_data_plot.py - plot data created with bby_stream.py  
list_devices.py - scan Bluetooth to find your Blueberry  
bby_details.py - see information about your Blueberry

## Getting Started

List all available Blueberry units (make sure yours is on):
```
python3 list_bbys.py
```

Now connect to the unit that you want stream from:
```
python3 Blueberry.py -a <Blueberry MAC address> -d
```

Now plot the data:  
```
python3 bby_data_plot.py -f <name of csv file.csv>
```

## Use in your own code

Blueberry.py file has a class `Blueberry` that is designed to be imported into your project. Just instantiate the class, pass in the device address and a callback, and use the start() function to start connecting and streaming. The callback should accept one dictionary arguement which is structured as follows:

LONG path response:
```
{'path': 'long_path', 'packet_index': 59, 'channel1': 194, 'channel2': 261, 'channel3': 317, 'sp': 154, 'dp': 55, 'hr': 0, 'hrv': 0, 'ml': 70, 'temperature': 5397}
```
SHORT path response:
```
{'path': 'short_path', 'packet_index': 11, 'channel1': 29074, 'channel2': 13263, 'channel3': 76933}
```
### Estimated Metrics (not for medical use, experimental):
DP = diastolic blood pressure
SP = systolic blood pressure
HR = heart rate
HRV = heart rate variability
ML = mental_load
temperature = body temperature (experimental)

## Help

Email cayden at blueberryx.com
