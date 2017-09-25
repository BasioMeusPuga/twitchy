#!/usr/bin/env python3
# Playtime class generator module

import sys
import time
import shlex
import select
import subprocess
import webbrowser

import twitchy_database
import twitchy_config
from twitchy_config import Colors

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

        # TODO Insert into the database the name of the game here

        display_name = self.channel_params['display_name']
        player = Options.video.player_final + f' --title {display_name}'
        quality = Options.quality_map[self.channel_params['quality']]

        print(' ' + Colors.WHITE +
              self.channel_params['display_name'] + Colors.ENDC +
              ' | ' + Colors.WHITE +
              self.channel_params['quality'].title() + Colors.ENDC)

        args_to_subprocess = f"streamlink twitch.tv/{self.channel_name} {quality} --player '{player}' --hls-segment-threads 3 --player-passthrough=hls"
        args_to_subprocess = shlex.split(args_to_subprocess)

        # Get the time when the stream starts
        self.start_time = time.time()

        self.player_process = subprocess.Popen(
            args_to_subprocess,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def time_tracking(self):
        end_time = time.time()
        time_watched = end_time - self.start_time

        database_instance = twitchy_database.DatabaseFunctions()
        # Even for a non watched channel, the database always has a 0 value associated
        # Therefore, there will be no None returns
        time_watched_channel = database_instance.fetch_data(
            ('TimeWatched',),
            'channels',
            {'Name': self.channel_name},
            'EQUALS')

        time_watched_game = database_instance.fetch_data(
            ('TimeWatched',),
            'games',
            {'Name': self.channel_params['game']},
            'EQUALS')

        print(time_watched_channel, time_watched_game)

def play_instance_generator(incoming_dict):
    playtime_instance = {}
    total_streams = len(incoming_dict)

    print(' q / Ctrl + C to quit \n Now watching:')

    # Create instances of the Playtime class
    for count, i in enumerate(incoming_dict.items()):
        playtime_instance[count] = Playtime(i[0], i[1])
        playtime_instance[count].play()

    playing_streams = [i for i in range(total_streams)]
    while playing_streams:
        for i in playing_streams:
            # process_returncode returns None in case the process is still running
            # It returns 0 in case the process exits without error
            playtime_instance[i].player_process.poll()
            process_returncode = playtime_instance[i].player_process.returncode

            if process_returncode:
                if process_returncode == 1:
                    stream_stdout = playtime_instance[i].player_process.stdout.read(
                        ).decode('utf-8').split('\n')
                    stream_stderr = playtime_instance[i].player_process.stderr.read(
                        ).decode('utf-8').split('\n')

                    all_error = stream_stdout + stream_stderr
                    error_message = [er for er in all_error if 'error:' in er]
                    print(' ' +
                          Colors.RED + playtime_instance[i].display_name
                          + Colors.ENDC +
                          ' (' + error_message[0] + ')')
                else:
                    playing_streams.remove(i)

            # For when the player process is terminated outside the script
            # TODO Why is this being executed?
            # elif not process_returncode:
            #     print(process_returncode)
            #     playtime_instance[i].time_tracking()
            #     playing_streams.remove(i)

        try:
            # The 0.8 is the polling interval for the streamlink process
            keypress, o, e = select.select([sys.stdin], [], [], 0.8)
            if keypress:
                keypress_made = sys.stdin.readline().strip()
                if keypress_made == "q":
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            for i in playing_streams:
                playtime_instance[i].time_tracking()
                playtime_instance[i].player_process.terminate()
            playing_streams.clear()
