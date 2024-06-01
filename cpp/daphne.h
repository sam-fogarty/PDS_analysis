#ifndef DAPHNE_H
#define DAPHNE_H

#include <iostream>
#include <vector>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

class Daphne {
public:
    Daphne(const std::string& ip);
    ~Daphne();
    void write_reg(unsigned long long addr, const std::vector<unsigned long long>& data);
    std::vector<unsigned long long> read_reg(unsigned long long addr, unsigned char size);
    void close_conn();

private:
    int sock;
    struct sockaddr_in target;
};

#endif // DAPHNE_H
