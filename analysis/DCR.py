import matplotlib.pyplot as plt
import numpy as np
import argparse
from scipy.signal import butter, filtfilt
from tqdm import tqdm
from scipy.signal import correlate
import h5py

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

def main(filepath):
    ###### DCR calculation
    threshold = -7 # set below 1 p.e. level

    # load data
    skiprows=0
    print(f'Loading waveforms from {filepath}')
    if '.csv' in filepath:
        wvfms_orig = np.loadtxt(filepath, delimiter=' ', skiprows=skiprows)
    elif '.hdf5' in filepath:
        with h5py.File(filepath, 'r') as f:
            wvfms_orig = np.array(f['data'])
    else:
        print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
        raise Exception('File type not recognized')
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
    
    template = np.load('Single_PE_Template.npy')
    start, end = 560, 900 # select signal in template
    template = template[start:end]

    correlation_threshold = 1000 # can increase this to get less large signals
    extra_signals = 0
    keep_array = np.zeros(len(wvfms), dtype=bool)
    amplitudes = []
    not_DC_indices = []
    DC_indices = []     #which waveforms have DC's
    not_DC_indices2 = []
    DC_indices2 = []    #where DC is in waveform

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
                DC_indices.append(wvfms_orig_indices[j])
                DC_indices2.append(i)
                # keep track of which waveforms have any good correlations
                if keep_array[j] == True and np.any(signal < threshold):
                    extra_signals += 1
                    #np.save(f'wvfm_{i}.npy', wvfms_orig[wvfms_orig_indices[j]])
                else:
                    keep_array[j] = True
                    amplitudes.append(np.min(wvfm))
                    '''
                    if (np.max(correlation) < 1500) & (np.max(correlation) > 1200):
                        not_DC_indices.append(wvfms_orig_indices[j])
                        not_DC_indices2.append(i)
                    elif np.max(correlation) > 1500:
                        DC_indices.append(wvfm_orig_indices[j])
                        DC_indices2.append(i)
                    '''
                    #np.save(f'wvfm_{i}.npy', wvfms_orig[wvfms_orig_indices[j]])
                i += 500 # skip ahead past the current signal and look for more signals in same waveform
        x +=1
    np.save('amplitudes.npy', amplitudes)
    print(f'Keep {np.sum(keep_array)} waveforms due to good correlation')
    print(f'Found {extra_signals} extra signals in waveforms')
    print(not_DC_indices)
    print(DC_indices)
    print(not_DC_indices2)
    print(DC_indices2)
    wvfms = wvfms[keep_array] # keep only waveforms with good correlations
        
    # print results
    NDCR = len(wvfms)+extra_signals
    print(f'Total number of signals found = {NDCR}')
    
    totaltime = ((nWvfms-wvfms_less)*len(wvfms[0])*16e-9)
    DCR = NDCR/totaltime
    DCR_err = np.sqrt(NDCR)/totaltime
    print(f'DCR = {DCR:.2f} +/- {DCR_err:.2f} Hz, {(DCR/(6*36)):.2f} +/- {(DCR_err/(6*36)):.2f} Hz/mm^2')
    #print('Fractional uncertainty = ', DCR_err/DCR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate Dark Count Rate")
    parser.add_argument('filepath', help='Input filepath')
    args = parser.parse_args()
    main(args.filepath)
