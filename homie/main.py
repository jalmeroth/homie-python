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
    "HOST": None,
    "PORT": 1883,
    "KEEPALIVE": 60,
    "USERNAME": None,
    "PASSWORD": None,
    "CA_CERTS": None,
    "DEVICE_ID": "xxxxxxxx",
    "DEVICE_NAME": "xxxxxxxx",
    "TOPIC": "devices"
}


class Homie(object):
    """docstring for Homie"""

    def __init__(self, configFile):
        super(Homie, self).__init__()
        atexit.register(self.quit)
        self.config = self.loadConfig(configFile)
        logger.debug("config: {}".format(self.config))

        self.startTime = time.time()
        self.fwname = None
        self.fwversion = None
        self.baseTopic = self.config.get("TOPIC")
        self.deviceId = self.config.get("DEVICE_ID")
        self.deviceName = self.config.get("DEVICE_NAME")
        self.nodes = []

        self.mqtt_topic = "/".join([
            self.baseTopic,
            self.deviceId,
        ])

        self.mqtt = HomieMqtt(self, self.deviceId)
        self.host = self.config.get("HOST")
        self.port = self.config.get("PORT")
        self.keepalive = self.config.get("KEEPALIVE")
        self.username = self.config.get("USERNAME")
        self.password = self.config.get("PASSWORD")
        self.ca_certs = self.config.get("CA_CERTS")

        if not self.host:
            raise ValueError("No host specified.")

        self.mqttRun()

        self.uptimeTimer = HomieTimer(60, self.mqttUptime)
        self.signalTimer = HomieTimer(60, self.mqttSignal)
        self.uptimeTimer.start()
        self.signalTimer.start()

    def overwriteConfigFromEnv(self, config):
        for key in DEFAULT_PREFS:
            config[key] = getenv(
                "HOMIE_" + key,
                config.get(key, DEFAULT_PREFS[key]))
        return config

    def loadConfig(self, configFile):
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
        return self.overwriteConfigFromEnv(config)

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

        if self.username:
            self.mqtt.username_pw_set(self.username, password=self.password)

        if self.ca_certs:
            self.mqtt.tls_set(self.ca_certs)

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
        payload = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.host, self.port))
        except Exception as e:
            logger.warn(e)
        else:
            payload = s.getsockname()[0]
            s.close()

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

    def quit(self):
        self.uptimeTimer.cancel()
        self.signalTimer.cancel()
        self.mqtt.publish(
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
