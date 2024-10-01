#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include "daphne.h"
//#include <TFile.h>
//#include <TTree.h>
#include <fstream>
#include "H5Cpp.h"
#include <getopt.h>
#include <filesystem>

const std::string DATASET_NAME = "data";

//enum OutputMode { root, CSV };å

// Function to parse command-line arguments
void parseArguments(int argc, char* argv[], int &run, std::string &trigger, int &endpoint, int &nwvfms, int &afe, int &ch) {
    std::string errorMessage = " --run <run number, req.> --ep <endpoint, opt.> --trig <trigger type, opt.>\n\n Argument Overview:\n--run: run number to save in filename (int, required)\n--trig: trigger type, soft or ext (str, required)\n--ep: DAPHNE endpoint address (int, optional)\n--nwvfms: Total number of waveforms to acquire (int, optional)\n--afe: AFE to record data from\n--ch: channel to record data from";
    if (argc < 2) {
         std::cerr << "This script is used to acquire a series of waveforms from one channel in DAPHNEv2.\n\nUsage: " << argv[0] << errorMessage << std::endl;
      	 exit(1);
    }
    // Struct to define long options
    static struct option long_options[] = {
        {"run", required_argument, 0, 'r'},
        {"trig", required_argument, 0, 't'},
        {"ep", required_argument, 0, 'e'},
        {"nwvfms", required_argument, 0, 'n'},
        {"afe", required_argument, 0, 'a'},
        {"ch", required_argument, 0, 'c'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}  // Terminator, dont change
    };

    int option_index = 0;
    int opt;
    int req_arg_count = 2;
    int arg_count = 0;
    // Parse command line arguments using getopt_long
    while ((opt = getopt_long(argc, argv, "r:t:e:n:a:c:h", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'r':
                run = std::stoi(optarg);
                arg_count += 1;
                break;
            case 't':
                trigger = optarg;
                arg_count += 1;
                break;
            case 'e':
                endpoint = std::stoi(optarg);
                break;
            case 'n':
                nwvfms = std::stoi(optarg);
                break;
            case 'a':
                afe = std::stoi(optarg);
                break;
            case 'c':
                ch = std::stoi(optarg);
                break;
            case 'h':
                std::cout << "Usage: " << argv[0] << errorMessage;
                exit(0);
                break;
            default:
                std::cerr << "Usage: " << argv[0] << errorMessage;
                exit(1);
        }
    }
    std::cout << arg_count << std::endl;
    if (arg_count < req_arg_count){
        std::cerr << "Usage: " << argv[0] << errorMessage;
        exit(1);
    }
}

int main(int argc, char* argv[]) {
    //default values
    int run = 0;
    int endpoint = 110; 
    int nwvfms = 10000; 
    int afe = 4;
    int ch = 4;
    std::string trigger;

    // Parse command-line arguments
    parseArguments(argc, argv, run, trigger, endpoint, nwvfms, afe, ch);

    std::cout << "Doing run " << run << " accessing DAPHNE endpoint " << endpoint << " with " << trigger << " trigger" << std::endl;
    std::cout << "Acquiring " << nwvfms << " waveforms from AFE " << afe << " and channel " << ch << std::endl; 
    // Output the parsed arguments
    //std::cout << "Run: " << run << "\n";
    //std::cout << "Endpoint: " << endpoint << "\n";
    //std::cout << "Trigger: " << trigger << "\n";
    //std::cout << "nwvfms: " << nwvfms << "\n";
    //std::cout << "afe: " << afe << "\n";
    //std::cout << "ch: " << ch << "\n";
    
    if (trigger != "ext" && trigger != "soft") {
        std::cerr << "Error: The --trig option must be either 'ext' or 'soft'.\n";
        exit(1);  // Exit with a non-zero status to indicate an error
    }
    bool use_software_trigger;
    if (trigger == "soft"){
        use_software_trigger = true;
    }
    else{
        use_software_trigger = false;
    }
    std::cout << "use_software_trigger: " << std::to_string(use_software_trigger) << std::endl;
    std::string filename = "data/run"+std::to_string(run)+".hdf5";
    // setup connection with daphne
    std::string ipaddr = "10.73.137."+std::to_string(endpoint);
    
    std::cout << "filename = " << filename << std::endl;
    std::cout << "ip address = " << ipaddr << std::endl;

    if (std::filesystem::exists(filename)) {
        std::cerr << "File " << filename << " already exists. Exiting...\n";
        return 1;  // Exit with a non-zero status to indicate failure
    }
    
    Daphne daphne(ipaddr);

    std::vector<int> combined_result;
    hsize_t offset[2] = {0, 0};

    std::ofstream hdf5File;
    H5::H5File file(filename, H5F_ACC_TRUNC);
    hsize_t initial_dims[2] = {0, 0};
    hsize_t max_dims[2] = {H5S_UNLIMITED, H5S_UNLIMITED};
    H5::DataSpace dataspace(2, initial_dims, max_dims);
    H5::DataType uint32_type = H5::PredType::NATIVE_UINT;

    H5::DSetCreatPropList propList;
    hsize_t array_length = 3900; //FIXME
    hsize_t chunk_dims[2] = {1, array_length};  // Define the chunk dimensions (1x3900 is the size of one waveform)
    propList.setChunk(2, chunk_dims);  // Set the chunk size for the dataset
    //propList.setLayout(H5D_CHUNKED);
    propList.setDeflate(2);

    H5::DataSet dataset = file.createDataSet(DATASET_NAME, uint32_type, dataspace, propList);

    // Set time limit for data collection
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::minutes(10);
    std::chrono::milliseconds delay(0);
    
    // setup some constants and parameters. Ideally some of these parameters should go into commandline arguments.
    int chunk_length = 150; // raising this generally increases rate, but only to a point it seems (about 150 on current machine and setup)
    unsigned int base_register = 0x40000000;
    unsigned int AFE_hex_base = 0x100000;
    unsigned int Channel_hex_base = 0x10000;
    int length = 2000; // 1000 is fine for LED tests. 4000 is whole buffer (rate will be lower)
    //bool use_software_trigger = true; // true to use software trigger, make sure external trigger pulse is off
    if (use_software_trigger) {
	    length = 4000;
    }
    
    hsize_t Length = static_cast<hsize_t>(length);
    const hsize_t hsizeArray[2] = { Length, static_cast<hsize_t>(nwvfms) };

    unsigned int chunks = length / chunk_length;
    bool use_iterations_limit = true; // limit the total number of waveforms saved, overrides time limit
    int iterations_limit = nwvfms;
    if (use_iterations_limit){
	    end_time = end_time + std::chrono::minutes(10000); // make sure script doesn't end prematurely if time limit is reached
    }
    int iteration = 0; // current iteration
    int base_address = base_register + (AFE_hex_base * afe) + (Channel_hex_base * ch);
    unsigned int last_timestamp = 0;
    unsigned int new_timestamp;
    int iterations_last = 0;
    auto last_time = std::chrono::steady_clock::now();
    std::cout << "starting taking data" << std::endl;
    while (std::chrono::steady_clock::now() < end_time) { // loop until time limit reached
        if (use_software_trigger) {
	     daphne.write_reg(0x2000, {1234});
	}
	unsigned int current_timestamp = daphne.read_reg(0x40500000, 1)[0];
	// make sure we are not recapturing the same waveform again
	if (last_timestamp != current_timestamp) {
	    combined_result.clear();
	    // read registers by the chunk, then combine
            for (unsigned int i = 0; i < chunks; ++i) {
                unsigned int address = base_address + i * chunk_length;
		std::vector<int> doutrec = daphne.read_reg(address, chunk_length);
                combined_result.insert(combined_result.end(), doutrec.begin(), doutrec.end());
            }
            unsigned int new_timestamp = daphne.read_reg(0x40500000, 1)[0];
            // only save waveform if no additional triggers happened while reading
	    if (new_timestamp == current_timestamp) {
		    hsize_t current_dims[2] = {offset[0]+1, offset[1]+array_length};
		    dataset.extend(current_dims);

		    H5::DataSpace new_dataspace = dataset.getSpace();
		    hsize_t batch_size[2] = {1, array_length};
		    new_dataspace.selectHyperslab(H5S_SELECT_SET, batch_size, offset);

		    hsize_t mem_dims[2] = {1, array_length};
		    H5::DataSpace memspace(2, mem_dims);

		    dataset.write(combined_result.data(), uint32_type, memspace, new_dataspace);
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
