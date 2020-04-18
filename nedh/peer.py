"""
Peer

"""

import asyncio

from typing import *

from ..edh import *


__all__ = ["CommCmd", "Peer"]


class CommCmd:
    __slots__ = ("dir", "src")

    def __init__(self, src: str, dir_: str = ""):
        self.src = src
        self.dir = dir_

    def __repr__(self):
        return f"CommCmd({self.src!r}, dir={self.dir!r})"


class Peer:
    def __init__(
        self,
        ident,
        posting: Callable[[CommCmd], Awaitable[None]],
        hosting: Callable[[], Awaitable[CommCmd]],
        channels: Dict[Any, EventSink] = {},
    ):
        self.ident = ident

        loop = asyncio.get_running_loop()
        self.eol = loop.create_future()
        self.posting = posting
        self.hosting = hosting
        self.channels = channels

    def __repr__(self):
        return f"Peer<{self.ident}>"
