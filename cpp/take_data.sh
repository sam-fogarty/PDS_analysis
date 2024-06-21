# Check if the starting run number is provided
if [ -z "$1" ]; then
	echo "Usage: $0 <starting_X>"
	exit 1
fi

X=$1

# Infinite loop to run data collection, until user does ctrl-c
while [ true ]
do
	# Format the current time and date
	TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

	# Run data acquisition
	./collect_data "data/run${X}"

	# log runnumber and timestamp to a text file
	echo "Run ${X}: ${TIMESTAMP}" >> run_log.txt
	X=$((X + 1))
	sleep 60
	done
