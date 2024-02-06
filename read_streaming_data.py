"""
Script to read and save DAPHNE streaming data into an easy to analyze h5 format
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import argparse
import h5py
#from tqdm import tqdm

import daqdataformats
from hdf5libs import HDF5RawDataFile
from rawdatautils.unpack.daphne import np_array_adc_stream, np_array_channels_stream

# TODO: Ask Manuel why these channels.
CHANNEL_LIST = [0, 1, 6, 7, 10, 11, 16, 17, 20, 21, 26, 27, 30, 31, 36, 37]

def save_data(channel, adc_data, output_filepath):
    ## Save adc data to corresponding channel dataset
    with h5py.File(output_filepath, 'a') as output_file:
        output_file[str(channel)].resize((output_file[str(channel)].shape[0] + adc_data.shape[0]), axis=0)
        output_file[str(channel)][-adc_data.shape[0]:] = adc_data

def main(input_filepath, output_filepath):
    ## Data Processing
    h5_file = HDF5RawDataFile(input_filepath)

    # Get all DAPHNEStream paths -> All fragments will be DAPHNEStreams
    frag_paths = h5_file.get_all_fragment_dataset_paths()
    daphne_paths = []
    for frag_path in frag_paths:
        if "DAPHNEStream" in frag_path:
            daphne_paths.append(frag_path)
    
    # setup output file with empty datasets for each channel
    with h5py.File(output_filepath, 'a') as output_file:
        for channel in CHANNEL_LIST:
            output_file.create_dataset(str(channel), data=np.zeros((0,)), maxshape=(None,))
    for frag_idx, path in enumerate(daphne_paths):
        frag = h5_file.get_frag(path)
        channels = np_array_channels_stream(frag) # Awkward shape: (N, 4), but each row is the same.
        channels = channels[0] # Since all rows are the same, just use the first.

        # Get data from channels in channel list
        for idx, channel in enumerate(channels):
            if channel in CHANNEL_LIST:
                adcs = np_array_adc_stream(frag) # Good shape: (num_ticks, 4)
                adcs = adcs[:, idx] # idx maps channel to waveform
                save_data(channel, adcs, output_filepath)
        print(f'{frag_idx}/{len(daphne_paths)} Fragments Saved')

if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Script to read DAPHNE streaming data and save to h5 file")

    # Define the arguments
    parser.add_argument('input_filepath', help="Input hdf5 filepath")
    parser.add_argument('output_filepath', help="Output h5 filepath")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.input_filepath, args.output_filepath)