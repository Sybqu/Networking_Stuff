#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <unistd.h>
#include <poll.h>

#define MYPORT "3490"
#define BACKLOG 10
#define MAX_CLIENTS 50

// IMPORTANT: figures out whether a sockaddr is IPv4 or IPv6,
// and returns a pointer to the actual address field inside it.
// Renamed from inet_ntop -> get_in_addr, since inet_ntop already
// exists in <arpa/inet.h> and takes a different signature.
void *get_in_addr(struct sockaddr *sa)
{
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in *)sa)->sin_addr);
    }
    return &(((struct sockaddr_in6 *)sa)->sin6_addr);
}

void poll_check(struct pollfd *fds, int n)
{
    int poll_count = poll(fds, n, -1);
    if (poll_count == -1) {
        perror("poll error");
        exit(1);
    }
    for (int i = 0; i < n; i++) {
        if (fds[i].revents & POLLIN) {
            printf("Data is available to read on socket %d\n", fds[i].fd);
        }
    }
}

// n is passed by pointer since accepting/dropping clients changes
// the count, and main's loop needs to see the updated value.
void connection_handler(struct pollfd *fds, int *n)
{
    for (int i = 0; i < *n; i++) {
        if (!(fds[i].revents & POLLIN)) {
            continue;
        }

        if (fds[i].fd == fds[0].fd) {
            // listener fired -> new connection waiting, not data
            struct sockaddr_storage their_addr;
            socklen_t addr_size = sizeof their_addr;
            int new_fd = accept(fds[0].fd, (struct sockaddr *)&their_addr, &addr_size);

            if (new_fd == -1) {
                perror("accept");
                continue;
            }

            if (*n >= MAX_CLIENTS) {
                printf("too many clients, rejecting new connection\n");
                close(new_fd);
                continue;
            }

            char ip_str[INET6_ADDRSTRLEN];
            inet_ntop(their_addr.ss_family,
                      get_in_addr((struct sockaddr *)&their_addr),
                      ip_str, sizeof ip_str);
            printf("new connection from %s on socket %d\n", ip_str, new_fd);

            fds[*n].fd = new_fd;
            fds[*n].events = POLLIN;
            (*n)++;
        } else {
            // client fd fired -> actual data (or disconnect) to handle
            char buffer[1024];
            memset(buffer, 0, sizeof buffer);

            int bytes_received = recv(fds[i].fd, buffer, sizeof(buffer) - 1, 0);

            if (bytes_received <= 0) {
                if (bytes_received == 0) {
                    printf("socket %d disconnected\n", fds[i].fd);
                } else {
                    perror("recv error");
                }
                close(fds[i].fd);

                // compact the array: swap last entry into this slot
                fds[i] = fds[*n - 1];
                (*n)--;
                i--; // recheck this index since it now holds a different fd
                continue;
            }

            buffer[bytes_received] = '\0';
            printf("socket %d says: %s\n", fds[i].fd, buffer);

            // broadcast to every OTHER connected client (skip listener at 0, skip sender)
            for (int j = 1; j < *n; j++) {
                if (fds[j].fd != fds[i].fd) {
                    send(fds[j].fd, buffer, bytes_received, 0);
                }
            }
        }
    }
}

int main()
{
    struct pollfd fds[MAX_CLIENTS + 1];
    int n = 1; // slot 0 reserved for the listener; grows as clients join

    struct addrinfo hints, *servinfo, *p;
    int yes = 1;
    int status;

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    // getaddrinfo called ONCE, before the loop -- not inside it
    if ((status = getaddrinfo(NULL, MYPORT, &hints, &servinfo)) != 0) {
        fprintf(stderr, "getaddrinfo error: %s\n", gai_strerror(status));
        return 1;
    }

    for (p = servinfo; p != NULL; p = p->ai_next) {
        // parens fixed: assignment must happen before the == check
        if ((fds[0].fd = socket(p->ai_family, p->ai_socktype, p->ai_protocol)) == -1) {
            perror("server: socket");
            continue;
        }

        if (setsockopt(fds[0].fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
            perror("setsockopt");
            exit(1);
        }

        if (bind(fds[0].fd, p->ai_addr, p->ai_addrlen) == -1) {
            close(fds[0].fd);
            perror("server: bind");
            continue;
        }
        break;
    }

    freeaddrinfo(servinfo);

    if (p == NULL) {
        fprintf(stderr, "server: failed to bind\n");
        exit(1);
    }

    fds[0].events = POLLIN;

    if (listen(fds[0].fd, BACKLOG) == -1) {
        perror("listen");
        exit(1);
    }

    printf("server listening on port %s\n", MYPORT);

    while (1) {
        poll_check(fds, n);        // optional: just logs which fds are ready
        connection_handler(fds, &n);
    }

    return 0;
}