"""
Peer

"""

import asyncio

from typing import *

from ..edh import *


__all__ = ["CommCmd", "Peer"]


class CommCmd:
    __slots__ = ("dir", "src")

    def __init__(dir_: str, self, src: str):
        self.dir = dir_
        self.src = src

    def __repr__(self):
        return f"CommCmd({self.dir!r},{self.src!r})"


class Peer:
    def __init__(
        self,
        ident,
        posting: Callable[[CommCmd], Awaitable[None]],
        hosting: Callable[[], Awaitable[CommCmd]],
        channels: Dict[Any, EventSink] = {},
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
        self.channels = channels

    def __repr__(self):
        return f"Peer<{self.ident}>"

    async def postCommand(self, src: str, dir_: str = ""):
        await self.posting(CommCmd(src, dir_))

    async def p2c(self, dir_: str, src: str):
        await self.posting(CommCmd(src, dir_))

    async def readCommand(self, cmdEnv=None):
        """
        Read next command from peer

        Note a command may target a specific channel, thus get posted to that
             channel's sink, and None will be returned from here for it.
        """
        f = await asyncio.as_completed((self.eol, self.hosting()))
        if self.eol.done():
            await self.eol  # reraise exception if that caused eol
            return EndOfStream
        cmd = await f
        assert isinstance(cmd, CommCmd), f"Unexpected cmd of type: {type(cmd)!r}"
        if "err" == cmd.dir:
            exc = RuntimeError(cmd.src)
            if not self.eol.done():
                self.eol.set_exception(exc)
            raise exc
        if cmdEnv is None:
            # TODO way to obtain caller's global scope and default to that ?
            cmdEnv = globals()
        try:
            cmdVal = run_py(cmd.src, cmdEnv, self.ident)
            if len(cmd.dir) < 1:
                return cmdVal
            chLctr = run_py(cmd.dir, cmdEnv, self.ident)
            chSink = self.channels.get(chLctr, None)
            if chSink is None:
                raise RuntimeError(f"Missing command channel: {chLctr!r}")
            chSink.publish(cmdVal)
            return None
        except Exception as exc:
            if not self.eol.done():
                self.eol.set_exception(exc)
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
