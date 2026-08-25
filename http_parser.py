fake_messages = ["Hello", "fake", "testing"]
import base64
import hashlib


def http_handler(request: bytes) -> dict | None:
    if b"\r\n\r\n" not in request:
        return None

    req = request.split(b"\r\n")
    meth, pth, ver = req[0].split()
    print(f"{meth} , {pth} , {ver}")

    http_dict = {}
    http_dict["method"] = meth.strip()
    http_dict["path"] = pth.strip()
    http_dict["version"] = ver.strip()
    headers_dict = {}

    # header parsing
    for line in req[1:]:
        if line == b"":
            break
        header, value = line.split(b": ", maxsplit=1)
        headers_dict[header.strip()] = value.strip()

    http_dict["headers"] = headers_dict

# WS HANDSHAKE

    # body parsing (POST)
    if http_dict["method"] == b"POST":
        if b"Content-Length" in http_dict["headers"]:
            body_len = int(http_dict["headers"][b"Content-Length"])
            _, body_post = request.split(b"\r\n\r\n", 1)

            if len(body_post) < body_len:
                return None  # body hasn't fully arrived yet — wait for more recv()

            http_dict["body"] = body_post[:body_len]

    return http_dict


def handle_index(req):
    with open("index.html", "rb") as f:
        body = f.read()
    return 200, {"Content-Type": "text/html"}, body


def handle_get_messages(req):
    body = "\n".join(fake_messages).encode()
    return 200, {"Content-Type": "text/plain"}, body


def handle_post_messages(req):
    fake_messages.append(req["body"].decode())
    return 201, {}, b"message received"

def handle_404(req):
    return 404, {"Content-Type": "text/plain"}, b"not found"

def build_response(status,headers,body):
    status_phrases = {
        200: "OK",
        201: "Created",
        404: "Not Found",
        500: "Internal Server Error"
    }
    phrase = status_phrases.get(status,"unknown")
    response_line = f"HTTP/1.1 {status},{phrase}\r\n"
    headers = dict(headers)
    headers["Content-Length"] = str(len(body))
    response_line = f"HTTP/1.1 {status},{phrase}\r\n"
    headers_line="".join(f"{k}:{v}" for k,v in headers.items())
    return (response_line + headers_line + "/r/n").encode + body

def is_ws(request: bytes):
    incoming_request = http_handler(request)
    if incoming_request["method"] == b"GET":
        upg_val = incoming_request["headers"].get(b"Upgrade",b"")
        if upg_val.lower() == b"websocket":
            return True
    return False  

def ws_upgrade(request: bytes):
    ws_req = http_handler(request)
    sec_ws_key = ws_req["headers"].get(b"Sec-WebSocket-Key",b"")
    GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = sec_ws_key + GUID 
    sha1_hash = hashlib.sha1(combined).digest()
    accept_bytes =  base64.b64encode(sha1_hash)
    accept_bytes.decode('utf-8')



## OOPS approach?











    


