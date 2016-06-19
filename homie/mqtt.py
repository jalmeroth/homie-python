#!/usr/bin/env python
import logging
import paho.mqtt.client as paho_mqtt
logger = logging.getLogger(__name__)


class HomieMqtt(paho_mqtt.Client):
    """docstring for HomieMqtt"""

    def __init__(self, homieObj, deviceId):
        super(HomieMqtt, self).__init__(deviceId)
        self._connected = False
        self._homieObj = homieObj

    def on_connect(self, mqttc, obj, flags, rc):
        self.connected = True
        self._homieObj.mqttSetup()

    def on_message(self, mqttc, obj, msg):
        logger.debug(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
        logger.debug("mid: " + str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        logger.debug("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_disconnect(self, mqttc, obj, rc):
        self.connected = False

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, state):
        logger.debug("connected: {}".format(state))
        self._connected = state

    def __del__(self):
        logger.debug("Quitting.")


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
