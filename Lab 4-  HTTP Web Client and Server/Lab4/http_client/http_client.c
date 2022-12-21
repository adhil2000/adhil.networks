/* The code is subject to Purdue University copyright policies.
 * DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/stat.h>

#define BUFFLEN 1024 

// Function Declarations
int write_file(char *buffer, int sock, int file);
void request_success(char *text);
void check_content_length(char *text);

// HTTP Web Page Downloader - A.A.
int main(int argc, char *argv[])
{
    if (argc != 4)
    {
        fprintf(stderr, "usage: ./http_client [host] [port number] [filepath]\n");
        exit(1);
    }

    // Get Host Name from argv[1] - A.A.
    char host_name[BUFFLEN];
    memset(host_name, 0, BUFFLEN);
    sscanf(argv[1], "%s", host_name);

    // Get Port Number from argv[2] - A.A.
    int port_num;
    sscanf(argv[2], "%d", &port_num);

    // Get File Path from argv[3] - A.A.
    char file_path[BUFFLEN];
    memset(file_path, 0, BUFFLEN);
    sscanf(argv[3], "%s", file_path);

    // Get Filename, Example: make.html - A.A.
    char file_name[BUFFLEN] = {0};
    strncpy(file_name, (strrchr(argv[3], '/') + 1), BUFFLEN);

    // 1. The program should open a TCP socket connection to the host and port number specified in the - A.A.
    //    command line, and then request the given file using HTTP/1.x protocol. - A.A.
    // Family: AF_INET
    // Type: SOCK_STREAM
    // Protocol: 0, default is TCP
    int sock = socket(AF_INET, SOCK_STREAM, 0);

    // Returns IP of Host Given it's Name (invokes DNS) - A.A.
    struct hostent *URL = NULL;
    URL = gethostbyname(host_name);

    // 2. An HTTP GET request looks like this: - A.A.
    //      GET /path/file.html HTTP/1.0\r\n
    //      [zero or more headers]\r\n
    //      [blank line]\r\n
    char request[BUFFLEN];
    memset(request, 0, BUFFLEN);
    snprintf(request, sizeof(request), "GET /%s HTTP/1.1\r\nHost: %s:%s\r\n\r\n", argv[3], argv[1], argv[2]);

    // Server Address Parameters - A.A.
    // struct sockaddr_in {
    //    short            sin_family;   // e.g. AF_INET
    //    unsigned short   sin_port;     // e.g. htons(3490)
    //    struct in_addr   sin_addr;     // see struct in_addr, below
    //    char             sin_zero[8];  // zero this if you want to

    struct sockaddr_in server_addr;
    bzero(&server_addr, sizeof(struct sockaddr_in));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port_num);
    server_addr.sin_addr.s_addr	= *((unsigned long *)URL->h_addr_list[0]);

    // Initiate Connection To A Server (e.g., 3-way handshake) - A.A.
    // * If the connection or binding succeeds, zero is returned.
    // * On error, -1 is returned, and errno is set to indicate the error.
    connect(sock, (struct sockaddr *)&server_addr, (socklen_t)sizeof(server_addr));

    // Send Data between Connection-Oriented Sockets -> URL Request - A.A.
    int request_length = strlen( request );
    // * On success, these calls return the number of bytes sent.  On
    // * error, -1 is returned, and errno is set to indicate the error.
    send(sock, request, request_length, 0 ); // puts 1 packet into the pipe with the contents of request

    int i = 0; 
    int bool = 1;
    int stdev = 0;
    char temp[1] = {0};
    char line[BUFFLEN] = {0};
    char temp_line[BUFFLEN] = {0}; 
    memset(line, 0, BUFFLEN);
    memset(temp_line, 0, BUFFLEN);

    // Removes 1 Packet from The Pipe and Stores in Temp
    while ((recv(sock, temp, 1, 0) == 1) && (bool)) // * Worry about Structure
    {

        if ((bool) && (stdev > (sizeof(line) - 1)))
        {
            bool = 0;
            break;
        }

        if ((bool) && (i < 4))
        {
            i = (temp[0] == '\r' || temp[0] == '\n') ? (i + 1) : 0;
            if (i == 0) { strncpy(temp_line + stdev, temp, 1); }
            strncpy(line + stdev, temp, 1);
            stdev++;
        }

        if ((bool) && (i == 4))
        {
            bool = 0;
            break;
        }
    }

    // Check for Code "200"
    request_success(line);
    // Check for Content-Length
    check_content_length(line);


    remove(file_name);
    int file = open(file_name, O_WRONLY | O_CREAT, 777 );

    char buffer[BUFFLEN] = {0};
    // Write to Directory
    write_file(buffer, sock, file);

    // Close Sockets
	close(file);
	close(sock);

    return 0;
}

// Function to check if "200" exists
void request_success(char *text)
{
    int status;
    char *temp_buf = text;
    sscanf(temp_buf, "%*s %d ", &status);
    // printf("%d\n", status);

    // If it’s not ”200”, the program should print the first line of the response to the terminal (stdout) and exit.
    if (status != 200)
    {
        printf("%s\n", temp_buf);
        exit(0);
    }
}

// Function to check Content-Length
void check_content_length(char *text)
{
    int total_bytes;
    char *temp_buff1 = text;

    // If the “Content-Length” field is not present in the response header, print the following error message to the terminal (stdout) and exit:
    // Error: could not download the requested file (file length unknown)
    if (total_bytes) {
        temp_buff1 = strstr(temp_buff1, "Content-Length:");
        if (temp_buff1) {
            sscanf(temp_buff1, "%*s %d", &total_bytes);

        } else {
            total_bytes = -1;
            printf("Error: could not download the requested file (file length unknown)\n");
        }
    }
}

// Write to File
int write_file(char *buffer, int sock, int file)
{
    int bool = 1;

    while (bool)
    {
        memset(buffer, 0, BUFFLEN );
        int fd = recv(sock, buffer, BUFFLEN, 0);
        if (fd <= 0)
        {
            return 0;
        }

        if (write(file, buffer, fd) == -1)
        {
            printf("file is %d\n", file);
            return 0;
        }
    }
    return 1;
}


