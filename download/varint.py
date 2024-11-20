def is_wide(x):
    return x > 127


def to_int(size_bytes):
    if is_wide(size_bytes[0]):
        return int.from_bytes([size_bytes[0] & 127, size_bytes[1]])
    else:
        return size_bytes[0]


def to_bytes(x):
    if is_wide(x):
        return bytes([x >> 8 | 0x80, x & 255])
    else:
        return bytes([x])
