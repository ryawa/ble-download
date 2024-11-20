from enum import IntEnum


class RadioChannel(IntEnum):
    PIT = 0x00
    DOWNLOAD = 0x01


class FileInitAction(IntEnum):
    WRITE = 1
    READ = 2


class FileDownloadTarget(IntEnum):
    DDR = 0
    QSPI = 1
    CBUF = 2
    VBUF = 3
    DDRC = 4
    DDRE = 5
    FLASH = 6
    RADIO = 7
    A1 = 13
    B1 = 14
    B2 = 15


class FileVendor(IntEnum):
    USER = 1
    SYS = 15
    DEV1 = 16
    DEV2 = 24
    DEV3 = 32
    DEV4 = 40
    DEV5 = 48
    DEV6 = 56
    VEX_VM = 64
    VEX = 240
    UNDEFINED = 241


class FileInitOption(IntEnum):
    NONE = 0
    OVERWRITE = 1


class FileExitAction(IntEnum):
    DO_NOTHING = 0
    RUN_PROGRAM = 1
    HALT = 2
    SHOW_RUN_SCREEN = 3
