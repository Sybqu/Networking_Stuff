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
Layer 2 — HTTP parsing (http_parser.py)                  DONE
Layer 3 — REST routing (routes_dict, handlers, builder)  DONE
Layer 4 — WS handshake (Upgrade detection, 101 response) DONE, verified against RFC 6455 known-good value
Layer 5 — WS frame parser/builder (opcodes, masking)     DONE
Layer 6 — Live broadcast over WS                         NEXT (currently echoes, not broadcasts)
TLS (HTTPS/WSS)                                          NOT STARTED
Media sharing (binary WS frames)                         NOT STARTED
Persistence                                              NOT STARTED (in-memory list only, deliberately)
```

### Files

- **`serv.py`** — owns all networking: dual-stack (IPv4/IPv6) socket setup via `getaddrinfo`, the `selectors`-based event loop, accepting connections, per-connection buffering, dispatching to either HTTP or WS handling based on a per-connection `mode` flag.
- **`http_parser.py`** — pure logic, no sockets. HTTP request parsing, response building, route handlers, the WS handshake math (SHA-1 + base64 of the `Sec-WebSocket-Key`), and the WS frame parser/builder.

### What's built and working

- **HTTP parsing**: Request-Line, headers, `Content-Length`-based body reading, completeness checks (returns `None` until a full request has arrived).
- **Response building**: Status-Line, headers, always-computed `Content-Length` — never hardcoded.
- **REST routing**: `(method, path)` → handler dict, GET/POST on `/` and `/messages`, 404 fallback.
- **WS handshake**: Detects `Upgrade: websocket`, computes `Sec-WebSocket-Accept` — verified byte-for-byte against the RFC 6455 example value.
- **WS framing**: Parses all three length encodings (6/8/14-byte headers), unmasks client payloads; builds unmasked server-to-client frames of any size. Handles close (`0x8`), ping (`0x9`)/pong (`0xA`), and currently echoes text/binary frames back to the sender.

### Immediate next steps

1. Verify the echo live against the JS test page.
2. Replace echo with real broadcast (reusing the `selectors.get_map()` relay pattern already proven in a standalone scratch demo).
3. Test with two browser tabs simultaneously.
4. Build out the test page into an actual chat UI.
5. Add TLS via Python's `ssl` module (wraps the existing socket — no change to parsing/routing logic underneath).
6. Media sharing via binary (`0x2`) WS frames, reusing the existing frame parser/builder unchanged.

### Deliberately not doing (for now)

- **No database** — an in-memory Python list (`fake_messages`) is the deliberate choice while proving the request/routing/broadcast pipeline. A local JSON file is the natural next step for persistence if needed later; a hosted DB (Supabase, etc.) is considered out of scope for a project about understanding every layer by hand.
- **No WSGI/ASGI framework compliance** — building the server itself, not a framework-compatible target.

---

## Shared concepts across both projects

- Raw socket lifecycle: `socket()` → `bind()` → `listen()` → `accept()` → `recv()`/`send()`.
- Multiplexing one thread across many connections (`poll()` in C, `selectors` in Python) instead of blocking or threading.
- Partial reads/writes are normal — TCP doesn't guarantee message boundaries, so both projects needed explicit buffering and "do I have a complete message yet?" checks.
- Protocol framing, solved twice independently: `\r\n\r\n` + `Content-Length` for HTTP, explicit length-prefixed binary frames for WebSocket — same underlying problem, different-layer solutions.
