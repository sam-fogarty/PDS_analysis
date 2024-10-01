# Check if the starting run number is provided
if [ -z "$1" ]; then
	echo "Usage: $0 <starting_X>"
	exit 1
fi

X=$1
I=0

vgain_list=( 0 200 400 600 800 1000 1200 1400 1600 1800 2000 2200 2400 2600 )
# Infinite loop to run data collection, until user does ctrl-c
ABD=true
while [ true ]
do
	# Format the current time and date
	TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
	echo "using vgain ${vgain_list[$I]}"
    if [ "$ABD" = true ]; then
		cd ..
		python3 offset_tuning.py --ep 110 --ch 4 --afe 0 --baseline 8200 --vgain ${vgain_list[$I]} --turn_on_oi True
		echo "turn on OI"
		ABD=false
	else
		cd ..
		python3 offset_tuning.py --ep 110 --ch 4 --afe 0 --baseline 8200 --vgain ${vgain_list[$I]}
		echo "turn off OI"
		ABD=true
	fi
	cd cpp
	# Run data acquisition
	./collect_data_new "data/run${X}"

	echo "Run ${X}"
	X=$((X + 1))
	if [ "$ABD" = true ]; then
		I=$((I + 1))
	fi
	sleep 1
done
