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
options = twitchy_config.Options()
options.parse_options()

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

def generate_table(table_data_incoming):
    # Universal function for generating tables
    # Applies to -d, -an, -n, and all the watch functions
    # Will wait for an input and return it to the function
    # that called it
    # Expects to take guidance from template_mapping() and emote()

    # We will be iterating over the display_dict dictionary
    # This is an Ordered dictionary
    # The lambda function is of critical importance since
    # it decides how the display will actually go
    # TODO Correlate the lamba function with Options

    display_dict = collections.OrderedDict(sorted(
        table_data_incoming.items(),
        key=lambda t: t[1]['game']))

    previous_game = None
    for count, i in enumerate(display_dict.items()):

        # If sorting is by GameName
        current_game = i[1]['game']
        if previous_game != current_game:
            print(Colors.CYAN + current_game)
            previous_game = current_game

        # Actual content of the table
        # TODO Correlate this with the other keys in the dictionary
        # TODO Figure out formatting
        print(
            Colors.YELLOW + str(count + 1),
            Colors.GREEN + i[1]['display_name'] + Colors.ENDC)

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
                options.video['default_quality']]]
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
                except IndexError:
                    selected_quality = options.video['default_quality']

                final_selection.append([
                    int(i[0]) - 1,
                    selected_quality])

        return_dict = collections.OrderedDict()
        for i in final_selection:
            # We'll be getting the relevant channel name from the
            # OrderedDict itself. This requires conversion of
            # the keys iterable into a list
            current = list(display_dict.items())[i[0]]

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
