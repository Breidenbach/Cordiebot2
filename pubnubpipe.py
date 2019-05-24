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
 
##################################################################################
#
#     Process Proclamations file 
#
##################################################################################

def no_msg(id):
    return "Message " + id + " not found."

class manage_p_file:
    def __init__(self):
        with open("proclamations.txt") as self.p_file:  
            self.p_data = json.load(self.p_file)
    def add(self, message):
        newID = 0
        for p in self.p_data['p_msg']:
            if int(p['ID']) > newID:
                newID = int(p['ID'])
        newID_str = str(newID + 1)
        r_data = {'ID' : newID_str, 'day': message['day'], 'month' : message['month'],
                'year' :  message['year'], 'message' : message['content'] }
        print (r_data)
        self.p_data['p_msg'].append(r_data)
        with open("proclamations.txt", 'w') as self.p_file:  
            json.dump(self.p_data, self.p_file)
        return r_data
    def change(self, message):
        print (str(message))
        r_data = no_msg(message['ID'])
        for p in self.p_data['p_msg']:
            if p['ID'] == message['ID']:
                p['day'] = message['day']
                p['month'] = message['month']
                p['year'] = message['year']
                p['message'] = message['content']
                r_data = str(p)
                with open("proclamations.txt", 'w') as self.p_file:  
                    json.dump(self.p_data, self.p_file)
                break
        return r_data
    def delete(self, message):
        print (str(message))
        r_data = no_msg(message['ID'])
        for i, p in enumerate(self.p_data['p_msg']):
            if p['ID'] == message['ID']:
                r_data = self.p_data['p_msg'].pop(i)
                with open("proclamations.txt", 'w') as self.p_file:  
                    json.dump(self.p_data, self.p_file)
                break        
        return r_data
    def get(self, message):
        r_data = no_msg(message['ID'])
        for p in self.p_data['p_msg']:
            print ("p['ID'] = ", p['ID'])
            if p['ID'] == message['ID']:
                r_data = p
                break
        return r_data
    def get_next(self, message):
        pass
    def get_by_date(self, message):
        return ("get by date not implimented.")
    def get_next_by_date(self, message):
        pass
    def resequence():
        with open("proclamations.txt", 'w') as self.p_file:  
            json.dump(self.p_data, self.p_file)
        return ("resequence not implimented.")
  
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
 
my_channel = 'cordiebot'

p_file = manage_p_file()

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
            if message.message['action'] == 1:
                print ("add message")
                self.response = "Action = add.  " + str(p_file.add(message.message))
            if message.message['action'] == 2:
                print ("change message")
                self.response = "Action = change.  " + str(p_file.change(message.message))
            if message.message['action'] == 3:
                print ("delete message")
                self.response = "Action = delete.  " + str(p_file.delete(message.message))
            if message.message['action'] == 4:
                print ("get message")
                rspns = "Action = retrieve.  " + str(p_file.get(message.message))
                self.response = rspns
            if message.message['action'] == 5:
                self.response = "not implemented"
            if message.message['action'] == 6:
                self.response = "not implemented"
            if message.message['action'] == 7:
                self.response = "not implemented"
            if message.message['action'] > 7:
                print ("invalid message")
                self.response = "invalid action"
            pubnub.publish().channel(my_channel).message(self.response).pn_async(my_publish_callback)
 

 
pubnub.add_listener(MySubscribeCallback("hello!!"))
pubnub.subscribe().channels(my_channel).execute()