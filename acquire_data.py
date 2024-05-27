#!/usr/bin/python3.6
# readwave_afe.py -- plot waveforms from the channels in AFEs from DAPHNE OUTPUT spy buffer(s) Python3
# 
# Manuel Arroyave <arroyave@fnal.gov>
# Sam Fogarty <samuel.fogarty@colostate.edu>

#from oei import *
import numpy as np 
from tqdm import tqdm
import h5py
import time
import os
import argparse
#import ivtools
import DaphneInterface as ivtools 
from datetime import datetime

def tune_offset(device, ep, afe, tolerance, target_pedestal, offsets_start, offset_diff, VGAIN):
    print(f'Tuning offsets in AFE {afe} channels to {target_pedestal} with tolerance {tolerance}')
    # tune pedestals to some target pedestal using the offset control
    channels=[0,1,2,3,4,5,6,7]
    offsets=[]
    do_offset_tune=True
     
    pedestal=target_pedestal
    #offset=offsets_start[0]
    #ch = channels[0]
    #device.write_reg(0x2000, [1234]) # software trigger, all spy buffers capture
    #a1=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
    #offset=offset+((pedestal-a1)/abs(pedestal-a1))
    #device.command(f'WR OFFSET CH {afe*8+ch} V {offset}')

    #device.write_reg(0x2000, [1234])
    #a2=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
    #a_diff = a2-a1
    #if a_diff != 0:
    #    offset+=int(abs(pedestal-a2)/a_diff)
    #offset_diff *= np.exp(VGAIN)
    if do_offset_tune:
        for ch in tqdm(channels):
            device.write_reg(0x2000, [1234]) # software trigger, all spy buffers capture
            a=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
            offset=offsets_start[0]
            #pedestal=target_pedestal

            initial_offset = offset
            offset += offset_diff
            while tolerance<=abs(pedestal-a):
                offset_increment = ((pedestal-a)/abs(pedestal-a))
                #offset=offset+offset_increment
                print(f'pedestal-a = {pedestal-a}; offset = {offset}')
                #print(f'offset = {offset}')
                #print(offset)
                a_last = a
                device.command(f'WR OFFSET CH {afe*8+ch} V {offset}') 
                device.write_reg(0x2000, [1234]) # trigger SPI buffer
                a=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
                #print(a)
                if int(a) == int(a_last):
                    offset+=offset_increment*10
                
                if abs(pedestal-a) > 6000:
                    offset+=offset_increment*10
                elif abs(pedestal-a) > 3000 and abs(pedestal-a) < 6000:
                    offset+=offset_increment*6
                elif abs(pedestal-a) > 1500 and abs(pedestal-a) < 3000:
                    offset+=offset_increment*4
                elif abs(pedestal-a) > 1000 and abs(pedestal-a) < 1500:
                    offset+=offset_increment*2
                elif abs(pedestal-a) > 500 and abs(pedestal-a) < 1000:
                    offset+=offset_increment*1
                else:
                    offset_increment = ((pedestal-a)/abs(pedestal-a))
                    offset=offset+offset_increment
                #print(f'pedestal-a = {pedestal-a}; offset = {offset}')
            final_offset = offset
            offsets.append(offset)
            offset_diff = final_offset - initial_offset
    else:
        for ch in channels:
            device.command(f'WR OFFSET CH {afe*8+ch} V {1100}') 
            offsets.append(1100)
    return offsets, offset_diff
    
def main(filepath_start, trig_type, ep, length, ch, afe, nWaveforms, formats, saving_range, VGAIN, initial_offset, target_pedestal):    
    nWaveforms = int(nWaveforms)
    length = int(length)
    initial_offset = int(initial_offset)
    target_pedestal = int(target_pedestal)
    if saving_range is None:
        start_index, stop_index = 0, length
    else:
        start_index, stop_index = saving_range.split(',')[0], saving_range.split(',')[1]
    formats_list = formats.split(',')

    if VGAIN is not None:
        if len(VGAIN.split(',')) == 1:
            VGAINs_list = [float(VGAIN)]
        else:
            VGAINs_list = [float(vgain) for vgain in VGAIN.split(',')]
    else:
        VGAINs_list = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        #VGAINs_list = [0.4] 
    VGAINs_labels_list = []
    for vgain in VGAINs_list:
        if vgain == 0:
            VGAINs_labels_list.append('0p0')
        else:
            VGAINs_labels_list.append(str(vgain).replace('.', 'p'))
    
    save_h5 = False
    save_csv = False
    save_npz = False
    if 'h5' in formats_list:
        save_h5 = True
    if 'csv' in formats_list or 'txt' in formats_list:
        save_csv = True
    if 'npz' in formats_list:
        save_npz = True

    # don't change these
    base_register = 0x40000000
    AFE_hex_base = 0x100000
    Channel_hex_base = 0x10000

    ch = np.array(ch.split(',')).astype('int')

    afe = int(afe)
    
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
    print(f'Starting acquisition of channel(s) {ch} on AFE {afe} on DAPHNE with endpoint {ep}...')

    ip = f'10.73.137.{ep}'
    device = ivtools.daphne(ip)
    print("DAPHNE firmware version %0X" % device.read_reg(0x9000,1)[2])
    data_dtype = np.dtype([('adc', '<i4', (length,)), ('channel', '<i2'), ('AFE', '<i2')])
    device.close()
    
    # get date for filename
    current_datetime = datetime.now()
    month = current_datetime.month
    day = current_datetime.day
    year = current_datetime.year
    date = str(year)+str(month)+str(day)
    filepath_start = filepath_start + f'_{date}'

    tolerance=500 # pedestal tolerance
    turn_on_OI = False
    offsets = np.ones(len(VGAINs_list))*initial_offset
    for k,VGAIN in enumerate(VGAINs_list):
        filepath_base = os.path.splitext(filepath_start)[0] # avoid '.''s in the filename other than in the file type (which is optional)
        main_directory = os.path.dirname(filepath_base)
        descriptor = os.path.basename(filepath_base)

        os.system(f'mkdir -p {filepath_start}')
        VGAIN_folder = filepath_start + f'/VGAIN{VGAINs_labels_list[k]}'
        os.system(f'mkdir -p {VGAIN_folder}')

        device = ivtools.daphne(ip)
        
        print(f'Setting VGAIN = {int(VGAIN*2666)} (Vctrl={(VGAIN):.2f})V) on AFE {afe}')
        device.command(f'WR AFE {str(int(afe))} VGAIN V {int(VGAIN*2666)}')
        
        print('')
        offset_diff = 0
        if turn_on_OI:
            target_pedestal = 8196
            offsets, offset_diff = tune_offset(device, ep, afe, tolerance, target_pedestal, offsets, offset_diff, VGAIN)
            print(f'Final offset DAC value = {np.array(offsets)[list(ch)]}')
            
            device.command(f'WR AFE {str(int(afe))} REG 52 V 16896')
            device.command(f'WR AFE {str(int(afe))} REG 51 V 0')
            
            # configure LNA
            #device.command(f'WR AFE {str(int(afe))} REG 52 V 16896')
            # configure PGA
            #device.command(f'WR AFE {str(int(afe))} REG 51 V 0')
            # change to 10MHz low pass filter
            #device.command(f'WR AFE {str(int(AFE))} REG 51 V 8')
        else:
            device.command(f'WR AFE {str(int(afe))} REG 52 V 21056')
            device.command(f'WR AFE {str(int(afe))} REG 51 V 16')

            offsets, offset_diff = tune_offset(device, ep, afe, tolerance, target_pedestal, offsets, offset_diff, VGAIN)
            print(f'Final offset DAC value = {np.array(offsets)[list(ch)]}')

        for chan in ch:
            filepath_base = descriptor
            chan = int(chan)
            nbad, ngood = 0, 0
            rec = np.zeros(nWaveforms, dtype=data_dtype)
            start_acquisition = time.time()
            iWvfm = 0
            progress_bar = tqdm(total=nWaveforms)
            last_timestamp = -1
            while True:
                data = np.zeros(length)
                if do_software_trigger:
                    device.write_reg(0x2000, [1234]) # trigger SPI buffer
                
                # save waveform from channel
                data_list=[]
                current_timestamp = int(device.read_reg(0x40500000, 1)[2])
                
                if last_timestamp != current_timestamp:
                    last_timestamp = current_timestamp
                    for i in range(chunks):
                        doutrec = device.read_reg(base_register+(AFE_hex_base * afe)+(Channel_hex_base * chan)+i*chunk_length,chunk_length)
                        data[i*chunk_length:(i+1)*chunk_length] = doutrec[2:]
        
                    new_timestamp = int(device.read_reg(0x40500000, 1)[2])
                    
                    if last_timestamp == new_timestamp and len(doutrec) > 0:
                        rec[iWvfm]['adc'] = np.array(data)
                        iWvfm += 1
                        progress_bar.update(1)
                        ngood+=1
                    else:
                        nbad+=1
                    last_timestamp = new_timestamp
                    if iWvfm >= nWaveforms:
                        break
                
            
            print(' ')
            print(f'Total number of bad triggers = {nbad}')
            print(f'Total number of good triggers = {ngood}')
            if turn_on_OI:
                OI_label = '_OIsON'
            else:
                OI_label = '_OIsOFF'
            VGAIN_label = VGAINs_labels_list[k]
            filepath_base = VGAIN_folder + '/' + filepath_base + f'_EP{ep}_VGAIN{VGAIN_label}_offset{int(offsets[chan])}{OI_label}'
            if save_h5: 
                with h5py.File(filepath_base+'_channel{chan}_AFE{afe}'+'.h5', 'w') as f:
                    dset_waveforms = f.create_dataset('waveforms', data=rec, dtype=data_dtype)
                print(f"Saved data to {filepath_base+'.h5'}")
            if save_npz:
                np.savez(filepath_base+'_channel{chan}_AFE{afe}'+'.npz', data=rec)
                print(f"Saved data to {filepath_base+'.npz'}")
            if save_csv:
                channel_filepath = filepath_base+f'_channel{chan}_AFE{afe}'+'.csv'
                print(f'Saving channel data to: {channel_filepath}')
                np.savetxt(channel_filepath, rec['adc'][:, start_index:stop_index], delimiter=' ', fmt='%d')        
        device.close()
        end_acquisition = time.time()
        print(f'Total time to acquire {nWaveforms} waveforms on DAPHNE endpoint {ep} was {"%.3f" % (end_acquisition-start_acquisition)} seconds with a rate of {"%.3f" % (nWaveforms / (end_acquisition-start_acquisition))} Hz')
        print(' ')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for acquiring waveforms from DAPHNE SPI buffers.")
    parser.add_argument('filename', help='Output filename, do not need to specify file type (also use no spaces). Specify formats with the --format flag.')
    parser.add_argument('--trig', default='ext', required=False,help="'soft' to use software trigger, 'ext' to use external trigger (i.e. not software trigger)")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137.')
    parser.add_argument('--points', default=1000, required=False, help="Number of data points in waveform to read from SPI buffers")
    parser.add_argument('--ch', required=False, default=None, help="List of channels to read from, formatted like '0,1,2'")
    parser.add_argument('--afe', required=False, default=None, help="List of AFEs to read from, formatted like '0,1'")
    parser.add_argument('--nWaveforms', required=False, default=10000, help='Total number of waveforms to acquire per channel.')
    parser.add_argument('--format', required=False, default='csv', help='Formats to save the data to. Options: h5, csv, npz. Comma separated formats will save the data in each format.')
    parser.add_argument('--saving_range', required=False, default=None, help='Range of data points to save to the output files. Formatted like start,stop.')
    parser.add_argument('--VGAIN', required=False, default=1.0, help='VGAIN values to use in Volts. Separate values by comma, e.g. 0.0,0.1,0.2')
    parser.add_argument('--offset', required=False, default=1100, help='Initial offset value to use for tuning pedestals')
    parser.add_argument('--target_pedestal', required=False, default=8000, help='Target pedestal value for offset tuning.')
    args = parser.parse_args()
    main(args.filename, args.trig, args.ep, args.points, args.ch, args.afe, args.nWaveforms, args.format, args.saving_range, args.VGAIN, args.offset, args.target_pedestal)
