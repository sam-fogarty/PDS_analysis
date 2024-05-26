############################################################
# Live-updating event display for DAPHNE using spy buffers
# Author: Sam Fogarty, fogar314@colostate.edu
############################################################

import ROOT
import time
import random
from array import array
import numpy as np
# requires ivtools version with signal module for dealing with ethernet timeouts, otherwise the code may freeze
import DaphneInterface as ivtools

import signal
import sys

def signal_handler(sig, frame):
    print('Ctrl+C detected. Exiting gracefully.')
    sys.exit(0)

# Register the signal handler
#signal.signal(signal.SIGINT, signal_handler)

def update_canvas(canvas, x_data, y_data):
    # update ROOT canvas with new plot data
    canvas.Clear()
    graph = ROOT.TGraph(len(x_data), array('d', x_data), array('d', y_data))
    graph.SetLineColor(ROOT.kBlue)
    graph.Draw("ALP")
    #graph.GetYaxis().SetRangeUser(8013, 8022)
    #graph.GetXaxis().SetRangeUser(0, 800) 
    canvas.Update()
    #print(y_data[0:10])

length=1500 # 4000 max
chunk_length=50 # how many points to read at a time
chunks=int(length/chunk_length)

# don't change these
base_register = 0x40000000
AFE_hex_base = 0x100000
Channel_hex_base = 0x10000

ip = f'10.73.137.110'
device = ivtools.daphne(ip)
print("DAPHNE firmware version %0X" % device.read_reg(0x9000,1)[2])
afe, chan = 0, 4
nWvfms_avg = 70 # number of waveforms to average for rolling average, set to 1 to plot each waveform without rolling average
do_software_trigger = False

# Create a ROOT canvas for plots
canvas = ROOT.TCanvas("canvas", "Dynamic Canvas", 800, 600)

last_timestamp = -1
x_data = np.arange(0, length)
y_data = np.zeros(length) # holds the wvfm sums
y_data_avg = np.zeros(length) # holds the wvfm average

# we will hold onto previous waveforms to be able to do rolling average
y_data_list_last = np.zeros((nWvfms_avg, length)) 
y_data_list_next = np.zeros((nWvfms_avg, length))
nWvfms_abs = 0 # keeps iterating forever
nWvfms = 0 # will reset every nWvfms_avg
both_lists_filled = False

# keep reading waveforms continuously
try:
    while True:
        if nWvfms_avg == 1:
            time.sleep(0.25)
        if do_software_trigger:
            device.write_reg(0x2000, [1234]) # trigger SPI buffer
        y_data = np.zeros(length)
        current_timestamp = int(device.read_reg(0x40500000, 1)[2])
        # check that the last trigger and current trigger are not the same, as to not double count triggers
        if last_timestamp != current_timestamp:
            last_timestamp = current_timestamp
            for i in range(chunks):
                doutrec = device.read_reg(base_register+(AFE_hex_base * afe)+(Channel_hex_base * chan)+i*chunk_length,chunk_length)
                y_data[i*chunk_length:(i+1)*chunk_length] = doutrec[2:]

            new_timestamp = int(device.read_reg(0x40500000, 1)[2])
            # check that the trigger timestamp has not changed over the course of reading
            if new_timestamp == last_timestamp:
                if nWvfms_abs < nWvfms_avg:
                    y_data_list_last[nWvfms, :] = y_data
                elif nWvfms_abs == nWvfms_avg-1:
                    y_data_list_last[nWvfms, :] = y_data
                    y_data_avg = np.sum(y_data_list_last, axis=0)/nWvfms_avg
                    update_canvas(canvas, x_data, y_data_avg)
                elif nWvfms_abs >= nWvfms_avg:
                    y_data_list_next[nWvfms, :] = y_data
                    y_data_avg = (np.sum(y_data_list_last[nWvfms+1:], axis=0)+np.sum(y_data_list_next[0:nWvfms+1], axis=0))/nWvfms_avg
                    update_canvas(canvas, x_data, y_data_avg)
                if nWvfms == nWvfms_avg-1 and nWvfms_abs >= 2*nWvfms_avg-1:
                    # replace y_data_list_last with y_data_list_next
                    y_data_list_last = np.copy(y_data_list_next)
                if nWvfms == nWvfms_avg-1:
                    nWvfms = 0
                else:
                    nWvfms += 1
                nWvfms_abs += 1
                last_timestamp = new_timestamp
except KeyboardInterrupt:
    print('Ctrl+C detected. Exiting gracefully.')
    sys.exit(0)
