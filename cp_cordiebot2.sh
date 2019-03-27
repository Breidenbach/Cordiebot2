#!/bin/bash

# copy the cordiebot2.py file to the current directory if it exists
if [ -f $1/cordiebot2.py ]; then
   cp $1/cordiebot2.py .
fi