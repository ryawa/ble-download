import logging
import zlib

from download import varint

from . import packets, utils, vex

logger = logging.getLogger(__name__)

COLD_START = 0x3800000
HOT_START = 0x7800000
CHUNK_SIZE = 4096


# TODO: streaming gzip
def upload_program(
    connection,
    name,
    description,
    icon,
    program_type,
    slot,
    compress_program,
    program_data,
    library_data,
    after_upload,
):
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
    ).encode()
    upload_file(
        connection,
        f"{base_filename}.ini",
        "ini",
        ini_data,
        COLD_START,
        None,
        vex.FileExitAction.DO_NOTHING,
    )
    bin_name = f"{base_filename}.bin"
    lib_name = f"{base_filename}_lib.bin"

    is_monolith = library_data is None

    if not is_monolith:
        logger.info("Uploading cold library binary")
        if compress_program:
            library_data = zlib.compress(library_data)
        upload_file(
            connection,
            lib_name,
            "bin",
            library_data,
            HOT_START,
            None,
            # vex.FileExitAction.DO_NOTHING,
            after_upload,
        )

    logger.info("Uploading program binary")
    if compress_program:
        program_data = zlib.compress(program_data)
    if is_monolith:
        linked_file = None
    else:
        linked_file = {
            "filename": lib_name,
            "vendor": 0,
        }

    upload_file(
        connection,
        bin_name,
        "bin",
        program_data,
        COLD_START,
        linked_file,
        after_upload,
    )


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
    window_size = int.from_bytes(
        transfer_response[start_idx : start_idx + 2], byteorder="little"
    )
    logger.info(f"Window size: {window_size}")
    # TODO: bluetooth is a lot more complicated
    max_chunk_size = min(window_size, CHUNK_SIZE)
    offset = 0
    for i in range(0, len(data), max_chunk_size):
        chunk = data[i : i + max_chunk_size]
        if len(chunk) < max_chunk_size and len(chunk) % 4 != 0:
            chunk = bytearray(chunk)
            chunk.extend([0] * (4 - len(chunk) % 4))
        logger.debug(f"Sending chunk of size {len(chunk)}")
        connection.packet_handshake(packets.WriteFilePacket(load_addr + i, chunk))
        # TODO: ble don't wait
    connection.packet_handshake(packets.ExitFileTransferPacket(after_upload))
    logger.info(f"Successfully uploaded file {filename}")
