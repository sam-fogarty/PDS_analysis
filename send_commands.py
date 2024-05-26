# uccmd.py -- send a command to the microcontroller and read the response
# uses the new SPI slave firmware. Python 3.

import DaphneInterface as ivtools
import argparse

def main(ep):
    device = ivtools.daphne(f"10.73.137.{ep}")
    
    print("DAPHNE Command Interpreter. Type 'help' to get command options. Type 'quit' to exit.")
    
    # prompt user for command
    while True:
        CmdString = input('daphne% ')
        if (CmdString=="quit" or CmdString=="quit()" or CmdString=='.q'):
            break
        # send command, read response
        response_data = device.command(CmdString)
        print(response_data)
    
    device.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DAPHNE command interpreter')
    parser.add_argument('--ep', required=True, help='DAPHNE IP endpoint, e.g. 110')
    args = parser.parse_args()
    main(args.ep)
