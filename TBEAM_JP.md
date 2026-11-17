# T-Beam v1.2 (AXP2101) + Japan fork

Additions on top of antirez/freakwan for the LILYGO T-Beam v1.2 sold in Japan
(920MHz, 技適, AXP2101 PMU, SX1276) with an external 0.96" SSD1306 OLED.

- `devices/device_config.tbeam_v1_2_axp2101.py`: powers the LoRa rail (ALDO2),
  turns GPS (ALDO3) off, sets 18650 charging to 4.2V / 500mA. Runs headless
  when no OLED answers at I2C 0x3C.
- `wan_config.py`: 920.8MHz, BW 125kHz, SF10, CR 4/8, 13dBm (ARIB STD-T108).
- `quickmsg.py`: canned messages on the IO38 button.
  Short press: switch view. Long press: select / next message. Short press
  while selecting: send. Manage with `!qm`, `!qm add <text>`, `!qm del <n>`,
  `!qm send <n>`, `!qm reset`. `label|text` shows `label` on the OLED.
- `jpfont.py` + `jpfont.bin`: Japanese on the OLED with the Misaki Gothic 8x8
  font (https://littlelimit.net/misaki.htm, free to use, copy and
  redistribute). Rebuild with `tools/misaki_bdf2bin.py misaki_gothic.bdf jpfont.bin`.
- `flash_tbeam.sh <port>`: erase, write MicroPython 1.22.2, copy everything.

OLED wiring: VCC->3V3, GND->GND, SCL->22, SDA->21.
