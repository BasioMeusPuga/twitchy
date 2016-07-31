#!/usr/bin/python

import requests
import json
import sqlite3

from multiprocessing.dummy import Pool as ThreadPool 
from os.path import expanduser

database = sqlite3.connect(str(expanduser("~") + '/.twitchy.db'))
database.row_factory = lambda cursor, row: row[0]
dbase = database.cursor()
names_from_db = dbase.execute('SELECT name FROM channels').fetchall()
database.close()

stream_final = {}
def status(channel_name):
	r = requests.get('https://api.twitch.tv/kraken/streams/' + channel_name)
	stream_data = json.loads(r.text)

	if str(stream_data['stream']) == "None":
		stream_final[channel_name] = [ "Offline" ]
	else:
		stream_final[channel_name] = [ stream_data['stream']['channel']['game'], stream_data['stream']['channel']['display_name'], stream_data['stream']['channel']['status'], stream_data['stream']['viewers'], stream_data['stream']['channel']['partner'] ]
	"""Dictionary Scheme
	Key: Channel name
	List0: Game Name
	List1: Display name
	List2: Stream Status
	List3: Viewers
	List4: Partner Status"""

pool = ThreadPool(30)
results = pool.map(status, names_from_db)
pool.close()
pool.join() 

#for channel_name in dbase:
	#status(channel_name[0])
for i in stream_final:
	if stream_final[i][0] != "Offline":
		print (stream_final[i][1])
		
		
