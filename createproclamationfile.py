##################################################################################
#
#     Create Proclamation File
#
#     This is the initial file of statements that the CordieBot uses when
#     speaking.
#
#     Important:  Note that embedded apostropies are not allowed in data fields.
#
##################################################################################

import json


data = {}  
data['p_msg'] = []  
data['p_msg'].append({  
    'ID': '1',
    'year': '2020',
    'month': '01',
    'day': '01',
    'message': 'Happy New Year and welcome to 2020'
})
data['p_msg'].append({  
    'ID': '2',
    'year': '',
    'month': '05',
    'day': '15',
    'message': 'Today is Moms birthday.'
})
data['p_msg'].append({  
    'ID': '3',
    'year': '',
    'month': '05',
    'day': '12',
    'message': 'Moms birthday is pretty soon.'
})
data['p_msg'].append({  
    'ID': '4',
    'year': '',
    'month': '06',
    'day': '10',
    'message': 'Today is Dads birthday.'
})
data['p_msg'].append({  
    'ID': '5',
    'year': '',
    'month': '06',
    'day': '10',
    'message': 'Dads birthday is pretty soon.'
})
data['p_msg'].append({  
    'ID': '6',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Were off to see the wizard.'
})
data['p_msg'].append({  
    'ID': '7',
    'year': '',
    'month': '',
    'day': '',
    'message': 'I am all shined up with no place to go.'
})
data['p_msg'].append({  
    'ID': '8',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Bots rule.'
})
data['p_msg'].append({  
    'ID': '9',
    'year': '',
    'month': '',
    'day': '',
    'message': 'has anybody seen r 2 d 2?'
})
data['p_msg'].append({  
    'ID': '10',
    'year': '',
    'month': '',
    'day': '',
    'message': 'I must not say: voldehmort.'
})
data['p_msg'].append({  
    'ID': '11',
    'year': '',
    'month': '',
    'day': '',
    'message': 'its a  bird, its a  plane, its, superman.'
})
data['p_msg'].append({  
    'ID': '12',
    'year': '',
    'month': '',
    'day': '',
    'message': 'i would like to taste a butter beer, but i dont have a tongue.'
})
data['p_msg'].append({  
    'ID': '13',
    'year': '',
    'month': '',
    'day': '',
    'message': 'yubba dubba doo.'
})
data['p_msg'].append({  
    'ID': '14',
    'year': '',
    'month': '',
    'day': '',
    'message': 'what would skoobie do?'
})
data['p_msg'].append({  
    'ID': '15',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Is it true?  Is it kind?  Will it help?'
})
data['p_msg'].append({  
    'ID': '16',
    'year': '',
    'month': '',
    'day': '',
    'message': 'B B 8.  That droid is great.'
})
data['p_msg'].append({  
    'ID': '17',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Am I the droid you are looking for?'
})
data['p_msg'].append({  
    'ID': '18',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Minecraft is fun.'
})
data['p_msg'].append({  
    'ID': '19',
    'year': '',
    'month': '',
    'day': '',
    'message': 'I have nothing to say about that.'
})
data['p_msg'].append({  
    'ID': '20',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Apologize.  Apologize.'
})
data['p_msg'].append({  
    'ID': '21',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Im sorry.  Oh, that is Victors line.'
})
data['p_msg'].append({  
    'ID': '22',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Kibo says Hi'
})
data['p_msg'].append({  
    'ID': '23',
    'year': '',
    'month': '',
    'day': '',
    'message': 'Is that a robophobic remark?'
})

with open('proclamations.txt', 'w') as outfile:  
    json.dump(data, outfile)
