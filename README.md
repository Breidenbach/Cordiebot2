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
- Holding the button for more than 5 seconds causes a shutdown of the system, so that a reboot can occur.  This allows reloading the wpa_supplicant.conf file can be reloaded from a USB drive, allowing the Cordiebot to get a new WIFI password or WIFI source.
- This version uses python multiprocessing to overlap the light show and speech.
- Since the weather and quotes from BrainyQuote.com require access to the internet, presumably over WIFI, this version has the capability of changing the WIFI name and password without a keyboard.  This is done by putting a replacement wpa_supplicant.conf file on a USB drive and inserting it into the RaspberryPi in the CordieBot.  When the drive is detected, the wpa_supplicant.conf file on the drive is moved to the /etc/wpa_supplicant directory and the system is rebooted.  It is expected that the drive will be removed during the reboot process.
