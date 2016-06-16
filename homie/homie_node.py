#!/usr/bin/env python
import logging
logger = logging.getLogger(__name__)


class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.nodeId = nodeId
        self.nodeType = nodeType

    @property
    def nodeId(self):
        return self._nodeId

    @nodeId.setter
    def nodeId(self, nodeId):
        self._nodeId = nodeId

    @property
    def nodeType(self):
        return self._nodeType

    @nodeType.setter
    def nodeType(self, nodeType):
        self._nodeType = nodeType


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
