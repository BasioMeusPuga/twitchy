#!/usr/bin/python


import requests
import json
import sqlite3
import sys
import select
import argparse
import locale
import subprocess
import shlex
import webbrowser

from multiprocessing.dummy import Pool as ThreadPool
from os.path import expanduser, exists
from random import randrange
from time import time
from shutil import which


# Options
player = "mpv"
mpv_hardware_acceleration = True
default_quality = "high"
truncate_status_at = 100
database_path = expanduser("~") + '/.twitchy.db'


# Color code declaration
class colors:
	GAMECYAN = '\033[96m'
	NUMBERYELLOW = '\033[93m'
	ONLINEGREEN = '\033[92m'
	OFFLINERED = '\033[91m'
	TEXTWHITE = '\033[97m'
	ENDC = '\033[0m'


# Stuff that isn't options. Or optional. Lel.
""" Check for requirements """
if which('livestreamer') is None:
	print(colors.OFFLINERED + " livestreamer " + colors.ENDC + "is not installed. FeelsBadMan.")
	exit()
if which(player) is None:
	print(colors.OFFLINERED + " " + player + colors.ENDC + " is not installed / doesn't exist. FeelsKappaMan.")
	exit()

""" Database related """
if not exists(database_path):
	print(" First run. Creating db and exiting")
	database = sqlite3.connect(database_path)
	database.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
	database.execute("CREATE TABLE games (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
	database.close()
	exit()
database = sqlite3.connect(database_path)
dbase = database.cursor()
""" Set locale for comma placement """
locale.setlocale(locale.LC_ALL, '')


# Functions
# I'm told global variables are literally Hitler
def get_options():
	if player == "mpv" and mpv_hardware_acceleration is True:
		player_final = "mpv --hwdec=vaapi --vo=vaapi --cache 8192"
	else:
		player_final = "mpv --cache 8192"
	return player_final, mpv_hardware_acceleration, default_quality, truncate_status_at, database_path
	""" Options List Scheme
	0: Video Player
	1: Hardware accel (for mpv)
	2: Default player quality
	3: Truncate status
	4: Database location """


# Display template mapping for extra spicy output
def template_mapping(display_number, called_from):

	third_column = 20
	""" What value is specified for the last column really doesn't matter
	as long as a value is specified """

	if called_from == "list":
		first_column = 25
		second_column = 40
	elif called_from == "listnocolor":
		first_column = 25
		second_column = 31
	elif called_from == "gameslist":
		first_column = 50
		second_column = 55
	elif called_from == "gameslistnocolor":
		first_column = 50
		second_column = 46
	elif called_from == "watch":
		first_column = 25
		second_column = 20
		third_column = 100

	template = "{0:%s}{1:%s}{2:%s}" % (first_column, second_column, third_column)
	if display_number >= 10:
		template = "{0:%s}{1:%s}{2:%s}" % (first_column - 1, second_column, third_column)
	if display_number >= 100:
		template = "{0:%s}{1:%s}{2:%s}" % (first_column - 2, second_column, third_column)

	return template


# Convert time in seconds to a more human readable format. This doesn't mean you're human.
def time_convert(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)

	if d > 0:
		time_converted = "%dd %02dh %02dm %02ds" % (d, h, m, s)
	elif h > 0:
		time_converted = "%02dh %02dm %02ds" % (h, m, s)
	else:
		time_converted = "%02dm %02ds" % (m, s)

	return time_converted


# Add to database. Call with "-a" or "-s". Haha I said ass.
def add_to_database(channel_input):
	final_addition_streams = []

	def final_addition(final_addition_input):
		something_added = False
		print(" " + colors.NUMBERYELLOW + "Additions to database:" + colors.ENDC)
		for channel_name in final_addition_input:
			does_it_exist = dbase.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_name).fetchone()
			if does_it_exist is None:
				something_added = True
				database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name)
				print(" " + channel_name)
		database.commit()
		if something_added is False:
			print(" " + colors.OFFLINERED + "None" + colors.ENDC)

	if sys.argv[1] == "-s":
		username = channel_input[0]
		r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels' % username)
		stream_data = json.loads(r.text)

		try:
			total_followed = stream_data['_total']
			r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels?limit=%s' % (username, str(total_followed)))
			stream_data = json.loads(r.text)
			for i in range(0, total_followed):
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


# Obscurely named function. Call with "-d", "-an" or "-n"
def read_modify_deletefrom_database(channel_input):
	table_wanted = input(" Change (s)treamer or (g)ame name? ")
	if table_wanted == "s":
		table_wanted = "channels"
	elif table_wanted == "g":
		table_wanted = "games"
	else:
		exit()

	if channel_input == "BlankForAllIntensivePurposes":
		relevant_list = dbase.execute('SELECT Name, TimeWatched, AltName FROM %s' % table_wanted).fetchall()
	else:
		relevant_list = dbase.execute("SELECT Name, TimeWatched, AltName FROM '{0}' WHERE Name LIKE '{1}'".format(table_wanted, ('%' + channel_input + '%'))).fetchall()

	if len(relevant_list) == 0:
		print(colors.OFFLINERED + " Database query returned nothing." + colors.ENDC)
		exit()

	relevant_list.sort()
	""" List Scheme of Tuples
	0: Name
	1: TimeWatched
	2: AltName """

	display_number = 1
	for i in relevant_list:
		if i[2] is not None:
			if table_wanted == "channels":
				template = template_mapping(display_number, "list")
			elif table_wanted == "games":
				template = template_mapping(display_number, "gameslist")

			if i[1] == 0:
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], colors.GAMECYAN + str(i[2]) + colors.OFFLINERED, " Unwatched" + colors.ENDC))
			else:
				time_watched = time_convert(i[1])
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], colors.GAMECYAN + str(i[2]) + colors.ENDC, time_watched))
		else:
			if table_wanted == "channels":
				template = template_mapping(display_number, "listnocolor")
			elif table_wanted == "games":
				template = template_mapping(display_number, "gameslistnocolor")

			if i[1] == 0:
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.OFFLINERED + " " + template.format(i[0], str(i[2]), "Unwatched") + colors.ENDC)
			else:
				time_watched = time_convert(i[1])
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], str(i[2]), time_watched))
		display_number = display_number + 1

	if sys.argv[1] == "-d":
		try:
			final_selection = input(" Stream / Channel number(s)? ")
			print(" " + colors.NUMBERYELLOW + "Deleted from database:" + colors.ENDC)
			entered_numbers = [int(i) for i in final_selection.split()]
			for j in entered_numbers:
				print(" " + relevant_list[j - 1][0])
				database.execute("DELETE FROM '{0}' WHERE Name = '{1}'".format(table_wanted, relevant_list[j - 1][0]))
			database.commit()
		except IndexError:
			print(colors.OFFLINERED + " How can columns be real if our databases aren\'t real?" + colors.ENDC)

	if sys.argv[1] == "-an":
		try:
			final_selection = int(input(" Stream / Channel number? "))
			old_name = relevant_list[final_selection - 1][0]
			new_name = input(" Replace " + old_name + " with? ")

			if new_name == "":
				database.execute("UPDATE '{0}' SET AltName = NULL WHERE Name = '{1}'".format(table_wanted, old_name))
			else:
				database.execute("UPDATE '{0}' SET AltName = '{1}' WHERE Name = '{2}'".format(table_wanted, new_name, old_name))
			database.commit()
		except:
			print(colors.OFFLINERED + " OH MY GOD WHAT IS THAT BEHIND YOU?" + colors.ENDC)

	database.close()
	exit()


# Generate stuff for livestreamer to agonize endless over. Is it fat? It's a program so no.
def watch(channel_input):
	database.row_factory = lambda cursor, row: row[0]
	dbase = database.cursor()

	print(" " + colors.NUMBERYELLOW + "Checking channels..." + colors.ENDC)
	if channel_input == "BlankForAllIntensivePurposes":
		status_check_required = dbase.execute('SELECT Name FROM channels').fetchall()
		altname_list = dbase.execute('SELECT AltName FROM channels').fetchall()
	elif sys.argv[1] == "-c":
		status_check_required = dbase.execute("SELECT Name FROM channels WHERE Name LIKE ?", ('%' + channel_input + '%',)).fetchall()
		altname_list = dbase.execute("SELECT AltName FROM channels WHERE Name LIKE ?", ('%' + channel_input + '%',)).fetchall()
	elif sys.argv[1] == "-w":
		status_check_required = channel_input
		altname_list = []
		for j in channel_input:
			altname_list.append(dbase.execute("SELECT AltName FROM channels WHERE Name = '%s'" % j).fetchone())

	stream_status = []

	def get_status(channel_name):
		r = requests.get('https://api.twitch.tv/kraken/streams/' + channel_name)
		stream_data = json.loads(r.text)

		try:
			stream_data['error']
		except:
			if stream_data['stream'] is not None:  # Offline Channels return None
				alt_name = altname_list[status_check_required.index(channel_name)]

				truncate_status_at = get_options()[3]
				status_message = str(stream_data['stream']['channel']['status'])
				if len(status_message) > truncate_status_at:
					status_message = status_message[0:truncate_status_at - 3] + "..."

				stream_status.append([stream_data['stream']['channel']['name'], str(stream_data['stream']['channel']['game']), status_message, stream_data['stream']['viewers'], alt_name, stream_data['stream']['channel']['partner']])
		""" List Scheme
		0: Stream name
		1: Game name
		2: Status message
		3: Viewers
		4: Alternate name
		5: Partner status """

	pool = ThreadPool(30)
	pool.map(get_status, status_check_required)
	pool.close()
	pool.join()

	if len(stream_status) > 0:
		stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
	else:
		print(" All channels offline")
		exit()

	stream_final = []
	games_shown = []
	display_number = 1

	for i in stream_status:
		display_name_game = dbase.execute("SELECT AltName FROM games WHERE Name = '%s'" % i[1]).fetchone()
		if display_name_game is None:
			display_name_game = i[1]

		if display_name_game not in games_shown:
			print(" " + colors.GAMECYAN + display_name_game + colors.ENDC)
			games_shown.append(display_name_game)

		stream_final.insert(display_number - 1, [i[0], i[1]])
		template = template_mapping(display_number, "watch")

		if i[4] is None:
			display_name = i[0]
		else:
			display_name = i[4]

		print(" " + colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(display_name, str(format(i[3], "n")), i[2]) + colors.ENDC))
		display_number = display_number + 1

	""" Parse user input.
	Multiple valid entries are passed to multi_twitch().
	Single entries are passed to playtime()
	Allows for time_tracking() and music identification
	using hacks so ugly they might as well be yo' mama. """

	try:
		stream_select = input(" Channel number(s)? ")

		watch_input_final = []
		final_selection = []
		default_quality = get_options()[2]

		entered_numbers = stream_select.split()
		for a in entered_numbers:
			watch_input_final.append(a.split("-"))

		for j in watch_input_final:
			if len(j) == 1:
				final_selection.append([stream_final[int(j[0]) - 1][0], default_quality])
			else:
				if j[1] == "l":
					custom_quality = "low"
				elif j[1] == "m":
					custom_quality = "medium"
				elif j[1] == "h":
					custom_quality = "high"
				elif j[1] == "s":
					custom_quality = "source"
				else:
					custom_quality = default_quality
				final_selection.append([stream_final[int(j[0]) - 1][0], custom_quality])

		if len(final_selection) == 1:
			playtime(final_selection[0][0], final_selection[0][1], stream_final[int(watch_input_final[0][0]) - 1][1])
		elif len(final_selection) > 1:
			database.close()  # This must be removed if time tracking is ever to be implemented for multi_twitch()
			multi_twitch(final_selection)
		else:
			random_stream = randrange(0, display_number - 1)
			final_selection = stream_final[random_stream][0]
			playtime(final_selection, default_quality, stream_final[random_stream][1])
	except (IndexError, ValueError):
		print(colors.OFFLINERED + " Huh? Wut? Lel? Kappa?" + colors.ENDC)


# Stuff to do once we have sufficient data to start livestreamer
def playtime(final_selection, stream_quality, game_name):
	does_it_exist = dbase.execute("SELECT Name FROM games WHERE Name = '%s'" % game_name).fetchone()
	if does_it_exist is None:
		database.execute("INSERT INTO games (Name,Timewatched,AltName) VALUES ('%s',0,NULL)" % game_name)
		database.commit()
	database.close()

	start_time = time()
	print(" Now watching " + colors.TEXTWHITE + final_selection + colors.ENDC + " | Quality: " + colors.TEXTWHITE + stream_quality + colors.ENDC)

	options = get_options()
	player_final = options[0] + " --title " + final_selection

	try:
		webbrowser.get('chromium').open_new('--app=http://www.twitch.tv/%s/chat?popout=' % final_selection)
	except:
		webbrowser.open_new('http://www.twitch.tv/%s/chat?popout=' % final_selection)

	args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3".format(final_selection, stream_quality, player_final)
	args_to_subprocess = shlex.split(args_to_subprocess)
	livestreamer_process = subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL)

	print(" q / Ctrl + C to quit | m to identify music ")
	while livestreamer_process.returncode is None:
		""" returncode does nothing without polling
		A delay in the while loop is introduced by the select function below """
		livestreamer_process.poll()
		try:
			keypress, o, e = select.select([sys.stdin], [], [], 0.8)
			if (keypress):
				keypress_made = sys.stdin.readline().strip()
				if keypress_made == "q":
					livestreamer_process.terminate()
				elif keypress_made == "m":
					webbrowser.open('http://www.twitchecho.com/%s' % final_selection)
		except KeyboardInterrupt:
			livestreamer_process.terminate()
			break

	time_tracking(final_selection, game_name, start_time)


# ONLY gets called if ONE channel is specified.
def time_tracking(channel_input, game_name, start_time):
	end_time = time()
	time_watched = int(end_time - start_time)

	database = sqlite3.connect(database_path)
	dbase = database.cursor()

	""" Update time watched for a channel that exists in the database (avoids exceptions due to -w) """
	does_it_exist = dbase.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_input).fetchone()
	if does_it_exist[0] is not None:
		total_time_watched = dbase.execute("SELECT TimeWatched FROM channels WHERE Name = '%s'" % channel_input).fetchone()
		total_time_watched = total_time_watched[0] + time_watched
		database.execute("UPDATE channels set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, channel_input))
		print(" Total time spent watching " + colors.TEXTWHITE + channel_input + colors.ENDC + ": " + time_convert(total_time_watched))

	""" Update time watched for game. All game names will already be in the database. """
	total_time_watched = dbase.execute("SELECT TimeWatched FROM games WHERE Name = '%s'" % game_name).fetchone()
	total_time_watched = total_time_watched[0] + time_watched
	database.execute("UPDATE games set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, game_name))
	print(" Total time spent watching " + colors.TEXTWHITE + game_name + colors.ENDC + ": " + time_convert(total_time_watched))

	database.commit()
	database.close()


# Alleged Multi-Twitch.
def multi_twitch(channel_input):
	print(" Now watching: ")
	number_of_channels = len(channel_input)
	player_final = get_options()[0]

	for i in range(0, number_of_channels - 1):
		stream_quality = channel_input[i][1]
		print(" " + colors.TEXTWHITE + channel_input[i][0] + colors.ENDC + " - " + colors.TEXTWHITE + stream_quality + colors.ENDC)
		args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3".format(channel_input[i][0], stream_quality, player_final + " --title " + channel_input[i][0])
		args_to_subprocess = shlex.split(args_to_subprocess)
		subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL)

	print(" " + colors.TEXTWHITE + channel_input[number_of_channels - 1][1] + colors.ENDC + " - " + colors.TEXTWHITE + stream_quality + colors.ENDC)
	stream_quality = channel_input[number_of_channels - 1][1]
	args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3".format(channel_input[number_of_channels - 1][0], stream_quality, player_final + " --title " + channel_input[number_of_channels - 1][0])
	args_to_subprocess = shlex.split(args_to_subprocess)
	subprocess.run(args_to_subprocess, stdout=subprocess.DEVNULL)
	exit()


# Parse CLI input
def main():
	parser = argparse.ArgumentParser(description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help=False)
	parser.add_argument('-h', '--help', help='This helpful message', action='help')
	parser.add_argument('-a', type=str, nargs='+', help='Add channel name(s) to database', metavar="", required=False)
	parser.add_argument('-an', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Set/Unset alternate names', required=False)
	parser.add_argument('-d', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Delete channel(s) from database', required=False)
	parser.add_argument('-c', type=str, help='Search string in database', metavar="", required=False)
	parser.add_argument('-s', type=str, nargs=1, help='Sync username\'s followed accounts to local database', metavar="username", required=False)
	parser.add_argument('-w', type=str, nargs='+', help='Watch specified channel(s)', metavar="", required=False)
	args = parser.parse_args()

	if args.a:
		add_to_database(args.a)
	elif args.an:
		read_modify_deletefrom_database(args.an)
	elif args.c:
		watch(args.c)
	elif args.d:
		read_modify_deletefrom_database(args.d)
	elif args.s:
		add_to_database(args.s)
	elif args.w:
		watch(args.w)
	else:
		watch("BlankForAllIntensivePurposes")

try:
	main()
except KeyboardInterrupt:
	database.close()
	exit()
