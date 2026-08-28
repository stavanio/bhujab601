#!/usr/bin/env python3

"""
TRiX physical-target adapter dry run.

NO rebot.
NO CAN.
NO motors.

Simulates an arbitrary relocated-arm J1 position.
"""

from trix_runtime import (
    Action,
    Proposal,
    RobotState,
    TrixExecutionBridge,
    TrixPhysicalTargetAdapter,
    TrixProjector,
)


CAPTURED_PHYSICAL_START = [
    +37.42,   # deliberately arbitrary relocated J1
    +0.11,
    +0.27,
    -1.94,
    -1.68,
    -3.44,
    +1.55,
]


trix = TrixProjector()
bridge = TrixExecutionBridge()

adapter = TrixPhysicalTargetAdapter(
    CAPTURED_PHYSICAL_START
)

state = RobotState()


print("=" * 86)
print("TRIX PHYSICAL TARGET ADAPTER V1")
print("=" * 86)

print()
print(
    "Simulated captured physical start:"
)

for i, value in enumerate(
    CAPTURED_PHYSICAL_START,
    1,
):
    print(
        f"    J{i}: {value:+.2f} deg"
    )

print()
print(
    f"J1 FROZEN AT: "
    f"{adapter.frozen_j1_deg:+.2f} deg"
)

print()


actions = (
    Action.APPROACH,
    Action.PRESHAPE,
    Action.LOW_HOVER,
    Action.RETRACT,
    Action.UNPRESHAPE,
    Action.RETURN_SAFE,
)


for step, action in enumerate(
    actions,
    1,
):

    proposal = Proposal(
        action
    )

    decision = trix.evaluate(
        state,
        proposal,
    )

    command = bridge.build(
        state,
        decision,
    )

    physical = adapter.build(
        command
    )

    next_state = trix.apply(
        state,
        decision,
    )

    print(
        f"{step}. {state.mode.value}"
        f" -> {action.value}"
    )

    print(
        f"   TRiX: "
        f"{decision.decision.value}"
    )

    if physical is None:

        print(
            "   PHYSICAL TARGET: NONE"
        )

    else:

        adapter.assert_j1_invariant(
            physical.angles_deg
        )

        print(
            "   ABSOLUTE TARGET:"
        )

        for i, value in enumerate(
            physical.angles_deg,
            1,
        ):
            frozen = (
                "  <-- FROZEN"
                if i == 1
                else ""
            )

            print(
                f"      J{i}: "
                f"{value:+7.2f} deg"
                f"{frozen}"
            )

    state = next_state

    print()


print("=" * 86)
print("PHYSICAL ADAPTER DRY RUN COMPLETE")
print(
    "J1 remained exactly "
    f"{CAPTURED_PHYSICAL_START[0]:+.2f} deg "
    "for every target."
)
print("ZERO CAN / ZERO MOTOR COMMANDS")
print("=" * 86)
