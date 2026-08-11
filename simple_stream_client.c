#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>

#include <arpa/inet.h>

#define PORT "3490" 

#define MAXDATASIZE 1024

void *get_in_addr(struct sockaddr *sa)
{
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in*)sa)->sin_addr);
    }

    return &(((struct sockaddr_in6*)sa)->sin6_addr);
}

int main(){
    int sockfd,bytes_received;  
    char buf[MAXDATASIZE];
    struct addrinfo hints,*servinfo,*p;
    int status;
    char s[INET6_ADDRSTRLEN];
    int yes=1;

    memset(&hints,0,sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;


    if(status = getaddrinfo(NULL,PORT,&hints,&servinfo)!=0){
        fprintf(stderr,"getaddrinfo error: %s\n",gai_strerror(status));
    }

    for (p = servinfo; p!= NULL ; p=p->ai_next)
    {
        if ((sockfd=socket(p->ai_family,p->ai_socktype,p->ai_protocol))==-1)
        {
            perror("server socket");
        }
        if (setsockopt(sockfd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof(int))==-1)
        {
            perror("setsockopt");
            exit(1);
        }
    
    if (connect(sockfd,p->ai_addr,p->ai_addrlen)==-1)
    {
        close(sockfd);
        perror("client: connection issue");
        continue;
    }
    
    break;
}
   freeaddrinfo(servinfo);

    if (p==NULL){
        perror("Failed to connect \n");
        exit(1);
    }

    inet_ntop(p->ai_family,get_in_addr((struct sockaddr *)p->ai_addr),s,sizeof(s));
    printf("client: connecting to %s\n",s);

    if ((bytes_received=recv(sockfd,buf,MAXDATASIZE-1,0))==-1)
    {
        perror("recv");
        exit(1);
    }
    buf[bytes_received]='\0';
    printf("client: received '%s'\n",buf);

    close(sockfd);





    return 0;
}