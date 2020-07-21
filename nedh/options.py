"""
"""

__all__ = [
    "CONIN",
    "CONOUT",
    "CONMSG",
    "ERR_CHAN",
    "DATA_CHAN",
]


# conventional Nedh channels for console IO
CONIN, CONOUT, CONMSG = 0, 1, 2

# conventional Nedh channel for error reporting
ERR_CHAN = "err"

# conventional Nedh channel for data exchange
DATA_CHAN = "data"

