import logging

from download import varint

from . import packets, utils, vex


def upload_program(connection, **kwargs):
    pass


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
    logging.info(f"Window size: {window_size}")
    # TODO: bluetooth is a lot more complicated
    logging.debug(f"transfer response: {transfer_response}")
    max_chunk_size = min(window_size, 4096)
    offset = 0
    for i in range(0, len(data), max_chunk_size):
        chunk = data[i : i + max_chunk_size]
        if len(chunk) < max_chunk_size and len(chunk) % 4 != 0:
            chunk = bytearray(chunk)
            chunk.extend([0] * (4 - len(chunk) % 4))
        logging.info(f"Sending chunk of size {len(chunk)}")
