#!/usr/bin/python3.6
# readwave_afe.py -- plot waveforms from the channels in AFEs from DAPHNE OUTPUT spy buffer(s) Python3
# 
# Manuel Arroyave <arroyave@fnal.gov>
# Sam Fogarty <samuel.fogarty@colostate.edu>

from oei import *
import numpy as np 
from tqdm import tqdm
import h5py
import time
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='DAPHNEv2 datataking script with SPI buffers')
    parser.add_argument('--file_descriptor', help='File descriptor to go into output filename', default=None)
    parser.add_argument('--nWaveforms', help='Number of waveforms to acquire from each channel', default=None)
    parser.add_argument('--daphne_endpoint', help='DAPHNE IP address endpoint', default=None)
    parser.add_argument('--read_all_channels', help='Option to save all channels', default=False)
    parser.add_argument('--do_software_trigger', help='Option to use software trigger for acquisition', default=True)
    parser.add_argument('--avg_waveforms', help='Option to save an averaged waveform of all waveforms', default=False)
    args = parser.parse_args()
    if args.file_descriptor is not None:
        file_descriptor = args.file_descriptor
    else:
        raise Exception('Need a file descriptor, e.g. --file_descriptor daphne_test')
    if args.nWaveforms is None:
        nWaveforms = args.nWaveforms
    else:
        nWaveforms = 10000
    if args.daphne_endpoint is None:
        daphne_ip_endpoint = 100
    else:
        daphne_ip_endpoint = args.daphne_endpoint

    if os.path.exists(f'{file_descriptor}.h5'):
        raise Exception('Output file '+ f'{file_descriptor}.h5' + ' already exists.')
    if os.path.exists(f'{file_descriptor}.csv'):
        raise Exception('Output file '+ f'{file_descriptor}.csv' + ' already exists.')
    read_all_channels = args.read_all_channels
    do_software_trigger = args.do_software_trigger
    avg_waveforms = args.avg_waveforms
    keep_acquiring = True

    if read_all_channels:
        channels = [0,1,2,3,4,5,6,7]
        AFEs = [0,1,2,3,4]
        print(f'Reading all channels and all AFEs.')
    else:
        channels = [0]
        AFEs = [0]
        print(f'Reading only channels {channels}, AFEs {AFEs}')
    
    # don't change these
    base_register = 0x40000000
    AFE_hex_base = 0x100000
    Channel_hex_base = 0x10000  
        
    thing = OEI(f"10.73.137.{daphne_ip_endpoint}")
    print(f'Reading from DAPHNE with IP: {10.73.137.{daphne_ip_endpoint}}')
    if do_software_trigger:
        print('Using software (random) trigger for acquisition.')
    else:
        print('Assuming external trigger for acquisition.')
    print(f'Reading {nWaveforms} waveforms from each channel.')

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
    
    if avg_waveforms:
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
    
    with h5py.File(f'{file_descriptor}.h5', 'w') as f:
        dset_waveforms = f.create_dataset('waveforms', data=rec, dtype=data_dtype)
        if avg_waveforms:
            dset_waveforms_avg = f.create_dataset('waveforms_avg', data=rec_avg, dtype=data_dtype)
    # save csv
    start_index = 0
    stop_index = 4000
    np.savetxt(f'{file_descriptor}.csv', np.array(f['waveforms']['adc'][:], dtype='i4')[:, start_index:stop_index], delimiter=',', fmt='%d')
    end_acquisition = time.time()
    print(f'Total time to acquire {nWaveforms} waveforms was {"%.3f" % (end_acquisition-start_acquisition)} seconds with a rate of {"%.3f" % (nWaveforms / (end_acquisition-start_acquisition))} Hz')    
    thing.close()

if __name__ == "__main__":
    main()
