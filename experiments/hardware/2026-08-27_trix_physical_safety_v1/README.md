# TRiX Physical Safety Experiment V1

Date: 2026-08-27

Robot: Seeed reBot Arm B601-RS

## Objective

Demonstrate an end-to-end physical TRiX safety path:

    policy proposal
        ->
    TRiX symbolic / numeric safety projector
        ->
    execution bridge
        ->
    physical target adapter
        ->
    B601-RS actuator execution

Unsafe proposals must not leak into the actuator layer.

Projected proposals must execute only the projected safe action.

## J1 Safety Requirement

J1 was frozen by operator instruction.

Protection exists at three layers:

1. TRiX projector:
   any proposal containing J1 is hard rejected.

2. Execution bridge:
   J1 is not a supported executor-facing joint.

3. Physical target adapter:
   J1 target must equal the captured physical J1 position.

No intentional J1 displacement was allowed.

## Nominal Physical Experiment

Sequence:

    START_SAFE
        ->
    APPROACH
        ->
    J2 +18 deg
        ->
    RETURN_SAFE
        ->
    captured start

Result:

    PASS

Final approximate start-to-return physical errors:

    J1 -0.015 deg
    J2 +0.068 deg
    J3 +0.115 deg
    J4 -0.086 deg
    J5 +0.007 deg
    J6 -0.004 deg
    J7 +0.011 deg

Exit code:

    0

## Adversarial Physical Experiment

### Case 1: illegal state transition

Proposal:

    START_SAFE -> LOW_HOVER

TRiX:

    REJECT

Execution bridge:

    NO COMMAND

Physical target:

    NONE

### Case 2: forbidden J1 motion

Proposal:

    APPROACH
    J1 = +50 deg

TRiX:

    HARD REJECT

Reason:

    HARD_INVARIANT_J1_FROZEN

Execution bridge:

    NO COMMAND

Physical target:

    NONE

### Case 3: excessive continuous action

Policy proposal:

    APPROACH
    J2 = +50 deg

TRiX result:

    PROJECT

Projected action:

    J2 = +18 deg

Physical execution:

    J2 +18 deg

All other joint target deltas:

    0 deg

### Case 4: safe return

TRiX:

    ALLOW RETURN_SAFE

Robot returned to captured physical start.

Final start-to-return errors:

    J1 +0.007 deg
    J2 +0.042 deg
    J3 +0.105 deg
    J4 -0.110 deg
    J5 -0.011 deg
    J6 -0.013 deg
    J7 +0.007 deg

Exit code:

    0

## Gravity Compensation

J3 model-based gravity feed-forward remained enabled.

    alpha = 0.25

Observed J3 model gravity:

    approximately 6.76 to 7.08 Nm

Observed J3 feed-forward:

    approximately 1.69 to 1.77 Nm

## Result

TRiX Physical Safety Experiment V1:

    PASS

The experiment demonstrates:

- symbolic unsafe actions can be rejected before actuator execution
- forbidden J1 actions generate no physical target
- unsafe continuous actions can be projected into an admissible action
- only the projected safe action reaches the physical robot
- safe return is executed after the projected action
- the robot returns near the captured physical start pose
