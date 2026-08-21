# Motor discovery

## Primary scan

From the `reBotArm_control_py` checkout:

```bash
uv run motorbridge-cli scan \
  --vendor robstride \
  --channel can0 \
  --start-id 1 \
  --end-id 7
```

Known-good result:

```text
[hit] probe=0x01 ... device_id=1
[hit] probe=0x02 ... device_id=2
[hit] probe=0x03 ... device_id=3
[hit] probe=0x04 ... device_id=4
[hit] probe=0x05 ... device_id=5
[hit] probe=0x06 ... device_id=6
[hit] probe=0x07 ... device_id=7
scan done: 7 motor(s) found
```

## Pre-assembled-arm rule

For the pre-assembled B601-RS, IDs 1–7 are expected. Do **not** rewrite IDs just because a scan failed. First verify:

1. 48 V arm power is on.
2. `can0` is UP at 1 Mbps.
3. the complete braided motor chain is connected.
4. the USB-CAN adapter is enumerated normally.

## Diagnostic history

### Earlier failure

```text
scan done: 1 motor(s) found
```

Only ID 1 answered.

Cause in this setup: downstream braided inter-joint cables were not all connected.

### After completing the chain

```text
scan done: 7 motor(s) found
```

This proved the USB-CAN adapter, bitrate, RobStride protocol, host ID, power path, and full CAN chain were functional.
