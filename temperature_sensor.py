#!/usr/bin/env python
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPERATURE_INTERVAL = 0.3

temperatureNode = homie.HomieNode("temperature", "temperature")


def main():
    Homie = homie.Homie(**homie.config)
    Homie.setFirmware("awesome-temperature", "1.0.0")

    while True:
        time.sleep(TEMPERATURE_INTERVAL)
        temperature = 22.0
        logger.info("Temperature: {:0.2f} °C".format(temperature))
        Homie.setNodeProperty(temperatureNode, "degrees", temperature, True)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.warn("Quitting.")
