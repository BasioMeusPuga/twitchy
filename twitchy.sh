#!/bin/bash
#Requires livestreamer, sqlite, toilet

#Options
database="$HOME/.twitchy.db"
video_player=mpv
quality=medium
truncate_status_at=108
show_offline=no
memes_everywhere=no
meme="RAISE YOUR DONGERS
 E S P O R T S
 DIGITAL ATHLETICS
 CYBERNETIC CALISTHENICS
 IT'S RAINING SALT
 A M E N O
 YOU CAME TO THE WRONG DONGERHOOD
 DUDUDUDUDU
 RELEASE THE KRAKEN
 F E E L S G O O D M A N
 xD xD xD xD xD xD
 I’VE GOT THE STREAM IN MY SIGHTS
 D O N G S Q U A D 4 2 0"

#Sanity checks
 if [[ ! -f /usr/bin/toilet ]]; then
		memes_everywhere=no
	fi

if [[ ! -f "$database" ]]; then
	echo " First run. Creating db and exiting."
	sqlite3 $database "create table channels (id INTEGER PRIMARY KEY,Name TEXT,TimeWatched INTEGER, AltName TEXT);"
	sqlite3 $database "create table games (id INTEGER PRIMARY KEY,Name TEXT,AltName TEXT);"
	exit
fi

rm /tmp/twitchy* 2> /dev/null

#Check status of each stream that meets criteria
function get_status {
	stream[$1]=$(curl -s https://api.twitch.tv/kraken/streams/$line)
	status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep '"stream":null')
		if [[ $status = "" ]]; then
			game_name=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep game | cut -d ":" -f2- | tr -d "\"" | sed -n 1p)
			channel_status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep status | cut -d ":" -f2- | tr -d "\"" | tr -d "%")
			partner=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep partner | cut -d ":" -f2- | tr -d "\"")
			echo $line";"$game_name";"$channel_status";"$partner >> /tmp/twitchyfinal
		else
 			echo $line";offline"  >> /tmp/twitchyfinal
		fi
} &> /dev/null

#Time watched tracking
start_time=0
trap ctrl_c INT
trap ctrl_c EXIT
function ctrl_c() {
	if [[ $run_once != "yes" ]]; then
	end_time=$(date +%s)
	time_watched=$[ $end_time - $start_time ]
    if [[ $final_selection != "" ]] && [[ $start_time != 0 ]]; then
		time_old=$(sqlite3 $database "select TimeWatched from channels where Name = '$final_selection';")
		time_new=$[ $time_old + $time_watched ]
		sqlite3 $database "update channels set TimeWatched = '$time_new' where Name = '$final_selection';"
		exit
		else
		exit
	fi
	run_once="yes"
	fi
}

case ${1} in

"-h"|"--help")
echo -ne " Usage: twitchy [OPTION]
 [ARGUMENTS]\t\t\tLaunch channel in $video_player
 -a <channel name>\t\tAdd channel
 -an\t\t\t\tSet/unset alternate names
 -d\t\t\t\tDelete channel
 -f\t\t\t\tList favorites
 -fr\t\t\t\tReset time watched
 -h\t\t\t\tThis helpful text
 -s <username>\t\t\tSync followed channels from specified account
 -w <channel name> \t\tWatch specified channel(s)
 
 Custom quality settings: Specify with hyphen next to channel number.
 E.g. <1-l 2-m 4-s> will simultaneously play channel 1 in low quality, 2 in medium quality, and 4 in source quality.\n"
exit
;;

#Add channel
"-a")

channel_name=$2
curl -s https://api.twitch.tv/kraken/streams/$channel_name > /tmp/twitchy
grep -q 404 /tmp/twitchy
	if [[ $? = 0 ]]; then
	echo " $channel_name doesn't exist"
	if [[ $memes_everywhere = "yes" ]]; then
 echo -n " ▒▒▒░░░░░░░░░░▄▐░░░░
 ▒░░░░░░▄▄▄░░▄██▄░░░
 ░░░░░░▐▀█▀▌░░░░▀█▄░
 ░░░░░░▐█▄█▌░░░░░░▀█▄
 ░░░░░░░▀▄▀░░░▄▄▄▄▄▀▀
 ░░░░░▄▄▄██▀▀▀▀░░░░░
 ░░░░█▀▄▄▄█░▀▀░░░░░░
 ░░░░▌░▄▄▄▐▌▀▀▀░░░░░
 ░▄░▐░░░▄▄░█░▀▀░░░░░
 ░▀█▌░░░▄░▀█▀░▀░░░░░
 ░░░░░░░░▄▄▐▌▄▄░░░░░
 ░░░░░░░░▀███▀█░▄░░░
 ░░░░░░░▐▌▀▄▀▄▀▐▄░░░
 ░░░░░░░▐▀░░░░░░▐▌░░
 ░░░░░░░█░░░░░░░░█░░
 ░░░░░░▐▌░░░░░░░░░█░ 
"
	fi
	else
	sqlite3 $database "insert into channels (Name,TimeWatched) values ('$channel_name',0);"
	echo " $channel_name added to database"
if [[ $memes_everywhere = "yes" ]]; then
 echo -n " ░░░░░▄██████████▄▄░░░
 ░░░░▄██████████████▐░░
 ░░▄█████████▀▀▓▀███░░░
 ░▄███████▓▒▒▒▒▒▒▓▓█▐░░
 ░▌████████▒▒▒▄▒▒▒▒▄▐░░
 ░░███████▒▒▒▀░▀▒▒▀▌░░░
 ░░▌▓▀▀██▒▒▒▒▒▄▄▒▒▄▌░░░
 ░░▌▒▓▓▌█▒▒▒▒▒▒▀░▒▀▌░░░
 ░░░▄▒░▌█▒▒▒▒▒▒▒▐░▒▌░░░
 ░░░▀█▓▓▓▒▒▒▒▒▒▒▀▀▒▐░░░
 ░░░░▌▓▓▓▒▒▒▒░░░░▒▐░░░░
 ░░░░░▀▄▓▓▒▒▒▒▌██▐░░░░░
 ░░░░░░▀▄▓▒▒▒▒▒▀▀░░░░░░
 ░░░░░░░░▀▄▄▒▒▓▄▐░░░░░░
"
	fi
	fi
;;

#Alternate naming
"-an")
 
read -p " Replace (s)treamer or (g)ame name: " replace_category
if [[ $replace_category = "s" ]]; then
	replace_streamer=1
	sqlite3 $database "select Name,AltName from channels;" | sort > /tmp/twitchy
	else
if [[ $replace_category = "g" ]]; then
	replace_game=1
	sqlite3 $database "select Name,AltName from games;" | sort > /tmp/twitchy
fi
fi

i=0
while read line
do
	real_name[i]=$(echo $line | cut -d "|" -f1)
	alternate_name[i]=$(echo $line | cut -d "|" -f2)
		if [[ ${alternate_name[$i]} = "" ]]; then
		alternate_name[i]="UNSET"
		fi
	a_var=$[ $i +1 ]

	echo -ne " "'\E[93m'$a_var'\E[0m'
	if [[ $replace_streamer = 1 ]]; then
	spacex="               "
	if [[ $a_var -lt 10 ]]; then
		printf " ""%s %s ${alternate_name[$i]} \n" " "${real_name[$i]}"${spacex:${#real_name[$i]}}"
	else
		printf " ""%s %s ${alternate_name[$i]} \n" ${real_name[$i]}"${spacex:${#real_name[$i]}}"
	fi
	else
	echo -e " "${real_name[$i]}"\t"${alternate_name[$i]}
	fi
i=$[ $i + 1 ]
done < /tmp/twitchy

	read -p " Select number: " select_number
	select_number=$[ $select_number -1 ]
	final_selection=${real_name[$select_number]}
	read -p " Replace $final_selection with: " final_name

if [[ $replace_streamer = 1 ]]; then
	sqlite3 $database "update channels set AltName = '$final_name' where Name = '$final_selection';"
else
	sqlite3 $database "update games set AltName = '$final_name' where Name = '$final_selection';"
fi
;;

#Sync followed channels from specified account
"-s")

user_id=$2
if [[ $user_id != "" ]]; then
	curl -s https://api.twitch.tv/kraken/users/$user_id/follows/channels > /tmp/twitchy
	grep -q 404 /tmp/twitchy
	if [[ $? = 0 ]]; then
		echo " $user_id doesn't exist"
		exit
	fi
fi

cat /tmp/twitchy | sed 's/,/\n/g' | grep -v "display" | grep name | cut -d ":" -f2- | tr -d "\"" | sort > /tmp/twitchynew
sqlite3 $database "select Name from channels;" | sort > /tmp/twitchyalreadyfollowed
comm -1 -3 /tmp/twitchyalreadyfollowed /tmp/twitchynew > /tmp/twitchyadd
	new_additions=$(cat /tmp/twitchyadd | wc -l)
		if [[ $new_additions = 0 ]]; then
			echo " All streams already in local database. dansgame."
			exit
		fi

	echo " Added to local database:"
	while read line
	do
	sqlite3 $database "insert into channels (Name,TimeWatched) values ('$line',0);"
	echo " "$line
	done < /tmp/twitchyadd
	if [[ $memes_everywhere = "yes" ]]; then
 echo -n " ░░░░░▄██████████▄▄░░░
 ░░░░▄██████████████▐░░
 ░░▄█████████▀▀▓▀███░░░
 ░▄███████▓▒▒▒▒▒▒▓▓█▐░░
 ░▌████████▒▒▒▄▒▒▒▒▄▐░░
 ░░███████▒▒▒▀░▀▒▒▀▌░░░
 ░░▌▓▀▀██▒▒▒▒▒▄▄▒▒▄▌░░░
 ░░▌▒▓▓▌█▒▒▒▒▒▒▀░▒▀▌░░░
 ░░░▄▒░▌█▒▒▒▒▒▒▒▐░▒▌░░░
 ░░░▀█▓▓▓▒▒▒▒▒▒▒▀▀▒▐░░░
 ░░░░▌▓▓▓▒▒▒▒░░░░▒▐░░░░
 ░░░░░▀▄▓▓▒▒▒▒▌██▐░░░░░
 ░░░░░░▀▄▓▒▒▒▒▒▀▀░░░░░░
 ░░░░░░░░▀▄▄▒▒▓▄▐░░░░░░
"
	fi
;;

#Delete streamer from database - Does not affect time tracking
"-d")

sqlite3 $database "select Name from channels;" | sort > /tmp/twitchy

i=0
while read line
do
	channel_name[i]="$line"
	a_var=$[ $i +1 ]
	echo -e " "'\E[93m'$a_var'\E[0m' $line
	i=$[ $i + 1 ]
done < /tmp/twitchy

echo -n " Channel number: "
read game_number
game_number=$[ $game_number -1 ]
final_selection=${channel_name[$game_number]}

sqlite3 $database "delete from channels where Name = '$final_selection';"

if [[ $memes_everywhere = "yes" ]]; then
		echo " "$final_selection" R E K T" | toilet -f smblock --gay
	else
		echo " "$final_selection "deleted from db"
	fi
;;

#Script argument is matched to database
*)

if [[ $1 = "-f" ]]; then
	fav_mode=1
 	sqlite3 $database "select TimeWatched,Name from channels where TimeWatched > 0;" | sort -gr | head -n5 | cut -d "|" -f2 > /tmp/twitchy
else
if [[ $1 = "-fr" ]]; then
	read -p " Reset time watched? (y/n) " confirm_reset
	if [[ $confirm_reset = "y" ]]; then
		sqlite3 $database "update channels set TimeWatched = 0;"
	fi
	exit
else
if [[ $1 = "-w" ]]; then
	onlywatch_mode=1
	for onlywatch_channel in "${@:2}"
	do
		show_offline=yes
		echo $onlywatch_channel | cut -d "-" -f1 >> /tmp/twitchy
	done
else
	channel_arg=$1
	sqlite3 $database "select Name from channels where Name like '%$channel_arg%';" > /tmp/twitchy
fi
fi
fi

totalstreams=$(cat /tmp/twitchy | wc -l)
	if [[ $totalstreams = 0 ]]; then
		if [[ $memes_everywhere = "yes" ]]; then
		echo -n " Gray Faec (no space)
 ░░░░░░░░░░░░░░░░░░░░
 ░░░░▄▀▀▀▀▀█▀▄▄▄▄░░░░
 ░░▄▀▒▓▒▓▓▒▓▒▒▓▒▓▀▄░░
 ▄▀▒▒▓▒▓▒▒▓▒▓▒▓▓▒▒▓█░
 █▓▒▓▒▓▒▓▓▓░░░░░░▓▓█░
 █▓▓▓▓▓▒▓▒░░░░░░░░▓█░
 ▓▓▓▓▓▒░░░░░░░░░░░░█░
 ▓▓▓▓░░░░▄▄▄▄░░░▄█▄▀░
 ░▀▄▓░░▒▀▓▓▒▒░░█▓▒▒░░
 ▀▄░░░░░░░░░░░░▀▄▒▒█░
 ░▀░▀░░░░░▒▒▀▄▄▒▀▒▒█░
 ░░▀░░░░░░▒▄▄▒▄▄▄▒▒█░
 ░░░▀▄▄▒▒░░░░▀▀▒▒▄▀░░
 ░░░░░▀█▄▒▒░░░░▒▄▀░░░
 ░░░░░░░░▀▀█▄▄▄▄▀░░░░
"
		exit
	else
		echo " Search string not found in database"
		exit
	fi
	fi

if [[ $memes_everywhere = "yes" ]]; then
	meme_quantity=$(echo "$meme" | wc -l)
	meme_number=$(echo $RANDOM % $meme_quantity + 1 | bc)
	display_meme=$(sed -n ${meme_number}p <<< "$meme")
	echo " "$display_meme | toilet -f smblock --gay -w 120
fi

if [[ $fav_mode = 1 ]]; then
	echo " Listing channels by most watched..."
	else
	echo " Checking channels..."
fi

while read line
	do
	get_status $line &
	done < /tmp/twitchy

while [[ $(cat /tmp/twitchyfinal | wc -l) != $totalstreams ]]
	do
	sleep .1
	done 2> /dev/null

sort /tmp/twitchyfinal -o /tmp/twitchyfinal

i=0
while read line
	do
	stream_name=$(echo $line | cut -d ";" -f1)
		real_name_stream=$stream_name
		alt_name_stream=$(sqlite3 $database "select AltName from channels where Name = '$stream_name';") 2> /dev/null
		if [[ $alt_name_stream != "" ]]; then
			stream_name=$alt_name_stream
		fi

	game_name=$(echo $line | cut -d ";" -f2 | sed 's/'\''//g')
		if [[ $game_name != "offline" ]] && [[ $game_name != "" ]]; then

			channel_name[i]=$real_name_stream
			game_played[i]=$game_name
			alt_name_game=$(sqlite3 $database "select AltName from games where Name = '$game_name';")
			if [[ $alt_name_game != "" ]]; then
				game_name=$alt_name_game
			fi

	partnership_status=$(echo $line | cut -d ";" -f4 | sed 's/'\''//g')
	if [[ $partnership_status = "true" ]]; then
			partner[i]=true
			else
			partner[i]=false
		fi
		
	stream_status=$(echo $line | cut -d ";" -f3)
		if [[ $(echo $stream_status | wc -m) -gt $truncate_status_at ]]; then
			stream_status=$(echo $stream_status | cut -c 1-$truncate_status_at)"..."
		fi
		
		a_var=$[ $i +1 ]
		spacex="               "
		spacex2="                                        "
		echo -ne " "'\E[93m'$a_var'\E[0m'
		printf " "'\E[92m'"%s %s $game_name${spacex2:${#game_name}}$stream_status \E[0m\n" $stream_name"${spacex:${#stream_name}}"
		i=$[ $i + 1 ]
	else
		if [[ $show_offline = "yes" ]]; then
			echo -e '\E[91m'" x "$stream_name'\E[0m'
		fi
	fi
	done < /tmp/twitchyfinal

if [[ $i = 0 ]]; then
	if [[ $onlywatch_mode = 1 ]]; then
		echo " Specified channels offline / Invalid"
	else
		echo " All channels offline"
	fi
	if [[ $memes_everywhere = "yes" ]]; then
echo -n " ░░░░░░░░░░░░░░░░░░░
 ░░▄█████████████▄ ░
 ▄████████▀▀▄▄▄▄▄▄█
 ███████▀▄█▀▀▀░░░░░▀▄
 █████▀▄█▀░░░░░░░░░░▀
 ███▀▄█▀▒▒▒▒▒░░░░▄▄▀░▓
 ██▀▄█▓▄▄▄▄▄▒▒▒░░▒▄▄░░
 ██▓█▀▓▀▄▄▄▒▒██▒░▀▀░░░
 ███▓▓▓▓▓▒▒▒▒▓▓▓▒░░░░░░
 ░███▓▓▓▓▓▒▒▒█▄▄▒░░░░░░░
 ░░███▓▓▓▓▓▒▒█▀▀▀▒░░░░░░
 ░░░▀█▓▓▓▓▓▓▒▒██░░██▒░░░
 ░░░░░▀▓▓▓▓▓▒▒▒▒▀▀▒▒▒░░░
 ░░░░░░▀▓▓▓▓▓▓▓▓██░░░░░
 ░░░░░░░░▀▓▓▓▓▓███▓▒░
"
fi
	exit
fi

echo -n " Channel number (Multiple allowed): "
read -a game_number

for_quality=("${game_number[@]}")
number_of_channels=${#game_number[@]}
if [[ $number_of_channels -gt 1 ]]; then
	multi_twitch=yes
fi

for check_channels in $(seq 0 $[ $number_of_channels -1 ])
	do
	if [[ ${game_number[$check_channels]} -gt $a_var ]]; then
		if [[ $memes_everywhere = "yes" ]]; then
	echo -n " Gay Faec (no space)
 ░░░░░░░░░░░░░░░░░░░░
 ░░░░▄▀▀▀▀▀█▀▄▄▄▄░░░░
 ░░▄▀▒▓▒▓▓▒▓▒▒▓▒▓▀▄░░
 ▄▀▒▒▓▒▓▒▒▓▒▓▒▓▓▒▒▓█░
 █▓▒▓▒▓▒▓▓▓░░░░░░▓▓█░
 █▓▓▓▓▓▒▓▒░░░░░░░░▓█░
 ▓▓▓▓▓▒░░░░░░░░░░░░█░
 ▓▓▓▓░░░░▄▄▄▄░░░▄█▄▀░
 ░▀▄▓░░▒▀▓▓▒▒░░█▓▒▒░░
 ▀▄░░░░░░░░░░░░▀▄▒▒█░
 ░▀░▀░░░░░▒▒▀▄▄▒▀▒▒█░
 ░░▀░░░░░░▒▄▄▒▄▄▄▒▒█░
 ░░░▀▄▄▒▒░░░░▀▀▒▒▄▀░░
 ░░░░░▀█▄▒▒░░░░▒▄▀░░░
 ░░░░░░░░▀▀█▄▄▄▄▀░░░░
" | toilet -f term --gay
	exit
	else
	echo " Invalid selection."
	exit
		fi
	fi
done

for check_channels in $(seq 0 $[ $number_of_channels -1 ])
	do
	game_number[$check_channels]=$[ ${game_number[$check_channels]} -1 ]
	final_selection[$check_channels]=${channel_name[${game_number[$check_channels]}]}
	quality_check[$check_channels]=$(echo ${for_quality[$check_channels]} | cut -d "-" -f2)
	case ${quality_check[$check_channels]} in
	"l")
		custom_quality=1
		final_quality[$check_channels]=low
	;;
	"m")
		custom_quality=1
		final_quality[$check_channels]=medium
	;;
	"h")
		custom_quality=1
		final_quality[$check_channels]=high
	;;
	"s")
		custom_quality=1
		final_quality[$check_channels]=source
	;;
	*)
		final_quality[$check_channels]=$quality
	;;
	esac
	
	if [[ $custom_quality = 1 ]]; then
	now_watching=$(echo $now_watching $(echo ${final_selection[$check_channels]}) "-" ${final_quality[$check_channels]} "|" )
	else
	now_watching=$(echo $now_watching $(echo ${final_selection[$check_channels]}) "|" )
	fi
done

if [[ $custom_quality = 1 ]]; then
echo " Video Quality: Custom | Video Player: "$video_player
else
echo " Video Quality: "$quality "| Video Player: "$video_player
fi
echo " Now watching: "${now_watching::-1}

for check_channels in $(seq 0 $[ $number_of_channels -2 ])
	do
	livestreamer twitch.tv/${final_selection[$check_channels]} ${final_quality[$check_channels]} --player $video_player &> /dev/null &
	done

if [[ $multi_twitch != "yes" ]]; then
	if [[ $onlywatch_mode != 1 ]]; then
		start_time=$(date +%s)
		played_before=$(sqlite3 $database "select Name from games where Name = '${game_played[$game_number]}';")
		if [[ $played_before = "" ]]; then
			sqlite3 $database "insert into games (Name) values ('${game_played[$game_number]}');"
		fi
	fi
	chromium --high-dpi-support=1 --force-device-scale-factor=1 --app=http://www.twitch.tv/${final_selection[$final_channel]}/chat?popout= &> /dev/null &
fi
	final_channel=$[ $number_of_channels -1 ]
	livestreamer twitch.tv/${final_selection[$final_channel]} ${final_quality[$final_channel]} --player $video_player &> /dev/null
;;

esac
