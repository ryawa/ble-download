import struct

from . import utils, varint

DEVICE_BOUND_HEADER = bytes([0xC9, 0x36, 0xB8, 0x47])
HOST_BOUND_HEADER = bytes([0xAA, 0x55])


# TODO: use struct.pack
# TODO: separate command/reply packets


class Cdc2CommandPacket:
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
        encoded.extend(utils.to_be_bytes(self.crc.checksum(encoded)))
        return encoded


class SetRadioChannelPacket(Cdc2CommandPacket):
    ID = 86
    EXT_ID = 16

    def __init__(self, channel):
        super().__init__()
        self.payload = bytearray()
        # Radio file control group
        self.payload.extend(bytes([0x01]))
        self.payload.extend(bytes([channel]))


class InitFileTransferPacket(Cdc2CommandPacket):
    ID = 86
    EXT_ID = 17

    def __init__(
        self,
        operation,
        target,
        vendor,
        options,
        write_file_size,
        load_address,
        write_file_crc,
        file_extension,
        timestamp,
        version,
        filename,
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
        write_file_size += 1
        self.payload.extend(write_file_size.to_bytes(4, byteorder="little"))
        self.payload.extend(load_address.to_bytes(4, byteorder="little"))
        self.payload.extend(write_file_crc.to_bytes(4, byteorder="little"))
        self.payload.extend(struct.pack("3sx", file_extension.encode()))
        self.payload.extend(timestamp.to_bytes(4, byteorder="little"))
        self.payload.extend(
            bytes(
                [
                    version["major"],
                    version["minor"],
                    version["build"],
                    version["beta"],
                ]
            )
        )
        self.payload.extend(struct.pack("23sx", filename.encode()))


class LinkFilePacket(Cdc2CommandPacket):
    ID = 86
    EXT_ID = 21

    def __init__(self, vendor, option, required_file):
        super().__init__()
        self.payload = bytearray()
        self.payload.extend([vendor, option])
        self.payload.extend(required_file.encode())


class WriteFilePacket(Cdc2CommandPacket):
    ID = 86
    EXT_ID = 19

    def __init__(self, address, chunk_data):
        super().__init__()
        self.payload = bytearray()
        self.payload.extend(utils.to_le_bytes(address))
        self.payload.extend(chunk_data)


class ExitFileTransferPacket(Cdc2CommandPacket):
    ID = 86
    EXT_ID = 18

    def __init__(self, after_upload):
        super().__init__()
        self.payload = bytearray([after_upload])
