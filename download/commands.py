from dataclasses import dataclass
import logging
import gzip
from tqdm import tqdm

from . import varint
from .connection import SerialConnection

from . import packets, utils, vex

logger = logging.getLogger(__name__)

COLD_START = 0x3800000
HOT_START = 0x7800000
CHUNK_SIZE = 4096


@dataclass
class LinkedFile:
    file_name: str
    vendor: vex.FileVendor


# Rewrite window_size with receive_payload


def upload_program(
    connection: SerialConnection,
    *,
    slot: int,
    name: str,
    description: str,
    program_type: str,
    icon: str,
    compress: bool,
    program_data: bytes,
    library_data: bytes | None,
    project_hash: str | None,
    after_upload: vex.FileExitAction,
):
    """Uploads a program to the device, including an ini file, the program binary, and optionally a library binary. If library_data is provided, the program will be linked to the library using a LinkFilePacket after the ini file is uploaded. If compress is True, the program and library data will be compressed using gzip before uploading."""
    base_file_name = f"slot_{slot}"

    ini_data = (
        f"[project]\n"
        f"ide={program_type}\n"
        f"[program]\n"
        f"name={name}\n"
        f"slot={slot-1}\n"
        f"icon={icon}\n"
        f"iconalt=\n"
        f"description={description}\n"
    ).encode()
    logger.info(f"Uploading {base_file_name}.ini")
    upload_file(
        connection,
        file_name=f"{base_file_name}.ini",
        file_type="ini",
        data=ini_data,
        load_addr=COLD_START,
        linked_file=None,
        after_upload=vex.FileExitAction.DO_NOTHING,
    )

    linked_file = None
    if library_data is not None:
        library_name = (
            f"{project_hash}.bin"
            if project_hash is not None
            else f"{base_file_name}_lib.bin"
        )
        linked_file = LinkedFile(library_name, vex.FileVendor.USER)
        upload_library(
            connection,
            library_name,
            library_data,
            compress,
            project_hash,
        )

    if compress:
        logger.info("Compressing program binary")
        program_data = gzip.compress(program_data)

    logger.info(f"Uploading program binary {base_file_name}.bin")
    upload_file(
        connection,
        file_name=f"{base_file_name}.bin",
        file_type="bin",
        data=program_data,
        load_addr=HOT_START,
        linked_file=linked_file,
        after_upload=after_upload,
    )


def upload_library(
    connection: SerialConnection,
    library_name: str,
    library_data: bytes,
    compress: bool,
    project_hash: str | None,
):
    if project_hash is not None:
        # Check if library name matches project hash
        metadata = packets.FileMetadataResponsePacket.from_payload(
            connection.packet_handshake(
                packets.GetFileMetadataPacket(
                    vendor=vex.FileVendor.USER,
                    reserved=0,
                    file_name=library_name,
                )
            )
        )
        if metadata is not None:
            logger.info("Library file found on device, skipping upload")
            return

    if compress:
        logger.info("Compressing library binary")
        library_data = gzip.compress(library_data)
        logger.info(f"Compressed library size: {len(library_data)} bytes")

    logger.info(f"Uploading cold library binary {library_name}")
    upload_file(
        connection,
        file_name=library_name,
        file_type="bin",
        data=library_data,
        load_addr=COLD_START,
        linked_file=None,
        after_upload=vex.FileExitAction.DO_NOTHING,
    )


def upload_file(
    connection: SerialConnection,
    *,
    file_name: str,
    file_type: str,
    data: bytes,
    load_addr: int,
    linked_file: LinkedFile | None,
    after_upload: vex.FileExitAction,
    vendor: vex.FileVendor = vex.FileVendor.USER,
    target: vex.FileTransferTarget = vex.FileTransferTarget.QSPI,
):
    """Uploads a file to the device using the file transfer protocol. If linked_file is provided, the file will be linked to the specified file after the ini file is uploaded. The after_upload parameter specifies what action to take after the upload is complete."""
    crc = utils.VEX_CRC_32.checksum(data)
    transfer_response = connection.packet_handshake(
        packets.InitFileTransferPacket(
            operation=vex.FileTransferOperation.WRITE,
            target=target,
            vendor=vendor,
            options=vex.FileTransferOptions.OVERWRITE,
            write_file_size=len(data),
            load_address=load_addr,
            write_file_crc=crc,
            metadata=packets.FileMetadata(
                extension=file_type,
                extension_type=vex.FileExtensionType.BINARY,
                timestamp=utils.j2000_timestamp(),
                version={
                    "major": 1,
                    "minor": 0,
                    "build": 0,
                    "beta": 0,
                },
            ),
            file_name=file_name,
        )
    )
    if linked_file is not None:
        connection.packet_handshake(
            packets.LinkFilePacket(
                vendor=linked_file.vendor,
                reserved=0,
                required_file=linked_file.file_name,
            )
        )

    is_wide = varint.is_wide(int.from_bytes(transfer_response[3:4]))
    start_idx = 6 + is_wide
    window_size = int.from_bytes(
        transfer_response[start_idx : start_idx + 2], byteorder="little"
    )

    # TODO: bluetooth is a lot more complicated
    max_chunk_size = min(window_size, CHUNK_SIZE)
    for i in tqdm(range(0, len(data), max_chunk_size)):
        chunk = data[i : i + max_chunk_size]
        if len(chunk) < max_chunk_size and len(chunk) % 4 != 0:
            chunk = bytearray(chunk)
            chunk.extend([0] * (4 - len(chunk) % 4))
        logger.debug(f"Sending chunk of size {len(chunk)}")
        connection.packet_handshake(
            packets.WriteFilePacket(address=load_addr + i, chunk_data=chunk)
        )
        # TODO: ble don't wait

    logger.info("Finalizing file transfer")
    connection.packet_handshake(
        packets.ExitFileTransferPacket(after_upload=after_upload)
    )
    logger.info(f"Successfully uploaded file {file_name}")
