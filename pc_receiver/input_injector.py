"""
input_injector.py — translates JSON HID events into real system input via pynput.

Supported event types:
  key          {"type":"key","key":"a","state":"down"|"up"}
  mouse        {"type":"mouse","dx":int,"dy":int}
  mouse_button {"type":"mouse_button","button":"left"|"right"|"middle","state":"down"|"up"}
  scroll       {"type":"scroll","dy":int}
"""

import logging
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse    import Button, Controller as MouseController
import config

log = logging.getLogger(__name__)

# ─── Special key name → pynput Key mapping ────────────────────────────────────
_KEY_MAP = {
    "KEY_RETURN":    Key.enter,
    "KEY_ENTER":     Key.enter,
    "KEY_SPACE":     Key.space,
    "KEY_BACKSPACE": Key.backspace,
    "KEY_DELETE":    Key.delete,
    "KEY_TAB":       Key.tab,
    "KEY_ESC":       Key.esc,
    "KEY_UP":        Key.up,
    "KEY_DOWN":      Key.down,
    "KEY_LEFT":      Key.left,
    "KEY_RIGHT":     Key.right,
    "KEY_CTRL":      Key.ctrl,
    "KEY_SHIFT":     Key.shift,
    "KEY_ALT":       Key.alt,
    "KEY_CAPS":      Key.caps_lock,
    "KEY_F1":        Key.f1,
    "KEY_F2":        Key.f2,
    "KEY_F3":        Key.f3,
    "KEY_F4":        Key.f4,
    "KEY_F5":        Key.f5,
    "KEY_F6":        Key.f6,
    "KEY_F7":        Key.f7,
    "KEY_F8":        Key.f8,
    "KEY_F9":        Key.f9,
    "KEY_F10":       Key.f10,
    "KEY_F11":       Key.f11,
    "KEY_F12":       Key.f12,
    "KEY_WIN":       Key.cmd,
    "KEY_HOME":      Key.home,
    "KEY_END":       Key.end,
    "KEY_PGUP":      Key.page_up,
    "KEY_PGDN":      Key.page_down,
    "KEY_INSERT":    Key.insert,
    "KEY_PRTSCRN":   Key.print_screen,
}

_BUTTON_MAP = {
    "left":   Button.left,
    "right":  Button.right,
    "middle": Button.middle,
}


class InputInjector:
    def __init__(self):
        self._kb    = KeyboardController()
        self._mouse = MouseController()

    # ─── Public dispatch ──────────────────────────────────────────────────────

    def dispatch(self, event: dict) -> None:
        etype = event.get("type")
        if   etype == "key":          self._handle_key(event)
        elif etype == "mouse":        self._handle_mouse(event)
        elif etype == "mouse_button": self._handle_mouse_button(event)
        elif etype == "scroll":       self._handle_scroll(event)
        else:
            log.warning("Unknown event type: %s", etype)

    # ─── Handlers ─────────────────────────────────────────────────────────────

    def _handle_key(self, event: dict) -> None:
        raw   = event.get("key", "")
        state = event.get("state", "down")
        key   = self._resolve_key(raw)
        if key is None:
            log.warning("Unresolvable key: %r", raw)
            return

        log.debug("Injecting key %s %s", raw, state)
        if state == "down":
            self._kb.press(key)
        else:
            self._kb.release(key)

    def _handle_mouse(self, event: dict) -> None:
        dx = int(event.get("dx", 0) * config.MOUSE_SPEED)
        dy = int(event.get("dy", 0) * config.MOUSE_SPEED)
        if dx or dy:
            log.debug("Injecting mouse move dx=%d dy=%d", dx, dy)
            self._mouse.move(dx, dy)

    def _handle_mouse_button(self, event: dict) -> None:
        btn_name = event.get("button", "left")
        state    = event.get("state", "down")
        button   = _BUTTON_MAP.get(btn_name)
        if button is None:
            log.warning("Unknown mouse button: %r", btn_name)
            return

        log.debug("Injecting mouse button %s %s", btn_name, state)
        if state == "down":
            self._mouse.press(button)
        else:
            self._mouse.release(button)

    def _handle_scroll(self, event: dict) -> None:
        dy = int(event.get("dy", 0))
        if dy:
            log.debug("Injecting scroll dy=%d", dy)
            self._mouse.scroll(0, dy)

    # ─── Key resolution ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_key(raw: str):
        if raw in _KEY_MAP:
            return _KEY_MAP[raw]
        if len(raw) == 1:
            return raw   # single printable character
        return None
