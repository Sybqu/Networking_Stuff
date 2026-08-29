import socket
import sys
import selectors

HOST = 'localhost'
PORT = 3490

from http_parser import (
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

addr_info = socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
def shutdown_server(sel, server_socket):
    print("\nShutting down — closing all connections...")
    for key in list(sel.get_map().values()):
        if isinstance(key.data, dict):
            key.fileobj.close()
    server_socket.close()
    sel.close()

def ip_check(server_socket):
    new_Sock, addr = server_socket.accept()
    if new_Sock.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
    elif new_Sock.family == socket.AF_INET6:
        print(f"Accepted connection from IPv6 address: {addr[0]}")
    return new_Sock, addr

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

routes_dict = {
    ("GET", b"/"): handle_index,
    ("GET", b"/messages"): handle_get_messages,
    ("POST", b"/messages"): handle_post_messages,
}

sel = selectors.DefaultSelector()
sel.register(sys.stdin, selectors.EVENT_READ, data="stdin")
sel.register(server_socket, selectors.EVENT_READ, data="listener")

while True:
    events = sel.select(timeout=None)
    for key, _ in events:
        if key.data == "listener":
            new_sock_for_comms, addr = ip_check(key.fileobj)
            new_sock_for_comms.setblocking(False)
            sel.register(new_sock_for_comms, selectors.EVENT_READ, data={"buffer": b""})

        elif key.data == "stdin":
            line = sys.stdin.readline()
            for other_key in list(sel.get_map().values()):
                if isinstance(other_key.data, dict):
                    other_key.fileobj.sendall(line.encode())

        else:
            conn = key.data
            client_sock = key.fileobj

            try:
                chunk = client_sock.recv(1024)
            except (ConnectionResetError, BrokenPipeError, OSError):
                chunk = b""

            if not chunk:
                sel.unregister(client_sock)
                client_sock.close()
                continue

            conn["buffer"] += chunk

            if conn.get("mode") == "ws":
                # buffer may hold more than one frame back to back
                while True:
                    result = ws_parse_frame(conn["buffer"])
                    if result is None:
                        break  # not a full frame yet — wait for next recv()

                    opcode, payload, consumed = result
                    conn["buffer"] = conn["buffer"][consumed:]  # drop what we just parsed

                    if opcode == 0x8:  # close
                        client_sock.send(ws_build_frame(0x8, b""))
                        sel.unregister(client_sock)
                        client_sock.close()
                        break
                    elif opcode == 0x9:  # ping
                        client_sock.send(ws_build_frame(0xA, payload))
                    elif opcode in (0x1, 0x2):  # text/binary
                        print(f"ws payload from {client_sock}: {bytes(payload)!r}")
                        client_sock.send(ws_build_frame(opcode, bytes(payload)))  # echo back for now

            else:
                req_dict = http_handler(conn["buffer"])

                if req_dict is not None:
                    conn["buffer"] = b""  # this request's bytes are fully consumed

                    if is_ws(req_dict):
                        status, headers, body = ws_upgrade(req_dict)
                        response = build_response(status, headers, body)
                        client_sock.send(response)
                        conn["mode"] = "ws"
                    else:
                        method = req_dict["method"].decode()
                        path = req_dict["path"]
                        handler_func = routes_dict.get((method, path), handle_404)
                        status, headers, body = handler_func(req_dict)
                        response = build_response(status, headers, body)
                        client_sock.send(response)
