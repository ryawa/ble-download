from hashlib import md5
import time
from base64 import b64encode

from crc import Calculator, Configuration, Crc16

VEX_CRC_16 = Calculator(Crc16.XMODEM.value)
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


def j2000_timestamp(timestamp: int | None = None) -> int:
    if timestamp is None:
        timestamp = int(time.time())
    return timestamp - 946684800


def project_hash(project_file: str) -> str:
    """Returns a base64-encoded md5 hash of the project file, which is used to determine if the program and library files on the device are up to date with the project file."""
    with open(project_file, "r") as f:
        data = f.read()
    return b64encode(md5(data.encode()).digest()).rstrip(b"=").decode("ascii")
