#!/usr/bin/env python
import logging
import paho.mqtt.client as paho_mqtt
logger = logging.getLogger(__name__)


class HomieMqtt(paho_mqtt.Client):
    """docstring for HomieMqtt"""

    def __init__(self, homieObj, clientId):
        super(HomieMqtt, self).__init__(clientId)
        self._connected = False
        self._homieObj = homieObj

    def on_connect(self, mqttc, obj, flags, rc):
        self.connected = True
        self._homieObj.mqttSetup()

    def on_message(self, mqttc, obj, msg):
        logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
        logger.info("mid: " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_disconnect(self, mqttc, obj, rc):
        self.connected = False

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, state):
        logger.info("connected: {}".format(state))
        self._connected = state


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
