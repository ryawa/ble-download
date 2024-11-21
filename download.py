import logging

from download import commands, packets
from download.connection import SerialConnection
from download.vex import FileExitAction, RadioChannel

logging.basicConfig(level=logging.DEBUG)


def main():
    connection = SerialConnection()
    if not hasattr(connection, "system_port"):
        logging.error("Connection failed")
        return

    with open("basic.bin", "rb") as file:
        program_data = file.read()

    connection.packet_handshake(packets.SetRadioChannelPacket(RadioChannel.PIT))
    commands.upload_program(
        connection,
        "squick",
        "A basic vexide program",
        "USER029x.bmp",
        "vexide",
        4,
        True,
        program_data,
        True,
        FileExitAction.SHOW_RUN_SCREEN,
    )


if __name__ == "__main__":
    main()
