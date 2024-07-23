#include "daphne.h"

Daphne::Daphne(const std::string& ip) {
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        throw std::runtime_error("Failed to create socket");
    }
    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    target.sin_port = htons(1024);
    inet_pton(AF_INET, ip.c_str(), &target.sin_addr);
}

Daphne::~Daphne() {
    close(sock);
}

void Daphne::write_reg(unsigned long long addr, const std::vector<unsigned long long>& data) {
    char cmd[10 + 8 * data.size()];
    cmd[0] = 0x01;
    cmd[1] = data.size();
    memcpy(cmd + 2, &addr, sizeof(addr));
    for (size_t i = 0; i < data.size(); ++i) {
        memcpy(cmd + 10 + 8 * i, &data[i], sizeof(data[i]));
    }
    sendto(sock, cmd, sizeof(cmd), 0, (struct sockaddr *)&target, sizeof(target));
}

std::vector<int> Daphne::read_reg(unsigned long long addr, unsigned char size) {
    char cmd[10];
    cmd[0] = 0x00; // Command type for read
    cmd[1] = size; // Size of the data to be read
    memcpy(cmd + 2, &addr, sizeof(addr)); // Copy the address into the command buffer

    // Send the command to the target device
    sendto(sock, cmd, 10, 0, (struct sockaddr *)&target, sizeof(target));

    // Buffer to receive the response
    char buffer[2 + 8 * size];
    recvfrom(sock, buffer, sizeof(buffer), 0, NULL, NULL);

    // Unpack the response
    std::vector<int> result(size);
    for (unsigned char i = 0; i < size; ++i) {
        result[i] = *((int*)(buffer + 2 + 8 * i));
    }

    return result;
}

void Daphne::close_conn() {
    close(sock);
}
