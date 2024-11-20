import logging

import serial.tools.list_ports

from . import packets, varint

logger = logging.getLogger(__name__)


class SerialConnection:
    VEX_USB_VID = 0x2888
    V5_BRAIN_USB_PID = 0x0501
    V5_SERIAL_BAUDRATE = 115200

    def __init__(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid != self.VEX_USB_VID:
                continue
            if port.pid == self.V5_BRAIN_USB_PID:
                match port.location[-1]:
                    case "0":
                        self.system_port = serial.Serial(
                            port.device, self.V5_SERIAL_BAUDRATE
                        )
                    case "2":
                        self.user_port = serial.Serial(
                            port.device, self.V5_SERIAL_BAUDRATE
                        )

    def receive_packet(self):
        packet = bytearray()
        header = self.system_port.read(2)
        if header != packets.HOST_BOUND_HEADER:
            logger.warning("Received packet with invalid header")
            return
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

    def send_packet(self, packet):
        self.system_port.write(packet.encode())
        self.system_port.flush()
        logger.debug(f"Sent packet: {packet.encode().hex(" ")}")

    # TODO: Receive packet needs poll?
    def packet_handshake(self, packet):
        self.send_packet(packet)
        return self.receive_packet()
