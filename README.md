# Cordiebot2
The new and improved Cordiebot using a Raspberry Pi model 3 A+ with logic written in Python 3

This version uses logic similar to the first for the light show, but now has new features:
- Uses the Cepstral voice for better speach
- Senses the number of times the touch switch is pressed in a short time
  -  1 touch and Cordiebot says the time of day and date
  -  2 touches and she says the current weather based on the location of the Cordiebot
  -  3 touches and she says the quote for the day from BrainyQuote.com
- This version uses python multiprocessing to overlap the light show and speech.
