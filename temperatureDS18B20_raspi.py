#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# DS18B20 1-wire temperature sensor
import time
import homie
import logging
import os
import glob
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

TEMPERATURE_INTERVAL = 60

config = homie.loadConfigFile("homie-python.json")
Homie = homie.Homie(config)
temperatureNode = Homie.Node("temperature", "temperature")

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        #temp_f = temp_c * 9.0 / 5.0 + 32.0 # uncomment this if you want fahrenheit and adjust variable in the line below
        return temp_c

def main():
    Homie.setFirmware("raspi-temperatureDS18B20", "1.0.0")
    temperatureNode.advertise("degrees")

    Homie.setup()

    while True:
        temperature = read_temp()
        logger.info("Temperature: {:0.2f} °C".format(temperature))
        temperatureNode.setProperty("degrees").send(temperature)
        time.sleep(TEMPERATURE_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
