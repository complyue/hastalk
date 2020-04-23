import asyncio
from typing import *

from .adt import *

__all__ = ["EndOfStream", "EdhPeerError", "read_stream"]


class _EndOfStream:
    __slots__ = ()

    @staticmethod
    def __repr__():
        return "EndOfStream"


# Edh uses nil to mark end-of-stream, it's improper in Python to use
# None for that purpose, so here we use an explicit singleton object
EndOfStream = _EndOfStream()


class EdhPeerError(RuntimeError):
    __slots__ = ("peer_site", "details")

    def __init__(self, peer_site: str, details: str):
        self.peer_site = peer_site
        self.details = details

    def __repr__(self):
        return f"EdhPeerError({self.peer_site!r}, {self.details!r})"

    def __str__(self):
        return f"🏗️ {self.peer_site!s}\n{self.details!s}"


async def read_stream(eos: asyncio.Future, rdr: Coroutine) -> Union[_EndOfStream, Any]:
    done, _pending = await asyncio.wait(
        {eos, asyncio.create_task(rdr)}, return_when=asyncio.FIRST_COMPLETED
    )
    if len(done) <= 1 and eos in done:
        # done without unprocessed item
        await eos  # reraise exception if that caused eos
        return EndOfStream
    for fut in done:
        if fut is not eos:
            return await fut
    assert False, 'impossible to reach here'
