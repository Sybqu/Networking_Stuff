import socket
import sys
import selectors
import traceback

HOST = 'localhost'
PORT = 3490

from http_parser import (
    HttpError,
    http_handler,
    handle_index,
    handle_get_messages,
    handle_post_messages,
    handle_404,
    build_response,
    is_ws,
    ws_upgrade,
    ws_parse_frame,
    ws_build_frame,
)

class Connection:
    def __init__(self,sock:socket.socket):
        self.sock = sock
        self.buffer =b""
        self.mode="http"
        # Connection Type : skippign its keep-alive for now
    def append(self,chunk:bytes)->None:
        self.buffer += chunk

    def consume(self,count:int)->None: # Count can be passed req_dict["length"]
        self.buffer = self.buffer[count:] 

    def Upgrade_WS(self):
        self.mode = "ws"
    # Send and close method , to remove the redundacy of error handling over n mover , tiny mistakes can lead to problem

    def send(self,data:bytes)->bool:
        try: 
          self.sock.sendall(data)
        except(BrokenPipeError,ConnectionResetError,BlockingIOError,OSError):
           return False;
        return True

    def close(self,sel:selectors.DefaultSelector)->bool:
        try:
            sel.unregister(self.sock)
        except(KeyError, ConnectionResetError, BlockingIOError, OSError):
            pass
        try:
            self.sock.close() # Missed this :P
        except(BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
            return False;
        return True


def shutdown_server(sel:selectors.DefaultSelector,server:socket):
    print("\nShutting down — closing all connections...")
    for key in list(sel.get_map().values()):
       if isinstance(key.data,Connection):
            key.data.close(sel) 
    server.close()        
    try:
        sel.close()
    except Exception:
        pass

def ip_check(server:socket): # IM a bit confused in this cuz im not using a setter later on but this returns 
    # new_connection i wonder if it will be treated as object,  earlier i was trying to initialize new_connection to none and then set values but tahts redudnadnt so is there a better way
    new_connection, addr = server.accept() 
    if new_connection.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
    elif new_connection.family == socket.AF_INET6:
        print(f"Accepted connection from IPv6 address: {addr[0]}")
    return Connection(new_connection), addr

def set_up(host=HOST, port=PORT): #Server setup afaik?
    server_socket = None
    addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
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
    return server_socket

# DISPATCH TABLE FOR HANDLING , CAN I USE? UHM OOPS HERE ITS PREFERED AFAIK
routes_dict = {
    ("GET", b"/"): handle_index,
    ("GET", b"/messages"): handle_get_messages,
    ("POST", b"/messages"): handle_post_messages,
}



def ws_broadcast(sel:selectors.DefaultSelector, frame:bytes):
    # Broadcast WebSocket frame to all connected clients in WebSocket mode
    for key in list(sel.get_map().values()):
        if isinstance(key.data, Connection) and key.data.mode== "ws":
           # peer_sock = Connection(key.fileobj,buffer="",mode="ws")
           peer_sock = key.data
           if not peer_sock.send(frame):
                        peer_sock.close(sel)

def run_server(host=HOST, port=PORT, ready_event=None, stop_event=None):
    server_socket = set_up(host, port)
    if server_socket is None:
        print("Failed to bind server socket.")
        if ready_event:
            ready_event.set()
        return

    actual_port = server_socket.getsockname()[1]
    sel = selectors.DefaultSelector()
    # sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
    sel.register(server_socket, selectors.EVENT_READ, data="listener")
    # Register server socket at idx1 (optional)

    if ready_event:
        ready_event.port = actual_port
        ready_event.server_socket = server_socket
        ready_event.set()

    try:
        while stop_event is None or not stop_event.is_set():
            events = sel.select(timeout=0.1)
            # select till timeout occurs
            for key, _ , mask in events: #(fileobj , events , data)
                if key.data == "listener": #(if im the server listening for sockets)
                    new_sock_for_comms, addr = ip_check(key.fileobj) # In the function protoype we are passing a socket , but accept is happening due to server socket
                    # so uh how will be accept it i havent really referenced the global server_socket anywhere or it has been referenced by itself in python?
                    new_sock_for_comms.sock.setblocking(False) #(assigning a new socket fd that communicates with others)
                    sel.register(new_sock_for_comms.sock, selectors.EVENT_READ, new_sock_for_comms)
                # Shelved for future improvement admin perms :>
                # elif key.data == "stdin": #(if the server wants to send data)
                #   line = sys.stdin.readline() 
                #   for other_key in list(sel.get_map().values()):#(list all the fds in selectors)
                #      if isinstance(other_key.data, dict):#(if a socket has a dict its a listener send all data)
                #         other_key.fileobj.sendall(line.encode())

                else:
                    conn = key.data
                    conn.sock = key.fileobj 
                    #assign client socket | i dont think i need to resassign socket to fileobj but well i see about this in review

                    try:
                        chunk = conn.sock.recv(1024)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        chunk = b""

                    if not chunk:
                        conn.sock.close(sel)
                        continue

                    conn.append(chunk) #(defined function)
                     # keep on recovering data from the client till all data received 
                    if conn.mode== "ws":
                        # WS SUPPORT AFTER CONNECTION UPGRADE
                        # buffer may hold more than one frame back to back
                        while True:
                            result = ws_parse_frame(conn.buffer)
                            if result is None:
                                break  # not a full frame yet — wait for next recv()

                            opcode, payload, consumed_bytes = result
                            conn.consume(consumed_bytes)

                            if opcode == 0x8:  # close
                                try: # im wondering if i need to remove these byte blocks cuz error handling has be done for functions under Connection clase but not functions in http_parser.py
                                    conn.send(ws_build_frame(0x8, b""))
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    pass
                                conn.close(sel)
                                break
                            elif opcode == 0x9:  # ping
                                try:
                                    conn.send(ws_build_frame(0xA, payload)) # pong :3
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    conn.close(sel)
                                    break
                            elif opcode in (0x1, 0x2):  # text/binary
                                print(f"ws payload from {conn}: {bytes(payload)!r}") # dont understand this line its a dictionary right ~ need to return object.buffer here but uh whats this line explin
                                frame = ws_build_frame(opcode, bytes(payload))
                                ws_broadcast(sel, frame)

                    else:
                        while True:
                            try:
                                req_dict = http_handler(conn.buffer)  # Drain all complete requests from buffer
                            except HttpError as err:
                                try:
                                    err_resp = build_response(err.status_code, {"Content-Type": "text/plain", "Connection": "close"}, err.message.encode() if err.message else b"Bad Request")
                                    conn.send(err_resp)
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    pass
                                conn.close(sel)
                                break

                            if req_dict is None:
                                break  # Incomplete request or buffer empty — wait for next recv()

                            conn["buffer"] = conn["buffer"][req_dict["length"]:]

                            if is_ws(req_dict):
                                status, headers, body = ws_upgrade(req_dict)
                                response = build_response(status, headers, body)
                                try:
                                    client_sock.sendall(response)
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    close_client(sel, client_sock)
                                    break
                                conn["mode"] = "ws"
                                break  # Upgraded to WebSocket, exit HTTP drain loop
                            else:
                                method = req_dict["method"].decode(errors="replace")
                                path = req_dict["path"]
                                handler_func = routes_dict.get((method, path), handle_404)
                                try:
                                    status, headers, body = handler_func(req_dict)
                                    response = build_response(status, headers, body)
                                except Exception:
                                    traceback.print_exc()
                                    try:
                                        err_resp = build_response(500, {"Content-Type": "text/plain", "Connection": "close"}, b"Internal Server Error")
                                        client_sock.sendall(err_resp)
                                    except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                        pass
                                    close_client(sel, client_sock)
                                    break

                                try:
                                    client_sock.sendall(response)
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    close_client(sel, client_sock)
                                    break
                                # fulfil req and send response to user
    finally:
        shutdown_server(sel, server_socket)

def main():
    run_server(HOST, PORT)

if __name__ == "__main__":
    main()
