#!/usr/bin/env python
import logging
from homie.helpers import isIdFormat
logger = logging.getLogger(__name__)


class HomieNodeProp(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, prop):
        super(HomieNodeProp, self).__init__()
        self.node = node  # stores ref to node
        self._prop = None
        self.prop = prop
        self.handler = None

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.prop, handler)

    def send(self, val):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.prop,
            ]),
            val,
        )

    @property
    def prop(self):
        return self._prop

    @prop.setter
    def prop(self, prop):
        if isIdFormat(prop):
            self._prop = prop
        else:
            logger.warning("'{}' has no valid ID-Format".format(prop))


class HomeNodeRange(HomieNodeProp):
    """docstring for HomeNodeRange"""

    def __init__(self, node, prop, lower, upper):
        super(HomeNodeRange, self).__init__(node, prop)
        self.node = node
        self._range = range(lower, upper)
        self.range = None
        self.lower = lower
        self.upper = upper

    def settable(self, handler):
        self.handler = handler
        for x in self._range:
            self.subscribe(self.node, self.prop+str(x), handler)

    def setRange(self, lower, upper):
        # Todo: validate input
        if lower in self._range and upper in self._range:
            self.range = range(lower, upper)
            return self
        else:
            logger.warning("Specified range out of announced range.")

    def send(self, val):
        if self.range is None:
            raise ValueError("Please specify a range.")

        for x in self.range:
            self.node.homie.publish(
                "/".join([
                    self.node.homie.baseTopic,
                    self.node.homie.deviceId,
                    self.node.nodeId,
                    self.prop + str(x),
                ]),
                val,
            )


class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, homie, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.homie = homie
        self.nodeId = nodeId
        self.nodeType = nodeType
        self.props = {}

    def advertise(self, prop):
        if prop not in self.props:
            homeNodeProp = HomieNodeProp(self, prop)
            homeNodeProp.setSubscribe(self.homie.subscribe)
            if homeNodeProp:
                self.props[prop] = homeNodeProp
                return(homeNodeProp)
        else:
            logger.warning("Property '{}' already announced.".format(prop))

    def advertiseRange(self, prop, lower, upper):
        if prop not in self.props:
            homeNodeRange = HomeNodeRange(self, prop, lower, upper)
            homeNodeRange.setSubscribe(self.homie.subscribe)
            if homeNodeRange:
                self.props[prop] = homeNodeRange
                return(homeNodeRange)
        else:
            logger.warning("Property '{}' already announced.".format(prop))

    def getProperties(self):
        data = ""
        for k, v in self.props.items():

            if data:    # join by comma
                data += "," + k
            else:       # nothing to join
                data = k

            if isinstance(v, HomeNodeRange):
                data += "[{}-{}]".format(
                    v.lower,
                    v.upper,
                )

            if v.handler:
                data += ":settable"

        return data

    def setProperty(self, prop):
        if prop not in self.props:
            raise ValueError("Property '{}' does not exist.".format(prop))
        return self.props[prop]

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
