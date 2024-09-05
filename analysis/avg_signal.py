import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
from tqdm import tqdm
import fire
import os
import h5py
from PIL import Image

def main(*filepath):
    colors = ['r', 'b', 'g', 'k', 'm', 'c', 'y']
    #labels = ['15ns', '20ns', '25ns', '30ns', '35ns', '40ns']
    os.system('rm -rf waveforms/*.png') 
    plt.figure(figsize=(8,6))
    save_gif = False
    for i,filename in enumerate(tqdm(filepath)):
        if '.csv' in filename:
            data = np.loadtxt(filename, delimiter=' ', skiprows=0)[:]
        elif '.hdf5' in filename:
            with h5py.File(filename, 'r') as f:
                data = np.array(f['data']).astype('float')
        else:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHH')
            raise Exception('File type not recognized')
        wvfm_sum = np.zeros(len(data[0]))
        nwvfm = 0
        filenames = []
        for k, wvfm in enumerate(data):
            wvfm -= np.mean(wvfm[0:200])
            #wvfm_sum += wvfm
            #nwvfm+=1
            if np.min(wvfm[690:730]) < -8.5 and np.min(wvfm[690:730]) > -14:
                if save_gif:
                    plt.figure()
                    plt.plot(wvfm)
                    filename=f'waveforms/waveform_{k}.png'
                    plt.savefig(filename)
                    filenames.append(filename)
                    plt.close()
                wvfm_sum += wvfm
                nwvfm += 1
        #avg_wvfm = np.sum(data,axis=0)/len(data)
        avg_wvfm = wvfm_sum/nwvfm
        ticks = np.arange(len(avg_wvfm))
        plt.plot(ticks[400:1400], avg_wvfm[400:1400], color=colors[i])
        #plt.vlines(ticks[np.argmin(np.diff(avg_wvfm))-6], ymin=np.min(avg_wvfm)*1.1, ymax=np.max(avg_wvfm)*1.1)
    #np.save('Single_PE_Template_44pt5V_2250VG', avg_wvfm[600:1200])
    if save_gif:
        images = [Image.open(filename) for filename in filenames]
        gif_filename='waveforms.gif'
        images[0].save(gif_filename, save_all=True, append_images=images[1:], duration=500, loop=0)
    plt.xlabel('16ns time ticks')
    plt.ylabel('ADC counts')
    #plt.title('LED Signals HD Module in Dewar at Warm \n (more optimal pulser config)')
    #plt.title('Pulser Noise HD Module in Dewar \n' + f'(channel {ch}, AFE {afe})')
    plt.title('Average 1 p.e. signal in CSU LN2 setup')
    plt.legend()
    #plt.xlim(560, 900)
    #plt.ylim(-15, 3)
    #plt.hist(rms_values)
    #plt.xlabel('ADC RMS')
    #plt.ylabel('Counts')
    plt.show()
    

if __name__ == "__main__":
    fire.Fire(main)
