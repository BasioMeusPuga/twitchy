#!/bin/bash
#Requires livestreamer, sqlite, toilet

#Options
database="$HOME/.twitchy.db"
video_player=mpv
quality=high
truncate_status_at=100
number_of_faves=10
show_offline=no

#Notify when online
notify_sound=""
check_interval_seconds=60

# Put yo' spicy memes here
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
 S P I C Y M E M E S
 D O N G S Q U A D 4 2 0"
 
function emote {
if [[ $1 = "--pogchamp" ]]; then
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

if [[ $1 = "--doot" ]]; then
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

if [[ $1 = "--kappa" ]]; then
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
fi

if [[ $1 = "--dansgame" ]]; then
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
}

function convert_time () {
num=$1
min=0
hour=0
day=0

if((num>59));then
	((sec=num%60))
	((num=num/60))

	if((num>59));then
		((min=num%60))
		((num=num/60))
		if((num>23));then
			((hour=num%24))
			((day=num/24))
		else
			((hour=num))
		fi
else
	((min=num))
fi
else
	((sec=num))
fi

if [[ "$day" = 0 ]]; then
	time_watched_hms=$(echo "$(printf "%02d" $hour)"h "$(printf "%02d" $min)"m "$(printf "%02d" $sec)"s)
else
	time_watched_hms=$(echo "$(printf "%02d" $day)"d "$(printf "%02d" $hour)"h "$(printf "%02d" $min)"m "$(printf "%02d" $sec)"s)
fi
}

#Sanity checks
 if [[ ! -f /usr/bin/toilet ]]; then
	memes_everywhere=no
fi

if [[ ! -f /usr/bin/sqlite3 ]] && [[ $1 != "-w" ]]; then
	echo " sqlite not installed. Only -w will function."
	exit
fi

if [[ ! -f "$database" ]]; then
	if [[ $1 != "-w" ]]; then
		echo " First run. Creating db and exiting."
		sqlite3 $database "create table channels (id INTEGER PRIMARY KEY,Name TEXT,TimeWatched INTEGER, AltName TEXT);"
		sqlite3 $database "create table games (id INTEGER PRIMARY KEY,Name TEXT,AltName TEXT);"
		exit
	else
		how_can_tables_be_real_if_our_databases_arent_real=1
	fi
fi

rm /tmp/twitchy* 2> /dev/null

#Check status of each stream that meets criteria
function get_status {
if [[ $fav_mode = 1 ]]; then
	stream[$1]=$(curl -s https://api.twitch.tv/kraken/streams/$(echo $line | cut -d "|" -f2))
	fav_time[$1]=$(echo $line | cut -d "|" -f1)
else
	stream[$1]=$(curl -s https://api.twitch.tv/kraken/streams/$line)
fi

status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep '"stream":null')
if [[ $status = "" ]]; then
	display_name=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep display_name | sed -n '1p' | cut -d ":" -f2- | tr -d "\"" | tr -d "%")
	game_name=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep game | sed -n '1p' | cut -d ":" -f2- | tr -d "\"" | sed -n 1p)
	channel_viewers=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep viewers | sed -n '1p' | cut -d ":" -f2- | tr -d "\"" | tr -d "%")
	channel_status=$(echo "${stream[$1]}" | sed 's/","/\n/g' | /bin/grep -o "status.*" | cut -c 10- | sed 's/%/%%/g' | sed 's/;/；/g')
	partner_status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep "\"partner\"" | sed -n '1p' | cut -d ":" -f2)

	if [[ $fav_mode = 1 ]]; then
		echo ${fav_time[$line]}"^"$(echo $line | cut -d "|" -f2)";"$game_name";"$channel_status";"$channel_viewers >> /tmp/twitchyfinal
	else
	if [[ $monitor_mode = 1 ]]; then
		echo $1 >> /tmp/twitchynowonline
	else
		echo $line";"$game_name";"$channel_status";"$channel_viewers";"$display_name";"$partner_status >> /tmp/twitchyfinal
	fi
	fi
else
	if [[ $fav_mode = 1 ]]; then
		echo ${fav_time[$line]}"^"$(echo $line | cut -d "|" -f2)";offline"  >> /tmp/twitchyfinal
	else
		echo $line";offline"  >> /tmp/twitchyfinal
	fi
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
		total_time_spent=$(sqlite3 $database "select TimeWatched from channels where Name = '$final_selection';")
		time_rank=$(sqlite3 $database "select TimeWatched,Name from channels where TimeWatched > 0;" | sort -gr | cat -n | grep $final_selection | awk '{print $1}')
		convert_time $total_time_spent
		total_time_spent=$time_watched_hms
		echo -e " Total time spent watching "$final_selection" - "'\E[1;97m'$total_time_spent" ("$time_rank")"'\E[0m'
		run_once="yes"
		trap 'kill $(jobs -p)' EXIT
		exit
	else
		exit
	fi
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
 -n\t\t\t\tMonitor selected offline channels and send a notification when any one comes online
 -no\t\t\t\tSTOP EVERYTHING
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
grep -q ":404" /tmp/twitchy
if [[ $? = 0 ]]; then
	echo " $channel_name doesn't exist"
	if [[ $memes_everywhere = "yes" ]]; then
		emote --doot
	fi
else
	if_already_added=$(sqlite3 $database "select Name from channels where Name = '$channel_name';")
		if [[ $if_already_added != "" ]]; then
		echo " $channel_name already in database"
		exit
		fi
	sqlite3 $database "insert into channels (Name,TimeWatched) values ('$channel_name',0);"
	echo " $channel_name added to database"
if [[ $memes_everywhere = "yes" ]]; then
	emote --pogchamp
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
	else
		alternate_name[i]=$(echo -e '\E[96m'${alternate_name[i]}'\E[0m')
	fi

	if [[ $replace_streamer = 1 ]]; then
		space=20
	else
		space=45
	fi

	a_var=$[ $i +1 ]
	echo -ne " "'\E[93m'$a_var'\E[0m'
	if [[ $a_var -lt 10 ]]; then
		printf "  ""%-"$space"s %-"$space"s\n" "${real_name[$i]}" "${alternate_name[$i]}"
		else
		printf " ""%-"$space"s %-"$space"s\n" "${real_name[$i]}" "${alternate_name[$i]}"
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
	emote --pogchamp
fi
;;

#Notify when channel comes online
#Delete channel from database
"-n"|"-d")

if [[ $1 = "-n" ]]; then
	sqlite3 $database "select Name from channels;" > /tmp/twitchy
	totalstreams=$(cat /tmp/twitchy | wc -l)

	while read line
	do
		get_status $line &
	done < /tmp/twitchy

	while [[ $(cat /tmp/twitchyfinal | wc -l) != $totalstreams ]]
	do
		sleep .1
	done 2> /dev/null

	/bin/grep ";offline" /tmp/twitchyfinal | cut -d ";" -f1 > /tmp/twitchytmp
	mv /tmp/twitchytmp /tmp/twitchyfinal
	sort /tmp/twitchyfinal -o /tmp/twitchyfinal
else
	sqlite3 $database "select Name from channels;" | sort > /tmp/twitchyfinal
fi

i=0
while read line
do
	channel_name[i]="$line"
	a_var=$[ $i +1 ]
	echo -e " "'\E[93m'$a_var'\E[0m' $line
	i=$[ $i + 1 ]
done < /tmp/twitchyfinal

echo -n " Channel number(s): "
read -a game_number
number_of_channels=${#game_number[@]}

for check_channels in $(seq 0 $[ $number_of_channels -1 ])
do
	intermediate_selection=$[ ${game_number[$check_channels]} -1 ]
	final_selection=${channel_name[$intermediate_selection]}
 	
 	if [[ $1 = "-d" ]]; then
 		sqlite3 $database "delete from channels where Name = '$final_selection';"
		if [[ $memes_everywhere = "yes" ]]; then
			echo " "$final_selection" R E K T" | toilet -f smblock --gay
		else
			echo " "$final_selection "deleted from db"
		fi
	else
		echo $final_selection >> /tmp/twitchynotify
	fi
done

if [[ $1 = "-d" ]]; then
	exit
fi

echo -e " Now monitoring:\n" $(cat /tmp/twitchynotify)

monitor_mode=1
touch /tmp/twitchynowonline

while true
do
	sleep $check_interval_seconds

while read line
	do
 		get_status $line
	done < /tmp/twitchynotify

	now_online=$(cat /tmp/twitchynowonline | sed ':a;N;$!ba;s/\n/ | /g')
	if [[ $now_online != "" ]]; then
		notify_message=$(echo -e "Now online:\n"$now_online)
		if [[ $notify_sound != "" ]]; then
			mplayer $notify_sound &
		fi
		notify-send -i 'dialog-information' "$notify_message"
		break
	fi

done &
;;

#Stop monitoring and exit ALL background processes
"-no")
killall -9 twitchy &> /dev/null
;;

#Script argument is matched to database
*)

if [[ $1 = "-f" ]]; then
	fav_mode=1
	show_offline=yes
 	sqlite3 $database "select TimeWatched,Name from channels where TimeWatched > 0;" | sort -gr | head -n$number_of_faves > /tmp/twitchy
else
if [[ $1 = "-fr" ]]; then
	read -p " Reset time watched? (yes/n) " confirm_reset
	if [[ $confirm_reset = "yes" ]]; then
		sqlite3 $database "update channels set TimeWatched = 0;"
	fi
	exit
else
if [[ $1 = "-w" ]]; then
	onlywatch_mode=1
	show_offline=yes
	for onlywatch_channel in "${@:2}"
	do
		echo $onlywatch_channel | cut -d "-" -f1 >> /tmp/twitchy
	done
else
	channel_arg=$1
	sqlite3 $database "select Name from channels where Name like '%$channel_arg%' or AltName like '%$channel_arg%';" > /tmp/twitchy
fi
fi
fi

totalstreams=$(cat /tmp/twitchy | wc -l)
if [[ $totalstreams = 0 ]]; then
	if [[ $memes_everywhere = "yes" ]]; then
		emote --kappa
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

if [[ $fav_mode = 1 ]]; then
	sort -gr /tmp/twitchyfinal -o /tmp/twitchyfinal
else
	LC_ALL=C sort -t ";" -k2,2 -k4nr /tmp/twitchyfinal -o /tmp/twitchyfinal
	touch /tmp/twitchygamesshown
fi

spacex="                      "
if [[ $fav_mode != 1 ]]; then
	spacex2="                         "
	truncate_status_at=$[ $truncate_status_at + 15 ]
else
	spacex2="                        "
fi

i=0
while read line
do
	
	if [[ $fav_mode = 1 ]]; then
		convert_time $(echo $line | cut -d "^" -f1)
		fav_time=$time_watched_hms
		line=$(echo $line | cut -d "^" -f2)
	fi
	
	real_name_stream=$(echo $line | cut -d ";" -f1)
	stream_name=$(echo $line | cut -d ";" -f5)
		if [[ $stream_name = "" ]]; then
			stream_name=$real_name_stream
		fi
	if [[ $how_can_tables_be_real_if_our_databases_arent_real != 1 ]]; then
		alt_name_stream=$(sqlite3 $database "select AltName from channels where Name like '$stream_name';") 2> /dev/null
		if [[ $alt_name_stream != "" ]]; then
			stream_name=$alt_name_stream
		fi
	fi
	
	game_name=$(echo $line | cut -d ";" -f2 | sed 's/'\''//g')
	stream_viewers=$(echo $line | cut -d ";" -f4 | sed 's/'\''//g')
	stream_viewers=$(printf "%'.f\n" $stream_viewers | cut -d "." -f1)
	if [[ $game_name != "offline" ]] && [[ $(echo $game_name | cut -d "^" -f1) != "offline" ]] && [[ $game_name != "" ]]; then
		channel_name[i]=$real_name_stream
		game_played[i]=$game_name
		
		if [[ $how_can_tables_be_real_if_our_databases_arent_real != 1 ]]; then
			alt_name_game=$(sqlite3 $database "select AltName from games where Name = '$game_name';")
			if [[ $alt_name_game != "" ]]; then
				game_name=$alt_name_game
			fi
		fi

		stream_status=$(echo $line | cut -d ";" -f3)
		if [[ $(echo $stream_status | wc -m) -gt $truncate_status_at ]]; then
			stream_status=$(echo $stream_status | cut -c 1-$truncate_status_at)"..."
		fi

		if [[ $fav_mode != 1 ]]; then
			/bin/grep -q "$game_name" /tmp/twitchygamesshown
			if [[ $? = 1 ]]; then
				echo $game_name >> /tmp/twitchygamesshown
				echo -e " "'\E[96m'$game_name'\E[0m'
			fi
			a_var=$[ $i +1 ]
			if [[ $a_var -gt 9 ]]; then
				spacex="                     "
			fi
			echo -ne " "'\E[93m'$a_var'\E[0m'
			printf " "'\E[92m'"%s %s $stream_viewers${spacex2:${#stream_viewers}}$stream_status \E[0m\n" $stream_name"${spacex:${#stream_name}}"
			i=$[ $i + 1 ]
		else
			a_var=$[ $i +1 ]
			if [[ $a_var -gt 9 ]]; then
				spacex="                     "
			fi
			game_name=$(echo '\E[96m'$game_name'\E[0m'" - "'\E[92m'$stream_status'\E[0m')
			echo -ne " "'\E[93m'$a_var'\E[0m'
			printf " "'\E[92m'"%s %s $fav_time${spacex2:${#fav_time}}$game_name \E[0m\n" $stream_name"${spacex:${#stream_name}}"
			i=$[ $i + 1 ]
		fi
	else
		
		if [[ $show_offline = "yes" ]]; then
			if [[ $fav_mode != 1 ]] && [[ $once_and_done != 1 ]]; then
				echo -e " "'\E[96m'"Offline"'\E[0m'
				once_and_done=1
			fi
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
		emote --dansgame
fi
	exit
fi

echo -n " Channel number(s): "
read -a game_number

if [[ $game_number = "" ]]; then
	emote --kappa
	game_number=$(shuf -i1-$a_var -n1)
fi

for_quality=("${game_number[@]}")
number_of_channels=${#game_number[@]}
if [[ $number_of_channels -gt 1 ]]; then
	multi_twitch=yes
fi

for check_channels in $(seq 0 $[ $number_of_channels -1 ])
do
	if [[ ${game_number[$check_channels]} -gt $a_var ]]; then
		if [[ $memes_everywhere = "yes" ]]; then
			emote --kappa | toilet -f term --gay
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
	
	partner_status_channel=$(/bin/grep ${final_selection[$check_channels]} /tmp/twitchyfinal | cut -d ";" -f6)
	if [[ $partner_status_channel = "true" ]]; then
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
	else
		custom_quality=1
		final_quality[$check_channels]=source
	fi
	
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
echo -e " Now watching: "'\E[1;97m'${now_watching::-1}'\E[0m'

for check_channels in $(seq 0 $[ $number_of_channels -2 ])
do
	if [[ $video_player = "mpv" ]]; then
		video_player_final=$video_player" --hwdec=vaapi --vo=vaapi --cache 8192 --title ${final_selection[$check_channels]}"
	fi
	livestreamer twitch.tv/${final_selection[$check_channels]} ${final_quality[$check_channels]} --player "$video_player_final" --hls-segment-threads 3 &> /dev/null &
done

if [[ $multi_twitch != "yes" ]]; then
	if [[ $onlywatch_mode != 1 ]]; then
		start_time=$(date +%s)
		played_before=$(sqlite3 $database "select Name from games where Name = '${game_played[$game_number]}';")
		if [[ $played_before = "" ]]; then
			sqlite3 $database "insert into games (Name) values ('${game_played[$game_number]}');"
		fi
	fi
	
	if [[ $BROWSER = "/usr/bin/chromium" ]]; then
		chromium --app=http://www.twitch.tv/${final_selection[$final_channel]}/chat?popout= &> /dev/null &
	else
		eval $BROWSER "http://www.twitch.tv/${final_selection[$final_channel]}/chat?popout=" &> /dev/null &
	fi
		
fi
	final_channel=$[ $number_of_channels -1 ]
	if [[ $video_player = "mpv" ]]; then
		video_player_final=$video_player" --hwdec=vaapi --vo=vaapi --cache 8192 --title ${final_selection[$final_channel]}"
	fi
	
if [[ $multi_twitch != "yes" ]]; then
	livestreamer twitch.tv/${final_selection[$final_channel]} ${final_quality[$final_channel]} --player "$video_player_final" --hls-segment-threads 3 &> /dev/null &
	while :
	do
		read -t 0.1 -n 1 key
			if [[ $key = q ]]; then
				ctrl_c
			else
			if [[ $key = m ]]; then
				eval $BROWSER twitchecho.com/${final_selection[$final_channel]} &> /dev/null
			fi
			fi
	done
	else
	livestreamer twitch.tv/${final_selection[$final_channel]} ${final_quality[$final_channel]} --player "$video_player_final" --hls-segment-threads 3 &> /dev/null
fi
;;

esac
