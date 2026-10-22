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

def shutdown_server(sel, server_socket):
    print("\nShutting down — closing all connections...")
    for key in list(sel.get_map().values()):
        if isinstance(key.data, dict):
            key.fileobj.close()
    try:
        server_socket.close()
    except Exception:
        pass
    try:
        sel.close()
    except Exception:
        pass

def ip_check(server_socket):
    new_Sock, addr = server_socket.accept()
    if new_Sock.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
    elif new_Sock.family == socket.AF_INET6:
        print(f"Accepted connection from IPv6 address: {addr[0]}")
    return new_Sock, addr

def set_up(host=HOST, port=PORT):
    new_socket = None
    addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
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

# DISPATCH TABLE FOR HANDLING , CAN I USE? UHM OOPS HERE ITS PREFERED AFAIK
routes_dict = {
    ("GET", b"/"): handle_index,
    ("GET", b"/messages"): handle_get_messages,
    ("POST", b"/messages"): handle_post_messages,
}

def close_client(sel, client_sock):
    try:
        sel.unregister(client_sock)
    except Exception:
        pass
    try:
        client_sock.close()
    except Exception:
        pass

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
            for key, _ in events: #(events : fileobj , events , data)
                if key.data == "listener": #(if im the server listening for sockets)
                    new_sock_for_comms, addr = ip_check(key.fileobj)
                    new_sock_for_comms.setblocking(False) #(assigning a new socket fd that communicates with others)
                    sel.register(new_sock_for_comms, selectors.EVENT_READ, data={"buffer": b""})
                # Shelved for future improvement admin perms :>
                # elif key.data == "stdin": #(if the server wants to send data)
                #   line = sys.stdin.readline() 
                #   for other_key in list(sel.get_map().values()):#(list all the fds in selectors)
                #      if isinstance(other_key.data, dict):#(if a socket has a dict its a listener send all data)
                #         other_key.fileobj.sendall(line.encode())

                else:
                    conn = key.data
                    client_sock = key.fileobj
                    #assign client socket

                    try:
                        chunk = client_sock.recv(1024)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        chunk = b""

                    if not chunk:
                        close_client(sel, client_sock)
                        continue

                    conn["buffer"] += chunk
                     # keep on recovering data from the client till all data received 
                    if conn.get("mode") == "ws":
                        # WS SUPPORT AFTER CONNECTION UPGRADE
                        # buffer may hold more than one frame back to back
                        while True:
                            result = ws_parse_frame(conn["buffer"])
                            if result is None:
                                break  # not a full frame yet — wait for next recv()

                            opcode, payload, consumed = result
                            conn["buffer"] = conn["buffer"][consumed:]  # drop what we just parsed

                            if opcode == 0x8:  # close
                                try:
                                    client_sock.sendall(ws_build_frame(0x8, b""))
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    pass
                                close_client(sel, client_sock)
                                break
                            elif opcode == 0x9:  # ping
                                try:
                                    client_sock.sendall(ws_build_frame(0xA, payload))
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    close_client(sel, client_sock)
                                    break
                            elif opcode in (0x1, 0x2):  # text/binary
                                print(f"ws payload from {client_sock}: {bytes(payload)!r}")
                                try:
                                    client_sock.sendall(ws_build_frame(opcode, bytes(payload)))  # echo back for now
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    close_client(sel, client_sock)
                                    break

                    else:
                        while True:
                            try:
                                req_dict = http_handler(conn["buffer"])  # Drain all complete requests from buffer
                            except HttpError as err:
                                try:
                                    err_resp = build_response(err.status_code, {"Content-Type": "text/plain", "Connection": "close"}, err.message.encode() if err.message else b"Bad Request")
                                    client_sock.sendall(err_resp)
                                except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
                                    pass
                                close_client(sel, client_sock)
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
