#!/usr/bin/env python3
"""
receiver.py — UDP listener for bt-hid-bridge Milestone 1.

Receives JSON HID events from the ESP32 over UDP and injects them as real
keyboard/mouse input via pynput.

Usage:
    python receiver.py

Emergency stop : Ctrl + Shift + F12
Resume         : Ctrl + Shift + F11
"""

import json
import logging
import socket
import sys
import threading

from pynput import keyboard

import config
from input_injector import InputInjector

# ─── Logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("receiver")

# ─── Global state ─────────────────────────────────────────────────────────────

_paused   = False
_running  = True
_injector = InputInjector()
_lock     = threading.Lock()


def set_paused(state: bool) -> None:
    global _paused
    with _lock:
        _paused = state
    status = "PAUSED — input injection suspended" if state else "RESUMED — input injection active"
    log.info("─── %s ───", status)
    print(f"\n{'⏸' if state else '▶'}  {status}\n")


def stop_receiver() -> None:
    global _running
    log.info("Emergency stop triggered — shutting down")
    print("\n🛑  Emergency stop — receiver is shutting down\n")
    _running = False


# ─── Hotkey listeners ─────────────────────────────────────────────────────────

def start_hotkey_listener() -> None:
    hotkeys = {
        config.HOTKEY_STOP:   lambda: stop_receiver(),
        config.HOTKEY_RESUME: lambda: set_paused(False),
    }
    # Ctrl+Shift+F12 → stop; Ctrl+Shift+F11 → resume
    # We also map a pause hotkey: Ctrl+Shift+F10
    hotkeys["<ctrl>+<shift>+<f10>"] = lambda: set_paused(True)

    listener = keyboard.GlobalHotKeys(hotkeys)
    listener.daemon = True
    listener.start()
    log.info("Hotkeys registered: stop=%s  pause=Ctrl+Shift+F10  resume=%s",
             config.HOTKEY_STOP, config.HOTKEY_RESUME)


# ─── Event processing ─────────────────────────────────────────────────────────

def process_packet(data: bytes, addr: tuple) -> None:
    global _paused

    try:
        text = data.decode("utf-8").strip()
        event = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        log.warning("Bad packet from %s:%d — %s", addr[0], addr[1], e)
        return

    etype = event.get("type")

    # Control messages are always processed even when paused
    if etype == "control":
        cmd = event.get("cmd", "")
        if cmd == "pause":
            set_paused(True)
        elif cmd == "resume":
            set_paused(False)
        elif cmd == "quit":
            stop_receiver()
        else:
            log.warning("Unknown control command: %r", cmd)
        return

    with _lock:
        is_paused = _paused

    if is_paused:
        log.debug("Dropped (paused): %s", text)
        return

    log.debug("Dispatching from %s: %s", addr[0], text)
    try:
        _injector.dispatch(event)
    except Exception as e:
        log.error("Injection error: %s — event: %s", e, text)


# ─── Main UDP loop ────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  bt-hid-bridge PC Receiver  —  Milestone 1")
    print("=" * 60)
    print(f"  Listening on  UDP {config.LISTEN_IP}:{config.LISTEN_PORT}")
    print(f"  Stop          {config.HOTKEY_STOP}")
    print(f"  Pause         Ctrl+Shift+F10")
    print(f"  Resume        {config.HOTKEY_RESUME}")
    print("=" * 60)
    print()

    start_hotkey_listener()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((config.LISTEN_IP, config.LISTEN_PORT))
    except OSError as e:
        log.error("Cannot bind to %s:%d — %s", config.LISTEN_IP, config.LISTEN_PORT, e)
        sys.exit(1)

    sock.settimeout(config.SOCKET_TIMEOUT)
    log.info("Socket bound — waiting for ESP32…")

    packets_received = 0
    last_sender = None

    while _running:
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break

        if addr != last_sender:
            last_sender = addr
            log.info("First packet from %s:%d", addr[0], addr[1])
            print(f"  Connected: ESP32 at {addr[0]}:{addr[1]}\n")

        packets_received += 1
        process_packet(data, addr)

    sock.close()
    log.info("Receiver stopped. Total packets received: %d", packets_received)
    print(f"\nReceiver stopped. Packets received: {packets_received}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
