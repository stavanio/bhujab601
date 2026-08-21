# USB-CAN firmware recovery

This chapter documents what happened to the UTC-T01 and how it was successfully recovered.

## Original state

The adapter originally enumerated as:

```text
USB ID: 1d50:606f
Manufacturer: bytewerk
Product: candleLight USB to CAN adapter
Linux driver: gs_usb
```

That was a valid native SocketCAN/candleLight configuration.

## Important retrospective

The original candleLight firmware was **not proven to be the cause of the arm communication problem**.

The original arm issue was later resolved through correct motor-chain connectivity. Firmware conversion should therefore **not** be the first response to a future CAN discovery failure.

## Entering STM32 DFU

With the arm powered OFF and CAN lines disconnected:

1. move UTC switch to `BOOT`;
2. unplug/replug USB.

Linux:

```bash
lsusb
```

DFU state:

```text
0483:df11 STMicroelectronics STM Device in DFU Mode
```

## Linux `dfu-util` problem encountered

The Seeed package contained:

```text
pcan_canable_hw.dfu
pcan_canable_hw.hex
pcan_canable_hw.bin
flash_pcan_ubuntu.sh
```

`dfu-util` detected:

```text
@Internal Flash /0x08000000/
```

but writes repeatedly stalled at:

```text
Erase [ ] 0%
```

The system also had an integrated camera exposing a DFU runtime interface, so the Seeed shell script initially saw more than one DFU-capable USB device.

## Windows DfuSe problem

The old DfuSe tool recognized `STM Device in DFU Mode`, loaded the `.dfu` file, but also stalled at 0%.

## Successful recovery path

The decisive workaround was:

1. use **STM32CubeProgrammer** on Windows;
2. put a **USB hub** between the Legion laptop and the UTC-T01;
3. connect using CubeProgrammer's **USB/DFU** mode;
4. CubeProgrammer then successfully read the device;
5. load Seeed's:
   `pcan_canable_hw.hex`;
6. program/download the file.

CubeProgrammer reported:

```text
File Download Complete
```

Then:

1. unplug USB;
2. move switch `BOOT` -> `120R`;
3. reconnect.

Ubuntu then reported:

```text
0c72:000c PEAK System PCAN-USB
```

and Linux exposed:

```text
can0
driver: pcan_usb
```

## Lesson

If STM32 DFU is detected but reads/writes stall on a Legion-class USB controller, try a simple USB hub before assuming flash protection or corrupt hardware.

Do not issue mass-erase/unprotect/option-byte commands casually.
