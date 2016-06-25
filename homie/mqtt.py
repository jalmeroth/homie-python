#!/usr/bin/env python
import logging
import paho.mqtt.client as paho_mqtt
logger = logging.getLogger(__name__)


class HomieMqtt(paho_mqtt.Client):
    """docstring for HomieMqtt"""

    def __init__(self, homieObj, deviceId, **kwargs):
        super(HomieMqtt, self).__init__(deviceId, **kwargs)

    def on_message(self, mqttc, obj, msg):
        logger.debug(
            " < " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_log(self, mqttc, obj, level, string):
        logger.debug("Log: " + str(string))

    def __del__(self):
        logger.debug("Quitting.")


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
