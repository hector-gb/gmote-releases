import time
import board
import digitalio

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# ---------- Buttons (active-high, internal pulldown) ----------
def setup_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.DOWN
    return b

# ---------- Transport selection ----------
# Default: BLE.  Hold D3 at boot → USB HID instead.
#
# D3 (not D4): only D0-D3 have keyswitches wired — see schematics/1x4b. D4 is
# broken out on the XIAO DIP but nothing connects to it, so it always read low
# and USB mode was unreachable. D0 is taken by boot.py's storage remount.
# Reading D3 here is independent of its runtime role (Leave call).
_mode_btn = setup_button(board.D3)
time.sleep(0.1)  # let pin settle
USE_BLE = not _mode_btn.value
_mode_btn.deinit()
print("D3 at boot:", not USE_BLE, "→ Transport:", "USB" if not USE_BLE else "BLE")

if USE_BLE:
    import adafruit_ble
    from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
    from adafruit_ble.services.standard.hid import HIDService

    hid = HIDService()
    ble = adafruit_ble.BLERadio()
    ble.name = "GMote"
    advertisement = ProvideServicesAdvertisement(hid)
    advertisement.appearance = 961  # HID keyboard

    kbd = Keyboard(hid.devices)
    print("Transport: BLE")
else:
    import usb_hid
    kbd = Keyboard(usb_hid.devices)
    print("Transport: USB")

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

def ble_advertise():
    print("BLE: advertising...")
    ble.start_advertising(advertisement)
    while not ble.connected:
        time.sleep(0.1)
    ble.stop_advertising()
    print("BLE: connected")

# BLE bond clearing lives in boot.py (hold D1 at boot) — at runtime every button
# already sends its own shortcut on press, so a hold gesture here would fire that
# shortcut before the hold completed.

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
last_state  = [False] * len(buttons)
last_change = [time.monotonic()] * len(buttons)

if USE_BLE:
    ble_advertise()

time.sleep(1.0)
print("Ready:", ", ".join([f"{pins[i]} -> {names[i]}" for i in range(len(pins))]))

# ---------- Main loop ----------
while True:
    if USE_BLE:
        if not ble.connected:
            ble_advertise()

    now = time.monotonic()
    for i, b in enumerate(buttons):
        cur = b.value

        if cur != last_state[i] and (now - last_change[i]) > DEBOUNCE_S:
            last_change[i] = now
            last_state[i]  = cur

            if cur:  # pressed edge -> tell the Mac which button this was
                print(f"{names[i]}: sent hotkey")
                send_shortcut(*combos[i])

    time.sleep(0.005)
