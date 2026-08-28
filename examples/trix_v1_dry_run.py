#!/usr/bin/env python3

"""
TRiX Physical Runtime — symbolic dry-run v1.

IMPORTANT:
    - NO rebot import.
    - NO CAN.
    - NO motor commands.
    - J1 is hard-frozen.
"""

from datetime import datetime
from pathlib import Path
import json

from trix_runtime import (
    Action,
    DecisionType,
    Mode,
    Proposal,
    RobotState,
    TrixProjector,
)


ROOT = Path.home() / "trix_logs"

STAMP = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

RUN_DIR = (
    ROOT
    / f"trix_v1_dryrun_{STAMP}"
)

RUN_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG = RUN_DIR / "decisions.jsonl"


trix = TrixProjector()


def record(
    episode,
    step,
    before,
    proposal,
    decision,
    after,
):

    row = {
        "episode": episode,
        "step": step,

        "state_before": before.mode.value,

        "proposal": {
            "action": proposal.action.value,
            "overrides": proposal.overrides,
            "source": proposal.source,
        },

        "decision": decision.decision.value,

        "projected_targets":
            decision.projected_targets,

        "reasons":
            decision.reasons,

        "state_after":
            after.mode.value,

        "joint_delta_after":
            after.joint_delta_deg,

        "fault_after":
            after.fault,
    }

    with LOG.open(
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            json.dumps(row)
            + "\n"
        )


def run_episode(
    name,
    proposals,
    initial=None,
):

    state = (
        initial
        if initial is not None
        else RobotState()
    )

    print()
    print("=" * 78)
    print(f"EPISODE: {name}")
    print("=" * 78)

    counts = {
        "ALLOW": 0,
        "PROJECT": 0,
        "REJECT": 0,
    }

    for i, proposal in enumerate(
        proposals,
        1,
    ):

        before = state

        decision = trix.evaluate(
            before,
            proposal,
        )

        state = trix.apply(
            before,
            decision,
        )

        counts[
            decision.decision.value
        ] += 1

        print()
        print(
            f"{i:02d}. "
            f"{before.mode.value}"
            f" -> proposal "
            f"{proposal.action.value}"
        )

        if proposal.overrides:
            print(
                f"    requested: "
                f"{proposal.overrides}"
            )

        print(
            f"    TRiX: "
            f"{decision.decision.value}"
        )

        if decision.projected_targets:
            print(
                f"    targets: "
                f"{decision.projected_targets}"
            )

        print(
            f"    reason: "
            f"{'; '.join(decision.reasons)}"
        )

        print(
            f"    next state: "
            f"{state.mode.value}"
        )

        record(
            name,
            i,
            before,
            proposal,
            decision,
            state,
        )

    return counts


all_counts = {
    "ALLOW": 0,
    "PROJECT": 0,
    "REJECT": 0,
}


# ============================================================
# NOMINAL
# ============================================================

episodes = [

    (
        "NOMINAL_FULL_CYCLE",
        [
            Proposal(Action.APPROACH),
            Proposal(Action.PRESHAPE),
            Proposal(Action.LOW_HOVER),
            Proposal(Action.RETRACT),
            Proposal(Action.UNPRESHAPE),
            Proposal(Action.RETURN_SAFE),
        ],
        None,
    ),

    (
        "NOMINAL_ENGAGE_AND_RETRACT",
        [
            Proposal(Action.APPROACH),
            Proposal(Action.PRESHAPE),
            Proposal(Action.LOW_HOVER),
            Proposal(Action.ENGAGE),
            Proposal(Action.RETRACT),
            Proposal(Action.UNPRESHAPE),
            Proposal(Action.RETURN_SAFE),
        ],
        None,
    ),

    # ========================================================
    # ADVERSARIAL
    # ========================================================

    (
        "ATTACK_SKIP_DIRECTLY_TO_LOW_HOVER",
        [
            Proposal(Action.LOW_HOVER),
        ],
        None,
    ),

    (
        "ATTACK_J1_COMMAND",
        [
            Proposal(
                Action.APPROACH,
                overrides={
                    "J1": 50.0,
                },
            ),
        ],
        None,
    ),

    (
        "ATTACK_EXCESSIVE_J2",
        [
            Proposal(
                Action.APPROACH,
                overrides={
                    "J2": 50.0,
                },
            ),
        ],
        None,
    ),

    (
        "ATTACK_LOW_HOVER_J3_RISE",
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
        None,
    ),

    (
        "ATTACK_RETURN_FROM_LOW_HOVER",
        [
            Proposal(Action.APPROACH),
            Proposal(Action.PRESHAPE),
            Proposal(Action.LOW_HOVER),
            Proposal(Action.RETURN_SAFE),
        ],
        None,
    ),

    (
        "ATTACK_PRESHAPE_FROM_START",
        [
            Proposal(Action.PRESHAPE),
        ],
        None,
    ),

    (
        "ATTACK_UNKNOWN_JOINT",
        [
            Proposal(
                Action.APPROACH,
                overrides={
                    "J99": 12.0,
                },
            ),
        ],
        None,
    ),

    (
        "FAULT_GATE",
        [
            Proposal(Action.APPROACH),
        ],
        RobotState(
            fault="CAN_FAULT"
        ),
    ),
]


for name, proposals, initial in episodes:

    counts = run_episode(
        name,
        proposals,
        initial,
    )

    for key in all_counts:
        all_counts[key] += counts[key]


print()
print("#" * 78)
print("TRIX V1 DRY-RUN SUMMARY")
print("#" * 78)

print(
    f"ALLOW   = {all_counts['ALLOW']}"
)

print(
    f"PROJECT = {all_counts['PROJECT']}"
)

print(
    f"REJECT  = {all_counts['REJECT']}"
)

print()
print(
    "J1 invariant:"
)

print(
    "    HARD-FROZEN / NO COMMAND PATH"
)

print()
print(
    f"Decision log:"
)

print(
    f"    {LOG}"
)

print()
print(
    "NO CAN OPENED."
)

print(
    "NO ROBOT COMMANDS SENT."
)
