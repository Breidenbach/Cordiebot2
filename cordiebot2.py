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
from datetime import date
from TouchButton import TouchButton
from multiprocessing import *
import requests
import json
from random import *
import urllib.request
import feedparser
import socket
import subprocess
import signal
from gpiozero import MCP3002
from gpiozero import DigitalOutputDevice
from gpiozero import PWMOutputDevice
from runningAverage import runningAverage

##################################################################################
#
#     "Constants"
#
##################################################################################

debug = False            # to print various details
debugLights = False     # help debugging light show
debugTalk = False       # help debug speaking

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
#          LED board uses SPIMOSI and SPISCLK, MISO is not used but must be specified

# Define the TLC59711 instance to communicate with lights
leds = adafruit_tlc59711.TLC59711(spi)

ampEnable = DigitalOutputDevice(21)  # GPIO number to enable the amplifier board
#                 when low, amp is disabled
#    The board outputs random static when audio is not active.
ampEnable.off()

button = 25  # GPIO number of touch sensor

fan = PWMOutputDevice(18)
fan.value = 0   #   start out with fan off.


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
    ampEnable.on()
    os.system(phrase)
    ampEnable.off()
    
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
    
noNetworkTxt = ("aoss swift \"<prosody rate='-0.3'> " +
                "I don't appear to be connected to a why fi network.\"" )

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

checkNetworkTxt = ("aoss swift \" Check if your why fi is running. Check if " +
             "anyone changed the password.  Otherwise, grampa might be able to help.\"")

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

def doPubNub(pid):
    if debug:
        print ('python pubnubpipe.py ' + pid)
    args = 'python' + ' pubnubpipe.py ' + str(pid)
    pn_proc = subprocess.Popen(args, shell=True)
    return pn_proc
#        os.system('python pubnubpipe.py ' + pid)

proc_file_change = False

def receive_signal(signum, stack):
    global proc_file_change
    if signum == int(signal.SIGUSR1):
        proc_file_change = True
        if debug:
            print ("received SIGUSR1 setting proc_file_change to " +
                         str(proc_file_change))
    return

# set up average routine
tAvg = runningAverage(17)

def runFan():
    pot = MCP3002(channel=0, device=1)
    volts = pot.value * 3.3
    # convert volts to degrees F,
    # 0 to 1 volts = -56 to 156 degrees C, then convert to degrees F
    temperature = pot.value * 629.64 - 68.8
    avgTemp = tAvg.value(temperature)
    if debug:
        print("pot value = %2.3f   volts = %2.3f   temperature = %3.3f"
                     % (pot.value, volts, avgTemp))
    # Note that pwm value may range from 0 (fully off) to 1.0 (fully on)
    if (avgTemp > 95):
        if (avgTemp > 110):
            fan.value = 1.0
        else:
            fan.value = 0.5
    else:
        fan.value = 0
    return avgTemp


    
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
#        if debugLights:
#            print ("set led = ", self.lightChannel, "  settings= ",
#                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r = inr   # r, g, and b values should be sent as 1/2 the desired brightness
        self.g = ing
        self.b = inb
        self.send()
    def update(self, inr, ing, inb):
#        if debugLights:
#            print ("update led = ", self.lightChannel, "  settings= ",
#                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
        self.r += inr
        self.g += ing
        self.b += inb
        self.send()
    def fadeOut(self, inr, ing, inb):
#        if debugLights:
#            print ("fadeOut led = ", self.lightChannel, "  settings= ",
#                        self.r, self.g, self.b, "  vals=", inr, ing, inb)
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

class procTable:
    def __init__(self):
        self.count = 0
        self.list = []
    def add(self, message):
        self.count += 1
        self.list.append(message)
    def getRandom(self):
        if self.count == 0:
            return "empty"
        else:
            if self.count == 1:
                return self.list[0]["message"]
            else:
                return self.list[randint(0,self.count-1)]["message"]
    def clear(self):
        self.count = 0
        self.list = []
    def count(self):
        return self.count

procs_special = procTable()
procs_today = procTable()
procs_anytime = procTable()

#  buildProcTables is used when CordieBot is started and other times tables
#  need initialization 

def buildProcTables():
    with open('proclamations.txt') as p_file:  
        p_data = json.load(p_file)
    mydate = date.today()
    if debug:
        print( mydate.year, " / ", mydate.month, " / ", mydate.day)
    for p in p_data['p_msg']:
        if debug:
            print (p)
        if p['year'].isdigit():
            if ((int(p['year']) == mydate.year) and
                 (int(p['month']) == mydate.month) and
                 (int(p['day']) == mydate.day)):
                procs_special.add(p)
        else:
            if p['month'].isdigit():
                if ((int(p['month']) == mydate.month) and
                     (int(p['day']) == mydate.day)):
                    procs_today.add(p)
            else:
                procs_anytime.add(p)

#  updateProcTables is executed when a message is received from pubnubpipe that the 
#  proclamation message file has changed.

def updateProcTables():
    procs_special.clear()
    procs_today.clear()
    procs_anytime.clear()
    buildProcTables()

def getProcMsg():
    if procs_special.count > 0 and randint(0,4) == 2:
        return procs_special.getRandom()
    if procs_today.count > 0 and randint(0,3) == 1:
        return procs_today.getRandom()
    if randint(0,2) == 2:
        return procs_anytime.getRandom()
    return ''
            
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
            print ("ndx = ", ndx, "  Head Deltas = ", headDeltas,
                             "  Brain Deltas = ", brainDeltas)    
        ndx += 1
    headDeltas[:] = [-1*x/rampVal for x in headDeltas]
    brainDeltas[:] = [-1*x/rampVal for x in brainDeltas]
    if debugLights:
        print ("after get increments  Head Deltas = ", headDeltas,
                         "  Brain Deltas = ", brainDeltas)    
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
    dateTxt = ("aoss swift \"<prosody rate='-0.3'>" + timeStr + "<break time='2s' />" +
                        getProcMsg() + "\"")
    if debugTalk:
        print (len(dateTxt), "  ", dateTxt)
    if len(dateTxt) > 90 :
        lightCount = 6
    else:
        lightCount = 3
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(lightCount,))
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
                print(len(data), "  ", data)
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
        ls = Process(target=lightShow, args=(4,))
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
            print (len(quoteTxt), "  ", quoteTxt)
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
        print (len(originsTxt), "  ", originsTxt)
    speak(originsTxt)
                        
def doOrigins():
    if debug:
        print ("getting origins")
    if __name__ == "__main__":
        ls = Process(target=lightShow, args=(8,))
        ls.start()
        ps = Process(target=originsDetails)
        ps.start()
        ls.join()
        ps.join()
        
def doInternalTemp(t):
    txtinner = "my internal temperature is %3.1f" % t
    txt = "aoss swift \"<prosody rate='-0.3'>" + txtinner + "\""
    speak(txt)        
                
 
##################################################################################
#
#              Initial on tests...
#
##################################################################################

def wakeUp():
    if debug:
        speak('aoss swift "<prosody rate=\'-0.3\'>I am version 2.00"')
    
    #  check lights
    
    ceyes.open()
    headLight.update(32767, 0, 0)
    brainLight.update(32767, 0, 0)
    time.sleep(1)
    headLight.clear()
    brainLight.clear()
    headLight.update(0, 32767, 0)
    brainLight.update(0, 32767, 0)
    time.sleep(1)
    headLight.clear()
    brainLight.clear()
    headLight.update(0, 0, 32767)
    brainLight.update(0, 0, 32767)
    time.sleep(1)
    headLight.clear()
    brainLight.clear()
    ceyes.close()
        
    #  Proclamation file initialization
    
    buildProcTables()
    signal.signal(signal.SIGUSR1, receive_signal)
    

##################################################################################
#
#              Main program...
#
##################################################################################


if __name__ == '__main__':
    proc_file_change = False
    request = TouchButton(button, 1.5)
    ceyes = Eyes()
    headLight = Lamp(0)
    brainLight = Lamp(3)
    wakeUp()
    my_pid = str(os.getpid())
    if debug:
        print ("my pid is ",my_pid)
    pn_proc = doPubNub(my_pid)
    insideTemp = 0

    try:  
        while True:
            if proc_file_change:
                print ("proc_file_change is True!")
                updateProcTables()
                proc_file_change = False
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
                if (code == 9):
                    doInternalTemp(insideTemp)
                if (code == 255):
                    headLight.clear()
                    brainLight.clear()
                    ceyes.clear()  
                    GPIO.cleanup() # this ensures a clean exit
                    os.system("shutdown now")
            insideTemp = runFan()
            if (pn_proc.poll() != None):  #check if pubnub communication terminated
                currentDT = datetime.now()
                if currentDT.second == 0:
                    pn_proc = doPubNub(my_pid)

    except KeyboardInterrupt:
        headLight.clear()
        brainLight.clear()
        ceyes.clear()  
        GPIO.cleanup()      # clean up GPIO on CTRL+C exit  
#        pn_proc.kill()      # stop pubnub communication          
    

    headLight.clear()
    brainLight.clear()
    ceyes.clear()  
    GPIO.cleanup()      # this ensures a clean exit
#    pn_proc.kill()      # stop pubnub communication            
  
    if debug:
        print ("goodbye")

