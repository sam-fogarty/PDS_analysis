import numpy as np
import matplotlib.pyplot as plt

file = 'DCR_measurements.npz'
#files = ['DCR_info_6222024_1.npz', 'DCR_info_6222024_2.npz', 'DCR_info_6222024_3.npz', 'DCR_info_6222024_4.npz']
#files = ['DCR_info_6232024_1.npz', 'DCR_info_6232024_2.npz', 'DCR_info_6232024_3.npz', 'DCR_info_6232024_4.npz', 'DCR_info_6232024_5.npz', 'DCR_info_6232024_6.npz']

fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12,6), sharex=True)
data = np.load(file, allow_pickle=True)
DCR = data['DCR_all']/(48*36)
DCR_err = data['DCR_err_all']/(48*36)
time_hour = data['time_hour'].astype('float')
time_minute = data['time_minute'].astype('float')
runnumbers = data['runnumbers_all'].astype('int')
mean_rms = data['mean_rms'].astype('float')
std_rms = data['std_rms'].astype('float')
time = []
time_float = []

for i in range(len(time_hour)):
    time.append(f'{time_hour[i]}:{time_minute[i]}')
    time_float.append(float(time_hour[i]) + float(time_minute[i])/60)

axes[0].errorbar(np.array(time_float)+0.008333, DCR, xerr=np.ones(len(time_float))*0.008333, yerr=DCR_err, fmt='bo', markersize=2)
axes[0].set_ylim(0, np.max(DCR) + 0.3)
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
print(tick_locations)
print(time_label)
#time_label = ['14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30', '18:00', '18:30', '19:00']
#axes[0].set_xticks(tick_locations)
#axes[0].set_xticklabels(time_label)
#plt.xticks(rotation=45)
axes[0].set_ylabel('DCR [Hz/mm^2]')
axes[1].set_xlabel('Local Time of Datataking')

#mean_rms = mean_rms[:len(mean_rms)]

std_rms = np.zeros(len(std_rms))
axes[1].errorbar(np.array(time_float)+0.008333, mean_rms, xerr=np.ones(len(time_float))*0.008333, yerr=std_rms, fmt='ro', markersize=2)
axes[1].set_ylim(min(mean_rms)*0.95, np.max(mean_rms)*1.05)
axes[1].set_ylabel('mean ADC RMS')
axes[1].set_xticks(tick_locations)
axes[1].set_xticklabels(time_label)
plt.xticks(rotation=45)
axes[0].set_title('DCR and Waveform RMS (8/8/2024, ERC)')
plt.show()
