import asyncio

from flux_led import BulbScanner, WifiLedBulb
import logging

from qozyd.models.bridges.exceptions import OfflineException
from qozyd.models.channels import SwitchChannel, ColorChannel, NumberChannel
from qozyd.models.things import Thing


from qozyd.plugins.bridge import BridgePlugin
from qozyd.utils import as_coroutine
from qozyd.utils.color import RGB


logger = logging.getLogger(__name__)


class WifiLED(BridgePlugin):
    VENDOR_PREFIX = "wifiled"

    def __init__(self, bridge):
        super().__init__(bridge)

        self.scanner = BulbScanner()
        self.bulbs = {}

    @property
    def active(self):
        return True

    @as_coroutine
    def _scan(self):
        return self.scanner.scan()

    async def find(self):
        bulb_infos = await self._scan()

        self.bulbs.clear()
        for bulb_info in bulb_infos:
            self.bulbs[bulb_info["id"]] = WifiLedBulb(bulb_info["ipaddr"])

    async def start(self, connection):
        await self.find()

        while not self.stopped:
            for thing in self.things.values():
                if self.is_online(thing):
                    await self.update_state(thing)

            await asyncio.sleep(1)

    async def scan(self):
        await self.find()

        for bulb in self.scanner.found_bulbs:
            thing = Thing(self.bridge, bulb["id"])
            thing.add_channel(SwitchChannel(thing, "power"))
            thing.add_channel(ColorChannel(thing, "color"))
            thing.add_channel(NumberChannel(thing, "coldwhite", min=0, max=100))
            thing.add_channel(NumberChannel(thing, "warmwhite", min=0, max=100))

            yield thing

    def is_online(self, thing):
        return thing.local_id in self.bulbs

    async def update_state(self, thing):
        bulb = self.bulbs[thing.local_id]
        bulb.update_state()

        await thing.channel("power").set(bulb.isOn())
        await thing.channel("color").set(RGB(*bulb.getRgb()))
        await thing.channel("coldwhite").set(int(bulb.cold_white / 255 * 100))
        await thing.channel("warmwhite").set(int(bulb.warm_white / 255 * 100))

    async def apply(self, thing, channel, value):
        if not self.is_online(thing):
            raise OfflineException

        bulb = self.bulbs[thing.local_id]

        if channel.name == "power":
            if value:
                bulb.turnOn()
            else:
                bulb.turnOff()
        elif channel.name == "color":
            bulb.setRgb(*value.rgb())
        elif channel.name == "coldwhite":
            bulb.setColdWhite(value)
        elif channel.name == "warmwhite":
            bulb.setWarmWhite(value)
        
        await channel.set(value)

        return True
