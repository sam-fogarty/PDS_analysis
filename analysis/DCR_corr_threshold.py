import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN
import h5py
import argparse
from tqdm import tqdm

def main(filepath, mode):

    # load single p.e. template
    template = np.load('Single_PE_Template_45V_800VG.npy')
    peak_index = np.where(template == np.min(template))[0][0]

    # load waveforms
    with h5py.File(filepath) as f:
        wvfms = np.array(f['data'])

    # subtract baseline
    baseline = np.mean(wvfms, axis=1)
    wvfms = wvfms - baseline[:, np.newaxis]

    # pick number of fake signals to add, find indices to place them at (this is random)
    prob_factor=0.98
    insert_index = (np.random.random(len(wvfms))*wvfms.shape[1]).astype('int')
    insert_or_not = np.random.random(len(wvfms)) < prob_factor
    counts=np.sum(~insert_or_not)
    print('Total signals inserted = ', counts)
    DCR = (counts/(wvfms.shape[0]*wvfms.shape[1]*16e-9))/(48*36)
    print('Fake DCR = ', DCR, ' Hz/mm^2')
    
    # insert fake signals
    peak_indices = []
    for i in tqdm(range(len(wvfms))):
        if insert_or_not[i]:
            peak_indices.append(None)
            continue # don't insert
        else:
            if insert_index[i]+len(template) >= wvfms.shape[1]:
                end = wvfms.shape[1]
            else:
                end = insert_index[i]+len(template)
            wvfms[i][insert_index[i]:end] = wvfms[i][insert_index[i]:end] + template[0:end-insert_index[i]]
            peak_indices.append(insert_index[i]+peak_index)
    
    if mode == 0:
        # simple threshold
        threshold = -95
        print(f'Using simple threshold of {threshold} to find dark counts')
        buffer =10 # for looking up if there is a true dark count nearby
        eps = 10 # points, for dbscan clustering
        min_samples = 1 # minimum number of points allowed in a group
        wvfms_orig_indices = np.arange(0, len(wvfms), 1)
        threshold_mask = (wvfms < threshold) #& ~(wvfms < lower_threshold)

        found_true_peaks = 0
        found_false_peaks = 0
        unique_labels_found = 0

        false_wvfm_indices = []
        true_wvfm_indices = []
        for i, wvfm in enumerate(wvfms):
            mask = wvfm < threshold
            if np.any(mask):
                indices = np.where(mask)[0]
                peak_index = peak_indices[i]
                
                # group together points above threshold
                db = DBSCAN(eps=eps, min_samples=min_samples).fit(indices[:,np.newaxis])
                unique_labels = np.unique(db.labels_)
                for label in unique_labels:
                    unique_labels_found += 1
                    center = np.mean(indices[db.labels_ == label])
                    if peak_index is not None:
                        if np.any(center > peak_index - buffer) and np.any(center < peak_index + buffer):
                            found_true_peaks += 1
                            true_wvfm_indices.append(i)
                        else:
                            found_false_peaks += 1
                            false_wvfm_indices.append(i)
                    else:
                        found_false_peaks += 1
                        false_wvfm_indices.append(i)
    elif mode == 1:
        # find above threshold samples; select waveforms with above threshold samples
        threshold_mask = (wvfms < threshold) #& ~(wvfms < lower_threshold)
        points_above = 0
        wvfms = wvfms[np.sum(threshold_mask, axis=1) > points_above]
    else:
        raise ValueError('No such mode')


    print(f'unique labels found = {unique_labels_found}')
    print(f'real peaks found = {found_true_peaks}')
    print(f'fake peaks found = {found_false_peaks}')
    print(f'total peaks found = {found_true_peaks + found_false_peaks}')
    print(f'total original peaks = {counts}')
    print(f'efficiency of finding true peaks = {found_true_peaks/counts}')
    print(f'purity of true peaks = {found_true_peaks / (found_true_peaks+found_false_peaks)}')
    #wvfms_new = wvfms_withfilter[np.sum(threshold_mask, axis=1).astype('bool')]
    #wvfms_orig_indices = wvfms_orig_indices[np.sum(threshold_mask, axis=1).astype('bool')]
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate Dark Count Rate")
    parser.add_argument('filepath', help='Filepath to below breakdown DCR run')
    parser.add_argument('--mode', default=1,help='Mode for finding DCs; 0 for simple threshold, 1 for correlation')
    args = parser.parse_args()
    main(args.filepath, args.mode)
