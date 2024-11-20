import logging

from download import commands
from download.connection import SerialConnection
from download.vex import FileExitAction

logging.basicConfig(level=logging.DEBUG)


def main():
    connection = SerialConnection()
    if not hasattr(connection, "system_port"):
        logging.error("Connection failed")
        return
    
    with open("basic.bin", "rb") as file:
        program_data = file.read()

    commands.upload_program(
        connection,
        "quick",
        "A basic vexide program",
        "USER029x.bmp",
        "vexide",
        4,
        True,
        program_data,
        True,
        FileExitAction.SHOW_RUN_SCREEN
    )


if __name__ == "__main__":
    main()
