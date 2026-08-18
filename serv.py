
def http_handler(request : bytes) -> dict | None :
    # print(f"data recieved = {data}")
    if b"\r\n\r\n" not in request:
            return None
    req = request.split(b"\r\n")
    print(req)
    meth , pth , ver = req[0].split()
    print(f"{meth} , {pth} , {ver}")
    
    http_dict={}
    http_dict["method"] = meth.strip()
    http_dict["path"] = pth.strip()
    http_dict["version"]=ver.strip()
    headers_dict ={} # hori particle se

   

    for line in req[1:]:
        if line == b"":
            break
        header , value = line.split(b": ",maxsplit=1)
        headers_dict[header.strip()]=value.strip()

    http_dict["Headers"] = headers_dict
    # print(http_dict)
    # print(headers_dict)    
    # print(req)
    # print(f"method : {method}, path :{path} ,HTTP-Version : {version}")
    
    return http_dict

