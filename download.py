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

    commands.upload_file(
        connection,
        "slot4",
        "ini",
        "[program]\ndescription = A test program.\nicon = USER029x.bmp\niconalt = \nslot = 4\nname = test\n[project]\nide = vexidebruh".encode(),
        0x3800000,
        None,
        FileExitAction.DO_NOTHING,
    )


if __name__ == "__main__":
    main()
