# -*- coding: utf-8 -*-

"""twitchy plugin for albert
Rules:
1. Configure --non-interactive to include at least
three values. The first one forms the text, the 2nd and 3rd
form the subtext.
2. The last value will have to be the channel name that is
passed back to twitchy
3. Any other values will still be searched, but will be ignored
for the display

Goes into:
/usr/share/albert/org.albert.extension.python/modules"""

import os
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

image_location = os.path.expanduser('~') + '/.config/twitchy3/images/'

def handleQuery(query):

    def get_channel_list():
        # Gets triggered every time there is a change in the query
        # This will exhaust API calls fast
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
                        matching[i[-1]] = {
                            'text': i[0],
                            'subtext1': i[1],
                            'subtext2': i[2]}

            for k in matching.items():

                my_text = k[1]['text']
                my_subtext = k[1]['subtext1'] + " | " + k[1]['subtext2']
                my_action = [ProcAction(
                    text="ProcAction",
                    commandline=["twitchy", "--non-interactive", "kickstart", k[0]],
                    cwd="~")]
                item = Item(
                    id=__prettyname__,
                    icon=image_location + k[0],
                    completion=query.rawString,
                    text=my_text,
                    subtext=my_subtext,
                    actions=my_action)
                results.append(item)

        return results
