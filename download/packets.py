from collections.abc import Mapping
from dataclasses import dataclass
import struct

from . import utils, varint, vex

DEVICE_BOUND_HEADER = bytes([0xC9, 0x36, 0xB8, 0x47])
HOST_BOUND_HEADER = bytes([0xAA, 0x55])


class Cdc2CommandPacket:
    ID = 0x56
    EXT_ID: int
    payload: bytearray

    def __init__(self):
        self.header = DEVICE_BOUND_HEADER
        self.crc = utils.VEX_CRC_16

    def encode(self):
        encoded = bytearray()
        encoded.extend(self.header)
        encoded.extend([self.ID])
        encoded.extend([self.EXT_ID])
        payload_size = varint.to_bytes(len(self.payload))
        encoded.extend(payload_size)
        encoded.extend(self.payload)
        encoded.extend(self.crc.checksum(encoded).to_bytes(2, byteorder="big"))
        return encoded


class Cdc2ResponsePacket:
    pass


class SetRadioChannelPacket(Cdc2CommandPacket):
    EXT_ID = 0x10

    def __init__(self, *, channel: vex.RadioChannel):
        super().__init__()
        self.payload = bytearray()
        # Radio file control group
        self.payload.extend(bytes([0x01]))
        self.payload.extend(bytes([channel]))


@dataclass
class FileMetadata:
    extension: str
    extension_type: vex.FileExtensionType
    timestamp: int
    version: Mapping[str, int]


class InitFileTransferPacket(Cdc2CommandPacket):
    EXT_ID = 0x11

    def __init__(
        self,
        *,
        operation: vex.FileTransferOperation,
        target: vex.FileTransferTarget,
        vendor: vex.FileVendor,
        options: vex.FileTransferOptions,
        write_file_size: int,
        load_address: int,
        write_file_crc: int,
        metadata: FileMetadata,
        file_name: str,
    ):
        super().__init__()
        self.payload = bytearray()
        self.payload.extend(
            [
                operation,
                target,
                vendor,
                options,
            ]
        )
        self.payload.extend(write_file_size.to_bytes(4, byteorder="little"))
        self.payload.extend(load_address.to_bytes(4, byteorder="little"))
        self.payload.extend(write_file_crc.to_bytes(4, byteorder="little"))
        self.payload.extend(struct.pack("3s", metadata.extension.encode()))
        self.payload.extend([metadata.extension_type])
        self.payload.extend(
            metadata.timestamp.to_bytes(4, byteorder="little", signed=True)
        )
        self.payload.extend(
            bytes(
                [
                    metadata.version["major"],
                    metadata.version["minor"],
                    metadata.version["build"],
                    metadata.version["beta"],
                ]
            )
        )
        self.payload.extend(struct.pack("23sx", file_name.encode()))


class LinkFilePacket(Cdc2CommandPacket):
    EXT_ID = 0x15

    def __init__(self, *, vendor: vex.FileVendor, reserved: int, required_file: str):
        super().__init__()
        self.payload = bytearray()
        self.payload.extend([vendor, reserved])
        self.payload.extend(struct.pack("23sx", required_file.encode()))


class WriteFilePacket(Cdc2CommandPacket):
    EXT_ID = 0x13

    def __init__(self, *, address: int, chunk_data: bytes):
        super().__init__()
        self.payload = bytearray()
        self.payload.extend(address.to_bytes(4, byteorder="little", signed=True))
        self.payload.extend(chunk_data)


class ExitFileTransferPacket(Cdc2CommandPacket):
    EXT_ID = 0x12

    def __init__(self, *, after_upload: vex.FileExitAction):
        super().__init__()
        self.payload = bytearray([after_upload])
