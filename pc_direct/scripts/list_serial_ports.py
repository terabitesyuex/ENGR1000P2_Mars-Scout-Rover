"""List local serial ports for later PC-direct verification."""

from __future__ import annotations

from serial.tools import list_ports


def main() -> int:
    for port in list_ports.comports():
        print(f"{port.device}\t{port.description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
