# Known-good baseline

Use this page when coming back to the arm after days/weeks/months.

## Hardware

- arm securely mounted
- all braided motor-chain cables connected
- 48 V supply connected
- USB-CAN switch at `120R`
- USB-CAN connected
- no second controller active

## Ubuntu

Check USB:

```bash
lsusb
```

Expected:

```text
0c72:000c PEAK System PCAN-USB
```

Bring up CAN:

```bash
sudo ip link set can0 down 2>/dev/null
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
```

Verify:

```bash
ip -details link show can0
```

Expected:

```text
state UP
can state ERROR-ACTIVE
bitrate 1000000
pcan_usb
```

## Discover motors

```bash
cd ~/reBotArm_control_py
uv run motorbridge-cli scan \
  --vendor robstride \
  --channel can0 \
  --start-id 1 \
  --end-id 7
```

Expected:

```text
7 motor(s) found
```

## Known-good mapping

```text
1 RS06
2 RS06
3 RS06
4 RS00
5 RS00
6 RS00
7 RS00 gripper
feedback/host ID = 0xFD
```

## Parameter state

Known-good commissioning status:

```text
Self-check PASSED
Online 7/7
Param readback ok=7 fail=0
Write-back verification passed
```

## Safe tiny motion

From `~/rebot_control`:

```bash
source .venv/bin/activate
python tiny_first_move.py
```

Known-good test:

```text
J1 +3 deg
1 deg/s
return to zero
disable
```

## Home verification

```bash
python examples/read_joint_angles.py
```

Current calibrated home is near:

```text
[0.54, 0.00, 0.00, 0.00, -0.02, -0.03, -0.06] deg
```
