import logging

from download import commands, packets
from download.connection import SerialConnection
from download.vex import FileExitAction, RadioChannel

logging.basicConfig(level=logging.INFO)


def main():
    connection = SerialConnection()
    if not hasattr(connection, "system_port"):
        logging.error("Connection failed")
        return

    with open("bin/hot.package.bin", "rb") as hot_binary:
        program_data = hot_binary.read()
    with open("bin/cold.package.bin", "rb") as cold_binary:
        library_data = cold_binary.read()

    connection.packet_handshake(packets.SetRadioChannelPacket(RadioChannel.PIT))
    commands.upload_program(
        connection,
        "hotcold",
        "A basic program uploaded through ble-download",
        "USER029x.bmp",
        "ble-download",
        4,
        True,
        program_data,
        library_data,
        FileExitAction.SHOW_RUN_SCREEN,
    )


if __name__ == "__main__":
    main()
