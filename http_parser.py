fake_messages = ["Hello", "fake", "testing"]
import base64
import hashlib
import struct

MAX_HEADER_SIZE = 8192

class HttpError(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def http_handler(request: bytes) -> dict | None:
    header_end_idx = request.find(b"\r\n\r\n")

    if header_end_idx == -1:
        if len(request)>MAX_HEADER_SIZE:
            raise HttpError(431,"Limit Exceeded")
        return None    
    if header_end_idx > MAX_HEADER_SIZE:
        raise HttpError(431,"Fields too large")    
    

    req = request.split(b"\r\n")
    header_end_idx = request.find(b"\r\n\r\n")
    req_len = header_end_idx+4

    if not req[0].strip():
        raise HttpError(400, "Empty request line")
    parts = req[0].split()
    if len(parts) != 3:
        raise HttpError(400, "Malformed request line")
    meth, pth, ver = parts
    print(f"{meth} , {pth} , {ver}")

    http_dict = {}
    http_dict["method"] = meth.strip()
    http_dict["path"] = pth.strip()
    http_dict["version"] = ver.strip()
    http_dict["body"] = b""  # default empty body (RFC 9112 s6.3)
    headers_dict = {}

# TCP is a continuous byte stream , improving partial requests / piplining
    # header parsing
    for line in req[1:]:
        if line == b"":
            break
        if b":" not in line:
            raise HttpError(400, "Header line missing colon")
        header, value = line.split(b":", maxsplit=1) # b": ".split() is bad what if the request contains ":" itself

        # RFC 9112 s5.1: No whitespace is allowed between the field name and colon
        if header.endswith(b" ") or header.endswith(b"\t"):
            raise HttpError(400, "Whitespace before colon in header field name")

        norm_key = header.lower().strip()
        # RFC 9112 s6.3: Reject duplicate Content-Length headers
        if norm_key == b"content-length" and norm_key in headers_dict:
            raise HttpError(400, "Duplicate Content-Length header")

        headers_dict[norm_key] = value.strip() # Header values are case sensitive
    http_dict["headers"] = headers_dict

    # RFC 9112: Reject Transfer-Encoding with 501 Not Implemented
    if b"transfer-encoding" in headers_dict:
        raise HttpError(501, "Transfer-Encoding not implemented")

    # Body framing driven by headers, not method
    if b"content-length" in headers_dict:
        cl_val = headers_dict[b"content-length"]
        # Content-Length must be ASCII digits only (reject -5, abc, 1_0, +5)
        if not cl_val or not cl_val.isdigit():
            raise HttpError(400, "Content-Length must contain only ASCII digits")

        body_len = int(cl_val)
        body_post = request[header_end_idx:]

        if len(body_post) < body_len:
            return None  # body hasn't fully arrived yet — wait for more recv()
        req_len += body_len

        http_dict["body"] = body_post[:body_len]

    http_dict["length"] = req_len        

    return http_dict


def handle_index(req_dict : dict):
    with open("index.html", "rb") as f:
        body = f.read()
    return 200, {"Content-Type": "text/html"}, body


def handle_get_messages(req_dict : dict):
    body = "\n".join(fake_messages).encode()
    return 200, {"Content-Type": "text/plain; charset=utf-8"}, body


def handle_post_messages(req_dict : dict):  
    fake_messages.append(req_dict["body"].decode())
    return 201, {}, b"message received"

def handle_404(req_dict : dict):
    return 404, {"Content-Type": "text/plain; charset=utf-8"}, b"not found"

def build_response(status,headers,body):
    status_phrases = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        411: "Length Required",
        413: "Payload Too Large",
        431: "Request Header Fields Too Large",
        500: "Internal Server Error",
        501: "Not Implemented",
        101: "Switching Protocols",
    }
    phrase = status_phrases.get(status,"unknown")
    response_line = f"HTTP/1.1 {status} {phrase}\r\n"
    headers = dict(headers)
    headers["Content-Length"] = str(len(body))
    headers_line="".join(f"{k}: {v}\r\n" for k,v in headers.items())
    return (response_line + headers_line + "\r\n").encode() + body

def is_ws(req_dict : dict):
    if req_dict["method"] == b"GET":
        upg_val = req_dict["headers"].get(b"upgrade",b"") # Convert Upgrade to lowercase , header look up + uniformity 
        if upg_val.lower() == b"websocket":
            return True
    return False  

def ws_upgrade(req_dict: dict):
    sec_ws_key = req_dict["headers"].get(b"sec-websocket-key", b"") # Same uniformity bug now fixed
    GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = sec_ws_key + GUID
    sha1_hash = hashlib.sha1(combined).digest()
    accept_str = base64.b64encode(sha1_hash).decode('utf-8')
    body = b""
    return 101, {"Upgrade": "websocket", "Connection": "Upgrade", "Sec-WebSocket-Accept": accept_str}, body


def ws_parse_frame(data: bytes) -> tuple[int, bytearray, int] | None:
    if len(data) < 2:
        return None  # not even the first 2 bytes yet

    byte0 = data[0]
    byte1 = data[1]

    FIN = (byte0 & 0b10000000) >> 7
    opcode = (byte0 & 0b00001111)

    MASK_bit = (byte1 & 0b10000000) >> 7
    payload_len = (byte1 & 0b01111111)

    if payload_len == 126:
        if len(data) < 4:
            return None  # extended length bytes haven't arrived yet
        actual_len = struct.unpack(">H", data[2:4])[0]
        mask_key = data[4:8]
        payload_start = 8

    elif payload_len == 127:
        if len(data) < 10:
            return None  # extended length bytes haven't arrived yet
        actual_len = struct.unpack(">Q", data[2:10])[0]
        mask_key = data[10:14]
        payload_start = 14

    else:
        actual_len = payload_len
        mask_key = data[2:6]
        payload_start = 6

    if len(data) < payload_start + actual_len:
        return None  # full payload hasn't arrived yet — wait for more recv()

    masked_payload = data[payload_start:payload_start + actual_len]

    unmasked = bytearray(len(masked_payload))
    for i in range(len(masked_payload)):
        unmasked[i] = masked_payload[i] ^ mask_key[i % 4]

    return (opcode, unmasked, payload_start + actual_len)

def ws_build_frame(opcode: int, payload: bytes) -> bytes:
    byte0 = (1 << 7) | opcode  # FIN=1, combined with opcode

    length = len(payload)

    if length <= 125:
        header = bytes([byte0, length])

    elif length <= 65535:
        header = bytes([byte0, 126]) + struct.pack(">H", length)

    else:
        header = bytes([byte0, 127]) + struct.pack(">Q", length)

    return header + payload







## OOPS approach?













