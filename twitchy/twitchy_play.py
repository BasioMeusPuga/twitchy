#!/usr/bin/env python3
# Playtime class generator module

import os
import sys
import time
import shlex
import select
import subprocess
import webbrowser

from twitchy import twitchy_database
from twitchy import twitchy_config
from twitchy.twitchy_config import Colors
from twitchy.twitchy_display import time_convert

Options = twitchy_config.Options()
Options.parse_options()


class Playtime:
    def __init__(self, channel_name, channel_params):
        # channel_name will come from the dictionary returned
        # from calling the api
        self.channel_name = channel_name
        self.channel_params = channel_params
        self.player_process = None
        self.start_time = None

    def play(self):

        # Display chat in a fresh browser window as a popup
        if Options.chat.enable:
            chat_url = f'http://www.twitch.tv/{self.channel_name}/chat?popout='
            try:
                webbrowser.get('chromium').open_new(f'--app={chat_url}')
            except webbrowser.Error:
                webbrowser.open_new(chat_url)
            except TypeError:
                webbrowser.get('chromium').open_new(f'--app={chat_url}')  # WTF?

        # Insert the name of only started games into the database
        # This keeps the database from getting too cluttered
        display_name = self.channel_params['display_name']
        player = Options.video.player_final
        if player[:3] == 'mpv':
            player += f' --title {display_name}'
        quality = Options.quality_map[self.channel_params['quality']]

        # The following prints to the console
        # If ever there is going to be a curses version
        # it will need to be suppressed
        if twitchy_config.print_to_stdout:
            print(' ' + Colors.WHITE +
                  self.channel_params['display_name'] + Colors.ENDC +
                  ' | ' + Colors.WHITE +
                  self.channel_params['quality'].title() + Colors.ENDC)

        args_to_subprocess = (
            f"streamlink twitch.tv/{self.channel_name} {quality} --player '{player}'")
        hls_settings = ' --hls-segment-threads 3'
        args_to_subprocess = shlex.split(args_to_subprocess + hls_settings)

        # Get the time when the stream starts
        self.start_time = time.time()

        if twitchy_config.non_interactive_mode:
            self.player_process = subprocess.Popen(
                args_to_subprocess,
                preexec_fn=os.setpgrp,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            exit(0)
        else:
            self.player_process = subprocess.Popen(
                args_to_subprocess,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setpgrp)

    def time_tracking(self):
        end_time = time.time()
        time_watched = end_time - self.start_time
        database_instance = twitchy_database.DatabaseFunctions()

        def fetch_time_data():
            # Even for a non watched channel, the database
            # always has a 0 value associated
            # Therefore, there will be no None returns
            time_watched_channel = database_instance.fetch_data(
                ('TimeWatched',),
                'channels',
                {'Name': self.channel_name},
                'EQUALS',
                True)

            time_watched_game = database_instance.fetch_data(
                ('TimeWatched',),
                'games',
                {'Name': self.channel_params['game']},
                'EQUALS',
                True)

            return time_watched_channel, time_watched_game

        time_data = fetch_time_data()

        time_values = {
            'channel_name': self.channel_name,
            'new_time_channel': time_data[0] + time_watched,
            'game_name': self.channel_params['game'],
            'new_time_game': time_data[1] + time_watched}

        database_instance.modify_data(
            'update_time',
            None,
            time_values)

        time_data_new = fetch_time_data()
        game_display_name = self.channel_params['game_display_name']
        if not game_display_name:
            game_display_name = self.channel_params['game']

        channel_rank = get_rank_data('channels', self.channel_name)
        if channel_rank:
            channel_rank = ' (' + channel_rank + ')'

        game_rank = get_rank_data('games', self.channel_params['game'])
        if game_rank:
            game_rank = ' (' + game_rank + ')'

        # Consider shfting this to the main module
        if twitchy_config.print_to_stdout:
            print(
                ' ' + Colors.WHITE +
                self.channel_params['display_name'] + ': ' + Colors.ENDC +
                time_convert(time_data_new[0]) + channel_rank +
                ' | ' + Colors.WHITE +
                game_display_name + ': ' + Colors.ENDC +
                time_convert(time_data_new[1]) + game_rank)


class VOD:
    def __init__(self, display_name, vod_title, vod_url):
        self.display_name = display_name
        self.vod_title = vod_title
        self.vod_url = vod_url
        self.player_process = None

    def play(self):
        player = Options.video.player_final + f' --title {self.display_name}'
        args_to_subprocess = (
            f"streamlink {self.vod_url} best --player '{player}'")
        hls_settings = ' --hls-segment-threads 3 --player-passthrough=hls'
        args_to_subprocess = shlex.split(args_to_subprocess + hls_settings)

        if twitchy_config.print_to_stdout:
            print(' ' + Colors.WHITE +
                  self.display_name + Colors.ENDC +
                  ' | ' + Colors.WHITE +
                  self.vod_title + Colors.ENDC)

        self.player_process = subprocess.Popen(
            args_to_subprocess,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)


def play_instance_generator(incoming_dict):
    playtime_instance = {}

    if not twitchy_config.vod_mode:
        # Create instances of the Playtime class
        for count, i in enumerate(incoming_dict.items()):
            playtime_instance[count] = Playtime(i[0], i[1])
            playtime_instance[count].play()

    else:
        for i in incoming_dict.items():
            display_name = i[0]
            for count, j in enumerate(i[1]):
                playtime_instance[count] = VOD(display_name, j[0], j[1])
                playtime_instance[count].play()

    if twitchy_config.disown:
        exit(0)

    # Time tracking switch
    time_tracking = twitchy_config.time_tracking

    total_streams = count + 1
    playing_streams = [i for i in range(total_streams)]
    while playing_streams:
        for i in playing_streams:
            # process_returncode returns None in case the process is still running
            # It returns 0 in case the process exits without error
            playtime_instance[i].player_process.poll()
            process_returncode = playtime_instance[i].player_process.returncode

            if process_returncode is not None:
                if process_returncode == 1:
                    stream_stdout = playtime_instance[i].player_process.stdout.read().decode(
                        'utf-8').split('\n')
                    stream_stderr = playtime_instance[i].player_process.stderr.read().decode(
                        'utf-8').split('\n')

                    all_error = stream_stdout + stream_stderr
                    error_message = [er for er in all_error if 'error:' in er]
                    print(' ' +
                          Colors.RED + playtime_instance[i].channel_params['display_name'] +
                          Colors.ENDC,
                          ':',
                          error_message)
                elif process_returncode == 0:
                    if time_tracking:
                        playtime_instance[i].time_tracking()
                playing_streams.remove(i)

        try:
            # The 0.8 is the polling interval for the streamlink process
            # The o, e is needed for reasons I don't completely understand
            keypress, o, e = select.select([sys.stdin], [], [], 0.8)
            if keypress:
                keypress_made = sys.stdin.readline().strip()
                if keypress_made == "q":
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            for i in playing_streams:
                if time_tracking:
                    playtime_instance[i].time_tracking()
                playtime_instance[i].player_process.terminate()
            playing_streams.clear()


def get_rank_data(table, name):
    # Returns the rank of the requisite channel or game
    # as a string
    database_instance = twitchy_database.DatabaseFunctions()

    time_and_name = database_instance.fetch_data(
        ('TimeWatched', 'Name'),
        table,
        None,
        'EQUALS')

    time_and_name.sort(reverse=True)
    names_only = [i[1] for i in time_and_name]

    try:
        rank = str(names_only.index(name) + 1)
    except ValueError:
        # In case the provided name is not in the database
        return

    return rank
