"""
Swarm batch work manager

"""
__all__ = [
    "manage_batch_jobs",
]

from typing import *
import asyncio

from ...edh import *
from ..headhunter import *
from ...log import *

logger = get_logger(__name__)


async def manage_batch_jobs(
    params: Callable[[], Iterable[Dict]], outlet: EventSink,
):
    hh = HeadHunter(outlet)
    hh.start_hunting()
    for ips in params():
        logger.debug(f"Dispatching job ips={ips!r}")
        await hh.dispatch_job(ips)
    logger.info("All jobs sent out.")
    await hh.finish_up()
    outlet.publish(EndOfStream)
