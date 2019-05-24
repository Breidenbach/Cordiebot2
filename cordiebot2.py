##################################################################################
#
# CordieBot2  Ver. 2.00
#
#  The CordieBot gets a new brain, using a Raspberry Pi instead of an Arduino.
#
#  Benefits:  Can receive info over WIFI
#
#  Actions:     States time and date (switch pressed 1 time)
#               Retrieves and states current weather conditions (switch pressed 2 times)
#               Retrieves and states quote of the day from BrainyQuote.com (switch
#                   pressed 3 times)
#               Shuts down the system so it can be safely powered off (switch press
#                   for more than 5 seconds)
#
#  Author: Hal Breidenbach
#
##################################################################################
#
#     Imports
#
##################################################################################

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
import socket
import subprocess

##################################################################################
#
#     "Constants"
#
##################################################################################

debug = True            # to print various details
debugLights = False     # help debugging light show
debugTalk = False       # help debug speaking

button = 25  # GPIO number of touch sensor
#              LED board uses SPIMOSI and SPISCLK
#              Sound output uses 18

ampEnable = 21  # GPIO number to enable the amplifier board
#                 when low, amp is disabled

# define how many increments to use for ramping in the lightShow routine
rampVal = 64

##################################################################################
#
#     I/O setup
#
##################################################################################

GPIO.setmode(GPIO.BCM)

# from blinkateest set up SPI communication port    
spi = busio.SPI(board.SCLK, board.MOSI, board.MISO)  # from blinkateest

# Define the TLC59711 instance to communicate with lights
leds = adafruit_tlc59711.TLC59711(spi)

GPIO.setup(ampEnable, GPIO.OUT, initial=GPIO.LOW)

##################################################################################
#
#     Function definitions
#
##################################################################################

def info(title):
    if (debug):
        print (title)
        print ('module name:', __name__)
        if hasattr(os, 'getppid'):  # only available on Unix
            print ('parent process:', os.getppid())
        print ('process id:', os.getpid())
    
def speak(phrase):
    info('function speak')
    if debug:
        print (phrase)
    GPIO.output(ampEnable, GPIO.HIGH)
    os.system(phrase)
    GPIO.output(ampEnable, GPIO.LOW)
    
def internet():
    return (os.system("ping -c 1 8.8.8.8") == 0)

def findCordiebotUSB():
    # file handle fh
    inLine = ""
    fh = open('/proc/mounts')
    while True:
        # read line
        line = fh.readline()
        # in python 2, print line
        # in python 3
        if "CORDIEBOT" in line:
            inLine = line
            break
        # check if line is not empty
        if not line:
            break
    fh.close()
    return inLine
    
noNetworkTxt = ("aoss swift \"I don't appear to be connected to a why fi network.\"" )

def informNoNetwork():
    speak(noNetworkTxt)

# check for wpa_supplicant.conf file repacement
#   If file is present, it is moved to /etc/wpa_supplicant/ and can be used
#   to find a new wifi network or change the password of an existing network.
#   Note that the system must be restarted to use the new wpa_supplicant.conf 
#   file.

wpa_supplicant_txt = ("aoss swift \"I have found a new why fi name and " +
                "password file.  I will start using that file now.\"" )
                
cordiebot2_txt = ("aoss swift \"I have found a new cordee bot2 file. " +
                "I will start using that file now.\"" )
                
shutdown_txt =  ( "aoss swift \"I need to restart which will take several seconds." + 
                "  Be sure to remove the USB drive while I am restarting.\"")

checkNetworkTxt = ("aoss swift \" Check if your why fi is running. Check if anyone changed " +
                "the password.  Otherwise, grampa might be able to help.\"")

def checkForConf(starting):
    CBLine = findCordiebotUSB()
    if CBLine == "":
        if starting == False:
            if debug:
                print ("not in view")
            speak(checkNetworkTxt)
        # else, no action
    else:
        if debug:
            print (CBLine)
        firstSpace = CBLine.find(' ')
        secondSpace = CBLine.find(' ', firstSpace + 1)
        dirSpec = CBLine[int(firstSpace + 1):int(secondSpace)]
        if debug:
            print (dirSpec)
    
        files = os. listdir(dirSpec)
        shutdown = False
        for name in files:
            if (name == "wpa_supplicant.conf"):
                if debug:
                    print ("found file ", name, " and copying it.")
                speak(wpa_supplicant_txt)
                p = subprocess.Popen("sudo /home/pi/CordieBot2/cp_wpa_conf.sh "+dirSpec,
                            shell=True)
                p.communicate()  # this waits for completion of the copy
                shutdown = True
            if (name == "cordiebot2.py"):
                if debug:
                    print ("found file ", name, "and copying it.")
                speak(cordiebot2_txt)
                p = subprocess.Popen("/home/pi/CordieBot2/cp_cordiebot2.sh "+dirSpec,
                            shell=True)
                p.communicate()  # this waits for completion of the copy
                shutdown = True
        if (shutdown == True):
            speak(shutdown_txt)
            os.system("shutdown -r now")

def doPubNub():
    os.system('python pubnubpipe.py')


##################################################################################
#
#     Class definitions
#
##################################################################################

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
        if debugLights:
            print ("set led = ", self.lightChannel, "  settings= ",
                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r = inr   # r, g, and b values should be sent as 1/2 the desired brightness
        self.g = ing
        self.b = inb
        self.send()
    def update(self, inr, ing, inb):
        if debugLights:
            print ("update led = ", self.lightChannel, "  settings= ",
                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r += inr
        self.g += ing
        self.b += inb
        self.send()
    def fadeOut(self, inr, ing, inb):
        if debugLights:
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

##################################################################################
#
#     Start up activity
#
##################################################################################


#  Routine to check for updates to the wpa_supplicant.conf or cordiebot2.py files,
#  and test internet access.
                        
checkForConf(True)

if internet():
    with urllib.request.urlopen("https://geoip-db.com/json") as url:
        data = json.loads(url.read().decode())
        if debug:
            print(data)
        city = data["city"]
        state = data["state"]
        postal = data["postal"]
        if debug:
            print (city, ",", state, "  ", postal)
else:
    informNoNetwork()
    checkForConf(False)

##################################################################################
#
#     Process Proclamations file 
#
##################################################################################


class manage_p_file:
    def __init__(self, file_in_memory):
        with open('proclamations.txt') as p_file:  
            p_data = json.load(p_file)
        self.file_in_memory = true
    def add_entry(message):
        with open('proclamations.txt', 'w') as p_file:  
            json.dump(p_data, p_file)
    def change_entry(message):
        with open('proclamations.txt', 'w') as p_file:  
            json.dump(p_data, p_file)
    def delete_entry(message):
        with open('proclamations.txt', 'w') as p_file:  
            json.dump(p_data, p_file)
    def return_entry(message):
        pass
    def return_next_entry(message):
        pass
    def return_by_date(message):
        pass
    def return_next_by_date(message):
        pass
    def resequence():
        with open('proclamations.txt', 'w') as p_file:  
            json.dump(p_data, p_file)
            
            
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
            if debugLights and (x %10 == 0):
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
    if debugLights:
        print ("after get increments  Head Deltas = ", headDeltas, "  Brain Deltas = ", brainDeltas)    
    for x in range(rampVal):
        headLight.update(headDeltas[0], headDeltas[1], headDeltas[2])
        brainLight.update(brainDeltas[0], brainDeltas[1], brainDeltas[2])
        time.sleep(rampDelay)
        if debugLights and (x %10 == 0):
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
    if debugLights:
        print ("newSkew: ", newSkew,  "  newAlt: ", newAlt)
    hues[skew] = newSkew - oldHues[skew]
    if debugLights:
        print ("skew = ", skew, "  value = ", hues[skew])
    hues[alt] = newAlt - oldHues[alt]
    if debugLights:
        print ("alt = ", alt, "  value = ", hues[alt])
    ndx = [0, 1, 2]
    ndx.remove(skew)
    ndx.remove(alt)
    hues[ndx[0]] = (-1 * hues[ndx[0]])/rampVal
    hues[skew] = hues[skew]/rampVal
    hues[alt] = hues[alt]/rampVal
    if debugLights:
        print ("getHue ndx = ", ndx, "  hues[ndx] = ", hues[ndx[0]], "  hues = ", hues)

##################################################################################
#
#              Speaking roles ...
#
##################################################################################

def doTime():
    date = datetime.now()
    timeStr = date.strftime("It is %I:%M %p on %A, %B %d")
    dateTxt = "aoss swift \"<prosody rate='-0.3'>" + timeStr + "\""
    if debugTalk:
        print (dateTxt)
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(2,))
        ls.start()
        ps = Process(target=speak, args=(dateTxt,))
        ps.start()
        ps.join()
        ls.join()

def weatherDetails():
    if internet():
        with urllib.request.urlopen("https://geoip-db.com/json") as url:
            data = json.loads(url.read().decode())
            if debugTalk:
                print(data)
            city = data["city"]
            state = data["state"]
            postal = data["postal"]
            if debugTalk:
                print (city, ",", state, "  ", postal)
        getWeather = ("http://api.openweathermap.org/data/2.5/weather?zip=" +
                str(postal) + 
                ",US&units=imperial&APPID=654aba6d654a67d6b2917f37c410141f")
        with urllib.request.urlopen(getWeather) as url:
            data = json.loads(url.read().decode())
        if debugTalk:
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
    else:
        informNoNetwork()
        checkForConf(False)

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
    if internet():
        data = feedparser.parse('https://www.brainyquote.com/link/quotebr.rss')
        quote = data['entries'][0]['summary_detail']['value']
        quote = quote[:-1]  # strip " off end
        quote = quote[1:]   # and front
        author = data['entries'][0]['title']
        quoteTxt = ("aoss swift \"<prosody rate='-0.3'>" + quote +
                     "<break strength='strong' />" + author + "\"")
        if debugTalk:
            print (quoteTxt)
        speak(quoteTxt)
    else:
        informNoNetwork()
        checkForConf(False)
        
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

def originsDetails():
    originsTxt = (  "aoss swift \"<prosody rate='-0.3'>I am Cordeebot." + 
                    "<break strength='strong' />" +
                    "I was made by Grampa in 20 16 for Cordies 11th birthday." +
                    "<break strength='strong' />" +
                    "In 20 19 Grampa gave me a new brain." +
                    "<break strength='strong' />" +                    
                    "I feel much smarter now.\"")
    if debugTalk:
        print (originsTxt)
    speak(originsTxt)
                        
def doOrigins():
    if debug:
        print ("getting origins")
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(6,))
        ls.start()
        ps = Process(target=originsDetails)
        ps.start()
        ls.join()
        ps.join()
        
                
 
##################################################################################
#
#              Initial on tests...
#
##################################################################################

def wakeUp():
    speak('aoss swift "I am version 2.00"')
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


if __name__ == '__main__':
    request = TouchButton(button, 1.5)
    ceyes = Eyes()
    headLight = Lamp(0)
    brainLight = Lamp(3)
    wakeUp()
    pn = Process(target=doPubNub)
    pn.start()

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
                if (code == 8):
                    doOrigins()
                if (code == 255):
                    headLight.clear()
                    brainLight.clear()
                    ceyes.clear()  
                    GPIO.cleanup() # this ensures a clean exit
                    os.system("shutdown now")
 
    except KeyboardInterrupt:
        headLight.clear()
        brainLight.clear()
        ceyes.clear()  
        GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
    

    headLight.clear()
    brainLight.clear()
    ceyes.clear()  
    GPIO.cleanup() # this ensures a clean exit
    pn.join()                
  
    print ("goodbye")

