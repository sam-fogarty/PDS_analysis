import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
from tqdm import tqdm
import fire
import os
import h5py

def main(filepath, index):
    
    plt.figure(figsize=(8,6))
    if '.csv' in filepath:
        data = np.loadtxt(filepath, delimiter=' ', skiprows=0)[index]
    elif '.hdf5' in filepath:
        with h5py.File(filepath, 'r') as f:
            data = np.array(f['data'][index]).astype('float')
    else:
        print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
        raise Exception('File type not recognized')
    wvfm = data - np.mean(data[0:500])
    
    ticks = np.arange(len(wvfm))
    plt.plot(ticks[400:1400], wvfm[400:1400])
    rise_index = np.argmin(np.diff(wvfm))-6
    plt.vlines(ticks[rise_index], ymin=np.min(wvfm)*1.1, ymax=np.max(wvfm)*1.1)
    print('index of rising edge = ', rise_index)
    #np.save('Single_PE_Template_2', avg_wvfm[600:1200])
    plt.xlabel('16ns time ticks')
    plt.ylabel('ADC counts')
    #plt.title('LED Signals HD Module in Dewar at Warm \n (more optimal pulser config)')
    #plt.title('Pulser Noise HD Module in Dewar \n' + f'(channel {ch}, AFE {afe})')
    #plt.title('Average 1 p.e. signal in CSU LN2 setup')
    plt.legend()
    #plt.xlim(560, 900)
    #plt.ylim(-15, 3)
    #plt.hist(rms_values)
    #plt.xlabel('ADC RMS')
    #plt.ylabel('Counts')
    plt.show()
    

if __name__ == "__main__":
    fire.Fire(main)
