"""Command-line interface for pyrenogy.

This module provides a beautiful CLI using Rich for interacting with
Renogy solar devices.
"""

import logging
import sys
import time
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .client import RenogyClient
from .exceptions import RenogyError
from .models import RenogyReading

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False)],
    )


def create_battery_panel(reading: RenogyReading) -> Panel:
    """Create a Rich panel for battery information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Unit", style="dim")

    battery = reading.battery

    # SOC with color coding
    soc = battery.state_of_charge
    if soc >= 80:
        soc_style = "green bold"
    elif soc >= 50:
        soc_style = "yellow"
    elif soc >= 20:
        soc_style = "orange1"
    else:
        soc_style = "red bold"

    table.add_row("State of Charge", Text(f"{soc}", style=soc_style), "%")
    table.add_row("Voltage", f"{battery.voltage:.1f}", "V")
    table.add_row("Current", f"{battery.current:.2f}", "A")
    table.add_row("Power", f"{battery.power:.1f}", "W")
    table.add_row("Temperature", f"{battery.temperature}", "°C")

    return Panel(table, title="[bold blue]Battery[/bold blue]", border_style="blue")


def create_solar_panel(reading: RenogyReading) -> Panel:
    """Create a Rich panel for solar panel information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_column("Unit", style="dim")

    solar = reading.solar

    # Power with color coding
    power = solar.power
    if power > 100:
        power_style = "green bold"
    elif power > 10:
        power_style = "yellow"
    else:
        power_style = "dim"

    table.add_row("Voltage", f"{solar.voltage:.1f}", "V")
    table.add_row("Current", f"{solar.current:.2f}", "A")
    table.add_row("Power", Text(f"{power}", style=power_style), "W")

    return Panel(table, title="[bold yellow]Solar Panel[/bold yellow]", border_style="yellow")


def create_load_panel(reading: RenogyReading) -> Panel:
    """Create a Rich panel for load information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Unit", style="dim")

    load = reading.load

    # Status indicator
    status = Text("ON", style="green bold") if load.is_on else Text("OFF", style="red")
    table.add_row("Status", status, "")
    table.add_row("Voltage", f"{load.voltage:.1f}", "V")
    table.add_row("Current", f"{load.current:.2f}", "A")
    table.add_row("Power", f"{load.power}", "W")

    return Panel(table, title="[bold magenta]Load Output[/bold magenta]", border_style="magenta")


def create_controller_panel(reading: RenogyReading) -> Panel:
    """Create a Rich panel for controller information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Unit", style="dim")

    controller = reading.controller

    table.add_row("Temperature", f"{controller.temperature}", "°C")
    table.add_row("Charging Status", controller.charging_status_text, "")

    return Panel(table, title="[bold white]Controller[/bold white]", border_style="white")


def create_device_info_panel(reading: RenogyReading) -> Panel:
    """Create a Rich panel for device information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="green")

    info = reading.device_info

    table.add_row("Model", info.model or "Unknown")
    table.add_row("Serial Number", info.serial_number or "Unknown")
    table.add_row("Hardware Version", info.hardware_version or "Unknown")
    table.add_row("Software Version", info.software_version or "Unknown")

    return Panel(table, title="[bold cyan]Device Information[/bold cyan]", border_style="cyan")


def create_summary_table(reading: RenogyReading) -> Table:
    """Create a summary table with all readings."""
    table = Table(title=f"Renogy Reading - {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Parameter", style="white")
    table.add_column("Value", justify="right", style="green")
    table.add_column("Unit", style="dim")

    # Battery section
    table.add_row("Battery", "State of Charge", str(reading.battery.state_of_charge), "%")
    table.add_row("", "Voltage", f"{reading.battery.voltage:.1f}", "V")
    table.add_row("", "Current", f"{reading.battery.current:.2f}", "A")
    table.add_row("", "Temperature", str(reading.battery.temperature), "°C")

    table.add_section()

    # Solar section
    table.add_row("Solar", "Voltage", f"{reading.solar.voltage:.1f}", "V")
    table.add_row("", "Current", f"{reading.solar.current:.2f}", "A")
    table.add_row("", "Power", str(reading.solar.power), "W")

    table.add_section()

    # Load section
    load_status = "ON" if reading.load.is_on else "OFF"
    table.add_row("Load", "Status", load_status, "")
    table.add_row("", "Voltage", f"{reading.load.voltage:.1f}", "V")
    table.add_row("", "Current", f"{reading.load.current:.2f}", "A")
    table.add_row("", "Power", str(reading.load.power), "W")

    table.add_section()

    # Controller section
    table.add_row("Controller", "Temperature", str(reading.controller.temperature), "°C")
    table.add_row("", "Status", reading.controller.charging_status_text, "")

    return table


def create_monitor_display(reading: RenogyReading) -> Table:
    """Create a compact display for monitoring mode."""
    table = Table(show_header=True, header_style="bold")

    table.add_column("Time", style="dim", width=8)
    table.add_column("SOC", justify="right", width=5)
    table.add_column("Batt V", justify="right", width=7)
    table.add_column("Batt A", justify="right", width=7)
    table.add_column("Solar W", justify="right", width=8)
    table.add_column("Load W", justify="right", width=7)
    table.add_column("Ctrl °C", justify="right", width=7)

    time_str = reading.timestamp.strftime("%H:%M:%S")

    # Color code SOC
    soc = reading.battery.state_of_charge
    if soc >= 80:
        soc_str = f"[green]{soc}%[/green]"
    elif soc >= 50:
        soc_str = f"[yellow]{soc}%[/yellow]"
    elif soc >= 20:
        soc_str = f"[orange1]{soc}%[/orange1]"
    else:
        soc_str = f"[red]{soc}%[/red]"

    # Color code solar power
    solar_w = reading.solar.power
    if solar_w > 100:
        solar_str = f"[green]{solar_w}[/green]"
    elif solar_w > 10:
        solar_str = f"[yellow]{solar_w}[/yellow]"
    else:
        solar_str = f"[dim]{solar_w}[/dim]"

    table.add_row(
        time_str,
        soc_str,
        f"{reading.battery.voltage:.1f}V",
        f"{reading.battery.current:.2f}A",
        solar_str,
        str(reading.load.power),
        str(reading.controller.temperature),
    )

    return table


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.version_option(version="0.1.0", prog_name="renogy")
def cli(verbose: bool):
    """Renogy Solar Device CLI - Read and control Renogy solar devices."""
    setup_logging(verbose)


@cli.command()
@click.option("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
@click.option("-d", "--device-id", default=1, help="Modbus device ID (default: 1)")
@click.option("-b", "--baudrate", default=9600, help="Baudrate (default: 9600)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def read(port: str, device_id: int, baudrate: int, output_json: bool):
    """Read current data from the device."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Connecting to device...", total=None)

            with RenogyClient(port, device_id=device_id, baudrate=baudrate) as client:
                reading = client.read_all()

        if output_json:
            import json

            console.print_json(json.dumps(reading.to_dict(), indent=2))
        else:
            console.print()
            console.print(create_device_info_panel(reading))
            console.print()

            # Create a grid layout
            from rich.columns import Columns

            panels = [
                create_battery_panel(reading),
                create_solar_panel(reading),
            ]
            console.print(Columns(panels, equal=True, expand=True))

            panels = [
                create_load_panel(reading),
                create_controller_panel(reading),
            ]
            console.print(Columns(panels, equal=True, expand=True))

    except RenogyError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)


@cli.command()
@click.option("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
@click.option("-d", "--device-id", default=1, help="Modbus device ID (default: 1)")
@click.option("-b", "--baudrate", default=9600, help="Baudrate (default: 9600)")
@click.option("-i", "--interval", default=5, help="Update interval in seconds (default: 5)")
@click.option("-c", "--count", default=0, help="Number of readings (0 = unlimited)")
def monitor(port: str, device_id: int, baudrate: int, interval: int, count: int):
    """Continuously monitor device data."""
    try:
        with RenogyClient(port, device_id=device_id, baudrate=baudrate) as client:
            console.print(f"[green]Connected to {port}[/green]")
            console.print(f"Monitoring every {interval} seconds. Press Ctrl+C to stop.\n")

            # Read device info once
            client.read_device_info()

            readings_taken = 0

            with Live(console=console, refresh_per_second=1) as live:
                while count == 0 or readings_taken < count:
                    try:
                        reading = client.read_realtime_data()
                        reading.device_info = client._device_info

                        # Create display
                        from rich.layout import Layout

                        layout = Layout()
                        layout.split_column(
                            Layout(create_device_info_panel(reading), size=6),
                            Layout(name="main"),
                        )
                        layout["main"].split_row(
                            Layout(create_battery_panel(reading)),
                            Layout(create_solar_panel(reading)),
                        )

                        # Alternative: use summary table
                        live.update(create_summary_table(reading))

                        readings_taken += 1
                        time.sleep(interval)

                    except RenogyError as e:
                        console.print(f"[red]Read error:[/red] {e}")
                        time.sleep(interval)

    except RenogyError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
        sys.exit(0)


@cli.command()
@click.option("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
@click.option("-d", "--device-id", default=1, help="Modbus device ID (default: 1)")
@click.option("-b", "--baudrate", default=9600, help="Baudrate (default: 9600)")
def info(port: str, device_id: int, baudrate: int):
    """Show device information."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Reading device information...", total=None)

            with RenogyClient(port, device_id=device_id, baudrate=baudrate) as client:
                device_info = client.read_device_info()

        console.print()
        table = Table(title="Device Information", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Model", device_info.model or "Unknown")
        table.add_row("Serial Number", device_info.serial_number or "Unknown")
        table.add_row("Hardware Version", device_info.hardware_version or "Unknown")
        table.add_row("Software Version", device_info.software_version or "Unknown")
        table.add_row("Port", port)
        table.add_row("Device ID", str(device_id))
        table.add_row("Baudrate", str(baudrate))

        console.print(table)

    except RenogyError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("-p", "--port", required=True, help="Serial port (e.g., COM3 or /dev/ttyUSB0)")
@click.option("-d", "--device-id", default=1, help="Modbus device ID (default: 1)")
@click.option("-b", "--baudrate", default=9600, help="Baudrate (default: 9600)")
@click.option("--on/--off", required=True, help="Turn load on or off")
def load(port: str, device_id: int, baudrate: int, on: bool):
    """Control the load output switch."""
    action = "ON" if on else "OFF"

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Switching load {action}...", total=None)

            with RenogyClient(port, device_id=device_id, baudrate=baudrate) as client:
                client.set_load(on)

                # Verify the change
                time.sleep(0.5)
                current_state = client.get_load_state()

        if current_state == on:
            console.print(f"[green]Load successfully switched {action}[/green]")
        else:
            console.print(f"[yellow]Warning: Load state may not have changed[/yellow]")

    except RenogyError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option("-p", "--port", help="Serial port to scan (optional)")
def scan(port: Optional[str]):
    """Scan for Renogy devices on serial ports."""
    import serial.tools.list_ports

    console.print("[cyan]Scanning for serial ports...[/cyan]\n")

    ports = list(serial.tools.list_ports.comports())

    if not ports:
        console.print("[yellow]No serial ports found[/yellow]")
        return

    table = Table(title="Available Serial Ports")
    table.add_column("Port", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Hardware ID", style="dim")

    for p in ports:
        table.add_row(p.device, p.description, p.hwid)

    console.print(table)

    if port:
        console.print(f"\n[cyan]Attempting to connect to {port}...[/cyan]")
        try:
            with RenogyClient(port, timeout=2.0) as client:
                info = client.read_device_info()
                console.print(f"[green]Found device: {info.model} (S/N: {info.serial_number})[/green]")
        except RenogyError as e:
            console.print(f"[red]Failed to connect: {e}[/red]")


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
