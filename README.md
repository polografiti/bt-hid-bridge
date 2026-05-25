# bt-hid-bridge

Turns an **ESP32** into a Bluetooth HID Host that bridges a physical keyboard
and mouse over Wi-Fi to a remote PC. A Python listener on the PC receives the
events and injects them as real system input.

```
[ BT Keyboard ]──BT Classic──┐
                              ├──[ ESP32 ]──Wi-Fi UDP──[ Python Receiver ]──[ pynput ]──> PC
[ BT Mouse    ]──BLE ────────┘
```

## Repository Structure

```
bt-hid-bridge/
├── esp32_firmware/         ESP-IDF 5.x firmware project
│   ├── main/
│   │   ├── main.c          Entry point + test event loop (Milestone 1)
│   │   ├── wifi_manager.c  Wi-Fi connection logic
│   │   ├── udp_sender.c    UDP socket + send helpers
│   │   └── CMakeLists.txt
│   ├── CMakeLists.txt
│   ├── sdkconfig.defaults  Build configuration defaults
│   └── config.h            Wi-Fi SSID/password, PC IP, port
│
├── pc_receiver/            Python UDP listener + input injector
│   ├── receiver.py         Main loop — UDP → dispatch
│   ├── input_injector.py   pynput keyboard/mouse injection
│   ├── config.py           Listen IP, port, hotkeys
│   └── requirements.txt
│
└── docs/
    ├── PLAN.md             Technical plan, architecture, milestones
    └── SETUP.md            Full setup instructions
```

## Quick Start

1. Edit `esp32_firmware/config.h` with your Wi-Fi credentials and PC IP.
2. Build and flash: `idf.py build && idf.py -p PORT flash monitor`
3. On the PC: `pip install pynput && python pc_receiver/receiver.py`

See [docs/SETUP.md](docs/SETUP.md) for complete instructions.

## Milestones

| # | Description | Status |
|---|-------------|--------|
| 1 | Wi-Fi + UDP test loop — simulated events injected on PC | ✅ Done |
| 2 | BLE HID Host — real BLE mouse/keyboard → PC | 🔜 Next |
| 3 | Classic BT HID Host — legacy keyboards | 🔜 Planned |
| 4 | NVS pairing cache, WebSocket transport, tray icon | 🔜 Planned |

## Safety

- **Emergency stop:** `Ctrl + Shift + F12` — halts all injection immediately
- **Pause:** `Ctrl + Shift + F10`
- **Resume:** `Ctrl + Shift + F11`
- All events are logged to stdout with timestamps

## Requirements

- ESP32 classic (WROOM-32 or DevKitC) — **not** S3 or C3 (no Classic BT)
- ESP-IDF 5.1+
- Python 3.8+ with `pynput`
- 2.4 GHz Wi-Fi network
