import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
from tqdm import tqdm
import fire
import os
import h5py

def main(*filepath):
    colors = ['r', 'b', 'g', 'k', 'm', 'c', 'y']
    #labels = ['15ns', '20ns', '25ns', '30ns', '35ns', '40ns']
    
    plt.figure(figsize=(8,6))
    for i,filename in enumerate(tqdm(filepath)):
        if '.csv' in filename:
            data = np.loadtxt(filename, delimiter=' ', skiprows=0)[:]
        elif '.hdf5' in filename:
            with h5py.File(filename, 'r') as f:
                data = np.array(f['data'])
        else:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
            raise Exception('File type not recognized')
        wvfm_sum = np.zeros(len(data[0]))
        nwvfm = 0
        for wvfm in data:
            wvfm -= np.mean(wvfm[0:200])
            if np.min(wvfm[500:600]) < -11 and np.min(wvfm[500:600]) > -18:
                wvfm_sum += wvfm
                nwvfm += 1
        #avg_wvfm = np.sum(data,axis=0)/len(data)
        avg_wvfm = wvfm_sum/nwvfm
        plt.plot(avg_wvfm, color=colors[i])
    plt.xlabel('16ns time ticks')
    plt.ylabel('ADC counts')
    #plt.title('LED Signals HD Module in Dewar at Warm \n (more optimal pulser config)')
    #plt.title('Pulser Noise HD Module in Dewar \n' + f'(channel {ch}, AFE {afe})')
    plt.title('Average 1 p.e. signal in CSU LN2 setup')
    plt.legend()
    plt.xlim(560, 900)
    plt.ylim(-15, 3)
    #plt.hist(rms_values)
    #plt.xlabel('ADC RMS')
    #plt.ylabel('Counts')
    plt.show()
    

if __name__ == "__main__":
    fire.Fire(main)
