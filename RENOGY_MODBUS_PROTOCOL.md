# Renogy Modbus RTU Protocol Documentation

> Reverse engineered from Renogy DC Home App v1.10.69

## Source Information

This protocol was reverse engineered from the Renogy DC Home Android app:
- **APK Source**: `Renogy_1.10.69_APKPure.xapk`
- **Package**: `com.renogy.dchome`
- **Decompiler**: jadx

### Key Source Files
| File | Contains |
|------|----------|
| `k4/d.java` | Command tag to Modbus frame mappings |
| `com/renogy/utillib/utils/ModBusUtils.java` | CRC calculation, hex parsing utilities |
| `com/renogy/dchome/ui/module/device/ctrl/activity/BleCtrlActivity.java` | Controller response parsing (voltage, current, SOC, etc.) |
| `com/renogy/dchome/ui/module/device/ctrl/CtrlConsts.java` | Controller constants, SKU lists |
| `com/renogy/dchome/ui/module/device/battery/ble/BleBatSingleActivity.java` | Battery response parsing |
| `com/renogy/dchome/ui/module/device/battery/ble/a.java` | Battery command tags |

## Overview

Renogy solar charge controllers, batteries, inverters, and DC-DC converters communicate using **Modbus RTU** protocol over RS485. This document details the register mappings and communication protocol.

## Communication Settings

| Parameter | Value |
|-----------|-------|
| Baud Rate | 9600 |
| Data Bits | 8 |
| Parity | None |
| Stop Bits | 1 |
| Default Device Address | 0xFF (broadcast) |

## Frame Format

### Request Frame
```
[Device Address (1 byte)]
[Function Code (1 byte)]
[Register Address (2 bytes, big-endian)]
[Register Count (2 bytes, big-endian)]
[CRC16 (2 bytes, little-endian)]
```

### Response Frame
```
[Device Address (1 byte)]
[Function Code (1 byte)]
[Byte Count (1 byte)]
[Data (N bytes)]
[CRC16 (2 bytes, little-endian)]
```

## CRC-16 Calculation

Uses CRC-16/MODBUS algorithm:
- Polynomial: 0xA001 (0x8005 reflected)
- Initial Value: 0xFFFF
- Result: Little-endian (low byte first)

> **Source**: `ModBusUtils.java:917-941` - method `u(byte[] bytes)`

```python
def calc_crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')
```

## Function Codes

| Code | Description |
|------|-------------|
| 0x03 | Read Holding Registers |
| 0x04 | Read Input Registers |
| 0x06 | Write Single Register |
| 0x10 | Write Multiple Registers |
| 0x79 | Custom: Clear History Data |

---

# Solar Charge Controller Registers

## Main Operating Data (0x0100 - 0x0122)

**Command Tag**: `controller_read_00_22_command`
**Modbus Frame**: `[ADDR] 03 01 00 00 23 [CRC]`
**Description**: Read 35 registers starting at 0x0100

> **Source**: `k4/d.java:449` defines command frame, `BleCtrlActivity.java:449-522` parses response

| Register | Offset | Name | Scale | Unit | Description |
|----------|--------|------|-------|------|-------------|
| 0x0100 | 0 | battery_soc | 1 | % | Battery State of Charge |
| 0x0101 | 2 | battery_voltage | ×0.1 | V | Battery Voltage |
| 0x0102 | 4 | charging_current | ×0.01 | A | Charging Current |
| 0x0103 Hi | 6 | controller_temp | signed | °C | Controller Temperature |
| 0x0103 Lo | 7 | battery_temp | signed | °C | Battery Temperature |
| 0x0104 | 8 | load_voltage | ×0.1 | V | Load Output Voltage |
| 0x0105 | 10 | load_current | ×0.01 | A | Load Output Current |
| 0x0106 | 12 | load_power | 1 | W | Load Power |
| 0x0107 | 14 | solar_voltage | ×0.1 | V | Solar Panel Voltage |
| 0x0108 | 16 | solar_current | ×0.01 | A | Solar Panel Current |
| 0x0109 | 18 | solar_power | 1 | W | Solar Panel Power |
| 0x010A | 20 | load_switch | bit | - | Load Switch Status |
| 0x0113 | 38 | min_battery_voltage_today | ×0.001 | V | Min Battery Voltage Today |
| 0x0114 | 40 | max_battery_voltage_today | ×0.001 | V | Max Battery Voltage Today |
| 0x011C-0x011D | 56-59 | power_generation_today | ×0.001 | kWh | Power Generated Today |
| 0x0120 Hi | 64 | load_status | bitmap | - | Load Switch + Charging State |
| 0x0120 Lo | 65 | charging_state | code | - | Charging State Code |
| 0x0121-0x0122 | 66-69 | fault_flags | bitmap | - | Error/Warning Flags |

## Alternate Operating Data (0x0101 - 0x0107)

**Command Tag**: `controller_read_01_07_command`
**Modbus Frame**: `[ADDR] 03 01 01 00 07 [CRC]`

| Register | Offset | Name | Scale | Unit |
|----------|--------|------|-------|------|
| 0x0101 | 0 | battery_voltage | ×0.1 | V |
| 0x0102 | 2 | charging_current | ×0.01 | A |
| 0x0103 Hi | 4 | controller_temp | signed | °C |
| 0x0103 Lo | 5 | battery_temp | signed | °C |
| 0x0104 | 6 | load_voltage | ×0.1 | V |
| 0x0105 | 8 | load_current | ×0.01 | A |
| 0x0107 | 12 | solar_voltage | ×0.1 | V |

## Solar Current/Power (0x0108 - 0x010E)

**Command Tag**: `controller_read_08_0E_command`
**Modbus Frame**: `[ADDR] 03 01 08 00 07 [CRC]`

| Register | Offset | Name | Scale | Unit |
|----------|--------|------|-------|------|
| 0x0108 | 0 | solar_current | ×0.01 | A |
| 0x0109 | 2 | solar_power | 1 | W |

## Daily Statistics (0x011C - 0x0122)

**Command Tag**: `controller_read_1C_22_command`
**Modbus Frame**: `[ADDR] 03 01 1C 00 07 [CRC]`

| Register | Offset | Name | Scale | Unit |
|----------|--------|------|-------|------|
| 0x011C-0x011D | 0-3 | power_generation_today | ×0.001 | kWh |
| 0x0120 Hi | 8 | load_switch_status | bit 7 | on/off |
| 0x0120 Lo | 9 | charging_state | code | - |
| 0x0121-0x0122 | 10-13 | fault_flags | bitmap | - |

## Device Information (0x000C - 0x0013)

**Command Tag**: `controller_read_sku_command`
**Modbus Frame**: `[ADDR] 03 00 0C 00 08 [CRC]`

| Register | Description |
|----------|-------------|
| 0x000C-0x0013 | Product SKU/Model (ASCII, 16 chars) |

## Serial Number (0x001F - 0x0027)

**Command Tag**: `controller_001f_0027_data`
**Modbus Frame**: `[ADDR] 03 00 1F 00 09 [CRC]`

| Register | Description |
|----------|-------------|
| 0x001F-0x0027 | Serial Number (ASCII, 18 chars) |

## Extended Parameters (0xE003 - 0xE01D)

**Command Tag**: `controller_read_03_1D_command`
**Modbus Frame**: `[ADDR] 03 E0 03 00 1B [CRC]`

| Offset | Name | Description |
|--------|------|-------------|
| 4-7 | battery_type | Battery Type Code |
| 106-107 | dc_load_enable | 0x0F = enabled |

## Firmware Version (0x0014 - 0x0015)

**Command Tag**: `0300140002`
**Modbus Frame**: `[ADDR] 03 00 14 00 02 [CRC]`

| Offset | Description | Format |
|--------|-------------|--------|
| 0-3 | Version | YYYY/MM/DD encoded |

---

# Battery Registers

## Cell Voltages (0x1388 / 5000 decimal)

**Command Tag**: `battery_read_00_35_data`
**Modbus Frame**: `[ADDR] 03 13 88 00 22 [CRC]`

| Offset | Name | Description |
|--------|------|-------------|
| 0-31 | cell_voltages | 16 cells × 2 bytes (mV) |
| 32-33 | total_voltage | Total pack voltage |

## Battery Current (0x13B2 / 5042 decimal)

**Command Tag**: `battery_read_42_47_data`
**Modbus Frame**: `[ADDR] 03 13 B2 00 06 [CRC]`

| Offset | Name | Scale | Unit |
|--------|------|-------|------|
| 0-1 | current | ×0.01 or ×0.1 | A |

## Battery Status (0x13F0 / 5104 decimal)

**Command Tag**: `battery_read_5104_5131_data`
**Modbus Frame**: `[ADDR] 03 13 F0 00 1C [CRC]`

| Offset | Name | Description |
|--------|------|-------------|
| 8-15 | status_flags | Battery status bitmap |

## Battery SKU (0x1402)

**Command Tag**: `battery_read_sku_command`
**Modbus Frame**: `[ADDR] 03 14 02 00 08 [CRC]`

---

# Inverter Registers

## Main Data (0x0FA0 / 4000 decimal)

**Command Tag**: `new_inv_4000_4009`
**Modbus Frame**: `[ADDR] 03 0F A0 00 0A [CRC]`

## SKU (0x10D7 / 4311 decimal)

**Command Tag**: `inverter_read_sku_cmd`
**Modbus Frame**: `[ADDR] 03 10 D7 00 08 [CRC]`

## Firmware Version (0x10DF / 4319 decimal)

**Command Tag**: `inv_version`
**Modbus Frame**: `[ADDR] 03 10 DF 00 08 [CRC]`

## Serial Number (0x1010 / 4112 decimal)

**Command Tag**: `inv_sn`
**Modbus Frame**: `[ADDR] 03 10 10 00 09 [CRC]`

---

# DC-DC Controller Registers

## Operating Data (0xE001)

**Command Tag**: `dcc_read_01_14_cmd`
**Modbus Frame**: `[ADDR] 03 E0 01 00 14 [CRC]`

## SKU (0x000C)

**Command Tag**: `dcc_read_sku_cmd`
**Modbus Frame**: `[ADDR] 03 00 0C 00 08 [CRC]`

---

# Charging State Codes

> **Source**: `com/renogy/dchome/ui/module/device/ctrl/a.java` - charging state string mappings

| Code | State |
|------|-------|
| 0x00 | Deactivated |
| 0x01 | Activated |
| 0x02 | MPPT Charging |
| 0x03 | Equalizing Charge |
| 0x04 | Boost Charge |
| 0x05 | Float Charge |
| 0x06 | Current Limiting (Overpower) |

---

# Fault/Error Flags (Bitmap)

> **Source**: `com/renogy/dchome/ui/module/device/ctrl/c.java` - method `a()` maps error codes to strings

| Bit | Controller Fault |
|-----|------------------|
| C0 | Charge MOS Short |
| C1 | Anti-Reverse MOS Short |
| C2 | Solar Panel Reverse Connected |
| C3 | Solar Panel Over-Voltage |
| C4 | Solar Panel Counter-Current |
| C5 | PV Input Side Over-Voltage |
| C6 | PV Input Side Short Circuit |
| C7 | PV Input Overpower |
| C8 | Ambient Temp High |
| C9 | Controller Temp High |
| C10 | Load Overpower/Current |
| C11 | Load Short Circuit |
| C12 | Battery Under Voltage |
| C13 | Battery Over Voltage |
| C14 | Battery Over-Discharge |

---

# Write Commands

## Toggle Load Switch

**Turn ON**: `[ADDR] 06 01 0A 00 01 [CRC]`
**Turn OFF**: `[ADDR] 06 01 0A 00 00 [CRC]`

## Clear Historical Data

**Modbus Frame**: `[ADDR] 79 00 00 00 01 [CRC]`

---

# Supported Device Models

## Solar Charge Controllers
- RNG-CTRL-RVR20/30/40 (Rover Series)
- RNG-CTRL-RVRPG20/30/40/60 (Rover Elite)
- RNG-CTRL-WND10/WNDPG10 (Wanderer)
- RCC30REGO, RCC60REGO-G2 (REGO Series)
- ML2420N

## Batteries
- RBT100LFP12S (LiFePO4 Series)
- Core Series Batteries

## Inverters
- REGO Series Inverters
- Phoenix Inverters

---

# Example Communication

## Read Battery SOC and Voltage

```
Request:  FF 03 01 00 00 02 C5 D4
          │  │  └──┬──┘ └──┬──┘ └──┬──┘
          │  │     │       │       └── CRC16
          │  │     │       └── 2 registers
          │  │     └── Start at 0x0100
          │  └── Function 03 (Read)
          └── Device Address 0xFF

Response: FF 03 04 00 64 00 C8 XX XX
          │  │  │  └──┬──┘ └──┬──┘
          │  │  │     │       └── Voltage: 0x00C8 = 200 → 20.0V
          │  │  │     └── SOC: 0x0064 = 100%
          │  │  └── 4 bytes of data
          │  └── Function 03
          └── Device Address
```

---

# References

- Reverse engineered from: Renogy DC Home App v1.10.69
- Source files: `com.renogy.utillib.utils.ModBusUtils`
- Command definitions: `k4.d` (decompiled)
- Parsing logic: `BleCtrlActivity.java`, `BleBatSingleActivity.java`
