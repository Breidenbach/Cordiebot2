# Cordiebot2
This bot was created from a brass lamp found in a resale store. Cordiebot 2 is a remake of the original Arduino version which was made as a present for my granddaughter's 11th birthday. The original Arduino version can be found in the repository: https://github.com/Breidenbach/CordieBot .

Note that the Cordiebot is a bot named after my granddaughter Cordie (duh).

The new and improved Cordiebot uses a Raspberry Pi model 3 A+ with logic written in Python 3.

This version uses logic similar to the original for the light show, but now has new features:
- Uses the Cepstral voice for better speach.
- Senses the number of times the touch switch is pressed in a short time:
  -  1 touch and Cordiebot says the time of day and date, possibly followed by a proclamation.
  -  2 touches and she says the current weather based on the location of the Cordiebot, possibly followed by a proclamation.
  -  3 touches and she says the quote for the day from BrainyQuote.com.
  -  8 touches and she tells her origin story.
  -  9 touches and she tells her internal temperature.
- Holding the button for more than 5 seconds causes a shutdown of the system, so that a reboot can occur.
- Check for a USB drive on start up, and when internet access is disrupted.  If the USB drive is found, check for a new wpa_supplicant.conf file or cordiebot2.py file.  If either file is found, copy it using special scripts to the appropriate directory. Thus this version has the capability of changing the WIFI name and password without a keyboard as well as updating the software.  It is expected that the USB drive will be removed during the reboot process.
- This version uses python multiprocessing to overlap the light show and speech.

PROCLAMATIONS

After the weather and time messages, the CordieBot will randomly make a proclamation drawn from a file of messages.  There are three types of proclamations:  for a specific date, for a specific month and day of any year, and for any date.  Proclamation examples:  "Today is mom's birthday" and "I am not the droid you are looking for".  The random selection is prioritized to most often select the current day's statements, followed by those that are for any year on the current date, followed by any other statements.

FILES

- The CordieBot application:
  - cordiebot2.py: the main script
  - CordieBot update scripts, executed when a USB drive is sensed:
    - cp_cordiebot2.sh: copies the cordiebot2.py file from a USB drive to the current directory
    - cp_wpa_conf.sh: copies the wpa_supplicant.conf file from a USB drive to /etc/wpa_supplicant/
    - testUSBmounted.py: script to test finding a USB drive.
  - TouchButton.py: class for the touch sensitive button.  Detectes the number of times the button is pressed with a short delay betwee presses, and if the button is pressed for more than five seconds.
  - pubnubpipe.py:  uses PubNub to communicate with the html app on home computer
  - runningAverage.py:  package to calculate a running average over a number of instances.
- Scripts to remotely update the proclamation file:
  - cbot_communication.html:  communicates from a host computer to the CordieBot to maintain the file of proclamations spoken after the time and weather.
  - Cbot_style.css:  style definitions used by cbot_communication.html
  - cbotspeechtest.py:  can be run on a local Raspberry Pi so that messages may be listened to prior to sending to the CordieBot.
- Support files:
  - createproclamationfile.py:  Used to create an initial list of statements for the CordieBot to recite.
  - keys.js:  container for the CordieBot PubNub keyes used for communication to the CordieBot.  This file is used in all the communication scripts:  pububpipe.py, cbotspeechtest.py, and cbot_communication.html.
