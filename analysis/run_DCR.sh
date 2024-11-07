#!/bin/bash

RUNLOG="../cpp/run_log_ERC_supercell_DCR_8224.txt"
DCR_filename="DCR_results_1105/DCR_measurements_802.npz"

#python3 DCR.py \
#        --filepath "../cpp/data/run5721.hdf5" \
#        --DCR_filename $DCR_filename \
#        --corr_threshold 200000 #\
	#--mock_data false


python3 DCR.py \
        --runlog $RUNLOG \
        --DCR_filename $DCR_filename \
        --corr_threshold 500 #\
	#--mock_data false

