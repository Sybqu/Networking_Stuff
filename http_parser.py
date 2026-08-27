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


def handle_index(req_dict : dict):
    with open("index.html", "rb") as f:
        body = f.read()
    return 200, {"Content-Type": "text/html"}, body


def handle_get_messages(req_dict : dict):
    body = "\n".join(fake_messages).encode()
    return 200, {"Content-Type": "text/plain"}, body


def handle_post_messages(req_dict : dict):
    fake_messages.append(req["body"].decode())
    return 201, {}, b"message received"

def handle_404(req_dict : dict):
    return 404, {"Content-Type": "text/plain"}, b"not found"

def build_response(status,headers,body):
    status_phrases = {
        200: "OK",
        201: "Created",
        404: "Not Found",
        500: "Internal Server Error",
        101: "Switching Protocols"
    }
    phrase = status_phrases.get(status,"unknown")
    response_line = f"HTTP/1.1 {status},{phrase}\r\n"
    headers = dict(headers)
    headers["Content-Length"] = str(len(body))
    response_line = f"HTTP/1.1 {status} {phrase}\r\n"
    headers_line="".join(f"{k}: {v}\r\n" for k,v in headers.items())
    return (response_line + headers_line + "\r\n").encode() + body

def is_ws(req_dict : dict):
    if req_dict["method"] == b"GET":
        upg_val = req_dict["headers"].get(b"Upgrade",b"")
        if upg_val.lower() == b"websocket":
            return True
    return False  

def ws_upgrade(req_dict: dict):
    sec_ws_key = req_dict["headers"].get(b"Sec-WebSocket-Key", b"")
    GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = sec_ws_key + GUID
    sha1_hash = hashlib.sha1(combined).digest()
    accept_str = base64.b64encode(sha1_hash).decode('utf-8')
    body = b""
    return 101, {"Upgrade": "websocket", "Connection": "Upgrade", "Sec-WebSocket-Accept": accept_str}, body

import random

def generate_adventurer():
    names = [
        "Kael", "Mira", "Zorin", "Vexa", "Borin",
        "Nyx", "Ragnar", "Lumi", "Drax", "Sera"
    ]

    classes = [
        "Engineer", "Wizard", "Rogue",
        "Berserker", "Alchemist", "Goblin Accountant"
    ]

    weapons = [
        "Rusty Sword", "Overclocked Laptop",
        "Ancient Spear", "Suspicious Stick",
        "Plasma Wrench", "Emotional Support Rock"
    ]

    quests = [
        "Defeat the dungeon boss",
        "Find the missing sandwich",
        "Debug the ancient machine",
        "Rescue the village chickens",
        "Steal the wizard's Wi-Fi password",
        "Figure out what that noise was"
    ]

    name = random.choice(names)
    player_class = random.choice(classes)
    weapon = random.choice(weapons)

    level = random.randint(1, 50)
    strength = random.randint(5, 100)
    intelligence = random.randint(5, 100)
    agility = random.randint(5, 100)
    luck = random.randint(1, 100)

    health = 100 + strength * 2
    mana = 50 + intelligence
    gold = random.randint(10, 5000)

    inventory = random.sample(
        weapons + [
            "Potion", "Bread", "Broken Compass",
            "Mysterious Key", "Three Rocks",
            "Expired Cheese", "USB Drive"
        ],
        k=5
    )

    active_quests = random.sample(quests, k=3)

    power_score = (
        strength * 0.35 +
        intelligence * 0.30 +
        agility * 0.20 +
        luck * 0.15
    )

    if power_score >= 80:
        rank = "ABSOLUTE UNIT"
    elif power_score >= 60:
        rank = "Elite"
    elif power_score >= 40:
        rank = "Competent"
    elif power_score >= 20:
        rank = "Questionable"
    else:
        rank = "Please Run"

    print("\n===== ADVENTURER PROFILE =====")
    print(f"Name:       {name}")
    print(f"Class:      {player_class}")
    print(f"Level:      {level}")
    print(f"Rank:       {rank}")
    print(f"Weapon:     {weapon}")
    print(f"Health:     {health}")
    print(f"Mana:       {mana}")
    print(f"Gold:       {gold} coins")
    print(f"Power:      {power_score:.1f}")
    print("\n--- STATS ---")
    print(f"Strength:   {strength}")
    print(f"Intellect:  {intelligence}")
    print(f"Agility:    {agility}")
    print(f"Luck:       {luck}")

    print("\n--- INVENTORY ---")
    for item in inventory:
        print(f"- {item}")

    print("\n--- ACTIVE QUESTS ---")
    for i, quest in enumerate(active_quests, 1):
        print(f"{i}. {quest}")

    print("\nStatus:", random.choice([
        "Ready for battle.",
        "Probably should sleep.",
        "Hungry but operational.",
        "Questioning life choices.",
        "Dangerously overconfident."
    ]))

    return {
        "name": name,
        "class": player_class,
        "level": level,
        "rank": rank,
        "power": round(power_score, 1),
        "inventory": inventory,
        "quests": active_quests
    }

    


# INSERT WS FRAME PARSING MAKE JS TEST SCRIPT AND ALL SET??? FALLAHICY


## OOPS approach?











    


