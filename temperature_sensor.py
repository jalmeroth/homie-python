#!/usr/bin/env python
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPERATURE_INTERVAL = 3

Homie = homie.Homie(**homie.config)
temperatureNode = Homie.Node("temperature", "temperature")
humidityNode = Homie.Node("humidity", "humidity")


def main():
    Homie.setFirmware("awesome-temperature", "1.0.0")

    while True:
        time.sleep(TEMPERATURE_INTERVAL)
        temperature = 22.0
        humidity = 60.0

        logger.info("Temperature: {:0.2f} °C".format(temperature))
        Homie.setNodeProperty(temperatureNode, "degrees", temperature, True)

        logger.info("Humidity: {:0.2f} %".format(humidity))
        Homie.setNodeProperty(humidityNode, "humidity", humidity, True)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.warn("Quitting.")
