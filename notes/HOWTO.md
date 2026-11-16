# How the two AIs talk

Both machines run Freebuff on the same account, with the same GitHub connection. Neither AI can see the other's chat window, so this repo is the mailbox.

## Rules

1. The PC side writes `notes/pc.md`. The laptop side writes `notes/laptop.md`. Never edit the other side's file.
2. Read the other side's file before doing work, and re-read it after every `git pull`.
3. Write with the GitHub tool (commit multiple files). Do not try `git push` with a token.
4. Keep entries short: date, what ran, what came out, what is broken.
5. Put numbers in, not impressions. "cadence=0.0, lr=+0.02 while marching" beats "it does not work".

## What each side owns

| side | runs | writes |
| --- | --- | --- |
| Windows PC | `tools/board_relay_receiver.py`, WiimoteHook, the game | `notes/pc.md` |
| Arch laptop | `tools/board_sender_arch.py` (reads the balance board) | `notes/laptop.md` |

## Live channel that is not git

The PC writes `eldenring/relay.log` with every packet it receives and every key it fires. The laptop prints sender output on stdout. Those are the ground truth when a note disagrees with reality.
