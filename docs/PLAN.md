# bt-hid-bridge — Technical Plan

## Overview

This project turns an ESP32 into a Bluetooth HID Host that bridges a physical
keyboard and/or mouse over Wi-Fi to a remote PC. A Python listener on the PC
receives the HID events and injects them as real system input.

---

## 1. ESP32 Board Selection

| Board      | BT Classic | BLE   | Verdict |
|------------|-----------|-------|---------|
| ESP32      | ✅ Yes     | ✅ Yes | **Best choice** |
| ESP32-S3   | ❌ No      | ✅ Yes | BLE HID only |
| ESP32-C3   | ❌ No      | ✅ Yes | BLE HID only, single-core |

**Recommendation: ESP32 classic (ESP32-WROOM-32 or ESP32-DevKitC).**

Reasons:
- Supports both Bluetooth Classic (BR/EDR) and BLE in a single chip.
- Most commercial keyboards and mice use Bluetooth Classic HID (not BLE).
- Modern gaming peripherals may use BLE or dual-mode — ESP32 handles both.
- ESP32-S3 and C3 are BLE-only, which would exclude most keyboards.

---

## 2. Bluetooth HID Host — Feasibility

### Bluetooth Classic HID Host
- **API:** `esp_bt_hidh` in ESP-IDF (component `bt`, profile `HH`)
- Available since ESP-IDF 4.x, stable in ESP-IDF 5.x
- Pairs and connects to HID Class devices (keyboards, mice, gamepads)
- Receives raw HID reports via callback
- Requires parsing HID Report Descriptors to decode key codes / axes

### BLE HID Host
- **API:** `esp_ble_hidh` in ESP-IDF 5.0+
- Connects to BLE HID peripherals (many modern BT mice, some keyboards)
- Simpler report structure for standard keyboard/mouse profiles
- GATT-based; reports delivered via notification callbacks

### Strategy
Start with **BLE HID Host** (simpler API, well-documented in ESP-IDF examples).
Add **Classic BT HID Host** in a later milestone for legacy keyboard support.
Both can coexist on the ESP32; they share the same `esp_hidh` abstraction layer
in ESP-IDF 5.0+, which wraps both transports under one callback interface.

### ESP-IDF vs Arduino
- **ESP-IDF** is the correct choice: the `esp_hidh` host API does not exist in
  the Arduino core. Arduino `BleKeyboard` etc. are *device* (peripheral) libs.
- Use **ESP-IDF 5.1 or later** for the unified `esp_hidh` with dual-mode support.

---

## 3. Recommended Libraries / APIs

### ESP32 (ESP-IDF)
| Purpose | Component / API |
|---------|----------------|
| Wi-Fi | `esp_wifi`, `esp_netif` |
| BT Classic HID Host | `bt` → `esp_bt_hidh_api.h` |
| BLE HID Host | `bt` → `esp_ble_hidh.h` |
| Unified HID Host | `esp_hidh` (ESP-IDF 5.0+) |
| NVS (config storage) | `nvs_flash` |
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
