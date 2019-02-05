# CordieBot2
#
#  The CordieBot gets a new brain, using a Raspberry Pi instead of an Arduino.
#
#  Benefits:  Can do time and date
#             Can receive info over WIFI
#
#  Author: Hal Breidenbach
import board
import busio
import time
import RPi.GPIO as GPIO   # will this compete with board?
import adafruit_tlc59711
import os
from datetime import datetime
from TouchButton import TouchButton
from multiprocessing import *
import requests
import json
from random import *
import urllib.request
import feedparser

# from blinkateest set up SPI communication port    
spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)  # from blinkateest

# Define the TLC59711 instance to communicate with lights
leds = adafruit_tlc59711.TLC59711(spi)


'''
{'base': 'stations',
 'dt': 1548882960,
 'clouds': {'all': 1},
 'wind': {'speed': 10.3,
    'deg': 210,
    'gust': 13.9},
 'visibility': 16093,
 'name': 'Ann Arbor',
 'cod': 200,
 'weather': [{'icon': '50d',
    'id': 721,
    'description': 'haze',
    'main': 'Haze'}],
 'sys': {'sunrise': 1548852594,
    'country': 'US',
    'id': 3313,
    'message': 0.0044,
    'type': 1,
    'sunset': 1548888459},
 'id': 420018002,
 'coord': {'lat': 42.31,
    'lon': -83.78},
 'main': {'pressure': 1020,
    'temp_max': 253.75,
    'temp_min': 249.25,
    'temp': 251.64,
    'humidity': 51}}

'''

##################################################################################
#
#     "Constants"
#
##################################################################################

debug = True  # to print various details

button = 25  # GPIO number of touch sensor
# LED board uses SPIMOSI and SPISCLK
# Sound output uses 18

#print ("GPIO GPIO12 ", board.GPIO12)
GPIO.setmode(GPIO.BCM)

# define how many increments to use for ramping in the lightShow routine
rampVal = 64

request = TouchButton(button, 1.5)

with urllib.request.urlopen("https://geoip-db.com/json") as url:
    data = json.loads(url.read().decode())
    if debug:
        print(data)
    city = data["city"]
    state = data["state"]
    postal = data["postal"]
    if debug:
        print (city, ",", state, "  ", postal)


class Eyes:
    def open(self):
        ndx = 0
        while ndx < 32767:
            leds[1] = (0, ndx, ndx*2)
            leds[2] = (0, ndx, ndx*2)
            time.sleep(0.005)
            ndx += 128
    def close(self):
        ndx = 32767
        while ndx > 0:
            leds[1] = (0, ndx, ndx*2)
            leds[2] = (0, ndx, ndx*2)
            time.sleep(0.005)
            ndx -= 128
        self.clear()
    def clear(self):
        leds[1] = (0, 0, 0)
        leds[2] = (0, 0, 0)
        

class Lamp:
    def __init__(self, lightChannel):
        self.lightChannel = lightChannel
        self.r = 0    # r, g, and b values should be sent as 1/2 the desired brightness
        self.g = 0
        self.b = 0
        self.send()
    def set(self, inr, ing, inb):
        print ("set led = ", self.lightChannel, "  settings= ",
                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r = inr   # r, g, and b values should be sent as 1/2 the desired brightness
        self.g = ing
        self.b = inb
        self.send()
    def update(self, inr, ing, inb):
        print ("update led = ", self.lightChannel, "  settings= ",
                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r += inr
        self.g += ing
        self.b += inb
        self.send()
    def fadeOut(self, inr, ing, inb):
        print ("fadeOut led = ", self.lightChannel, "  settings= ",
                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r = self.r - inr
        self.g = self.g - ing
        self.b = self.b - inb
        self.send()
    def clear(self):
        self.r = 0 
        self.g = 0
        self.b = 0
        self.send()
    def rvalues(self):
        return self.r
    def gvalues(self):
        return self.g
    def bvalues(self):
        return self.b
    def send(self):
        leds[self.lightChannel] = (int(self.r)*2, int(self.g)*2, int(self.b)*2)

def info(title):
    if (debug):
        print (title)
        print ('module name:', __name__)
        if hasattr(os, 'getppid'):  # only available on Unix
            print ('parent process:', os.getppid())
        print ('process id:', os.getpid())
    

##################################################################################
#
#     lightShow()
#
#     Ramp head and brain lamps on to random colors.
#     Repeat 'count' times.
#     When done, fade to off.
#
##################################################################################

def lightShow(count):
    ceyes.open()
    
    rampDelay = 0.03
    headDeltas = [0,0,0]
    brainDeltas = [0,0,0]
    ndx = 0
    while ndx < count:
        getHue(headDeltas)
        getHue(brainDeltas)
        if debug:
            print ("ndx = ", ndx, " hues head & brain: ", headDeltas, brainDeltas)
        for x in range(rampVal):
            headLight.update(headDeltas[0], headDeltas[1], headDeltas[2])
            brainLight.update(brainDeltas[0], brainDeltas[1], brainDeltas[2])
            time.sleep(rampDelay)
            if debug and (x %10 == 0):
                print (x)
        headDeltas[0] = headLight.rvalues()
        headDeltas[1] = headLight.gvalues()
        headDeltas[2] = headLight.bvalues()
        brainDeltas[0] = brainLight.rvalues()
        brainDeltas[1] = brainLight.gvalues()
        brainDeltas[2] = brainLight.bvalues()
        if debug:
            print ("ndx = ", ndx, "  Head Deltas = ", headDeltas, "  Brain Deltas = ", brainDeltas)    
        ndx += 1
    headDeltas[:] = [-1*x/rampVal for x in headDeltas]
    brainDeltas[:] = [-1*x/rampVal for x in brainDeltas]
    if debug:
        print ("after get increments  Head Deltas = ", headDeltas, "  Brain Deltas = ", brainDeltas)    
    for x in range(rampVal):
        headLight.update(headDeltas[0], headDeltas[1], headDeltas[2])
        brainLight.update(brainDeltas[0], brainDeltas[1], brainDeltas[2])
        time.sleep(rampDelay)
        if debug and (x %10 == 0):
            print (x)
    headLight.clear()
    brainLight.clear()
    ceyes.close()

def getHue(hues):
    oldHues = hues
    if debug:
        print ("getHue start ", hues)
    skew = randint(0,2)
    alt = (skew + randint(1,2)) % 3
    newSkew = randint(0, 32767)
    newAlt = 32767 - newSkew
    if debug:
        print ("newSkew: ", newSkew,  "  newAlt: ", newAlt)
    hues[skew] = newSkew - oldHues[skew]
    if debug:
        print ("skew = ", skew, "  value = ", hues[skew])
    hues[alt] = newAlt - oldHues[alt]
    if debug:
        print ("alt = ", alt, "  value = ", hues[alt])
    ndx = [0, 1, 2]
    ndx.remove(skew)
    ndx.remove(alt)
    hues[ndx[0]] = (-1 * hues[ndx[0]])/rampVal
    hues[skew] = hues[skew]/rampVal
    hues[alt] = hues[alt]/rampVal
    if debug:
        print ("getHue ndx = ", ndx, "  hues[ndx] = ", hues[ndx[0]], "  hues = ", hues)

##################################################################################
#
#              Speaking roles ...
#
##################################################################################

def speak(phrase):
    info('function speak')
    if debug:
        print (phrase)
    os.system(phrase)
    
def doTime():
    date = datetime.now()
    timeStr = date.strftime("It is %I:%M %p on %A, %B %d")
    dateTxt = "aoss swift \"<prosody rate='-0.3'>" + timeStr + "\""
    if debug:
        print (dateTxt)
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(1,))
        ls.start()
        ps = Process(target=speak, args=(dateTxt,))
        ps.start()
        ps.join()
        ls.join()

def weatherDetails():
    with urllib.request.urlopen("https://geoip-db.com/json") as url:
        data = json.loads(url.read().decode())
        if debug:
            print(data)
        city = data["city"]
        state = data["state"]
        postal = data["postal"]
        if debug:
            print (city, ",", state, "  ", postal)
    getWeather = ("http://api.openweathermap.org/data/2.5/weather?zip=" +
            str(postal) + 
            ",US&units=imperial&APPID=654aba6d654a67d6b2917f37c410141f")
    with urllib.request.urlopen(getWeather) as url:
        data = json.loads(url.read().decode())
    if debug:
        print (data)
    temp = str(int(data["main"]["temp"])) + " degree"
    if not (temp[0:1] == "1 " or temp[0:2] == "-1 "):
        temp = temp + "s"
    condition = data["weather"][0]["description"] # extract weather description from
                                            # returned data.
    # substitute some phrases to make them more understandable or better English
    condition = condition.replace("sky","skies")
    condition = condition.replace("haze","hazey skies")
    condition = condition.replace("overcast","over cast")
    condition = condition.replace("thunderstorm","thunderstorms")
    weatherTxt = ("aoss swift \"<prosody rate='-0.3'>The temperature outside is " +
        temp + " with " +
        condition + "\"")
    speak(weatherTxt)


def doWeather():
    if debug:
        print ("getting weather")
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(3,))
        ls.start()
        ps = Process(target=weatherDetails)
        ps.start()
        ls.join()
        ps.join()                
        if debug:
            print ('%s.exitcode = %s' % (ps.name, ps.exitcode))
            print ('%s.exitcode = %s' % (ls.name, ls.exitcode))

def quoteDetails():
    data = feedparser.parse('https://www.brainyquote.com/link/quotebr.rss')
    quote = data['entries'][0]['summary_detail']['value']
    quote = quote[:-1]  # strip " off end
    quote = quote[1:]   # and front
    author = data['entries'][0]['title']
    quoteTxt = ("aoss swift \"<prosody rate='-0.5'>" + quote +
                 "<break strength='strong' />" + author + "\"")
    if debug:
        print (quoteTxt)
    speak(quoteTxt)

def doQuote():
    if debug:
        print ("getting quote")
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(4,))
        ls.start()
        ps = Process(target=quoteDetails)
        ps.start()
        ls.join()
        ps.join()                
 
##################################################################################
#
#              Initial on tests...
#
##################################################################################

def wakeUp():
    speak('aoss swift "Hi "')
    ceyes.open()
    ceyes.close()
    headLight.update(32767, 32767, 32767)
    brainLight.update(32767, 32767, 32767)
    time.sleep(1)
    headLight.clear()
    brainLight.clear()

##################################################################################
#
#              Main program...
#
##################################################################################

ceyes = Eyes()
headLight = Lamp(0)
brainLight = Lamp(3)
wakeUp() 

try:  
    while True:
        code = request.read()
        if (code != 0):
            if debug:
                print ("code:  ", code)
            if (code == 1):   #  date/time request
                doTime()
            if (code == 2):
                doWeather()
            if (code == 3):
                doQuote()
 
except KeyboardInterrupt:
    headLight.clear()
    brainLight.clear()
    ceyes.clear()  
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
    

headLight.clear()
brainLight.clear()
ceyes.clear()  
GPIO.cleanup() # this ensures a clean exit
  
print ("goodbye")

