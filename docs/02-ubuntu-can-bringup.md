# Ubuntu CAN bring-up

Validated on Ubuntu 24.04.

## Verify USB-CAN enumeration

After the successful PCAN-compatible firmware recovery:

```bash
lsusb
```

Known-good result:

```text
0c72:000c PEAK System PCAN-USB
```

## Verify SocketCAN interface

```bash
ip -br link
```

Known-good state after enumeration:

```text
can0   DOWN   <NOARP,ECHO>
```

## Bring `can0` up at 1 Mbps

```bash
sudo ip link set can0 down 2>/dev/null
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
```

Verify:

```bash
ip -details link show can0
```

Known-good result includes:

```text
state UP
can state ERROR-ACTIVE (berr-counter tx 0 rx 0)
bitrate 1000000
pcan_usb
```

## Important

After unplugging/replugging the USB-CAN adapter, repeat the CAN setup above.

## Convenience script

Use:

```bash
./scripts/can_up.sh
```
