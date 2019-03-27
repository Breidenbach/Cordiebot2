# Cordiebot2
This bot was created from a brass lamp found in a resale store. Cordiebot 2 is a remake of the original Arduino version which was made as a present for my granddaughter's 11th birthday. The original Arduino version can be found in the repository: Cordiebot.

Note that the Cordiebot is a bot named after my granddaughter Cordie (duh).

The new and improved Cordiebot uses a Raspberry Pi model 3 A+ with logic written in Python 3.

This version uses logic similar to the original for the light show, but now has new features:
- Uses the Cepstral voice for better speach.
- Senses the number of times the touch switch is pressed in a short time:
  -  1 touch and Cordiebot says the time of day and date.
  -  2 touches and she says the current weather based on the location of the Cordiebot.
  -  3 touches and she says the quote for the day from BrainyQuote.com.
  -  8 touches and she tells her origin story.
- Holding the button for more than 5 seconds causes a shutdown of the system, so that a reboot can occur.
- Check for a USB drive on start up, and when internet access is disrupted.  If the USB drive is found, check for a new wpa_supplicant.conf file or cordiebot2.py file.  If either file is found, copy it using special scripts to the appropriate directory. Thus this version has the capability of changing the WIFI name and password without a keyboard as well as updating the software.  It is expected that the USB drive will be removed during the reboot process.
- This version uses python multiprocessing to overlap the light show and speech.
