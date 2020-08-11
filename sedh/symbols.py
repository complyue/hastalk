"""
"""

__all__ = [
    "doOneJob",
    "shouldRetryJob",
]

from ..edh import *


# effect identifier for computation working out
doOneJob = Symbol("@doOneJob")

# effect identifier for job retry control on failure
# can be true/false or a callback procedure taking
# ( jobExc, ips ), and returning a new ips to retry
shouldRetryJob = Symbol("@shouldRetryJob")
