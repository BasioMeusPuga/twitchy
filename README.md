# twitchy
livestreamer wrapper for twitch.tv

This script hopefully fulfills the needs of the discerning git cloner who wants to watch Twitch, hates the CPU utilization of having a browser/flash running, and 
has only a terminal (and the 3 or so required accessory programs) handy.
*Requires livestreamer, sqlite, toilet*

What you get with the script:
* Moderately severe meme support.
* Tracking of most watched channels.
* Sync your followed accounts to a local sqlite database that does not judge you.
* Really fast bash multi-threading using nothing but &. (Kappa)
* A cure for pattern baldness. (Keepo? This feels like a Keepo.)
* Flippable switches in the first few lines of the script.
* Multi Twitch support so rudimentary you'll curse your loincloth wearing ancestors for not thinking of it first.
* The ability to display alternate names for games / streamers. If your happiness is somehow contingent upon displaying "Hearthstone: Heroes of Warcraft" as "Wizard Poker", well, you've come to the right place.

**Usage**

    twitchy [OPTION]
    [ARGUMENTS]                    Launch channel in mpv
    -a <channel name>              Add channel
    -an                            Set/unset alternate names
    -d                             Delete channel
    -f                             List favorites
    -fr                            Reset time watched
    -h                             This helpful text
    -s <username>                  Sync followed channels from specified account
    -w <channel name>              Watch specified channel(s)
    
**Examples**

Using no argument while launching the script will check the status of every channel in the local database:
![alt tag](https://imgur.com/cwdHy7L.png)

Alternate view with alphabetical sorting - set $sort_by_games != yes on line 11
![alt tag](https://imgur.com/JbP14Xo.png)
    
Add "bobross" to local database:

    $ twitchy -a bobross
    
Display all strings matching *obr*:

    $ twitchy obr
    Checking channels...
    1 bobross                   Creative                                The Joy of Painting Monday Season 7 Marathon #painting...
    2 mariobro                  Sonic: Generations                      #WhereMuhPrincessAt?
    x yobringmeabetterexample                               
    3 flatulentcobra            Wizard Poker                            Playing secret Paladin. Killing a puppy later.
    Channel number (Multiple allowed): 1-h 2-s 3-l

    Custom quality settings: Specify with hyphen next to channel number.
    E.g. <1-h 2-s 3-l> will simultaneously play channel 1 in high quality, 2 in source quality, and 3 in low quality.
    
Watch specified channel(s) - Do not have to be in local database:

    $ twitchy -w northernlion cobaltstreak
    Checking channels...
    x cobaltstreak
    1 northernlion              The Binding of Isaac: Afterbirth        Egg
    Channel number (Multiple allowed): 1
    
*Caveat Emptor: Chat is launched in a chromium window. If you prefer firefox / another browser / the inevitability of being claimed by the void, line 590 (or thereabouts) is where you need to be. Just substitute for firefox / comment it out.*
