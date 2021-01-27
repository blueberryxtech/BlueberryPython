"""
Service Explorer
----------------
An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.
Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

Edited Cayden Pierce, Blueberry
"""
import platform
import asyncio
import logging
import sys

from bleak import BleakClient


LONG_CHAR = "3f3e3d3c-3b3a-3938-3736-353433323130"
SHORT_CHAR = "2f2e2d2c-2b2a-2928-2726-252423222120"
async def run(address, debug=False):
    log = logging.getLogger(__name__)
    if debug:
        import sys

        log.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        log.addHandler(h)

    async with BleakClient(address) as client:
        x = await client.is_connected()
        log.info("Connected: {0}".format(x))

        long_handle = None
        short_handle = None
        for service in client.services:
            log.info("[Service] {0}: {1}".format(service.uuid, service.description))
            for char in service.characteristics:
                if (char.uuid == LONG_CHAR):
                    long_handle = char.handle
                if (char.uuid == SHORT_CHAR):
                    short_handle = char.handle

                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))
                    except Exception as e:
                        value = str(e).encode()
                else:
                    value = None
                log.info(
                    "\t[Characteristic] {0}: (Handle: {1}) ({2}) | Name: {3}, Value: {4} ".format(
                        char.uuid,
                        char.handle,
                        ",".join(char.properties),
                        char.description,
                        value,
                    )
                )
                for descriptor in char.descriptors:
                    value = await client.read_gatt_descriptor(descriptor.handle)
                    log.info(
                        "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
                            descriptor.uuid, descriptor.handle, bytes(value)
                        )
                    )
        print("\n\n\nVALUES TO ADD TO bbxChars object: ")
        print("LONG CHARACTERISTIC HANDLE: {}".format(long_handle))
        print("SHORT CHARACTERISTIC HANDLE: {}".format(short_handle))


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Missing argument MAC address, use like: python3 blueberry_details.py <MAC ADDRESS>")
        sys.exit()

    mac = sys.argv[1]
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run(mac, True))
