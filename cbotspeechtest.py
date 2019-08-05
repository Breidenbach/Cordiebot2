##################################################################################
#
#     Imports
#
##################################################################################

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import json
import sys
import os
import signal
from gpiozero import DigitalOutputDevice
 
##################################################################################
#
#     Set up I/O 
#
##################################################################################

ampEnable = DigitalOutputDevice(21)  # GPIO number to enable the amplifier board
#                 when low, amp is disabled
#    The board outputs random static when audio is not active.
ampEnable.off()
        
    
##################################################################################
#
#     Set up PubNub 
#
##################################################################################


keyfile = "./keys.html"
pnconfig = PNConfiguration()

try:
    with open(keyfile, 'r') as f:
        for value in f.readlines():  # read all lines
            frst = value.find("'") + 1
            lst = value.rfind("'")
            if "Publish" in value:
                pnconfig.publish_key =  value[frst:lst]           
            else:
                if "Subscribe" in value:
                    pnconfig.subscribe_key =  value[frst:lst]           

except Exception as ex:
    print(ex)

pubnub = PubNub(pnconfig)
 
my_channel = 'cordietalk'

def process_message(msg):
    print ("process message: ", msg)
    
def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        pass  # Message successfully published to specified channel.
    else:
        pass  # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];
 
 
class MySubscribeCallback(SubscribeCallback):
    def __init__(self, response):
        self.response = response
        
    def presence(self, pubnub, presence):
        pass  # handle incoming presence data
 
    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            pass  # This event happens when radio / connectivity is lost
 
        elif status.category == PNStatusCategory.PNConnectedCategory:
            # Connect event. You can do stuff like publish, and know you'll get it.
            # Or just use the connected event to confirm you are subscribed for
            # UI / internal notifications, etc
            pubnub.publish().channel(my_channel).message(self.response).pn_async(my_publish_callback)
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.
 
    def message(self, pubnub, message):
        print("from Hal: " + str(message.message))
        if message.message != self.response:
            #process_message(message.message)
            phrase = ("aoss swift \"<prosody rate='-0.3'>" +
                     str(message.message['content']) +
                     "<break strength='strong' />\"")
            ampEnable.on()
            os.system(phrase)
            ampEnable.off()
            pubnub.publish().channel(my_channel).message(self.response).pn_async(my_publish_callback)
 
pubnub.add_listener(MySubscribeCallback("hello!!"))
pubnub.subscribe().channels(my_channel).execute()