import socket
import sys
import selectors

HOST = 'localhost'
PORT = 3490


# 1. Resolve address and create the server socket
addr_info = socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)

def ip_check(server_socket):
    new_Sock, addr = server_socket.accept()
        
        # Check IPv4 or IPv6
    if new_Sock.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
       
        
    elif new_Sock.family == socket.AF_INET6:
            print(f"Accepted connection from IPv6 address: {addr[0]}")

    return new_Sock,addr

          
def set_up():
    new_socket = None
    for family, socktype, proto, canonname, sockaddr in addr_info:
        try:
           new_socket = socket.socket(family, socktype, proto)
           new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
           new_socket.bind(sockaddr)
           new_socket.listen(5)
           print(f"Listening on {sockaddr} (Family: {family.name})")
           break
        except OSError:
            if new_socket:
                new_socket.close()
            new_socket = None
            
    return new_socket

server_socket = set_up()  

if server_socket is None:
    print("Failed to bind server socket.")
    sys.exit(1)
    server_socket.close()

# main

sel = selectors.DefaultSelector()
sel.register(server_socket, selectors.EVENT_READ, data=None)    
while True:
    events = sel.select(timeout=None)
    for key, _ in events:
        if key.data is None:
            new_sock_for_comms , addr = ip_check(key.fileobj)
            new_sock_for_comms .setblocking(False)

            sel.register(new_sock_for_comms , selectors.EVENT_READ, data=addr)
        else:
            
            client_ip = key.data[0]
            data = key.fileobj.recv(1024)

            if data:
                print(f"Received data from {addr}: {data.decode()}")
                sock = key.fileobj
               if sock!=server_socket and sock!=new_sock_for_comms:
                key.fileobj.sendall(data)  # Echo back the received data
            else:
                print(f"Closing connection to {addr}")
                sel.unregister(key.fileobj)
                key.fileobj.close()




