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
    3.60,   # J2 HOLD
    1.50,   # J3 HOLD + gravity FF
    3.60,   # J4 HOLD
    4.50,   # J5 HOLD
    4.50,   # J6 HOLD
    6.00,   # J7 GRIPPER
]

TOL_DEG = 0.08
TIMEOUT_S = 12.0
HOLD_S = 1.5


def fmt(values):
    return "  ".join(
        f"J{i+1}={float(v):+7.2f}"
        for i, v in enumerate(values)
    )


def wait_command(arm, target):
    deadline = time.monotonic() + TIMEOUT_S

    while True:
        commanded = arm.get_command_angles()

        err = max(
            abs(float(a) - float(b))
            for a, b in zip(commanded, target)
        )

        if err <= TOL_DEG:
            return

        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"COMMAND_TIMEOUT max_error={err:.3f} deg"
            )

        time.sleep(0.05)


def execute_action(
    arm,
    trix,
    bridge,
    adapter,
    state,
    captured,
    action,
):
    proposal = Proposal(
        action,
        source="trix_physical_gripper_v1",
    )

    decision = trix.evaluate(
        state,
        proposal,
    )

    print()
    print("=" * 76)
    print(
        f"TRiX: {state.mode.value} / "
        f"{state.gripper_state.value}"
        f" -> {action.value}"
        f" -> {decision.decision.value}"
    )
    print("=" * 76)

    if decision.decision == DecisionType.REJECT:
        raise RuntimeError(
            "TRIX_REJECT: "
            + "; ".join(decision.reasons)
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

    target = physical.angles_deg

    print("TARGET:")
    print(fmt(target))

    print()
    print("DELTA FROM CAPTURED START:")

    deltas = []

    for i, (start, value) in enumerate(
        zip(captured, target),
        1,
    ):
        delta = float(value) - float(start)
        deltas.append(delta)

        print(
            f"  J{i}: {delta:+.3f} deg"
        )

    # Hard experiment invariant:
    # only J7 is allowed to move in this test.
    for index in range(6):
        if abs(deltas[index]) > 1e-9:
            raise RuntimeError(
                f"ARM_JOINT_MOVEMENT_FORBIDDEN:"
                f"J{index+1}={deltas[index]:+.6f}"
            )

    expected_j7 = (
        40.0
        if action == Action.OPEN_GRIPPER
        else 0.0
    )

    if abs(deltas[6] - expected_j7) > 1e-9:
        raise RuntimeError(
            "UNEXPECTED_J7_TARGET:"
            f"{deltas[6]:+.6f}"
        )

    arm.set_joint_angles(target)

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

    for i, (a, t) in enumerate(
        zip(actual, target),
        1,
    ):
        print(
            f"  J{i}: "
            f"{float(a)-float(t):+.3f} deg"
        )

    state = trix.apply(
        state,
        decision,
    )

    print()
    print(
        "STATE AFTER:"
        f" arm={state.mode.value},"
        f" gripper={state.gripper_state.value},"
        f" J7_delta={state.gripper_delta_deg:+.1f}"
    )

    time.sleep(HOLD_S)

    return state, actual


def main():

    arm = ReBotRSMITController()
    started = False

    try:
        print("=" * 76)
        print("TRIX PHYSICAL GRIPPER V1")
        print("OBJECTLESS OPEN/CLOSE CYCLE")
        print("J1-J6 MUST NOT MOVE")
        print("J7 OPEN = +40 DEG RELATIVE")
        print("J7 CLOSED = CAPTURED POSITION")
        print("=" * 76)

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

        state = RobotState()

        print()
        print("INITIAL TRIX STATE:")
        print(
            f"arm={state.mode.value}, "
            f"gripper={state.gripper_state.value}"
        )

        sequence = (
            Action.OPEN_GRIPPER,
            Action.CLOSE_GRIPPER,
            Action.OPEN_GRIPPER,
            Action.CLOSE_GRIPPER,
        )

        for action in sequence:
            state, _ = execute_action(
                arm,
                trix,
                bridge,
                adapter,
                state,
                captured,
                action,
            )

        final = arm.read_joint_angles()

        print()
        print("=" * 76)
        print("TRIX GRIPPER V1 RESULT")
        print("=" * 76)

        print(
            f"final arm state: "
            f"{state.mode.value}"
        )

        print(
            f"final gripper state: "
            f"{state.gripper_state.value}"
        )

        print()
        print("START -> FINAL ACTUAL:")

        for i, (start, value) in enumerate(
            zip(captured, final),
            1,
        ):
            print(
                f"  J{i}: "
                f"{float(value)-float(start):+.3f} deg"
            )

        if state.gripper_state != GripperState.CLOSED:
            raise RuntimeError(
                "FINAL_GRIPPER_STATE_NOT_CLOSED"
            )

        print()
        print("TRIX PHYSICAL GRIPPER V1: PASS")

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
