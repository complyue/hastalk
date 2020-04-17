"""
Event Processing

"""

import asyncio

from typing import *

from .adt import *


__all__ = ["BrdCstChan", "EventSink"]


class BrdCstChan:
    """
    Broadcasting channel par to STM's see:
        http://hackage.haskell.org/package/stm/docs/Control-Concurrent-STM-TChan.html#v:newBroadcastTChan

    But unlike with STM, such a chan can be read without dup

    While in Pythonic ways, such a chan can be used like:
        async for ev in <chan>:
            ...

    """

    __slots__ = "nxt"

    def __init__(self):
        loop = asyncio.get_running_loop()
        self.nxt = loop.create_future()

    async def write(self, ev):
        loop = asyncio.get_running_loop()
        nxt = loop.create_future()
        self.nxt.set_result((ev, nxt))
        self.nxt = nxt

    async def read(self):
        (ev, _) = await self.nxt
        return ev

    async def __aiter__(self):
        nxt = self.nxt
        while True:
            (ev, nxt) = await nxt
            yield ev


class EventSink:
    """
    EventSink par to Edh's

    """

    __slots__ = ("seqn", "mrv", "chan", "subc")

    def __init__(self):
        self.seqn = 0
        self.mrv = None
        self.chan = BrdCstChan()
        self.subc = 0

    def subscribe(self) -> Tuple[BrdCstChan, Maybe[Any]]:
        """
        Returns a readable channel and the most recent event value.

        """
        self.subc += 1  # todo simulate int64 wrap back?
        if self.seqn > 0:
            return self.chan, Just(self.mrv)
        else:
            return self.chan, Nothing()

    async def publish(self, ev):
        self.seqn += 1  # todo simulate int64 wrap back?
        self.mrv = ev
        await self.chan.write(ev)
