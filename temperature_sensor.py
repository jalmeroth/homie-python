#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPERATURE_INTERVAL = 3

Homie = homie.Homie("homie-python.json")
temperatureNode = Homie.Node("temperature", "temperature")
humidityNode = Homie.Node("humidity", "humidity")


def main():
    Homie.setFirmware("awesome-temperature", "1.0.0")
    temperatureNode.advertise("degrees", "float", "-273:1000",
                              "Temperature in Celsius", "°C")
    humidityNode.advertise("percentage", "float", "0:100", "Relative Humidity",
                           "%")
    Homie.setup()

    while True:
        temperature = 22.0
        humidity = 60.0

        logger.info("Temperature: {:0.2f} °C".format(temperature))
        temperatureNode.setProperty("degrees").send(temperature)

        logger.info("Humidity: {:0.2f} %".format(humidity))
        humidityNode.setProperty("percentage").send(humidity)


        time.sleep(TEMPERATURE_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
