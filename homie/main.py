#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
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
        atexit.register(self._exitus)
        signal.signal(signal.SIGTERM, self._sigTerm)
        signal.signal(signal.SIGHUP, self._sigHup)

        self._initAttrs(configFile)
        if not self.host:
            raise ValueError("No host specified.")

        self.startTime = time.time()
        self.fwname = None
        self.fwversion = None
        self.nodes = []
        self.timers = []
        self.subscriptions = []
        self.subscribe_all_forced = False

        self.mqtt_topic = str("/".join([
            self.baseTopic,
            self.deviceId,
        ]))

        self._setupCalled = False
        self._mqtt_connected = False  # connected
        self._mqtt_subscribed = False  # subscribed
        clientId = "Homie-" + str(self.deviceId)

        try:
            self.mqtt = HomieMqtt(self, clientId, protocol=self.protocol)
        except Exception as e:
            raise e

    def Timer(self, *args):
        homieTimer = HomieTimer(*args)
        self.timers.append(homieTimer)
        return(homieTimer)

    def Node(self, *args):
        homeNode = HomieNode(*args)
        self.nodes.append(homeNode)
        return(homeNode)

    def _loadConfig(self, configFile):
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

    def _initAttrs(self, configFile):
        """ Initialize homie attributes from env/config/defaults """

        # load configuration from configFile
        config = self._loadConfig(configFile)

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

    def _checkBeforeSetup(self):
        """ checks whether setup() was called before """
        if self._setupCalled:
            raise BaseException(
                "✖ {}(): has to be called before setup()".format(
                    sys._getframe(1).f_code.co_name  # name of caller
                ))
        else:
            pass

    def _initialize(self):
        """ init and connect MQTT """
        # logger.debug("Initializing MQTT")
        self.mqtt.on_connect = self._connected
        self.mqtt.on_subscribe = self._subscribed
        self.mqtt.on_publish = self._published
        self.mqtt.on_disconnect = self._disconnected

        self.mqtt.will_set(
            self.mqtt_topic + "/$online", payload="false", retain=True)

        if self.username:
            self.mqtt.username_pw_set(self.username, password=self.password)

        if self.ca_certs:
            self.mqtt.tls_set(self.ca_certs)

        self.mqtt.connect(self.host, self.port, self.keepalive)
        self.mqtt.loop_start()

    def _subscribe(self):
        logger.debug("Subscriptions: {}".format(self.subscriptions))
        if self.subscriptions:
            self.mqtt.subscribe(self.subscriptions)
            if self.subscribe_all_forced and not self.subscribe_all:
                self._unsubscribe()
        else:
            self.mqtt.subscribe(self.mqtt_topic + "/#", int(self.qos))
            self.subscribe_all_forced = True

    def _unsubscribe(self, topic=None):
        if not topic:
            topic = self.mqtt_topic + "/#"
        logger.debug("_unsubscribe: {}".format(topic))
        self.mqtt.unsubscribe(str(topic))

    def _connected(self, *args):
        # logger.debug("_connected: {}".format(args))
        self.mqtt_connected = True

        if not self.mqtt_subscribed:
            self._subscribe()

        self.publish(
            self.mqtt_topic + "/$online",
            payload="true", retain=True)
        self.publish(
            self.mqtt_topic + "/$name",
            payload=self.deviceName, retain=True)

        self.publishFwname()
        self.publishFwversion()
        self.publishNodes()
        self.publishLocalip()
        self.publishUptime()
        self.publishSignal()

    def _subscribed(self, *args):
        # logger.debug("_subscribed: {}".format(args))
        if not self.mqtt_subscribed:
            self.mqtt_subscribed = True

    def _published(self, *args):
        # logger.debug("_published: {}".format(args))
        pass

    def _disconnected(self, mqtt, obj, rc):
        self.mqtt_connected = False
        self.mqtt_subscribed = False

    def setup(self):
        """ set homie up """
        self._setupCalled = True

        # init and connect MQTT
        self._initialize()

        self.uptimeTimer = self.Timer(60, self.publishUptime)
        self.signalTimer = self.Timer(60, self.publishSignal)
        self.uptimeTimer.start()
        self.signalTimer.start()

    def setFirmware(self, name, version):
        """docstring for setFirmware"""
        self._checkBeforeSetup()

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
        self._checkBeforeSetup()

        # user qos prefs
        if qos is None:
            qos = int(self.qos)

        subscription = str("/".join(
            [
                self.mqtt_topic,
                homieNode.nodeId,
                attr,
                "set"
            ]))

        logger.debug("subscribe: {} {}".format(subscription, qos))

        if not self.subscribe_all:
            self.subscriptions.append((subscription, qos))

        if self.mqtt_connected:
            self._subscribe()

        self.mqtt.message_callback_add(subscription, callback)

    def subscribeProperty(self, homieNode, attr, callback, qos=None):
        """ Register new subscription for property and add a callback """
        self._checkBeforeSetup()

        # user qos prefs
        if qos is None:
            qos = int(self.qos)

        subscription = str("/".join(
            [
                self.mqtt_topic,
                homieNode.nodeId,
                attr
            ]))

        logger.debug("subscribe: {} {}".format(subscription, qos))

        if not self.subscribe_all:
            self.subscriptions.append((subscription, qos))

        if self.mqtt_connected:
            self._subscribe()

        self.mqtt.message_callback_add(subscription, callback)

    def publish(self, topic, payload, retain=True, **kwargs):
        """ Publish messages to MQTT, if connected """
        if self.mqtt_connected:
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

    def publishFwname(self):
        """ Publish fwname of the script to MQTT """
        payload = str(self.fwname)
        if self.fwname:
            self.publish(
                self.mqtt_topic + "/$fwname",
                payload=payload, retain=True)

    def publishFwversion(self):
        """ Publish fwversion of the script to MQTT """
        payload = str(self.fwversion)
        if self.fwversion:
            self.publish(
                self.mqtt_topic + "/$fwversion",
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

    @property
    def mqtt_connected(self):
        return self._mqtt_connected

    @mqtt_connected.setter
    def mqtt_connected(self, state):
        logger.debug("connected: {}".format(state))
        self._mqtt_connected = state

    @property
    def mqtt_subscribed(self):
        return self._mqtt_subscribed

    @mqtt_subscribed.setter
    def mqtt_subscribed(self, state):
        logger.debug("subscribed: {}".format(state))
        self._mqtt_subscribed = state

    def _exitus(self):
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
