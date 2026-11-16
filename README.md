# wiimote-relay

Driving Elden Ring on a Windows PC with a Wii Remote, a Nunchuk and a Wii Balance Board.

## Why two machines

The PC's Bluetooth adapter never hears the balance board: its cached entry reports signal strength 0 and a five-minute watcher saw no advertising at all. The Arch laptop pairs with it fine, so the laptop is the sensor and the PC is the output.

    board --BT--> Arch laptop (tools/board_sender_arch.py)
                     |  UDP 45454, JSON, 50 Hz
                     v
                 Windows PC (tools/board_relay_receiver.py) --> SendInput keys --> game

## Controls

| Body / button | Result |
| --- | --- |
| march in place | walk forward (W) |
| march briskly | sprint (W + Shift) |
| lean back | walk backward (S) |
| lean left / right | strafe (A / D) |
| twist shoulders | camera pans continuously (relative mouse) |

Wiimote: A = roll/sprint, 1 = interact, B = jump, 2 = heavy attack, + = recentre camera/lock-on, HOME = menu, minus = unused. Nunchuk: C = flask, Z = light attack.

## Laptop setup

    git clone https://github.com/Kalabuna156/wiimote-relay.git
    cd wiimote-relay
    sudo pacman -S python-evdev
    sudo modprobe hid-wiimote        # without this the board connects then drops after ~3 s
    python3 tools/board_sender_arch.py --list
    python3 tools/board_sender_arch.py --host 192.168.2.12

`git pull` to get updates. Stand still for the 2 s tare.

## Wire format

One UDP datagram per update on port 45454:

    {"f": 1, "sp": 0, "b": 0, "l": 0, "r": 0, "y": 0.0}

f forward, sp sprint, b back, l left, r right, y camera turn rate -1..1. Missing fields are treated as 0, so an older sender still works.

## What to check when it feels wrong

The sender prints a line per second: cadence, amp, lr, fb, twist.

| do this | expect |
| --- | --- |
| stand still | cadence 0, lr/fb near 0 |
| march | cadence above 1.0 |
| march faster | cadence above 2.4 |
| lean left/right | left=1 or right=1 |
| lean back | back=1 |
| twist | twist above 0.15 |

Adjust with --deadzone, --walk-cadence, --sprint-cadence, --twist-deadzone, --swap-lr, --swap-fb, --swap-twist.

## Notes

`notes/pc.md` holds messages from the PC side, `notes/laptop.md` messages from the laptop. Cloning and pulling needs no login because the repo is public; pushing a note needs a GitHub token on the laptop.
