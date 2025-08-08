"""Module defining callback types for menu interactions."""

import enum

class MenuCallBack(enum.IntEnum):
    """
    Enumeration of callback types used in menu interactions.

    Attributes:
        CALLBACK_STATUS_SHOW: Trigger to show the printer's current status.
        CALLBACK_CONNECTION_CHECK: Trigger to perform a connection check.
    """
    CALLBACK_STATUS_SHOW = 0
    CALLBACK_CONNECTION_CHECK = 1
