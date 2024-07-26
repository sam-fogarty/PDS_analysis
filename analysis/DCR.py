import matplotlib.pyplot as plt
import numpy as np
import argparse
from scipy.signal import butter, filtfilt
from tqdm import tqdm
from scipy.signal import correlate
import h5py
import os

def apply_filter(waveform, cutoff_freq, order):
    """
    Apply a filter to the input waveform.

    Parameters:
        waveform (array_like): Input waveform array.
        cutoff_freq (float): Cutoff frequency of the high-pass filter in Hz.
        order (int): Order of the high-pass filter.

    Returns:
        array_like: Filtered waveform.
    """
    sampling_freq = 62.5e6
    normalized_cutoff_freq = cutoff_freq / (sampling_freq / 2)
    b, a = butter(order, normalized_cutoff_freq, btype='lowpass', analog=False)
    filtered_waveform = filtfilt(b, a, waveform)

    return filtered_waveform

def calculate_rms_deviation(array):
    mean = np.mean(array)
    deviations = array - mean
    squared_deviations = deviations ** 2
    mean_squared_deviation = np.mean(squared_deviations)
    rms_deviation = np.sqrt(mean_squared_deviation)
    return rms_deviation

def main(filepath, run_end):
    ###### DCR calculation
    threshold = -7 # set below 1 p.e. level
    run_start = int(filepath.strip('.hdf5').strip('.csv').split('run')[-1])
    run_end = int(run_end)
    dirname = os.path.dirname(filepath)
    DCR_filename='DCR_measurements.npz'
    mean_rms, std_rms = [],[]
    if run_end is not None:
        runlog = np.loadtxt('../cpp/run_log.txt', delimiter=' ', dtype=str)
        runs = np.arange(run_start, run_end+1)
        time_hour, time_minute = [], []
        DCR_all, DCR_err_all = [], []
        runnumbers_all = []
    else:
        runs = [run_start]
    k=-1
    for run in runs:
        if os.path.exists(DCR_filename) and run_end is not None:
            DCR_data = np.load(DCR_filename)
            runnumbers_file = DCR_data['runnumbers_all']
            if run in runnumbers_file:
                print(f'skipping run{run}, its data is already in the DCR file')
                continue
            else:
                k+=1
        # load data
        skiprows=0
        run_filepath = f'{dirname}/run{run}.hdf5'
        
        print(f'Loading waveforms from {run_filepath}')
        if '.csv' in filepath:
            wvfms_orig = np.loadtxt(run_filepath, delimiter=' ', skiprows=skiprows)
        elif '.hdf5' in filepath:
            with h5py.File(run_filepath, 'r') as f:
                wvfms_orig = np.array(f['data'])
        else:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
            raise Exception('File type not recognized')

        rms_values = []
        for wvfm in wvfms_orig[:500]:
            rms = calculate_rms_deviation(wvfm)
            rms_values.append(rms)
        mean_rms.append(np.mean(rms_values))
        std_rms.append(np.std(rms_values))
        print(f'mean waveform rms (pre-filtering) = {mean_rms[k]}')

        wvfms_orig_indices = np.arange(0, len(wvfms_orig), 1)
        nWvfms = len(wvfms_orig)
        print('Finished loading waveforms.')
        # apply low pass to waveforms
        cutoff_freq = 3.5e6
        order=2
        wvfms = apply_filter(wvfms_orig, cutoff_freq, order)

        # remove waveforms with large overall standard deviations
        std_cut = 8
        std_mask = np.std(wvfms, axis=1) < std_cut
        wvfms = wvfms[std_mask]
        wvfms_less = np.sum(~std_mask) # make sure to subtract these from the total time in the end
        wvfms_orig_indices = wvfms_orig_indices[std_mask]
        # subtract baseline
        baseline = np.mean(wvfms, axis=1)
        wvfms = wvfms - baseline[:, np.newaxis]

        # find above threshold samples; select waveforms with above threshold samples
        threshold_mask = wvfms < threshold
        wvfms = wvfms[np.sum(threshold_mask, axis=1) > 0]
        wvfms_orig_indices = wvfms_orig_indices[np.sum(threshold_mask, axis=1) > 0]
        
        template = np.load('Single_PE_Template_2.npy')
        start, end = 50, 550 # select signal in template
        template = template[start:end]

        correlation_threshold = 1500 # can increase this to get less large signals
        extra_signals = 0
        keep_array = np.zeros(len(wvfms), dtype=bool)
        amplitudes = []

        x = 0
        # loop through each waveform and find ones with good correlation between template and itself
        for j, wvfm in tqdm(enumerate(wvfms)):
            i = 0
            # loop through each waveforms points to test each section for correlation
            while i < len(wvfm) - 50: # probably safe to stop a bit before the end of waveform
                if end-start+i > len(wvfm): # if near end of wvfm, slice template appropriately to fit
                    wvfm_end = len(wvfm)
                else:
                    wvfm_end = end-start+i
                signal = wvfm[i:wvfm_end]
                correlation = correlate(signal, template, mode='same')
                i += 5 # for speed skip ahead
                if (np.max(correlation) > correlation_threshold) and np.any(signal < threshold):
                    # keep track of which waveforms have any good correlations
                    if keep_array[j] == True and np.any(signal < threshold):
                        extra_signals += 1
                        #np.save(f'wvfm_{i}.npy', wvfms_orig[wvfms_orig_indices[j]])
                    else:
                        keep_array[j] = True
                        amplitudes.append(np.min(wvfm))
                        #np.save(f'wvfm_{i}.npy', wvfms_orig[wvfms_orig_indices[j]])
                    i += 500 # skip ahead past the current signal and look for more signals in same waveform
            x +=1
        #np.save('amplitudes.npy', amplitudes)
        print(f'Keep {np.sum(keep_array)} waveforms due to good correlation')
        print(f'Found {extra_signals} extra signals in waveforms')
        wvfms = wvfms[keep_array] # keep only waveforms with good correlations
            
        # print results
        NDCR = len(wvfms)+extra_signals
        print(f'Total number of signals found = {NDCR}')
        
        totaltime = ((nWvfms-wvfms_less)*len(wvfms[0])*16e-9)
        DCR = NDCR/totaltime
        DCR_err = np.sqrt(NDCR)/totaltime
        nsipms = 48
        print(f'DCR = {DCR:.2f} +/- {DCR_err:.2f} Hz, {(DCR/(nsipms*36)):.2f} +/- {(DCR_err/(nsipms*36)):.2f} Hz/mm^2')
        #print('Fractional uncertainty = ', DCR_err/DCR)

        if run_end is not None:
            try:
                time = runlog[:,3][runlog[:,1] == f'{run}:'][0].split(':')
            except:
                print(f'Time for run {run} cannot be found in runlog')
                continue
            hour = int(time[0])-1
            minute = int(time[1])
            time_hour.append(hour)
            time_minute.append(minute)
            DCR_all.append(DCR)
            DCR_err_all.append(DCR_err)
            runnumbers_all.append(run)

    if os.path.exists(DCR_filename) and run_end is not None:
        DCR_data = np.load(DCR_filename)
        DCR_all = np.concatenate((DCR_data['DCR_all'], DCR_all/(nsipms*36)))
        DCR_err_all = np.concatenate((DCR_data['DCR_err_all'], DCR_err_all/(nsipms*36)))
        time_hour = np.concatenate((DCR_data['time_hour'], time_hour))
        time_minute = np.concatenate((DCR_data['time_minute'], time_minute))
        runnumbers_all = np.concatenate((DCR_data['runnumbers_all'], runnumbers_all))
        mean_rms = np.concatenate((DCR_data['mean_rms'], mean_rms))
        std_rms = np.concatenate((DCR_data['std_rms'], std_rms))

    if run_end is not None:
        if os.path.exists(DCR_filename):
            print(f'Adding new DCR data to {DCR_filename}')
        else:
            print(f'Saving DCR data to {DCR_filename}')
        np.savez(DCR_filename, DCR_all=DCR_all, DCR_err_all=DCR_err_all, time_hour=time_hour, time_minute=time_minute, runnumbers_all=runnumbers_all, mean_rms=mean_rms, std_rms=std_rms)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate Dark Count Rate")
    parser.add_argument('filepath', help='Input filepath')
    parser.add_argument('run_end', default=None, help='Input filepath')
    args = parser.parse_args()
    main(args.filepath, args.run_end)
