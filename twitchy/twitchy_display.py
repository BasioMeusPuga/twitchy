#!/usr/bin/env python3
# Table display and selection module

import locale
import random

from twitchy import twitchy_config
from twitchy.twitchy_config import Colors

Options = twitchy_config.Options()
Options.parse_options()

# Set locale for comma placement
locale.setlocale(locale.LC_ALL, '')


# Display template mapping for extra spicy output
def template_mapping(called_from):

    third_column = 1
    # Preceding specification is pointless as long as it's non zero
    # If however, it exceeds the column number of the terminal,
    # we'll get the unenviable free line breaks. That's just silly.

    if called_from == 'list':
        first_column = 30
        second_column = 40
    elif called_from == 'gameslist':
        first_column = 50
        second_column = 55
    elif called_from == 'watch':
        first_column = 25
        second_column = 20
    elif called_from == 'vods':
        first_column = 25
        second_column = 80

    template = '{0:%s}{1:%s}{2:%s}' % (
        first_column, second_column, third_column)
    return template


# Convert time in seconds to a more human readable format
def time_convert(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    # FizzBuzz
    time_converted = ''
    if d > 0:
        time_converted += f'{d}d '
    if h > 0:
        time_converted += f'{h}h '
    if m > 0:
        time_converted += f'{m}m'
    else:
        time_converted = f'{s}s'

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
        ' ░░░░░░░░▀▀█▄▄▄▄▀░░░░')

    print(kappa)


def get_selection(mode, table_max_val):
    # Returns whatever the user selects at the relevant prompt
    # Modes are 'online_channels' and 'database'

    try:
        channel_selection = input(' Number? ')

        # Whatever is selected is passed to this list
        # This is then iterated upon to get the list of parameters
        # that will be passed back to the parent function
        final_selection = []

        entered_numbers = channel_selection.split()
        if not entered_numbers:
            # Everything should error out in case a null selection is
            # made when we're operating purely with database values
            # Otherwise, we're going for a random selection
            # with default quality video
            if mode == 'database':
                raise ValueError
            elif mode == 'online_channels':
                final_selection = [[
                    random.randrange(0, table_max_val),
                    Options.video.default_quality]]
                emote()
                return final_selection

        else:
            quality_dict = {
                'l': 'low',
                'm': 'medium',
                'h': 'high',
                's': 'source'}

            entered_numbers = [i.split('-') for i in entered_numbers]
            for i in entered_numbers:
                if int(i[0]) > table_max_val:
                    raise IndexError

                try:
                    selected_quality = quality_dict[i[1]]
                except (KeyError, IndexError):
                    # Anything that has a valid digit that prefixes it
                    # is started at the default_quality
                    selected_quality = Options.video.default_quality

                final_selection.append([
                    int(i[0]) - 1,
                    selected_quality])

            return final_selection

    except (IndexError, ValueError):
        print(Colors.RED + ' Invalid input.' + Colors.ENDC)
        exit(1)
    except (KeyboardInterrupt, EOFError):
        print()
        exit(1)


class GenerateWatchTable():
    # Applies to the watch functions
    # Will wait for an input and return it to the function
    # that called it

    def __init__(self, table_data_incoming):
        self.table_data_incoming = table_data_incoming
        self.item_count = None
        self.display_list = None

    def table_display(self, display_list):
        # Accepts a list containg the first, second, and third
        # columns. These are shown according to formatting guidance
        # from the other functions in this class
        # The self.display_list also has a [3] that corresponds to relational
        # parameters that will be used at the time of selection

        # It's worth remembering that sorting is case sensitive
        # Goodbye, one little bit of my sanity

        self.display_list = display_list
        if Options.display.sort_by == 'GameName':
            # The lambda function is of critical importance since
            # it decides how the display will actually go
            # The - in the lambda implies sorting is by reverse
            # A negative value is only applicable to integers
            self.display_list.sort(
                key=lambda x: (x[3]['game_display_name'].lower(), -x[3]['viewers']))
            previous_game = None

        else:
            sorting_column_index = int(Options.display.sort_by) - 1
            self.display_list.sort(
                key=lambda x: x[sorting_column_index].lower())

        template = template_mapping('watch')
        list_digits = len(str(len(display_list)))

        for count, i in enumerate(self.display_list):

            # If sorting is by GameName, print only the
            # name of every game that's mentioned for the first time
            if Options.display.sort_by == 'GameName':
                current_game = i[3]['game_display_name']
                if previous_game != current_game:
                    previous_game = current_game
                    print(
                        ' ' +
                        Options.colors.game_name +
                        current_game)

            print(
                ' ' +
                Options.colors.numbers + str(count + 1).rjust(list_digits) +
                ' ' +
                template.format(
                    Options.colors.column1 + i[0],
                    Options.colors.column2 + i[1].rjust(8),
                    Options.colors.column3 + i[2]) +
                Colors.ENDC)

    def begin(self):
        # self.table_data_incoming is the bog standard dictionary that
        # will be iterated upon
        # Since columns are selectable, the table will have to be built
        # for each channel here
        # Valid options are: ChannelName, Viewers, Uptime, StreamStatus, GameName
        final_columns = []
        for i in self.table_data_incoming.items():

            game_display_name = i[1]['game_display_name']
            display_columns = []
            for j in Options.columns:

                if j == 'ChannelName':
                    add_this = i[1]['display_name']

                elif j == 'Viewers':
                    # Convert the number of viewers into a string
                    # formatted by an appropriately placed comma
                    add_this = str(format(i[1]['viewers'], 'n'))

                elif j == 'Uptime':
                    # Convert the uptime into H:M:S
                    add_this = time_convert(i[1]['uptime'])

                elif j == 'StreamStatus':
                    add_this = i[1]['status']
                    if len(add_this) > Options.display.truncate_status:
                        add_this = add_this[:Options.display.truncate_status] + '...'

                elif j == 'GameName':
                    if game_display_name:
                        add_this = game_display_name

                display_columns.append(add_this)

            # At [3] in display_columns, is a dictionary containg both
            # the (alternate) game_name as well as the real channel name
            if not game_display_name:
                game_display_name = i[1]['game']
            relational_params = {
                'name': i[0],
                'viewers': i[1]['viewers'],
                'game_display_name': game_display_name}

            display_columns.append(relational_params)
            final_columns.append(display_columns)

        self.table_display(final_columns)
        final_selection = get_selection(
            'online_channels', len(self.table_data_incoming))

        # Generate the final selection dictionary
        # Its keys are the names of the channels
        # Corresponding values are channel params
        # Channel quality is inserted as a value on the basis
        # of its selection from the relevant function
        selected_channels = {}
        for i in final_selection:
            channel_name = self.display_list[i[0]][3]['name']
            selected_channels[channel_name] = self.table_data_incoming[channel_name]
            selected_channels[channel_name]['quality'] = i[1]

        return selected_channels


class GenerateDatabaseTable:
    # Applies to functions that deal with the database
    def __init__(self, table_data_incoming, table):
        self.table_data_incoming = table_data_incoming
        self.table = table

    def table_display(self, display_list):
        # self.table_data_incoming is a list of tuples
        # Indices
        # 0: Channel name
        # 1: Time Watched
        # 2: Alt Name

        if self.table == 'channels':
            template = template_mapping('list')
        elif self.table == 'games':
            template = template_mapping('gameslist')

        # Sort by Time watched and then by channel name
        display_list.sort(key=lambda x: x[0])

        list_digits = len(str(len(display_list)))
        for count, i in enumerate(display_list):

            # Display colors in case of specific value ranges only
            row_color2 = Colors.ENDC

            if i[1] == 0:
                time_watched = Colors.RED + ' Unwatched'
            else:
                time_watched = time_convert(i[1]).rjust(10)

            alt_name = i[2]
            if alt_name:
                row_color2 = Colors.CYAN
                time_watched = ' ' + time_watched

            print(
                ' ' +
                Options.colors.numbers + str(count + 1).rjust(list_digits) +
                Colors.ENDC +
                ' ' +
                template.format(
                    i[0],
                    row_color2 + str(alt_name),
                    Colors.ENDC + time_watched) +
                Colors.ENDC)

    def begin(self):

        self.table_display(self.table_data_incoming)
        final_selection = get_selection(
            'database', len(self.table_data_incoming))

        # A double 0 index is required because we're reusing the
        # get_selection function. This also returns the default quality
        # setting in case of selection of a list of numbers
        return_list = [
            self.table_data_incoming[i[0]][0] for i in final_selection]

        return return_list

class GenerateVODTable:
    def __init__(self, vod_data):
        self.vod_data = vod_data

    def table_display(self, display_list):
        template = template_mapping('vods')
        list_digits = len(str(len(display_list)))
        for count, i in enumerate(display_list):

            print(
                ' ' +
                Options.colors.numbers + str(count + 1).rjust(list_digits) +
                Colors.ENDC +
                ' ' +
                template.format(i[0], i[1], ''))

    def begin(self):
        self.table_display(self.vod_data)
        final_selection = get_selection(
            'database', len(self.vod_data))

        return_list = [
            [self.vod_data[i[0]][1], self.vod_data[i[0]][2]] for i in final_selection]

        return return_list
