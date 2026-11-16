#!/usr/bin/env python3
"""Read a Wii Balance Board on Arch Linux and relay it to the Windows PC.

Control scheme:
  march in place        -> walk forward (W)
  march briskly         -> sprint (W + Shift)
  lean back             -> walk backward (S)
  lean left / right     -> strafe left / right (A / D)
  twist shoulders L/R   -> camera pans left / right, continuously while twisted

Forward is driven by *stepping*, which shows up as an oscillation in total weight across all four
sensors. Leaning alone barely changes total weight, only the balance between sensors, so the two
are cleanly separable.

The laptop is the sensor because this PC's Bluetooth adapter never hears the board.

Setup on the laptop:
    sudo pacman -S python-evdev
    sudo modprobe hid-wiimote        # without it the board drops ~3 s after connecting
    python3 board_sender_arch.py --list
    python3 board_sender_arch.py --host 192.168.2.12
"""

import argparse
import json
import socket
import sys
import time
from collections import deque

try:
    import evdev
    from evdev import ecodes
except ImportError:
    sys.exit("python-evdev missing: sudo pacman -S python-evdev")

DEFAULT_PORT = 45454


def find_board(pattern):
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if pattern.lower() in dev.name.lower():
            return dev
    return None


def abs_axes(dev):
    return [code for code, info in dev.capabilities().get(ecodes.EV_ABS, [])]


class MarchDetector:
    """Count steps-per-second from the oscillation of total weight."""

    def __init__(self, window=3.0):
        self.window = window
        self.samples = deque()
        self.steps = deque()
        self.armed = True
        self.amplitude = 0.0

    def push(self, now, total):
        self.samples.append((now, total))
        while self.samples and now - self.samples[0][0] > 4.0:
            self.samples.popleft()

        values = [v for _, v in self.samples]
        if len(values) < 8:
            return

        low, high = min(values), max(values)
        mid = (low + high) / 2.0
        self.amplitude = (high - low) / 2.0
        if self.amplitude < 2.0:
            return

        band = self.amplitude * 0.35
        if self.armed and total > mid + band:
            self.steps.append(now)
            self.armed = False
        elif not self.armed and total < mid - band:
            self.armed = True

        while self.steps and now - self.steps[0] > self.window:
            self.steps.popleft()

    def cadence(self):
        if not self.steps:
            return 0.0
        return len(self.steps) / self.window


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", help="Windows PC address")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--match", default="wii", help="substring of the device name")
    ap.add_argument("--deadzone", type=float, default=0.18, help="tilt deadzone for back/left/right")
    ap.add_argument("--walk-cadence", type=float, default=1.0, help="steps per second to start moving")
    ap.add_argument("--sprint-cadence", type=float, default=2.4, help="steps per second to sprint")
    ap.add_argument("--swap-lr", action="store_true", help="flip left/right if strafing is inverted")
    ap.add_argument("--swap-fb", action="store_true", help="flip front/back if leaning is inverted")
    ap.add_argument("--twist-deadzone", type=float, default=0.15,
                    help="how much shoulder twist starts a camera pan")
    ap.add_argument("--swap-twist", action="store_true", help="flip the camera pan direction")
    ap.add_argument("--list", action="store_true", help="list input devices and exit")
    args = ap.parse_args()

    if args.list:
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            axes = abs_axes(dev)
            names = [ecodes.ABS.get(c, c) for c in axes]
            print(f"{path}  {dev.name}  axes={names}")
        return

    if not args.host:
        sys.exit("--host is required (the Windows PC's IP)")

    board = find_board(args.match)
    if board is None:
        sys.exit(f"no input device matching '{args.match}' - try --list")

    codes = sorted(abs_axes(board))
    print(f"board: {board.name} ({board.path})")
    print(f"sensor axes: {[ecodes.ABS.get(c, c) for c in codes]}")
    if len(codes) < 4:
        sys.exit("need four sensor axes (TL, TR, BL, BR); this device reported "
                 f"{len(codes)} - wrong device, or hid-wiimote is not driving it")

    tl, tr, bl, br = codes[0], codes[1], codes[2], codes[3]
    state = {c: 0 for c in codes}

    print("stand still for 2 s (taring)...")
    start = time.time()
    baselines = {c: [] for c in codes}
    for event in board.read_loop():
        if event.type == ecodes.EV_ABS and event.code in baselines:
            baselines[event.code].append(event.value)
        if time.time() - start > 2:
            break
    zero = {c: (sum(v) / len(v) if v else 0) for c, v in baselines.items()}
    print(f"zero: { {ecodes.ABS.get(c, c): round(v, 1) for c, v in zero.items()} }")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (args.host, args.port)
    march = MarchDetector()

    print(f"sending to {dest[0]}:{dest[1]} - ctrl+c to stop")
    print("march in place to walk, faster to sprint, lean back/left/right to move that way")

    last_send = 0.0
    last_report = 0.0
    for event in board.read_loop():
        if event.type != ecodes.EV_ABS or event.code not in state:
            continue
        state[event.code] = event.value

        now = time.time()
        if now - last_send < 0.02:
            continue
        last_send = now

        total = sum(state[c] for c in codes)
        if total <= 0:
            continue
        march.push(now, total)

        lr = ((state[tl] + state[bl]) - (state[tr] + state[br])) / total
        fb = ((state[tl] + state[tr]) - (state[bl] + state[br])) / total
        twist = ((state[tl] + state[br]) - (state[tr] + state[bl])) / total
        if args.swap_lr:
            lr = -lr
        if args.swap_fb:
            fb = -fb
        if args.swap_twist:
            twist = -twist
        turn = twist if abs(twist) > args.twist_deadzone else 0.0

        cadence = march.cadence()
        walking = cadence >= args.walk_cadence
        sprint = cadence >= args.sprint_cadence
        back = fb < -args.deadzone
        left = lr > args.deadzone
        right = lr < -args.deadzone

        packet = json.dumps({
            "f": int(walking), "sp": int(sprint),
            "b": int(back), "l": int(left), "r": int(right),
            "y": round(turn, 3),
        }).encode()
        sock.sendto(packet, dest)

        if now - last_report > 1.0:
            last_report = now
            print(f"  cadence={cadence:4.1f}/s amp={march.amplitude:6.1f} lr={lr:+.2f} fb={fb:+.2f}"
                  f" twist={twist:+.2f} -> walk={int(walking)} sprint={int(sprint)} back={int(back)}"
                  f" left={int(left)} right={int(right)} turn={turn:+.2f}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped")
