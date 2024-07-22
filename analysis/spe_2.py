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
    startTime = 1138
    integrationWindow = 15
    window_size = 1 # rolling average window size

    do_gaussian_fit = True
    
    def Gaussian2(x, mu1, mu2, sigma1, sigma2, A1, A2):
        return A1*np.exp(-(mu1-x)**2/(2*sigma1))+A2*np.exp(-(mu2-x)**2/(2*sigma2))
    
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
        wvfm -= np.mean(wvfm[0:500])
        integral = np.trapz(wvfm[startTime:startTime+integrationWindow], dx=1)
        integrals.append(integral)
    hist_range = (-100, 1000)
    hist = np.histogram(integrals, bins = round((1/6)*(max(integrals)-min(integrals))))
    hist_bins, hist_bincenters = hist[0], hist[1][:-1]
    x_values = np.arange(hist_range[0], hist_range[1], 1)
    if do_gaussian_fit:

        peaks = signal.find_peaks(hist[0], height = 0.5*max(hist[0]))
        print(peaks)
        data = hist[0][:(peaks[0][1]+round(0.25*abs(hist[1][peaks[0][0]]-hist[1][peaks[0][1]])))]
        fit, error = curve_fit(Gaussian2, hist[1][:len(hist[0])], hist[0], p0=[hist[1][peaks[0][0]], hist[1][peaks[0][1]], 100, 100, hist[0][peaks[0][0]], hist[0][peaks[0][1]]])
        plt.plot(hist[1][:len(hist[0])], hist[0])
        plt.plot(hist[1], Gaussian2(hist[1], *fit))
        snr = fit[1]/np.sqrt(fit[2])

        mean0, mean1, var0, var1, height0, height1 = fit
        stdv0 = np.sqrt(var0)
        stdv1 = np.sqrt(var1)
        SNR = mean1/stdv0

        plt.annotate(r'$\sigma_b$ = '+ f'{stdv0:.2f} ADC*ns\n' \
                + r'$\mu_b$ = ' + f'{mean0:.2f} ADC*ns\n' \
                r'$\sigma_1$ = '+ f'{stdv1:.2f} ADC*ns\n' \
                + r'$\mu_1$ = ' + f'{mean1:.2f} ADC*ns\n' \
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
