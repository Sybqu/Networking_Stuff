#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdlib.h>
#define MYPORT "3490"
#define BACKLOG 10
#include <unistd.h>

int main()
{
    struct sockaddr_storage their_addr;
    socklen_t addr_size;
    struct addrinfo hints, *res;
    int new_fd;

    memset(&hints, 0, sizeof(hints));
    hints.ai_flags = AI_PASSIVE;
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int status;
    if ((status = getaddrinfo(NULL, MYPORT, &hints, &res)) != 0)
    {

        fprintf(stderr, "gai error:%s\n", gai_strerror(status));

        exit(1);
    };

    int sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sockfd == -1)
    {
        perror("socket creation failed");
    }
    int yes = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
    bind(sockfd, res->ai_addr, res->ai_addrlen);
    listen(sockfd, BACKLOG);
    addr_size = sizeof(their_addr);
    new_fd = accept(sockfd, (struct sockaddr *)&their_addr, &addr_size);
    printf("SUP GANG YOU ARE NOW LISTENING ON MY PERSONAL SERVER ^^ lfg \n");
    freeaddrinfo(res);
    char msg[] = "hi twin , turning on the chat client now ,im sending this from my raw http socket server fwaeh, please immediately start typing your message \n";
    int len = strlen(msg);

    int sent = send(new_fd, msg, len, 0);
    while (1)
    {
        char buffer[1024];
        char my_msg[1024];
        memset(buffer, 0, sizeof(buffer));
        char format_recv[1024];

        int received = recv(new_fd, buffer, sizeof(buffer), 0);
        char formatted_msg[1024];

        if (received <= 0)
        {
            printf("client disconnected \n");
            break;
        }

        buffer[received] = '\0';

        printf("Client: %s\n", buffer);

        printf("Cbau : \n");
        fflush(stdout);
        fgets(my_msg, 1024, stdin);
        snprintf(formatted_msg,sizeof(formatted_msg),"Cbau: %s",my_msg);

        send(new_fd, formatted_msg, strlen(formatted_msg), 0);
    }
    return 0;
}