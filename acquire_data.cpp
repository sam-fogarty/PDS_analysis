#include <iostream>
#include <vector>
#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <arpa/inet.h>
#include <unistd.h>
#include <iomanip> // for std::hex

class Daphne {
private:
    int sock;
    struct sockaddr_in target;

public:
    Daphne(std::string ipaddr, int port = 2001) {
        if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
            std::cerr << "Socket creation error" << std::endl;
            exit(EXIT_FAILURE);
        }

        memset(&target, 0, sizeof(target));
        target.sin_family = AF_INET;
        target.sin_port = htons(port);

        if (inet_pton(AF_INET, ipaddr.c_str(), &target.sin_addr) <= 0) {
            std::cerr << "Invalid address/ Address not supported" << std::endl;
            exit(EXIT_FAILURE);
        }
    }

    std::vector<unsigned long long> read_reg(unsigned long long addr, unsigned char size) {
        char cmd[10];
        cmd[0] = 0x00;
        cmd[1] = size;
        memcpy(cmd + 2, &addr, sizeof(addr));

        sendto(sock, cmd, 10, 0, (struct sockaddr *)&target, sizeof(target));

        char buffer[2 + 8 * size];
        recvfrom(sock, buffer, sizeof(buffer), 0, NULL, NULL);

        std::vector<unsigned long long> result;
        result.resize(size);
        memcpy(&result[0], buffer, sizeof(result[0]) * size);
        return result;
    }

    void write_reg(unsigned long long addr, std::vector<unsigned long long> data) {
        char cmd[10 + 8 * data.size()];
        cmd[0] = 0x01;
        cmd[1] = data.size();
        memcpy(cmd + 2, &addr, sizeof(addr));

        for (size_t i = 0; i < data.size(); ++i) {
            memcpy(cmd + 10 + 8 * i, &data[i], sizeof(data[i]));
        }

        sendto(sock, cmd, sizeof(cmd), 0, (struct sockaddr *)&target, sizeof(target));
    }

    void close_conn() {
        close(sock);
    }
};

int daphne_c_test() {
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

        // Calculate the address for the current chunk
        unsigned long long address = base_register + (AFE_hex_base * afe) + (Channel_hex_base * chan) + i * chunk_length;

        // Read from the device
        std::vector<unsigned long long> doutrec = daphne.read_reg(address, chunk_length);

        // Concatenate the doutrec vector to combined_result
        combined_result.insert(combined_result.end(), doutrec.begin(), doutrec.end());
    }

    // Print combined result
    std::cout << "Combined Result: ";
    for (const auto &value : combined_result) {
        std::cout << value << " ";
        //std::cout << "0x" << std::hex << std::uppercase << value << " ";
    }
    std::cout << std::endl;


    daphne.close_conn();

    return 0;
}

