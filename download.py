import logging

from download import commands, packets
from download.connection import SerialConnection
from download.vex import FileExitAction, RadioChannel

logging.basicConfig(level=logging.INFO)


def main():
    try:
        connection = SerialConnection()
    except Exception as e:
        logging.error(f"Failed to connect to device: {e}")
        raise

    with open("bin/hot.package.bin", "rb") as hot_binary:
        program_data = hot_binary.read()
    with open("bin/cold.package.bin", "rb") as cold_binary:
        library_data = cold_binary.read()

    connection.packet_handshake(
        packets.SetRadioChannelPacket(channel=RadioChannel.DOWNLOAD)
    )
    commands.upload_program(
        connection,
        slot=3,
        name="hotcold",
        description="A basic program uploaded through ble-download",
        program_type="ble-download",
        icon="USER029x.bmp",
        compress=True,
        program_data=program_data,
        library_data=library_data,
        after_upload=FileExitAction.SHOW_RUN_SCREEN,
    )


if __name__ == "__main__":
    main()
