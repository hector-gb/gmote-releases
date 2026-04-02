import time
import board
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# ---------- Helpers ----------
def send_shortcut(*keys):
    kbd.send(*keys)
    kbd.release_all()

def bring_meet_front():
    # Your macOS Quick Action shortcut
    send_shortcut(Keycode.CONTROL, Keycode.COMMAND, Keycode.M)
    time.sleep(0.5)  # let macOS/Chrome focus

# ---------- Buttons (active-high, internal pulldown) ----------
def setup_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.DOWN  # active-high
    return b

# ---------- Actions ----------
def act_meet_front():
    print("Meet front")
    bring_meet_front()

def act_mic():
    print("Mic (Cmd+D)")
    bring_meet_front()
    send_shortcut(Keycode.COMMAND, Keycode.D)

def act_cam():
    print("Camera (Cmd+E)")
    bring_meet_front()
    send_shortcut(Keycode.COMMAND, Keycode.E)

def act_hand():
    print("Raise hand (Ctrl+Cmd+H)")
    bring_meet_front()
    send_shortcut(Keycode.CONTROL, Keycode.COMMAND, Keycode.H)

def act_hang_up():
    print("Hang up Meeting ()")
    bring_meet_front()
    send_shortcut(Keycode.COMMAND, Keycode.W)

# ---------- Mapping (EDIT THIS) ----------
# Change pins or reorder freely without touching the scan loop.
mapping = [
    (board.D0, act_mic),
    (board.D1, act_cam),
    (board.D2, act_hand),
    (board.D3, act_hang_up),
]

pins = [p for (p, _) in mapping]
actions = [fn for (_, fn) in mapping]
buttons = [setup_button(p) for p in pins]

# ---------- Debounce ----------
DEBOUNCE_S = 0.05
last_state = [False] * len(buttons)
last_change = [time.monotonic()] * len(buttons)

time.sleep(1.0)
print("Ready:", ", ".join([f"{pins[i]} -> {actions[i].__name__}" for i in range(len(pins))]))

while True:
    now = time.monotonic()

    for i, b in enumerate(buttons):
        cur = b.value  # False=released, True=pressed

        if cur != last_state[i] and (now - last_change[i]) > DEBOUNCE_S:
            last_change[i] = now
            last_state[i] = cur

            if cur:  # pressed edge
                actions[i]()

    time.sleep(0.005)
