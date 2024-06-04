import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse
from tqdm import tqdm
import pandas as pd

def main(filename):
    wvfms = np.genfromtxt(filename, delimiter=' ', max_rows=10000)
    window_size = 20
    pedestal_range = (350, 450)

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
        wvfm_corr[eventID, :] = wvfm_smoothed
    num_waveforms, num_time_steps = wvfm_corr.shape
    #num_time_steps -= window_size
    flattened_waveforms = wvfm_corr.ravel()
    #flattened_waveforms = flattened_waveforms[~np.isnan(flattened_waveforms)]

    plt.figure(figsize=(10, 6))
    meanADC = np.mean(flattened_waveforms[~np.isnan(flattened_waveforms)])
    # Adjust the number of bins and range
    ymax = 10
    ymin = -70
    num_bins_x = int(num_time_steps/1)
    num_bins_y = int((ymax - ymin)/1)
    range_x = [0, num_time_steps*16]
    range_y = [ymin, ymax]

    plt.hist2d(
            np.tile(np.arange(num_time_steps)*16, num_waveforms),
            flattened_waveforms,
            bins=[num_bins_x, num_bins_y],
            range=[range_x, range_y],
            cmap='viridis',
            cmin=1
            )

    plt.xlabel(r'Time [ns]')
    plt.ylabel('Amplitude (ADC counts)')
    #plt.title(f'Persistence Plot (Run: {runnumber}, LED Voltage: {runnum_LED_dict[runnumber]}V)')
    cbar = plt.colorbar()

    vmin=0
    vmax=500 # may need to adjust to better emphasize N p.e. waveform lines
    plt.clim(vmin=vmin, vmax=vmax)
    
    #plt.ylim(-40, 10)
    plt.xlim(9000, 12000)
    #plt.ylim(-50, 30)
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    parser.add_argument('filepath', help='Input filepath')
    args = parser.parse_args()
    main(args.filepath)
