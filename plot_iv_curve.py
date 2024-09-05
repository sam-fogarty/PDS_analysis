import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline
import pandas as pd
from scipy.signal import butter, filtfilt

#filepath='iv_current_warm_50p5_to_53V_finer.npz'
filepath='iv_current_cold_working_952024.npz'
data = np.load(filepath)
current = -1*data['current']
v = data['v']

xvalues = np.arange(40, 47, 0.05)
window_size=10
df = pd.DataFrame({'current': current})
current = df['current'].rolling(window=window_size).mean()
current = np.array(current)[window_size-1:]
v = v[window_size-1:]

logv = np.log(current)
cs = CubicSpline(v, logv)
deriv_logv = cs.derivative()
cs2 = CubicSpline(xvalues, deriv_logv(xvalues))
deriv2_logv = cs2.derivative()

#deriv_logv = np.diff(logv)/(v[1]-v[0])
#deriv2_logv = np.diff(deriv_logv)/(v[1]-v[0])

plt.plot(v, logv, 'b--', label='ln(I)')
plt.plot(xvalues, deriv_logv(xvalues), 'r-', label="f'ln(I)")
plt.plot(xvalues, deriv2_logv(xvalues), 'g-.', label="f''ln(I)")
plt.legend()
plt.xlim(40, 47)
plt.xlabel('Bias [V]')
plt.ylabel('current')
plt.title('IV curve for supercell in LN2 at CSU (HPK)')
plt.show()
