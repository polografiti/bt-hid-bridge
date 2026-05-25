# bt-hid-bridge — Technical Plan

## Overview

This project turns an ESP32 into a Bluetooth HID Host that bridges a physical
keyboard and/or mouse over Wi-Fi to a remote PC. A Python listener on the PC
receives the HID events and injects them as real system input.

---

## 1. ESP32 Board Selection

| Board      | BT Classic | BLE   | Verdict |
|------------|-----------|-------|---------|
| ESP32      | ✅ Yes     | ✅ Yes | Full coverage |
| ESP32-S3   | ❌ No      | ✅ Yes | BLE HID only |
| **ESP32-C3** | ❌ No    | ✅ Yes | **Board in use — BLE only** |

**Board in use: ESP32-C3 Super Mini**
- Built-in USB-JTAG (no external CH340/CP2102 needed), port: `/dev/cu.usbmodem1101`
- Single-core RISC-V @ 160 MHz, 4 MB flash
- **BLE 5.0 only — no Bluetooth Classic (BR/EDR)**

**Implication:** this bridge only works with **BLE HID** peripherals. Classic BT
keyboards/mice (most pre-2018 hardware) are out of scope for this board.
BLE HID devices that work: Apple Magic Keyboard/Mouse, Logitech MX series,
most modern slim keyboards and mice marketed as "BLE" or "Bluetooth 5".

If Classic BT support is needed later, swapping in an **ESP32 classic** board is
the path — zero firmware logic changes, just re-target and add `esp_bt_hidh`.

---

## 2. Bluetooth HID Host — Feasibility

### Bluetooth Classic HID Host
- **NOT available on ESP32-C3.** Requires ESP32 classic.
- API would be `esp_bt_hidh` — documented for future board upgrade.

### BLE HID Host (active target)
- **API:** NimBLE host stack via `esp_nimble_hci` + `host/ble_hs.h` (ESP-IDF 5.x)
- NimBLE is preferred over Bluedroid on C3: smaller RAM footprint, better docs
- Scan → connect → discover GATT services → subscribe to HID Report characteristic
- HID reports delivered via GATT notification callback
- Standard BLE HID profile (0x1812) covers keyboard + mouse + consumer control

### ESP-IDF vs Arduino
- **ESP-IDF** is required: no BLE HID Host implementation exists in Arduino core.
- Use **ESP-IDF 5.1+**, target `esp32c3`, NimBLE stack.

---

## 3. Recommended Libraries / APIs

### ESP32-C3 (ESP-IDF 5.1+)
| Purpose | Component / API |
|---------|----------------|
| Wi-Fi | `esp_wifi`, `esp_netif` |
| BLE HID Host | NimBLE → `host/ble_hs.h`, `host/ble_gatt.h` |
| BLE scan/connect | `host/ble_gap.h` |
| NVS (config/pairing) | `nvs_flash` |
| UDP socket | POSIX `lwip/sockets.h` |
| FreeRTOS tasks | `freertos/FreeRTOS.h` |

### Python (PC Receiver)
| Purpose | Library |
|---------|---------|
| UDP listener | `socket` (stdlib) |
| Keyboard injection | `pynput.keyboard` |
| Mouse injection | `pynput.mouse` |
| Emergency stop hotkey | `pynput.keyboard.GlobalHotKeys` |
| Logging | `logging` (stdlib) |

---

## 4. Event Protocol

Simple JSON over UDP. One JSON object per datagram, newline-terminated.

```json
{"type":"key","key":"a","state":"down"}
{"type":"key","key":"a","state":"up"}
{"type":"key","key":"KEY_RETURN","state":"down"}
{"type":"mouse","dx":10,"dy":-4}
{"type":"mouse_button","button":"left","state":"down"}
{"type":"mouse_button","button":"left","state":"up"}
{"type":"scroll","dy":-1}
{"type":"control","cmd":"pause"}
{"type":"control","cmd":"resume"}
```

Key names use pynput `Key.*` names for special keys; single characters for
printable keys. This mapping is handled in the Python receiver.

UDP default port: **9000**

Future: WebSocket transport can be added alongside UDP without protocol changes —
the same JSON format works over both.

---

## 5. Milestone Plan

### Milestone 1 — Wi-Fi + UDP Test Loop (no BT)
**Goal:** Prove the full pipeline end-to-end before adding Bluetooth.

- ESP32 connects to Wi-Fi (SSID/pass in `config.h`)
- ESP32 sends simulated test HID events over UDP every 100 ms
- Python receiver listens on UDP, decodes JSON, injects via pynput
- Emergency stop hotkey (Ctrl+Shift+F12) halts injection
- Visible log output on both sides

Files:
```
esp32_firmware/main/main.c           — WiFi init + test event loop
esp32_firmware/main/wifi_manager.c/h — WiFi connect/reconnect logic
esp32_firmware/main/udp_sender.c/h   — UDP socket + send helpers
esp32_firmware/config.h              — SSID, password, PC IP, port
pc_receiver/receiver.py              — UDP listener main loop
pc_receiver/input_injector.py        — pynput keyboard + mouse injection
pc_receiver/config.py                — PC-side settings
```

### Milestone 2 — BLE HID Host
- Scan for and pair to a BLE HID mouse/keyboard
- Parse HID reports from BLE notifications
- Forward decoded events to Milestone 1 UDP sender
- Test: physical BLE mouse controls PC cursor

### Milestone 3 — Classic Bluetooth HID Host
- Add `esp_bt_hidh` alongside BLE host
- Pair to classic BT keyboard
- Parse HID keyboard reports → key codes
- Same UDP pipeline

### Milestone 4 — Reliability & Polish
- NVS-backed pairing cache (auto-reconnect to known devices)
- WebSocket transport option
- Pairing mode button (GPIO)
- Connection status LED
- Windows tray icon for PC receiver

---

## 6. Architecture Diagram

```
[ BT Keyboard ]──BT Classic──┐
                              ├──[ ESP32 HID Host ]──WiFi UDP──[ Python Receiver ]──[ pynput ]──> PC Input
[ BT Mouse    ]──BLE ────────┘
                               config.h                config.py
```

---

## 7. Risks and Alternatives

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Classic BT HID Host pairing complexity | Medium | Start with BLE (simpler API); add classic later |
| HID Report Descriptor parsing errors | Medium | Use `esp_hid_parser` helper in esp-idf or hardcode common keyboard/mouse report formats |
| UDP packet loss (local network) | Low | Retry critical events; use sequence numbers if needed |
| pynput permissions on macOS (Accessibility) | Medium | Document; Windows is primary target and needs no special permissions |
| ESP32 BT + WiFi coexistence | Low | ESP-IDF handles coexistence via `esp_coex`; use 2.4 GHz AP |
| Keyboard with non-standard HID reports | Low | Log raw reports for manual mapping |

---

## 8. ESP-IDF Setup (Quick Reference)

```bash
# Install ESP-IDF 5.1
mkdir -p ~/esp && cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && git checkout v5.1.2
./install.sh esp32
source export.sh

# Build Milestone 1
cd /path/to/bt-hid-bridge/esp32_firmware
idf.py set-target esp32
idf.py build
idf.py -p /dev/cu.usbserial-XXXX flash monitor
```
