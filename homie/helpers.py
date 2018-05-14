#!/usr/bin/env python
"""Provide helper functions."""
import re
import logging
from uuid import getnode as get_mac

logger = logging.getLogger(__name__)


def generateDeviceId():
    """Generate device Id."""
    logger.debug("generateDeviceId")
    return "{:02x}".format(get_mac())


def isIdFormat(idString):
    """Validate device Id."""
    logger.debug("isIdFormat")
    if isinstance(idString, str):
        r = re.compile('(^(?!\-)[a-z0-9\-]+(?<!\-)$)')
        return True if r.match(idString) else False
