#!/usr/bin/python3.6
# readwave_afe.py -- plot waveforms from the channels in AFEs from DAPHNE OUTPUT spy buffer(s) Python3
#
# Sam Fogarty <samuel.fogarty@colostate.edu> 
# Manuel Arroyave <arroyave@fnal.gov>

from oei import *
import numpy as np 
import matplotlib.pyplot as plt
import time
from tqdm import tqdm
import argparse

def main(trig_type, EP, length, ch, afe):
    keep_plotting = True
    ###### edit these lines depending on the daphne, AFEs, and channels you want to look at 
    # for the daphne you'd like to look at, put the endpoint of its ip address here
    ip = f"10.73.137.{EP}"
    
    # list the channels and AFEs you'd like to plot
    # Can specify channels and AFEs in the commandline, e.g.:
    # --ch 0,1,2 plots channels 0-2 on all AFEs,
    # --afe 0,1 plots all channels on AFEs 0-1
    # --ch 0,1 --afe 0,1,2 plots channels 0-1 in AFEs 0-2
    # if not specified. automatically plots all channels and AFEs
    if ch is None and afe is None:
        channels = [0,1,2,3,4,5, 6,7]
        AFEs = [0,1,2,3,4] # 0, 1, 2, 3, and/or 4
    elif ch is not None and afe is None:
        channels = [int(c) for c in ch.split(',')]
        AFEs = [0,1,2,3,4]
    elif ch is None and afe is not None:
        channels = [0,1,2,3,4,5,6,7]
        AFEs = [int(a) for a in afe.split(',')]
    elif ch is not None and afe is not None:
        channels = [int(c) for c in ch.split(',')]
        AFEs = [int(a) for a in afe.split(',')]
    else:
        raise Exception('Invalid ch and afe arguments.')
    
    #######
    # plot-related stuff to adjust for showing different numbers of AFEs
    if len(AFEs) == 1:
        figsize = (7,5)
        nrows, ncols = 1, 1
    elif len(AFEs) == 2:
        figsize = (14,5)
        nrows, ncols = 1, 2
    elif len(AFEs) == 3:
        figsize = (16.5, 4)
        nrows, ncols = 1, 3
    elif len(AFEs) >= 4:
        figsize = (16, 9)
        nrows, ncols = 2, 3
    
    plt.ion()

    # don't change these
    base_register = 0x40000000
    AFE_hex_base = 0x100000
    Channel_hex_base = 0x10000
    
    # set trig type, software trigger is default
    if trig_type == 'soft':
        do_software_trigger = True
    elif trig_type == 'ext':
        do_software_trigger = False
    else:
        raise ValueError(f"Invalid trig type {trig_type}, possible values: soft, ext")
    thing = OEI(ip)
    
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:gray', 'tab:olive']
    chunk_length=50 # how many points to read at a time
    chunks=int(length/chunk_length)
    while keep_plotting:
        total_time = 0
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, sharex=False, sharey=False, figsize=figsize)
        if len(AFEs) == 1:
            axes = [axes]
        if do_software_trigger:
            thing.write(0x2000,[1234]) # trigger SPI buffer
        # this list of lists is used to store waveform data
        rec = [[] for i in range(len(channels))]
        # loop through AFEs, grab waveforms from channels and plot
        
        for g,AFE in enumerate(tqdm(AFEs, desc='Processing AFEs: ')):
            start = time.time()
            # this list of lists is used to store waveform data
            rec = [[] for i in range(len(channels))]
            for i in range (chunks):
                for d,channel in enumerate(channels):
                    doutrec = thing.read(base_register+(AFE_hex_base * AFE)+(Channel_hex_base * channel)+i*chunk_length,chunk_length)
                    #print(f'len(doutrec) = {doutrec}')
                    #print(doutrec)
                    for word in doutrec[2:]:
                        rec[d].append(word)
            end = time.time()
            total_time += end-start
            #print('Time to acquire: ', end-start)
            for d,channel in enumerate(tqdm(channels, desc='Processing channels in AFE: ')):
                if len(AFEs) <= 3:
                    plot = axes[g]
                    if g == 0:
                        plot.set_ylabel('14 bits data')
                else:
                    if g < 3:
                        plot = axes[0,g]
                        if g == 0:
                            plot.set_ylabel('14 bits data')
                    else:
                        plot = axes[1, g-3]
                        if g == 3:
                            plot.set_ylabel('14 bits data')
                plot.set_title(f'AFE{AFE}', fontsize=10)
                plot.plot(rec[d][0:-1], linewidth=0.5,color=colors[channel], label=f'ch {channel}')
                plot.set_xlabel('samples', fontsize=8)
                plot.legend(loc='lower right',fontsize='xx-small',framealpha=0.5)
                #plot.set_xlim(1000, 2000)
        
        if len(AFEs) == 5:
            axes[1, 2].remove()
        elif len(AFEs) == 4:
            axes[1, 2].remove()
            axes[1, 1].remove()
        plt.show(block=False)
        plt.pause(1)
        print('Total time to acquire {len(channels) * len(AFEs)} channels is {"%.4f" % total_time} seconds.')
        user_input = input("Enter 'a' to acquire again, 'q' to quit, or enter a new DAPHNE endpoint address (e.g. 107, 109).\n")
        if user_input == 'q':
            keep_plotting = False
            thing.close()
        elif user_input == 'a':
            plt.close()
            continue
        elif user_input.isnumeric():
            plt.close()
            daphne_ip_endpoint = int(user_input)
        else:
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for plotting waveforms from DAPHNE SPI buffers.")
    parser.add_argument('--trig', default='soft', required=False,help="'soft' to use software trigger, 'ext' to use external trigger (i.e. not software trigger)")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137.')
    parser.add_argument('--points', default=4000, required=False, help="Number of data points in waveform to read from SPI buffers")
    parser.add_argument('--ch', required=False, default=None, help="List of channels to read from, formatted like '0,1,2'")
    parser.add_argument('--afe', required=False, default=None, help="List of AFEs to read from, formatted like '0,1'")
    args = parser.parse_args()
    main(args.trig, args.ep, args.points, args.ch, args.afe)
