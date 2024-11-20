import logging
import zlib

from download import varint

from . import packets, utils, vex

logger = logging.getLogger(__name__)

COLD_START = 0x3800000


def upload_program(connection, name, description, icon, program_type, slot, compress_program, data, is_monolith, after_upload):
    logger.info("Uploading program ini file")
    base_filename = f"slot_{slot}"
    ini_data = (
        f"[program]\n"
        f"description = {description}\n"
        f"icon = {icon}\n"
        f"iconalt = \n"
        f"slot = {slot}\n"
        f"name = {name}\n"
        f"\n"
        f"[project]\n"
        f"ide = {program_type}\n"
    )
    upload_file(f"{base_filename}.ini", "ini", ini_data, COLD_START, None, vex.FileExitAction.DO_NOTHING)
    bin_name = f"{base_filename}.bin"
    lib_name = f"{base_filename}_lib.bin"

    if is_monolith:
        program_data = data
        library_data = None
    
    # TODO: hot/cold library

    logger.info("Uploading program binary")
    # TODO: streaming gzip
    if compress_program:
        program_data = zlib.compress(program_data)
    upload_file(bin_name, "bin", None, program_data, None, COLD_START, linked_file, after_upload)



def upload_file(
    connection,
    filename,
    filetype,
    data,
    load_addr,
    linked_file,
    after_upload,
    vendor=vex.FileVendor.USER,
    target=vex.FileDownloadTarget.QSPI,
):
    crc = utils.VEX_CRC_32.checksum(data)
    transfer_response = connection.packet_handshake(
        packets.InitFileTransferPacket(
            vex.FileInitAction.WRITE,
            target,
            vendor,
            vex.FileInitOption.OVERWRITE,
            len(data),
            load_addr,
            crc,
            filetype,
            utils.j2000_timestamp(),
            {
                "major": 1,
                "minor": 0,
                "build": 0,
                "beta": 0,
            },
            filename,
        )
    )
    if linked_file is not None:
        connection.packet_handshake(
            packets.LinkFilePacket(linked_file["vendor"], 0, linked_file["filename"])
        )
    payload_size = varint.to_int(transfer_response[3:5])
    is_wide = varint.is_wide(int.from_bytes(transfer_response[3:4]))
    start_idx = 6 + is_wide
    window_size = int.from_bytes(transfer_response[start_idx : start_idx + 2])
    logger.info(f"Window size: {window_size}")
    # TODO: bluetooth is a lot more complicated
    max_chunk_size = min(window_size, 4096)
    offset = 0
    for i in range(0, len(data), max_chunk_size):
        chunk = data[i : i + max_chunk_size]
        if len(chunk) < max_chunk_size and len(chunk) % 4 != 0:
            chunk = bytearray(chunk)
            chunk.extend([0] * (4 - len(chunk) % 4))
        logger.info(f"Sending chunk of size {len(chunk)}")
        connection.packet_handshake(packets.WriteFilePacket(load_addr + i, chunk))
        # TODO: ble don't wait
    connection.packet_handshake(packets.ExitFileTransferPacket(after_upload))
    logger.info(f"Successfully uploaded file {filename}")
