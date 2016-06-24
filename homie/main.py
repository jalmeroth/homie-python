#!/usr/bin/env python
import json
import time
import signal
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
    "SUBSCRIBE_ALL": {"key": "subscribe_all", "val": False},
    "TOPIC": {"key": "baseTopic", "val": "devices"},
    "USERNAME": {"key": "username", "val": None},
}


class Homie(object):
    """docstring for Homie"""

    def __init__(self, configFile):
        super(Homie, self).__init__()
        atexit.register(self.quit)
        signal.signal(signal.SIGTERM, self._sigTerm)
        signal.signal(signal.SIGHUP, self._sigHup)
        self.initAttrs_(configFile)

        self.startTime = time.time()
        self.fwname = None
        self.fwversion = None
        self.nodes = []
        self.timers = []
        self.subscriptions = []

        self.mqtt_topic = "/".join([
            self.baseTopic,
            self.deviceId,
        ])

        self.mqtt = HomieMqtt(self, self.deviceId, protocol=self.protocol)

        if not self.host:
            raise ValueError("No host specified.")

        self.mqttRun()

        self.uptimeTimer = self.Timer(60, self.publishUptime)
        self.signalTimer = self.Timer(60, self.publishSignal)
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

    def Timer(self, *args):
        homieTimer = HomieTimer(*args)
        self.timers.append(homieTimer)
        return(homieTimer)

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

    def subscribe(self, homieNode, attr, callback, qos=None):
        """ Register new subscription and add a callback """

        # user qos prefs
        if qos is None:
            qos = int(self.qos)

        subscription = "/".join(
            [
                self.mqtt_topic,
                homieNode.nodeId,
                attr,
                "set"
            ])

        logger.debug("subscribe: {} {}".format(subscription, qos))

        if not self.subscribe_all:
            self.subscriptions.append((subscription, qos))

        if self.mqtt.connected:
            self.mqtt.subscribe(self.subscriptions)

        self.mqtt.message_callback_add(subscription, callback)

    def mqttRun(self):
        self.mqtt.will_set(
            self.mqtt_topic + "/$online", payload="false", retain=True)

        if self.username:
            self.mqtt.username_pw_set(self.username, password=self.password)

        if self.ca_certs:
            self.mqtt.tls_set(self.ca_certs)

        self.mqtt.connect(self.host, self.port, self.keepalive)
        self.mqtt.loop_start()

    def mqttSetup(self):
        if self.subscribe_all:
            self.mqtt.subscribe(self.mqtt_topic + "/#", int(self.qos))
        else:
            self.mqtt.subscribe(self.subscriptions)

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

        self.publishNodes()
        self.publishLocalip()
        self.publishUptime()
        self.publishSignal()

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

    def publishNodes(self):
        """ Publish registered nodes to MQTT """
        payload = ",".join(
            [(str(x.nodeId) + ":" + str(x.nodeType)) for x in self.nodes])
        self.publish(
            self.mqtt_topic + "/$nodes",
            payload=payload, retain=True)

    def publishLocalip(self):
        """ Publish local IP Address to MQTT """
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

    def publishUptime(self):
        """ Publish uptime of the script to MQTT """
        payload = int(time.time() - self.startTime)
        self.publish(
            self.mqtt_topic + "/$uptime",
            payload=payload, retain=True)

    def publishSignal(self):
        """ Publish current signal strength to MQTT """
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
        """ Clean up before exit """

        # cancel all registered timers
        for timer in self.timers:
            timer.cancel()

        self.publish(
            self.mqtt_topic + "/$online",
            payload="false", retain=True)

        self.mqtt.loop_stop()
        self.mqtt.disconnect()

    def _sigTerm(self, signal, frame):
        """ let's do a quit, which atexit will notice """
        logger.debug("Received SIGTERM")
        raise SystemExit

    def _sigHup(self, signal, frame):
        """ let's do a quit, which atexit will notice """
        logger.debug("Received SIGHUP")
        raise SystemExit

    def __del__(self):
        logger.debug("Quitting.")


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
