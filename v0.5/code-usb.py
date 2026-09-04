import time
import board
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# The board no longer sends Meet's shortcuts itself. Each button just fires one
# obscure hotkey that identifies WHICH button was pressed; the Mac-side Quick
# Action runs findmeet.sh, which focuses Meet, waits until Chrome is actually
# frontmost with Meet active, and only then sends the real shortcut.
#
# That kills the old race: there is no longer a blind delay here that has to be
# long enough for Chrome to finish focusing.

# ---------- Helpers ----------
def send_shortcut(*keys):
    kbd.send(*keys)
    kbd.release_all()

# ---------- Buttons (active-high, internal pulldown) ----------
def setup_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.DOWN  # active-high
    return b

# ---------- Mapping (EDIT THIS) ----------
# Each hotkey must match the key_equivalent registered by gmote-installer.sh:
#   mic ^~$@m   camera ^~$@n   hand ^~$@j   leave ^~$@k
#
# Four modifiers (Ctrl+Opt+Shift+Cmd) because three-modifier combos collide with
# real apps — ^~@n was already taken by VS Code.
MOD = (Keycode.CONTROL, Keycode.ALT, Keycode.SHIFT, Keycode.COMMAND)

mapping = [
    (board.D0, "Mic",        MOD + (Keycode.M,)),
    (board.D1, "Camera",     MOD + (Keycode.N,)),
    (board.D2, "Raise hand", MOD + (Keycode.J,)),
    (board.D3, "Leave call", MOD + (Keycode.K,)),
]

pins = [p for (p, _, _) in mapping]
names = [n for (_, n, _) in mapping]
combos = [k for (_, _, k) in mapping]
buttons = [setup_button(p) for p in pins]

# ---------- Debounce ----------
DEBOUNCE_S = 0.05
last_state = [False] * len(buttons)
last_change = [time.monotonic()] * len(buttons)

time.sleep(1.0)
print("Ready:", ", ".join([f"{pins[i]} -> {names[i]}" for i in range(len(pins))]))

while True:
    now = time.monotonic()

    for i, b in enumerate(buttons):
        cur = b.value  # False=released, True=pressed

        if cur != last_state[i] and (now - last_change[i]) > DEBOUNCE_S:
            last_change[i] = now
            last_state[i] = cur

            if cur:  # pressed edge -> tell the Mac which button this was
                print(f"{names[i]}: sent hotkey")
                send_shortcut(*combos[i])

    time.sleep(0.005)
