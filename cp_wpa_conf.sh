#!/bin/bash

# copy the wpa_supplicant.conf file to the system directory if it exists
if [ -f $1/wpa_supplicant.conf ]; then
   cp $1/wpa_supplicant.conf /etc/wpa_supplicant/
fi