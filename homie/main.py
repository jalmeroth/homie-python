#!/usr/bin/env python
import os
import time
import socket
import logging
from homie.mqtt import HomieMqtt
from homie.timer import HomieTimer
from homie.node import HomieNode
logger = logging.getLogger(__name__)


class Homie(object):
    """docstring for Homie"""

    def __init__(self, **kwargs):
        super(Homie, self).__init__()
        logger.debug("kwargs: {}".format(kwargs))
        self.startTime = time.time()
        self.fwname = None
        self.fwversion = None
        self.baseTopic = kwargs.get("TOPIC")
        self.deviceId = kwargs.get("DEVICE_ID")
        self.deviceName = kwargs.get("DEVICE_NAME")
        self.nodes = []

        self.mqtt_topic = "/".join([
            self.baseTopic,
            self.deviceId,
        ])

        self.mqtt = HomieMqtt(self, self.deviceId)
        self.host = kwargs.get("HOST")
        self.port = kwargs.get("PORT", 1883)
        self.keepalive = kwargs.get("KEEPALIVE", 60)

        if not self.host:
            raise ValueError("No host specified.")

        self.mqttRun()

        uptime = HomieTimer(60, self.mqttUptime)
        signal = HomieTimer(60, self.mqttSignal)
        uptime.start()
        signal.start()

    def on_set(self, mqttc, obj, msg):
        pass

    def on_reset(self, mqttc, obj, msg):
        pass

    def on_ota(self, mqttc, obj, msg):
        pass

    def Node(self, *args):
        homeNode = HomieNode(*args)
        self.nodes.append(homeNode)
        return(homeNode)

    def setFirmware(self, name, version):
        """docstring for setFirmware"""
        self.fwname = name
        self.fwversion = version
        logger.debug("{}: {}".format(self.fwname, self.fwversion))

    def setNodeProperty(self, homieNode, prop, val, retained=True):
        topic = "/".join([
            self.mqtt_topic,
            homieNode.nodeId,
            prop
        ])

        self.mqtt.publish(topic, payload=val, retain=retained)

        msgs = [
            topic,
            str(val),
            str(retained)
        ]
        logger.debug(" ".join(msgs))

    def subscribe(self, homieNode, attr, callback):
        subscription = "/".join(
            [
                self.mqtt_topic,
                homieNode.nodeId,
                attr,
                "set"
            ])

        logger.debug("subscribe: {}".format(subscription))

        self.mqtt.message_callback_add(
            subscription, callback)

    def mqttRun(self):
        self.mqtt.will_set(
            self.mqtt_topic + "/$online", payload="false", retain=True)
        self.mqtt.connect(self.host, self.port, self.keepalive)
        self.mqtt.loop_start()
        self.mqtt.subscribe(self.mqtt_topic + "/#", 0)

    def mqttNodes(self):
        payload = ",".join(
            [(str(x.nodeId) + ":" + str(x.nodeType)) for x in self.nodes])
        self.mqtt.publish(
            self.mqtt_topic + "/$nodes",
            payload=payload, retain=True)

    def mqttLocalip(self):
        payload = socket.gethostbyname(socket.gethostname())
        self.mqtt.publish(
            self.mqtt_topic + "/$localip",
            payload=payload, retain=True)

    def mqttUptime(self):
        payload = int(time.time() - self.startTime)
        self.mqtt.publish(
            self.mqtt_topic + "/$uptime",
            payload=payload, retain=True)

    def mqttSignal(self):
        # default payload
        payload = 100

        # found on linux
        wireless = "/proc/net/wireless"
        wireless = os.path.realpath(os.path.abspath(wireless))

        logger.debug("wireless: {} exists: {}".format(
            wireless,
            os.path.exists(wireless)))

        if os.path.exists(wireless):
            cmd = "cat %s | awk 'NR==3 {print $3}'" % wireless
            logger.debug("cmd: {}".format(cmd))

            qlink = os.popen(cmd).read().strip()
            if qlink:
                payload = int(float(qlink))
                logger.debug("qlink: {}".format(payload))

        self.mqtt.publish(
            self.mqtt_topic + "/$signal",
            payload=payload, retain=True)

    def mqttSetup(self):
        self.mqtt.publish(
            self.mqtt_topic + "/$online",
            payload="true", retain=True)
        self.mqtt.publish(
            self.mqtt_topic + "/$name",
            payload=self.deviceName, retain=True)
        self.mqtt.publish(
            self.mqtt_topic + "/$fwname",
            payload=self.fwname, retain=True)
        self.mqtt.publish(
            self.mqtt_topic + "/$fwversion",
            payload=self.fwversion, retain=True)
        self.mqttNodes()
        self.mqttLocalip()
        self.mqttUptime()
        self.mqttSignal()

    @property
    def baseTopic(self):
        return self._baseTopic

    @baseTopic.setter
    def baseTopic(self, baseTopic):
        self._baseTopic = baseTopic

    @property
    def deviceId(self):
        return self._deviceId

    @deviceId.setter
    def deviceId(self, deviceId):
        self._deviceId = deviceId


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
