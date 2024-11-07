#!/usr/bin/env python3
# init.py -- send a series of commands to initialize DAPHNEv2 configuration

from time import sleep
from tqdm import tqdm
import argparse
import DaphneInterface as ivtools

def main(EP):

    VGAIN = 2666
    offset = 1118

    AFEs = [0,1,2,3,4]
    IP_endpoints = [ep for ep in EP.split(',')]
    IP_start = "10.73.137"

    for i in IP_endpoints:
        device = ivtools.daphne(f"{IP_start}.{i}")
        if False:
            device.command('RD OFFSET CH 6')

        if True:
            # run initial command
            device.command('CFG AFE ALL INITIAL')

            # write commands to each channel
            for ch in tqdm(range(40),unit='Channels'):
                device.command('WR OFFSET CH ' + str(int(ch)) + f' V {offset}')
                device.command('CFG OFFSET CH ' + str(int(ch)) + ' GAIN 2')

            print(f'Configuring AFE registers 4, 51, 52 and Attenuators')
            # write commands to each AFE
            for AFE in tqdm(AFEs,unit='AFE'):
                device.command('WR AFE '+ str(int(AFE)) + ' REG 52 V 21056')
                device.command('WR AFE '+ str(int(AFE)) + ' REG 4 V 24')
                device.command('WR AFE '+ str(int(AFE)) + ' REG 51 V 16')
                device.command('WR AFE '+ str(int(AFE)) + f' VGAIN V {VGAIN}')
            print('Finished writing commands.')
        device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for configuring DAPHNE analog front end")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137., otherwise edit script)')
    #parser.add_argument('--vgain', required=False, default=None, help='VGAIN DAC setting to control gain/attenuation in DAPHNE')
    args = parser.parse_args()
    main(args.ep)





