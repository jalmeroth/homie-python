#!/usr/bin/env python
import json
import time
import socket
import atexit
import logging
import os.path
from os import getenv
from homie.mqtt import HomieMqtt
from homie.timer import HomieTimer
from homie.node import HomieNode
logger = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "CA_CERTS": {"key": "ca_certs", "val": None},
    "DEVICE_ID": {"key": "deviceId", "val": "xxxxxxxx"},
    "DEVICE_NAME": {"key": "deviceName", "val": "xxxxxxxx"},
    "HOST": {"key": "host", "val": None},
    "KEEPALIVE": {"key": "keepalive", "val": 60},
    "PASSWORD": {"key": "password", "val": None},
    "PORT": {"key": "port", "val": 1883},
    "PROTOCOL": {"key": "protocol", "val": None},
    "QOS": {"key": "qos", "val": 1},
    "TOPIC": {"key": "baseTopic", "val": "devices"},
    "USERNAME": {"key": "username", "val": None}
}


class Homie(object):
    """docstring for Homie"""

    def __init__(self, configFile):
        super(Homie, self).__init__()
        atexit.register(self.quit)
        self.initAttrs_(configFile)

        self.startTime = time.time()
        self.fwname = None
        self.fwversion = None
        self.nodes = []

        self.mqtt_topic = "/".join([
            self.baseTopic,
            self.deviceId,
        ])

        self.mqtt = HomieMqtt(self, self.deviceId, protocol=self.protocol)

        if not self.host:
            raise ValueError("No host specified.")

        self.mqttRun()

        self.uptimeTimer = HomieTimer(60, self.mqttUptime)
        self.signalTimer = HomieTimer(60, self.mqttSignal)
        self.uptimeTimer.start()
        self.signalTimer.start()

    def initAttrs_(self, configFile):
        """ Initialize homie attributes from env/config/defaults """

        # load configuration from configFile
        config = self.loadConfig(configFile)

        # iterate through DEFAULT_PREFS
        for pref in DEFAULT_PREFS:
            key = DEFAULT_PREFS[pref]['key']
            val = getenv(
                "HOMIE_" + pref,                # env
                config.get(
                    pref,                       # config
                    DEFAULT_PREFS[pref]['val']  # defaults
                )
            )

            # set attr self.key = val
            setattr(self, key, val)

            logger.debug("{}: {}".format(key, getattr(self, key)))

    def loadConfig(self, configFile):
        """ load configuration from configFile """
        config = {}
        configFile = os.path.realpath(configFile)
        try:
            fp = open(configFile)
        except EnvironmentError as e:
            logger.debug(e)
        else:
            try:
                config = json.load(fp)
            except Exception as e:
                raise e
            finally:
                fp.close()
        logger.debug("config: {}".format(config))
        return config

    def Node(self, *args):
        homeNode = HomieNode(*args)
        self.nodes.append(homeNode)
        return(homeNode)

    def setFirmware(self, name, version):
        """docstring for setFirmware"""
        self.fwname = name
        self.fwversion = version
        logger.debug("{}: {}".format(self.fwname, self.fwversion))

    def setNodeProperty(self, homieNode, prop, val, retain=True):
        topic = "/".join([
            self.mqtt_topic,
            homieNode.nodeId,
            prop
        ])
        self.publish(topic, payload=val, retain=retain)

    def publish(self, topic, payload, retain=True, **kwargs):
        """ Publish messages to MQTT, if connected """
        if self.mqtt.connected:
            msgs = [
                topic,
                str(payload),
                str(retain)
            ]

            (result, mid) = self.mqtt.publish(
                topic,
                payload=payload,
                retain=retain,
                **kwargs)

            logger.debug(str(mid) + " > " + " ".join(msgs))
        else:
            logger.warn("Not connected.")

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

        if self.username:
            self.mqtt.username_pw_set(self.username, password=self.password)

        if self.ca_certs:
            self.mqtt.tls_set(self.ca_certs)

        self.mqtt.connect(self.host, self.port, self.keepalive)
        self.mqtt.loop_start()

    def mqttNodes(self):
        payload = ",".join(
            [(str(x.nodeId) + ":" + str(x.nodeType)) for x in self.nodes])
        self.publish(
            self.mqtt_topic + "/$nodes",
            payload=payload, retain=True)

    def mqttLocalip(self):
        payload = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.host, self.port))
        except Exception as e:
            logger.warn(e)
        else:
            payload = s.getsockname()[0]
            s.close()

        self.publish(
            self.mqtt_topic + "/$localip",
            payload=payload, retain=True)

    def mqttUptime(self):
        payload = int(time.time() - self.startTime)
        self.publish(
            self.mqtt_topic + "/$uptime",
            payload=payload, retain=True)

    def mqttSignal(self):
        # default payload
        payload = 100

        # found on linux
        wireless = "/proc/net/wireless"

        try:
            fp = open(wireless)
        except EnvironmentError as e:
            logger.debug(e)
        else:
            for i, line in enumerate(fp):
                if i == 2:
                    data = line.split()
                    payload = int(float(data[2]))
                elif i > 2:
                    break
            fp.close()

        self.publish(
            self.mqtt_topic + "/$signal",
            payload=payload, retain=True)

    def mqttSetup(self):
        self.mqtt.subscribe(self.mqtt_topic + "/#", int(self.qos))
        self.publish(
            self.mqtt_topic + "/$online",
            payload="true", retain=True)
        self.publish(
            self.mqtt_topic + "/$name",
            payload=self.deviceName, retain=True)
        self.publish(
            self.mqtt_topic + "/$fwname",
            payload=self.fwname, retain=True)
        self.publish(
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

    def quit(self):
        self.uptimeTimer.cancel()
        self.signalTimer.cancel()
        self.publish(
            self.mqtt_topic + "/$online",
            payload="false", retain=True)
        self.mqtt.loop_stop()
        self.mqtt.disconnect()

    def __del__(self):
        logger.debug("Quitting.")


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
