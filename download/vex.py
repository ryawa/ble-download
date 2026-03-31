from enum import IntEnum


class RadioChannel(IntEnum):
    PIT = 0x00
    DOWNLOAD = 0x01


class FileTransferOperation(IntEnum):
    WRITE = 0x01
    READ = 0x02


class FileTransferTarget(IntEnum):
    DDR = 0x00
    QSPI = 0x01
    CBUF = 0x02
    VBUF = 0x03
    DDRC = 0x04
    DDRE = 0x05
    FLASH = 0x06
    RADIO = 0x07
    A1 = 0x0D
    B1 = 0x0E
    B2 = 0x0F


class FileVendor(IntEnum):
    USER = 0x01
    SYS = 0x0F
    DEV1 = 0x10
    DEV2 = 0x18
    DEV3 = 0x20
    DEV4 = 0x28
    DEV5 = 0x30
    DEV6 = 0x38
    VEX_VM = 0x40
    VEX = 0xF0
    UNDEFINED = 0xF1


class FileTransferOptions(IntEnum):
    NONE = 0x00
    OVERWRITE = 0x01


class FileExitAction(IntEnum):
    DO_NOTHING = 0x00
    RUN_PROGRAM = 0x01
    HALT = 0x02
    SHOW_RUN_SCREEN = 0x03


class FileExtensionType(IntEnum):
    BINARY = 0x00
    VM = 0x61
    ENCRYPTED_BINARY = 0x73
    ZIPPED = 0x7A
