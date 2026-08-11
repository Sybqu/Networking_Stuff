#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(){
    int status;
    struct addrinfo hints;
    struct addrinfo *res;
    memset(&hints,0,sizeof(hints));
    hints.ai_flags =AI_PASSIVE;
    hints.ai_family=AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if((status=getaddrinfo(NULL,"3490",&hints,&res))!=0){
        fprintf(stderr,"gai error:%s\n", gai_strerror(status));
        exit(1);
    }
    freeaddrinfo(res);
    return 0;
}