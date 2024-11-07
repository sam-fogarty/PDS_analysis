import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse
from tqdm import tqdm
from scipy import signal
from scipy.optimize import curve_fit
import h5py

def main(filepath):
    startTime = 699
    integrationWindow = 30
    window_size = 1 # rolling average window size

    do_gaussian_fit = True
    
    def Gaussian3(x, mu1, mu2, mu3, sigma1, sigma2, sigma3, A1, A2, A3):
        return A1*np.exp(-(mu1-x)**2/(2*sigma1))+A2*np.exp(-(mu2-x)**2/(2*sigma2))+A3*np.exp(-(mu3-x)**2/(2*sigma3))
    
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
        wvfm = wvfm.astype(float)
        wvfm -= np.mean(wvfm[0:500])
        #print(wvfm[680:720])
        integral = np.trapz(wvfm[startTime:startTime+integrationWindow], dx=1)
        integrals.append(integral)
    #hist_range = (-2000, 3000)
    hist = np.histogram(integrals, bins = round((1/80)*(max(integrals)-min(integrals))))
    hist_bins, hist_bincenters = hist[0], hist[1][:-1]
    #x_values = np.arange(hist_range[0], hist_range[1], 1)
    plt.plot(hist[1][:len(hist[0])], hist[0])
    if do_gaussian_fit:

        peaks = signal.find_peaks(hist[0], height = 0.3*max(hist[0]))
        print(peaks)
        data = hist[0][:(peaks[0][2]+round(0.1*abs(hist[1][peaks[0][0]]-hist[1][peaks[0][1]])))]
        fit, error = curve_fit(Gaussian3, hist[1][:len(data)], data, p0=[hist[1][peaks[0][0]], hist[1][peaks[0][1]], hist[1][peaks[0][2]], 200, 200, 200, hist[0][peaks[0][0]], hist[0][peaks[0][1]], hist[0][peaks[0][2]]])

        #plt.plot(hist[1][:len(hist[0])], hist[0])
        plt.plot(hist[1][:len(data)], Gaussian3(hist[1][:len(data)], *fit))
        snr = fit[1]/np.sqrt(fit[3])

        mean0, mean1, mean2, var0, var1, var2, height0, height1, height2 = fit
        stdv0 = np.sqrt(var0)
        stdv1 = np.sqrt(var1)
        stdv2 = np.sqrt(var2)
        SNR = mean1/stdv0
        print(f'SNR = {SNR}')
        plt.annotate(r'$\sigma_b$ = '+ f'{stdv0:.2f} ADC*ns\n' \
                + r'$\mu_b$ = ' + f'{mean0:.2f} ADC*ns\n' \
                r'$\sigma_1$ = '+ f'{stdv1:.2f} ADC*ns\n' \
                + r'$\mu_1$ = ' + f'{mean1:.2f} ADC*ns\n' \
                + 'SNR = ' + f'{SNR:.2f}', xy=(5000, 400),fontsize=10, color='red',
                             bbox=dict(boxstyle='round,pad=0.3', edgecolor='black', facecolor='white'))

    plt.xlim(-1500, 10000)
    #plt.hist(rms_values)
    plt.xlabel('Integral [ADC*tick]')
    plt.ylabel('Counts')
    #plt.title('spe Waveform Integral Plot \n (cold test, 45V bias, LED 9.3ns, 3.5V, VGAIN=2000)')
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    parser.add_argument('filepath', help='Input filepath')
    args = parser.parse_args()
    main(args.filepath)
