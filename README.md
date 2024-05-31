### Scripts for data acquisition, plotting, and analysis of DUNE PDS setups using DAPHNE spy buffers
This code has been developed/collected for use at CSU for the DUNE PDS module testing, which utilizes DAPHNE v2 for reading out signals from SiPMs. The data acquisition is done with the spy buffers.
The spy buffers can be triggered with an external trigger pulse directly to DAPHNE or by a command over the serial interface. Spy buffers can capture 4000 samples or about 65 us of data from any channel. The data must then be read from the spy buffer registers over the serial interface. There are detailed instructions available for configuring and operating DAPHNE in this setup, but the following is a short description. Note that to connect to the DAPHNE to a PC one needs to change the ethernet IP address to 10.73.137.1. For the examples, below we use DAPHNE endpoint 110. It is recommended to use a linux-based terminal (mac should probably work too, but these scripts were only tested in Ubuntu). There are linux terminals available on the Windows store.

All scripts that can read or write to DAPHNE registers uses the DaphneInterface.py library. This is based on a library from https://github.com/marroyav/daphne_interface, but modified mainly to gracefully handle ethernet timeouts. 

For configuring registers for data taking, one can use `python3 init.py --ep 110`. This script configures the AFEs and individual channels, and sets VGAIN and offset. This step is an essential first step for datataking. One can modify the script to set registers differently as preferred.

Following running the init stage (or before) one needs to configure the DAPHNE clocks. Run `python3 config_clocks.py --ep 110` to configure DAPHNE to use the internal clocks (by default). Before this waveforms will look strange. To check that the clocks are aligned, you can run `python3 dump_data.py --ep 110` which will print some data from each channel. Look at channel 8 in each AFE and make sure they all read 3F80.

To read and plot waveforms from one trigger, you can use `read_waveforms.py`. There are commandline options for specifying the channel and AFE to plot. 

To acquire data and save to a file, you can use `acquire_data.py`. By default this will save waveforms to individual csv files for each channel. Note that there will be a rate limit due largely to the code speed (because it is written in python), so the rate starting from 0 will increase with increasing rate, peak, then start to decrease. The reason for this is the code will throw out waveforms that were overwritten while reading them. If a new trigger happens while reading a waveform (when using external trigger mode exclusively), the spy buffer will be overwritten even though the code is in the middle of reading it. So you would see drastic jumps in the waveforms. The script will always capture the desired number of waveforms, it will just take longer because of this effect. The script will also set a VGAIN and adjust the baseline to the desired level. So by specifying multiple VGAIN values in the commandline (comma-separated, no spaces) the script will acquire data from each VGAIN setting in the channels requested. Can also specify different target pedestal.

You can use `send_commands.py` to read and write to registers in DAPHNE in a commandline interface. This is based on a script found in the `daphne2_fpga` repository, but adapted to use the new DaphneInterface. Type `help` in the interface to get useful commands. Or `H` after a command like `WR` or `RD` for more tips.

`set_all_trims.py` sets trim values for various channels automatically. The script is by default setup to set trims for the CSU DAPHNE.

`set_bias.py` is a useful helper script for setting bias values for any channel. The input is a voltage in volts (and AFE and DAPHNE endpoint). The voltage is converted to a DAC value before writing to the corresponding register. The script uses a linear regression of DAC vs Measured Voltage with multimeter for CSU DAPHNE.

`daphne_event_display.py` is a pyROOT-based live event display. It will read waveforms continuously and update a ROOT canvas. Supports rolling average. Note that you might need to use slower trigger rate if using external trigger mode for script to work. Ideally this script would be written in C or C++ (same for `acquire_data.py`) which should eleviate these rate issues. 
 

