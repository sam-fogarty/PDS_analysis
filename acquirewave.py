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
import argparse

def main(filepath_base, trig_type, EP, length, ch, afe, nWaveforms, formats, saving_range):
    
    filepath_base = os.path.splitext(filepath_base)[0] # avoid '.''s in the filename other than in the file type (which is optional)
    nWaveforms = int(nWaveforms)
    length = int(length)
    
    main_directory = os.path.dirname(filepath_base)
    descriptor = os.path.basename(filepath_base)
    if not os.path.exists(filepath_base):
        os.mkdir(filepath_base)
    filepath_base = filepath_base + f'/{descriptor}'
    if saving_range is None:
        start_index, stop_index = 0, length
    else:
        start_index, stop_index = saving_range.split(',')[0], saving_range.split(',')[1]
    formats_list = formats.split(',')
    save_h5 = False
    save_csv = False
    save_npz = False
    if 'h5' in formats_list:
        save_h5 = True
    if 'csv' in formats_list or 'txt' in formats_list:
        save_csv = True
    if 'npz' in formats_list:
        save_npz = True

    daphne_ip_endpoint = [ep for ep in EP.split(',')]
    
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
    chunk_length=100
    chunks=int(length/chunk_length) 
    start_acquisition = time.time()
    print(f'Starting acquisition of {len(AFEs) * len(channels)} channels on DAPHNE(s) with endpoint(s) {daphne_ip_endpoint}...')
    for ep in daphne_ip_endpoint:
        EP_dir = filepath_base+f'/endpoint{ep}'
        #if not os.path.exists(EP_dir):
        #    os.mkdir(EP_dir)
        thing = OEI(f"10.73.137.{ep}")
    
        data_dtype = np.dtype([('adc', '<i4', (length,)), ('channel', '<i2'), ('AFE', '<i2')])
        rec = np.zeros((len(AFEs)*len(channels)*nWaveforms), dtype=data_dtype)
        start_acquisition = time.time()
        iWvfm = 0
        for w in tqdm(range(nWaveforms), desc = f' Reading waveforms from endpoint {ep}: '):
            if do_software_trigger:
                thing.write(0x2000,[1234]) # trigger SPI buffer

            # loop through AFEs, grab waveforms from channels, save to array
            for g,AFE in enumerate(AFEs):
                for d,channel in enumerate(channels):
                    data_list=[]
                    for i in range(chunks):
                        doutrec = thing.read(base_register+(AFE_hex_base * AFE)+(Channel_hex_base * channel)+i*chunk_length,chunk_length)
                        for word in doutrec[2:]:
                            data_list.append(word)
                    rec[iWvfm]['adc'] = np.array(data_list)
                    rec[iWvfm]['AFE'] = AFE
                    rec[iWvfm]['channel'] = channel
                    iWvfm += 1
        
        filepath_base = filepath_base + f'_EP{ep}'
        if save_h5: 
            with h5py.File(filepath_base+'.h5', 'w') as f:
                dset_waveforms = f.create_dataset('waveforms', data=rec, dtype=data_dtype)
            print(f"Saved data to {filepath_base+'.h5'}")
        if save_npz:
            np.savez(filepath_base+'.npz', data=rec)
            print(f"Saved data to {filepath_base+'.npz'}")
        if save_csv:
            print(f'Saving channel data to individual files to this directory: {os.path.dirname(filepath_base)}')
            for AFE in AFEs:
                for channel in channels:
                    channel_filepath = filepath_base+f'_channel{channel}_AFE{AFE}'+'.csv'
                    np.savetxt(channel_filepath, rec[(rec['AFE'] == AFE) & (rec['channel'] == channel)]['adc'][:, start_index:stop_index], delimiter=',', fmt='%d')

    end_acquisition = time.time()
    print(f'Total time to acquire {nWaveforms} waveforms on DAPHNE endpoint(s) {daphne_ip_endpoint} was {"%.3f" % (end_acquisition-start_acquisition)} seconds with a rate of {"%.3f" % (nWaveforms / (end_acquisition-start_acquisition))} Hz')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for acquiring waveforms from DAPHNE SPI buffers.")
    parser.add_argument('filename', help='Output filename, do not need to specify file type (also use no spaces). Specify formats with the --format flag.')
    parser.add_argument('--trig', default='soft', required=False,help="'soft' to use software trigger, 'ext' to use external trigger (i.e. not software trigger)")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137.')
    parser.add_argument('--points', default=4000, required=False, help="Number of data points in waveform to read from SPI buffers")
    parser.add_argument('--ch', required=False, default=None, help="List of channels to read from, formatted like '0,1,2'")
    parser.add_argument('--afe', required=False, default=None, help="List of AFEs to read from, formatted like '0,1'")
    parser.add_argument('--nWaveforms', required=False, default=10000, help='Total number of waveforms to acquire per channel.')
    parser.add_argument('--format', required=False, default='h5,csv', help='Formats to save the data to. Options: h5, csv, npz. Comma separated formats will save the data in each format.')
    parser.add_argument('--saving_range', required=False, default=None, help='Range of data points to save to the output files. Formatted like start,stop.')
    args = parser.parse_args()
    main(args.filename, args.trig, args.ep, args.points, args.ch, args.afe, args.nWaveforms, args.format, args.saving_range)
