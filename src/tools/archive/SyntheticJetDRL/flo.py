import struct

def ReadFloat(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!f',y_bytes)[0]
    y = round(y,6)
    return y

def WriteFloat(value,reverse=False):
    y_bytes = struct.pack('!f',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

def ReadDint(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!i',y_bytes)[0]
    return y

def WriteDint(value,reverse=False):
    y_bytes = struct.pack('!i',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

if __name__ == "__main__":
    print(ReadFloat((15729,16458)))
    print(WriteFloat(26))
    print(ReadDint((1734,6970)))
    print(WriteDint(456787654))
