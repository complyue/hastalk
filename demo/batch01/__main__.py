"""

this is an entry moduel to hook up some worker nodes from the swarm,
to accomplish the work defined in some module, with arbitrary overrides
possible from this module

it's a good idea to archive this file as part of the result data done by
the swarm, even version control them

don't put too much logic in this entry module, an entry module should just
like a comprehensive command line, don't program the command line, or you
are going to repeat yourself in duplicating works in such entry modules

"""

from typing import *
import asyncio

from hastalk import *

# work definition scripts are allowed to change the inferred
# configuration at `hastalk.sedh.senv`, import it as a namespace to
# always use up-to-date artifacts living there
import hastalk.sedh.senv as senv

# import reusable work definition from some module
import hastalk.demo.batch

# import the work module's effects as well
effect_import(hastalk.demo.batch)


logger = get_logger(__package__)


# hyper parameters
effect(
    dict(
        swarmIface="0.0.0.0",
        swarmAddr="127.0.0.1",
        swarmPort=3722,
        priority=0,
        headcount=3,
        cfwInterval=3,
    )
)


# ad-hoc parameter overrides
def m_range():
    for m in range(7, 9):
        yield m


asyncio.run(
    hastalk.demo.batch.manage_this_work(
        # what's specified here will override artifacts those samely named in
        # the reused work definition module's scope, they serve as lexical
        # default values to `manage_this_work()` defined there
        m_range=m_range,
    )
)

