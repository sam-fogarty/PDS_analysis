import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse
from tqdm import tqdm

def calculate_rms_deviation(array):
    mean = np.mean(array)
    deviations = array - mean
    squared_deviations = deviations ** 2
    mean_squared_deviation = np.mean(squared_deviations)
    rms_deviation = np.sqrt(mean_squared_deviation)
    return rms_deviation

def main():
    ch = 4
    afe = 0
    #runnumbers = [14,15,16,17,18,19,20]
    #runnumbers = [48, 49, 50, 51, 52, 53]
    runnumbers = [67, 65]
    #runnumbers = [33, 34, 35, 36, 37, 38]
    #runnumbers = [21, 22, 23, 24, 25]
    filenames = []
    for runnum in runnumbers:
        filenames.append(f'run{runnum}_2024520/VGAIN1p0/run{runnum}_2024520_EP110_VGAIN1p0_offset1118_OIsOFF_channel{ch}_AFE{afe}.csv')
    #labels = ['20ns', '19ns', '18ns', '17ns', '16ns', '15ns', '14ns']
    #labels = ['150ns', '140ns', '130ns', '120ns', '110ns', '100ns']
    labels = ['68 ohm w/ LED', '298 ohm w/ LED']
    #labels = ['LED HL 3V; LL 0V \n DAPHNE PW 1us; RFE 16.8ns', 'LED HL 3V; LL 1.5V \n DAPHNE PW 1us; RFE 500ns']
    #labels = ['']
    #labels = ['25ns', '23ns', '21ns', '19ns', '17ns', '15ns']
    #labels = ['35ns', '34ns', '33ns', '32ns', '31ns']
    colors = ['r', 'b', 'g', 'k', 'm', 'c', 'y']
    plt.figure(figsize=(8,6))
    for i,filename in enumerate(tqdm(filenames)):
        data = np.genfromtxt(filename, delimiter=' ')
        avg_wvfm = np.sum(data,axis=0)/len(data)
        avg_wvfm -= np.mean(avg_wvfm[0:200])
        print(f'min = {np.min(avg_wvfm)}')
        print(f'max = {np.max(avg_wvfm)}')
        print(f'max/min = {-1*np.max(avg_wvfm)/np.min(avg_wvfm)}')
        plt.plot(avg_wvfm, label=labels[i], color=colors[i])
    plt.xlabel('16ns time ticks')
    plt.ylabel('ADC counts')
    #plt.title('LED Signals HD Module in Dewar at Warm \n (more optimal pulser config)')
    plt.title('Pulser Noise HD Module in Dewar \n' + f'(channel {ch}, AFE {afe})')
    plt.legend()
    plt.xlim(0, 1000)
    #plt.hist(rms_values)
    #plt.xlabel('ADC RMS')
    #plt.ylabel('Counts')
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    main()
