import socket
import sys

HOST = 'localhost'
PORT = 3490

active_clients = {}  # Dictionary to store active client sockets and their addresses

# 1. Resolve address and create the server socket
addr_info = socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
server_socket = None

def ip_check(server_socket):
    client_socket, addr = server_socket.accept()
        
        # Check IPv4 or IPv6
    if client_socket.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
       
        
    elif client_socket.family == socket.AF_INET6:
            print(f"Accepted connection from IPv6 address: {addr[0]}")

    return client_socket,addr
         
def connection_handler(poll_dict : dict, connections : int):
    while True:
        new_sock,new_ip = ip_check(server_socket)
        active_clients[new_ip]=new_sock




    ...


for family, socktype, proto, canonname, sockaddr in addr_info:
    try:
        server_socket = socket.socket(family, socktype, proto)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(sockaddr)
        server_socket.listen(5)
        print(f"Listening on {sockaddr} (Family: {family.name})")
        break
    except OSError:
        if server_socket:
            server_socket.close()
        server_socket = None

if server_socket is None:
    print("Failed to bind server socket.")
    sys.exit(1)

# 2. Main server loop with error handling
try:
    client_socket, addr = server_socket.accept()
    
    # Check IPv4 or IPv6
    if client_socket.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
    elif client_socket.family == socket.AF_INET6:
        print(f"Accepted connection from IPv6 address: {addr[0]}")

    # 'with' ensures the client socket closes automatically
    with client_socket:
        while True:
            try:
                # Send data
                msg = input("Enter data to send (or press Enter to quit): ")
                if not msg:
                    break
                client_socket.sendall(msg.encode('utf-8'))
                
                # Receive data
                data = client_socket.recv(1024)
                if not data:
                    print("Client disconnected gracefully.")
                    break
                    
                print(f"Received data from client: {data.decode('utf-8')}")
                
            except (ConnectionResetError, BrokenPipeError):
                print("Error: Client dropped the connection unexpectedly.")
                break

except KeyboardInterrupt:
    print("\nServer shut down by user.")
except OSError as e:
    print(f"Server error: {e}")
finally:
    server_socket.close()