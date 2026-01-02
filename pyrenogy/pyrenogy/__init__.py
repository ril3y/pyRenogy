"""PyRenogy - Python library for communicating with Renogy solar devices.

This package provides a client for reading data from Renogy solar charge
controllers via USB-to-RS485 adapters using the Modbus RTU protocol.

Example:
    >>> from pyrenogy import RenogyClient
    >>> with RenogyClient("/dev/ttyUSB0") as client:
    ...     reading = client.read_all()
    ...     print(f"Battery: {reading.battery.state_of_charge}%")
    ...     print(f"Solar Power: {reading.solar.power}W")

Features:
    - Read battery status (SOC, voltage, current, temperature)
    - Read solar panel data (voltage, current, power)
    - Read load output data (voltage, current, power)
    - Control load switch (on/off)
    - Read device information (model, serial number, versions)
    - Beautiful CLI with rich output

"""

__version__ = "0.1.0"
__author__ = "PyRenogy Contributors"

from .client import RenogyClient, calculate_crc16, verify_crc
from .exceptions import (
    CommunicationError,
    ConnectionError,
    CRCError,
    DeviceNotFoundError,
    InvalidResponseError,
    ModbusError,
    RenogyError,
    TimeoutError,
)
from .models import (
    BatteryData,
    ControllerData,
    DailyStats,
    DeviceInfo,
    HistoricalStats,
    LoadData,
    RenogyReading,
    SolarData,
)
from .registers import (
    CHARGING_STATUS,
    CONTROL_REGISTERS,
    DAILY_STATS_REGISTERS,
    DEVICE_INFO_REGISTERS,
    HISTORICAL_STATS_REGISTERS,
    RegisterDefinition,
    RegisterType,
    SCC_REGISTERS,
    get_all_device_info_registers,
    get_all_realtime_registers,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "RenogyClient",
    "calculate_crc16",
    "verify_crc",
    # Exceptions
    "RenogyError",
    "CommunicationError",
    "ConnectionError",
    "CRCError",
    "DeviceNotFoundError",
    "InvalidResponseError",
    "ModbusError",
    "TimeoutError",
    # Models
    "BatteryData",
    "ControllerData",
    "DailyStats",
    "DeviceInfo",
    "HistoricalStats",
    "LoadData",
    "RenogyReading",
    "SolarData",
    # Registers
    "CHARGING_STATUS",
    "CONTROL_REGISTERS",
    "DAILY_STATS_REGISTERS",
    "DEVICE_INFO_REGISTERS",
    "HISTORICAL_STATS_REGISTERS",
    "RegisterDefinition",
    "RegisterType",
    "SCC_REGISTERS",
    "get_all_device_info_registers",
    "get_all_realtime_registers",
]
