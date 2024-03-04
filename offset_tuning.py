#!/usr/bin/env python3
# offset_tuning.py; tune offsets in selected channels
import numpy as np 
from oei import *
from init import write_and_read
from tqdm import tqdm

ip_endpoints_salev = []
ip_endpoints_jura = [100]
offset=1118 # initial offset value to set
target_pedestal=8196 # pedestal value to aim for in tuning
tolerance=100 # tolerance allowed from target pedestal
print_pedestals = True # option to print pedestals each loop
nChannels = 8 # per AFE
nAFEs = 5
channel_AFE_to_skip = [(0, 0), (0, 1), (0, 2), (0,3)] # list of tuples (channel, AFE)
for i in ip_endpoints_jura:
    thing = OEI(f"10.73.137.{i}")
    print("DAPHNE firmware version %0X" % thing.read(0x9000,1)[2])
    print(f'DAPHNE ip address = 10.73.137.{i}')
    for afe in tqdm(range(nAFEs),unit='AFE'):
        for ch in range(nChannels):
            if (afe, ch) not in channel_AFE_to_skip:
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

