"""Data models for Renogy device responses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DeviceInfo:
    """Device identification and version information."""

    model: str = ""
    serial_number: str = ""
    hardware_version: str = ""
    software_version: str = ""

    def __str__(self) -> str:
        return f"{self.model} (S/N: {self.serial_number})"


@dataclass
class BatteryData:
    """Battery status and measurements."""

    state_of_charge: int = 0  # Percentage (0-100)
    voltage: float = 0.0      # Volts
    current: float = 0.0      # Amps (charging current)
    temperature: int = 0      # Celsius (signed)

    @property
    def power(self) -> float:
        """Calculate battery power in watts."""
        return self.voltage * self.current

    def __str__(self) -> str:
        return f"Battery: {self.state_of_charge}% @ {self.voltage:.1f}V, {self.current:.2f}A"


@dataclass
class SolarData:
    """Solar panel measurements."""

    voltage: float = 0.0   # Volts
    current: float = 0.0   # Amps
    power: int = 0         # Watts

    def __str__(self) -> str:
        return f"Solar: {self.voltage:.1f}V, {self.current:.2f}A, {self.power}W"


@dataclass
class LoadData:
    """Load output measurements."""

    voltage: float = 0.0   # Volts
    current: float = 0.0   # Amps
    power: int = 0         # Watts
    is_on: bool = False    # Load switch state

    def __str__(self) -> str:
        state = "ON" if self.is_on else "OFF"
        return f"Load ({state}): {self.voltage:.1f}V, {self.current:.2f}A, {self.power}W"


@dataclass
class ControllerData:
    """Controller status and measurements."""

    temperature: int = 0      # Celsius (signed)
    charging_status: int = 0  # Charging state code

    @property
    def charging_status_text(self) -> str:
        """Get human-readable charging status."""
        from .registers import CHARGING_STATUS
        return CHARGING_STATUS.get(self.charging_status, f"Unknown ({self.charging_status})")

    def __str__(self) -> str:
        return f"Controller: {self.temperature}°C, {self.charging_status_text}"


@dataclass
class DailyStats:
    """Daily statistics."""

    min_battery_voltage: float = 0.0
    max_battery_voltage: float = 0.0
    max_charging_current: float = 0.0
    max_discharging_current: float = 0.0
    max_charging_power: int = 0
    max_discharging_power: int = 0
    charging_amp_hours: int = 0
    discharging_amp_hours: int = 0
    power_generation: int = 0      # Wh
    power_consumption: int = 0     # Wh


@dataclass
class HistoricalStats:
    """Historical/cumulative statistics."""

    total_operating_days: int = 0
    total_over_discharges: int = 0
    total_full_charges: int = 0
    total_amp_hours_charged: int = 0
    total_amp_hours_discharged: int = 0
    total_power_generated: int = 0    # kWh
    total_power_consumed: int = 0     # kWh


@dataclass
class RenogyReading:
    """Complete reading from a Renogy device."""

    timestamp: datetime = field(default_factory=datetime.now)
    device_info: DeviceInfo = field(default_factory=DeviceInfo)
    battery: BatteryData = field(default_factory=BatteryData)
    solar: SolarData = field(default_factory=SolarData)
    load: LoadData = field(default_factory=LoadData)
    controller: ControllerData = field(default_factory=ControllerData)
    daily_stats: Optional[DailyStats] = None
    historical_stats: Optional[HistoricalStats] = None

    def __str__(self) -> str:
        lines = [
            f"Reading at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  {self.battery}",
            f"  {self.solar}",
            f"  {self.load}",
            f"  {self.controller}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert reading to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "device": {
                "model": self.device_info.model,
                "serial_number": self.device_info.serial_number,
            },
            "battery": {
                "soc": self.battery.state_of_charge,
                "voltage": self.battery.voltage,
                "current": self.battery.current,
                "temperature": self.battery.temperature,
                "power": self.battery.power,
            },
            "solar": {
                "voltage": self.solar.voltage,
                "current": self.solar.current,
                "power": self.solar.power,
            },
            "load": {
                "voltage": self.load.voltage,
                "current": self.load.current,
                "power": self.load.power,
                "is_on": self.load.is_on,
            },
            "controller": {
                "temperature": self.controller.temperature,
                "charging_status": self.controller.charging_status,
                "charging_status_text": self.controller.charging_status_text,
            },
        }
