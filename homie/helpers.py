#!/usr/bin/env python
import re
import logging
from uuid import getnode as get_mac

logger = logging.getLogger(__name__)


def generateDeviceId():
    logger.debug("generateDeviceId")
    return "{:02x}".format(get_mac())


def isIdFormat(idString):
    logger.debug("isIdFormat")
    if isinstance(idString, str):
        r = re.compile('(^(?!\-)[a-z0-9\-]+(?<!\-)$)')
        return True if r.match(idString) else False


def main():
    pass


if __name__ == '__main__':
    main()
