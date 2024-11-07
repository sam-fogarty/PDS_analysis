#!/usr/bin/env python3
# offset_tuning.py; tune offsets in selected channels
import numpy as np 
import DaphneInterface as ivtools
from tqdm import tqdm
import argparse

def main(EP, ch, afe, baseline, vgain, oi):

    offset=1118 # initial offset value to set
    target_pedestal=int(baseline) # pedestal value to aim for in tuning
    tolerance=500 # tolerance allowed from target pedestal
    print_pedestals = True # option to print pedestals each loop

    ip_endpoints = [int(ep) for ep in EP.split(',')]
    if oi:
        oi = bool(oi)
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
    pedestal=target_pedestal
    for i in ip_endpoints:
        device = ivtools.daphne(f"10.73.137.{i}")
        print("DAPHNE firmware version %0X" % device.read_reg(0x9000,1)[2])

        for afe in tqdm(AFEs,unit='AFE'):
            device.command(f'WR AFE {afe} VGAIN V {int(vgain)}')
            for ch in channels:
                device.write_reg(0x2000, [1234]) # software trigger, all spy buffers capture
                a=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
                if print_pedestals:
                    print (a)
                while tolerance<=abs(target_pedestal-a) or a == 0:
                    offset_increment = ((target_pedestal-a)/abs(target_pedestal-a)) 
                    offset=offset+((target_pedestal-a)/abs(target_pedestal-a)) 
                    device.command(f'WR OFFSET CH {afe*8+ch} V {offset}')
                    device.write_reg(0x2000, [1234]) # software trigger, all spy buffers capture
                    a=np.average(device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),50)[40:])
                    if print_pedestals:
                        print (a) 
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
                print("AFE%d[%d]: " % (afe,ch),end="")
                for x in device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),15)[3:]:
                    print("%04X " % x,end="")
                print()
            print()
            if oi:
                device.command(f'WR {int(afe)} REG 52 V 16896')
                device.command(f'WR {int(afe)} REG 51 V 0')
            else:
                device.command(f'WR {int(afe)} REG 52 V 21056')
                device.command(f'WR {int(afe)} REG 51 V 16')
           
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script tuning the offsets on selected channels.")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137.')
    parser.add_argument('--ch', required=True, default=None, help="List of channels to read from, formatted like '0,1,2'")
    parser.add_argument('--afe', required=True, default=None, help="List of AFEs to read from, formatted like '0,1'")
    parser.add_argument('--baseline', required=True, default=None, help="Target baseline")
    parser.add_argument('--vgain_dac', required=False, default=None, help="VGAIN to set")
    parser.add_argument('--turn_on_oi', required=False, default=False, help="Option to turn on/off offset integrators")
    args = parser.parse_args()
    main(args.ep, args.ch, args.afe, args.baseline, args.vgain_dac, args.turn_on_oi)
