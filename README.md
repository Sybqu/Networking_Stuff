# Networking Projects — README

Two from-scratch networking builds, no frameworks, working through raw sockets in both C and Python.

---

## 1. C — Multi-client Chat Server (poll())

**What it is:** A multi-client TCP chat server in C, built from Beej's Guide to Network Programming, starting from raw `getaddrinfo`/`bind`/`listen`/`accept` fundamentals.

**Path taken:**
- Started as a single-client TCP echo/chat server (`recv`/`send` loop).
- Hit the classic blocking-I/O wall — couldn't type and receive at the same time on one thread.
- Learned `poll()` to multiplex many sockets on one thread, no threading needed.
- Rebuilt into a real multi-client group chat server using `poll()`.

**Status:** On hold, minor cleanup left. Working multi-client chat over `poll()`.

**Possible next steps considered:**
- Wrapping this in a WebSocket-capable evolution (superseded for now by the Python WS build below, which reached that milestone first).
- Packaging as a mobile app with a separate client (Flutter considered) once the protocol's stable.
- Was tunneling around mobile hotspot CGNAT with `bore` for testing with others; moved dev environment from Kali to NixOS mid-project.

---

## 2. Python — Raw-Socket HTTP + WebSocket Server

**What it is:** An HTTP/1.1 server and WebSocket implementation built entirely from Python's `socket`/`selectors` modules — no `http.server`, no Flask, no frameworks. Goal: a browser-based chat app with media sharing, understanding every layer by hand.

### Architecture

```
Layer 1 — sockets/selectors (accept, poll loop)          DONE
Layer 2 — HTTP parsing (http_parser.py)                  DONE (RFC 9112 strict framing + guardrails)
Layer 3 — REST routing (routes_dict, handlers, builder)  DONE
Layer 4 — WS handshake (Upgrade detection, 101 response) DONE, verified against RFC 6455 known-good value
Layer 5 — WS frame parser/builder (opcodes, masking)     DONE
Layer 6 — Live broadcast over WS                         NEXT (currently echoes, not broadcasts)
TLS (HTTPS/WSS)                                          NOT STARTED
Media sharing (binary WS frames)                         NOT STARTED
Persistence                                              NOT STARTED (in-memory list only, deliberately)
```

### Files

- **`serv.py`** — owns all networking: dual-stack (IPv4/IPv6) socket setup via `getaddrinfo`, the `selectors`-based event loop, accepting connections, per-connection buffering, dispatching to either HTTP or WS handling based on a per-connection `mode` flag, crash isolation, and connection teardown.
- **`http_parser.py`** — pure logic, strictly no sockets. HTTP request parsing, RFC 9112 validation, response building with extended reason phrases, route handlers, the WS handshake math (SHA-1 + base64 of the `Sec-WebSocket-Key`), and the WS frame parser/builder.
- **`test_server.py`** — 12 end-to-end integration tests speaking raw wire TCP bytes against a running server.

### What's Built and Working (Fixed Guardrails)

- **Crash Isolation & Network Guards**:
  - `HttpError` exception carrying HTTP status codes for any protocol violations; `serv.py` returns the exact status response and closes only that socket.
  - Handler exception sandbox: catches `Exception` (never `BaseException`), logs the full traceback with `traceback.print_exc()`, answers `500 Internal Server Error`, and keeps the server alive for subsequent clients.
  - Send-error isolation: `BrokenPipeError`, `ConnectionResetError`, `BlockingIOError`, and `OSError` are trapped per connection and never crash the main event loop.
- **Strict RFC 9112 HTTP Parsing**:
  - **Header-Driven Body Framing**: Body consumption is driven by `Content-Length`, allowing `PUT`, `DELETE`, and `POST` to isolate payload bytes without stream corruption.
  - **Pipelining Drain Loop**: The server loop uses a `while True` drain to process multiple requests packed into a single `recv()` buffer without stalling.
  - **Whitespace Guard**: Rejects field-lines with whitespace between field-name and colon with `400 Bad Request` (RFC 9112 §5.1 request smuggling guard).
  - **Duplicate Header Guard**: Rejects duplicate `Content-Length` headers with `400 Bad Request` (RFC 9112 §6.3.5).
  - **Digit-Only Validation**: `Content-Length` is validated for ASCII digits only (rejecting signs like `+5`, negative `-5`, underscores `1_0`, or alpha strings `abc`).
  - **Transfer-Encoding Rejection**: Explicitly rejects `Transfer-Encoding` with `501 Not Implemented`.
  - **Empty Body Default**: Requests with no `Content-Length` default to an empty body `b""` (RFC 9112 §6.3), preventing `KeyError` crashes in handlers.
  - **Extended Reason Phrases**: Includes 400, 404, 405, 411, 413, 431, 500, 501, 101, 200, 201.
- **WebSocket Handshake & Framing**:
  - Detects `Upgrade: websocket`, computes `Sec-WebSocket-Accept` — verified byte-for-byte against the RFC 6455 example value.
  - Parses all three length encodings (6/8/14-byte headers), unmasks client payloads; builds unmasked server-to-client frames of any size. Handles close (`0x8`), ping (`0x9`)/pong (`0xA`), and echoes text/binary frames.

---

### What Is Deliberately Out of Scope / Not Fixed Yet

- **OOP Refactoring**: Kept as pure functions and procedural dictionary data structures (`http_dict`, `conn["buffer"]`). Refactoring into `Request`, `Response`, and `Router` classes is scheduled for the next phase.
- **Non-blocking Write Queueing**: `client_sock.sendall()` can still block if kernel socket buffers are completely full under heavy throughput. A production event loop registers `EVENT_WRITE` to drain outbound response buffers asynchronously.
- **Chunked Transfer-Encoding**: The server currently rejects chunked transfer with 501 rather than de-chunking it.
- **Unbounded Header Protection**: No max buffer length (e.g. 8KB limit) is enforced while searching for `\r\n\r\n`. A client sending infinite bytes without `\r\n\r\n` would grow memory until exhausted (`431 Request Header Fields Too Large`).
- **WebSocket Broadcast**: Server still echoes back to the sender rather than broadcasting across `sel.get_map()` to all active WS connections.
- **Server Stdin Broadcast**: Commented out / shelved for future admin tooling.
- **Database / Persistence**: Kept as an in-memory list (`fake_messages`).

---

### Running the Test Suite

Run the 12 raw-socket integration tests from the project directory:

```bash
python -m unittest test_server.py
```

Tests cover:
1. Two pipelined requests in one send -> two distinct responses.
2. Slow drip: request sent one byte at a time -> one correct response.
3. Header line with no colon -> 400 response, server remains alive for new connections.
4. `"Host : x"` (space before colon) -> 400 response.
5. Duplicate `Content-Length` headers -> 400 response.
6. Malformed `Content-Length` (`-5`, `abc`, `1_0`, `+5`) -> 400 response.
7. `Transfer-Encoding` present -> 501 response.
8. `PUT`/`DELETE` with `Content-Length` followed by pipelined `GET` -> both handled, body isolated.
9. `POST` with no `Content-Length` -> empty body handled cleanly without crashing.
10. Handler raising an unhandled exception -> 500 response, server remains alive.
11. Missing template file (`index.html`) -> 500 response, server remains alive.
12. Abrupt client disconnect mid-response -> send error trapped, server remains alive.
