import logging

import serial.tools.list_ports

from . import packets, varint

logger = logging.getLogger(__name__)


class SerialConnection:
    """Manages the serial connection to the V5 Brain and provides methods for sending and receiving packets"""

    VEX_USB_VID = 0x2888
    V5_BRAIN_USB_PID = 0x0501
    V5_SERIAL_BAUDRATE = 115200

    def __init__(self):
        """Find V5 Brain USB ports and open serial connections to them"""
        ports = serial.tools.list_ports.comports()
        ports = filter(
            lambda p: p.vid == self.VEX_USB_VID and p.pid == self.V5_BRAIN_USB_PID,
            ports,
        )
        system_device = None
        user_device = None
        for port in ports:
            if port.device[-1] == "1":
                system_device = port.device
            elif port.device[-1] == "3":
                user_device = port.device
        if not system_device or not user_device:
            raise Exception("Could not find V5 Brain USB ports")
        self.system_port = serial.Serial(system_device, self.V5_SERIAL_BAUDRATE)
        self.user_port = serial.Serial(user_device, self.V5_SERIAL_BAUDRATE)

    def receive_packet(self) -> bytes:
        """Read a packet from the system port and return the raw bytes"""
        packet = bytearray()

        header = self.system_port.read(2)
        if header != packets.HOST_BOUND_HEADER:
            raise Exception("Received packet with invalid header")
        packet.extend(header)

        # Command ID
        packet.extend(self.system_port.read())

        size_bytes = bytearray()
        size_bytes.extend(self.system_port.read())
        if varint.is_wide(size_bytes[0]):
            size_bytes.extend(self.system_port.read())
        size = varint.to_int(size_bytes)
        packet.extend(size_bytes)

        packet.extend(self.system_port.read(size))

        logger.debug(f"Received packet: {packet.hex(" ")}")
        return packet

    def send_packet(self, packet: packets.Cdc2CommandPacket) -> None:
        """Send a packet to the system port"""
        self.system_port.write(packet.encode())
        self.system_port.flush()
        logger.debug(f"Sent packet: {packet.encode().hex(" ")}")

    def packet_handshake(self, packet: packets.Cdc2CommandPacket) -> bytes:
        """Send a packet and wait for a response"""
        self.send_packet(packet)
        return self.receive_packet()
