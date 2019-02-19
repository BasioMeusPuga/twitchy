# twitchy
CLI streamlink wrapper for twitch.tv

**Requires streamlink, python >= 3.6, python-requests**

This script hopefully fulfills the needs of the discerning git cloner who wants to watch Twitch, and hates the CPU utilization of having a browser/flash running, especially since the current status of hardware accelerated video on Linux browsers is somewhere between non existent and abysmal.

Features:
* Tracking of most watched channels.
* Custom layouts: User adjustable colors and columns
* VOD support
* Sync your followed accounts to a local sqlite database that does not judge you.
* Stream multiple... streams at once.
* Integration with your conky / dmenu / rofi
* The ability to display alternate names for games / streamers. If your happiness is somehow contingent upon displaying "Hearthstone: Heroes of Warcraft" as "Wizard Poker", well, you've come to the right place.

## Installation
1. Clone the repository
2. In the root directory, type:

        $ python setup.py build
        # python setup.py install

3. Launch with `twitchy`

Alternatively, use the AUR package:
https://aur.archlinux.org/packages/twitchy-git

Please delete `~/.config/twitchy3/*` and restart twitchy before reporting any issues.

## Usage

    $ twitchy [ARGUMENT] [OPTIONS]

    [ARGUMENT] to the script is used as a search string for channels in the local database.

    [OPTIONS]
    -h, --help                      This helpful message
    -a <channel name>               Add channel(s)
    -an [*searchstring*]            Set/unset alternate names
    --configure                     Configure options
    -d [*searchstring*]             Delete channel(s) from database
    --non-interactive [go / kickstart]
                                    Generate parsable data for integration elsewhere
    --reset                         Delete everything and start over
    -s <username>                   Sync followed channels from specified account
    -v <channel name>               Watch channel's recorded videos
    -w <channel name>               Watch specified channel(s)

    First run:
    Will create both the database and an editable config file in ~/.config/twitchy3/

    While playing:
    <q / Ctrl + C> to quit

    Run in non-interactive mode. This is useful for integration with dmenu / rofi / conky.
    --non-interactive go            Get customizable comma separated list of channel / game data
    --non-interactive kickstart <>  Start channel directly without asking for confirmation

## Examples

Using no argument while launching the script will check the status of every channel in the local database:
![alt tag](https://i.imgur.com/1Id6J7G.png)

Add channels to local database:

    $ twitchy -a bobross <channel2> <channel3> ...
    $ twitchy -s <your twitch username>

Display all strings matching *obr*:

    $ twitchy obr
    Checking channels...
    Creative
    1 bobross                   80085           The Joy of Painting Monday Season 7 Marathon #painting...
    Sonic: Generations
    2 mariobro                  123             #WhereMuhPrincessAt?
    Wizard Poker
    3 flatulentcobra            6969            Playing secret Paladin. Killing a puppy later.
    Channel number(s): 1-h 2-s 3-l

    Custom quality settings: Specify with hyphen next to channel number.
    E.g. <1-h 2-s 3-l> will simultaneously play
    channel 1 in high quality, 2 in source quality, and 3 in low quality.

Watch specified channel(s) - Do not have to be in local database:

    $ twitchy -w northernlion cobaltstreak
    Checking channels...
    The Binding of Isaac: Afterbirth
    1 northernlion                5757          Egg
    Channel number(s): 1

## Plugins

Thanks to twitchy's `--non-interactive` flag, it is easy to integrate it
with various tools, like the ones below.

### Albert

Supports the excellent [Albert launcher](https://github.com/albertlauncher/albert)
<p align="center">
  <img width="500" height="320" src="https://i.imgur.com/JRp00ie.png">
</p>

Move `twitchy_albert.py` in the `plugins` directory to `/usr/share/albert/org.albert.extension.python/modules`

### Py3status

Supports the excellent [py3status](https://github.com/ultrabug/py3status)
<p align="center">
  <img src="https://user-images.githubusercontent.com/852504/53009602-84416280-3401-11e9-9f95-c2b2ce58f711.png" />
</p>

Move `twitchy_py3status.py` in the `plugins` directory to somewhere
in your py3status module paths as `twitchy.py`.

### Rofi

Supports a custom [rofi](https://github.com/DaveDavenport/rofi) mode
<p align="center">
  <img width="500" src="http://apetresc-screenshot.s3.amazonaws.com/2018-01-04-23.21.42.png" />
</p>

Move `rofi-twitchy` in the `plugins` directory to somewhere on your
`PATH`, and invoke it with:

```
$ rofi -modi twitchy:rofi-twitchy -show twitchy
```

Of course, you probably want to bind this command to a keyboard shortcut
in your window manager.
