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

def main():
    keep_plotting = True
    ###### edit these lines depending on the daphne, AFEs, and channels you want to look at 
    # for the daphne you'd like to look at, put the endpoint of its ip address here
    ip = "10.73.137.100"
    # put number that's on sticker. Used for labeling plots
    # list the channels you'd like to plot
    all_channels=True
    if all_channels:
        channels = [0,1,2,3,4,5, 6,7]
        # AFEs to look at
        AFEs = [0,1,2,3,4] # 0, 1, 2, 3, and/or 4
    else:
        channels = [0]
        AFEs = [0]
    #######
    #print(f'Acquiring and plotting {len(channels)} channels and {len(AFEs)} AFEs in DAPHNE with endpoint {daphne_ip_endpoint}')
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
         
    do_software_trigger = True
        
    thing = OEI(ip)
    
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:gray', 'tab:olive']
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
            length=4000
            chunk_length=50
            chunks=int(length/chunk_length)
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
                plot.set_xlim(1000, 2000)
        
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
    main()
