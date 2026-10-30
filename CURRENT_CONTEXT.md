# Current Project Context & Architecture State

**Last Updated:** 2026-10-30  
**Repository:** [Networking_Stuff](https://github.com/Sybqu/Networking_Stuff)  
**Goal:** A high-performance, browser-based chat server with live WebSockets, built from first principles using Python's raw `socket` and `selectors` modules (no `http.server`, Flask, or external web frameworks).

---

## 1. Architectural Map & Completed Milestones

```text
[ Incoming TCP Bytes ]
       │
       ▼
serv.py (I/O & Concurrency Layer)
  ├── Dual-stack IPv4/IPv6 socket setup (getaddrinfo, port 0 ephemeral binding)
  ├── selectors.DefaultSelector non-blocking event loop
  ├── accept_connection: cleans up socket acceptance and instantiates Connection
  ├── Connection (OOP State Shell):
  │     ├── self.sock: OS socket handle
  │     ├── self.buffer: byte stream accumulation
  │     ├── self.mode: "http" | "ws"
  │     ├── append(chunk) / consume(count): buffer slicing
  │     ├── send(data) -> bool: centralized network error isolation (BrokenPipe, etc.)
  │     └── close(sel): safe selector unregistration followed by OS socket closure
  ├── HTTP Pipelining Drain Loop: drains all requests in buffer without dropping connections
  └── ws_broadcast: multi-client live frame distribution with disconnect isolation
       │
       ▼
http_parser.py (Pure Protocol Logic — No Sockets)
  ├── Strict RFC 9112 Framing & Smuggling Guards:
  │     ├── Rejects whitespace before header colon (400)
  │     ├── Header-driven body consumption (Content-Length driven, not method driven)
  │     ├── Rejects duplicate Content-Length headers (400)
  │     ├── ASCII digit validation for Content-Length (rejects +5, -5, 1_0, abc)
  │     ├── Content-Length digit cap (len <= 10, rejects >10 digits and >4300 digits CVE-2020-10735 DoS)
  │     ├── Header buffer bounds check: MAX_HEADER_SIZE = 8192 (431 Slowloris defense)
  │     └── Rejects Transfer-Encoding with 501 Not Implemented
  ├── REST Dispatch Table: routes_dict = {("GET", b"/"): handle_index, ...}
  ├── Extended Reason Phrases: 101, 200, 201, 400, 404, 405, 411, 413, 431, 500, 501
  └── RFC 6455 WebSocket Implementation:
        ├── ws_upgrade: SHA-1 + Base64 accept calculation (verified against RFC test vector)
        ├── ws_parse_frame: 7-bit, 16-bit, and 64-bit frame unmasking
        └── ws_build_frame: server-to-client frame construction
```

---

## 2. Invariants & Guardrails (DO NOT BREAK)

1. **Decoupled Error Domains:** Application logic exceptions in route handlers return `500 Internal Server Error` with `traceback.print_exc()` and keep the server alive. Network write exceptions (`BrokenPipeError`, `ConnectionResetError`, `BlockingIOError`, `OSError`) are trapped inside `Connection.send()` and never leak into the selector loop.
2. **Loop Control Flow in Pipelining:** Inside `serv.py`'s HTTP drain loop:
   ```python
   if not conn.send(response):
       conn.close(sel)
       break
   ```
   **Never** call `conn.close(sel)` or `break` unconditionally after a successful response. Doing so immediately kills pipelined requests (breaking Tests 1 and 8).
3. **Clean Teardown Order:** In `Connection.close(sel)`: Unregister from selector *first*, then close the OS socket. Catch `Exception` on unregister so a missing selector key never skips closing the OS socket.

---

## 3. Test Suite

The test suite runs 14 end-to-end wire tests against raw TCP sockets:
```bash
python -m unittest Networking_Stuff/test_server.py
```
**Current Status:** `Ran 14 tests ... OK` (100% passing).

---

## 4. Prioritized Roadmap

### Tier 0: Immediate Hardening (COMPLETED)
1. **`accept()` Guard (COMPLETED 2026-10-28):** Wrapped `server.accept()` in `try/except OSError` inside `accept_connection()` returning `(None, None)`, checked with `if not conn or not addr: continue` inside `run_server()`. Prevents `EMFILE` / `ECONNABORTED` from killing the listener.
2. **Header Buffer Limit (431) (COMPLETED 2026-10-30):** Enforced `MAX_HEADER_SIZE = 8192` in `http_handler()`. If `\r\n\r\n` is not encountered within that limit or if header boundary exceeds 8KB, raises `HttpError(431, "Limit Exceeded")`. Tested with slowloris and oversized header streams (Test 14).
3. **Content-Length Digit Cap (400) (COMPLETED 2026-10-30):** Validate `len(cl_val) <= 10` before `int(cl_val)` to prevent Python CVE-2020-10735 quadratic parsing DoS and unhandled `ValueError`. Tested with >10 digits and 5,000 digits (Test 6).

### Tier 1: Known Issues & Security (Deferred until public tunneling)
* Documented in [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md):
  * Idle timeouts & connection caps (`EMFILE` protection).
  * WebSocket `MASK` bit enforcement on client frames (RFC 6455 §5.1, code 1002).
  * `Origin` header validation against Cross-Site WebSocket Hijacking (CSWSH).
  * Non-blocking write queue (`EVENT_WRITE`) for slow clients.
  * Honoring `Connection: close`.

### Tier 2: Frontend & Feature Upgrades
1. **Frontend Chat UI in [`index.html`](./index.html):**
   * Connect via `const ws = new WebSocket("ws://" + location.host);`
   * Use `element.textContent` (never `innerHTML`) to prevent XSS.
   * Auto-scroll message feed and connection status pill.
2. **JSON Messaging & `Hub` Pattern:**
   * Structured payloads: `{"type": "chat", "user": "alice", "text": "hello"}`.
   * Central `Hub` class managing active WebSocket connections and broadcasting.
3. **Persistence:** SQLite for message history catch-up.
4. **Media Sharing:** Binary WebSocket frames (`opcode 0x2`).

---

## 5. File Layout

* `serv.py` — Networking, event loop, connection management.
* `http_parser.py` — Pure HTTP/WS protocol logic.
* `test_server.py` — Raw wire integration tests.
* `index.html` — Browser client.
* `KNOWN_ISSUES.md` — Security issues & CVE documentation.
* `.gitignore` — Ignores `__pycache__`, `.pyc`, and compiled C binaries.
