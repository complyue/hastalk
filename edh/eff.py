__all__ = ["Symbol", "effect"]
from typing import *
import asyncio
import inspect

from ..log import *

logger = get_logger(__name__)


class Symbol:
    __slots__ = ("repr",)

    def __init__(self, repr_: str):
        self.repr = repr_

    def __repr__(self):
        return self.repr

    __str__ = __repr__


def effect(key2get_or_dict2put: Optional[Union[dict, object]] = None, **kws2put):
    EFFSKEY = "__effects__"  # this better be a local than global

    if isinstance(key2get_or_dict2put, dict):
        key2get = None
        dict2put = key2get_or_dict2put
    else:
        key2get = key2get_or_dict2put
        dict2put = None

    coro_task = None
    try:
        coro_task = asyncio.current_task()
    except:
        pass
    if coro_task is None:
        # no asynchronous context, definitely called by synchronous code

        frame = inspect.currentframe().f_back
        scope = frame.f_locals
        if kws2put or dict2put:
            effs = scope.get(EFFSKEY, None)
            if effs is None:
                effs = {}
                scope[EFFSKEY] = effs
            if dict2put:
                effs.update(dict2put)
            if kws2put:
                effs.update(kws2put)

        if key2get is None:
            return None
        while True:
            effs = scope.get(EFFSKEY, None)
            if effs is not None:
                art = effs.get(key2get, effs)
                if art is not effs:
                    return art
            frame = frame.f_back
            if frame is None:
                raise ValueError(f"No such effect: {key2get!r}")
            scope = frame.f_locals

    else:  # asynchronous context involved

        # handling asynchronous effects here so far,
        # but maybe synchronous code called by async code is calling this,
        # while it's the sychronous code meant to resolve sync effects,
        # TODO think about it and figure out how to detect the cases and handle
        # them respectively
        async_stack = coro_task.get_stack()
        if async_stack is None:
            assert False, "this possible?"
            return None
        # this function is not a coroutine, so the top is already caller frame
        frame = async_stack[-1]
        scope = frame.f_locals
        if kws2put or dict2put:
            effs = scope.get(EFFSKEY, None)
            if effs is None:
                effs = {}
                scope[EFFSKEY] = effs
            if dict2put:
                effs.update(dict2put)
            if kws2put:
                effs.update(kws2put)

        if key2get is None:
            return None

        for frame in reversed(async_stack):
            scope = frame.f_locals
            effs = scope.get(EFFSKEY, None)
            if effs is not None:
                art = effs.get(key2get, effs)
                if art is not effs:
                    return art

        raise ValueError(f"No such async effect: {key2get!r}")
