import os,sys
import subprocess

debug = True

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

CBLine = findCordiebotUSB()
if CBLine == "":
    if debug:
        print ("not in view")
else:
    if debug:
        print (CBLine)
    firstSpace = CBLine.find(' ')
    secondSpace = CBLine.find(' ', firstSpace + 1)
    dirSpec = CBLine[int(firstSpace + 1):int(secondSpace)]
    if debug:
        print (dirSpec)
    
    files = os.listdir(dirSpec)
    for name in files:
        if (name == "wpa_supplicant.conf"):
            if debug:
                print ("found file ", name, " and copying it.")
            p = subprocess.Popen("sudo /home/pi/CordieBot2/cp_wpa_conf.sh "+dirSpec,
                        shell=True)
            p.communicate()