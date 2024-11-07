# Check if the starting run number is provided
if [ -z "$1" ]; then
	echo "Usage: $0 <starting_X>"
	exit 1
fi

X=$1

DATE=$(date +"%m-%d-%Y")
# Infinite loop to run data collection, until user does ctrl-c
while [ true ]
do
    ./dg_ctrl 10.73.137.111 0 # turn off output on pulser
	TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    cd ..
    python3 set_bias.py --ep 110 --afe 4 --v 45 --run_type cold
    cd cpp
    # Run data acquisition
    ./collect_data --run "${X}" --trig soft
    echo "Run ${X}: ${TIMESTAMP}" >> run_log_${DATE}_DCR_ABD.txt
    X=$((X + 1))

    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    ./dg_ctrl 10.73.137.111 1 # turn on output on pulser
    ./collect_data --run "${X}" --trig ext
    echo "Run ${X}: ${TIMESTAMP}" >> run_log_${DATE}_LED.txt
    X=$((X + 1))

    ./dg_ctrl 10.73.137.111 0 # turn off output on pulser
    cd ..
    python3 set_bias.py --ep 110 --afe 4 --v 30 --run_type cold
    cd cpp
    ./collect_data --run "${X}" --trig soft
    echo "Run ${X}: ${TIMESTAMP}" >> run_log_${DATE}_DCR_BBD.txt
	# log runnumber and timestamp to a text file
	
	if [ "$ABD" = false ]; then
		echo "Run ${X}: ${TIMESTAMP}" >> run_log.txt
	fi
    X=$((X + 1))
	sleep 1
	done
