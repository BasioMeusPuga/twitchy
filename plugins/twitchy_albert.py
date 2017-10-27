# -*- coding: utf-8 -*-

"""twitchy plugin for albert
Works only in the default
config for --non-interactive.
Goes into:
/usr/share/albert/org.albert.extension.python/modules"""

import subprocess
from albertv0 import *

__iid__ = "PythonInterface/v0.1"
__prettyname__ = "Twitchy"
__version__ = "1.0"
__trigger__ = "tw "
__author__ = "BasioMeusPuga"
__dependencies__ = []

icon = iconLookup('gnome-twitch')
if not icon:
    icon = ":python_module"


def get_channel_list():
    channels = subprocess.Popen(
        'twitchy --non-interactive go',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    channels_stdout = channels.stdout.readlines()
    channels_list = [
        i.decode('utf-8').replace('\n', '').split(',') for i in channels_stdout]

    return channels_list


online_channels = get_channel_list()


def handleQuery(query):
    results = []
    if query.isTriggered:
        args = query.string.split()
        args_num = len(args)

        if args_num > 1:
            item = Item(id=__prettyname__, icon=icon, completion=query.rawString)
            item.text = 'Too many arguments'
            item.subtext = 'Twitchy takes only one argument in this mode'
            results.append(item)
        else:
            matching = {}
            if args_num == 1:
                search_term = query.string
            elif args_num == 0:
                search_term = ''

            for i in online_channels:
                for j in i:
                    if search_term.lower() in j.lower():
                        matching[i[2]] = {
                            'game_display_name': i[1],
                            'channel_display_name': i[3]}

            for k in matching.items():

                my_text = k[1]['channel_display_name']
                my_subtext = k[1]['game_display_name']
                my_action = [ProcAction(
                    text="ProcAction",
                    commandline=["twitchy", "--non-interactive", "kickstart", k[0]],
                    cwd="~")]
                item = Item(
                    id=__prettyname__,
                    icon=icon,
                    completion=query.rawString,
                    text=my_text,
                    subtext=my_subtext,
                    actions=my_action)
                results.append(item)

        return results
