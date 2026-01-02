"""Main Renogy client for Modbus RTU communication.

This module provides the RenogyClient class for communicating with Renogy
solar devices via USB-to-RS485 adapters using the Modbus RTU protocol.

Reverse engineered from Renogy DC Home App v1.10.69
CRC algorithm source: ModBusUtils.java:917-941 method u(byte[] bytes)
"""

import logging
import struct
import time
from typing import Optional

import serial

from .exceptions import (
    CommunicationError,
    CRCError,
    DeviceNotFoundError,
    InvalidResponseError,
    ModbusError,
    TimeoutError,
    get_modbus_exception_message,
)
from .models import (
    BatteryData,
    ControllerData,
    DeviceInfo,
    LoadData,
    RenogyReading,
    SolarData,
)

logger = logging.getLogger(__name__)


# CRC-16/MODBUS lookup table (precomputed for polynomial 0xA001)
# Source: ModBusUtils.java:917-941 uses polynomial 40961 (0xA001) with init 0xFFFF
# The app uses bitwise calculation; this is an equivalent lookup table for speed
CRC_TABLE = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040,
]


def calculate_crc16(data: bytes) -> int:
    """Calculate CRC-16/MODBUS checksum.

    Args:
        data: Bytes to calculate CRC for

    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF
    for byte in data:
        crc = (crc >> 8) ^ CRC_TABLE[(crc ^ byte) & 0xFF]
    return crc


def verify_crc(data: bytes) -> bool:
    """Verify CRC-16/MODBUS checksum of received data.

    Args:
        data: Complete message including CRC bytes

    Returns:
        True if CRC is valid
    """
    if len(data) < 3:
        return False
    message = data[:-2]
    received_crc = struct.unpack("<H", data[-2:])[0]
    calculated_crc = calculate_crc16(message)
    return received_crc == calculated_crc


class RenogyClient:
    """Client for communicating with Renogy devices via Modbus RTU.

    This client supports reading data from Renogy solar charge controllers
    through USB-to-RS485 adapters.

    Example:
        >>> with RenogyClient("/dev/ttyUSB0") as client:
        ...     reading = client.read_all()
        ...     print(f"Battery: {reading.battery.state_of_charge}%")

    Attributes:
        port: Serial port path
        device_id: Modbus device ID (default 1)
        baudrate: Serial baudrate (default 9600)
        timeout: Read timeout in seconds (default 1.0)
    """

    # Modbus function codes
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_REGISTERS = 0x10

    def __init__(
        self,
        port: str,
        device_id: int = 1,
        baudrate: int = 9600,
        timeout: float = 1.0,
    ):
        """Initialize Renogy client.

        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
            device_id: Modbus slave device ID (default 1)
            baudrate: Serial communication speed (default 9600)
            timeout: Read timeout in seconds (default 1.0)
        """
        self.port = port
        self.device_id = device_id
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._device_info: Optional[DeviceInfo] = None

    def __enter__(self) -> "RenogyClient":
        """Context manager entry - opens connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes connection."""
        self.disconnect()

    def connect(self) -> None:
        """Open serial connection to device.

        Raises:
            DeviceNotFoundError: If the port cannot be opened
            CommunicationError: If connection fails
        """
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
        except serial.SerialException as e:
            raise DeviceNotFoundError(f"Cannot open port {self.port}: {e}") from e

    def disconnect(self) -> None:
        """Close serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info(f"Disconnected from {self.port}")
        self._serial = None

    @property
    def is_connected(self) -> bool:
        """Check if serial connection is open."""
        return self._serial is not None and self._serial.is_open

    def _build_request(self, function_code: int, start_address: int, count: int) -> bytes:
        """Build a Modbus RTU request frame.

        Args:
            function_code: Modbus function code
            start_address: Starting register address
            count: Number of registers to read

        Returns:
            Complete request frame with CRC
        """
        frame = struct.pack(
            ">BBHH",
            self.device_id,
            function_code,
            start_address,
            count,
        )
        crc = calculate_crc16(frame)
        frame += struct.pack("<H", crc)
        return frame

    def _send_request(self, request: bytes) -> bytes:
        """Send request and receive response.

        Args:
            request: Complete Modbus request frame

        Returns:
            Response data (without device ID, function code, or CRC)

        Raises:
            CommunicationError: If not connected
            TimeoutError: If no response received
            CRCError: If response CRC is invalid
            ModbusError: If device returns an error
        """
        if not self.is_connected:
            raise CommunicationError("Not connected to device")

        # Clear any pending data
        self._serial.reset_input_buffer()

        # Send request
        self._serial.write(request)
        logger.debug(f"TX: {request.hex()}")

        # Small delay for device processing
        time.sleep(0.05)

        # Read response header (device ID + function code + byte count)
        header = self._serial.read(3)
        if len(header) < 3:
            raise TimeoutError("No response from device")

        device_id, function_code, byte_count = struct.unpack("BBB", header)

        # Check for Modbus exception
        if function_code & 0x80:
            # Exception response - byte_count is actually exception code
            exception_code = byte_count
            # Read CRC
            crc_bytes = self._serial.read(2)
            raise ModbusError(
                get_modbus_exception_message(exception_code),
                function_code=function_code & 0x7F,
                exception_code=exception_code,
            )

        # Read data + CRC
        remaining = self._serial.read(byte_count + 2)
        if len(remaining) < byte_count + 2:
            raise TimeoutError("Incomplete response from device")

        response = header + remaining
        logger.debug(f"RX: {response.hex()}")

        # Verify CRC
        if not verify_crc(response):
            raise CRCError("Response CRC validation failed")

        # Return data portion only
        return remaining[:byte_count]

    def read_registers(self, start_address: int, count: int) -> list[int]:
        """Read holding registers from device.

        Args:
            start_address: Starting register address
            count: Number of registers to read

        Returns:
            List of register values (16-bit unsigned integers)

        Raises:
            Various exceptions from _send_request
        """
        request = self._build_request(self.READ_HOLDING_REGISTERS, start_address, count)
        data = self._send_request(request)

        # Unpack register values (big-endian 16-bit)
        values = []
        for i in range(0, len(data), 2):
            value = struct.unpack(">H", data[i : i + 2])[0]
            values.append(value)

        return values

    def write_register(self, address: int, value: int) -> None:
        """Write a single holding register.

        Args:
            address: Register address
            value: Value to write (16-bit unsigned)

        Raises:
            Various exceptions from _send_request
        """
        frame = struct.pack(
            ">BBHH",
            self.device_id,
            self.WRITE_SINGLE_REGISTER,
            address,
            value,
        )
        crc = calculate_crc16(frame)
        frame += struct.pack("<H", crc)

        self._send_request(frame)
        logger.info(f"Wrote {value} to register 0x{address:04X}")

    def read_device_info(self) -> DeviceInfo:
        """Read device identification information.

        Returns:
            DeviceInfo with model, serial number, and versions
        """
        info = DeviceInfo()

        try:
            # Read device model/SKU (8 registers = 16 chars at 0x000C)
            model_data = self.read_registers(0x000C, 8)
            model_bytes = b"".join(struct.pack(">H", v) for v in model_data)
            info.model = model_bytes.decode("ascii", errors="ignore").strip("\x00").strip()
        except Exception as e:
            logger.warning(f"Failed to read device model: {e}")

        try:
            # Read serial number (8 registers at 0x0018)
            serial_data = self.read_registers(0x0018, 8)
            serial_bytes = b"".join(struct.pack(">H", v) for v in serial_data)
            info.serial_number = serial_bytes.decode("ascii", errors="ignore").strip("\x00").strip()
        except Exception as e:
            logger.warning(f"Failed to read serial number: {e}")

        try:
            # Read hardware/software versions
            version_data = self.read_registers(0x0014, 4)
            info.hardware_version = f"V{version_data[0] >> 8}.{version_data[0] & 0xFF}"
            info.software_version = f"V{version_data[2] >> 8}.{version_data[2] & 0xFF}"
        except Exception as e:
            logger.warning(f"Failed to read versions: {e}")

        self._device_info = info
        return info

    def read_realtime_data(self) -> RenogyReading:
        """Read real-time monitoring data from device.

        Returns:
            RenogyReading with current battery, solar, and load data
        """
        reading = RenogyReading()

        # Read main data block (registers 0x0100-0x010A, 11 registers)
        try:
            data = self.read_registers(0x0100, 11)

            # Battery data
            reading.battery.state_of_charge = data[0]
            reading.battery.voltage = data[1] * 0.1
            reading.battery.current = data[2] * 0.01

            # Temperatures (0x0103: high byte = controller, low byte = battery)
            temp_reg = data[3]
            controller_temp = (temp_reg >> 8) & 0xFF
            battery_temp = temp_reg & 0xFF
            # Handle signed temperatures
            if controller_temp > 127:
                controller_temp -= 256
            if battery_temp > 127:
                battery_temp -= 256
            reading.controller.temperature = controller_temp
            reading.battery.temperature = battery_temp

            # Load data
            reading.load.voltage = data[4] * 0.1
            reading.load.current = data[5] * 0.01
            reading.load.power = data[6]

            # Solar data
            reading.solar.voltage = data[7] * 0.1
            reading.solar.current = data[8] * 0.01
            reading.solar.power = data[9]

            # Load switch state
            reading.load.is_on = data[10] == 1

        except Exception as e:
            logger.error(f"Failed to read realtime data: {e}")
            raise

        # Get cached device info or read it
        if self._device_info:
            reading.device_info = self._device_info

        return reading

    def read_all(self, include_device_info: bool = True) -> RenogyReading:
        """Read all available data from device.

        Args:
            include_device_info: Whether to read device info (slower)

        Returns:
            Complete RenogyReading with all data
        """
        if include_device_info and not self._device_info:
            self.read_device_info()

        reading = self.read_realtime_data()

        if self._device_info:
            reading.device_info = self._device_info

        return reading

    def set_load(self, on: bool) -> None:
        """Turn load output on or off.

        Args:
            on: True to turn on, False to turn off
        """
        value = 1 if on else 0
        self.write_register(0x010A, value)
        logger.info(f"Load switched {'ON' if on else 'OFF'}")

    def get_load_state(self) -> bool:
        """Get current load switch state.

        Returns:
            True if load is on, False if off
        """
        data = self.read_registers(0x010A, 1)
        return data[0] == 1
