import board

import digitalio
import storage


def held(pin):
    """True if the button on `pin` is held at boot (active-high, pulldown)."""
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.DOWN
    v = b.value
    b.deinit()
    return v


# D0 held → skip the remount, leaving the drive writable by the host so code.py
# can be copied over. Otherwise CircuitPython takes write access and the drive
# is read-only to the Mac.
if not held(board.D0):
    storage.remount('/', False)

# D1 held → erase BLE bonds so the gmote can pair with a different computer.
#
# Done at boot rather than in code.py: while running, every button already sends
# its own shortcut on press, so a hold-to-reset gesture there would fire that
# shortcut first. At boot the buttons have no runtime role, so there's no clash.
#
# NOTE: this only clears the board's side. If the host still holds a stale bond,
# also remove the gmote there (System Settings → Bluetooth → Forget), or
# reconnection will still fail.
if held(board.D1):
    import _bleio

    _bleio.adapter.erase_bonding()
    print("BLE: bonds erased — ready to pair")
