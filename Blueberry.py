# -*- coding: utf-8 -*-
"""
cayden, Blueberry
hbldh <henrik.blidh@gmail.com>, BLEAK

This is the Blueberry class. Use it to connect to the Blueberry and stream data.

If there are features missing add them and make a PR or reach out with a Github issue or email cayden@blueberryx.com

"""

import sys
import logging
import asyncio
import platform
import bitstring
import argparse
import time
import signal
import atexit

from bleak import BleakClient 
from bleak import _logger as logger

class Blueberry:
    """
    Blueberry class to be instantatied in users' programs and used to stream from the Blueberry"
    Works in Windows, Linux, MacOS, and Raspberry Pi
    Be aware that the "run()" funcation is asynchronous with asyncio, so it must be handled as such. - see the example scripts for how to deal with it.
    """
    def __init__(self, device_address, callback=None, debug=False):
        self.device_address = device_address
        self.callback = callback
        self.debug = debug

        self.client = None
        
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
                                "handles": [19, 20, 27, 47],
                                  },
                    "longFnirsCharacteristic": {
                            "name": 'long_path',
                                "uuid": '3f3e3d3c-3b3a-3938-3736-353433323130',
                                "handles": [23, 31, 22, 51],
                                  }

                    }
        self.stream = False
        self.logger = None

        #logging
        self.l = None
        self.h = None

        #stop if killed
        # Clean up connections, etc. when exiting (even by KeyboardInterrupt)
        #atexit.register(self.stop)

    def _cleanup(self):
        """Clean up connections, so that the underlying OS software does not
        leave them open.
        """
        # Use a copy of the list because each connection will be deleted
        # on disconnect().
        for connection in self._connections.copy():
            connection.disconnect()

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
            data["ptt_mean_amplitude"] = res[5]
            data["ptt_ratio"] = res[6]
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
            ptt_mean_amplitude = data["ptt_mean_amplitude"]
            ptt_ratio = data["ptt_ratio"]
            hr = data["hr"]
            hrv = data["hrv"]
            ml = data["ml"]
            temperature = data["temperature"]

        if self.debug:
            if data["path"] == "long_path" and data["big"] == True:
                print("Blueberry: {}, path: {}, index: {}, C1: {}, C2: {}, C3: {}, ptt_mean_amplitude : {}, ptt_ratio : {}, HR : {}, HRV : {}, ML : {}, temperature : {},".format(sender, path, p_idx, c1, c2, c3, ptt_mean_amplitude, ptt_ratio, hr, hrv, ml, temperature))
            else:
                print("Blueberry: {}, path: {}, index: {}, C1: {}, C2: {}, C3: {}".format(sender, path, p_idx, c1, c2, c3))

        if self.callback is not None:
            self.callback(data)

    async def stop(self):
        #stop stream
        print("Quitting, but first must disconnect...")
        self.stream = False
        await asyncio.sleep(0.2)
        if self.client != None:
            await self.client.disconnect()

    async def run(self):
        self.stream = True

        #connect and stream
        SHORT_PATH_CHAR_UUID = self.bbxchars["shortFnirsCharacteristic"]["uuid"]
        LONG_PATH_CHAR_UUID = self.bbxchars["longFnirsCharacteristic"]["uuid"]

        print("Trying to connect...")
        async with BleakClient(self.device_address) as self.client:
            x = await self.client.is_connected()
            print("Connected to: {0}".format(self.device_address))

            await self.client.start_notify(SHORT_PATH_CHAR_UUID, self.notification_handler)
            await self.client.start_notify(LONG_PATH_CHAR_UUID, self.notification_handler)
            while self.stream:
                await asyncio.sleep(0.1)
            await self.client.stop_notify(SHORT_PATH_CHAR_UUID)
            await self.client.stop_notify(LONG_PATH_CHAR_UUID)
        print("Blueberry disconnected.")
