# TRiX B601-RS Hardware Baseline

Date: 2026-08-25

## Proven hardware stack

- Seeed reBot Arm B601-RS
- RobStride RS06: J1-J3
- RobStride RS00: J4-J7
- SocketCAN can0 @ 1 Mbps
- rebot_control continuous MIT controller @ 200 Hz
- BK Precision 1902 power supply
- 48 V
- Current limit: 15 A
- Normal operating state: CV

## Important power finding

The severe thud / torque-loss behavior was traced to a shared
DC-bus undervoltage event.

During a failing J3 lift:

- J3 current increased normally under load.
- J3 then dropped to zero torque.
- J1-J7 subsequently reported undervoltage/reset state.
- Several joints reported overcurrent immediately before the
  shared undervoltage event.

After restoring the BK supply current limit to 15 A, the same
motion architecture executed smoothly without the bus collapse.

Do not run the arm with an accidentally low PSU current limit.

Expected idle display is approximately:

    48 V
    ~0.1 A actual load
    CV

while the current LIMIT remains configured to 15 A.

## Controller gains

The working MIT gains remain the established values in
config/rebotarm_rs.yaml.

No gain increase was required to resolve the catastrophic thud.

## Proven motion topology

Captured start
    ->
J1 large positive pre-position
    ->
J2 forward/clearance
    ->
J4 clearance
    ->
J3 rise
    ->
distal coordinated work
    ->
exact reverse work path
    ->
J3 return
    ->
J4 return
    ->
J2 return
    ->
J1 return LAST
    ->
captured start
    ->
hold

Ctrl+C behavior for the working experimental scripts:

    disable motors
    no automatic return-to-zero

## Working script lineage

- j3_closed_loop_proof.py
    Proved stable J2/J4/J3 chain motion and exact return.

- j3_closed_loop_proof_FLAWLESS_BASELINE.py
    Frozen commissioning baseline.

- full_arm_cycle.py
    Proven coordinated J1-J6 cycle.

- trix_large_slow.py
    Large-workspace J1-first TRiX topology.

- trix_large_v2.py
    J1 +102 degree large-workspace version.

- trix_large_v3_1p5.py
    1.5x motion-speed version with increased J2 forward lean.

- run_trix_logged.sh
    Passive CAN + console + configuration flight recorder.

## Remaining controls work

1. Freeze proven motion executor.
2. Add gravity feed-forward without changing the proven
   trajectory/power architecture.
3. Add VBUS/current/fault telemetry guards.
4. Expose stable motion primitives to TRiX.
5. Run repeatable logged TRiX hardware episodes.

Gravity compensation is still pending. J3 currently holds the
gravity-loaded configuration using feedback position error and
therefore has measurable static tracking error.
