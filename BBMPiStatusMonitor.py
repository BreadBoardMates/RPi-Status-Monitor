#!/usr/bin/python
# -*- coding: utf-8 -*-
# Dependencies:
## pip3 install psutil

import time
import sys
import psutil
import socket
import fcntl
import struct
import uptime
from gpiozero import CPUTemperature
from rpi_mates.controller import RPiMatesController as MatesController
from mates.constants import *

def up():
    t = uptime.uptime()
    days = 0
    hours = 0
    min = 0
    out = ''
    while t > 86400:
        t -= 86400
        days += 1
    while t > 3600:
        t -= 3600
        hours += 1
    while t > 60:
        t -= 60
        min += 1
    out += str(days) + 'd '
    out += str(hours) + 'h '
    out += str(min) + 'm'
    return out


def get_interface_ipaddress(network):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,
                                struct.pack('256s',
                                network[:15].encode('utf-8')))[20:24])  # SIOCGIFADDR
    except OSError:
        return '0.0.0.0'

def get_rpi_model():
    model = "Unknown Raspberry Pi Model"
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Model"):
                    model = line.split(":")[1].strip()
                    break
    except FileNotFoundError:
        model="Could not determine Raspberry Pi model (no /proc/cpuinfo found)"
    except Exception as e:
        model = f"An error occured: (e)"

    return model 


if __name__ == '__main__':

    rpi_model = get_rpi_model()

    if "Pi 5" in rpi_model:
        mates = MatesController('/dev/ttyAMA0')
    else:
        mates = MatesController('/dev/serial0')

    mates.begin(115200)
    print("===========================")
    print(rpi_model, ": TIMI-130 Status Monitor")
    print("Press CTRL + C to exit.")

    gtime = up()
    lastCpuUse = 0
    lastTemp = 0
    lastlTemp = 0
    lastRamUse = 0
    lastWIPaddr = '0.0.0.0'
    lastEIPaddr = '0.0.0.0'

    mates.updateTextArea(5, gtime, True)
    cpu = CPUTemperature()
    lastlTemp = int(cpu.temperature * 10)

    IPinterval = 0
    
    while True:
        cpu = CPUTemperature()
        gcpu = int(cpu.temperature)
        lcpu = int(cpu.temperature * 10)
        cpuuse = int(psutil.cpu_percent())
        ramuse = int(psutil.virtual_memory().percent)

        if cpuuse < lastCpuUse:
            lastCpuUse = lastCpuUse - (1 + (lastCpuUse - cpuuse > 9))
        if cpuuse > lastCpuUse:
            lastCpuUse = lastCpuUse + 1 + (cpuuse - lastCpuUse > 9)
        if gcpu < lastTemp:
            lastTemp = lastTemp - (1 + (lastTemp - gcpu > 9))
        if gcpu > lastTemp:
            lastTemp = lastTemp + 1 + (gcpu - lastTemp > 9)
        if lcpu < lastlTemp:
            lastlTemp = lastlTemp - 1
        if lcpu > lastlTemp:
            lastlTemp = lastlTemp + 1
        if ramuse < lastRamUse:
            lastRamUse = lastRamUse - (1 + (lastRamUse - ramuse > 9))
        if ramuse > lastRamUse:
            lastRamUse = lastRamUse + 1 + (ramuse - lastRamUse > 9)

        if gcpu != lastTemp:
            mates.setWidgetValueByIndex(MatesWidget.MATES_MEDIA_GAUGE_B,0, lastTemp)
        if lcpu != lastlTemp:
            mates.setLedDigitsShortValue(0, lastlTemp)
        if cpuuse != lastCpuUse:
            mates.setWidgetValueByIndex(MatesWidget.MATES_MEDIA_GAUGE_B,1, lastCpuUse)
            mates.setLedDigitsShortValue(1, lastCpuUse)
        if ramuse != lastRamUse:
            mates.setWidgetValueByIndex(MatesWidget.MATES_MEDIA_GAUGE_B,2, lastRamUse)
            mates.setLedDigitsShortValue(2, lastRamUse)

        if IPinterval > 20:
            tempIPaddr = get_interface_ipaddress('eth0')
            if tempIPaddr != lastEIPaddr:
                mates.updateTextArea(1, tempIPaddr, True)
                lastEIPaddr = tempIPaddr

            tempIPaddr = get_interface_ipaddress('wlan0')
            if tempIPaddr != lastWIPaddr:
                mates.updateTextArea(3, tempIPaddr, True)
                lastWIPaddr = tempIPaddr
            IPinterval = 0

        IPinterval = IPinterval + 1
        time.sleep(0.060)

        tempTime = up()
        if tempTime != gtime:
            mates.updateTextArea(5, tempTime, True)
            gtime = tempTime
        time.sleep(0.040)
    
