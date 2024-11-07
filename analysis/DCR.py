import matplotlib.pyplot as plt
import numpy as np
import argparse
from scipy.signal import butter, filtfilt
from tqdm import tqdm
from scipy.signal import correlate
import h5py
import os
import time as timer
from sklearn.cluster import DBSCAN

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

def main(filepath, run_end, DCR_filename, runlog, template_path, mock_data, corr_threshold, corr_threshold_filename):
    np.random.seed(15)
    print('mock_data = ', mock_data)
    if filepath is None and runlog is None:
        raise Exception('Either provide a filepath or runlog')
    if corr_threshold is None:
        correlation_threshold = 100000
    else:
        correlation_threshold = int(corr_threshold)
    print(f'Finding dark counts with correlation threshold of {correlation_threshold}')
    ###### DCR calculation
    mock_data = bool(mock_data)

    threshold = -12 # set below 1 p.e. level
    lower_threshold = -200
    
    dirname = '../cpp/data'
    if DCR_filename is None and runlog is not None:
        DCR_filename=f"DCR_measurements_{runlog.split('.')[0]}.npz"
    elif DCR_filename is not None:
        DCR_filename=str(DCR_filename)
    else:
        DCR_filename=f"DCR_measurements_test.npz"
    
    mean_rms, std_rms = [],[]
    if runlog is not None:
        if runlog is not None:
            runlog_path = runlog
        else:
            runlog_path='../cpp/run_log.txt'
        runlog = np.loadtxt(runlog_path, delimiter=' ', dtype=str)
        runs=[]
        for i in range(len(runlog)):
            runs.append(int(runlog[i][1].strip(':')))
        #runs = np.arange(run_start, run_end+1)
        time_hour, time_minute = [], []
        DCR_all, DCR_err_all = [], []
        runnumbers_all = []
        if run_end is not None:
            run_end = int(run_end)
        else:
            run_end = runs[-1]
    else:
        run = int(filepath.split('.hdf5')[0].split('.csv')[0].split('run')[-1])
        runs = [run]
    k=-1
    for run in runs:
        start_time = timer.time()
        if os.path.exists(DCR_filename):# and run_end is not None:
            DCR_data = np.load(DCR_filename)
            runnumbers_file = DCR_data['runnumbers_all']
            if run in runnumbers_file:
                print(f'skipping run{run}, its data is already in the DCR file')
                continue
            else:
                k+=1
        if run_end is not None and run >= run_end:
            break
        # load data
        skiprows=0
        run_filepath = f'{dirname}/run{run}.hdf5'
        
        print(f'Loading waveforms from {run_filepath}')
        if not os.path.exists(run_filepath):
            print(f'{run_filepath} not found, continuing')
            continue
        if '.csv' in run_filepath:
            wvfms_orig = np.loadtxt(run_filepath, delimiter=' ', skiprows=skiprows)
        elif '.hdf5' in run_filepath:
            try:
                with h5py.File(run_filepath, 'r') as f:
                    wvfms_orig = np.array(f['data'])
            except:
                print('Could not find file ', run_filepath)
                continue
        else:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
            raise Exception('File type not recognized')

        if template_path is None:
                #template = np.load('Single_PE_Template_45V_800VG.npy')
                template = np.load('Single_PE_Template_45V_2000VG.npy')
        else:
                template = np.load(template_path)

        if mock_data: 
            # load single p.e. template
            
            peak_index = np.where(template == np.min(template))[0][0]

            # subtract baseline
            baseline = np.mean(wvfms_orig, axis=1)
            wvfms_orig = wvfms_orig - baseline[:, np.newaxis]

            # pick number of fake signals to add, find indices to place them at (this is random)
            prob_factor=0.98
            insert_index = (np.random.random(len(wvfms_orig))*wvfms_orig.shape[1]).astype('int')
            insert_or_not = np.random.random(len(wvfms_orig)) < prob_factor
            #counts=np.sum(~insert_or_not)
            
            #insert_end = 3500
            insert_start = 0
            insert_end = wvfms_orig.shape[1]

            # insert fake signals
            peak_indices = []
            total_counts = 0
            for i in tqdm(range(len(wvfms_orig))):
                if insert_or_not[i] or insert_index[i] > insert_end or insert_index[i] < insert_start:
                    peak_indices.append(None)
                    continue # don't insert
                else:
                    if insert_index[i]+len(template) >= insert_end:
                        end = insert_end
                    else:
                        end = insert_index[i]+len(template)
                    wvfms_orig[i][insert_index[i]:end] = wvfms_orig[i][insert_index[i]:end] + template[0:end-insert_index[i]]
                    peak_indices.append(insert_index[i]+peak_index)
                    total_counts += 1

            print('Total signals inserted = ', total_counts)
            #True_DCR = (counts/(wvfms_orig.shape[0]*wvfms_orig.shape[1]*16e-9))/(48*36)
            True_DCR = (total_counts/(wvfms_orig.shape[0]*(insert_end-insert_start)*16e-9))/(48*36)
            print('Fake DCR = ', True_DCR, ' Hz/mm^2')

            peak_indices = np.array(peak_indices)
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
        cutoff_freq = 20e6
        order=2
        wvfms = apply_filter(wvfms_orig, cutoff_freq, order)

         # subtract baseline
        baseline = np.mean(wvfms, axis=1)
        wvfms = wvfms - baseline[:, np.newaxis]
        # remove waveforms with large overall standard deviations
        #std_cut = 50
        #std_mask = np.std(wvfms, axis=1) < std_cut
        #print('wvfms cut due to noise: ',np.sum(~std_mask))
        
        peak_to_peak = np.max(wvfms, axis=1) - np.min(wvfms, axis=1)
        counts, edges = np.histogram(peak_to_peak, bins=200, range=(0,400))
        mean_peak_to_peak = edges[:-1][np.argmax(counts)]
        std_peak_to_peak = np.std(peak_to_peak[peak_to_peak < mean_peak_to_peak])
        std_peak_to_peak_cut = 5.0*std_peak_to_peak
        #plt.step(edges[:-1], counts)
        #plt.show()
        std_mask = peak_to_peak < 400 #mean_peak_to_peak+std_peak_to_peak_cut
        wvfms = wvfms[std_mask]
        print('wvfms cut with std cut = ', np.sum(~std_mask))
        wvfms_less = np.sum(~std_mask) # make sure to subtract these from the total time in the end
        wvfms_orig_indices = wvfms_orig_indices[std_mask]
        if mock_data:
            peak_indices = peak_indices[std_mask]

        # find above threshold samples; select waveforms with above threshold samples
        threshold_mask = (wvfms < threshold) #& ~(wvfms < lower_threshold)
        threshold_mask_mask = np.sum(threshold_mask, axis=1) > 0
        wvfms = wvfms[threshold_mask_mask]
        print('wvfms cut using threshold = ', np.sum(~threshold_mask_mask))
        if mock_data:
            peak_indices = peak_indices[threshold_mask_mask]
        wvfms_orig_indices = wvfms_orig_indices[threshold_mask_mask]
        threshold_mask = threshold_mask[threshold_mask_mask]
        
        start, end = 50, 550 # select signal in template
        template = template[start:end]

        extra_signals = 0
        keep_array = np.zeros(len(wvfms), dtype=bool)
        
        x = 0

        corr_list = []
        signal_indices = []
        wvfm_indices = []
        true_signal_indices = []
        wvfm_size = len(wvfms[0])

        right_edge = len(wvfms[0]) - 0
        left_edge = 0
        if mock_data:
            notNoneMask = np.not_equal(peak_indices, None)
            counts -= np.count_nonzero((peak_indices[notNoneMask] > right_edge) | (peak_indices[notNoneMask] < left_edge))
            #True_DCR = (counts/(wvfms.shape[0]*wvfms.shape[1]*16e-9))/(48*36)
        # loop through each waveform and find ones with good correlation between template and itself
        signal_rms=[]
        for j, wvfm in tqdm(enumerate(wvfms)):
            i = left_edge
            # loop through each waveforms points to test each section for correlation
            #print('hello')
            found_signal = False
            while i < right_edge: # probably safe to stop a bit before the end of waveform
                #if j > 16:
                #    print(j, i)
                # set where to start iteration; saves time and should increase purity.
                # only does this at the beginning once, or after a signal has been found already.
                if i == 0 or found_signal:
                    threshold_indices = np.where(threshold_mask[j][i:])[0]
                    if np.count_nonzero(threshold_indices):
                        min_threshold_point = np.min(threshold_indices)
                        if min_threshold_point - 100 < i:
                            pass
                        elif min_threshold_point - 100 < left_edge:
                            i = left_edge
                        else:
                            i = min_threshold_point - 100
                    else:
                        break
                    found_signal = False
                if end-start+i > wvfm_size: # if near end of wvfm, slice template appropriately to fit
                    wvfm_end = wvfm_size
                else:
                    wvfm_end = end-start+i
                signal = wvfm[i:wvfm_end]
                
                correlation = correlate(signal, template, mode='same')
                i += 10 # for speed skip ahead
                #corr_list.append(np.max(correlation))
                
                signal_threshold = np.any(threshold_mask[j][i:wvfm_end])
                if (np.max(correlation) > correlation_threshold) and signal_threshold:
                    # keep track of which waveforms have any good correlations
                    if keep_array[j] == True:
                        extra_signals += 1
                    else:
                        keep_array[j] = True
                    signal_rms.append(np.std(signal))
                    signal_indices.append(i+np.where(signal == np.min(signal))[0][0])
                    wvfm_indices.append(j)
                    if mock_data:
                        true_signal_indices.append(peak_indices[j])
                    
                    i += 700 # skip ahead past the current signal and look for more signals in same waveform
                    found_signal = True
                #else:
                #    signal_indices.append(-1)
                #    wvfm_indices.append(j)
                #    true_signal_indices.append(peak_indices[j])
            x +=1
        signal_indices = np.array(signal_indices)
        #print('how many non-None true signal indices = ', np.sum(~np.equal(true_signal_indices, None)))
        #print('how many signal indices found = ', np.sum(signal_indices != -1))
        if mock_data:
            buffer = 50 # for looking up if there is a true dark count nearby

            found_true_peaks = 0
            found_false_peaks = 0

            false_wvfm_indices = []
            true_wvfm_indices = []
            # print(true_signal_indices)
            for i in tqdm(range(len(wvfm_indices))):
                #if true_signal_indices[i] is not None:
                    #print(signal_indices[i], true_signal_indices[i])
                if signal_indices[i] != -1 and true_signal_indices[i] is not None:
                    #print('found signal index = ', signal_indices[i])
                    #print('true signal index = ', true_signal_indices[i])
                    if signal_indices[i] > true_signal_indices[i] and signal_indices[i] < true_signal_indices[i] + buffer:
                        found_true_peaks += 1
                        true_wvfm_indices.append(i)
                    else:
                        found_false_peaks += 1
                        false_wvfm_indices.append(i)
                elif signal_indices[i] != -1 and true_signal_indices[i] is None:
                    found_false_peaks += 1
                    false_wvfm_indices.append(i)
            print(f'real peaks found = {found_true_peaks}')
            print(f'fake peaks found = {found_false_peaks}')
            print(f'total peaks found = {found_true_peaks + found_false_peaks}')
            print(f'total original peaks = {total_counts}')
            efficiency = found_true_peaks/total_counts
            print(f'efficiency of finding true peaks = {found_true_peaks/total_counts}')
            purity = found_true_peaks / (found_true_peaks+found_false_peaks)
            print(f'purity of true peaks = {purity}')

            
        #np.save('amplitudes.npy', amplitudes)
        #np.save('points_above_threshold.npy', points_above_threshold)
        print(f'Keep {np.sum(keep_array)} waveforms due to good correlation')
        print(f'Found {extra_signals} extra signals in waveforms')

        wvfms = wvfms[keep_array] # keep only waveforms with good correlations
            
        # print results
        NDCR = len(wvfms)+extra_signals
        print(f'Total number of signals found = {NDCR}')
        if len(wvfms):
            totaltime = ((nWvfms-wvfms_less)*len(wvfms[0])*16e-9)
            DCR = NDCR/totaltime
            DCR_err = np.sqrt(NDCR)/totaltime
            nsipms = 48
            DCR_mm2 = DCR/(nsipms*36)
            DCR_err_mm2 = DCR_err/(nsipms*36)
            mean_signal_rms = np.mean(signal_rms)
            print(f'mean signal rms = {mean_signal_rms}')
            print(f'DCR = {DCR:.3f} +/- {DCR_err:.3f} Hz, {(DCR_mm2):.3f} +/- {(DCR_err_mm2):.3f} Hz/mm^2')
            #print('Fractional uncertainty = ', DCR_err/DCR)

            if corr_threshold_filename is not None and mock_data:
                values = [str(correlation_threshold), str(efficiency), str(purity), str(found_true_peaks), str(found_false_peaks), str(DCR_mm2)]
                file_exists = os.path.exists(corr_threshold_filename)
                with open(corr_threshold_filename, 'a') as f:
                    if not file_exists:
                        f.write(f'True Real Signals, {total_counts} \n')
                        f.write(f'True DCR_mm2, {True_DCR}\n')
                        f.write('Correlation Threshold, Efficiency, Purity, Real Peaks, Fake Peaks, DCR_mm2 \n')
                    f.write(','.join(values) + '\n')

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
        end_time = timer.time()
        print(f'Total time = {(end_time-start_time):.2f} seconds')
    if os.path.exists(DCR_filename) and run_end is not None:
        DCR_data = np.load(DCR_filename)
        DCR_all = np.concatenate((DCR_data['DCR_all'], DCR_all))
        DCR_err_all = np.concatenate((DCR_data['DCR_err_all'], DCR_err_all))
        time_hour = np.concatenate((DCR_data['time_hour'], time_hour))
        time_minute = np.concatenate((DCR_data['time_minute'], time_minute))
        runnumbers_all = np.concatenate((DCR_data['runnumbers_all'], runnumbers_all))
        mean_rms = np.concatenate((DCR_data['mean_rms'], mean_rms))
        std_rms = np.concatenate((DCR_data['std_rms'], std_rms))
        signal_rms = np.concatenate((DCR_data['signal_rms'], mean_signal_rms))

    if run_end is not None:
        if os.path.exists(DCR_filename):
            print(f'Adding new DCR data to {DCR_filename}')
        else:
            print(f'Saving DCR data to {DCR_filename}')
        np.savez(DCR_filename, DCR_all=DCR_all, DCR_err_all=DCR_err_all, time_hour=time_hour, time_minute=time_minute, runnumbers_all=runnumbers_all, mean_rms=mean_rms, std_rms=std_rms, signal_rms=signal_rms)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate Dark Count Rate")
    parser.add_argument('--filepath', required=False, default=None, help='Input filepath')
    parser.add_argument('--run_end', required=False, default=None, help='Run to finish at.')
    parser.add_argument('--DCR_filename', required=False, default=None, help='Name of DCR file')
    parser.add_argument('--runlog', required=False, default=None, help='Path to runlog')
    parser.add_argument('--template', required=False, default=None, help='Path to single p.e. template')
    parser.add_argument('--mock_data', required=False, default=False, help='True or False, is input data to be used for mock data (below breakdown)')
    parser.add_argument('--corr_threshold', required=False, default=None, help='Correlation threshold to use for finding dark counts')
    parser.add_argument('--corr_threshold_filename', required=False, default=None, help='Optional filename to store efficiency and purity values for a correlation threshold value')

    args = parser.parse_args()
    main(args.filepath, args.run_end, args.DCR_filename, args.runlog, args.template, args.mock_data, args.corr_threshold, args.corr_threshold_filename)
