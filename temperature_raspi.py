#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPERATURE_INTERVAL = 60

Homie = homie.Homie("homie-python.json")
temperatureNode = Homie.Node("temperature", "temperature")


def getCpuTemperature():
    tempFile = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = tempFile.read()
    tempFile.close()
    return (float(cpu_temp) / 1000)


def main():
    Homie.setFirmware("raspi-temperature", "1.0.0")

    while True:
        temperature = getCpuTemperature()
        logger.info("Temperature: {:0.2f} °C".format(temperature))
        Homie.setNodeProperty(temperatureNode, "degrees", temperature, True)
        time.sleep(TEMPERATURE_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
