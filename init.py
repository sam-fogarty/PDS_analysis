#!/usr/bin/env python3
# init.py -- send a series of commands to initialize DAPHNEv2 configuration

from oei import *
from time import sleep
from tqdm import tqdm
import argparse

def write_and_read(thing, CmdString, get_response=True):
    CmdByteList = []
    #print('Sending command: ', CmdString)
    for ch in CmdString:
        CmdByteList.append(ord(ch))

    CmdByteList.append(0x0d) # tack on CR
    for i in range((len(CmdByteList)+49)//50):
        thing.writef(0x90000000, CmdByteList[i*50:(i+1)*50])

    ResString = ""
    if get_response:
        more = 40
        #print(' ')
        #print('Response: ')
        while more > 0:
            ResByteList = thing.readf(0x90000000,50) 
            for b in ResByteList[2:]:
                if b==255:
                    break
                elif b==1:
                    ResString += "[START]"
                elif b==2:
                    ResString += "[RESULT]"
                elif b==3:
                    ResString += "[END]"	
                elif chr(b).isprintable:
                    more = 40
                    ResString = ResString + chr(b)
            sleep(0.005)
            more -= 1
        ResString = ResString + chr(0)
        #print(ResString)

def main(EP):

    VGAIN = 0
    offset = 1118

    AFEs = [0,1,2,3,4]
    IP_endpoints = [ep for ep in EP.split(',')]
    IP_start = "10.73.137"

    for i in IP_endpoints:
        thing = OEI(f"{IP_start}.{i}")
        if False:
            write_and_read(thing, 'RD OFFSET CH 6', get_response=True)

        if True:
            # run initial command
            write_and_read(thing, 'CFG AFE ALL INITIAL')

            # write commands to each channel
            for ch in tqdm(range(40),unit='Channels'):
                write_and_read(thing, 'WR OFFSET CH ' + str(int(ch)) + f' V {offset}', get_response=True)
                write_and_read(thing, 'CFG OFFSET CH ' + str(int(ch)) + ' GAIN 2', get_response=True)

            print(f'Configuring AFE registers 4, 51, 52 and Attenuators')
            # write commands to each AFE
            for AFE in tqdm(AFEs,unit='AFE'):
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 52 V 21056', get_response=True)
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 4 V 24', get_response=True)
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 51 V 16', get_response=True)
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + f' VGAIN V {VGAIN}', get_response=True)
            print('Finished writing commands.')
        thing.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for configuring DAPHNE analog front end")
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint (assuming IP starts with 10.73.137., otherwise edit script)')
    #parser.add_argument('--vgain', required=False, default=None, help='VGAIN DAC setting to control gain/attenuation in DAPHNE')
    args = parser.parse_args()
    main(args.ep)





