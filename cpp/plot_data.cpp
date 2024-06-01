#include <iostream>
#include <vector>
#include "daphne.h"
#include <TApplication.h>
#include <TCanvas.h>
#include <TGraph.h>

int main(int argc, char** argv) {
    TApplication theApp("App", &argc, argv);

    std::string ipaddr = "10.73.137.110";
    Daphne daphne(ipaddr);

    daphne.write_reg(0x2000, {1234});
    std::vector<unsigned long long> result = daphne.read_reg(0x40500000, 1);
    for (auto val : result) {
        std::cout << "timestamp = " << val << std::endl;
    }

    const unsigned long long chunk_length = 100;
    const unsigned long long base_register = 0x40000000;
    const unsigned long long AFE_hex_base = 0x100000;
    const unsigned long long Channel_hex_base = 0x10000;
    const unsigned long long length = 1000;
    const unsigned long long chunks = length / chunk_length;

    std::vector<unsigned long long> combined_result; // Vector to store combined results

    unsigned long long afe = 0; 
    unsigned long long chan = 0;
    for (unsigned long long i = 0; i < chunks; ++i) {
        unsigned long long address = base_register + (AFE_hex_base * afe) + (Channel_hex_base * chan) + i * chunk_length;
        std::vector<unsigned long long> doutrec = daphne.read_reg(address, chunk_length);
        combined_result.insert(combined_result.end(), doutrec.begin(), doutrec.end());
    }

    // Prepare data for plotting
    int n = combined_result.size();
    double* x = new double[n];
    double* y = new double[n];

    for (int i = 0; i < n; ++i) {
        x[i] = i; // X-axis can be the index
        y[i] = combined_result[i]; // Y-axis is the data value
    }

    // Create a TGraph and plot it
    TCanvas* c1 = new TCanvas("c1", "Data Plot", 800, 600);
    TGraph* graph = new TGraph(n, x, y);
    graph->SetTitle("Combined Result Plot;Index;Value");
    graph->Draw("AL");

    // Save the plot as a PNG file
    c1->SaveAs("combined_result_plot.png");

    // Run the application to display the canvas
    theApp.Run();

    delete[] x;
    delete[] y;

    daphne.close_conn();

    return 0;
}

