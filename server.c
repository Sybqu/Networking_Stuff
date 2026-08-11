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


int main(){
    struct sockaddr_storage their_addr;
    socklen_t addr_size;
    struct addrinfo hints,*res;
    int new_fd;



    memset(&hints,0,sizeof(hints));
    hints.ai_flags=AI_PASSIVE;
    hints.ai_family=AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

   int status;
if((status=getaddrinfo(NULL,MYPORT,&hints,&res))!=0){

fprintf(stderr,"gai error:%s\n", gai_strerror(status));

exit(1);

};

int sockfd = socket(res->ai_family,res->ai_socktype,res->ai_protocol);
 if(sockfd==-1){
        perror("socket creation failed");
    }
int yes=1;
setsockopt(sockfd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof(yes));
bind(sockfd,res->ai_addr,res->ai_addrlen);
listen(sockfd,BACKLOG);
addr_size=sizeof(their_addr);
new_fd=accept(sockfd,(struct sockaddr *)&their_addr,&addr_size);
printf("SUP GANG YOU ARE NOW LISTENING ON MY PERSONAL SERVER ^^ lfg \n");
freeaddrinfo(res);

while(1){
char msg[] = "hi twins im sending this from my raw http socket server fwaeh immediately start typing \n";
int len = strlen(msg);

int sent =  send(new_fd,msg,len,0);
char buffer[1024];
int received = recv(new_fd,buffer,1023,0);

if (received == -1) {
    perror("recv failed");
} else if (received == 0) {
    printf("The client closed the connection.\n");
} else {
 
    buffer[received] = '\0';
    
    printf("Netcat sent us: %s\n", buffer);
}
    char my_msg[1024];

    fgets(my_msg, 1024, stdin);
    send(new_fd,my_msg,strlen(my_msg),0);

}

return 0;
}