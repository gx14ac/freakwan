#!/bin/sh
# Flash MicroPython + FreakWAN to a LILYGO T-Beam v1.2.
# Usage: ./flash_tbeam.sh /dev/cu.usbserial-XXXX   (or /dev/cu.wchusbserial-XXXX)
set -e
PORT="$1"
[ -n "$PORT" ] || { echo "usage: $0 <serial port>"; ls /dev/cu.*usb* 2>/dev/null; exit 1; }
cd "$(dirname "$0")"
cp devices/device_config.tbeam_v1_2_axp2101.py device_config.py

echo "== 1/3 erase flash"
esptool --port "$PORT" erase_flash
echo "== 2/3 write MicroPython"
esptool --port "$PORT" --baud 460800 write_flash -z 0x1000 \
  devices/micropython-images/t3_and_tbeam/ESP32_GENERIC-20240222-v1.22.2.bin
sleep 3
echo "== 3/3 copy FreakWAN"
mpremote connect "$PORT" cp *.py jpfont.bin :
mpremote connect "$PORT" reset
echo "done. watch the log with: mpremote connect $PORT repl"
