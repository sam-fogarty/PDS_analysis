#!/usr/bin/python3.6
# readwave_afe.py -- plot waveforms from the channels in AFEs from DAPHNE OUTPUT spy buffer(s) Python3
# 
# Manuel Arroyave <arroyave@fnal.gov>

from oei import *
import numpy as np 
from tqdm import tqdm
import h5py
import time
import os

def main():
    
    output_filepath = 'VGAIN_BIAS_tests_March12024/daphne_fnal_config5_VGAIN0_BIAS47_10MHzPGALPFON_openchannel.h5' # must be a .h5 file
    if os.path.exists(output_filepath):
        raise Exception('Output file '+ str(output_filepath) + ' already exists.')
    
    keep_acquiring = True
    nWaveforms = 10000
    ###### edit these lines depending on the daphne, AFEs, and channels you want to look at 
    # for the daphne you'd like to look at, put the endpoint of its ip address here
    daphne_ip_endpoint = 100
    # put number that's on sticker. Used for labeling plot.
    daphne_sticker = 3
    # list the channels you'd like to plot
    channels = [0]
    #channels = [0,1]
    # AFEs to look at
    AFEs = [0] # 0, 1, 2, 3, and/or 4
    #######
    
    # don't change these
    base_register = 0x40000000
    AFE_hex_base = 0x100000
    Channel_hex_base = 0x10000
         
    do_software_trigger = False
        
    thing = OEI(f"10.73.137.{daphne_ip_endpoint}")
    
    data_dtype = np.dtype([('adc', '<i4', (4000,)), ('channel', '<i2'), ('AFE', '<i2')])
    rec = np.zeros((len(AFEs)*len(channels)*nWaveforms), dtype=data_dtype)
    start_acquisition = time.time()
    print(f'Starting acquisition of {len(AFEs) * len(channels)} channels...')
    iWvfm = 0
    for w in tqdm(range(nWaveforms), desc = ' Reading waveforms: '):
        if do_software_trigger:
            thing.write(0x2000,[1234]) # trigger SPI buffer

        # loop through AFEs, grab waveforms from channels and plot
        for g,AFE in enumerate(AFEs):
            length=4000
            chunk_length=100
            chunks=int(length/chunk_length)
            #fullWord = np.zeros((0,))
            for d,channel in enumerate(channels):
                data_list=[]
                for i in range(chunks):
                    doutrec = thing.read(base_register+(AFE_hex_base * AFE)+(Channel_hex_base * channel)+i*chunk_length,chunk_length)
                    for word in doutrec[2:]:
                        data_list.append(word)
                    #fullWord = np.concatenate((fullWord, doutrec[2:]))
                rec[iWvfm]['adc'] = np.array(data_list)
                rec[iWvfm]['AFE'] = AFE
                rec[iWvfm]['channel'] = channel
                iWvfm += 1
    
    average_waveforms = False
    if average_waveforms:
        # average waveforms
        rec_avg = np.zeros((len(AFEs)*len(channels)), dtype=data_dtype)
        iWvfm = 0
        for AFE in AFEs:
            for channel in channels:
                wvfm_avg = np.sum(rec[(rec['channel'] == channel) & 
                    (rec['AFE'] == AFE)]['adc'], axis=0) / nWaveforms
                rec_avg[iWvfm]['adc'] = wvfm_avg
                rec_avg[iWvfm]['AFE'] = AFE
                rec_avg[iWvfm]['channel'] = channel 
                iWvfm += 1
    
    with h5py.File(output_filepath, 'w') as f:
        dset_waveforms = f.create_dataset('waveforms', data=rec, dtype=data_dtype)
        if average_waveforms:
            dset_waveforms_avg = f.create_dataset('waveforms_avg', data=rec_avg, dtype=data_dtype)
    end_acquisition = time.time()
    print(f'Total time to acquire {nWaveforms} waveforms was {"%.3f" % (end_acquisition-start_acquisition)} seconds with a rate of {"%.3f" % (nWaveforms / (end_acquisition-start_acquisition))} Hz')    
    thing.close()

if __name__ == "__main__":
    main()
