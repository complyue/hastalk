"""
Event processing constructs at par to Edh's

PubChan/SubChan here are some similar to STM's TChan, see:
    http://hackage.haskell.org/package/stm/docs/Control-Concurrent-STM-TChan.html

But unlike TChan of STM, PubChan here is not buffering items, when a PubChan has
no SubChan reading its item stream, the item written to the PubChan is discarded
immediately.

Multiple SubChan can consume items from a single PubChan concurrently, and a
SubChan's buffer is unbounded, so a slow consumer to a fast producer will increase
the program's memory footprint, which will be ever increasing until the consumers
catch up with the producer.

"""

import asyncio

from typing import *

from .adt import *


__all__ = ["EndOfStream", "PubChan", "SubChan", "EventSink"]


class _EndOfStream:
    __slots__ = ()

    @staticmethod
    def __repr__():
        return "EndOfStream"


EndOfStream = _EndOfStream()


class PubChan:
    """
    Publisher's channel, write only

    """

    __slots__ = "nxt"

    def __init__(self):
        loop = asyncio.get_running_loop()
        self.nxt = loop.create_future()

    def write(self, ev):
        loop = asyncio.get_running_loop()
        nxt = loop.create_future()
        self.nxt.set_result((ev, nxt))
        self.nxt = nxt

    async def stream(self):
        """
        This is the async iterator to consume subsequent items from this
        channel.
        """
        nxt = self.nxt
        while True:
            (itm, nxt) = await nxt
            if itm is EndOfStream:
                break
            yield itm


class SubChan:
    """
    Subscriber's channel, read only.
    
    """

    __slots__ = "nxt"

    def __init__(self, pubChan: "PubChan"):
        """
        Create a subscriber's channel from a publisher's channel

        All subsequent items written to the PubChan will be buffered for this
        SubChan until consumed with `subChan.read()`

        CAVEAT: Consuming this SubChan slower than producing to the PubChan
                will increase memory footprint.
        """
        self.nxt = pubChan.nxt

    async def read(self):
        (itm, self.nxt) = await self.nxt
        return itm


class EventSink:
    """
    EventSink at par to Edh's

    """

    __slots__ = ("seqn", "mrv", "chan", "subw")

    def __init__(self):
        # sequence number
        self.seqn = 0
        # most recent event value
        self.mrv = None
        # the publish channel
        self.chan = PubChan()
        # subscriber waiters, must be coroutines
        self.subw = []

    async def publish(self, ev):
        if self.seqn >= 9223372036854775807:
            # int64 wrap back to 1 on overflow
            self.seqn = 1
        else:
            self.seqn += 1
        self.mrv = ev
        self.chan.write(ev)

    async def stream(self):
        """
        This is the async iterator an event consumer should use to consume
        subsequent events from this sink.

        """
        nxt = self.chan.nxt
        if self.seqn > 0:
            yield self.mrv
        subw = self.subw
        if len(subw) > 0:
            self.subw = []
            for producer in subw:
                asyncio.create_task(producer)
        while True:
            (itm, nxt) = await nxt
            if itm is EndOfStream:
                break
            yield itm

    def runProducer(self, producer: Coroutine):
        """
        This is the producer scheduler that should be used to schedule a
        coroutine to run, which is going to publish events into this sink,
        but only after some consumer has started consuming events from
        this sink, i.e. to ensure no event from the producer coroutine can
        be missed by the consumer.
        """
        self.subw.append(producer)
