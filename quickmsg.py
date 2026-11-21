# Quick (canned) messages sent with the device button.
#
# Button usage:
#   short press              -> switch view (original FreakWAN behavior)
#   long press (>= 0.8s)     -> enter selection, or go to the next message
#   short press in selection -> send the selected message
#   no press for 10s         -> selection canceled
#   any press during the screen saver only wakes the display
#
# Messages are stored one per line in quickmsg.txt and managed with !qm:
#   !qm                     list
#   !qm add <text>          add (optional "label|text": the OLED shows the
#                           short label, the full text is sent)
#   !qm del <n>             delete message n
#   !qm send <n>            send message n
#   !qm reset               restore the default messages

import uasyncio as asyncio
import time
from clictrl import CommandsController

FILENAME = "quickmsg.txt"
DEFAULTS = ["OK", "無事です", "助けが必要です"]
LONG_MS = 800
TIMEOUT_MS = 10000

def split_entry(entry):
    if '|' in entry:
        label, text = entry.split('|', 1)
        return label.strip(), text.strip()
    return entry, entry

class QuickMsg:
    def __init__(self, fw, pin):
        self.fw = fw
        self.pin = pin
        self.selecting = False
        self.idx = 0
        self.deadline = 0
        self.load()

    def load(self):
        try:
            with open(FILENAME, "rb") as f:
                lines = f.read().decode("utf-8").split("\n")
            self.items = [l for l in lines if l.strip()]
        except OSError:
            self.items = list(DEFAULTS)

    def save(self):
        with open(FILENAME, "wb") as f:
            f.write("\n".join(self.items).encode("utf-8"))

    def show(self, line):
        self.fw.serial_log("[qm] " + line)
        if self.fw.display:
            self.fw.switch_view(self.fw.scroller)
            self.fw.scroller.print(line)
            self.fw.refresh_view()

    def send(self, i):
        label, text = split_entry(self.items[i])
        self.fw.cmdctrl.exec_user_command(text, self.fw.reply_to_serial)

    # If the OLED screen saver is on (only the battery icon is shown),
    # a press just wakes the display up and is otherwise ignored.
    # Without this, a short press switched views behind the screen saver
    # and the device looked frozen.
    def wake(self):
        sc = self.fw.scroller
        if not self.fw.display or sc is None: return False
        sc.update_screensaver_state()
        if sc.state != sc.StateSaver: return False
        sc.last_update = time.time()
        self.fw.switch_view(sc)
        return True

    def long_press(self):
        if self.wake(): return
        if not self.items:
            self.show("No quick msgs (!qm add)")
            return
        if self.selecting:
            self.idx = (self.idx + 1) % len(self.items)
        else:
            self.selecting = True
            self.idx = 0
        label, text = split_entry(self.items[self.idx])
        self.show("[%d/%d] %s ?" % (self.idx + 1, len(self.items), label))
        self.deadline = time.ticks_add(time.ticks_ms(), TIMEOUT_MS)

    def short_press(self):
        if self.wake(): return
        if self.selecting:
            self.selecting = False
            self.send(self.idx)
        else:
            self.fw.button_0_pressed(None)

    async def run(self):
        down_since = None
        long_fired = False
        while True:
            await asyncio.sleep_ms(20)
            now = time.ticks_ms()
            pressed = self.pin.value() == 0
            if pressed:
                if down_since is None:
                    down_since = now
                    long_fired = False
                elif not long_fired and time.ticks_diff(now, down_since) >= LONG_MS:
                    long_fired = True
                    self.long_press()
            elif down_since is not None:
                if not long_fired and time.ticks_diff(now, down_since) >= 30:
                    self.short_press()
                down_since = None
            if self.selecting and time.ticks_diff(now, self.deadline) > 0:
                self.selecting = False
                self.show("canceled")

# The !qm command, attached to FreakWAN's command controller.
def cmd_qm(self, argv, argc, send_reply):
    qm = self.fw.quickmsg
    sub = argv[1] if argc > 1 else "list"
    if sub == "list":
        if not qm.items:
            send_reply("No quick messages. Use: !qm add <text>")
        for i, e in enumerate(qm.items):
            label, text = split_entry(e)
            send_reply("%d: %s" % (i + 1, text if label == text else label + " | " + text))
    elif sub == "add" and argc > 2:
        qm.items.append(" ".join(argv[2:]))
        qm.save()
        send_reply("Added as %d" % len(qm.items))
    elif sub in ("del", "send") and argc == 3:
        try:
            i = int(argv[2]) - 1
            assert 0 <= i < len(qm.items)
        except Exception:
            send_reply("No such quick message: " + argv[2])
            return True
        if sub == "del":
            removed = qm.items.pop(i)
            qm.save()
            send_reply("Deleted: " + removed)
        else:
            qm.send(i)
    elif sub == "reset":
        qm.items = list(DEFAULTS)
        qm.save()
        send_reply("Quick messages reset to defaults")
    else:
        return False
    return True

def install(fw, pin):
    fw.quickmsg = QuickMsg(fw, pin)
    CommandsController.cmd_qm = cmd_qm
    asyncio.create_task(fw.quickmsg.run())
