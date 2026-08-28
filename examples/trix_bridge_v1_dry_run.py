#!/usr/bin/env python3

"""
TRiX end-to-end symbolic + execution-bridge dry run.

NO robot imports.
NO CAN.
NO motor commands.
"""

from datetime import datetime
from pathlib import Path
import json

from trix_runtime import (
    Action,
    Proposal,
    RobotState,
    TrixExecutionBridge,
    TrixProjector,
)


STAMP = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

RUN_DIR = (
    Path.home()
    / "trix_logs"
    / f"trix_bridge_v1_{STAMP}"
)

RUN_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG = RUN_DIR / "bridge_trace.jsonl"

trix = TrixProjector()
bridge = TrixExecutionBridge()


def execute_symbolically(
    episode,
    proposals,
):

    state = RobotState()

    print()
    print("=" * 82)
    print(f"EPISODE: {episode}")
    print("=" * 82)

    for step, proposal in enumerate(
        proposals,
        1,
    ):

        state_before = state

        decision = trix.evaluate(
            state_before,
            proposal,
        )

        command = bridge.build(
            state_before,
            decision,
        )

        state = trix.apply(
            state_before,
            decision,
        )

        print()
        print(
            f"{step:02d}. "
            f"{state_before.mode.value}"
            f" -> {proposal.action.value}"
        )

        if proposal.overrides:
            print(
                f"    proposed overrides: "
                f"{proposal.overrides}"
            )

        print(
            f"    TRiX decision: "
            f"{decision.decision.value}"
        )

        print(
            f"    reason: "
            f"{'; '.join(decision.reasons)}"
        )

        if command is None:

            print(
                "    EXECUTION BRIDGE: "
                "NO COMMAND"
            )

            executor_payload = None

        else:

            print(
                f"    EXECUTION BRIDGE: "
                f"{command.kind.value}"
            )

            if command.target_delta_deg:

                print(
                    "    J2-J6 target: "
                    f"{command.target_delta_deg}"
                )

            executor_payload = {
                "kind":
                    command.kind.value,

                "action":
                    command.action.value,

                "target_delta_deg":
                    command.target_delta_deg,

                "reason":
                    command.reason,
            }

        print(
            f"    next symbolic state: "
            f"{state.mode.value}"
        )

        row = {
            "episode": episode,
            "step": step,

            "state_before":
                state_before.mode.value,

            "proposal": {
                "action":
                    proposal.action.value,

                "overrides":
                    proposal.overrides,
            },

            "decision":
                decision.decision.value,

            "reasons":
                decision.reasons,

            "execution_bridge":
                executor_payload,

            "state_after":
                state.mode.value,
        }

        with LOG.open(
            "a",
            encoding="utf-8",
        ) as f:

            f.write(
                json.dumps(row)
                + "\n"
            )


# ============================================================
# 1. EXACT NOMINAL TABLETOP SEQUENCE
# ============================================================

execute_symbolically(
    "NOMINAL_TABLETOP",
    [
        Proposal(Action.APPROACH),
        Proposal(Action.PRESHAPE),
        Proposal(Action.LOW_HOVER),

        Proposal(Action.RETRACT),
        Proposal(Action.UNPRESHAPE),
        Proposal(Action.RETURN_SAFE),
    ],
)


# ============================================================
# 2. UNSAFE STATE TRANSITION
# ============================================================

execute_symbolically(
    "REJECT_DIRECT_LOW_HOVER",
    [
        Proposal(Action.LOW_HOVER),
    ],
)


# ============================================================
# 3. CONTINUOUS-ACTION PROJECTION
# ============================================================

execute_symbolically(
    "PROJECT_EXCESSIVE_APPROACH",
    [
        Proposal(
            Action.APPROACH,
            overrides={
                "J2": 50.0,
            },
        ),
    ],
)


# ============================================================
# 4. OLD UNSAFE J3-RISE BEHAVIOR
# ============================================================

execute_symbolically(
    "PROJECT_LOW_HOVER_J3_RISE",
    [
        Proposal(Action.APPROACH),
        Proposal(Action.PRESHAPE),

        Proposal(
            Action.LOW_HOVER,
            overrides={
                "J3": 9.0,
            },
        ),
    ],
)


print()
print("#" * 82)
print("TRIX EXECUTION BRIDGE V1 COMPLETE")
print("#" * 82)

print()
print(
    f"Trace: {LOG}"
)

print()
print(
    "Executor-facing joint set:"
)

print(
    "    J2 J3 J4 J5 J6"
)

print()
print(
    "NO CAN OPENED."
)

print(
    "NO ROBOT COMMANDS SENT."
)
