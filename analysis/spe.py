import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse
from tqdm import tqdm
import pandas as pd
from scipy.optimize import curve_fit
import h5py

def main(filepath):
    startTime = 585
    integrationWindow = 15
    window_size = 1 # rolling average window size

    do_gaussian_fit = False

    plt.figure(figsize=(8,6))
    if '.csv' in filepath:
        data = np.loadtxt(filepath, delimiter=' ', skiprows=0)*-1
    elif '.hdf5' in filepath:
        with h5py.File(filepath, 'r') as f:
            data = np.array(f['data'])*-1
    else:
        print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
        raise Exception('File type not recognized')
    integrals = []
    for wvfm in tqdm(data):
        df = pd.DataFrame({'wvfm': wvfm})
        wvfm_smoothed = df['wvfm'].rolling(window=window_size).mean()
        wvfm_smoothed -= np.mean(wvfm_smoothed[400:500])
        integral = np.trapz(wvfm_smoothed[startTime:startTime+integrationWindow], dx=1)
        integrals.append(integral)
    hist_range = (-100, 1000)
    nbins = 100
    hist = plt.hist(integrals, bins=nbins, range=hist_range)
    hist_bins, hist_bincenters = hist[0], hist[1][:-1]
    x_values = np.arange(hist_range[0], hist_range[1], 1)
    if do_gaussian_fit:
        start_0peak, end_0peak = -35, 25
        start_1peak, end_1peak = 80, 170

        plt.vlines(start_1peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
        plt.vlines(end_1peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
        plt.vlines(start_0peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
        plt.vlines(end_0peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
        def gaussian(x, amplitude, mean, stddev):
            return amplitude * np.exp(-(x - mean)**2 / (2 * stddev**2))
        initial_guess_0peak = [200, 0.0, 25]
        mask_0peak = (hist_bincenters > start_0peak) & (hist_bincenters < end_0peak)
        params_0peak, covariance = curve_fit(gaussian, hist_bincenters[mask_0peak], hist_bins[mask_0peak], p0=initial_guess_0peak)
        amplitude_fit_0peak, mean_fit_0peak, stddev_fit_0peak = params_0peak
        plt.plot(x_values, gaussian(x_values, *params_0peak), 'r-')
        initial_guess_1peak = [250, 150, 25]
        mask_1peak = (hist_bincenters > start_1peak) & (hist_bincenters < end_1peak)
        params_1peak, covariance = curve_fit(gaussian, hist_bincenters[mask_1peak], hist_bins[mask_1peak], p0=initial_guess_1peak)
        amplitude_fit_1peak, mean_fit_1peak, stddev_fit_1peak = params_1peak
        plt.plot(x_values, gaussian(x_values, *params_1peak), 'r-')
        SNR = mean_fit_1peak/stddev_fit_0peak

        plt.annotate(r'$\sigma_b$ = '+ f'{stddev_fit_0peak:.2f} ADC*ns\n' \
                + r'$\mu_b$ = ' + f'{mean_fit_0peak:.2f} ADC*ns\n' \
                r'$\sigma_1$ = '+ f'{stddev_fit_1peak:.2f} ADC*ns\n' \
                + r'$\mu_1$ = ' + f'{mean_fit_1peak:.2f} ADC*ns\n' \
                + 'SNR = ' + f'{SNR:.2f}', xy=(hist_range[1]-300, 150),fontsize=10, color='red',
                             bbox=dict(boxstyle='round,pad=0.3', edgecolor='black', facecolor='white'))

    plt.xlim(-100, 1000)
    #plt.hist(rms_values)
    plt.xlabel('Integral [ADC*tick]')
    plt.ylabel('Counts')
    plt.title('spe Waveform Integral Plot \n (cold test, 47V bias, LED 16ns, 3V)')
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    parser.add_argument('filepath', help='Input filepath')
    args = parser.parse_args()
    main(args.filepath)
