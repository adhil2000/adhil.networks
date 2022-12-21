/* The code is subject to Purdue University copyright policies.
 * DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>

#define LISTEN_QUEUE 50 /* Maximum outstanding connection requests; listen() param */

#define DBADDR "127.0.0.1"
#define BUFFLEN 1024
#define MAXLEN 4096

//output function declarations
void send_200(int sock);
void send_400(int sock);
void send_404(int sock);
void send_408(int sock);
void send_501(int sock);

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: ./http_server [server port] [DB port]\n");
        exit(1);
    }

    //grab input data
    int server_port;
    sscanf(argv[1], "%d", &server_port);

    int db_port;
    sscanf(argv[2], "%d", &db_port);

    //store socket data
    int sock;
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket");
        exit(1);
    }

    //declare server address details
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    bzero(&(server_addr.sin_zero), 8);
    server_addr.sin_port = htons(server_port);

    if (bind(sock, (struct sockaddr *) &server_addr, sizeof(struct sockaddr)) < 0) {
        perror("bind");
        exit(1);
    }

    if (listen(sock, 10) < 0) {
        perror("listen");
        exit(1);
    }

    struct hostent* he;
    int sockUDP;

    if ((he = gethostbyname(DBADDR)) == NULL) {
        herror("gethostbyname");
        exit(1);
    }

    if ((sockUDP = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socketUDP");
        exit(1);
    }

    //declare data address details
    struct sockaddr_in data_addr;
    data_addr.sin_family = AF_INET;
    data_addr.sin_port = htons(db_port);
    data_addr.sin_addr = *((struct in_addr *)he->h_addr_list[0]);
    bzero(&(data_addr.sin_zero), 8);
    char searchBuf[BUFFLEN] = {0};

    if (connect(sockUDP, (struct sockaddr *) &data_addr,sizeof(struct sockaddr)) < 0)
    {
        perror("connectUDP");
    }

    //declare variables used for later
    bool run_server= true;
    struct timeval time_value = {5,0};
    char buf[MAXLEN] = {0};
    setsockopt(sockUDP, SOL_SOCKET,SO_RCVTIMEO,(char *)&time_value,sizeof(struct timeval));
    int client_sock;
    int ssize;
    char dst[INET_ADDRSTRLEN];
    struct sockaddr_in client_addr;
    char method[BUFFLEN] = {0};
    char filePath[BUFFLEN] = {0};
    char site1[BUFFLEN] = {0};
    char printPath[BUFFLEN] = {0};
    int len;
    int numbytes;

    while(run_server == true) {
        ssize = sizeof(struct sockaddr_in);
        if ((client_sock = accept(sock,
                                  (struct sockaddr *) &client_addr, &ssize)) < 0) {
            perror("accept");
            continue;
        }

        inet_ntop(AF_INET, &(client_addr.sin_addr), dst, INET_ADDRSTRLEN);

        //set memory
        memset(printPath, 0, BUFFLEN);
        memset(method, 0, BUFFLEN);
        memset(filePath, 0, BUFFLEN);
        memset(site1, 0, BUFFLEN);
        char exactPath[BUFFLEN] = {"./Webpage"};

        char temp[1] = {0};
        int stdE = 0;
        int stdFr = 2;
        int i = 0;

        strncpy(printPath, " \"", 2);

        //check we are getting data from client sock
        while (recv(client_sock, temp, 1, 0) == 1) {
            if(temp[0] == '\r' || temp[0] == '\n') {
                strncpy(printPath + stdFr, "\" ", 2);
                break;

            }
            if(temp[0] == ' ')
            {
                i++;
                stdE = 0;
                strncpy(printPath + stdFr, temp, 1);
                stdFr++;
                continue;
            }

            //for our return conditions
            switch (i) {
                case 0:
                    strncpy(method + stdE, temp, 1);
                case 1:
                    strncpy(filePath + stdE, temp, 1);
                case 2:
                    strncpy(site1 + stdE, temp, 1);
                default:
                    strncpy(printPath + stdFr, temp, 1);
                    stdE++;
                    stdFr++;
                    break;
            }
        }

        strcat (exactPath,filePath);

        //output
        fprintf(stdout, "%s", dst);
        fprintf(stdout, "%s", printPath);

        //The web server will only support the GET method. If a browser sends other methods
        //(POST,HEAD, PUT, for example), the server responds with status code 501.
        if(strcmp(method, "GET") != 0)
        {
            //send to 501
            send_501(client_sock);
            fprintf(stdout, "501 Not Implemented\n");
            close(client_sock);
            continue;
        }
        if (run_server == true) {

            //the server should make sure that the request URI does not contain “/../”
            //and it does not end with “/..” because allowing “..” in the request URI is a big security risk
            int temp_out = 1;
            if(("/..") == NULL) {
                temp_out = -1;
            }
            int len1 = strlen(filePath);
            int len2 = strlen("/..");

            if((len1 < len2) ||  (len1 == 0 || len2 == 0)) {
                temp_out = -1;
            }

            while(len2 >= 1) {
                if(("/..")[len2 - 1] != filePath[len1 - 1])
                    temp_out = 0;
                len2--;
                len1--;
            }
            //The server should also check that the request URI(the part that comes after GET)
            //starts with “/”. If not, it should respond with “400 Bad Request”.
            //if those conditions aren't met, send a bad request method
            if((strncmp(filePath, "/", 1) != 0) || (strstr(filePath, "/../")) || (temp_out == 1)) {
                //send to 400
                send_400(client_sock);
                //WHY IS THIS SEG FAULTING!!!!!
                fprintf(stdout, "400 Bad Request\n");
                //i was forgetting to close client sock
                close(client_sock);
                continue;
            }
        }

        //condition to be met later since we likely dont want to run this every time
        if (run_server == true) {
            struct stat starter_path;
            stat(exactPath, &starter_path);
            int checker = S_ISDIR(starter_path.st_mode);

            //If the request URI ends with “/”, the server should treat it as if there were “index.html” appended to it.
            int temp_out = 1;
            if(("/") == NULL) {
                temp_out = -1;
            }
            int len1 = strlen(filePath);
            int len2 = strlen("/");

            if((len1 < len2) ||  (len1 == 0 || len2 == 0)) {
                temp_out = -1;
            }

            //#kartik is stupid
            while(len2 >= 1) {
                if(("/")[len2 - 1] != filePath[len1 - 1])
                    temp_out = 0;
                len2--;
                len1--;
            }

            //for indexing
            if((temp_out == 1) || checker) {
                strcat (exactPath,"index.html");
            }

        }

        //look for the given picture - cattos
        if(strstr(filePath, "?key="))
        {
            memset(searchBuf, 0, BUFFLEN);
            int i = 0;
            int j = 0;
            int bool1 = 0;
            char *tempfilePath = filePath;
            char *tempsearchBuf = searchBuf;
            while (i < strlen(tempfilePath)) {
                if (bool1 == 1)
                {
                    if (tempfilePath[i] != '+')
                    {
                        strncpy(tempsearchBuf + j, tempfilePath + i, 1);
                    }
                    else
                    {
                        strncpy(tempsearchBuf + j, " ", 1);
                    }
                    j++;
                }
                bool1 = (filePath[i] == '=') ? 1 : bool1;
                i++;
            }


            //messages to be sent according to the readme
            send(sockUDP, searchBuf, sizeof(searchBuf), 0);
            memset(buf, 0, MAXLEN);
            if ((numbytes = recv(sockUDP, buf, MAXLEN, MSG_WAITALL)) < 0)
            {
                //send t 408
                send_408(client_sock);
                fprintf(stdout, "408 Request Timeout\n");
                close(client_sock);
                continue;
            }
            if (strstr(buf, "File Not Found")!=NULL)
            {
                //send to 404
                send_404(client_sock);
                fprintf(stdout, "404 Not Found\n");
                close(client_sock);
                continue;
            }
            else
            {
                send_200(client_sock);

                if (strstr(buf, "DONE")!=NULL)
                {
                    send(client_sock, buf, (numbytes-4), 0);
                    fprintf(stdout, "200 OK\n");
                    close(client_sock);
                    continue;
                }
                send(client_sock, buf, numbytes, 0);
                while(strstr(buf, "DONE")==NULL)
                {
                    memset(buf, 0, MAXLEN);
                    if ((numbytes = recv(sockUDP, buf, MAXLEN, MSG_WAITALL)) < 0) {
                        //This one is for Nick - may he rest in peace
                        send_408(client_sock);
                        fprintf(stdout, "408 Request Timeout\n");
                        close(client_sock);
                        continue;
                    }
                    send(client_sock, buf, numbytes, 0);
                }
                send(client_sock, buf, (numbytes-4), 0);
                fprintf(stdout, "200 OK\n");
                close(client_sock);
                continue;
            }
        }

        int fp = open(exactPath, O_RDONLY);
        if(fp == -1)
        {
            //send that shit again
            send_404(client_sock);
            fprintf(stdout, "404 Not Found\n");
            close(client_sock);
            continue;
        }

        send_200(client_sock);

        memset(buf, 0, MAXLEN);

        //should only need to run things once
        len = read(fp,buf,MAXLEN);
        send(client_sock, buf, len, 0);
        //give it some time to catch up
        usleep(10000);

        //We actually need to loop through it a few times
        while (len) {
            len=read(fp,buf,MAXLEN);
            send(client_sock, buf, len, 0);
            //give it some time to catch up
            usleep(10000);
        }

        close(fp);
        fprintf(stdout, "200 OK\n");

        //close to stop the seg-faults
        close(client_sock);

    }

    close(sockUDP);
    close(sock);

    //not exit
    return 0;
}

//Functions for printing output
void send_200(int sock) {
    char html[19] = "HTTP/1.0 200 OK\r\n\r\n";
    send(sock, html, sizeof(html), 0);
}

void send_400(int sock) {
    char html1[BUFFLEN] =  "HTTP/1.0 400 Bad Request\r\n\r\n<html><body><h1>400 Bad Request</h1></body></html>";
    send(sock, html1, sizeof(html1), 0);
}

void send_404(int sock) {
    char html2[BUFFLEN] = "HTTP/1.0 404 Not Found\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>";
    send(sock, html2, sizeof(html2), 0);
}

void send_408(int sock) {
    char html3[BUFFLEN] = "HTTP/1.0 408 Request Timeout\r\n\r\n<html><body><h1>408 Request Timeout</h1></body></html>";
    send(sock, html3, sizeof(html3), 0);
}

void send_501(int sock) {
    char html4[BUFFLEN] = "HTTP/1.0 501 Not Implemented\r\n\r\n<html><body><h1>501 Not Implemented</h1></body></html>";
    send(sock, html4, sizeof(html4), 0);
}