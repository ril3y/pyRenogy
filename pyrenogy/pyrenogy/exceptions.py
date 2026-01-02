"""Custom exceptions for pyrenogy package."""


class RenogyError(Exception):
    """Base exception for all Renogy-related errors."""

    pass


class CommunicationError(RenogyError):
    """Error during serial communication with device."""

    pass


class CRCError(RenogyError):
    """CRC validation failed for received data."""

    pass


class ModbusError(RenogyError):
    """Modbus protocol error."""

    def __init__(self, message: str, function_code: int | None = None, exception_code: int | None = None):
        super().__init__(message)
        self.function_code = function_code
        self.exception_code = exception_code


class ConnectionError(RenogyError):
    """Failed to connect to device."""

    pass


class TimeoutError(RenogyError):
    """Communication timeout."""

    pass


class InvalidResponseError(RenogyError):
    """Invalid or unexpected response from device."""

    pass


class DeviceNotFoundError(RenogyError):
    """Device not found on specified port."""

    pass


# Modbus exception codes
MODBUS_EXCEPTION_CODES = {
    0x01: "Illegal Function",
    0x02: "Illegal Data Address",
    0x03: "Illegal Data Value",
    0x04: "Slave Device Failure",
    0x05: "Acknowledge",
    0x06: "Slave Device Busy",
    0x08: "Memory Parity Error",
    0x0A: "Gateway Path Unavailable",
    0x0B: "Gateway Target Device Failed to Respond",
}


def get_modbus_exception_message(code: int) -> str:
    """Get human-readable message for Modbus exception code."""
    return MODBUS_EXCEPTION_CODES.get(code, f"Unknown Exception (0x{code:02X})")
