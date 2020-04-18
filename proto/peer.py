"""
Peer

"""

import asyncio

from typing import *

from ..edh import *

__all__ = ["CommCmd", "Peer"]


CmdDir = str
CmdSrc = str


class CommCmd:
    __slots__ = ("dir", "src")

    def __init__(self, src: CmdSrc, dir_: CmdDir = ""):
        self.src = src
        self.dir = dir_

    def __repr__(self):
        return f"CommCmd({self.src!r}, dir={self.dir!r})"


class Peer:
    def __init__(
        self,
        ident,
        hosting: Callable[[], Awaitable[CommCmd]],
        channels: Dict[Any, EventSink] = {},
        posting:  Callable[[CommCmd],Awaitable[None]] ,
    ):
        self.ident = ident
        loop = asyncio.get_running_loop()
        self.eol = loop.create_future()
        self.hosting = hosting
        self.channels = channels
        self.posting=posting

    def __repr__(self):
        return f"Peer<{self.ident}>"
