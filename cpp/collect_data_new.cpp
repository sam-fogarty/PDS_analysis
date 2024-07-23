#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include "daphne.h"
//#include <TFile.h>
//#include <TTree.h>
#include <fstream>
#include "H5Cpp.h"

const std::string DATASET_NAME = "data";

//enum OutputMode { root, CSV };

void parseArguments(int argc, char* argv[], std::string &filename) {
     if (argc != 2) {
         std::cerr << "Usage: " << argv[0] << " <filename>" << std::endl;
	 exit(1);
     }
     filename = argv[1];
}

int main(int argc, char* argv[]) {

    std::string filename;
    parseArguments(argc, argv, filename);

    // setup connection with daphne
    std::string ipaddr = "10.73.137.110";
    Daphne daphne(ipaddr);

    std::vector<unsigned long long> combined_result;
    hsize_t offset[2] = {0, 0};

    std::ofstream hdf5File;
    filename += ".hdf5"; 
    H5::H5File file(filename, H5F_ACC_TRUNC);
    hsize_t initial_dims[2] = {0, 0};
    hsize_t max_dims[2] = {H5S_UNLIMITED, H5S_UNLIMITED};
    H5::DataSpace dataspace(2, initial_dims, max_dims);
    H5::DataType uint64_type = H5::PredType::NATIVE_ULLONG;

    H5::DSetCreatPropList propList;
    hsize_t chunk_dims[2] = {1, 3900};  // Define the chunk dimensions (1x1 for simplicity)
    propList.setChunk(2, chunk_dims);  // Set the chunk size for the dataset
    //propList.setLayout(H5D_CHUNKED);
    propList.setDeflate(6);

    H5::DataSet dataset = file.createDataSet(DATASET_NAME, uint64_type, dataspace, propList);

    // Set time limit for data collection
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::minutes(10);
    std::chrono::milliseconds delay(0);
    
    // setup some constants and parameters. Ideally some of these parameters should go into commandline arguments.
    unsigned long long chunk_length = 150; // raising this generally increases rate, but only to a point it seems (about 150 on current machine and setup)
    unsigned long long base_register = 0x40000000;
    unsigned long long AFE_hex_base = 0x100000;
    unsigned long long Channel_hex_base = 0x10000;
    unsigned long long length = 4000; // 1000 is fine for LED tests. 4000 is whole buffer (rate will be lower)
    bool use_software_trigger = true; // true to use software trigger, make sure external trigger pulse is off
    if (use_software_trigger) {
	    length = 4000;
    }

    hsize_t Length = static_cast<hsize_t>(length);
    const hsize_t hsizeArray[2] = { Length, 10000 };

    //H5::DSetCreatPropList plist;
    //hsize_t chunk_dims[1] = {1}; // Chunk size: one row at a time
    //plist.setChunk(1, chunk_dims);

    //H5::DataSet dataset = file.createDataSet(DATASET_NAME, H5::PredType::NATIVE_ULLONG, memspace);
    //catch (H5::Exception& e){
	    //std::cerr << "It happened here" << std::endl;}


    unsigned long long chunks = length / chunk_length;
    bool use_iterations_limit = true; // limit the total number of waveforms saved, overrides time limit
    unsigned long long iterations_limit = 100;
    if (use_iterations_limit){
	    end_time = end_time + std::chrono::minutes(10000); // make sure script doesn't end prematurely if time limit is reached
    }
    unsigned long long iteration = 0; // current iteration
    unsigned long long afe = 0;
    unsigned long long chan = 4; // put in argument!
    unsigned long long base_address = base_register + (AFE_hex_base * afe) + (Channel_hex_base * chan);
    unsigned long long last_timestamp = 0;
    unsigned long long new_timestamp;
    unsigned long long iterations_last = 0;
    auto last_time = std::chrono::steady_clock::now();
    std::cout << "starting taking data" << std::endl;
    while (std::chrono::steady_clock::now() < end_time) { // loop until time limit reached
        if (use_software_trigger) {
	     daphne.write_reg(0x2000, {1234});
	}
	unsigned long long current_timestamp = daphne.read_reg(0x40500000, 1)[0];
	// make sure we are not recapturing the same waveform again
	if (last_timestamp != current_timestamp) {
	    combined_result.clear();
	    // read registers by the chunk, then combine
            for (unsigned long long i = 0; i < chunks; ++i) {
                unsigned long long address = base_address + i * chunk_length;
                std::vector<unsigned long long> doutrec = daphne.read_reg(address, chunk_length);
                combined_result.insert(combined_result.end(), doutrec.begin(), doutrec.end());
            }
            unsigned long long new_timestamp = daphne.read_reg(0x40500000, 1)[0];
            // only save waveform if no additional triggers happened while reading
	    if (new_timestamp == current_timestamp) {
		    hsize_t current_dims[2] = {offset[0]+1, offset[1]+3900};
		    dataset.extend(current_dims);

		    H5::DataSpace new_dataspace = dataset.getSpace();
		    hsize_t batch_size[2] = {1, 3900};
		    new_dataspace.selectHyperslab(H5S_SELECT_SET, batch_size, offset);

		    hsize_t mem_dims[2] = {1, 3900};
		    H5::DataSpace memspace(2, mem_dims);

		    dataset.write(combined_result.data(), uint64_type, memspace, new_dataspace);
		    offset[0] += 1;

		   ++iteration;

	    last_timestamp = new_timestamp;
            if (iteration % 50 == 0) { // print rate and time/iterations remaining
            	auto current_time = std::chrono::steady_clock::now();
		std::chrono::duration<double> elapsed = current_time - last_time;
                
		last_time = current_time;
		double rate = (iteration - iterations_last) / elapsed.count();
		//std::chrono::duration<double> elapsed = current_time - start_time;
            	//double rate = iteration / elapsed.count();
            	double remaining_time = std::chrono::duration<double>(end_time - current_time).count();
                if (rate != 0) { // sometimes at high rate you'll get a 0 rate print statement, so we just filter them out
		    if (!use_iterations_limit){
            	        std::cout << "Rate: " << rate << " iterations/sec, Time remaining: " << remaining_time << " seconds" << std::endl;
		    }
		    else {
                        std::cout << "Rate: " << rate << " iterations/sec, Waveforms remaining: " << iterations_limit - iteration << std::endl;
		    }
		    iterations_last = iteration;
		
	            }
	        }

	}
	else {
            last_timestamp = current_timestamp;

	}
	if (use_iterations_limit && iteration >= iterations_limit) {
                break;
	}
        }
    }
    dataset.close();
    hdf5File.close(); 

    daphne.close_conn();

    return 0;
}
