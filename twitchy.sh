#!/bin/bash
#Requires livestreamer, sqlite, toilet

#Options
database="$HOME/.twitchy.db"
video_player=mpv
quality=medium
truncate_status_at=108
memes_everywhere=yes
	if [[ ! -f /usr/bin/toilet ]]; then
		memes_everywhere=no
	fi

if [[ ! -f "$database" ]]; then
	echo " First run. Creating db and exiting."
	sqlite3 $database "create table channels (id INTEGER PRIMARY KEY,Name TEXT,TimeWatched INTEGER);"
	exit
fi

rm /tmp/twitchy* 2> /dev/null

function get_status {
while read line
do
	stream[$1]=$(curl -s https://api.twitch.tv/kraken/streams/$line)
	status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep '"stream":null')
		if [[ $status = "" ]]; then
			game_name=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep game | cut -d ":" -f2- | tr -d "\"" | sed -n 1p)
			channel_status=$(echo "${stream[$1]}" | sed 's/,/\n/g' | grep status | cut -d ":" -f2- | tr -d "\"")
			echo $line";"$game_name";"$channel_status >> /tmp/twitchyfinal
		else
 			echo $line";offline"  >> /tmp/twitchyfinal
		fi
done < /tmp/twitchylinks$1
} &> /dev/null

start_time=0
trap ctrl_c INT
trap ctrl_c EXIT
function ctrl_c() {
	end_time=$(date +%s)
	time_watched=$[ $end_time - $start_time ]
    if [[ $final_selection != "" ]]; then
		time_old=$(sqlite3 $database "select TimeWatched from channels where Name = '$final_selection';")
		time_new=$[ $time_old + $time_watched ]
		sqlite3 $database "update channels set TimeWatched = '$time_new' where Name = '$final_selection';"
		exit
		else
		exit
	fi
}

case ${1} in

"-h"|"--help")
echo -ne " Usage: twitchy [OPTION]
 [ARGUMENTS]\tLaunch channel in $video_player
 -a\t\tAdd channel
 -d\t\tDelete channel
 -f\t\tList favorites
 -h\t\tThis helpful text
 -w\t\tWatch specified channel\n"
exit
;;


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

"-w")

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

echo " Now watching "$channel_name
echo " Video Quality: "$quality "| Video Player: "$video_player
chromium --high-dpi-support=1 --force-device-scale-factor=1 --app=http://www.twitch.tv/$channel_name/chat?popout= &> /dev/null &
livestreamer twitch.tv/$channel_name $quality --player $video_player &> /dev/null

	fi
;;

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
		echo " R E K T "$final_selection | toilet -f smblock --gay
	else
		echo " "$final_selection "deleted from db"
	fi
;;

*)

if [[ $1 = "-f" ]]; then
	fav_mode=1
 	sqlite3 $database "select TimeWatched,Name from channels where TimeWatched > 0;" | sort -gr | head -n5 | cut -d "|" -f2 > /tmp/twitchy
else
	channel_arg=$1
	sqlite3 $database "select Name from channels where Name like '%$channel_arg%';" > /tmp/twitchy
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

if [[ $fav_mode != 1 ]]; then
thread_total=5
thread_total_remainder=$[ $thread_total +1 ]
thread_total_calc=$[ $thread_total -1 ]
thread_difference=$(echo $totalstreams / $thread_total | bc)

for i in $(seq 1 $thread_difference)
	do
	for thread_number in $(seq 0 $thread_total_calc)
	do
		var_number=$[ $thread_number + 1 ]
		var[$var_number]=$[ $i + ($thread_difference * $thread_number) ]
		sed -n "${var[$var_number]}"p /tmp/twitchy >> /tmp/twitchylinks$var_number
	done
	done
cat /tmp/twitchylinks* > /tmp/twitchycoveredlinks 2> /dev/null
comm -1 -3 /tmp/twitchycoveredlinks /tmp/twitchy > /tmp/twitchylinks$thread_total_remainder 2> /dev/null

for status_check_number in $(seq 1 $thread_total_calc)
	do
	get_status $status_check_number &
	done
	get_status $thread_total_remainder &
	get_status $thread_total

while [[ $(cat /tmp/twitchyfinal | wc -l) != $totalstreams ]]
	do
	sleep .1
	done 2> /dev/null
	sort /tmp/twitchyfinal -o /tmp/twitchyfinal
	else
	cp /tmp/twitchy /tmp/twitchylinks1
	get_status 1
fi

i=0
while read line
	do
	stream_name=$(echo $line | cut -d ";" -f1)
	game_name=$(echo $line | cut -d ";" -f2)
		if [[ $game_name != "offline" ]] && [[ $game_name != "" ]]; then
			channel_name[i]=$stream_name
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
			echo -e '\E[91m'" x "$stream_name'\E[0m'
		fi
	done < /tmp/twitchyfinal

if [[ $i = 0 ]]; then
	echo " All channels offline"
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

echo -n " Channel number: "
read game_number

if [[ $game_number -gt $a_var ]]; then
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

game_number=$[ $game_number -1 ]
final_selection=${channel_name[$game_number]}

start_time=$(date +%s)
echo " Now watching "$final_selection
echo " Video Quality: "$quality "| Video Player: "$video_player
chromium --high-dpi-support=1 --force-device-scale-factor=1 --app=http://www.twitch.tv/$final_selection/chat?popout= &> /dev/null &
livestreamer twitch.tv/$final_selection $quality --player $video_player &> /dev/null
;;

esac
