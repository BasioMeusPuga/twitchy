#!/usr/bin/env python3
# Configuration and settings module

import os
import sys
import shutil
import configparser
import collections

location_prefix = os.path.expanduser('~') + '/.config/twitchy3/'
os.makedirs(location_prefix, exist_ok=True)
os.makedirs(location_prefix + 'images', exist_ok=True)

# Runtime Options
# Putting these inside a class makes them not work
# So control the OCPD
print_to_stdout = True
time_tracking = True
vod_mode = False
non_interactive_mode = False
disown = False


class YouAndTheHorseYouRodeInOn(Exception):
    def __init__(self, message):
        self.message = message
        self.print_error()

    def print_error(self):
        # This could be extended to include logging
        print(Colors.RED + self.message + Colors.ENDC)
        exit(1)


class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'


class ConfigInit:
    def __init__(self, for_test=False):
        # Create database and config files
        self.config_path = location_prefix + 'twitchy.cfg'

        self.player = self.default_quality = self.truncate_status_at = None
        self.mt_chat = self.check_interval = None

        if for_test:
            self.write_to_config_file(True)

        if not os.path.exists(self.config_path):
            self.configure_options()
        else:
            with open(self.config_path, 'r') as current_config:
                first_line = current_config.readlines()[0]
            if first_line == '# TEST CONFIG FILE\n' and not sys.argv[0] == 'setup.py':
                os.remove(self.config_path)
                self.configure_options()

    def configure_options(self):
        try:
            # Turns out, we don't actually need a no_default
            yes_default = ['y', 'Y', 'yes', 'YES']

            print(Colors.CYAN + ' Configure:' + Colors.ENDC)

            self.player = input(' Media player [mpv]: ')
            if not shutil.which(self.player):
                if shutil.which('mpv'):
                    self.player = 'mpv'
                else:
                    print(Colors.RED + ' ' + self.player + Colors.ENDC +
                          ' is not in $PATH. Please check if this is what you want.')
                    raise KeyboardInterrupt

            self.default_quality = input(' Default stream quality [low/medium/HIGH/source]: ')
            if (self.default_quality == '' or
                    self.default_quality not in ['low', 'medium', 'source']):
                self.default_quality = 'high'

            try:
                self.truncate_status_at = int(input(' Truncate stream status at [AUTO]: '))
            except ValueError:
                self.truncate_status_at = 0

            try:
                self.check_interval = int(
                    input(' Interval (seconds) in between channel status checks [60]: '))
            except ValueError:
                self.check_interval = 60

            print('\n' + Colors.CYAN + ' Current Settings:' + Colors.ENDC)
            penultimate_check = (
                f' Media player: {Colors.YELLOW + self.player + Colors.ENDC}\n'
                f' Default Quality: {Colors.YELLOW + self.default_quality + Colors.ENDC}\n'
                f' Truncate status at: {Colors.YELLOW + str(self.truncate_status_at) + Colors.ENDC}\n'
                f' Check interval: {Colors.YELLOW + str(self.check_interval) + Colors.ENDC}')
            print(penultimate_check)

            do_we_like = input(' Does this look correct to you? [Y/n]: ')
            if do_we_like == '' or do_we_like in yes_default:
                self.write_to_config_file()

            else:
                raise KeyboardInterrupt

        except KeyboardInterrupt:
            try:
                final_decision = input(
                    Colors.RED +
                    ' Do you wish to restart? [y/N]: ' +
                    Colors.ENDC)
                if final_decision in yes_default:
                    print()
                    self.configure_options()
                else:
                    exit(1)
            except KeyboardInterrupt:
                exit(1)

        except EOFError:
            print('\n', Colors.RED + 'Writing default values' + Colors.ENDC)
            self.player = 'mpv'
            self.default_quality = 'source'
            self.check_interval = 60
            self.truncate_status_at = 0
            self.write_to_config_file()

    def write_to_config_file(self, test_config=False):
        if test_config:
            self.player = 'test_player'
            self.default_quality = 'source'
            self.truncate_status_at = 60
            self.check_interval = 0
            config_header = '# TEST CONFIG FILE\n'
        else:
            config_header = '# Twitchy configuration file\n'

        config_string = (
            '# OPTIONS ARE CASE SENSITIVE\n'
            '\n'
            '[VIDEO]\n'
            f'Player = {self.player}\n'
            '# This is only valid if using mpv.\n'
            '# Valid options are: False, <hw. acceleration method>\n'
            '# Valid methods are: vaapi (Intel), vdpau (Nvidia) etc.\n'
            'MPVHardwareAcceleration = False\n'
            '# Valid options are: low, mid, high, source\n'
            f'DefaultQuality = {self.default_quality}\n'
            '\n'
            '\n'
            '[COLUMNS]\n'
            '# Valid options are: ChannelName, Viewers, Uptime, StreamStatus, GameName\n'
            '# Columns do not auto resize so be gentle with what you use for Column 2\n'
            'Column1 = ChannelName\n'
            'Column2 = Viewers\n'
            'Column3 = StreamStatus\n'
            '\n'
            '\n'
            '[DISPLAY]\n'
            '# Valid options are: 1, 2, 3 or GameName\n'
            'SortBy = GameName\n'
            '# Shows the name of each column in case sorting is not by GameName\n'
            'ColumnNames = True\n'
            '# Set to 0 for auto truncation. Any other positive integer for manual control\n'
            f'TruncateStatus = {self.truncate_status_at}\n'
            f'CheckInterval = {self.check_interval}\n'
            '\n'
            '\n'
            '[COLORS]\n'
            '# Valid colors are: black, gray, white\n'
            '# AND dark(red, green, yellow, blue, magenta, cyan)\n'
            'Numbers = yellow\n'
            'GameName = cyan\n'
            'Column1 = green\n'
            'Column2 = white\n'
            'Column3 = green\n'
            '\n'
            '\n'
            '[CHAT]\n'
            'Enable = True\n'
            '\n'
            '\n'
            '[NON-INTERACTIVE]\n'
            '# Valid options are:\n'
            '# GameName, GameAltName, ChannelName, ChannelAltName, Status, Viewers, Uptime\n'
            'DisplayScheme = GameAltName, GameName, ChannelAltName, ChannelName\n'
            'Delimiter = ,\n')

        with open(self.config_path, 'w') as config_file:
            config_file.write(config_header + config_string)

        if not test_config:
            print(Colors.CYAN +
                  f' Config written to {self.config_path}. Read for additional settings.' +
                  Colors.ENDC)
            exit()

    def remove_config(self):
        os.remove(self.config_path)


class Options:
    def __init__(self):
        self.config_path = location_prefix + 'twitchy.cfg'

        # The class attributes are mostly dictionaries as declared below
        self.video = self.columns = self.display = None
        self.colors = self.chat = self.conky_run = self.quality_map = None
        self.non_int_display_scheme = self.non_int_delimiter = None

    def parse_options(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)

        # Video options
        video_section = config['VIDEO']

        player = video_section.get('Player', 'mpv')
        # Treating this as a string so as to
        # not need another line for the kind of hw. decoding
        hw_accel = video_section.get('MPVHardwareAcceleration', 'false').lower()
        hw_accel_valid = ['false', 'vaapi', 'vdpau']
        if hw_accel not in hw_accel_valid:
            hw_accel = 'false'

        player_final = player
        if player == 'mpv':
            if hw_accel != 'false':
                player_final = 'mpv --hwdec={0} --cache 8192'.format(hw_accel)
            else:
                player_final = 'mpv --cache 8192'

        default_quality = video_section.get('DefaultQuality', 'high')
        if default_quality not in ['low', 'medium', 'high', 'source']:
            default_quality = 'high'

        # Which columns to display
        columns_section = config['COLUMNS']

        # Display options
        display_section = config['DISPLAY']
        sort_by = display_section.get('SortBy', 'GameName')
        if sort_by not in ['1', '2', '3', 'GameName']:
            sort_by = 'GameName'

        truncate_status_at = display_section.getint('TruncateStatus', 0)
        if truncate_status_at == 0:
            truncate_status_at = shutil.get_terminal_size().columns - 44

        # Color selection
        colors_section = config['COLORS']
        numbers = colors_section.get('Numbers', 'yellow')
        game_name = colors_section.get('GameName', 'cyan')
        column1 = colors_section.get('Column1', 'green')
        column2 = colors_section.get('Column2', 'green')
        column3 = colors_section.get('Column3', 'green')

        # Escape codes per color
        escape_codes = {
            'black': '\033[30m',
            'darkgray': '\033[90m',
            'darkred': '\033[31m',
            'red': '\033[91m',
            'darkgreen': '\033[32m',
            'green': '\033[92m',
            'darkyellow': '\033[33m',
            'yellow': '\033[93m',
            'darkblue': '\x1b[0;34;40m',
            'blue': '\033[94m',
            'darkmagenta': '\033[35m',
            'magenta': '\033[95m',
            'darkcyan': '\033[36m',
            'cyan': '\033[96m',
            'gray': '\033[37m',
            'white': '\033[97m',
            'end': '\033[0m'}

        # When to display chat
        chat_section = config['CHAT']

        # How to display data in non-interactive operation
        non_interactive = config['NON-INTERACTIVE']
        display_scheme = non_interactive.get(
            'DisplayScheme', ('GameName', 'GameAltName', 'ChannelName', 'ChannelAltName'))
        display_scheme = display_scheme.replace(' ', '').split(',')
        delimiter = non_interactive.get('Delimiter', ',')

        try:
            Columns = collections.namedtuple(
                'Columns',
                ['column1', 'column2', 'column3'])
            self.columns = Columns(
                columns_section.get('Column1', 'ChannelName'),
                columns_section.get('Column2', 'Viewers'),
                columns_section.get('Column3', 'StreamStatus'))

            Video = collections.namedtuple(
                'Video',
                ['default_quality', 'player_final'])
            self.video = Video(
                default_quality,
                player_final)

            Display = collections.namedtuple(
                'Display',
                ['sort_by', 'column_names', 'truncate_status', 'check_interval'])
            self.display = Display(
                sort_by,
                display_section.getboolean('ColumnNames', False),
                truncate_status_at,
                display_section.getint('CheckInterval', 60))

            Colors = collections.namedtuple(
                'Colors',
                ['numbers', 'game_name', 'column1', 'column2', 'column3'])
            self.colors = Colors(
                escape_codes[numbers],
                escape_codes[game_name],
                escape_codes[column1],
                escape_codes[column2],
                escape_codes[column3])

            Chat = collections.namedtuple(
                'Chat',
                ['enable'])
            self.chat = Chat(
                chat_section.getboolean('Enable', True))

            # Required only at runtime in case values for a conky instance are needed
            self.conky_run = False

            self.quality_map = {
                'low': '360p',
                'medium': '480p',
                'high': '720p',
                'source': 'best'}

            self.non_int_display_scheme = display_scheme
            self.non_int_delimiter = delimiter

        except KeyError:
            print(Colors.RED +
                  ' Error getting options. Running --configure:' +
                  Colors.ENDC)
            gen_config = ConfigInit()
            gen_config.configure_options()
