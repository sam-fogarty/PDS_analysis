# set_bias.py Converts desired bias voltage to DAC values and sends it to appropriate AFE
#Uses the new SPI slave firmware. Python 3.

import DaphneInterface as ivtools
import argparse

def main(ep,afe,v):

    afe = int(afe)
    v = float(v)

    device = ivtools.daphne(f"10.73.137.{ep}")

    def DAC_for_V(afe, v):
        if afe==0:
            return abs(round((v-0.053)/0.0394))
        elif afe==1:
            return abs(round((v-0.0447)/0.0391))
        elif afe==2:
            return abs(round((v-0.00945)/0.0392))
        elif afe==3:
            return abs(round((v+0.371)/0.0391))
        elif afe==4:
            return abs(round((v-0.00328)/0.0391))
        else:
            raise ValueError("We only have AFE's 0-4!")

    if v==0:
        dac = 0
    else:
        dac = DAC_for_V(afe, v)

    CmdString = f"WR AFE {afe} BIASSET V {dac}"
    print(CmdString)

    #send command, read response
    response_data = device.command(CmdString)
    print(response_data)
    
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DAPHNE command interpreter')
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint, e.g. 110')
    parser.add_argument('--afe', required=True, help='Which AFE are we setting bias for? Number 0-4')
    parser.add_argument('--v', required=True, help='What bias voltage do you want? Positive number')
    args = parser.parse_args()
    main(args.ep,args.afe,args.v)
