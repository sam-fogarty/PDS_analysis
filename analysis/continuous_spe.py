import matplotlib.pyplot as plt
import numpy as np
import argparse
from tqdm import tqdm
from scipy.optimize import curve_fit
import h5py
import os 
from tqdm import tqdm

def main(runlog_path):
    startTime = 428
    integrationWindow = 30
    window_size = 1 # rolling average window size

    do_gaussian_fit = True

    runlog = np.loadtxt(runlog_path, delimiter=' ', dtype=str)
    runs=[]
    for i in range(len(runlog)):
        runs.append(int(runlog[i][1].strip(':')))
    time_hour, time_minute, runnumbers_all = [], [], []
    image_folder_path = os.path.basename(runlog_path).split('.')[0]
    os.system(f'mkdir -p {image_folder_path}')

    SNR_values = []
    for run in tqdm(runs):
        filepath = f'../cpp/data/run{run}.hdf5'
        plt.figure(figsize=(8,6))
        with h5py.File(filepath, 'r') as f:
            data = np.array(f['data'])*-1
        baseline = np.mean(data[:, 0:200], axis=1)
        data = data - baseline[:, np.newaxis]
        integrals = np.trapz(data[:, startTime:startTime+integrationWindow], axis=1)

        hist_range = (-2000, 15000)
        nbins = 200
        hist = plt.hist(integrals, bins=nbins, range=hist_range)
        hist_bins, hist_bincenters = hist[0], hist[1][:-1]
        x_values = np.arange(hist_range[0], hist_range[1], 1)
        if do_gaussian_fit:
            start_0peak, end_0peak = -800, 800
            start_1peak, end_1peak = 1200, 2800

            plt.vlines(start_1peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
            plt.vlines(end_1peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
            plt.vlines(start_0peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
            plt.vlines(end_0peak, ymin=0, ymax=np.max(hist_bins), color='g', alpha=0.5)
            def gaussian(x, amplitude, mean, stddev):
                return amplitude * np.exp(-(x - mean)**2 / (2 * stddev**2))
            initial_guess_0peak = [100, 0.0, 40]
            mask_0peak = (hist_bincenters > start_0peak) & (hist_bincenters < end_0peak)
            params_0peak, covariance = curve_fit(gaussian, hist_bincenters[mask_0peak], hist_bins[mask_0peak], p0=initial_guess_0peak)
            amplitude_fit_0peak, mean_fit_0peak, stddev_fit_0peak = params_0peak
            plt.plot(x_values, gaussian(x_values, *params_0peak), 'r-')
            initial_guess_1peak = [100, 2000.0, 200]
            mask_1peak = (hist_bincenters > start_1peak) & (hist_bincenters < end_1peak)
            params_1peak, covariance = curve_fit(gaussian, hist_bincenters[mask_1peak], hist_bins[mask_1peak], p0=initial_guess_1peak)
            amplitude_fit_1peak, mean_fit_1peak, stddev_fit_1peak = params_1peak
            plt.plot(x_values, gaussian(x_values, *params_1peak), 'r-')
            SNR = abs(mean_fit_1peak/stddev_fit_0peak)

            plt.annotate(r'$\sigma_b$ = '+ f'{stddev_fit_0peak:.2f} ADC*ns\n' \
                    + r'$\mu_b$ = ' + f'{mean_fit_0peak:.2f} ADC*ns\n' \
                    r'$\sigma_1$ = '+ f'{stddev_fit_1peak:.2f} ADC*ns\n' \
                    + r'$\mu_1$ = ' + f'{mean_fit_1peak:.2f} ADC*ns\n' \
                    + 'SNR = ' + f'{SNR:.2f}', xy=(6000, 600),fontsize=10, color='red',
                                bbox=dict(boxstyle='round,pad=0.3', edgecolor='black', facecolor='white'))
            SNR_values.append(SNR)

            try:
                time = runlog[:,3][runlog[:,1] == f'{run}:'][0].split(':')
            except:
                print(f'Time for run {run} cannot be found in runlog')
                continue
            hour = int(time[0])-1
            minute = int(time[1])
            time_hour.append(hour)
            time_minute.append(minute)
            runnumbers_all.append(run)
        
            #print(f'SNR = {SNR}')
        plt.xlabel('Integral [ADC*tick]')
        plt.ylabel('Counts')
        plt.savefig(f'{image_folder_path}/{run}.jpg')
        plt.close()
    np.savez(f'{image_folder_path}_SNR.npz', SNR=SNR_values, time_hour=time_hour, time_minute=time_minute, runnumbers=runnumbers_all)
        #plt.title('spe Waveform Integral Plot \n (cold test, 47V bias, LED 16ns, 3V)')
        #plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate spe for files in a run log")
    parser.add_argument('runlog', help='run log path')
    args = parser.parse_args()
    main(args.runlog)
