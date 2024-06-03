import matplotlib.pyplot as plt
import numpy as np
import warnings
import time
import argparse

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

def main():
    ch = 4
    afe = 0
    filenames = [f'run39_2024516/VGAIN1p0/run39_2024516_EP110_VGAIN1p0_offset1118_OIsOFF_channel{ch}_AFE{afe}.csv', \
                f'run40_2024516/VGAIN1p0/run40_2024516_EP110_VGAIN1p0_offset1118_OIsOFF_channel{ch}_AFE{afe}.csv']
    colors = ['r', 'g', 'b']
    labels = ['Clean Room \n Wrapped Module', 'In Dewar \n Mini Module']
    for i, filename in enumerate(filenames):
        data = np.loadtxt(filename, delimiter=' ')[0:1000]
        rms_values = []
        for wvfm in data:
            rms = calculate_rms_deviation(wvfm)
            rms_values.append(rms)
        
        plt.hist(rms_values, range=(0,5),bins=100,color=colors[i], label=labels[i], alpha=0.5)
    #plt.hist(rms_values)
    plt.xlabel('ADC RMS')
    plt.ylabel('Counts')
    plt.xlim(1,3)
    plt.title(f'Waveform RMS \n Open Channel \n' + f'(channel {ch}, AFE {afe})')
    plt.legend()
    plt.show()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make RMS distributions")
    args = parser.parse_args()
    main()
