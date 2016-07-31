#!/usr/bin/python

import requests
import json
import sqlite3

from multiprocessing.dummy import Pool as ThreadPool 
from os.path import expanduser
from os import system

database = sqlite3.connect(str(expanduser("~") + '/.twitchy.db'))
database.row_factory = lambda cursor, row: row[0]
dbase = database.cursor()
names_from_db = dbase.execute('SELECT name FROM channels').fetchall()
database.close()

class colors:
    GAMECYAN = '\033[96m'
    NUMBERYELLOW = '\033[93m'
    ONLINEGREEN = '\033[92m'
    OFFLINERED = '\033[93m'
    ENDC = '\033[0m'
    
stream_status = {}
def get_status(channel_name):
	r = requests.get('https://api.twitch.tv/kraken/streams/' + channel_name)
	stream_data = json.loads(r.text)

	if str(stream_data['stream']) == "None":
		stream_status[channel_name] = [ "Offline" ]
	else:
		stream_status[channel_name] = [ stream_data['stream']['channel']['game'], stream_data['stream']['channel']['display_name'], stream_data['stream']['channel']['status'], stream_data['stream']['viewers'], stream_data['stream']['channel']['partner'] ]
	"""Dictionary Scheme
	Key: Channel name
	List0: Game Name
	List1: Display name
	List2: Stream Status
	List3: Viewers
	List4: Partner Status"""

pool = ThreadPool(30)
results = pool.map(get_status, names_from_db)
pool.close()
pool.join() 

# Sorting code goes here:

stream_final = []
template = "{0:20}{1:10}{2:100}"

games_shown = []
display_number = 1
for i in stream_status:
	if stream_status[i][0] != "Offline":
		if stream_status[i][0] not in games_shown:
			print (colors.GAMECYAN + stream_status[i][0] + colors.ENDC)
			games_shown.append(stream_status[i][0])
	
		stream_final.insert(display_number - 1, stream_status[i][1].lower())
		print (colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(stream_status[i][1], str(stream_status[i][3]), stream_status[i][2]) + colors.ENDC))
		display_number = display_number + 1

stream_select = int(input("Channel number? "))
final_selection = stream_final[stream_select - 1]
print ("Now watching " + final_selection)
system('livestreamer twitch.tv/' + final_selection + ' high --player mpv --hls-segment-threads 3')
