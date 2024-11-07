import numpy as np
import matplotlib.pyplot as plt

filename='corr_threshold_scan.txt'
data = np.loadtxt(filename, skiprows=3, delimiter=',')
i=0
with open(filename, 'r') as file:
        # Loop through each line in the file
        for line in file:
            if i == 1:
                true_dcr = float(line.split(',')[1])
            elif i > 1:
                break
            i+=1

corr_threshold = data[:,0]
E = data[:,1]
P = data[:,2]
Real_Peaks = data[:,3]
Fake_Peaks = data[:,4]
DCR = data[:,5]

fig, axes = plt.subplots(figsize=(14,8), nrows=3, ncols=1)
axes[0].plot(corr_threshold, E, 'go', label='Efficiency')
axes[0].plot(corr_threshold, P, 'r*', label='Purity')
axes[0].legend()

axes[1].plot(corr_threshold, Real_Peaks, 'go', label='Number of Real Peaks Found')
axes[1].plot(corr_threshold, Fake_Peaks, 'r*', label='Number of Fake Peaks Found')
axes[1].legend()

axes[2].hlines(true_dcr, xmin=min(corr_threshold), xmax=max(corr_threshold), label=f'True DCR, {true_dcr:.3f}')
axes[2].plot(corr_threshold, DCR, 'ro', label='DCR')
axes[2].legend()
axes[0].set_title('10/8/2024 run5549')
axes[2].set_xlabel('Correlation Threshold')
plt.show()
