# TRiX B601-RS Tabletop Hardware Milestone

Date: 2026-08-26

## Purpose

Freeze the first proven B601-RS physical manipulation baseline that combines:

- large-workspace J1 positioning
- staged tabletop approach
- model-based J3 gravity feed-forward
- repeatable return to captured start
- passive CAN flight recording
- successful 3x velocity experiment

## Hardware

Robot: Seeed reBot Arm B601-RS

Actuators:
- J1-J3: RobStride RS06
- J4-J7: RobStride RS00

Power:
- 48 V
- 15 A current limit
- CV operation

CAN:
- SocketCAN can0
- 1 Mbps

Control:
- MIT
- 200 Hz

## Gravity Compensation

Experimental model-based feed-forward:

    tau_ff = alpha * g(q)

For this milestone:

    alpha = 0.25

Only J3 receives gravity feed-forward in the current experimental wrapper.

Physical testing demonstrated stable J3 holding under changing arm geometry.

## V4

Large-workspace trajectory:

    J1 +110 deg
    J2 +10 deg
    J4 +10 deg
    J3 +9 deg

V4 demonstrated large-workspace motion and accurate return, but FK and
physical observation showed the final J3 rise moved the gripper upward,
making the pose unsuitable as the final tabletop approach.

## V5 Tabletop Stage 1

Staged approach:

    CAPTURE START
        |
        v
    J1 +110 deg
        |
        v
    J2 +18 deg
        |
        v
    J4 +14 deg
        |
        v
    J2 +30 deg
        |
        v
    HOLD

J3 remains near its captured-start position.

J5/J6 work displacement is disabled for this first low-hover test.

Safe reverse:

    J2 30 -> 18
    J4 -> start
    J2 -> start
    J1 -> start LAST

## V5 Physical Result

Successful physical run:

    run_20260826_215919_v5_tabletop_stage1_grav025

Final J2 approach showed close tracking.

Example near final approach:

    J2 command 28.92 deg
    J2 actual  28.78 deg

J3 hold result:

    before  +0.35 deg
    after   +0.35 deg
    drift   +0.00 deg

Gravity estimate during final approach:

    gJ3 approximately 7.06 to 7.15 Nm
    tauFF approximately 1.77 to 1.79 Nm

CAN remained ERROR-ACTIVE with zero TX/RX error counters.

Exit code:

    0

Physical observation at the final V5 pose:

    gripper nose approximately 5 inches above tabletop

Approximate J2 motor center to gripper nose distance:

    approximately 24 inches

These physical dimensions are approximate manual measurements and should
not yet be interpreted as calibrated URDF frame measurements.

## 3x Velocity Experiment

The exact V5 geometry was subsequently executed with velocity limits
increased by 3x.

Velocity limits:

    J1  4.50 deg/s
    J2  3.60 deg/s
    J3  1.50 deg/s
    J4  3.60 deg/s
    J5  4.50 deg/s
    J6  4.50 deg/s
    J7  2.25 deg/s

No geometry, Kp/Kd, gravity-alpha, CAN configuration, or power settings
were intentionally changed for the speed experiment.

Physical observation:

    Motion was smooth and completed successfully.

This establishes the fast constant-velocity tabletop baseline.

## Important Interpretation

The current executor is rate-limited in position at 200 Hz.

It is NOT yet acceleration-limited or jerk-limited.

The successful 3x run therefore becomes the upper proven baseline for
this executor before introducing a dedicated acceleration-limited
trajectory generator.

## Next Engineering Steps

1. Freeze this baseline.
2. Add reusable TRiX motion primitives:
   - PREPOSITION
   - APPROACH
   - LOW_HOVER
   - ENGAGE
   - RETRACT
   - RETURN_SAFE
   - HOME
3. Build symbolic transition/admissibility rules.
4. Run deterministic nominal and intentionally inadmissible episodes.
5. Add an acceleration-limited trajectory generator without modifying
   the frozen hardware baseline.
6. Refine physical table-frame calibration.
7. Progress from low-hover to pregrasp and pick/place.
8. Integrate VLM/policy proposals through the TRiX safety projector.

