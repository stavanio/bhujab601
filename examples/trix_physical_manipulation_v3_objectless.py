#!/usr/bin/env python3

import time

from rebot import ReBotRSMITController

from trix_runtime import (
    Action,
    DecisionType,
    GripperState,
    Proposal,
    RobotState,
    TrixExecutionBridge,
    TrixPhysicalTargetAdapter,
    TrixProjector,
)


SPEEDS_DEG_S = [
    4.50,   # J1 HOLD
    3.60,   # J2
    1.50,   # J3
    3.60,   # J4
    4.50,   # J5
    4.50,   # J6
    6.00,   # J7 gripper
]

TIMEOUT_S = 18.0
TOL_DEG = 0.08
HOLD_S = 0.8


EXPECTED = {
    Action.OPEN_GRIPPER:
        [0, 0, 0, 0, 0, 0, 40],

    Action.APPROACH:
        [0, 18, 0, 0, 0, 0, 40],

    Action.PRESHAPE:
        [0, 18, 0, 14, 0, 0, 40],

    Action.LOW_HOVER:
        [0, 30, 0, 14, 0, 0, 40],

    Action.DEEP_HOVER:
        [0, 36, -3, 14, 0, 0, 40],

    Action.ENGAGE:
        [0, 36, -3, 14, 0, 0, 0],

    Action.RETURN_LOW_HOVER:
        [0, 30, 0, 14, 0, 0, 0],

    Action.RETRACT:
        [0, 18, 0, 14, 0, 0, 0],

    Action.UNPRESHAPE:
        [0, 18, 0, 0, 0, 0, 0],

    Action.RETURN_SAFE:
        [0, 0, 0, 0, 0, 0, 0],

    Action.RELEASE:
        [0, 0, 0, 0, 0, 0, 40],

    Action.CLOSE_GRIPPER:
        [0, 0, 0, 0, 0, 0, 0],
}


SEQUENCE = (
    Action.OPEN_GRIPPER,
    Action.APPROACH,
    Action.PRESHAPE,
    Action.LOW_HOVER,
    Action.DEEP_HOVER,
    Action.ENGAGE,
    Action.RETURN_LOW_HOVER,
    Action.RETRACT,
    Action.UNPRESHAPE,
    Action.RETURN_SAFE,
    Action.RELEASE,
    Action.CLOSE_GRIPPER,
)


def fmt(values):
    return "  ".join(
        f"J{i+1}={float(v):+7.2f}"
        for i, v in enumerate(values)
    )


def wait_command(arm, target):

    deadline = time.monotonic() + TIMEOUT_S

    while True:

        command = arm.get_command_angles()

        error = max(
            abs(float(a) - float(b))
            for a, b in zip(command, target)
        )

        if error <= TOL_DEG:
            return

        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"COMMAND_TIMEOUT error={error:.3f}"
            )

        time.sleep(0.05)


def build(
    trix,
    bridge,
    adapter,
    state,
    action,
):

    proposal = Proposal(
        action,
        source="trix_physical_manipulation_v3",
    )

    decision = trix.evaluate(
        state,
        proposal,
    )

    if decision.decision == DecisionType.REJECT:
        raise RuntimeError(
            f"TRIX_REJECT:{action.value}:"
            + ";".join(decision.reasons)
        )

    command = bridge.build(
        state,
        decision,
    )

    physical = adapter.build(
        command,
    )

    if physical is None:
        raise RuntimeError(
            f"NO_PHYSICAL_TARGET:{action.value}"
        )

    adapter.assert_j1_invariant(
        physical.angles_deg
    )

    next_state = trix.apply(
        state,
        decision,
    )

    return (
        decision,
        physical,
        next_state,
    )


def verify_target(
    captured,
    action,
    target,
):

    delta = [
        float(t) - float(s)
        for s, t in zip(
            captured,
            target,
        )
    ]

    expected = EXPECTED[action]

    for index, (actual, exp) in enumerate(
        zip(delta, expected),
        1,
    ):

        if abs(actual - exp) > 1e-6:
            raise RuntimeError(
                f"{action.value}:"
                f"BAD_J{index}_DELTA:"
                f"{actual:+.6f},"
                f"expected={exp:+.6f}"
            )

    return delta


def execute(
    arm,
    trix,
    bridge,
    adapter,
    captured,
    state,
    action,
):

    decision, physical, next_state = build(
        trix,
        bridge,
        adapter,
        state,
        action,
    )

    target = physical.angles_deg

    delta = verify_target(
        captured,
        action,
        target,
    )

    print()
    print("=" * 80)

    print(
        f"{state.mode.value}/"
        f"{state.gripper_state.value}"
        f" -> {action.value}"
        f" -> {decision.decision.value}"
    )

    print("=" * 80)

    print("TARGET:")
    print(fmt(target))

    print()
    print("DELTA:")

    for index, value in enumerate(
        delta,
        1,
    ):
        print(
            f"  J{index}: "
            f"{value:+.3f} deg"
        )

    arm.set_joint_angles(
        target
    )

    wait_command(
        arm,
        target,
    )

    time.sleep(0.40)

    actual = arm.read_joint_angles()

    print()
    print("ACTUAL:")
    print(fmt(actual))

    print()
    print("ACTUAL - TARGET:")

    for index, (a, t) in enumerate(
        zip(actual, target),
        1,
    ):

        print(
            f"  J{index}: "
            f"{float(a)-float(t):+.3f} deg"
        )

    print()
    print(
        f"STATE AFTER: "
        f"{next_state.mode.value}/"
        f"{next_state.gripper_state.value}"
        f" J7_delta="
        f"{next_state.gripper_delta_deg:+.1f}"
    )

    time.sleep(HOLD_S)

    return next_state


def main():

    arm = ReBotRSMITController()
    started = False

    try:

        print("=" * 80)
        print("TRIX MANIPULATION V3 — OBJECTLESS")
        print("FULL REACH + GRIPPER STATE CHAIN")
        print("J1 HARD-FROZEN")
        print("=" * 80)

        arm.start(
            enable_esc=False,
            install_signal_handlers=False,
        )

        started = True

        arm.set_max_speeds(
            SPEEDS_DEG_S
        )

        captured = arm.read_joint_angles()

        print()
        print("CAPTURED START:")
        print(fmt(captured))

        trix = TrixProjector()
        bridge = TrixExecutionBridge()

        adapter = TrixPhysicalTargetAdapter(
            captured
        )

        # --------------------------------------------------------
        # PRECOMPUTE / VERIFY FULL TRAJECTORY BEFORE MOVING
        # --------------------------------------------------------

        state = RobotState()

        print()
        print("=" * 80)
        print("FULL PRE-MOTION TRIX PLAN")
        print("=" * 80)

        preview_state = state

        for action in SEQUENCE:

            decision, physical, next_state = build(
                trix,
                bridge,
                adapter,
                preview_state,
                action,
            )

            delta = verify_target(
                captured,
                action,
                physical.angles_deg,
            )

            print(
                f"{preview_state.mode.value}/"
                f"{preview_state.gripper_state.value}"
                f" -> {action.value}"
                f" -> {decision.decision.value}"
                f" | "
                + " ".join(
                    f"J{i+1}={x:+.0f}"
                    for i, x in enumerate(delta)
                )
            )

            preview_state = next_state

        if (
            preview_state.mode.value
            != "START_SAFE"
        ):
            raise RuntimeError(
                "PREVIEW_NOT_START_SAFE"
            )

        if (
            preview_state.gripper_state
            != GripperState.CLOSED
        ):
            raise RuntimeError(
                "PREVIEW_GRIPPER_NOT_CLOSED"
            )

        print()
        print(
            "PRE-MOTION PLAN VALIDATED."
        )

        time.sleep(2.0)

        # --------------------------------------------------------
        # PHYSICAL EXECUTION
        # --------------------------------------------------------

        state = RobotState()

        for action in SEQUENCE:

            state = execute(
                arm,
                trix,
                bridge,
                adapter,
                captured,
                state,
                action,
            )

        final = arm.read_joint_angles()

        print()
        print("=" * 80)
        print("TRIX MANIPULATION V3 RESULT")
        print("=" * 80)

        print(
            f"final arm state: "
            f"{state.mode.value}"
        )

        print(
            f"final gripper state: "
            f"{state.gripper_state.value}"
        )

        print()
        print("START -> FINAL:")

        for index, (s, f) in enumerate(
            zip(captured, final),
            1,
        ):
            print(
                f"  J{index}: "
                f"{float(f)-float(s):+.3f} deg"
            )

        if (
            state.mode.value
            != "START_SAFE"
        ):
            raise RuntimeError(
                "FINAL_ARM_NOT_START_SAFE"
            )

        if (
            state.gripper_state
            != GripperState.CLOSED
        ):
            raise RuntimeError(
                "FINAL_GRIPPER_NOT_CLOSED"
            )

        print()
        print(
            "TRIX MANIPULATION V3 OBJECTLESS: PASS"
        )

        time.sleep(1.0)

    finally:

        if started:
            arm.stop(
                return_to_zero=False,
                wait=True,
            )

        print(
            "MOTORS DISABLED / CAN CLOSED"
        )


if __name__ == "__main__":
    main()
