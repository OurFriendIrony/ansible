#!/bin/bash

# Check if Ethernet interface is up
if ip link show eth0 | grep -q "state UP"; then
    # Ethernet is up, disable WiFi
    sudo ifconfig wlan0 down
else
    # Ethernet is down, enable WiFi
    sudo ifconfig wlan0 up
fi

