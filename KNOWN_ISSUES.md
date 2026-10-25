# Known Issues & Security Hardening Roadmap

This document outlines architectural limitations, protocol edge cases, and known security exposure areas in this from-scratch HTTP/1.1 and WebSocket server.

> **Operational Rule:** *Hardening gates exposure, not local development.*  
> While these issues do not impact offline testing or localhost experimentation, all Tier 1 items must be addressed before exposing this service to public interfaces (e.g., via `bore`, ngrok, or production deployment).

---

## 1. High & Critical Protocol Vulnerabilities

### 1.1 Unbounded Header Buffering — Slowloris / Memory Exhaustion (CWE-400)
* **Status:** Open (Tier 1)
* **Risk:** High (Denial of Service)
* **Description:** In `serv.py`, incoming chunks are continuously appended to `conn.buffer` until the sequence `\r\n\r\n` is detected. A malicious client can drip single header bytes infinitely without ever sending `\r\n\r\n`, consuming server memory until the process is killed by the OS kernel OOM-killer.
* **Remediation:** Enforce a maximum header size limit (e.g., 8KB / 16KB). If `b"\r\n\r\n"` is not found within this threshold, immediately terminate the connection with `431 Request Header Fields Too Large`.

### 1.2 Integer String Conversion DoS — CVE-2020-10735
* **Status:** Open (Tier 0 / Tier 1)
* **Risk:** Medium / High (Process Crash / CPU Exhaustion)
* **Description:** RFC 9112 §6.3 specifies that `Content-Length` contains digits. However, an attacker providing 5,000+ digits (e.g., `Content-Length: 1111...`) can trigger Python's quadratic integer parsing limit (CVE-2020-10735), which raises an unhandled `ValueError: Exceeds the limit (4300 digits) for integer string conversion`.
* **Remediation:** Validate that `len(cl_val) <= 10` (max ~10GB value) prior to converting via `int(cl_val)`. Return `400 Bad Request` or `413 Payload Too Large` if length is exceeded.

### 1.3 Cross-Site WebSocket Hijacking (CSWSH)
* **Status:** Open (Tier 1)
* **Risk:** High (Unauthorized Actions in Browsers)
* **Description:** The WebSocket handshake in `http_parser.py` validates `Sec-WebSocket-Key` but does not inspect or validate the `Origin` header. An attacker on an external malicious site (`evil.com`) can initiate a WebSocket connection from the victim's browser to `ws://localhost:3490` and hijack authenticated sessions.
* **Remediation:** Enforce an allowlist of trusted origins against `req_dict["headers"].get(b"origin")`. Reject untrusted origins with `403 Forbidden` prior to switching protocols.

### 1.4 Unmasked Client WebSocket Frame Injection — RFC 6455 §5.1
* **Status:** Open (Tier 1)
* **Risk:** Medium (Cache Poisoning / Protocol Smuggling)
* **Description:** RFC 6455 §5.1 explicitly mandates that all frames sent from a client to a server must be masked (`MASK` bit = 1). If an unmasked frame is received, the server MUST close the connection with status code 1002 (Protocol Error).
* **Remediation:** In `ws_parse_frame()`, verify `MASK_bit == 1`. If `0`, immediately abort and send close frame `0x8` with code `1002`.

---

## 2. Resource & Connection Lifecycle Constraints

### 2.1 Synchronous Outbound Write Blocking (`sendall` Backpressure)
* **Status:** Open (Tier 1 / Tier 2)
* **Risk:** High under real traffic (Starvation of all clients)
* **Description:** Sockets are marked non-blocking for reads, but responses are pushed using synchronous `sendall()`. If a client has a small TCP receive window or experiences high latency, `sendall()` blocks the entire selector thread.
* **Remediation:** Introduce an outbound write queue (`conn.out_buffer`) and register `selectors.EVENT_WRITE` to drain bytes incrementally as the kernel buffer clears.

### 2.2 Lack of Idle Timeouts & Connection Caps (CWE-400)
* **Status:** Open (Tier 1)
* **Risk:** Medium (File Descriptor Exhaustion)
* **Description:** Connections remain open indefinitely until the client closes them. A small botnet opening 1,000 idle TCP connections without sending data will exhaust the server's file descriptor limit (`EMFILE`).
* **Remediation:** Track `last_active_timestamp` on `Connection`, enforce an idle timeout (e.g., 60 seconds), and place a hard limit on total concurrent active connections (e.g., 512).

### 2.3 Honoring `Connection: close`
* **Status:** Open (Tier 1)
* **Risk:** Low (RFC Compliance)
* **Description:** If a client explicitly sends `Connection: close`, the server currently leaves the TCP socket open for pipelining instead of closing after the response is transmitted.
* **Remediation:** Check `req_dict["headers"].get(b"connection") == b"close"` and trigger `conn.close(sel)` after sending.

### 2.4 In-Memory Unbounded Message Storage (`fake_messages`)
* **Status:** Open (Tier 1)
* **Risk:** Medium (RAM Exhaustion)
* **Description:** `handle_post_messages` appends incoming message bodies to a Python list `fake_messages` without bounds or payload size caps.
* **Remediation:** Enforce payload size limit (e.g. 64KB) and cap maximum messages in memory or transition to SQLite.
