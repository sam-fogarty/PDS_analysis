// script for controlling SRS pulser from PC through ethernet
// To compile: gcc -o dg_ctrl dg_ctrl.c
// To run: ./dg_ctrl IP_ADDRESS [OPTION]
// OPTION is an integer which will decide how to set the pulser configuration. 
//     Options are: 0: default, turn on external trigger on CD and EF
//                  1: Turn off external trigger on CD and EF (just sets delays to 0)
//                  2: Turn on PPS pulse on AB
// check ip address with steps below. If using with DAPHNE, set the ip to 10.73.137.1XY 
// for example XY = 11. 
// To setup: Press Shift key then NET key to access network settings. Enable: TCPIP, DHCP, STATIC IP, and BARE. Reset network.
//           Press Shift key then Status key: Press up arrow key, Status again, then a few more times until you get to the IP.
//           Use this IP for controlling/pinging the pulser. Don't forget to connect the pulser to the internet with the ethernet cable.

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* prototypes */
int dg_connect(unsigned long ip);
int dg_close(void);
int dg_write(char *str);
int dg_read(char *buffer, unsigned num);

int sDG645; /* DG645 tcpip socket */
unsigned dg_timeout = 3000; /* Read timeout in milliseconds */

int main(int argc, char * argv[])
{
    char buffer[1024];
    int optionalArg = 0;
    
    /* Make sure ip address is supplied on the command line */
    if (argc < 2) {
        printf("Usage: dg_ctrl IP_ADDRESS [OPTION]\n");
        exit(1);
    }
    
    if (argc >= 3) {
        optionalArg = atoi(argv[2]);
    }
    

    /* Connect to the dg645 */
    if (dg_connect(inet_addr(argv[1]))) {
        printf("Connection Succeeded\n");
        
        if (optionalArg == 0) {
	    printf("Using option 0: Turn off output on EF\n");
	} else if (optionalArg == 1) {
	    printf("Using option 1: Turn on output on EF for LED calibration\n");
	} else if (optionalArg == 2) {
            printf("Using option 2: Turning on PPS pulsing on AB output.\n");
        } else {
            printf("Unsupported option. Exiting...\n");
	    exit(1);
        }
	
        /* Get identification string */
        dg_write("*idn?\n");
        if (dg_read(buffer, sizeof(buffer)))
            printf("%s", buffer);
        else
            printf("Timeout\n");
        
        /* Load default settings */
        //dg_write("*rst\n");
        /* Set internal triggering */
        dg_write("tsrc 0\n");
        

        if (optionalArg == 0) {
            dg_write("trat 0.0001\n"); /* Set trigger rate */
            dg_write("dlay 5,4,0\n"); // second edge
            dg_write("dlay 4,3,0\n"); // first edge
        } else if (optionalArg == 1) {
            dg_write("trat 250\n"); /* Set trigger rate */
            dg_write("dlay 5,4,9.3e-9\n"); // second edge
            dg_write("dlay 4,3,10e-9\n"); // first edge
            //dg_write("dlay 7,6,200e-9\n");
            dg_write("lamp 2,3.5\n");
        }
        /* Make sure all commands have executed before closing connection */
        dg_write("*opc?\n");
        if (!dg_read(buffer, sizeof(buffer)))
            printf("Timeout\n");
        
        /* Close the connection */
        if (dg_close())
            printf("Closed connection\n");
        else
            printf("Unable to close connection");
    }
    else
        printf("Connection Failed\n");
    
    return 0;
}

int dg_connect(unsigned long ip)
{
    /* Connect to the DG645 */
    struct sockaddr_in intrAddr;
    int status;
    sDG645 = socket(AF_INET, SOCK_STREAM, 0);
    if (sDG645 == -1)
        return 0;
    
    /* Bind to a local port */
    memset(&intrAddr, 0, sizeof(intrAddr));
    intrAddr.sin_family = AF_INET;
    intrAddr.sin_port = htons(0);
    intrAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    if (bind(sDG645, (const struct sockaddr *)&intrAddr, sizeof(intrAddr)) == -1) {
        close(sDG645);
        sDG645 = -1;
        return 0;
    }
    
    /* Setup address for the connection to dg on port 5025 */
    memset(&intrAddr, 0, sizeof(intrAddr));
    intrAddr.sin_family = AF_INET;
    intrAddr.sin_port = htons(5025);
    intrAddr.sin_addr.s_addr = ip;
    status = connect(sDG645, (const struct sockaddr *)&intrAddr, sizeof(intrAddr));
    if (status) {
        close(sDG645);
        sDG645 = -1;
        return 0;
    }
    
    return 1;
}

int dg_close(void)
{
    if (close(sDG645) != -1)
        return 1;
    else
        return 0;
}

int dg_write(char *str)
{
    /* Write string to connection */
    int result;
    result = send(sDG645, str, strlen(str), 0);
    if (result == -1)
        result = 0;
    return result;
}

int dg_read(char *buffer, unsigned num)
{
    /* Read up to num bytes from connection */
    int count;
    fd_set setRead, setWrite, setExcept;
    struct timeval tm;

    /* Use select() so we can timeout gracefully */
    tm.tv_sec = dg_timeout / 1000;
    tm.tv_usec = (dg_timeout % 1000) * 1000;
    FD_ZERO(&setRead);
    FD_ZERO(&setWrite);
    FD_ZERO(&setExcept);
    FD_SET(sDG645, &setRead);
    count = select(sDG645 + 1, &setRead, NULL, NULL, &tm);
    if (count == -1) {
        printf("select failed: connection aborted\n");
        close(sDG645);
        exit(1);
    }
    count = 0;
    if (FD_ISSET(sDG645, &setRead)) {
        /* We've received something */
        count = recv(sDG645, buffer, num - 1, 0);
        if (count == -1) {
            printf("Receive failed: connection aborted\n");
            close(sDG645);
            exit(1);
        }
        else if (count) {
            buffer[count] = '\0';
        }
        else {
            printf("Connection closed by remote host\n");
            close(sDG645);
            exit(1);
        }
    }
    return count;
}

