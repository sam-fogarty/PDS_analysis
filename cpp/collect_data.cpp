#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include "daphne.h"
#include <TFile.h>
#include <TTree.h>

int main() {
    std::string ipaddr = "10.73.137.110";
    Daphne daphne(ipaddr);

    // Output file and tree setup
    TFile *file = new TFile("waveforms.root", "RECREATE");
    TTree *tree = new TTree("waveforms", "Waveforms data");

    std::vector<unsigned long long> combined_result;
    tree->Branch("waveform", &combined_result);

    // Time duration for data collection
    auto start_time = std::chrono::steady_clock::now();
    auto end_time = start_time + std::chrono::minutes(1);
    std::chrono::milliseconds delay(0);

    unsigned long long chunk_length = 100;
    unsigned long long base_register = 0x40000000;
    unsigned long long AFE_hex_base = 0x100000;
    unsigned long long Channel_hex_base = 0x10000;
    unsigned long long length = 4000;
    unsigned long long chunks = length / chunk_length;

    unsigned long long iteration = 0;
    while (std::chrono::steady_clock::now() < end_time) {
        daphne.write_reg(0x2000, {1234});
	combined_result.clear();
        unsigned long long afe = 0;
        unsigned long long chan = 4;
        for (unsigned long long i = 0; i < chunks; ++i) {
            unsigned long long address = base_register + (AFE_hex_base * afe) + (Channel_hex_base * chan) + i * chunk_length;
            std::vector<unsigned long long> doutrec = daphne.read_reg(address, chunk_length);
            combined_result.insert(combined_result.end(), doutrec.begin(), doutrec.end());
        }

        tree->Fill();
        ++iteration;

        auto current_time = std::chrono::steady_clock::now();
        std::chrono::duration<double> elapsed = current_time - start_time;
        double rate = iteration / elapsed.count();
        double remaining_time = std::chrono::duration<double>(end_time - current_time).count();

        if (iteration % 10 == 0) { // Print every 10 iterations
            std::cout << "Rate: " << rate << " iterations/sec, Time remaining: " << remaining_time << " seconds" << std::endl;
        }

        std::this_thread::sleep_for(delay);
    }

    file->Write();
    file->Close();

    daphne.close_conn();

    return 0;
}
