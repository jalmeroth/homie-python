#!/usr/bin/env python
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = {
    "HOST": "test.mosquitto.org",
    "PORT": 1883,
    "KEEPALIVE": 10,
    "USERNAME": "",
    "PASSWORD": "",
    "CA_CERTS": "",
    "DEVICE_ID": "xxxxxxxx",
    "DEVICE_NAME": "xxxxxxxx",
    "TOPIC": "devices"
}

Homie = homie.Homie(config)
switchNode = Homie.Node("switch", "switch")


def switchOnHandler(mqttc, obj, msg):
    payload = msg.payload.decode("UTF-8").lower()
    if payload == 'true':
        logger.info("Switch: ON")
        Homie.setNodeProperty(switchNode, "on", "true", True)
    else:
        logger.info("Switch: OFF")
        Homie.setNodeProperty(switchNode, "on", "false", True)


def main():
    Homie.setFirmware("relay-switch", "1.0.0")
    Homie.subscribe(switchNode, "on", switchOnHandler)
    Homie.setup()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
