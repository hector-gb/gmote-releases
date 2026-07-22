import time
import board
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# Press brings Meet to the front; release sends the shortcut. Holding the
# button longer gives Chrome more time to focus, so the user can watch Meet
# come front before letting go.
#
# MIN_FOCUS_S is the floor: a quick tap is padded out to this much delay so
# fast presses are no worse than the old fixed sleep. Set to 0 to test pure
# falling-edge (delay is then entirely how long the button is held).
MIN_FOCUS_S = 0.5

# ---------- Helpers ----------
def send_shortcut(*keys):
    kbd.send(*keys)
    kbd.release_all()

def bring_meet_front():
    send_shortcut(Keycode.CONTROL, Keycode.ALT, Keycode.COMMAND, Keycode.M)

# ---------- Buttons (active-high, internal pulldown) ----------
def setup_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.DOWN  # active-high
    return b

# ---------- Mapping (EDIT THIS) ----------
# Change pins or reorder freely without touching the scan loop.
mapping = [
    (board.D0, "Mic (Cmd+D)",            (Keycode.COMMAND, Keycode.D)),
    (board.D1, "Camera (Cmd+E)",         (Keycode.COMMAND, Keycode.E)),
    (board.D2, "Raise hand (Ctrl+Cmd+H)", (Keycode.CONTROL, Keycode.COMMAND, Keycode.H)),
    (board.D3, "Hang up (Cmd+W)",        (Keycode.COMMAND, Keycode.W)),
]

pins = [p for (p, _, _) in mapping]
names = [n for (_, n, _) in mapping]
combos = [k for (_, _, k) in mapping]
buttons = [setup_button(p) for p in pins]

# ---------- Debounce ----------
DEBOUNCE_S = 0.05
last_state = [False] * len(buttons)
last_change = [time.monotonic()] * len(buttons)
press_time = [0.0] * len(buttons)

time.sleep(1.0)
print("Ready:", ", ".join([f"{pins[i]} -> {names[i]}" for i in range(len(pins))]))

while True:
    now = time.monotonic()

    for i, b in enumerate(buttons):
        cur = b.value  # False=released, True=pressed

        if cur != last_state[i] and (now - last_change[i]) > DEBOUNCE_S:
            last_change[i] = now
            last_state[i] = cur

            if cur:  # pressed edge -> focus Meet, then wait for release
                press_time[i] = now
                print(f"{names[i]}: focusing Meet")
                bring_meet_front()
            else:  # released edge -> send the shortcut
                held = now - press_time[i]
                if held < MIN_FOCUS_S:
                    time.sleep(MIN_FOCUS_S - held)
                print(f"{names[i]}: sent (held {held * 1000:.0f} ms)")
                send_shortcut(*combos[i])

    time.sleep(0.005)
