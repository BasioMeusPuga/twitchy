#!/usr/bin/env python3
# Playtime class generator module

import time
import shlex
import subprocess
import webbrowser

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
        # TODO Find a way to get a global variable that allows for the
        # checking if multiple streams are being played > show chat
        if Options.chat.enable:
            chat_url = f'http://www.twitch.tv/{self.channel_name}/chat?popout='
            try:
                webbrowser.get('chromium').open_new(f'--app={chat_url}')
            except webbrowser.Error:
                webbrowser.open_new(chat_url)

        # TODO Database correlations

        display_name = self.channel_params['display_name']
        player = Options.video.player_final + f' --title {display_name}'
        quality = Options.quality_map[self.channel_params['quality']]

        args_to_subprocess = f"streamlink twitch.tv/{self.channel_name} {quality} --player '{player}' --hls-segment-threads 3 --player-passthrough=hls"
        args_to_subprocess = shlex.split(args_to_subprocess)

        # Get the time when the stream starts
        self.start_time = time.time()

        self.player_process = subprocess.run(
            args_to_subprocess
        )

incoming_dict = {
    'hsdogdog': {
        'display_name': 'fuckboi',
        'game': 'Hearthstone',
        'quality': 'high',
        'status': 'Dog - The best decks with the chillest dudes',
        'uptime': 24273,
        'viewers': 14701}}

# This class must be instantiated like so
for i in incoming_dict.items():
    a = Playtime(i[0], i[1])
    a.play()