#!/usr/bin/env python
import logging
from homie.helpers import isIdFormat
logger = logging.getLogger(__name__)


class HomieNodeProperty(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, propertyId):
        super(HomieNodeProperty, self).__init__()
        self.node = node  # stores ref to node
        self._propertyId = None
        self.propertyId = propertyId
        self.handler = None
        self._settable = False

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.propertyId, handler)
        self._settable = True

    def send(self, value):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.propertyId,
            ]),
            value,
        )

    def representation(self):
        repr = self.propertyId
        if self._settable:
            repr += ":settable"
        return repr

    @property
    def propertyId(self):
        return self._propertyId

    @propertyId.setter
    def propertyId(self, propertyId):
        if isIdFormat(propertyId):
            self._propertyId = propertyId
        else:
            logger.warning("'{}' has no valid ID-Format".format(propertyId))


class HomieNodeRange(HomieNodeProperty):
    """docstring for HomieNodeRange"""

    def __init__(self, node, propertyId, lower, upper):
        super(HomieNodeRange, self).__init__(node, propertyId)
        self.node = node
        self._range = range(lower, upper + 1)
        self.range = None
        self.lower = lower
        self.upper = upper
        self.range_names = [(propertyId + "_" + str(x)) for x in self._range]

    def settable(self, handler):
        self.handler = handler
        for x in self._range:
            self.subscribe(self.node, "{}_{}".format(self.propertyId, x), handler)

    def setRange(self, lower, upper):
        # Todo: validate input
        if lower in self._range and upper in self._range:
            self.range = range(lower, upper + 1)
            return self
        else:
            logger.warning("Specified range out of announced range.")

    def send(self, value):
        if self.range is None:
            raise ValueError("Please specify a range.")

        for x in self.range:
            self.node.homie.publish(
                "/".join([
                    self.node.homie.baseTopic,
                    self.node.homie.deviceId,
                    self.node.nodeId,
                    self.propertyId + "_" + str(x),
                ]),
                value,
            )

    def representation(self):
        repr = "{}[{}-{}]".format(self.propertyId, self.lower, self.upper)
        if self._settable:
            repr += ":settable"
        return repr


class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, homie, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.homie = homie
        self.nodeId = nodeId
        self.nodeType = nodeType
        self.properties = {}

    def advertise(self, propertyId):
        if propertyId not in self.properties:
            homieNodeProperty = HomieNodeProperty(self, propertyId)
            homieNodeProperty.setSubscribe(self.homie.subscribe)
            if homieNodeProperty:
                self.properties[propertyId] = homieNodeProperty
                return(homieNodeProperty)
        else:
            logger.warning("Property '{}' already announced.".format(propertyId))

    def advertiseRange(self, propertyId, lower, upper):
        if propertyId not in self.properties:
            homieNodeRange = HomieNodeRange(self, propertyId, lower, upper)
            homieNodeRange.setSubscribe(self.homie.subscribe)
            if homieNodeRange:
                self.properties[propertyId] = homieNodeRange
                return(homieNodeRange)
        else:
            logger.warning("Property '{}' already announced.".format(propertyId))

    def setProperty(self, propertyId):
        if propertyId not in self.properties:
            raise ValueError("Property '{}' does not exist".format(propertyId))
        return self.properties[propertyId]

    def sendProperties(self):
        nodeTopic = "/".join([self.homie.baseTopic, self.homie.deviceId, self.nodeId])

        self.homie.publish(nodeTopic + "/$type", self.nodeType)

        payload = ",".join([property.representation() for id, property in self.properties.items()])
        self.homie.publish(nodeTopic + "/$properties", payload)

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
