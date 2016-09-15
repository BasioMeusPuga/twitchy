#!/usr/bin/python3
# Requires: python3, livestreamer
# rev = 36


import sys
import json
import shlex
import select
import locale
import sqlite3
import requests
import argparse
import webbrowser
import subprocess

from time import time, sleep, strftime
from shutil import which
from random import randrange
from ast import literal_eval
from os import remove
from os.path import expanduser, exists, realpath, dirname


# Color code declaration
class colors:
	GAMECYAN = '\033[96m'
	NUMBERYELLOW = '\033[93m'
	ONLINEGREEN = '\033[92m'
	OFFLINERED = '\033[91m'
	TEXTWHITE = '\033[97m'
	ENDC = '\033[0m'


# Shenanigan avoidance
database_path = expanduser("~") + '/.twitchy.db'
global http_header
http_header = {'Client-ID': 'guulhcvqo9djhuyhb2vi56wqnglc351'}


# Options
def configure_options(special_occasion):
	try:
		print(colors.GAMECYAN + " Configure:" + colors.ENDC)
		player = input(" Media player [mpv]: ")
		if which(player) is None:
			if which('mpv') is not None:
				player = "mpv"
			else:
				print(colors.OFFLINERED + " " + player + colors.ENDC + " is not in $PATH. Please check if this is what you want.")
				raise

		mpv_hardware_acceleration = True
		if player == "mpv":
			mpv_option = input(" Use hardware acceleration (vaapi) with mpv [Y/n]: ")
			if mpv_option == "yes" or mpv_option == "Y" or mpv_option == "y" or mpv_option == "":
				mpv_hardware_acceleration = True
			else:
				mpv_hardware_acceleration = False

		default_quality = input(" Default stream quality [low/medium/HIGH/source]: ")
		if default_quality == "" or (default_quality != "low" and default_quality != "medium" and default_quality != "source"):
			default_quality = "high"

		truncate_status_at = input(" Truncate stream status at [100]: ")
		if truncate_status_at == "":
			truncate_status_at = 100
		else:
			truncate_status_at = int(truncate_status_at)

		""" The number of favorites displayed no longer includes offline channels.
		i.e. setting this value to n will display - in descending order of time watched,
		the first n ONLINE channels in the database """
		number_of_faves_displayed = input(" Number of favorites to display [5]: ")
		if number_of_faves_displayed == "":
			number_of_faves_displayed = 5
		else:
			number_of_faves_displayed = int(number_of_faves_displayed)

		chat_for_MT = input(" Display chat for multiple Twitch streams [y/N]: ")
		if chat_for_MT == "" or chat_for_MT == "N" or chat_for_MT == "n" or chat_for_MT == "no":
			display_chat_for_multiple_twitch_streams = False
		else:
			display_chat_for_multiple_twitch_streams = True

		check_int = input(" Interval (seconds) in between channel status checks [60]: ")
		if check_int == "":
			check_interval = 60
		else:
			check_interval = int(check_int)

		print("\n" + colors.GAMECYAN + " Current Settings:" + colors.ENDC)
		penultimate_check = """ Media Player: {0}
 Default Quality: {1}
 Truncate status at: {2}
 Number of faves: {3}
 Display chat for multiple streams: {4}
 Check interval: {5}""".format(colors.NUMBERYELLOW + player + colors.ENDC, colors.NUMBERYELLOW + default_quality + colors.ENDC, colors.NUMBERYELLOW + str(truncate_status_at) + colors.ENDC, colors.NUMBERYELLOW + str(number_of_faves_displayed) + colors.ENDC, colors.NUMBERYELLOW + str(display_chat_for_multiple_twitch_streams) + colors.ENDC, colors.NUMBERYELLOW + str(check_interval) + colors.ENDC)

		print(penultimate_check)

		do_we_like = input(" Does this look correct to you? [Y/n]: ")
		if do_we_like == "Y" or do_we_like == "yes" or do_we_like == "y" or do_we_like == "":
			options_to_insert = [["player", player], ["mpv_hardware_acceleration", mpv_hardware_acceleration], ["default_quality", default_quality], ["truncate_status_at", truncate_status_at], ["number_of_faves_displayed", number_of_faves_displayed], ["display_chat_for_multiple_twitch_streams", display_chat_for_multiple_twitch_streams], ["check_interval", check_interval]]

			database = sqlite3.connect(database_path)
			if special_occasion == "FirstRun":
				database.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
				database.execute("CREATE TABLE games (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
				database.execute("CREATE TABLE miscellaneous (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")
				database.execute("CREATE TABLE options (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")

			elif special_occasion == "TheDudeAbides":
				database.execute("DELETE FROM options")
				database.execute("VACUUM")

			for i in options_to_insert:
				database.execute("INSERT INTO options (Name,Value) VALUES ('{0}','{1}')".format(i[0], str(i[1])))
			database.commit()
			database.close()
		else:
			raise
	except:
		final_decision = input(colors.OFFLINERED + " Do you wish to restart? [y/N]: " + colors.ENDC)
		if final_decision == "Y" or final_decision == "yes" or final_decision == "y":
			print()
			configure_options(special_occasion)
		else:
			exit()


# Stuff that isn't options. Or optional. Lel.
""" Check for requirements """
if which('livestreamer') is None:
	print(colors.OFFLINERED + " livestreamer " + colors.ENDC + "is not installed. FeelsBadMan.")
	exit()

""" Existential doubts go here """
if not exists(database_path):
	print(colors.GAMECYAN + " First run. Creating db and running configure." + colors.ENDC)
	configure_options("FirstRun")
	exit()
database = sqlite3.connect(database_path)
dbase = database.cursor()

""" Not so existential ones here"""
try:
	options_from_database = dbase.execute("SELECT Value FROM options").fetchall()
	""" Database options scheme:
		0: player
		1: mpv_hardware_acceleration
		2: default_quality
		3: truncate_status_at
		4: number_of_faves_displayed
		5: display_chat_for_multiple_twitch_streams
		6: check_interval """

	player = options_from_database[0][0]
	mpv_hardware_acceleration = literal_eval(options_from_database[1][0])
	default_quality = options_from_database[2][0]
	truncate_status_at = int(options_from_database[3][0])
	number_of_faves_displayed = int(options_from_database[4][0])
	display_chat_for_multiple_twitch_streams = literal_eval(options_from_database[5][0])
	check_interval = int(options_from_database[6][0])
except:
	print(colors.OFFLINERED + " Error getting options. Running --configure:" + colors.ENDC)
	configure_options("TheDudeAbides")
	exit()

""" Set locale for comma placement """
locale.setlocale(locale.LC_ALL, '')


# Functions
def get_options():
	if player == "mpv" and mpv_hardware_acceleration is True:
		player_final = "mpv --hwdec=vaapi --vo=vaapi --cache 8192"
	else:
		player_final = "mpv --cache 8192"
	return player_final, mpv_hardware_acceleration, default_quality, truncate_status_at, display_chat_for_multiple_twitch_streams
	""" Options List Scheme
	0: Video Player
	1: Hardware accel (for mpv) - Boolean
	2: Default player quality
	3: Truncate status
	4: Display chat if Multiple streams are played """


# Display template mapping for extra spicy output
def template_mapping(display_number, called_from):

	third_column = 20
	""" Preceding specification is mostly pointless as long as it's non zero """

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
	elif called_from == "vods":
		first_column = 40
		second_column = 60

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
		time_converted = "%dd %dh %dm" % (d, h, m)
	elif h > 0:
		time_converted = "%dh %dm" % (h, m)
	elif m > 0:
		time_converted = "%dm" % m
	else:
		time_converted = "%ds" % s

	return time_converted


# Emotes - Kappa? Kappa.
def emote(whatzisface):
	kappa = (
		" ░░░░░░░░░░░░░░░░░░░░\n"
		" ░░░░▄▀▀▀▀▀█▀▄▄▄▄░░░░\n"
		" ░░▄▀▒▓▒▓▓▒▓▒▒▓▒▓▀▄░░\n"
		" ▄▀▒▒▓▒▓▒▒▓▒▓▒▓▓▒▒▓█░\n"
		" █▓▒▓▒▓▒▓▓▓░░░░░░▓▓█░\n"
		" █▓▓▓▓▓▒▓▒░░░░░░░░▓█░\n"
		" ▓▓▓▓▓▒░░░░░░░░░░░░█░\n"
		" ▓▓▓▓░░░░▄▄▄▄░░░▄█▄▀░\n"
		" ░▀▄▓░░▒▀▓▓▒▒░░█▓▒▒░░\n"
		" ▀▄░░░░░░░░░░░░▀▄▒▒█░\n"
		" ░▀░▀░░░░░▒▒▀▄▄▒▀▒▒█░\n"
		" ░░▀░░░░░░▒▄▄▒▄▄▄▒▒█░\n"
		" ░░░▀▄▄▒▒░░░░▀▀▒▒▄▀░░\n"
		" ░░░░░▀█▄▒▒░░░░▒▄▀░░░\n"
		" ░░░░░░░░▀▀█▄▄▄▄▀░░░░\n")

	print("\n" + kappa)


# Add to database. Call with "-a" or "-s". Haha I said ass.
def add_to_database(channel_input):
	final_addition_streams = []

	def final_addition(final_addition_input):
		something_added = False
		print(" " + colors.NUMBERYELLOW + "Additions to database:" + colors.ENDC)
		for channel_name in final_addition_input:
			does_it_exist = dbase.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_name.lower()).fetchone()
			if does_it_exist is None:
				something_added = True
				database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name.lower())
				print(" " + channel_name)
		database.commit()
		if something_added is False:
			print(" " + colors.OFFLINERED + "None" + colors.ENDC)

	if sys.argv[1] == "-s":
		username = channel_input[0]
		r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels' % username, headers=http_header)
		stream_data = json.loads(r.text)

		try:
			total_followed = stream_data['_total']
			r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels?limit=%s' % (username, str(total_followed)), headers=http_header)
			stream_data = json.loads(r.text)
			for i in range(0, total_followed):
				final_addition_streams.append(stream_data['follows'][i]['channel']['name'].lower())
			final_addition(final_addition_streams)
		except:
			print(" " + username + " doesn't exist")

	if sys.argv[1] == "-a":
		for names_for_addition in channel_input:
			r = requests.get('https://api.twitch.tv/kraken/streams/' + names_for_addition, headers=http_header)
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
def read_modify_deletefrom_database(channel_input, whatireallywant_ireallyreallywant):
	if whatireallywant_ireallyreallywant == "ItsHammerTime":
		table_wanted = "channels"
	else:
		table_wanted = input(" Modify (s)treamer or (g)ame name? ")
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
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], colors.GAMECYAN + str(i[2]) + colors.OFFLINERED, "  Unwatched" + colors.ENDC))
			else:
				time_watched = time_convert(i[1]).rjust(11)
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], colors.GAMECYAN + str(i[2]) + colors.ENDC, time_watched))
		else:
			if table_wanted == "channels":
				template = template_mapping(display_number, "listnocolor")
			elif table_wanted == "games":
				template = template_mapping(display_number, "gameslistnocolor")

			if i[1] == 0:
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.OFFLINERED + " " + template.format(i[0], str(i[2]), "  Unwatched") + colors.ENDC)
			else:
				time_watched = time_convert(i[1]).rjust(11)
				print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], str(i[2]), time_watched))
		display_number = display_number + 1

	final_selection = input(" Stream / Channel number(s)? ")

	if sys.argv[1] == "-d":
		try:
			print(" " + colors.NUMBERYELLOW + "Deleted from database:" + colors.ENDC)
			entered_numbers = [int(i) for i in final_selection.split()]
			for j in entered_numbers:
				print(" " + relevant_list[j - 1][0])
				database.execute("DELETE FROM '{0}' WHERE Name = '{1}'".format(table_wanted, relevant_list[j - 1][0]))
			database.commit()
			database.close()
		except IndexError:
			print(colors.OFFLINERED + " How can columns be real if our databases aren\'t real?" + colors.ENDC)

	if sys.argv[1] == "-an":
		try:
			old_name = relevant_list[int(final_selection) - 1][0]
			new_name = input(" Replace " + old_name + " with? ")

			if new_name == "":
				database.execute("UPDATE '{0}' SET AltName = NULL WHERE Name = '{1}'".format(table_wanted, old_name))
			else:
				database.execute("UPDATE '{0}' SET AltName = '{1}' WHERE Name = '{2}'".format(table_wanted, new_name, old_name))
			database.commit()
			database.close()
		except IndexError:
			print(colors.OFFLINERED + " OH MY GOD WHAT IS THAT BEHIND YOU?" + colors.ENDC)

	if sys.argv[1] == "-n":
		watch_list = []
		try:
			entered_numbers = [int(i) for i in final_selection.split()]
			watch_list = [relevant_list[j - 1][0] for j in entered_numbers]
		except:
			print(colors.OFFLINERED + " Yerr a wizard, \'arry" + colors.ENDC)
			exit()

		if len(watch_list) == 0:
			exit()
		print(" " + colors.NUMBERYELLOW + "Now monitoring:" + colors.ENDC)
		watch_list = list(set(watch_list))
		watch_list.sort()
		print(colors.TEXTWHITE + " " + ", ".join(watch_list) + colors.ENDC)
		vigilo_confido(watch_list)


# Watches channels into the night. Like a silent protector.
def vigilo_confido(monitor_deez):
	player = get_options()[0]

	channel_list_conky = ", ".join(monitor_deez)
	database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % ("BellatorInMachina", channel_list_conky))
	database.commit()

	try:
		while len(monitor_deez) > 0:
			channel_list = ",".join(monitor_deez)
			r = requests.get('https://api.twitch.tv/kraken/streams/' + "?limit=100" + "&channel=" + channel_list, headers=http_header)
			stream_data = json.loads(r.text)
			total = stream_data['_total']

			for i in range(0, total):
				channel_name = stream_data['streams'][i]['channel']['name']
				print(" " + colors.ONLINEGREEN + channel_name + colors.ENDC + " online @ " + strftime('%H:%M'), end='')
				monitor_deez.remove(channel_name)

				channel_list_conky = ", ".join(monitor_deez)
				database.execute("UPDATE miscellaneous set Value = '%s' WHERE Name = 'BellatorInMachina'" % (channel_list_conky))
				database.commit()

				if len(channel_list_conky) > 0:
					print(" | Waiting for: " + colors.TEXTWHITE + channel_list_conky + colors.ENDC)
				else:
					print()

				if player == "vlc":
						player = "cvlc"

				if which('notify-send') is not None:
					args_to_subprocess = "notify-send --urgency=critical -i \'dialog-information\' \'Twitchy\' \'{0} is online\'".format(channel_name)
					args_to_subprocess = shlex.split(args_to_subprocess)
					subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

				script_dir = dirname(realpath(__file__))
				args_to_subprocess = "{0} {1}/alarm.mp3".format(player, script_dir)
				args_to_subprocess = shlex.split(args_to_subprocess)
				subprocess.run(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

			if len(monitor_deez) > 0:
				sleep(check_interval)

		database.execute("DELETE FROM miscellaneous")
		database.execute("VACUUM")
	except KeyboardInterrupt:
		database.execute("DELETE FROM miscellaneous")
		database.execute("VACUUM")

	database.close()
	exit()


# Much VOD such wow
def vod_watch(channel_input):
	channel_input = channel_input[0]
	i_wanna_see = input(" Watch (b)roadcasts or (h)ighlights: ")

	broadcast_string = ""
	if i_wanna_see == "b":
		broadcast_string = "?broadcasts=true"

	r = requests.get('https://api.twitch.tv/kraken/channels/{0}/videos{1}'.format(channel_input, broadcast_string), headers=http_header)
	stream_data = json.loads(r.text)

	try:
		totalvids = str(stream_data['_total'])
		if int(totalvids) == 0:
			raise
	except:
		print(colors.OFFLINERED + " Channel does not exist or No VODs found." + colors.ENDC)
		exit()

	display_name = stream_data['videos'][0]['channel']['display_name']

	""" Default to source quality in case the channel is not a Twitch partner """
	p = requests.get('https://api.twitch.tv/kraken/channels/' + channel_input, headers=http_header)
	stream_data_partner = json.loads(p.text)
	ispartner = stream_data_partner['partner']
	if ispartner is False:
		default_quality = "source"
		display_name_show = display_name + "*"
	else:
		default_quality = get_options()[2]
		display_name_show = display_name

	if broadcast_string == "":
		limit_string = "?limit=" + totalvids
		print(" Highlights for " + colors.NUMBERYELLOW + display_name_show + colors.ENDC + ":")
	else:
		limit_string = "&limit=" + totalvids
		print(" Past broadcasts for " + colors.NUMBERYELLOW + display_name_show + colors.ENDC + ":")

	r = requests.get('https://api.twitch.tv/kraken/channels/{0}/videos{1}{2}'.format(channel_input, broadcast_string, limit_string), headers=http_header)
	stream_data = json.loads(r.text)

	vod_links = []
	display_number = 1
	for i in stream_data['videos']:
		template = template_mapping(display_number, "vods")
		creation_time = i['created_at'].split('T')[0]
		video_title = i['title']
		if len(video_title) > 55:
			video_title = i['title'][:55] + "..."
		if i_wanna_see == "b":
			print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i['game'], video_title, creation_time))
		else:
			print(" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(video_title, creation_time, ""))
		vod_links.append([i['url'], i['title']])
		display_number = display_number + 1

	vod_select = int(input(" VOD number: "))
	video_final = vod_links[vod_select - 1][0]
	player_final = get_options()[0] + " --title " + "\"" + display_name + " - " + vod_links[vod_select - 1][1] + "\""

	database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % (display_name + " - " + vod_links[vod_select - 1][1], "(VOD)"))
	database.commit()

	print(" Now watching " + colors.TEXTWHITE + display_name + " - " + vod_links[vod_select - 1][1] + colors.ENDC + " | Quality: " + colors.TEXTWHITE + default_quality.title() + colors.ENDC)
	args_to_subprocess = "livestreamer {0} {1} --player '{2}' --hls-segment-threads 3 --player-passthrough=hls --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(video_final, default_quality, player_final)
	args_to_subprocess = shlex.split(args_to_subprocess)
	subprocess.run(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	database.execute("DELETE FROM miscellaneous")
	database.execute("VACUUM")

	database.close()
	exit()


# Generate stuff for livestreamer to agonize endless over. Is it fat? It's a program so no.
def watch(channel_input):

	try:
		if sys.argv[1] == "-s" or sys.argv[1] == "-v":
			print(colors.OFFLINERED + " Only one argument is permitted." + colors.ENDC)
			exit()
	except IndexError:
		pass

	database.row_factory = lambda cursor, row: row[0]
	dbase = database.cursor()

	try:
		if sys.argv[1] == "--conky":
			pass
		else:
			raise
	except:
		print(" " + colors.NUMBERYELLOW + "Checking channels..." + colors.ENDC)

	if channel_input == "BlankForAllIntensivePurposes":
		status_check_required = dbase.execute('SELECT Name FROM channels').fetchall()
		altname_list = dbase.execute('SELECT AltName FROM channels').fetchall()

	elif sys.argv[1] == "-w":
		status_check_required = channel_input
		altname_list = []
		for j in channel_input:
			altname_list.append(dbase.execute("SELECT AltName FROM channels WHERE Name = '%s'" % j).fetchone())

	elif sys.argv[1] == "-f":
		status_check_required = dbase.execute("SELECT Name FROM channels WHERE TimeWatched > 0").fetchall()
		altname_list = dbase.execute("SELECT AltName FROM channels WHERE TimeWatched > 0").fetchall()
		timewatched_list = dbase.execute("SELECT TimeWatched FROM channels WHERE TimeWatched > 0").fetchall()

	else:
		status_check_required = database.execute("SELECT Name FROM channels WHERE Name LIKE '{0}' or AltName LIKE '{1}'".format(('%' + channel_input + '%'), ('%' + channel_input + '%'))).fetchall()
		altname_list = database.execute("SELECT AltName FROM channels WHERE Name LIKE '{0}' or AltName LIKE '{1}'".format(('%' + channel_input + '%'), ('%' + channel_input + '%'))).fetchall()

	stream_status = []

	def get_status(status_check_required):
		number_of_checks = len(status_check_required)

		channel_list = ",".join(status_check_required)
		r = requests.get('https://api.twitch.tv/kraken/streams/' + "?limit=" + str(number_of_checks) + "&channel=" + channel_list, headers=http_header)
		stream_data = json.loads(r.text)
		total = stream_data['_total']

		for i in range(0, total):
			channel_name = stream_data['streams'][i]['channel']['name']

			game_name_formatted = str(stream_data['streams'][i]['channel']['game']).replace("\'", "")

			truncate_status_at = get_options()[3]
			status_message = str(stream_data['streams'][i]['channel']['status'])
			if len(status_message) > truncate_status_at:
				status_message = status_message[0:truncate_status_at - 3] + "..."

			alt_name = altname_list[status_check_required.index(channel_name)]
			if alt_name is None:
				alt_name = stream_data['streams'][i]['channel']['display_name']

			timewatched = 0
			try:
				if sys.argv[1] == "-f":
					timewatched = timewatched_list[status_check_required.index(channel_name)]
			except:
				pass

			stream_status.append([channel_name, game_name_formatted, status_message, stream_data['streams'][i]['viewers'], alt_name, stream_data['streams'][i]['channel']['partner'], timewatched])
			""" List Scheme
			0: Channel name
			1: Game name
			2: Status message
			3: Viewers
			4: Display name
			5: Partner status - Boolean
			6: Time Watched - Should be zero if not explicitly queried"""

	get_status(status_check_required)

	""" Return online channels for conky
	Terminate the watch() function """
	try:
		if sys.argv[1] == "--conky":
			output = ""
			for i in stream_status:
				if sys.argv[2] == "go":
					output = i[4] + ", " + output
				else:
					""" The omission of the space is intentional """
					output = i[0] + "," + output
			output = output.strip()[:-1]
			return output
	except:
		pass

	""" Continuation of the standard watch() function """
	if len(stream_status) > 0:
		try:
			if sys.argv[1] == "-f":
				""" The display list is now sorted in descending order """
				stream_status = sorted(stream_status, key=lambda x: x[6], reverse=True)

				""" Get ranks to display for -f """
				names_only = []
				database2 = sqlite3.connect(database_path)
				all_seen = database2.execute("SELECT TimeWatched,Name FROM channels WHERE TimeWatched > 0").fetchall()
				database2.close()
				all_seen.sort(reverse=True)
				names_only = [el[1] for el in all_seen]
			else:
				raise
		except:
			stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
	else:
		print(colors.OFFLINERED + " All channels offline" + colors.ENDC)
		exit()

	stream_final = []
	games_shown = []
	display_number = 1

	for i in stream_status:
		display_name_game = dbase.execute("SELECT AltName FROM games WHERE Name = '%s'" % i[1]).fetchone()
		if display_name_game is None:
			display_name_game = i[1]

		if i[5] is True:
			display_name_strimmer = i[4]
		else:
			display_name_strimmer = i[4] + "*"

		stream_final.insert(display_number - 1, [i[0], i[1], i[4], i[5]])
		""" List scheme
		0: Channel Name
		1: Game Name
		2: Display Name
		3: Partner status - Boolean """
		template = template_mapping(display_number, "watch")

		""" We need special formatting in case of -f """
		try:
			if sys.argv[1] == "-f":
				column_3_display = colors.GAMECYAN + display_name_game + colors.ONLINEGREEN + " - " + i[2]
				rank = str(names_only.index(i[0]) + 1)
				print(" " + colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(display_name_strimmer + " (" + rank + ")", time_convert(i[6]).rjust(11), column_3_display) + colors.ENDC))
				display_number = display_number + 1
				if display_number == number_of_faves_displayed + 1:
					break
			else:
				raise
		except:
			if display_name_game not in games_shown:
				print(" " + colors.GAMECYAN + display_name_game + colors.ENDC)
				games_shown.append(display_name_game)
			print(" " + colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(display_name_strimmer, str(format(i[3], "n")).rjust(8), i[2]) + colors.ENDC))
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
			ispartner = stream_final[int(j[0]) - 1][3]
			if ispartner is True:
				if len(j) == 1:
					final_selection.append([stream_final[int(j[0]) - 1][0], default_quality, stream_final[int(j[0]) - 1][2]])
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
					final_selection.append([stream_final[int(j[0]) - 1][0], custom_quality, stream_final[int(j[0]) - 1][2]])
			elif ispartner is False:
					final_selection.append([stream_final[int(j[0]) - 1][0], "source", stream_final[int(j[0]) - 1][2]])

		if len(final_selection) == 1:
			playtime(final_selection[0][0], final_selection[0][1], stream_final[int(watch_input_final[0][0]) - 1][1], final_selection[0][2])
		elif len(final_selection) > 1:
			multi_twitch(final_selection)
		else:
			""" Random selection - In case only enter is pressed """
			emote("Kappa")
			random_stream = randrange(0, display_number - 1)
			final_selection = stream_final[random_stream][0]
			ispartner = stream_final[random_stream][3]
			if ispartner is True:
				playtime(final_selection, default_quality, stream_final[random_stream][1], stream_final[random_stream][2])
			else:
				playtime(final_selection, "source", stream_final[random_stream][1], stream_final[random_stream][2])
	except (IndexError, ValueError):
		print(colors.OFFLINERED + " Huh? Wut? Lel? Kappa?" + colors.ENDC)


# Stuff to do once we have sufficient data to start livestreamer
def playtime(final_selection, stream_quality, game_name, display_name):
	start_time = time()

	""" Add game name to database after it's been started at least once """
	does_it_exist = dbase.execute("SELECT Name FROM games WHERE Name = '%s'" % game_name).fetchone()
	if does_it_exist is None:
		database.execute("INSERT INTO games (Name,Timewatched,AltName) VALUES ('%s',0,NULL)" % game_name)

	""" For conky output - Populate the miscellaneous table with the display name and start time """
	database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % (display_name, start_time))
	database.commit()
	database.close()

	print(" Now watching " + colors.TEXTWHITE + display_name + colors.ENDC + " | Quality: " + colors.TEXTWHITE + stream_quality.title() + colors.ENDC)

	options = get_options()
	player_final = options[0] + " --title " + display_name.replace(' ', '')

	try:
		webbrowser.get('chromium').open_new('--app=http://www.twitch.tv/%s/chat?popout=' % final_selection)
	except:
		webbrowser.open_new('http://www.twitch.tv/%s/chat?popout=' % final_selection)

	args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3 --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(final_selection, stream_quality, player_final)
	args_to_subprocess = shlex.split(args_to_subprocess)
	livestreamer_process = subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	print(" q / Ctrl + C to quit | m to identify music ")
	while livestreamer_process.returncode is None:
		""" returncode does nothing without polling
		A delay in the while loop is introduced by the select method below """
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

	time_tracking(final_selection, game_name, start_time, display_name)


# Currently a separate function because I might implement time tracking for multiple streams one day
# And also because NO ONE FUNCTION SHOULD HAVE ALL THAT POWER
def time_tracking(channel_input, game_name, start_time, display_name):
	end_time = time()
	time_watched = int(end_time - start_time)

	database = sqlite3.connect(database_path)
	dbase = database.cursor()

	""" Update time watched for a channel that exists in the database (avoids exceptions due to -w) """
	channel_record = dbase.execute("SELECT Name,TimeWatched FROM channels WHERE Name = '%s'" % channel_input).fetchone()
	if channel_record is not None:
		total_time_watched = channel_record[1] + time_watched
		database.execute("UPDATE channels set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, channel_input))

		names_only = []
		all_seen = dbase.execute("SELECT TimeWatched,Name FROM channels WHERE TimeWatched > 0").fetchall()
		all_seen.sort(reverse=True)
		names_only = [el[1] for el in all_seen]
		rank = str(names_only.index(channel_input) + 1)
		print(" Total time spent watching " + colors.TEXTWHITE + display_name + colors.ENDC + ": " + time_convert(total_time_watched) + " (" + rank + ")")

	""" Update time watched for game. All game names will already be in the database. """
	game_details = dbase.execute("SELECT TimeWatched,Name,AltName FROM games WHERE Name = '%s'" % game_name).fetchone()
	total_time_watched = game_details[0] + time_watched
	database.execute("UPDATE games set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, game_name))

	all_seen = dbase.execute("SELECT TimeWatched,Name FROM games WHERE TimeWatched > 0").fetchall()
	all_seen.sort(reverse=True)
	names_only = [el[1] for el in all_seen]
	rank = str(names_only.index(game_name) + 1)
	if game_details[2] is None:
		game_display_name = game_details[1]
	else:
		game_display_name = game_details[2]
	print(" Total time spent watching " + colors.TEXTWHITE + game_display_name + colors.ENDC + ": " + time_convert(total_time_watched) + " (" + rank + ")")

	"""For conky output - Truncate table miscellaneous after stream ends """
	database.execute("DELETE FROM miscellaneous")
	database.execute("VACUUM")

	database.commit()
	database.close()
	exit()


# Alleged Multi-Twitch.
def multi_twitch(channel_input):
	database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('Multiple420BlazeItChannels','0')")
	database.commit()
	print(" Now watching: ")
	number_of_channels = len(channel_input)
	""" channel_input list scheme:
	0: Channel Name
	1: Stream quality
	2: Display Name """

	def zhu_li_do_the_thing(channel_name, stream_quality, display_name, current_channel):
		player_final = get_options()[0]
		player_final = player_final + " --title " + display_name.replace(' ', '')
		print(" " + colors.TEXTWHITE + display_name + colors.ENDC + " - " + colors.TEXTWHITE + stream_quality.title() + colors.ENDC)

		display_chat = get_options()[4]
		if display_chat is True:
			try:
				webbrowser.get('chromium').open_new('--app=http://www.twitch.tv/%s/chat?popout=' % channel_name)
			except:
				webbrowser.open_new('http://www.twitch.tv/%s/chat?popout=' % channel_name)

		args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3 --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(channel_name, stream_quality, player_final)
		args_to_subprocess = shlex.split(args_to_subprocess)
		if current_channel < (number_of_channels - 1):
			subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			subprocess.run(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	for i in range(0, number_of_channels):
		zhu_li_do_the_thing(channel_input[i][0], channel_input[i][1], channel_input[i][2], i)

	database.execute("DELETE FROM miscellaneous")
	database.execute("VACUUM")

	database.commit()
	database.close()
	exit()


# Update the script to the latest git revision
def update_script():
	print(" " + colors.NUMBERYELLOW + "Checking for update..." + colors.ENDC)
	script_path = realpath(__file__)

	with open(script_path) as script_text:
		the_lines = script_text.readlines()
	current_revision = the_lines[2].replace("\n", '')
	script_text.close()

	script_git_list = []
	script_git = requests.get('https://raw.githubusercontent.com/BasioMeusPuga/twitchy/master/twitchy.py', stream=True)
	for x in script_git.iter_lines():
		script_git_list.append(x)
	git_revision = script_git_list[2].decode("utf-8")

	if current_revision == git_revision:
		print(" " + colors.ONLINEGREEN + "Already at latest revision." + colors.ENDC)
	else:
		script_path = open(realpath(__file__), mode='w')
		script_git = requests.get('https://raw.githubusercontent.com/BasioMeusPuga/twitchy/master/twitchy.py', stream=True)
		script_path.write(script_git.text)
		print(" " + colors.ONLINEGREEN + "Updated to Revision" + git_revision.split('=')[1] + colors.ENDC)

	exit()


# I hereby declare this the greatest declaration of ALL TIME
def firefly_needed_another_6_seasons(at_least):
	output = "Something has gone horribly, horribly wrong."
	if at_least == "go" or at_least == "gone":
		print(watch("BlankForAllIntensivePurposes"))
		exit()

	database = sqlite3.connect(database_path)
	dbase = database.cursor()

	play_status = dbase.execute("SELECT Name,Value FROM miscellaneous").fetchall()
	number_playing = len(play_status)
	if number_playing == 0:
		exit(1)

	if number_playing == 1:
		now_playing = play_status[0][0]
		if now_playing == "Multiple420BlazeItChannels":
			output = "Multiple streams playing..."
		elif now_playing == "BellatorInMachina":
			output = "(M) " + play_status[0][1]
		else:
			if play_status[0][1] != "(VOD)":
				current_time = int(time())
				start_time = int(float(play_status[0][1]))
				time_watched = str(time_convert(current_time - start_time))
			else:
				time_watched = "(VOD)"

			if at_least == "np":
				output = now_playing
			elif at_least == "tw":
				output = time_watched
			else:
				output = now_playing + " | " + time_watched

	print(output)
	exit()


# Ok. So maybe this one is it.
def nuke_it_from_orbit():
	print("Are you sure you want to remove the database and start over?")
	confirm = input('Please type ' + colors.OFFLINERED + 'KappaKeepoPogChamp' + colors.ENDC + ' to continue: ')
	if confirm == 'KappaKeepoPogChamp':
		remove(database_path)


# Parse CLI input
def main():
	parser = argparse.ArgumentParser(description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help=False)
	parser.add_argument('searchfor', type=str, nargs='?', help='Search for channel name in database', metavar="*searchstring*")
	parser.add_argument('-h', '--help', help='This helpful message', action='help')
	parser.add_argument('-a', type=str, nargs='+', help='Add channel name(s) to database', metavar="", required=False)
	parser.add_argument('-an', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Set/Unset alternate names', metavar="*searchstring*", required=False)
	parser.add_argument('--configure', action='store_true', help='Configure options', required=False)
	parser.add_argument('--conky', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Generate data for conky', metavar="np / tw / go / gone", required=False)
	parser.add_argument('-d', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Delete channel(s) from database', metavar="*searchstring*", required=False)
	parser.add_argument('-f', action='store_true', help='Check if your favorite channels are online', required=False)
	parser.add_argument('-n', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Notify when online', metavar="*searchstring*", required=False)
	parser.add_argument('--reset', action='store_true', help='Start over', required=False)
	parser.add_argument('-s', type=str, nargs=1, help='Sync username\'s followed accounts to local database', metavar="username", required=False)
	parser.add_argument('--update', action='store_true', help='Update to git master', required=False)
	parser.add_argument('-v', type=str, nargs=1, help='Watch VODs', metavar="", required=False)
	parser.add_argument('-w', type=str, nargs='+', help='Watch specified channel(s)', metavar="", required=False)
	args = parser.parse_args()

	if args.searchfor:
		watch(args.searchfor)
	elif args.a:
		add_to_database(args.a)
	elif args.an:
		read_modify_deletefrom_database(args.an, "CantTouchThis")
	elif args.configure:
		configure_options("TheDudeAbides")
	elif args.conky:
		firefly_needed_another_6_seasons(args.conky)
	elif args.d:
		read_modify_deletefrom_database(args.d, "CantTouchThis")
	elif args.f:
		watch("NotReallyNeededSoIHaveToAskYouIfYouCalledYourMotherToday")
	elif args.n:
		read_modify_deletefrom_database(args.n, "ItsHammerTime")
	elif args.reset:
		nuke_it_from_orbit()
	elif args.s:
		add_to_database(args.s)
	elif args.update:
		update_script()
	elif args.v:
		vod_watch(args.v)
	elif args.w:
		watch(args.w)
	else:
		watch("BlankForAllIntensivePurposes")

try:
	main()
except KeyboardInterrupt:
	database.close()
	exit()
