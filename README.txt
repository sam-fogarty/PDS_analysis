DUNE PDS analysis scripts and notebooks.
Scripts with descriptions:
- init.py ; script for setting up daphne v2 with initial register values, VGAIN, etc
- offset_tuning.py ; tune pedestals for channels to be close to some target pedestal
- acquirewave.py ; script for acquiring and saving data from daphne v2 SPI buffers on selected channels
- read_waveforms.py ; read and plot waveforms from selected channels and plot them
- turn_on_offset_integrators.py ; turn on the offset integrators for daphne v2's, should tune the pedestals to as close to 8196 as possible before doing this.

Note: These scripts have to be run within the OEI/python directory in this git repo: https://github.com/DUNE/daphne2_fpga 
Notebooks:
- PDS_waveform analysis.ipynb ; read data from file and make spe persistence plots, charge integral histograms, SNR calculation
- DAPHNE_randomTrigger_analysis.ipynb ; acquire random trigger data for calculating FFTs and RMS values
