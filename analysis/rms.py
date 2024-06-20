import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import fire
import os

class fft:
    def __init__(self, sig, dt=16e-9, plot=False):
        np.seterr(divide = 'ignore') 
        if dt is None:
            dt = 1
            t = np.arange(0, sig.shape[-1])
            xLabel = "samples"
        else:
            t = np.arange(0, sig.shape[-1]) * dt
            xLabel = "freq [Hz]"

        if sig.shape[0] % 2 != 0:
            warnings.warn("signal preferred to be even in size, autoFixing it...")
            t = t[:-1]
            sig = sig[:-1]

        sigFFT = np.fft.fft(sig) / t.shape[0] 

        freq = np.fft.fftfreq(t.shape[0], d=dt)

        firstNegInd = np.argmax(freq < 0)
        freqAxisPos = freq[:firstNegInd]
        sigFFTPos = 2 * sigFFT[:firstNegInd] 

        if plot:
            plt.figure()
            plt.plot(freqAxisPos, 20*np.log10(np.abs(sigFFTPos)/2**14))
            plt.ylim([-140, -80])
            plt.xscale("log")
            plt.xlabel(xLabel)
            plt.ylabel("U.A.")
            plt.title("Analytic FFT plot")
            plt.show()

        self.x = freqAxisPos /10e5
        self.y = 20*np.log10(np.abs(sigFFTPos)/2**14)
#wf=readwave(plot=True).wf
#f=fft   (wf,dt=None,plot=True)     
        
class mean_fft:
    def __init__(self, data,label=None,plot=False):
        np.seterr(divide = 'ignore') 
        fft_list_x=[]
        fft_list_y=[]
        std_list=[]
        for k in range(len(data)):
            fft_list_x.append(fft(data[k]).x)
            fft_list_y.append(fft(data[k]).y)
            std_list.append(np.std(data[k],axis=0))
        self.x=np.mean(fft_list_x,axis=0) 
        self.y=np.mean(fft_list_y,axis=0)
        self.stdx=np.mean(std_list,axis=0)
        if plot:
            plt.rcParams["figure.figsize"] = (10,7)
            plt.figure()
            plt.plot(self.x,self.y,linewidth=1,label=f'{label} \t rms={np.round(self.stdx,2)}'.expandtabs())
            plt.ylim([min(self.y)-10, -80])
            #plt.xscale("log")
            # plt.xlim([0.2, 3])
            plt.legend()
            plt.ylabel("dBFS")
            plt.xlabel("MHz")
            plt.title("FFT")
            plt.tight_layout()

def calculate_rms_deviation(array):
    mean = np.mean(array)
    deviations = array - mean
    squared_deviations = deviations ** 2
    mean_squared_deviation = np.mean(squared_deviations)
    rms_deviation = np.sqrt(mean_squared_deviation)
    return rms_deviation

def main(*filenames):
    colors = ['r', 'b', 'k', 'm', 'y', 'g']
    linestyles = ['-', '--', '-.', '.', '-', '--']
    if not len(filenames):
        raise Exception('Include some csv files!')
    median_rms = []
    for i, filename in enumerate(filenames):
        data = np.loadtxt(filename, delimiter=' ')[0:1000]
        rms_values = []
        for wvfm in data:
            rms = calculate_rms_deviation(wvfm)
            rms_values.append(rms)
        median_rms.append(np.median(rms))
        plot_data = plt.hist(rms_values, range=(0, 10),bins=250,color=colors[i], label=os.path.basename(filename).strip('.csv')+'\n'+f'median rms = {median_rms[i]}', alpha=0.5)
        bin_contents = plot_data[0]
        plt.vlines(x=median_rms[i], ymin=0, ymax=max(bin_contents)*1.2)
    #plt.hist(rms_values)
    plt.xlabel('ADC RMS')
    plt.ylabel('Counts')
    #plt.xlim(1,3)
    plt.title(f'Waveform RMS')
    plt.legend()
    plt.show()
    

if __name__ == "__main__":
    fire.Fire(main)
