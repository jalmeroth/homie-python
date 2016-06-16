#!/usr/bin/env python
import time
import socket
import logging
from homie.mqtt import HomieMqtt
from homie.timer import HomieTimer
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

    def mqttUptime(self):
        self.mqtt.publish(
            self.mqtt_topic + "/$uptime",
            payload=(time.time() - self.startTime), retain=True)

    def mqttSignal(self):
        self.mqtt.publish(
            self.mqtt_topic + "/$signal",
            payload=100, retain=True)

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
        self.mqtt.publish(
            self.mqtt_topic + "/$localip",
            payload=socket.gethostbyname(socket.gethostname()), retain=True)
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
