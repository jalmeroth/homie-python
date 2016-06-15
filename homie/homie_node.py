#!/usr/bin/env python
import logging
logger = logging.getLogger(__name__)


class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.nodeId = nodeId
        self.nodeType = nodeType


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
