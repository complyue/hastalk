
__all__ = [
 "EndOfStream", 'EdhPeerError'
]


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

