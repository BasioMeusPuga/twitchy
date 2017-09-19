#!/usr/bin/env python3

import locale
import random
import collections

from pprint import pprint

import twitchy_config
from twitchy_config import Colors

# For the love of God, a direct reference to class.method()
# is a direct reference to class.method()
# It will not populate the class attributes for you
# Even if you ask nicely
Options = twitchy_config.Options()
Options.parse_options()

# Set locale for comma placement
locale.setlocale(locale.LC_ALL, '')


# Display template mapping for extra spicy output
def template_mapping(called_from):

    third_column = 20
    # Preceding specification is mostly pointless as long as it's non zero
    # If however, it exceeds the column number of the terminal, we'll get the unenviable
    # free line breaks. That's just silly.

    if called_from == 'list':
        first_column = 25
        second_column = 40
    elif called_from == 'listnocolor':
        first_column = 25
        second_column = 31
    elif called_from == 'gameslist':
        first_column = 50
        second_column = 55
    elif called_from == 'gameslistnocolor':
        first_column = 50
        second_column = 46
    elif called_from == 'watch':
        first_column = 25
        second_column = 20
    elif called_from == 'vods':
        first_column = 40
        second_column = 60

    template = '{0:%s}{1:%s}{2:%s}' % (first_column, second_column, third_column)
    return template


# Convert time in seconds to a more human readable format,
def time_convert(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    if d > 0:
        time_converted = '%dd %dh %dm' % (d, h, m)
    elif h > 0:
        time_converted = '%dh %dm' % (h, m)
    elif m > 0:
        time_converted = '%dm' % m
    else:
        time_converted = '%ds' % s

    return time_converted


# Emotes - Kappa? Kappa.
def emote():
    kappa = (
        ' ░░░░░░░░░░░░░░░░░░░░\n'
        ' ░░░░▄▀▀▀▀▀█▀▄▄▄▄░░░░\n'
        ' ░░▄▀▒▓▒▓▓▒▓▒▒▓▒▓▀▄░░\n'
        ' ▄▀▒▒▓▒▓▒▒▓▒▓▒▓▓▒▒▓█░\n'
        ' █▓▒▓▒▓▒▓▓▓░░░░░░▓▓█░\n'
        ' █▓▓▓▓▓▒▓▒░░░░░░░░▓█░\n'
        ' ▓▓▓▓▓▒░░░░░░░░░░░░█░\n'
        ' ▓▓▓▓░░░░▄▄▄▄░░░▄█▄▀░\n'
        ' ░▀▄▓░░▒▀▓▓▒▒░░█▓▒▒░░\n'
        ' ▀▄░░░░░░░░░░░░▀▄▒▒█░\n'
        ' ░▀░▀░░░░░▒▒▀▄▄▒▀▒▒█░\n'
        ' ░░▀░░░░░░▒▄▄▒▄▄▄▒▒█░\n'
        ' ░░░▀▄▄▒▒░░░░▀▀▒▒▄▀░░\n'
        ' ░░░░░▀█▄▒▒░░░░▒▄▀░░░\n'
        ' ░░░░░░░░▀▀█▄▄▄▄▀░░░░\n')

    print('\n' + kappa)

class GenerateTable():
    def __init__(self, table_data_incoming):
        self.table_data_incoming = table_data_incoming
        self.display_dict = None

    def get_selection(self):
        # Returns whatever the user selects at the relevant prompt
        pass

    def table_display(self, display_list):
        # Accepts a list containg the first, second, and third
        # columns. These are shown according to formatting guidance
        # from the other functions in this class

        # In the following case, we also expect the presence
        # of i[3], the GameName
        # I think this should be passed to this function regardless
        if Options.display.sort_by == 'GameName':
            previous_game = None

        for count, i in enumerate(display_list):

            # If sorting is by GameName, print only the
            # name of every game that's mentioned for the first time
            if Options.display.sort_by == 'GameName':
                current_game = i[3]
                if previous_game != current_game:
                    previous_game = current_game
                    print(Options.colors.game_name + current_game)

            print(
                Options.colors.numbers + str(count + 1) + ' ' +
                Options.colors.column1 + i[0] + ' ' +
                Options.colors.column2 + i[1] + ' ' +
                Options.colors.column3 + i[2] + Colors.ENDC)

    def watch(self):
        # Applies to the watch functions
        # Will wait for an input and return it to the function
        # that called it

        column_dict = {
            'ChannelName': 'display_name',
            'Viewers': 'viewers',
            'Uptime': 'uptime',
            'StreamStatus': 'status',
            'GameName': 'game'}

        # The lambda function is of critical importance since
        # it decides how the display will actually go
        # The - in the lambda implies sorting is by reverse

        # By default, streams are first sorted by the game name (0),
        # and then by the number of viewers (3)
        if Options.display.sort_by == 'GameName':
            sorting_key = lambda t: (t[1]['game'], -t[1]['viewers'])

        # In this case, the integer value of the column is related to the
        # column name and things are sorted accordingly
        else:
            sorting_column_index = int(Options.display.sort_by) - 1
            sorting_column_name = Options.columns[sorting_column_index]
            sorting_key = lambda t: -t[1][column_dict[sorting_column_name]]

        # We will be iterating over the display_dict dictionary
        # This is an Ordered dictionary
        self.display_dict = collections.OrderedDict(sorted(
            self.table_data_incoming.items(),
            key=sorting_key))

        # Since columns are selectable, the table will have to be built
        # for each channel here
        # Valid options are: ChannelName, Viewers, Uptime, StreamStatus, GameName
        final_columns = []
        for i in self.display_dict.items():
            display_columns = []
            for j in Options.columns:
                # Get the name of the required dictionary item from the
                # column_dict declared above
                add_this = i[1][column_dict[j]]

                # Account for special cases
                # TODO Check the database for alternate naming here
                if j == 'Viewers':
                    # Convert the number of viewers into a string
                    # formatted by an appropriately placed comma
                    add_this = str(format(add_this, 'n'))
                elif j == 'Uptime':
                    # Convert the uptime into H:M:S
                    add_this = time_convert(add_this)

                display_columns.append(add_this)

            # In case sorting is by game name, this is expected regardless
            # of what the other columns are
            if Options.display.sort_by == 'GameName':
                display_columns.append(i[1]['game'])

            final_columns.append(display_columns)

        self.table_display(final_columns)
        exit(1)

        try:
            channel_selection = input(' Number? ')

            # Whatever is selected is passed to this list
            # This is then iterated upon to get the list of parameters
            # that will be passed back to the parent function
            final_selection = []

            entered_numbers = channel_selection.split()
            if not entered_numbers:
                final_selection = [[
                    random.randrange(0, count),
                    Options.video.default_quality]]
            else:
                quality_dict = {
                    'l': 'low',
                    'm': 'medium',
                    'h': 'high',
                    's': 'source'}

                entered_numbers = [i.split('-') for i in entered_numbers]
                for i in entered_numbers:
                    try:
                        selected_quality = quality_dict[i[1]]
                    except (KeyError, IndexError):
                        # Anything that has a valid digit that prefixes it
                        # is started at the default_quality
                        selected_quality = Options.video.default_quality

                    final_selection.append([
                        int(i[0]) - 1,
                        selected_quality])

            return_dict = collections.OrderedDict()
            for i in final_selection:
                # We'll be getting the relevant channel name from the
                # OrderedDict itself. This requires conversion of
                # the keys iterable into a list
                current = list(self.display_dict.items())[i[0]]

                # Furthermore, additional relevant data can be inserted into
                # the dictionary at index 1
                # Currently, this includes: quality selection
                current[1]['quality'] = i[1]

                # Populate the dictionary that will be returned to
                # tha parent function
                return_dict[current[0]] = current[1]

            return return_dict

        except (IndexError, ValueError):
            print(Colors.RED + ' Invalid input.' + Colors.ENDC)
            exit(1)
