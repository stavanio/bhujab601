# Hardware topology

## B601-RS motor map

| Joint | Motor ID | Motor type |
|---|---:|---|
| J1 | 1 | RS06 |
| J2 | 2 | RS06 |
| J3 | 3 | RS06 |
| J4 | 4 | RS00 |
| J5 | 5 | RS00 |
| J6 | 6 | RS00 |
| J7 / gripper | 7 | RS00 |

Host / feedback ID used by the B601-RS configuration: `0xFD`.

## Functional topology

```text
Ubuntu laptop
    |
    | USB
    v
USB-CAN adapter
    |
    | CAN @ 1 Mbps
    v
XT30 2+2 / CAN-power distribution
    |
    v
J1 -> braided XT30 2+2 -> J2 -> J3 -> J4 -> J5 -> J6 -> J7

48 V supply
    |
    +----------------------------------> arm power network
```

## Critical commissioning discovery

The arm's braided XT30 2+2 interconnects must continue through the motor chain.

A partially connected chain produced:

```text
J1 = online
J2-J7 = offline
```

After completing the braided inter-joint cable chain:

```text
J1-J7 = all online
```

This was a decisive diagnostic result.

## USB extension

A USB extension was used successfully to move the laptop/control point farther from the arm. After any USB-CAN unplug/replug, the SocketCAN interface must be brought up again.

## Do not infer undocumented wiring

The current written Seeed B601-RS docs do not provide a complete text-only external pin-by-pin mapping for every CAN/power breakout connection. Keep vendor-shipped orientation and connector mapping unless verified from official diagrams/video/hardware markings.
