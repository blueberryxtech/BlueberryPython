# -*- coding: utf-8 -*-
"""
cayden, Blueberry
hbldh <henrik.blidh@gmail.com>, BLEAK
"""

import sys
import logging
import asyncio
import platform
import bitstring
import argparse
import time

from bleak import BleakClient 
from bleak import _logger as logger


class Blueberry:
    def __init__(self, device_address, callback=None, debug=False):
        #translate address to be multi-platform
#        self.device_address = (
#            device_address # <--- Change to your device's address here if you are using Windows or Linux
#            if platform.system() != "Darwin"
#            else mac # <--- Change to your device's address here if you are using macOS
#        )
        self.device_address = device_address
        self.callback = callback
        self.debug = debug
        
        #Blueberry glasses GATT server characteristics information
        self.bbxService={"name": 'fnirs service',
                    "uuid": '0f0e0d0c-0b0a-0908-0706-050403020100' }
        self.bbxchars={
                  "commandCharacteristic": {
                      "name": 'write characteristic',
                          "uuid": '1f1e1d1c-1b1a-1918-1716-151413121110',
                          "handles": [None],
                            },
                    "shortFnirsCharacteristic": {
                            "name": 'short_path',
                                "uuid": '2f2e2d2c-2b2a-2928-2726-252423222120',
                                "handles": [20, 27],
                                  },
                    "longFnirsCharacteristic": {
                            "name": 'long_path',
                                "uuid": '3f3e3d3c-3b3a-3938-3736-353433323130',
                                "handles": [23, 30],
                                  }

                    }
        self.stream = False
        self.logger = None

        #logging
        self.l = None
        self.h = None

    #unpack fNIRS byte string
    def unpack_fnirs(self, sender, packet):
        data = dict()
        data["path"] = None
        #figure out which characteristic sent it (using the handle, why do we have UUID AND handle?)
        for char in self.bbxchars:
            if sender in self.bbxchars[char]["handles"]:
                data["path"] = self.bbxchars[char]["name"]
                break
            elif type(sender) == str and sender.lower() == self.bbxchars[char]["uuid"]:
                data["path"] = self.bbxchars[char]["name"]
                break
        if data["path"] == None:
            print("Error unknown handle number: {}. See: https://github.com/blueberryxtech/BlueberryPython/issues/1 or reach out to cayden@blueberryx.com".format(sender))
            return None
        #unpack packet
        aa = bitstring.Bits(bytes=packet)
        if data["path"] == "long_path" and len(packet) >= 21:
            pattern = "uintbe:8,uintbe:8,intbe:32,intbe:32,intbe:32,uintbe:8,uintbe:8,uintbe:8,uintbe:8,uintbe:8,uintbe:16"
            res = aa.unpack(pattern)
            data["packet_index"] = res[0]
            data["sample_index"] = res[1]
            data["channel1"] = res[2] #740
            data["channel2"] = res[3] #880
            data["channel3"] = res[4] #850
            data["sp"] = res[5]
            data["dp"] = res[6]
            data["hr"] = res[7]
            data["hrv"] = res[8]
            data["ml"] = res[9]
            data["temperature"] = res[10]
            data["big"] = True #big: whether or not the extra metrics were packed in
        else:
            pattern = "uintbe:8,uintbe:8,intbe:32,intbe:32,intbe:32,uintbe:8,uintbe:8"
            res = aa.unpack(pattern)
            data["packet_index"] = res[0]
            data["sample_index"] = res[1]
            data["channel1"] = res[2] #740
            data["channel2"] = res[3] #880
            data["channel3"] = res[4] #850
            data["big"] = False #big: whether or not the extra metrics were packed in
        return data

    def notification_handler(self, sender, data):
        """Simple notification handler which prints the data received."""
        data = self.unpack_fnirs(sender, data)
        if data is None:
            return
        p_idx = data["packet_index"]
        s_idx = data["sample_index"]
        path = data["path"]
        c1 = data["channel1"]
        c2 = data["channel2"]
        c3 = data["channel3"]

        if data["path"] == "long_path" and data["big"] == True:
            sp = data["sp"]
            dp = data["dp"]
            hr = data["hr"]
            hrv = data["hrv"]
            ml = data["ml"]
            temperature = data["temperature"]

        if self.debug:
            if data["path"] == "long_path" and data["big"] == True:
                print("Blueberry: {}, path: {}, index: {}, C1: {}, C2: {}, C3: {}, SP : {}, DP : {}, HR : {}, HRV : {}, ML : {}, temperature : {},".format(sender, path, p_idx, c1, c2, c3, sp, dp, hr, hrv, ml, temperature))
            else:
                print("Blueberry: {}, path: {}, index: {}, C1: {}, C2: {}, C3: {}".format(sender, path, p_idx, c1, c2, c3))

        if self.callback is not None:
            self.callback(data)

    def start(self):
        #start stream
        self.stream = True
        #start main loop
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        loop.run_until_complete(self.run(self.device_address, self.debug))

    def stop(self):
        #stop stream
        self.stream = False

    async def run(self, address, debug):
        SHORT_PATH_CHAR_UUID = self.bbxchars["shortFnirsCharacteristic"]["uuid"]
        LONG_PATH_CHAR_UUID = self.bbxchars["longFnirsCharacteristic"]["uuid"]

        print("Trying to connect...")
        async with BleakClient(address) as client:
            x = await client.is_connected()
            print("Connected to: {0}".format(x))

            await client.start_notify(SHORT_PATH_CHAR_UUID, self.notification_handler)
            await client.start_notify(LONG_PATH_CHAR_UUID, self.notification_handler)
            while self.stream:
                await asyncio.sleep(0.1)
            await client.stop_notify(SHORT_PATH_CHAR_UUID)
            await client.stop_notify(LONG_PATH_CHAR_UUID)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a","--address", help="MAC address of the blueberry")
    parser.add_argument("-d", "--debug", help="debug", action='store_true')
    args = parser.parse_args()

    #get address
    mac = args.address

    #get debug
    debug=args.debug

    save = True
    save_file = open("{}.csv".format(time.time()), "w+")
    save_file.write("timestamp,idx,path,c1,c2,c3\n")
    def my_callback(data):
        print(data)
        idx = data["packet_index"]
        path = data["path"]
        c1 = data["channel1"]
        c2 = data["channel2"]
        c3 = data["channel3"]

        if save:
            if data["path"] == "long_path" and data["big"] == True:
                    save_file.write("{},{},{},{},{},{}\n".format(time.time(), idx, path, c1, c2, c3))
            else:
                    save_file.write("{},{},{},{},{},{}\n".format(time.time(), idx, path, c1, c2, c3))

 
    bby = Blueberry(mac, callback=my_callback, debug=debug)
    bby.start() #this is blocking
    bby.stop()
    save_file.close()
