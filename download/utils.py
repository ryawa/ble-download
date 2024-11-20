import time

from crc import Calculator, Configuration, Crc16

VEX_CRC_16 = Calculator(Crc16.XMODEM)
VEX_CRC_32 = Calculator(
    Configuration(
        width=32,
        polynomial=0x04C11DB7,
        init_value=0x00000000,
        final_xor_value=0x00000000,
        reverse_input=False,
        reverse_output=False,
    )
)


def to_be_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, byteorder="big")


def to_le_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, byteorder="little")


def j2000_timestamp():
    return int(time.time()) - 946684800
