"""
Micro Protocol that Nedh speaks

"""


import asyncio

from typing import *

from ..edh import *


__all__ = ["Packet", "textPacket", "sendPacket", "receivePacketStream"]


MAX_HEADER_LENGTH = 60


PacketDirective = str
PacketPayload = bytes


class Packet(NamedTuple):
    dir: PacketDirective
    payload: PacketPayload


def textPacket(dir_: str, txt: str):
    if not txt.startswith("\n"):
        txt = "\n" + txt
    if not txt.endswith("\n"):
        txt = txt + "\n"
    Packet(dir_, txt.encode("utf-8"))


async def sendPacket(
    peer_site: str, outlet: asyncio.StreamWriter, pkt: Packet,
):
    pkt_len = len(pkt.payload)
    pkt_hdr = f"[{pkt_len!r}#{pkt.dir!s}]"
    if len(pkt_hdr) > MAX_HEADER_LENGTH:
        raise EdhPeerError(self.peer_site, "sending out long packet header")
    outlet = outlet
    await outlet.drain()
    outlet.write(pkt_hdr.encode("utf-8"))
    outlet.write(pkt.payload)


PacketSink = Callable[[Packet], Awaitable]

# as Python lacks tail-call-optimization, looping within (async) generator
# is used here instead of tail recursion
async def receivePacketStream(
    peer_site: str,
    intake: asyncio.StreamReader,
    pkt_sink: PacketSink,
    eos: asyncio.Future,
):
    """
    Receive all packets being streamed to the specified intake stream

    The caller is responsible to close the intake/outlet streams anyway
    appropriate, but only after eos is signaled.
    """

    async def parse_pkts():
        readahead = b""

        def parse_hdr():
            nonlocal readahead
            while True:
                if len(readahead) < 1:
                    readahead = await intake.read(MAX_HEADER_LENGTH)
                    if not readahead:
                        return -1, "eos"
                if b"[" != readahead[0]:
                    raise EdhPeerError(peer_site, "missing packet header")
                hdr_end_pos = readahead.find(b"]")
                if hdr_end_pos < 0:
                    readahead += await intake.read(MAX_HEADER_LENGTH)
                    continue
                # got a full packet header
                hdr = readahead[1:hdr_end_pos].decode("utf-8")
                readahead = readahead[hdr_end_pos + 1 :]
                plls, dir_ = hdr.split("#", 1)
                payload_len = int(plls)
                return payload_len, dir_

        while True:
            payload_len, dir_ = parse_hdr()
            if payload_len < 0:  # normal eos, try mark and done
                if not eos.done():
                    eos.set_result(EndOfStream)
                return
            more2read = payload_len - len(readahead)
            if more2read == 0:
                payload = readahead
                readahead = b""
            elif more2read > 0:
                more_payload = intake.readexactly(more2read)
                payload = readahead + more_payload
                readahead = b""
            else:  # readahead contains more than this packet
                payload = readahead[:more2read]
                readahead = readahead[more2read:]
            yield dir_, payload

    # as end-of-stream can be signaled due to other reasons than end
    # of the intaking stream, here we iterate over the async generator
    # programmatically, along with frequent eos checks
    pkt_in = parse_pkts()
    try:
        while not eos.done():
            for f in asyncio.as_completed({eos, pkt_in.__anext__()}):
                if f is eos:
                    await eos  # reraise exception if that caused eos
                    return
                pkt = await f
                await pkt_sink(pkt)
                break
    except StopAsyncIteration:
        pass
