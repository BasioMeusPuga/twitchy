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

Usage: 

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
    Custom quality settings: Specify with hyphen next to channel number.
    E.g. <1-l 2-m 4-s> will simultaneously play channel 1 in low quality, 2 in medium quality, and 4 in source quality.
