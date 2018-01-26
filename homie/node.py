#!/usr/bin/env python
import logging
from homie.helpers import isIdFormat
logger = logging.getLogger(__name__)


class HomieNodeProp(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, prop_id, datatype, val_format, name=None,
                 unit=None):
        super(HomieNodeProp, self).__init__()
        self.node = node  # stores ref to node
        self._prop_id = None
        self.prop_id = prop_id
        self.handler = None
        self._settable = False
        self.datatype = datatype
        self.format = val_format
        self.name = name or prop_id
        self.unit = unit

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.prop_id, handler)
        self._settable = True

    def send(self, val):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.prop_id,
            ]),
            val,
        )

    def send_attributes(self):
        topic = "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.prop_id,
            ])
        self.node.homie.publish(topic + "/$name", self.name)
        self.node.homie.publish(topic + "/$datatype", self.datatype)
        self.node.homie.publish(topic + "/$format", self.format)
        self.node.homie.publish(topic + "/$settable", self._settable)
        if self.unit:
            self.node.homie.publish(topic + "/$unit", self.unit)

    @property
    def prop_id(self):
        return self._prop_id

    @prop_id.setter
    def prop_id(self, prop_id):
        if isIdFormat(prop_id):
            self._prop_id = prop_id
        else:
            logger.warning("'{}' has no valid ID-Format".format(prop_id))


class HomeNodeRange(HomieNodeProp):
    """docstring for HomeNodeRange"""

    def __init__(self, node, prop_id, lower, upper, datatype, val_format,
                 names=[], unit=None):
        super(HomeNodeRange, self).__init__(node, prop_id, datatype, val_format,
                 None, unit)
        #self.node = node
        self._range = range(lower, upper + 1)
        self.range = None
        self.lower = lower
        self.upper = upper
        self.range_names = names or [(prop_id + "_" + str(x)) for x in self._range]

    def settable(self, handler):
        self.handler = handler
        for x in self._range:
            self.subscribe(self.node, self.prop_id+str(x), handler)

    def setRange(self, lower, upper):
        # Todo: validate input
        if lower in self._range and upper in self._range:
            self.range = range(lower, upper + 1)
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
                    self.prop_id + "_" + str(x),
                ]),
                val,
            )

    def send_attributes(self):
        for x in self._range:
            topic = "/".join([
                    self.node.homie.baseTopic,
                    self.node.homie.deviceId,
                    self.node.nodeId,
                    self.prop_id + "_" + str(x)
                ])
            self.node.homie.publish(topic + "/$name", self.range_names[x - min(self._range)])
            self.node.homie.publish(topic + "/$datatype", self.datatype)
            self.node.homie.publish(topic + "/$format", self.format)
            self.node.homie.publish(topic + "/$settable", self._settable)
            if self.unit:
                self.node.homie.publish(topic + "/$unit", self.unit)


class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, homie, nodeId, nodeType, name=None):
        super(HomieNode, self).__init__()
        self.homie = homie
        self.nodeId = nodeId
        self.nodeType = nodeType
<<<<<<< HEAD
        self.nodeProperties = []

    def addProperty(self, propId, settable=False):
        self.nodeProperties.append(propId + (":settable" if settable else ""))
        return self

    def nodeProperties(self):
        return self.nodeProperties
||||||| merged common ancestors
=======
        self.nodeName = name or nodeId
        self.props = {}

    def advertise(self, prop_id, datatype, val_format, name=None,
                  unit=None):
        if prop_id not in self.props:
            homeNodeProp = HomieNodeProp(self, prop_id, datatype, val_format,
                                         name, unit)
            homeNodeProp.setSubscribe(self.homie.subscribe)
            if homeNodeProp:
                self.props[prop_id] = homeNodeProp
                return(homeNodeProp)
        else:
            logger.warning("Property '{}' already announced.".format(prop_id))

    def advertiseRange(self, prop, lower, upper, datatype, val_format,
                       name=None, unit=None):
        if prop not in self.props:
            homeNodeRange = HomeNodeRange(self, prop, lower, upper, datatype,
                                          val_format, name, unit)
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

        return data

    def setProperty(self, prop):
        if prop not in self.props:
            raise ValueError("Property '{}' does not exist.".format(prop))
        return self.props[prop]

    def send_attributes(self):
        topic = "/".join([
                self.homie.baseTopic,
                self.homie.deviceId,
                self.nodeId,
            ])

        logger.debug("$name: {}:{}".format(self.nodeId, self.nodeName))
        self.homie.publish(topic + "/$name", self.nodeName)

        logger.debug("$type: {}:{}".format(self.nodeId, self.nodeType))
        self.homie.publish(topic + "/$type", self.nodeType)

        logger.debug("$properties: {}:{}".format(self.nodeId, self.getProperties()))
        self.homie.publish(topic + "/$properties", self.getProperties())

>>>>>>> dev

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

    @property
    def nodeName(self):
        return self._nodeName

    @nodeName.setter
    def nodeName(self, nodeName):
        self._nodeName = nodeName


def main():
    pass


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
