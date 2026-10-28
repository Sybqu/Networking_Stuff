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
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = b""
        self.mode = "http"

    def __repr__(self) -> str:
        try:
            peer = self.sock.getpeername()
        except OSError:
            peer = "disconnected"
        return f"<Connection peer={peer} mode={self.mode}>"

    def append(self, chunk: bytes) -> None:
        self.buffer += chunk

    def consume(self, count: int) -> None:
        self.buffer = self.buffer[count:]

    def upgrade_to_ws(self) -> None:
        self.mode = "ws"

    def send(self, data: bytes) -> bool:
        try:
            self.sock.sendall(data)
        except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
            return False
        return True

    def close(self, sel: selectors.DefaultSelector) -> bool:
        try:
            sel.unregister(self.sock)
        except Exception:
            pass
        try:
            self.sock.close()
        except (BrokenPipeError, ConnectionResetError, BlockingIOError, OSError):
            return False
        return True


def shutdown_server(sel: selectors.DefaultSelector, server: socket.socket | None):
    print("\nShutting down — closing all connections...")
    for key in list(sel.get_map().values()):
        if isinstance(key.data, Connection):
            key.data.close(sel)
    if server:
        try:
            server.close()
        except Exception:
            pass
    try:
        sel.close()
    except Exception:
        pass

def accept_connection(server: socket.socket):
  try:
      new_connection, addr = server.accept()
      if new_connection.family == socket.AF_INET:
        print(f"Accepted connection from IPv4 address: {addr[0]}")
      elif new_connection.family == socket.AF_INET6:
        print(f"Accepted connection from IPv6 address: {addr[0]}")
  except(OSError):
       return None,None;
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
    sel.register(server_socket, selectors.EVENT_READ, data="listener") #
    # Register server socket at idx1 (optional)

    if ready_event:
        ready_event.port = actual_port
        ready_event.server_socket = server_socket
        ready_event.set()

    try:
        while stop_event is None or not stop_event.is_set():
            events = sel.select(timeout=0.1)
            for key, _ in events:
                if key.data == "listener":
                    conn, addr = accept_connection(key.fileobj)
                    if not conn or not addr :
                        continue;                       
                    conn.sock.setblocking(False)
                    sel.register(conn.sock, selectors.EVENT_READ, data=conn)

                else:
                    conn = key.data

                    try:
                        chunk = conn.sock.recv(1024)
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        chunk = b""

                    if not chunk:
                        conn.close(sel)
                        continue

                    conn.append(chunk)
                    if conn.mode == "ws":
                        while True:
                            result = ws_parse_frame(conn.buffer)
                            if result is None:
                                break

                            opcode, payload, consumed_bytes = result
                            conn.consume(consumed_bytes)

                            if opcode == 0x8:  # close
                                conn.send(ws_build_frame(0x8, b""))
                                conn.close(sel)
                                break
                            elif opcode == 0x9:  # ping
                                if not conn.send(ws_build_frame(0xA, payload)):
                                    conn.close(sel)
                                    break
                            elif opcode in (0x1, 0x2):  # text/binary
                                print(f"ws payload from {conn}: {bytes(payload)!r}")
                                frame = ws_build_frame(opcode, bytes(payload))
                                ws_broadcast(sel, frame)

                    else:
                        while True:
                            try:
                                req_dict = http_handler(conn.buffer)
                            except HttpError as err:
                                err_resp = build_response(err.status_code, {"Content-Type": "text/plain; charset=utf-8", "Connection": "close"}, err.message.encode() if err.message else b"Bad Request")
                                conn.send(err_resp)
                                conn.close(sel)
                                break

                            if req_dict is None:
                                break

                            conn.consume(req_dict["length"])

                            if is_ws(req_dict):
                                status, headers, body = ws_upgrade(req_dict)
                                response = build_response(status, headers, body)

                                if not conn.send(response):
                                    conn.close(sel)

                                conn.upgrade_to_ws()
                                break
                            else:
                                method = req_dict["method"].decode(errors="replace")
                                path = req_dict["path"]
                                handler_func = routes_dict.get((method, path), handle_404)
                                try:
                                    status, headers, body = handler_func(req_dict)
                                    response = build_response(status, headers, body)
                                except Exception:
                                    traceback.print_exc()
                                    err_resp = build_response(500, {"Content-Type": "text/plain; charset=utf-8", "Connection": "close"}, b"Internal Server Error")
                                    conn.send(err_resp)
                                    conn.close(sel)
                                    break

                                if not conn.send(response):
                                    conn.close(sel)
                                    break
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
    finally:
        shutdown_server(sel, server_socket)
# Is this optimal tho , everything is in a single loop
def main():
    run_server(HOST, PORT)

if __name__ == "__main__":
    main()
