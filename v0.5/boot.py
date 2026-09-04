import board

import digitalio
import storage
btn = digitalio.DigitalInOut(board.D0)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.DOWN
if not btn.value:
    storage.remount('/', False)
btn.deinit()
