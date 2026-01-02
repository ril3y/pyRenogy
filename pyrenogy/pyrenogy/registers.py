"""Register definitions for Renogy solar devices.

This module contains register addresses and definitions for communicating
with Renogy solar charge controllers via Modbus RTU protocol.

Reverse engineered from Renogy DC Home App v1.10.69
Source files:
    - k4/d.java: Command tag to Modbus frame mappings
    - BleCtrlActivity.java: Response parsing with offsets and scales
    - ModBusUtils.java: CRC calculation and hex parsing
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable


class RegisterType(IntEnum):
    """Type of Modbus register."""
    HOLDING = 0x03  # Read holding registers
    INPUT = 0x04    # Read input registers
    COIL = 0x01     # Read coils
    DISCRETE = 0x02 # Read discrete inputs


@dataclass
class RegisterDefinition:
    """Definition of a single register or register group."""
    address: int
    name: str
    description: str
    length: int = 1
    scale: float = 1.0
    unit: str = ""
    signed: bool = False
    register_type: RegisterType = RegisterType.HOLDING
    decoder: Callable[[bytes], any] | None = None


# Device Information Registers
DEVICE_INFO_REGISTERS = {
    "device_model": RegisterDefinition(
        address=0x000C,
        name="device_model",
        description="Device Model/SKU",
        length=8,  # 16 ASCII characters
    ),
    "serial_number": RegisterDefinition(
        address=0x0018,
        name="serial_number",
        description="Device Serial Number",
        length=8,  # 16 ASCII characters
    ),
    "hardware_version": RegisterDefinition(
        address=0x0014,
        name="hardware_version",
        description="Hardware Version",
        length=2,
    ),
    "software_version": RegisterDefinition(
        address=0x0016,
        name="software_version",
        description="Software Version",
        length=2,
    ),
}


# Solar Charge Controller Registers (base 0x0100)
# Source: k4/d.java - "controller_read_00_22_command" -> "0301000023"
# Source: BleCtrlActivity.java:449-522 - response parsing
SCC_REGISTERS = {
    # Battery registers
    # Source: BleCtrlActivity.java:450-452 - hexRsp.substring(6, 10) for SOC
    "battery_soc": RegisterDefinition(
        address=0x0100,
        name="battery_soc",
        description="Battery State of Charge",
        unit="%",
    ),
    # Source: BleCtrlActivity.java:453-455 - ModBusUtils.J(r1) * 0.1f
    "battery_voltage": RegisterDefinition(
        address=0x0101,
        name="battery_voltage",
        description="Battery Voltage",
        scale=0.1,  # Source: BleCtrlActivity.java:454
        unit="V",
    ),
    # Source: BleCtrlActivity.java:456-458 - ModBusUtils.j(r3) * 0.01f
    "charging_current": RegisterDefinition(
        address=0x0102,
        name="charging_current",
        description="Battery Charging Current",
        scale=0.01,  # Source: BleCtrlActivity.java:457
        unit="A",
    ),
    "temperatures": RegisterDefinition(
        address=0x0103,
        name="temperatures",
        description="Controller and Battery Temperature",
        signed=True,
        unit="°C",
    ),
    # Load registers
    "load_voltage": RegisterDefinition(
        address=0x0104,
        name="load_voltage",
        description="Load Voltage",
        scale=0.1,
        unit="V",
    ),
    "load_current": RegisterDefinition(
        address=0x0105,
        name="load_current",
        description="Load Current",
        scale=0.01,
        unit="A",
    ),
    "load_power": RegisterDefinition(
        address=0x0106,
        name="load_power",
        description="Load Power",
        unit="W",
    ),
    # Solar panel registers
    # Source: BleCtrlActivity.java:483-485 - hexRsp.substring(34, 38), * 0.1f
    "solar_voltage": RegisterDefinition(
        address=0x0107,
        name="solar_voltage",
        description="Solar Panel Voltage",
        scale=0.1,  # Source: BleCtrlActivity.java:485
        unit="V",
    ),
    # Source: BleCtrlActivity.java:486-488 - hexRsp.substring(38, 42), * 0.01f
    "solar_current": RegisterDefinition(
        address=0x0108,
        name="solar_current",
        description="Solar Panel Current",
        scale=0.01,  # Source: BleCtrlActivity.java:488
        unit="A",
    ),
    # Source: BleCtrlActivity.java:489-491 - hexRsp.substring(42, 46)
    "solar_power": RegisterDefinition(
        address=0x0109,
        name="solar_power",
        description="Solar Panel Power",
        unit="W",
    ),
}


# Daily Statistics Registers
DAILY_STATS_REGISTERS = {
    "daily_min_battery_voltage": RegisterDefinition(
        address=0x010B,
        name="daily_min_battery_voltage",
        description="Daily Minimum Battery Voltage",
        scale=0.1,
        unit="V",
    ),
    "daily_max_battery_voltage": RegisterDefinition(
        address=0x010C,
        name="daily_max_battery_voltage",
        description="Daily Maximum Battery Voltage",
        scale=0.1,
        unit="V",
    ),
    "daily_max_charging_current": RegisterDefinition(
        address=0x010D,
        name="daily_max_charging_current",
        description="Daily Maximum Charging Current",
        scale=0.01,
        unit="A",
    ),
    "daily_max_discharging_current": RegisterDefinition(
        address=0x010E,
        name="daily_max_discharging_current",
        description="Daily Maximum Discharging Current",
        scale=0.01,
        unit="A",
    ),
    "daily_max_charging_power": RegisterDefinition(
        address=0x010F,
        name="daily_max_charging_power",
        description="Daily Maximum Charging Power",
        unit="W",
    ),
    "daily_max_discharging_power": RegisterDefinition(
        address=0x0110,
        name="daily_max_discharging_power",
        description="Daily Maximum Discharging Power",
        unit="W",
    ),
    "daily_charging_amp_hours": RegisterDefinition(
        address=0x0111,
        name="daily_charging_amp_hours",
        description="Daily Charging Amp-hours",
        unit="Ah",
    ),
    "daily_discharging_amp_hours": RegisterDefinition(
        address=0x0112,
        name="daily_discharging_amp_hours",
        description="Daily Discharging Amp-hours",
        unit="Ah",
    ),
    "daily_power_generation": RegisterDefinition(
        address=0x0113,
        name="daily_power_generation",
        description="Daily Power Generation",
        unit="Wh",
    ),
    "daily_power_consumption": RegisterDefinition(
        address=0x0114,
        name="daily_power_consumption",
        description="Daily Power Consumption",
        unit="Wh",
    ),
}


# Historical Statistics Registers
HISTORICAL_STATS_REGISTERS = {
    "total_operating_days": RegisterDefinition(
        address=0x0115,
        name="total_operating_days",
        description="Total Operating Days",
        unit="days",
    ),
    "total_battery_over_discharges": RegisterDefinition(
        address=0x0116,
        name="total_battery_over_discharges",
        description="Total Battery Over-discharges",
    ),
    "total_battery_full_charges": RegisterDefinition(
        address=0x0117,
        name="total_battery_full_charges",
        description="Total Battery Full Charges",
    ),
}


# Control Registers
CONTROL_REGISTERS = {
    "load_switch": RegisterDefinition(
        address=0x010A,
        name="load_switch",
        description="Load Switch Control",
    ),
}


# Charging Status Codes
# Source: com/renogy/dchome/ui/module/device/ctrl/a.java - method a() returns string resource ID
# Source: BleCtrlActivity.java:508-509 - hexRsp.substring(134, 138), bits parsed for state
CHARGING_STATUS = {
    0x00: "Deactivated",
    0x01: "Activated",
    0x02: "MPPT Charging",
    0x03: "Equalizing Charging",
    0x04: "Boost Charging",
    0x05: "Float Charging",
    0x06: "Current Limiting",
}


# Battery Type Codes
BATTERY_TYPES = {
    0: "User Defined",
    1: "Sealed Lead Acid",
    2: "Gel",
    3: "Flooded",
    4: "Lithium",
}


def get_all_realtime_registers() -> dict[str, RegisterDefinition]:
    """Get all real-time monitoring registers."""
    return {**SCC_REGISTERS}


def get_all_device_info_registers() -> dict[str, RegisterDefinition]:
    """Get all device information registers."""
    return {**DEVICE_INFO_REGISTERS}


def get_register_range(registers: dict[str, RegisterDefinition]) -> tuple[int, int]:
    """Get the start address and total length for a group of registers.

    Args:
        registers: Dictionary of register definitions

    Returns:
        Tuple of (start_address, total_length)
    """
    if not registers:
        return (0, 0)

    min_addr = min(r.address for r in registers.values())
    max_reg = max(registers.values(), key=lambda r: r.address + r.length)
    total_length = (max_reg.address + max_reg.length) - min_addr

    return (min_addr, total_length)
