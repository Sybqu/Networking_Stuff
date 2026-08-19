import socket
import sys
import selectors

HOST = 'localhost'
PORT = 3490


from http_parser import http_handler

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
    # Fix: unpacking 5 variables
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
sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
sel.register(server_socket, selectors.EVENT_READ, data="listener")    
while True:
    events = sel.select(timeout=None)
    for key, _ in events:
        if key.data is "listener":
            new_sock_for_comms , addr = ip_check(key.fileobj)
            new_sock_for_comms .setblocking(False)

            sel.register(new_sock_for_comms , selectors.EVENT_READ, data={"buffer":b""})
        elif key.data is "stdin":
            line = sys.stdin.readline()
            for other_key in list(sel.get_map().values()):
                 if isinstance(other_key.data, dict):   # a real client conn
                      other_key.fileobj.sendall(line.encode())
        else:
            conn = key.data
            client_sock = key.fileobj

            try:
                chunk = client_sock.recv(1024)
            except (ConnectionResetError, BrokenPipeError, OSError):
                chunk = b""
            print(f"utf-8 decoded chunk: {chunk.decode()}")


            if not chunk:
                sel.unregister(client_sock)
                client_sock.close()
                continue

            conn["buffer"] += chunk
            result = http_handler(conn["buffer"])

            if result is not None:
                client_sock.send(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nhi')
                

                




     
