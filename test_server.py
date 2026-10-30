import os
import socket
import struct
import sys
import threading
import time
import unittest

# Ensure Networking_Stuff is in sys.path and is current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

import serv


class TestRawSocketServer(unittest.TestCase):
    def setUp(self):
        self.stop_event = threading.Event()
        self.ready_event = threading.Event()
        self.server_thread = threading.Thread(
            target=serv.run_server,
            kwargs={
                "host": "127.0.0.1",
                "port": 0,
                "ready_event": self.ready_event,
                "stop_event": self.stop_event,
            },
            daemon=True,
        )
        self.server_thread.start()
        self.assertTrue(self.ready_event.wait(timeout=3.0), "Server failed to start in time")
        self.port = self.ready_event.port

    def tearDown(self):
        self.stop_event.set()
        self.server_thread.join(timeout=1.0)

    def connect_client(self, timeout=2.0):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("127.0.0.1", self.port))
        return s

    def read_all(self, s, timeout=1.0):
        s.settimeout(timeout)
        chunks = []
        while True:
            try:
                data = s.recv(4096)
                if not data:
                    break
                chunks.append(data)
            except (socket.timeout, OSError):
                break
        return b"".join(chunks)

    # 1. two pipelined requests in one send -> two responses
    def test_01_pipelined_requests(self):
        with self.connect_client() as s:
            req = (
                b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
                b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n"
            )
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertEqual(
                data.count(b"HTTP/1.1 200 OK"),
                2,
                f"Expected 2 HTTP 200 responses, got: {data!r}",
            )

    # 2. request sent one byte at a time -> one correct response
    def test_02_slow_drip_one_byte_at_a_time(self):
        with self.connect_client() as s:
            req = b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n"
            for b in req:
                s.sendall(bytes([b]))
                time.sleep(0.005)
            data = self.read_all(s, timeout=1.5)
            self.assertIn(b"HTTP/1.1 200 OK", data)
            self.assertIn(b"fake", data)

    # 3. header line with no colon -> 400, then server still serves a new client
    def test_03_header_line_with_no_colon(self):
        with self.connect_client() as s:
            req = b"GET /messages HTTP/1.1\r\nHostNoColonHere\r\n\r\n"
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"400", data, f"Expected 400 for missing colon, got: {data!r}")

        # Server must still be alive and serve a new client
        with self.connect_client() as s2:
            s2.sendall(b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n")
            data2 = self.read_all(s2, timeout=1.0)
            self.assertIn(b"HTTP/1.1 200 OK", data2)

    # 4. "Host : x" (space before colon) -> 400
    def test_04_space_before_colon(self):
        with self.connect_client() as s:
            req = b"GET /messages HTTP/1.1\r\nHost : localhost\r\n\r\n"
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"400", data, f"Expected 400 for space before colon, got: {data!r}")

    # 5. duplicate Content-Length headers -> 400
    def test_05_duplicate_content_length(self):
        with self.connect_client() as s:
            req = (
                b"POST /messages HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Content-Length: 5\r\n"
                b"Content-Length: 5\r\n"
                b"\r\n"
                b"hello"
            )
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"400", data, f"Expected 400 for duplicate Content-Length, got: {data!r}")

    # 6. Content-Length of -5, abc, 1_0, +5 -> 400
    def test_06_invalid_content_length_values(self):
        invalid_lengths = [b"-5", b"abc", b"1_0", b"+5"]
        for val in invalid_lengths:
            with self.subTest(val=val):
                with self.connect_client() as s:
                    req = (
                        b"POST /messages HTTP/1.1\r\n"
                        b"Host: localhost\r\n"
                        b"Content-Length: " + val + b"\r\n"
                        b"\r\n"
                        b"test"
                    )
                    s.sendall(req)
                    data = self.read_all(s, timeout=1.0)
                    self.assertIn(b"400", data, f"Expected 400 for Content-Length: {val!r}, got: {data!r}")

    # 7. Transfer-Encoding present -> 501
    def test_07_transfer_encoding_present(self):
        with self.connect_client() as s:
            req = (
                b"POST /messages HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Transfer-Encoding: chunked\r\n"
                b"\r\n"
                b"5\r\nhello\r\n0\r\n\r\n"
            )
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"501", data, f"Expected 501 for Transfer-Encoding, got: {data!r}")

    # 8. DELETE/PUT with Content-Length and a body followed by a pipelined GET ->
    #    both handled, body not parsed as the next request
    def test_08_delete_put_with_body_pipelined_get(self):
        with self.connect_client() as s:
            req = (
                b"PUT /messages HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Content-Length: 4\r\n"
                b"\r\n"
                b"test"
                b"GET /messages HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"\r\n"
            )
            s.sendall(req)
            data = self.read_all(s, timeout=1.5)
            # Both requests must be responded to, and GET /messages must return 200 OK
            self.assertIn(b"HTTP/1.1 200 OK", data, f"Expected GET /messages 200 in response, got: {data!r}")
            # Ensure the PUT response is present (e.g. 404 or other valid HTTP status)
            self.assertGreaterEqual(data.count(b"HTTP/1.1 "), 2, f"Expected 2 responses, got: {data!r}")

    # 9. POST with no Content-Length -> treated as empty body (RFC 9112 s6.3), handler must not crash
    def test_09_post_with_no_content_length(self):
        with self.connect_client() as s:
            req = (
                b"POST /messages HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"\r\n"
            )
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"HTTP/1.1 201 Created", data, f"Expected 201 Created, got: {data!r}")

    # 10. handler raises -> 500, server alive
    def test_10_handler_raises(self):
        def explode_handler(req_dict):
            raise RuntimeError("Handler explosive failure!")

        serv.routes_dict[("GET", b"/explode")] = explode_handler
        try:
            with self.connect_client() as s:
                s.sendall(b"GET /explode HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data = self.read_all(s, timeout=1.0)
                self.assertIn(b"500", data, f"Expected 500 for exploding handler, got: {data!r}")

            # Server must still be alive
            with self.connect_client() as s2:
                s2.sendall(b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data2 = self.read_all(s2, timeout=1.0)
                self.assertIn(b"HTTP/1.1 200 OK", data2)
        finally:
            serv.routes_dict.pop(("GET", b"/explode"), None)

    # 11. index.html missing -> 500, server alive
    def test_11_index_html_missing(self):
        index_path = os.path.join(BASE_DIR, "index.html")
        backup_path = os.path.join(BASE_DIR, "index.html.testing_backup")
        if os.path.exists(index_path):
            os.rename(index_path, backup_path)
        try:
            with self.connect_client() as s:
                s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data = self.read_all(s, timeout=1.0)
                self.assertIn(b"500", data, f"Expected 500 when index.html is missing, got: {data!r}")

            # Server must still be alive
            with self.connect_client() as s2:
                s2.sendall(b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n")
                data2 = self.read_all(s2, timeout=1.0)
                self.assertIn(b"HTTP/1.1 200 OK", data2)
        finally:
            if os.path.exists(backup_path):
                os.rename(backup_path, index_path)

    # 12. client disconnects mid-response -> server alive
    def test_12_client_disconnects_mid_response(self):
        s = self.connect_client()
        # Enable SO_LINGER with timeout 0 to force an immediate TCP RST upon close
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        s.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        # Abruptly close mid-conversation
        s.close()

        time.sleep(0.1)

        # Server must still be alive and accept new connections
        with self.connect_client() as s2:
            s2.sendall(b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n")
            data2 = self.read_all(s2, timeout=1.0)
            self.assertIn(b"HTTP/1.1 200 OK", data2)

    # 13. WebSocket broadcast: frame sent from Client 1 is received by Client 2
    def test_13_websocket_broadcast(self):
        s1 = self.connect_client()
        s2 = self.connect_client()
        try:
            # Upgrade Client 1
            s1.sendall(
                b"GET / HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n"
                b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                b"\r\n"
            )
            resp1 = self.read_all(s1, timeout=0.5)
            self.assertIn(b"101 Switching Protocols", resp1)

            # Upgrade Client 2
            s2.sendall(
                b"GET / HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n"
                b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                b"\r\n"
            )
            resp2 = self.read_all(s2, timeout=0.5)
            self.assertIn(b"101 Switching Protocols", resp2)

            # Client 1 sends masked text frame: "hello everyone"
            payload = b"hello everyone"
            mask_key = b"1234"
            masked_payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
            client_frame = bytes([0x81, 0x80 | len(payload)]) + mask_key + masked_payload
            s1.sendall(client_frame)

            # Client 2 should receive the broadcasted server frame
            data = s2.recv(4096)
            self.assertIn(b"hello everyone", data)
        finally:
            s1.close()
            s2.close()

    # 14. header fields too large (> 8192) -> 431, server alive
    def test_14_header_fields_too_large(self):
        # Case A: Unterminated slowloris flood (> 8192 bytes with no \r\n\r\n)
        with self.connect_client() as s:
            req = b"GET / HTTP/1.1\r\nX-Junk: " + (b"A" * 9000)
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"431", data, f"Expected 431 for unterminated header flood, got: {data!r}")

        # Case B: Terminated header exceeding limit
        with self.connect_client() as s:
            req = b"GET / HTTP/1.1\r\nHost: localhost\r\nX-Long: " + (b"B" * 9000) + b"\r\n\r\n"
            s.sendall(req)
            data = self.read_all(s, timeout=1.0)
            self.assertIn(b"431", data, f"Expected 431 for oversized header, got: {data!r}")

        # Server must still be alive
        with self.connect_client() as s2:
            s2.sendall(b"GET /messages HTTP/1.1\r\nHost: localhost\r\n\r\n")
            data2 = self.read_all(s2, timeout=1.0)
            self.assertIn(b"HTTP/1.1 200 OK", data2)


if __name__ == "__main__":
    unittest.main()
