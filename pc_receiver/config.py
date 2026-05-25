# ─── PC Receiver Configuration ────────────────────────────────────────────────

LISTEN_IP   = "0.0.0.0"   # bind to all interfaces
LISTEN_PORT = 9000

# How long to wait on socket.recvfrom() before checking state (seconds)
SOCKET_TIMEOUT = 0.5

# Logging: DEBUG shows every injected event; INFO shows connect/control events
LOG_LEVEL = "INFO"

# Emergency stop / resume hotkeys (pynput format)
HOTKEY_STOP   = "<ctrl>+<shift>+<f12>"
HOTKEY_RESUME = "<ctrl>+<shift>+<f11>"

# Mouse movement scaling factor (1.0 = raw delta from ESP32)
MOUSE_SPEED = 1.0
