from flux_led import BulbScanner, WifiLedBulb

from qozyd.models.bridges.exceptions import OfflineException
from qozyd.models.bridges import Bridge
from qozyd.models.channels import SwitchChannel, ColorChannel, NumberChannel
from qozyd.models.things import Thing

import time
from qozyd.utils.color import RGB


class WifiLED(Bridge):
    VENDOR_PREFIX = "wifiled"
    _v_bulbs = {}
    _v_scanner = BulbScanner()

    def __init__(self, instance_id):
        super().__init__(instance_id)

        self._v_scanner = BulbScanner()
        self._v_bulbs = {}

    @property
    def active(self):
        return True

    def start(self, connection):
        while not self.stopped:
            bulb_infos = self._v_scanner.scan()

            self._v_bulbs.clear()
            for bulb_info in bulb_infos:
                self._v_bulbs[bulb_info["id"]] = WifiLedBulb(bulb_info["ipaddr"])

            for thing in self.things.values():
                if self.is_online(thing):
                    self.update_state(thing)

            time.sleep(1)

    def scan(self):
        for bulb in self._v_scanner.found_bulbs:
            thing = Thing(self, bulb["id"])
            thing.add_channel(SwitchChannel(thing, "power"))
            thing.add_channel(ColorChannel(thing, "color"))
            thing.add_channel(NumberChannel(thing, "coldwhite", min=0, max=100))
            thing.add_channel(NumberChannel(thing, "warmwhite", min=0, max=100))

            yield thing

    def is_online(self, thing):
        return thing.local_id in self._v_bulbs

    def update_state(self, thing):
        bulb = self._v_bulbs[thing.local_id]
        bulb.update_state()

        thing.channel("power").set(bulb.isOn())
        thing.channel("color").set(RGB(*bulb.getRgb()))
        thing.channel("coldwhite").set(int(bulb.cold_white / 255 * 100))
        thing.channel("warmwhite").set(int(bulb.warm_white / 255 * 100))

    def apply(self, thing, channel, value):
        if not self.is_online(thing):
            raise OfflineException

        bulb = self._v_bulbs[thing.local_id]

        if channel.name == "power":
            if value:
                bulb.turnOn()
            else:
                bulb.turnOff()
        elif channel.name == "color":
            bulb.setRgb(value[0], value[1], value[2])
        elif channel.name == "coldwhite":
            bulb.setColdWhite(value)
        elif channel.name == "warmwhite":
            bulb.setWarmWhite(value)
        
        channel.set(value)

        return True
