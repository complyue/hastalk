"""
Event processing constructs at par to Edh's

"""

import asyncio

from typing import *

from .adt import *


__all__ = ["Chan", "EventSink"]


class Chan:
    """
    Chan here is some similar to STM's TChan, see:
        http://hackage.haskell.org/package/stm/docs/Control-Concurrent-STM-TChan.html

    But unlike TChan of STM, a chan object here does NOT buffer items, when a Chan has
    no reader, any item is immediately discarded when written to it.

    And a Chan here can do both broadcasting as well as unicasting, even at the same
    time, wrt how it is consumed:

      *) Broadcast readers read a Chan with async for:
            async for ev in chan:
                ...
         Multiple such concurrent readers are fed with the same stream of items

      *) Unicast readers read a Chan by repeatedly call:
            chan.read()
         A stream of items are stochastically distributed to multiple such readers if
         they run concurrently, in a respect load-balanced.

      *) Mixing broadcast / unicast readers is techinically possible, but the semantic
         is hard to reason, and seems barely purposeful.

    """

    __slots__ = "nxt"

    def __init__(self, dupOf: Optional["Chan"] = None):
        if dupOf is None:
            loop = asyncio.get_running_loop()
            self.nxt = loop.create_future()
        elif isinstance(dupOf, Chan):
            self.nxt = dupOf.nxt
        else:
            raise TypeError(f"Can not duplicate to a Chan from type {type(dupOf)!r}")

    async def write(self, ev):
        loop = asyncio.get_running_loop()
        nxt = loop.create_future()
        if self.nxt.done():
            # TODO triage what this situation is, should be dealt at all, then how ?
            # may just be some Chans written separately after duplicated one or more
            # from a common source, I don't see big problems so far.
            pass
        else:
            self.nxt.set_result((ev, nxt))
        self.nxt = nxt

    async def read(self):
        (itm, self.nxt) = await self.nxt
        return itm

    async def __aiter__(self):
        while True:
            (itm, self.nxt) = await self.nxt
            yield itm


class EventSink:
    """
    EventSink at par to Edh's

    """

    __slots__ = ("seqn", "mrv", "chan", "subc")

    def __init__(self):
        self.seqn = 0
        self.mrv = None
        self.chan = Chan()
        self.subc = 0

    def subscribe(self) -> Tuple[Chan, Maybe[Any]]:
        """
        Returns a duplicated channel to read events, as well as the
        most recent event value.

        """
        self.subc += 1  # todo simulate int64 wrap back?
        if self.seqn > 0:
            return Chan(self.chan), Just(self.mrv)
        else:
            return Chan(self.chan), Nothing()

    async def publish(self, ev):
        self.seqn += 1  # todo simulate int64 wrap back?
        self.mrv = ev
        await self.chan.write(ev)
