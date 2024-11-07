import numpy as np
import matplotlib.pyplot as plt
import argparse

def main(filepath):
    file = filepath
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(12,6), sharex=True)
    data = np.load(file, allow_pickle=True)
    time_hour = data['time_hour'].astype('float')
    time_minute = data['time_minute'].astype('float')
    SNR = data['SNR'].astype('float')
    #runnumbers = data['runnumbers_all'].astype('int')
    time = []
    time_float = []

    for i in range(len(time_hour)):
        time.append(f'{time_hour[i]}:{time_minute[i]}')
        time_float.append(float(time_hour[i]) + float(time_minute[i])/60)

    axes.plot(np.array(time_float)+0.008333, SNR, 'bo', markersize=3)
    axes.set_ylim(np.min(SNR)-1, np.max(SNR) + 1)
    increment = 0.25
    tick_locations = np.arange(min(time_hour), max(time_hour)+1, increment)
    time_label = []
    hour = min(time_hour)
    minute = 0
    for i in range(len(tick_locations)):
        if minute < 0.2:
            minute_label = f'0{int(minute*60)}'
        else:
            minute_label = f'{int(minute*60)}'

        time_label.append(f'{int(hour)}:{minute_label}')
        minute += increment 
        if minute >= 1:
            hour += 1
            minute = 0
    
    #time_label = ['14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30', '18:00', '18:30', '19:00']
    #axes[0].set_xticks(tick_locations)
    #axes[0].set_xticklabels(time_label)
    #plt.xticks(rotation=45)
    axes.set_ylabel('SNR')
    axes.set_xlabel('Local Time of Datataking')

    #mean_rms = mean_rms[:len(mean_rms)]

    axes.set_xticks(tick_locations)
    axes.set_xticklabels(time_label)
    plt.xticks(rotation=45)
    axes.set_title(f"SNR ({filepath.split('.')[0]})")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot SNR")
    parser.add_argument('filepath', help='Input filepath to npz file with SNR info')
    args = parser.parse_args()
    main(args.filepath)