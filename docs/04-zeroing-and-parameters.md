# Zero calibration and parameter initialization

Use **MotorBridge Studio** after all 7 motors scan successfully.

## Start gateway

```bash
cd ~/reBotArm_control_py
uv run motorbridge-gateway --bind 127.0.0.1:9002
```

In MotorBridge Studio connect to:

```text
ws://127.0.0.1:9002
```

Select:

```text
Arm Model: rebot-arm-robstride
CAN channel: can0
```

## First-time order

The Studio first-time guide states:

1. Select the matching arm model.
2. Manually place all 7 joints at a safe initial mechanical posture.
3. Scan all joints and confirm online status.
4. Run Zero All with the required safety confirmations.
5. Read Params for record.
6. Apply Default Template.
7. Write Params.

## Zeroing

The arm was manually positioned to the official Seeed B601-RS zero-pose geometry before zeroing.

Normal zeroing was used once the joint-state safety check was satisfied.

After zeroing, the joint readings were essentially zero.

## Developer parameter panel

MotorBridge Studio v1.1.4 hides the detailed parameter table in normal mode.

With the MotorBridge page focused in Firefox:

1. hold `Ctrl`;
2. tap `D`, then `E`, then `V` quickly;
3. release `Ctrl`.

A yellow `DEV` indicator appears and the detailed **Joint Control Params** panel becomes visible.

The panel includes:

- Read Params
- Write Params
- Apply Default Template
- Export Params
- Import Params

## Parameter initialization performed

1. `Read Params`
2. `Export Params` — saved the original motor configuration
3. `Apply Default Template`
4. `Write Params`
5. post-write readback verification

Final Studio result:

```text
Write-back verification passed.
```

Self-check also reported:

```text
Online Joints: 7/7
Param Read-back: ok=7, fail=0
Self-check: PASSED
```

## Important

Do not run MotorBridge Studio/gateway as an active controller at the same time as a separate Python control program.
