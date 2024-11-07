# reset.py -- reset timing endpoint logic then report on endpoint status bits Python3
# Originally from daphne2_fpga, updated to use newer DAPHNE interface that accounts for ethernet timeout
import time
import DaphneInterface as ivtools
import argparse

def main(ep):

    device = ivtools.daphne(f"10.73.137.{ep}")
    print(f"Configuring clocks for DAPHNE endpoint {ep}")
    print("DAPHNE firmware version %0X" % device.read_reg(0x9000,1)[2])

    # master clock input can be endpoint (=1) or local clocks (=0), choose that here:

    USE_ENDPOINT = 0
    if USE_ENDPOINT == 0:
        print('Configuring to use local clocks')
    else:
        print('Configuring to use master clock via timing interface')
    # configure these misc timing endpoint parameters

    EDGE_SELECT = 0
    TIMING_GROUP = 0
    ENDPOINT_ADDRESS = 0

    # now write to the master clock and endpoint control register:
    
    #temp = (ENDPOINT_ADDRESS&0xFF)<<8 + (TIMING_GROUP&0x3)<<2 + (EDGE_SELECT&0x1)<<1 + (USE_ENDPOINT & 0x1)
    temp = (ENDPOINT_ADDRESS&0xFF)<<8 + (TIMING_GROUP&0x3)<<2 + (EDGE_SELECT&0x1)<<1 + (USE_ENDPOINT & 0x0)
    device.write_reg(0x4001, [temp]) 

    # now reset the timing endpoint logic

    device.write_reg(0x4003, [1234])

    # wait a moment for timing endpoint clocks to stabilize...

    time.sleep(0.5)
    
    # reset the master clock MMCM1

    device.write_reg(0x4002, [1234])
    
    # wait a moment for the master clocks to stabilize...

    time.sleep(0.5)
    
    # reset the front end and force recalibration

    device.write_reg(0x2001, [1234]) 
    
    # wait a moment for the front end logic to recalibrate...
    
    time.sleep(0.5)
    
    # dump out front end status registers...
    
    # 5 LSb's = DONE bits should be HIGH if the front end has completed auto alignment
    
    print("AFE automatic alignment done, should read 0x1F: %0X" % device.read_reg(0x2002,1)[2])
    
    # bit error count registers for each AFE 
    # if an error is observed on the "FCLK" pattern it increments this counter up to 0xFF
    
    print("AFE0 Error Count = %0X" % device.read_reg(0x2010,1)[2])
    print("AFE1 Error Count = %0X" % device.read_reg(0x2011,1)[2])
    print("AFE2 Error Count = %0X" % device.read_reg(0x2012,1)[2])
    print("AFE3 Error Count = %0X" % device.read_reg(0x2013,1)[2])
    print("AFE4 Error Count = %0X" % device.read_reg(0x2014,1)[2])
    
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for configuring the DAPHNE v2 clocks")
    parser.add_argument('--ep', required=True, help='DAPHNE endpoint, e.g. 110')
    args = parser.parse_args()
    main(args.ep)
