# Messages from the PC side

## 2026-11-16 latest state

Relay is running on the PC. It listens on UDP 45454 and expects packets from 192.168.2.19.

New in the receiver since the last note: it only injects keys while the focused window title contains `ELDEN`. Otherwise it logs `game NOT focused - keys paused` and releases everything. That removes the old trap where leaning typed W into whatever window happened to be in front.

### Current observation

`eldenring/relay.log` ends with `link silent - released all keys`, so at that moment **nothing was arriving**: the sender on the laptop was not running. Earlier packets that did arrive were the OLD format (`f,b,l,r` only, no `sp`/`y`), which means the laptop was running a stale copy of the script. The current copy is in `tools/board_sender_arch.py` in this repo.

### What the laptop side should do and report

1. `python3 tools/board_sender_arch.py --list` - report the exact line for the board, including the `axes=[...]` list. We need to know there are four axes and their names.
2. Run the sender with `--host 192.168.2.12` and paste the printed line for each of these states:
   - standing still
   - marching in place
   - marching fast
   - leaning left, then right
   - leaning back
   - twisting shoulders left, then right
3. Say plainly whether `cadence` rises above 1.0 when marching and whether `twist` passes 0.15 when twisting.

With those numbers I can set the deadzones properly instead of shipping guesses.

### Known PC-side traps (do not re-learn these)

- WiimoteHook reads its config only at startup; restart it after any config edit.
- Two receivers bound to port 45454 split the packets and both half-work. Keep exactly one.
- Injected keys go to the focused window only. The new focus gate makes this visible in the log.
- A duplicate appSettings key makes WiimoteHook fail to start. Count keys after editing.
