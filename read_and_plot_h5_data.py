import h5py
import numpy as np
import matplotlib.pyplot as plt

filename = 'daphne_fnal_LED_config1_VGAIN300_Feb272024.h5'
f = h5py.File(filename, 'r')

i = 0
subtract_pedestal = True

while True:
    if subtract_pedestal:
        start = 0
        end = 250
        pedestal = np.mean(f['waveforms'][i]['adc'][start:end])
    else:
        pedestal = 0
    wvfm = (f['waveforms'][i]['adc'] - pedestal)*-1
    
    fig = plt.figure(figsize=(8, 6))
    root = fig.canvas.manager.window.winfo_toplevel()
    root.geometry("800x600+100+100")
    plt.plot(wvfm)
    plt.xlabel('ticks')
    plt.ylabel('ADCs')
    plt.title(f'Waveform {i}')
    plt.show(block=False)
    plt.pause(1)    
    user_input = input("Enter index of waveform to plot, 'a' to plot next waveform, or 'q' to quit: \n")
    if user_input == 'q':
        break
    elif user_input == 'a':
        i += 1
        plt.close()
        continue
    elif user_input.isnumeric():
        i = int(user_input)
        plt.close()
f.close()
