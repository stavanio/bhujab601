# bhujab601

Personal bring-up, recovery, commissioning, and control notes for a **Seeed reBot Arm B601-RS** using **RobStride** actuators.

This repository exists to preserve a **known-good, independently reproducible baseline** for my B601-RS rather than depending on scattered browser history, chat logs, or vendor UI state.

## Current known-good state

- Hardware: Seeed reBot Arm B601-RS, pre-assembled kit with gripper
- Actuators: 3 × RobStride RS06 + 4 × RobStride RS00
- Power: 48 V
- CAN bitrate: 1 Mbps
- Motor IDs: 1–7
- Host / feedback ID: `0xFD`
- Ubuntu CAN interface: `can0`
- USB-CAN runtime after recovery: `0c72:000c PEAK System PCAN-USB`
- Linux driver: `pcan_usb`
- Motor discovery: **7/7 motors responding**
- Zero calibration: completed
- Default parameter write: completed
- Post-write readback: **passed**
- First motion: J1 ±3° at 1°/s, successful
- Verified resting joint angles after commissioning: approximately
  `[0.54, 0.00, 0.00, 0.00, -0.02, -0.03, -0.06] deg`

## Start here

1. [Known-good hardware topology](docs/01-hardware-topology.md)
2. [Ubuntu CAN bring-up](docs/02-ubuntu-can-bringup.md)
3. [Motor discovery](docs/03-motor-discovery.md)
4. [MotorBridge zeroing + parameters](docs/04-zeroing-and-parameters.md)
5. [First controlled motion](docs/05-first-motion.md)
6. [USB-CAN firmware recovery](docs/06-usb-can-firmware-recovery.md)
7. [Full troubleshooting history](docs/07-troubleshooting-history.md)
8. [Known-good baseline / quick recovery](docs/08-known-good-baseline.md)
9. [Official Seeed references](docs/09-official-sources.md)

## Golden rule

Before changing IDs, firmware, termination, wiring, or calibration:

```bash
ip -details link show can0
uv run motorbridge-cli scan --vendor robstride --channel can0 --start-id 1 --end-id 7
```

If all 7 motors respond, **do not change the CAN physical layer**.

## Safety

- Power the arm from the required 48 V supply.
- Do not hot-plug XT30 2+2 motor/power connectors.
- Keep the arm securely mounted.
- Keep people outside the arm's moving workspace during enabled motion.
- First motion should be single-joint, small-angle, low-speed.
- Do not run MotorBridge Studio and a second controller simultaneously.

## Upstream projects

- Seeed B601-RS Quick Start
- Seeed B601-RS MIT control guide
- Seeed `reBotArm_control_py`
- `LAN-GER/rebot_control`
- MotorBridge / MotorBridge Studio

See [official sources](docs/09-official-sources.md).
