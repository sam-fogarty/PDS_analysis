# dump.py -- dump DAPHNE spy buffers Python3

import DaphneInterface as ivtools
import argparse

def main(ep):
    device = ivtools.daphne(f"10.73.137.{ep}")

    print("DAPHNE firmware version %0X" % device.read_reg(0x9000,1)[2])

    device.write_reg(0x2000, [1234]) # software trigger, all spy buffers capture

    print()

    # dump data from all channels
    for afe in range(5):
        for ch in range(9):
            print("AFE%d[%d]: " % (afe,ch),end="")
            for x in device.read_reg(0x40000000+(afe*0x100000)+(ch*0x10000),20)[3:]:
                print("%04X " % x,end="")
            print()
        print()
       
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dump spy buffer data for all channels in DAPHNE")
    parser.add_argument("--ep", required=True, help='DAPHNE endpoint address, e.g. 110')
    args = parser.parse_args()
    main(args.ep)
