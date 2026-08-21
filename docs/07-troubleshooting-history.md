# Troubleshooting history

This is the chronological record of the bring-up.

## 1. Initial symptoms

- B601-RS pre-assembled kit
- 4 × RS00 + 3 × RS06
- 48 V
- CAN 1 Mbps
- zero RobStride replies
- USB-CAN TX occurred but no usable motor communication
- `can0` could become ERROR-PASSIVE

Initial adapter:

```text
1d50:606f
bytewerk
candleLight USB to CAN adapter
gs_usb
```

## 2. Ground/termination exploration

Continuity observations:

```text
UTC GND -> BK negative = OL
BK negative -> arm negative = ~0.8 ohm
```

A temporary third ground wire was tested; it did not solve communication.

This was not the final fix.

## 3. Firmware detour

Because the supplied UTC-T01 could run multiple firmware personalities, the adapter was converted from candleLight/gs_usb to Seeed's PCAN-compatible firmware.

Ubuntu `dfu-util` and Windows DfuSe both stalled.

STM32CubeProgrammer through a USB hub successfully programmed:

```text
pcan_canable_hw.hex
```

Recovered runtime:

```text
0c72:000c PEAK System PCAN-USB
pcan_usb
```

## 4. PCAN SocketCAN validation

```bash
sudo ip link set can0 down 2>/dev/null
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
ip -details link show can0
```

Known-good:

```text
ERROR-ACTIVE
tx 0
rx 0
bitrate 1000000
pcan_usb
```

## 5. First meaningful motor scan

Result:

```text
ID 1 = hit
IDs 2-7 = no reply
```

This proved the PC-CAN path and at least J1 were working.

## 6. Actual root cause of incomplete discovery

The braided XT30 2+2 motor-chain cables were completed across the arm.

Next scan:

```text
IDs 1-7 = all hit
scan done: 7 motor(s) found
```

## 7. Commissioning

- MotorBridge Studio connected
- `rebot-arm-robstride`
- Scan All Joints: 7/7
- physical zero pose set
- Zero All completed
- developer parameter panel enabled
- Read Params
- exported original params
- Apply Default Template
- Write Params
- write-back verification passed

## 8. First controlled motion

`rebot_control` virtual environment created.

First meaningful motion:

```text
J1: 0 -> +3 deg
speed: 1 deg/s
return: +3 -> 0 deg
disable
```

Successful.

## 9. Home verification

Repeated actual encoder readings after commissioning stayed approximately:

```text
J1 +0.54 deg
J2  0.00 deg
J3  0.00 deg
J4  0.00 deg
J5 -0.02 deg
J6 -0.03 deg
J7 -0.06 deg
```

This is the current known-good calibrated base state.
