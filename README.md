# twitchy
livestreamer / streamlink wrapper for twitch.tv

**Requires livestreamer (or streamlink), python3**

This script hopefully fulfills the needs of the discerning git cloner who wants to watch Twitch, hates the CPU utilization of having a browser/flash running, and has only a terminal handy.

Features:
* Integration with your conky instance.
* Tracking of most watched channels.
* View VODs
* Get notified when a channel you watch comes online
* Music identification (uses twitchecho.com)
* Sync your followed accounts to a local sqlite database that does not judge you.
* Stream as many... streams as you want at once.
* The ability to display alternate names for games / streamers. If your happiness is somehow contingent upon displaying "Hearthstone: Heroes of Warcraft" as "Wizard Poker", well, you've come to the right place.

## Installation
1. Clone the repository
2. Move twitchy.py to $PATH
3. alarm.mp3 should be in the same directory as twitchy.py

Alternatively, use the AUR package:
https://aur.archlinux.org/packages/twitchy-git

## Usage

    $ twitchy [ARGUMENT] [OPTIONS]
    
    [ARGUMENT] to the script is used as a search string for channels in the local database.
    
    [OPTIONS]
    -h, --help                      This helpful message
    -a <channel name>               Add channel(s)
    -an                             Set/unset alternate names
    --configure                     Configure options
    --conky [ go / csvnames ]       Generate data for conky
    -d                              Delete channel(s) from database
    -f                              Check which of your favorite channels are online
    -n                              Notify if a channel comes online
    -s <username>                   Sync followed channels from specified account
    --update                        Update to the latest git revision
    -v <channel name>               Watch channel's recorded videos
    -w <channel name>               Watch specified channel(s)
    
    While playing:
    <m> to attempt music identification with twitchecho
    <q> to quit
    
    Notification settings:
    When a channel comes online, the script will play alarm.mp3 (in the same directory as itself).
    While the path of the file is hardcoded, feel free to replace it with whatever you find (in)appropriate.
    
    Conky options. Execute script with:
    --conky                         Now playing
    --conky go                      Get comma separated list of alternate and formatted channel names
    --conky csvnames                Get comma separated list of channel names from database
    The script will exit with exit code 1 in case either np or tw is used while nothing is playing.
    
## Examples

Using no argument while launching the script will check the status of every channel in the local database:
![alt tag](https://i.imgur.com/1Id6J7G.png)
    
Add "bobross" to local database:

    $ twitchy -a bobross
    
Display all strings matching *obr*:

    $ twitchy obr
    Checking channels...
    Creative
    1 bobross                   80085                       The Joy of Painting Monday Season 7 Marathon #painting...
    Sonic: Generations
    2 mariobro                  123                         #WhereMuhPrincessAt?
    Wizard Poker                               
    3 flatulentcobra            6969                        Playing secret Paladin. Killing a puppy later.
    Channel number(s): 1-h 2-s 3-l

    Custom quality settings: Specify with hyphen next to channel number.
    E.g. <1-h 2-s 3-l> will simultaneously play channel 1 in high quality, 2 in source quality, and 3 in low quality.
    
Watch specified channel(s) - Do not have to be in local database:

    $ twitchy -w northernlion cobaltstreak
    Checking channels...
    The Binding of Isaac: Afterbirth
    1 northernlion                5757                      Egg
    Offline
    x cobaltstreak
    Channel number(s): 1
