 

int main(){
    int status;
    struct addrinfo hints;
    struct addrinfo *res,*p;
 
    
    memset(&hints,0,sizeof(hints));
    hints.ai_flags =AI_PASSIVE;
    hints.ai_family=AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    char ipstr[INET6_ADDRSTRLEN];


    if((status=getaddrinfo(NULL,"3490",&hints,&res))!=0){
        fprintf(stderr,"gai error:%s\n", gai_strerror(status));
        exit(1);
    }
    int sockfd = socket(res->ai_family,res->ai_socktype,res->ai_protocol);
    if(sockfd==-1){
        perror("socket creation failed");
    }
     bind(sockfd,res->ai_addr,res->ai_addrlen);
    int yes=1;
    setsockopt(sockfd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof(yes));

   /* int connection = connect(sockfd,res->ai_addr,res->ai_addrlen);
    if(connection==-1){
        perror("Connection failed");
    }
*/
int listening = listen(sockfd,6);
if(listenin==-1){
   perror("matter holiya ustaad");
}
    return 0;
}    
