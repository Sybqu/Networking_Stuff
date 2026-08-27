import socket
import sys
import selectors

HOST = 'localhost'
PORT = 3490

# I CALL HER ARC KYONKI WO BANNA CHAHTI MERE CIRCLE KA HISSA FAHHHHH
from http_parser import (
    http_handler,
    handle_index,
    handle_get_messages,
    handle_post_messages,
    handle_404,
    build_response,
    is_ws,
    ws_upgrade
)
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

# Routes

routes_dict = {
    ("GET",b"/") : handle_index ,
    ("GET",b"/messages") : handle_get_messages,
    ("POST",b"/messages") : handle_post_messages,
    
}



sel = selectors.DefaultSelector()
sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
sel.register(server_socket, selectors.EVENT_READ, data="listener")    
while True:
    events = sel.select(timeout=None)
    for key, _ in events:
        if key.data == "listener":
            new_sock_for_comms , addr = ip_check(key.fileobj)
            new_sock_for_comms .setblocking(False)

            sel.register(new_sock_for_comms , selectors.EVENT_READ, data={"buffer":b""})
        elif key.data == "stdin":
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
            req_dict = http_handler(conn["buffer"])

            
            if req_dict is not None:
                if is_ws(req_dict) is True:
                    status,headers,body = ws_upgrade(req_dict)
                    response = build_response(status,headers,body)
                    print(response)
                    client_sock.send(response)
                    conn["mode"]="ws"
                else:
                    method = req_dict["method"].decode()
                    path = req_dict["path"]
                    handler_func = routes_dict.get((method, path), handle_404)
                    status, headers, body = handler_func(req_dict)
                    response = build_response(status, headers, body)  # still need to write this
                    client_sock.send(response)
                    print(build_response(200, {"Content-Type": "text/plain"}, b"hi"))

            else:
                pass  # not a full request yet — just wait for the next recv()

        

    

                
                
