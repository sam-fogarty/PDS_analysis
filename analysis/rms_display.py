############################################################
# Live-updating event display for DAPHNE using spy buffers
# Author: Sam Fogarty, fogar314@colostate.edu
############################################################

import ROOT
import time
import random
from array import array
import numpy as np
import fire
import os

import signal
import sys
from tqdm import tqdm

def calculate_rms_deviation(array):
    mean = np.mean(array)
    deviations = array - mean
    squared_deviations = deviations ** 2
    mean_squared_deviation = np.mean(squared_deviations)
    rms_deviation = np.sqrt(mean_squared_deviation)
    return rms_deviation

def update_canvas(canvas, x_data, y_data):
    # update ROOT canvas with new plot data
    canvas.Clear()
    graph = ROOT.TGraph(len(x_data), array('d', x_data), array('d', y_data))
    graph.SetLineColor(ROOT.kBlue)
    graph.Draw("ALP")
    graph.GetYaxis().SetRangeUser(0, np.around(np.min(y_data)+2))
    graph.GetXaxis().SetTitle('run number')
    graph.GetYaxis().SetTitle('ADC RMS')
    #graph.GetXaxis().SetRangeUser(400, 1100) 
    canvas.Update()
    #print(y_data[0:10])

def main(runstart):
    # Create a ROOT canvas for plots
    canvas = ROOT.TCanvas("canvas", "Dynamic Canvas", 800, 600)

    x_data = []
    y_data = []
    folder = '../cpp/data/'
    runnumber = runstart
    filename = f'{folder}run{runnumber}.csv'
    wait = False
    # keep reading waveforms continuously
    while True: # loop thru files
        if not os.path.exists(filename):
            raise Exception(f'file {filename} does not exist!')
        print(f'Calculating rms for {filename}')
        data = np.loadtxt(filename, delimiter=' ')[0:500]
        rms_values = []
        for wvfm in data:
            rms = calculate_rms_deviation(wvfm[0:1000])
            rms_values.append(rms)
        x_data.append(runnumber)
        y_data.append(np.median(rms))
        runnumber += 1
        filename = f'{folder}run{runnumber}.csv'
        while True: # plot once encountered file that does not exist yet, then wait until next file exists
            if not os.path.exists(f'{folder}run{runnumber}.csv'):
                update_canvas(canvas, x_data, y_data)
                wait = True
            elif os.path.exists(f'{folder}run{runnumber}.csv') and wait:
                print('waiting')
                time.sleep(60)
                break
            elif os.path.exists(f'{folder}run{runnumber}.csv') and not wait:
                break
            else:
                pass
    
if __name__ == '__main__':
    fire.Fire(main)
