# twitchy
livestreamer wrapper for twitch.tv

This script hopefully fulfills the needs of the discerning git cloner who wants to watch Twitch, hates the CPU utilization of having a browser/flash running, and 
has only a terminal (and the 3 or so required accessory programs) handy.
*Requires livestreamer, sqlite, toilet*

What you get with the script:
* Moderately severe meme support.
* Background monitoring of selected offline channel. Shiny notifications if/when they come online.
* Tracking of most watched channels.
* Music identification hotkey (uses twitchecho.com)
* Sync your followed accounts to a local sqlite database that does not judge you.
* Really fast bash multi-threading using nothing but &. (Kappa)
* A cure for pattern baldness. (Keepo? This feels like a Keepo.)
* Flippable switches in the first few lines of the script.
* Multi Twitch support so rudimentary you'll curse your loincloth wearing ancestors for not thinking of it first.
* The ability to display alternate names for games / streamers. If your happiness is somehow contingent upon displaying "Hearthstone: Heroes of Warcraft" as "Wizard Poker", well, you've come to the right place.

**Usage**

    twitchy [OPTION]
    [ARGUMENTS]                                Launch channel in $video_player_you_have_installed
    -a <channel name>                          Add channel
    -an                                        Set/unset alternate names
    -d                                         Delete channel
    -f                                         List favorites
    -fr                                        Reset time watched
    -h                                         This helpful text
    -n                                         Monitor selected offline channels and send a notification when any one comes online
    -no                                        STOP EVERYTHING
    -s <username>                              Sync followed channels from specified account
    -w <channel name>                          Watch specified channel(s)
    
    When playing:
    m to attempt music identification with twitchecho
    q to quit
    
**Examples**

Using no argument while launching the script will check the status of every channel in the local database:
![alt tag](https://imgur.com/cwdHy7L.png)
    
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
