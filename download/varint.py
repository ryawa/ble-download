def is_wide(x: int) -> bool:
    return x > (0xFF >> 1)


def to_int(size_bytes: bytes) -> int:
    if is_wide(size_bytes[0]):
        return int.from_bytes([size_bytes[0] & (0xFF >> 1), size_bytes[1]])
    else:
        return size_bytes[0]


def to_bytes(x: int) -> bytes:
    if is_wide(x):
        return bytes([x >> 8 | 0x80, x & 0xFF])
    else:
        return bytes([x])
