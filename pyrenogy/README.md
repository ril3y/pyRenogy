# PyRenogy

A Python library for communicating with Renogy solar devices via USB-to-RS485 adapters using Modbus RTU protocol.

## Features

- Read battery status (SOC, voltage, current, temperature)
- Read solar panel data (voltage, current, power)
- Read load output data (voltage, current, power)
- Control load switch (on/off)
- Read device information (model, serial number, versions)
- Beautiful CLI with rich output (tables, colors, panels)
- Proper CRC-16/MODBUS calculation
- Type hints throughout
- Comprehensive error handling

## Installation

```bash
pip install pyrenogy
```

For development:

```bash
git clone https://github.com/pyrenogy/pyrenogy.git
cd pyrenogy
pip install -e ".[dev]"
```

## Hardware Requirements

- Renogy Solar Charge Controller (tested with Rover, Wanderer, Adventurer series)
- USB-to-RS485 adapter (CH340, FTDI, or similar)
- RS485 cable to connect adapter to controller's RS485 port

## CLI Usage

### Read Current Data

```bash
renogy read --port COM3
renogy read --port /dev/ttyUSB0
```

Output:
```
+-----------------+------------------+
| Device Information                 |
+-----------------+------------------+
| Model           | RNG-CTRL-WND30   |
| Serial Number   | 1234567890       |
| Hardware Version| V1.0             |
| Software Version| V2.3             |
+-----------------+------------------+

+------------------+    +------------------+
| Battery          |    | Solar Panel      |
+------------------+    +------------------+
| SOC          85% |    | Voltage   32.5V  |
| Voltage   13.2V  |    | Current   3.21A  |
| Current   2.45A  |    | Power      104W  |
| Temp        25°C |    +------------------+
+------------------+
```

### Continuous Monitoring

```bash
renogy monitor --port COM3 --interval 5
```

### Device Information

```bash
renogy info --port COM3
```

### Control Load Switch

```bash
renogy load --port COM3 --on
renogy load --port COM3 --off
```

### Scan for Devices

```bash
renogy scan
renogy scan --port COM3
```

### JSON Output

```bash
renogy read --port COM3 --json
```

## Python API

### Basic Usage

```python
from pyrenogy import RenogyClient

# Using context manager (recommended)
with RenogyClient("/dev/ttyUSB0") as client:
    reading = client.read_all()

    print(f"Battery SOC: {reading.battery.state_of_charge}%")
    print(f"Battery Voltage: {reading.battery.voltage}V")
    print(f"Solar Power: {reading.solar.power}W")
    print(f"Load Power: {reading.load.power}W")
```

### Manual Connection

```python
from pyrenogy import RenogyClient

client = RenogyClient("COM3", device_id=1, baudrate=9600)
client.connect()

try:
    # Read device info
    info = client.read_device_info()
    print(f"Device: {info.model}")

    # Read real-time data
    reading = client.read_realtime_data()
    print(f"Battery: {reading.battery.state_of_charge}%")

    # Control load
    client.set_load(True)  # Turn on
    client.set_load(False)  # Turn off

finally:
    client.disconnect()
```

### Error Handling

```python
from pyrenogy import RenogyClient, RenogyError, DeviceNotFoundError, TimeoutError

try:
    with RenogyClient("/dev/ttyUSB0") as client:
        reading = client.read_all()
except DeviceNotFoundError:
    print("Device not found on specified port")
except TimeoutError:
    print("Device did not respond")
except RenogyError as e:
    print(f"Communication error: {e}")
```

## Data Models

### RenogyReading

Complete reading containing all device data:

```python
reading.timestamp         # datetime
reading.device_info       # DeviceInfo
reading.battery           # BatteryData
reading.solar             # SolarData
reading.load              # LoadData
reading.controller        # ControllerData
```

### BatteryData

```python
battery.state_of_charge   # int (0-100%)
battery.voltage           # float (V)
battery.current           # float (A)
battery.temperature       # int (°C)
battery.power             # float (W) - calculated
```

### SolarData

```python
solar.voltage             # float (V)
solar.current             # float (A)
solar.power               # int (W)
```

### LoadData

```python
load.voltage              # float (V)
load.current              # float (A)
load.power                # int (W)
load.is_on                # bool
```

## Register Map

Key registers for Solar Charge Controller (base 0x0100):

| Address | Description | Scale | Unit |
|---------|-------------|-------|------|
| 0x0100 | Battery SOC | 1 | % |
| 0x0101 | Battery Voltage | 0.1 | V |
| 0x0102 | Charging Current | 0.01 | A |
| 0x0103 Hi | Controller Temp | 1 | °C |
| 0x0103 Lo | Battery Temp | 1 | °C |
| 0x0104 | Load Voltage | 0.1 | V |
| 0x0105 | Load Current | 0.01 | A |
| 0x0106 | Load Power | 1 | W |
| 0x0107 | Solar Voltage | 0.1 | V |
| 0x0108 | Solar Current | 0.01 | A |
| 0x0109 | Solar Power | 1 | W |
| 0x010A | Load Switch | 1 | on/off |

Device info registers:

| Address | Description |
|---------|-------------|
| 0x000C-0x0013 | Device Model (ASCII) |
| 0x0018-0x001F | Serial Number (ASCII) |

## Troubleshooting

### Device Not Found

- Check that the USB-RS485 adapter is connected
- Verify the correct port (use `renogy scan` to list ports)
- On Linux, ensure user has permission to access serial port:
  ```bash
  sudo usermod -a -G dialout $USER
  ```

### Timeout Errors

- Check RS485 cable connections (A+/B- polarity)
- Try different baud rates (9600 is most common)
- Verify device ID (default is 1)

### CRC Errors

- Check for electrical interference
- Try shorter cables
- Ensure proper termination if using long cables

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
