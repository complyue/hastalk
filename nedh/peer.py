"""
Peer

"""

import asyncio

from typing import *

from ..edh import *

from .mproto import *


__all__ = ["Peer"]


class Peer:
    def __init__(
        self,
        ident,
        posting: Callable[[Packet], Awaitable],
        hosting: Callable[[], Awaitable[Packet]],
        channels: Dict[Any, EventSink] = None,
    ):
        loop = asyncio.get_running_loop()
        # identity of peer
        self.ident = ident
        # end-of-life state
        self.eol = loop.create_future()
        # cmd outlet
        self.posting = posting
        # cmd intake
        self.hosting = hosting
        # cmd mux
        self.channels = channels or {}

    def __repr__(self):
        return f"Peer<{self.ident}>"

    async def join(self):
        await self.eol

    def stop(self):
        if not self.eol.done():
            self.eol.set_result(None)

    def armedChannel(self, chLctr: object) -> EventSink:
        return self.channels.get(chLctr, None)

    def armChannel(self, chLctr: object, chSink: Optional[EventSink]) -> EventSink:
        if chSink is None:
            chSink = EventSink()
        self.channels[chLctr] = chSink
        return chSink

    async def postCommand(self, src: str, dir_: str = ""):
        await self.posting(textPacket(dir_, src))

    async def p2c(self, dir_: str, src: str):
        await self.posting(textPacket(dir_, src))

    async def readCommand(self, cmdEnv=None) -> Optional[object]:
        """
        Read next command from peer

        Note a command may target a specific channel, thus get posted to that
             channel's sink, and None will be returned from here for it.
        """
        eol = self.eol
        pkt = await read_stream(eol, self.hosting())
        if pkt is EndOfStream:
            return EndOfStream
        assert isinstance(pkt, Packet), f"Unexpected packet of type: {type(pkt)!r}"
        if "err" == pkt.dir:
            exc = RuntimeError(pkt.payload.decode("utf-8"))
            if not eol.done():
                eol.set_exception(exc)
            raise exc
        if cmdEnv is None:
            # TODO way to obtain caller's global scope and default to that ?
            pass
        if pkt.dir.startswith("blob:"):
            blob_dir = pkt.dir[5:]
            if len(blob_dir) < 1:
                return pkt.payload
            chLctr = run_py(blob_dir, cmdEnv, self.ident)
            chSink = self.channels.get(chLctr, None)
            if chSink is None:
                raise RuntimeError(f"Missing command channel: {chLctr!r}")
            chSink.publish(pkt.payload)
            return None
        # interpret as textual command
        src = pkt.payload.decode("utf-8")
        try:
            cmdVal = run_py(src, cmdEnv, self.ident)
            if len(pkt.dir) < 1:
                return cmdVal
            chLctr = run_py(pkt.dir, cmdEnv, self.ident)
            chSink = self.channels.get(chLctr, None)
            if chSink is None:
                raise RuntimeError(f"Missing command channel: {chLctr!r}")
            chSink.publish(cmdVal)
            return None
        except Exception as exc:
            if not eol.done():
                eol.set_exception(exc)
            raise  # reraise as is


def run_py(code: str, globals_: dict = None, src_name="<py-code>") -> object:
    """
    Run arbitrary Python code in supplied globals, return evaluated value of last statement.

    """
    if globals_ is None:
        globals_ = {}
    try:
        ast_ = ast.parse(code, src_name, "exec")
        last_expr = None
        last_def_name = None
        for field_ in ast.iter_fields(ast_):
            if "body" != field_[0]:
                continue
            if len(field_[1]) > 0:
                le = field_[1][-1]
                if isinstance(le, ast.Expr):
                    last_expr = ast.Expression()
                    last_expr.body = field_[1].pop().value
                elif isinstance(le, (ast.FunctionDef, ast.ClassDef)):
                    last_def_name = le.name
        exec(compile(ast_, src_name, "exec"), globals_)
        if last_expr is not None:
            return eval(compile(last_expr, src_name, "eval"), globals_)
        elif last_def_name is not None:
            return globals_[last_def_name]
        return None
    except Exception:
        logger.error(
            f"""Error running Python code:
-=-{src_name}-=-
{code!s}
-=*{src_name}*=-
""",
            exc_info=True,
        )
        raise
