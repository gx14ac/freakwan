### LILYGO T-BEAM v1.2 (AXP2101 PMU, SX1276) hardware configuration
### Based on devices/device_config.tbeam_t22_v1_1.py (AXP192 version).
### External 0.96" SSD1306 OLED wired to: VCC->3V3 GND->GND SCL->22 SDA->21

from machine import Pin, SoftI2C
import time
from axp2101 import AXP2101

class DeviceConfig:
    config = {}

    config['ssd1306']= {
        'sda': 21,
        'scl': 22,
        'xres': 128,
        'yres': 64,
    }

    # Run headless if no OLED answers at I2C address 0x3C (not wired yet).
    if 0x3c not in SoftI2C(sda=Pin(21), scl=Pin(22)).scan():
        print("[T-Beam] no OLED found at 0x3C, running headless")
        del config['ssd1306']

    # No user LED wired to a GPIO on v1.2 (the charge LED belongs to the PMU).
    config['tx_led'] = False

    config['sx1276'] = {
        'miso': 19,
        'mosi': 27,
        'clock': 5,
        'chipselect': 18,
        'reset': 23,
        'dio0': 26
    }

    pmu = None

    def power_up(freakwan):
        pmu = AXP2101(sda=21, scl=22)
        DeviceConfig.pmu = pmu
        chip_id = pmu.read(0x03)
        print("[AXP2101] chip id", hex(chip_id), "(expected 0x4a)")

        # T-Beam v1.2 power rails:
        #   DCDC1 -> ESP32 and the 3V3 header pin (OLED). On at boot.
        #   ALDO2 -> LoRa radio
        #   ALDO3 -> GPS (not used by FreakWAN, left off to save power)
        # Voltage register value v gives 0.5 + 0.1*v volts: 28 = 3.3V.
        pmu.write(0x93, 28)     # ALDO2 3.3V
        pmu.setbit(0x90, 1)     # ALDO2 on  (LoRa)
        pmu.clearbit(0x90, 2)   # ALDO3 off (GPS)
        time.sleep_ms(50)       # Let the radio power settle before SPI.

        # Battery voltage measurement.
        pmu.setbit(0x68, 0)     # Battery detection on
        pmu.setbit(0x30, 0)     # Battery voltage ADC on

        # 18650 Li-ion charging: 4.2V termination, 500mA.
        pmu.write(0x64, 3)      # 3 = 4.2V
        pmu.write(0x62, 11)     # 11 = 500mA

        # Middle button (IO38), low when pressed. Polled by quickmsg.py:
        # short press switches views, long press selects quick messages.
        DeviceConfig.button0 = Pin(38, Pin.IN)

    def get_battery_microvolts():
        if DeviceConfig.pmu is None: return 0
        # PMU status 1 (0x00) bit 3: battery present. Without a battery the
        # ADC reads noise, which FreakWAN takes for an empty battery and
        # shuts down. Return 0 so it is treated as USB powered (100%).
        if not DeviceConfig.pmu.read(0x00) & 0x08: return 0
        return DeviceConfig.pmu.get_battery_voltage() * 1000
