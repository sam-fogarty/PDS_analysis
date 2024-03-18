#!/usr/bin/env python3
# offset_tuning.py; tune offsets in selected channels
import numpy as np 
from oei import *
from init import write_and_read
from tqdm import tqdm
import argparse

def main(EP, ch, afe):

    offset=1118 # initial offset value to set
    target_pedestal=8196 # pedestal value to aim for in tuning
    tolerance=200 # tolerance allowed from target pedestal
    print_pedestals = True # option to print pedestals each loop

    ip_endpoints = [int(ep) for ep in EP.split(',')]
    
    # Can specify channels and AFEs in the commandline, e.g.:
    # --ch 0,1,2 plots channels 0-2 on all AFEs,
    # --afe 0,1 plots all channels on AFEs 0-1
    # --ch 0,1 --afe 0,1,2 plots channels 0-1 in AFEs 0-2
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
    
    for i in ip_endpoints:
        thing = OEI(f"10.73.137.{i}")
        print("DAPHNE firmware version %0X" % thing.read(0x9000,1)[2])
        print(f'DAPHNE ip address = 10.73.137.{i}')
        for afe in tqdm(AFEs,unit='AFE'):
            for ch in channels:
                thing.write(0x2000, [1234]) # software trigger, all spy buffers capture
                a=np.average(thing.read(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
                if print_pedestals:
                    print (a)
                while tolerance<=abs(target_pedestal-a) or a == 0:
                    offset=offset+((target_pedestal-a)/abs(target_pedestal-a))
                    write_and_read(thing, f'WR OFFSET CH {afe*8+ch} V {offset}',get_response=True) 
                    thing.write(0x2000, [1234]) # software trigger, all spy buffers capture
                    a=np.average(thing.read(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
                    if print_pedestals:
                        print (a) 
                print("AFE%d[%d]: " % (afe,ch),end="")
                for x in thing.read(0x40000000+(afe*0x100000)+(ch*0x10000),15)[3:]:
                    print("%04X " % x,end="")
                print()
            print()
           
    thing.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script tuning the offsets on selected channels.")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137.')
    parser.add_argument('--ch', required=False, default=None, help="List of channels to read from, formatted like '0,1,2'")
    parser.add_argument('--afe', required=False, default=None, help="List of AFEs to read from, formatted like '0,1'")
    args = parser.parse_args()
    main(args.ep, args.ch, args.afe)
