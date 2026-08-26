#!/usr/bin/env python3

import math
import time

from _bootstrap import setup_project_path
setup_project_path()

from rebot import ReBotRSMITController


# No gain changes.
# These only control the existing command-position ramp.
SPEEDS = [
    0.60,   # J1
    0.48,   # J2
    0.24,   # J3
    0.48,   # J4
    0.60,   # J5
    0.60,   # J6
    0.36,   # J7
]

# Relative to ACTUAL starting pose.
J2_DELTA = +4.0
J4_DELTA = +8.0
J3_DELTA = +6.0
WORK_DELTA = +8.0
J1_PREPOSITION_DELTA = +102.0


def read_actual(arm, joint):
    idx = joint - 1

    with arm._io_lock_guard():
        v = arm.motors[idx].robstride_get_param_f32(
            0x7019,
            timeout_ms=150,
        )

    return math.degrees(float(v))


def read_iqf(arm, joint):
    idx = joint - 1

    try:
        with arm._io_lock_guard():
            v = arm.motors[idx].robstride_get_param_f32(
                0x701A,
                timeout_ms=150,
            )

        return float(v)

    except Exception:
        return None


def enable_joint(arm, joint):
    idx = joint - 1

    with arm._io_lock_guard():
        arm.motors[idx].enable()

    time.sleep(0.20)


def move_pose(
    arm,
    target,
    label,
    watch_joint=None,
):
    start_cmd = list(
        arm.get_command_angles()
    )

    arm.set_joint_angles(target)

    travel_time = max(
        abs(b - a) / max(v, 1e-6)
        for a, b, v
        in zip(
            start_cmd,
            target,
            SPEEDS,
        )
    )

    timeout = travel_time + 6.0

    print()
    print("=" * 72)
    print(label)
    print("=" * 72)

    print(
        "FROM:",
        [round(x, 2) for x in start_cmd]
    )

    print(
        "TO:  ",
        [round(x, 2) for x in target]
    )

    t0 = time.monotonic()
    next_print = t0

    while True:

        now = time.monotonic()

        cmd = list(
            arm.get_command_angles()
        )

        remain = max(
            abs(a - b)
            for a, b
            in zip(cmd, target)
        )

        if (
            watch_joint is not None
            and now >= next_print
        ):
            actual = read_actual(
                arm,
                watch_joint,
            )

            iqf = read_iqf(
                arm,
                watch_joint,
            )

            iq_text = (
                "N/A"
                if iqf is None
                else f"{iqf:+.3f}"
            )

            print(
                f"J{watch_joint}: "
                f"cmd={cmd[watch_joint-1]:+.2f}° "
                f"actual={actual:+.2f}° "
                f"iqf={iq_text}"
            )

            next_print = now + 1.0

        if remain <= 0.05:
            break

        if now - t0 > timeout:
            raise RuntimeError(
                f"{label}: command ramp timeout"
            )

        time.sleep(0.10)

    time.sleep(1.0)


def hold_until_ctrl_c(arm):

    print()
    print("=" * 72)
    print("BACK AT CAPTURED START.")
    print("MOTORS HOLDING.")
    print("Ctrl+C = DISABLE ALL MOTORS + EXIT.")
    print("=" * 72)

    while True:
        time.sleep(1.0)


def main():

    arm = ReBotRSMITController()

    try:

        arm.start(
            enable_esc=False,
            install_signal_handlers=False,
        )

        arm.set_max_speeds(
            SPEEDS
        )

        # Controller synchronizes command positions
        # to physical positions during connect().
        start = list(
            arm.get_command_angles()
        )

        print()
        print("CAPTURED START:")

        for j, q in enumerate(start, 1):
            print(
                f"  J{j}: {q:+.2f}°"
            )

        # Clean initial state once.
        for idx in range(6):

            with arm._io_lock_guard():
                arm.motors[idx].clear_error()

            time.sleep(0.05)

            with arm._io_lock_guard():
                arm.motors[idx].enable()

            time.sleep(0.05)

        # --------------------------------------------------------
        # Build the three chain poses RELATIVE to captured start.
        # --------------------------------------------------------

        # --------------------------------------------------------
        # LARGE-WORKSPACE J1 PREPOSITION
        #
        # J1 moves first and then HOLDS there while the rest of
        # the linkage executes.
        # --------------------------------------------------------

        j1_pose = list(start)

        j1_pose[0] = (
            start[0] + J1_PREPOSITION_DELTA
        )

        p1 = list(j1_pose)

        p1[1] = (
            start[1] + J2_DELTA
        )

        p2 = list(p1)
        p2[3] = (
            start[3] + J4_DELTA
        )

        p3 = list(p2)
        p3[2] = (
            start[2] + J3_DELTA
        )

        # --------------------------------------------------------
        # TRIX PREPOSITION:
        # J1 FIRST
        # --------------------------------------------------------

        move_pose(
            arm,
            j1_pose,
            "TRIX PREPOSITION: J1 +102 DEG RELATIVE -- CONTROLLED",
            watch_joint=1,
        )

        print()
        print("J1 PREPOSITION REACHED.")
        print("Holding 2 seconds before linkage motion...")

        time.sleep(2.0)

        # --------------------------------------------------------
        # OUTBOUND
        # --------------------------------------------------------

        move_pose(
            arm,
            p1,
            "1/3 J2 CLEARANCE",
            watch_joint=2,
        )

        move_pose(
            arm,
            p2,
            "2/3 J4 CLEARANCE",
            watch_joint=4,
        )

        # This is the only intervention we're testing.
        #
        # No Kp/Kd change.
        # No clear_error here.
        # Just make sure J3 is explicitly enabled immediately
        # before it is asked to lift.
        print()
        print(
            "EXPLICIT J3 ENABLE IMMEDIATELY BEFORE RISE"
        )

        enable_joint(
            arm,
            3,
        )

        j3_before = read_actual(
            arm,
            3,
        )

        iq_before = read_iqf(
            arm,
            3,
        )

        print(
            f"J3 BEFORE: "
            f"actual={j3_before:+.2f}° "
            f"iqf={iq_before}"
        )

        move_pose(
            arm,
            p3,
            "3/3 J3 +4 DEGREE PHYSICAL PROOF",
            watch_joint=3,
        )

        j3_after = read_actual(
            arm,
            3,
        )

        iq_after = read_iqf(
            arm,
            3,
        )

        moved = (
            j3_after - j3_before
        )

        print()
        print(
            "J3 RESULT:"
        )

        print(
            f"  before = {j3_before:+.2f}°"
        )

        print(
            f"  after  = {j3_after:+.2f}°"
        )

        print(
            f"  moved  = {moved:+.2f}°"
        )

        print(
            f"  iqf    = {iq_after}"
        )

        # --------------------------------------------------------
        # FULL-ARM COORDINATED WORK LOOP
        #
        # J2/J3/J4 remain exactly at the proven elevated pose.
        #
        # J1/J5/J6 move together.
        #
        # Exact topology:
        #
        # P3 -> A -> B -> A -> P3
        # --------------------------------------------------------

        work_a = list(p3)

        work_a[4] = start[4] + WORK_DELTA
        work_a[5] = start[5] - WORK_DELTA

        work_b = list(p3)

        work_b[4] = start[4] - WORK_DELTA
        work_b[5] = start[5] + WORK_DELTA

        print()
        print("#" * 72)
        print("BEGIN TRIX LARGE-WORKSPACE COORDINATED CYCLE")
        print("#" * 72)

        move_pose(
            arm,
            work_a,
            "WORK 1/4: P3 -> WORK A  "
            "[J1 HOLDS; J5/J6 coordinated]",
            watch_joint=3,
        )

        move_pose(
            arm,
            work_b,
            "WORK 2/4: WORK A -> WORK B  "
            "[J1 HOLDS; J5/J6 coordinated]",
            watch_joint=3,
        )

        move_pose(
            arm,
            work_a,
            "WORK 3/4: EXACT REVERSE B -> A",
            watch_joint=3,
        )

        move_pose(
            arm,
            p3,
            "WORK 4/4: EXACT REVERSE A -> P3",
            watch_joint=3,
        )

        print()
        print("WORK LOOP COMPLETE.")
        print("J1 preposition + J2/J3/J4 clearance configuration preserved.")

        # --------------------------------------------------------
        # EXACT CHAIN RETURN
        #
        # Same speed limiter as outbound.
        # --------------------------------------------------------

        move_pose(
            arm,
            p2,
            "RETURN 1/3: J3 -> START J3",
            watch_joint=3,
        )

        move_pose(
            arm,
            p1,
            "RETURN 2/3: J4 -> START J4",
            watch_joint=4,
        )

        move_pose(
            arm,
            j1_pose,
            "RETURN 3/4: J2 -> START J2; J1 STILL PREPOSITIONED",
            watch_joint=2,
        )

        # --------------------------------------------------------
        # J1 RETURNS LAST.
        #
        # Nothing else in the chain moves during this segment.
        # --------------------------------------------------------

        print()
        print("#" * 72)
        print("FINAL TRIX RETURN: J1 COMES HOME LAST")
        print("#" * 72)

        move_pose(
            arm,
            start,
            "RETURN 4/4: J1 SLOWLY -> EXACT CAPTURED START",
            watch_joint=1,
        )

        # --------------------------------------------------------
        # Physical readback after complete return.
        # --------------------------------------------------------

        final2 = read_actual(
            arm,
            2,
        )

        final3 = read_actual(
            arm,
            3,
        )

        final4 = read_actual(
            arm,
            4,
        )

        print()
        print("FINAL PHYSICAL CHECK:")

        print(
            f"J2 start={start[1]:+.2f}° "
            f"actual={final2:+.2f}°"
        )

        print(
            f"J3 start={start[2]:+.2f}° "
            f"actual={final3:+.2f}°"
        )

        print(
            f"J4 start={start[3]:+.2f}° "
            f"actual={final4:+.2f}°"
        )

        print()
        print(
            f"J3 PHYSICAL EXCURSION ACHIEVED: {moved:+.2f}°"
        )

        print(
            "Trajectory will now complete the controlled "
            "return to the captured start."
        )

        print()
        print("=" * 72)
        print("FULL J1-J6 RETURN VERIFICATION")
        print("=" * 72)

        for joint in range(1, 7):

            actual = read_actual(
                arm,
                joint,
            )

            target = start[joint - 1]

            error = target - actual

            print(
                f"J{joint}: "
                f"start={target:+.2f}°  "
                f"final={actual:+.2f}°  "
                f"error={error:+.2f}°"
            )

        hold_until_ctrl_c(
            arm
        )

    except KeyboardInterrupt:

        print()
        print(
            "CTRL+C -> DISABLING ALL MOTORS"
        )

        try:
            arm.disable_motors()

        finally:
            print(
                "MOTORS DISABLED"
            )

    except Exception as exc:

        print()
        print(
            "ERROR:",
            repr(exc),
        )

        print(
            "DISABLING ALL MOTORS"
        )

        try:
            arm.disable_motors()

        finally:
            print(
                "MOTORS DISABLED"
            )


if __name__ == "__main__":
    main()
