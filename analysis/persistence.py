import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse
from tqdm import tqdm
import pandas as pd
import h5py

def main(filename):
    if '.csv' in filename:
        wvfms = np.genfromtxt(filename, delimiter=' ', max_rows=10000)
    elif '.hdf5' in filename:
        with h5py.File(filename, 'r') as f:
            wvfms = np.array(f['data'])
    else:
        print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
        raise Exception('File type not recognized')
    window_size = 1
    pedestal_range = (350, 450)
    amplitudes = []
    # make array to store smoothed waveforms
    wvfm_corr = np.zeros((wvfms.shape[0], wvfms.shape[1]))
    for eventID in tqdm(range(wvfm_corr.shape[0])):
        wvfm = wvfms[eventID]
        mean = np.mean(wvfm[pedestal_range[0]:pedestal_range[1]])
        df = pd.DataFrame({'wvfm': wvfm})
    
        # Apply rolling average
        wvfm_smoothed = df['wvfm'].rolling(window=window_size).mean()
        
        # Subtract pedestal
    
        wvfm_smoothed = wvfm_smoothed - mean
        amplitudes.append(np.min(wvfm_smoothed))
        wvfm_corr[eventID, :] = wvfm_smoothed
    num_waveforms, num_time_steps = wvfm_corr.shape
    #num_time_steps -= window_size
    flattened_waveforms = wvfm_corr.ravel()
    #flattened_waveforms = flattened_waveforms[~np.isnan(flattened_waveforms)]

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(16,6))
    meanADC = np.mean(flattened_waveforms[~np.isnan(flattened_waveforms)])
    # Adjust the number of bins and range
    ymax = 10
    ymin = -70
    num_bins_x = int(num_time_steps/1)
    num_bins_y = int((ymax - ymin)/1)
    range_x = [0, num_time_steps*16]
    range_y = [ymin, ymax]
    
    plot2d = axes[0].hist2d(
            np.tile(np.arange(num_time_steps)*16, num_waveforms),
            flattened_waveforms,
            bins=[num_bins_x, num_bins_y],
            range=[range_x, range_y],
            cmap='viridis',
            vmin=1,
            vmax=700
            )
    #cmap = plt.cm.jet    
    axes[0].set_xlabel(r'Time [ns]')
    axes[0].set_ylabel('Amplitude (ADC counts)')
    #plt.title(f'Persistence Plot (Run: {runnumber}, LED Voltage: {runnum_LED_dict[runnumber]}V)')
    colorbar = fig.colorbar(plot2d[3], ax=axes[0])

    vmin=0
    vmax=500 # may need to adjust to better emphasize N p.e. waveform lines
    #colorbar.clim(vmin=vmin, vmax=vmax)
    
    #plt.ylim(-40, 10)
    axes[0].set_xlim(9000, 11000)
    #plt.ylim(-50, 30)

    axes[1].hist(amplitudes, bins=75, range=(-75, 10))
    axes[1].set_xlabel('Waveform Amplitude')
    axes[1].set_xticks([-70,-60,-50,-40,-30,-20,-10,0, 10])
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    parser.add_argument('filepath', help='Input filepath')
    args = parser.parse_args()
    main(args.filepath)
