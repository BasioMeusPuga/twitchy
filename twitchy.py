#!/usr/bin/python

import requests
import json
import sqlite3
import sys
import argparse

from multiprocessing.dummy import Pool as ThreadPool 
from os.path import expanduser
from os import system

database = sqlite3.connect(str(expanduser("~") + '/.twitchy.db'))
database.row_factory = lambda cursor, row: row[0]
dbase = database.cursor()

class colors:
	GAMECYAN = '\033[96m'
	NUMBERYELLOW = '\033[93m'
	ONLINEGREEN = '\033[92m'
	OFFLINERED = '\033[93m'
	ENDC = '\033[0m'
    
# Functions
## Add to database. Call with "-a" or "-s". Haha I said ass.
def add_to_database(channel_input):
	final_addition_streams = []

	def final_addition (final_addition_input):
		for channel_name in final_addition_input:
			does_it_exist = dbase.execute("SELECT Name FROM channels WHERE name = '%s'" % channel_name).fetchone()
			if str(does_it_exist) == "None":
				database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name)
				database.commit()
				print(" " + channel_name + " added to database")
			else:
				print(" " + channel_name + " is already in database")

	if sys.argv[1] == "-s":
		username = channel_input[0]
				
		r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels' % username)
		stream_data = json.loads(r.text)
		
		try:
			total_followed = stream_data['_total']
			r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels?limit=%s' % (username, str(total_followed)))
			stream_data = json.loads(r.text)
			sync_run_once = True
			for i in range(0,total_followed):
				final_addition_streams.append(stream_data['follows'][i]['channel']['name'].lower())
			final_addition(final_addition_streams)
		except:
			print(" " + username + " doesn't exist")

	if sys.argv[1] == "-a":
		for names_for_addition in channel_input:
			r = requests.get('https://api.twitch.tv/kraken/streams/' + names_for_addition)
			stream_data = json.loads(r.text)
			try:
				stream_data['error']
				print(" " + names_for_addition + " doesn't exist")
			except:
				final_addition_streams.append(names_for_addition)
		final_addition(final_addition_streams)

	database.close()
	exit()

## Livestreamer called here with "-w", "-c" or our carefully chosen input string
def watch(channel_input):
	print (" " + colors.NUMBERYELLOW + "Checking channels..." + colors.ENDC)
	if channel_input == "BlankForAllIntensivePurposes":
		status_check_required = dbase.execute('SELECT name FROM channels').fetchall()
	elif sys.argv[1] == "-c":
		status_check_required = dbase.execute("SELECT name FROM channels WHERE name LIKE ?", ('%'+channel_input+'%',)).fetchall()
	else:
		status_check_required = channel_input
	
	database.close()
	stream_status = []
	def get_status(channel_name):
		r = requests.get('https://api.twitch.tv/kraken/streams/' + channel_name)
		stream_data = json.loads(r.text)

		try:
			stream_data['error']
		except:
			if str(stream_data['stream']) != "None":

				stream_status.append([stream_data['stream']['channel']['name'], str(stream_data['stream']['channel']['game']), str(stream_data['stream']['channel']['status']), stream_data['stream']['viewers'], stream_data['stream']['channel']['partner']])
		"""Dictionary Scheme
		List0: Display name
		List1: Game Name
		List2: Stream Status
		List3: Viewers
		List4: Partner Status"""

	pool = ThreadPool(30)
	results = pool.map(get_status, status_check_required)
	pool.close()
	pool.join() 

	if len(stream_status) > 0:
		stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
	else:
		print (" All channels offline")
		exit()

	stream_final = []
	games_shown = []
	display_number = 1
	template = "{0:25}{1:20}{2:100}"

	for i in stream_status:
		if i[1] not in games_shown:
			print (" " + colors.GAMECYAN + i[1] + colors.ENDC)
			games_shown.append(i[1])
		
		stream_final.insert(display_number - 1, i[0])
		if display_number >= 10:
			template = "{0:24}{1:20}{2:100}"
		elif display_number >= 100:
			template = "{0:23}{1:20}{2:100}"

		print (" " + colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(i[0], str(i[3]), i[2]) + colors.ENDC))
		display_number = display_number + 1

	stream_select = int(input(" Channel number? "))
	final_selection = stream_final[stream_select - 1]
	print (" Now watching " + final_selection)
	system('livestreamer twitch.tv/' + final_selection + ' high --player mpv --hls-segment-threads 3')

# Parse CLI input
parser = argparse.ArgumentParser(description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help = False)
parser.add_argument('-h', '--help', help='This helpful message', action='help')
parser.add_argument('-a', type=str, nargs='+', help='Add channel name(s) to database', metavar = "", required=False)
parser.add_argument('-c', type=str, help='Search string in database', metavar = "", required=False)
parser.add_argument('-s', type=str, nargs = 1, help='Sync specific channel\'s followed accounts to local database', metavar = "username", required=False)
parser.add_argument('-w', type=str, nargs='+', help='Watch specific channel(s)', metavar = "", required=False)
args = parser.parse_args()

if args.a:
	add_to_database(args.a)
if args.c:
	watch(args.c)
elif args.s:
	add_to_database(args.s)
elif args.w:
	watch(args.w)
else:
	watch("BlankForAllIntensivePurposes")