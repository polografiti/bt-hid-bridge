# Setup Guide

## Hardware Required

- **ESP32-WROOM-32** or **ESP32-DevKitC** (classic ESP32, not S3/C3)
- USB cable (data, not charge-only)
- 2.4 GHz Wi-Fi access point
- PC running Windows (primary) or macOS/Linux

---

## Part 1 — ESP-IDF Toolchain Setup

### macOS / Linux

```bash
mkdir -p ~/esp && cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout v5.1.2
./install.sh esp32
source export.sh        # run this in every new terminal session
```

### Windows

Download the ESP-IDF Windows Installer from:
https://dl.espressif.com/dl/esp-idf/

Install version 5.1.x, select target `esp32`.
Use the "ESP-IDF PowerShell" shortcut to get a pre-configured terminal.

---

## Part 2 — Configure the Firmware

Edit `esp32_firmware/config.h`:

```c
#define WIFI_SSID     "YourNetworkName"
#define WIFI_PASSWORD "YourWiFiPassword"
#define PC_IP         "192.168.1.100"   // IP of the PC running receiver.py
#define UDP_PORT      9000
```

---

## Part 3 — Build and Flash

```bash
cd bt-hid-bridge/esp32_firmware

# Set target (only needed once)
idf.py set-target esp32

# Build
idf.py build

# Flash (replace PORT with your serial port)
# macOS:  /dev/cu.usbserial-XXXX  or  /dev/cu.SLAB_USBtoUART
# Linux:  /dev/ttyUSB0
# Windows: COM3 (check Device Manager)
idf.py -p /dev/cu.usbserial-0001 flash monitor
```

The `monitor` command shows ESP32 serial output. Press `Ctrl+]` to exit.

---

## Part 4 — PC Receiver Setup

### Install Python dependencies

```bash
pip install pynput
# or
pip3 install pynput
```

### Configure the receiver

Edit `pc_receiver/config.py`:

```python
LISTEN_IP   = "0.0.0.0"   # listen on all interfaces
LISTEN_PORT = 9000
LOG_LEVEL   = "INFO"
```

### Run the receiver

```bash
cd bt-hid-bridge/pc_receiver
python receiver.py
```

#### Windows — No special permissions needed.

#### macOS — Accessibility permission required:
1. System Settings → Privacy & Security → Accessibility
2. Add Terminal (or your IDE) to the allowed list

#### Linux — May need `sudo` or uinput group membership:
```bash
sudo usermod -aG input $USER   # log out and back in
```

---

## Part 5 — Emergency Stop

Press **Ctrl + Shift + F12** at any time to stop all input injection.
Press **Ctrl + Shift + F11** to resume.

The receiver also accepts these UDP control messages:
```json
{"type":"control","cmd":"pause"}
{"type":"control","cmd":"resume"}
{"type":"control","cmd":"quit"}
```

---

## Part 6 — Verify Milestone 1

1. Flash the ESP32 — watch serial output, confirm "WiFi connected" and "Sending test events"
2. Run `python receiver.py` on the PC
3. Move cursor to an empty text area
4. You should see: simulated keypresses ('h', 'e', 'l', 'l', 'o') and mouse movements
5. Check receiver log for "Injecting" lines

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| ESP32 won't connect to WiFi | Double-check SSID/password in `config.h`; ensure 2.4 GHz band |
| Receiver gets no packets | Check `PC_IP` in `config.h` matches your PC's IP (`ipconfig` / `ip addr`) |
| macOS: no input injected | Add Terminal to Accessibility in System Settings |
| Windows firewall blocks UDP | Allow Python through Windows Defender Firewall |
| pynput import error | Run `pip install pynput` |
