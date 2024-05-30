# set_bias.py Converts desired bias voltage to DAC values and sends it to appropriate AFE
#Uses the new SPI slave firmware. Python 3.

import DaphneInterface as ivtools
import argparse
import time
from tqdm import tqdm

def main(ep, tozero):

    chtr = {0:976, 1:962, 2:982, 3:987, 4:976, 5:985, 6:986, 7:983,
            8:652, 9:649, 10:642, 11:639, 12:639, 13:653, 14:639, 15:641,
            16:490, 17:505, 18:507, 19:505, 20:500, 21:496, 22:506, 23:503,
            24:18, 25:51, 26:14, 27:37, 28:46, 29:14, 30:33, 31:50,
            32:335, 33:342, 34:348, 35:348, 36:350, 37:348, 38:350, 39:333}

    device = ivtools.daphne(f"10.73.137.{ep}")

    for i in tqdm(range(0, 40)):
        if tozero is not None and tozero:
            trim = 0
        else:
            trim = chtr[i]
        CmdString = f"WR TRIM CH {i} V {trim}"
        #print(CmdString)
        #send command, read response
        response_data = device.command(CmdString)
        #print(response_data)
        time.sleep(0.05)
    
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DAPHNE command interpreter')
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint, e.g. 110')
    parser.add_argument('--tozero', required=False, default=None, action='store_true')
    args = parser.parse_args()
    main(args.ep, args.tozero)
