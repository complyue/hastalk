__all__ = ["effect"]
import asyncio
import inspect


def effect(get_key=None, **put_pairs):
    EFFSKEY = "__effects__"  # this better be a local than global

    coro_task = None
    try:
        coro_task = asyncio.current_task()
    except:
        pass
    if coro_task is None:
        # no asynchronous context, definitely called by synchronous code

        frame = inspect.currentframe().f_back
        scope = frame.f_locals
        if put_pairs:
            effs = scope.get(EFFSKEY, None)
            if effs is None:
                effs = {}
                scope[EFFSKEY] = effs
            effs.update(put_pairs)

        if get_key is None:
            return None
        while True:
            effs = scope.get(EFFSKEY, None)
            if effs is not None:
                art = effs.get(get_key, effs)
                if art is not effs:
                    return art
            frame = frame.f_back
            if frame is None:
                return None
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
        if put_pairs:
            effs = scope.get(EFFSKEY, None)
            if effs is None:
                effs = {}
                scope[EFFSKEY] = effs
            effs.update(put_pairs)

        if get_key is None:
            return None

        for frame in reverse(async_stack):
            scope = frame.f_locals
            art = scope.get(get_key, scope)
            if art is not scope:
                return art

        return None
