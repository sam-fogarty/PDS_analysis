# Check if the starting run number is provided
if [ -z "$1" ]; then
	echo "Usage: $0 <starting_X>"
	exit 1
fi

X=$1

# Infinite loop to run data collection, until user does ctrl-c
ABD=true
while [ true ]
do
	# Format the current time and date
	TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
	if [ "$ABD" = true ]; then
		cd ..
		python3 set_bias.py --ep 110 --afe 4 --v 45 --run_type cold
		cd cpp
		# Run data acquisition
		./collect_data --run "${X}" --trig soft
		ABD=false
	else
		cd ..
		python3 set_bias.py --ep 110 --afe 4 --v 30 --run_type cold
		cd cpp
		./collect_data --run "${X}" --trig soft
		ABD=true
	fi
	# log runnumber and timestamp to a text file
	
	
	if [ "$ABD" = false ]; then
		echo "Run ${X}: ${TIMESTAMP}" >> run_log.txt
	fi
    X=$((X + 1))
	sleep 5
	done
