# Messages from the PC side

2026-11-16 - Relay verified working end to end. Captured from the PC receiver:

    first packet from 192.168.2.19
      packet 1: {"f": 1, "b": 0, "l": 0, "r": 0}
      key W DOWN

What the laptop should do next, and report back:

1. Run the CURRENT tools/board_sender_arch.py (older copies send no sp/y fields, so marching and twist do not exist).
2. Paste the printed line while standing still, while marching, while leaning left and right, and while twisting.
3. Note whether cadence rises above 1.0 when marching, and whether twist exceeds 0.15 when twisting.

Known good: packets arrive from 192.168.2.19 to 192.168.2.12 on UDP 45454, and the PC injects W/A/S/D.
Known PC-side traps: config is read only at WiimoteHook startup; two receivers bound to port 45454 split the packets; injected keys go to the focused window only.
