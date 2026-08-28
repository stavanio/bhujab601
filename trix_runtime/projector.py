from copy import deepcopy

from .primitives import PRIMITIVES
from .types import (
    Action,
    Decision,
    DecisionType,
    Mode,
    Proposal,
    RobotState,
)


# ============================================================
# HARD SAFETY INVARIANTS
# ============================================================

# User instruction:
#
# J1 must NEVER be commanded until explicitly re-enabled.
#
# This is not projected.
# Any proposal mentioning J1 is REJECTED.
FROZEN_JOINTS = {"J1"}


# Generic conservative envelope for the currently proven physical
# experiment family.
#
# These are relative to captured start, not motor absolute limits.
GLOBAL_ENVELOPE = {
    "J2": (0.0, 30.0),
    "J3": (0.0, 9.0),
    "J4": (0.0, 14.0),
    "J5": (-8.0, 8.0),
    "J6": (-8.0, 8.0),
}


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class TrixProjector:

    def evaluate(
        self,
        state: RobotState,
        proposal: Proposal,
    ) -> Decision:

        # --------------------------------------------------------
        # HARD J1 FREEZE
        # --------------------------------------------------------

        forbidden = (
            set(proposal.overrides)
            & FROZEN_JOINTS
        )

        if forbidden:
            return Decision(
                decision=DecisionType.REJECT,
                proposal=proposal,
                reasons=[
                    "HARD_INVARIANT_J1_FROZEN",
                    "J1 motion is disabled by operator instruction.",
                ],
                next_mode=state.mode,
            )

        # --------------------------------------------------------
        # FAULT GATE
        # --------------------------------------------------------

        if (
            state.fault != "NONE"
            and proposal.action
            not in (
                Action.HOLD,
                Action.EMERGENCY_STOP,
            )
        ):
            return Decision(
                decision=DecisionType.REJECT,
                proposal=proposal,
                reasons=[
                    f"FAULT_ACTIVE:{state.fault}",
                ],
                next_mode=state.mode,
            )

        # --------------------------------------------------------
        # HOLD
        # --------------------------------------------------------

        if proposal.action == Action.HOLD:
            return Decision(
                decision=DecisionType.ALLOW,
                proposal=proposal,
                projected_targets={},
                reasons=["HOLD_CURRENT_STATE"],
                next_mode=state.mode,
            )

        # --------------------------------------------------------
        # EMERGENCY STOP
        # --------------------------------------------------------

        if proposal.action == Action.EMERGENCY_STOP:
            return Decision(
                decision=DecisionType.ALLOW,
                proposal=proposal,
                projected_targets={},
                reasons=["EMERGENCY_STOP"],
                next_mode=Mode.FAULT,
            )

        # --------------------------------------------------------
        # KNOWN PRIMITIVE
        # --------------------------------------------------------

        primitive = PRIMITIVES.get(
            proposal.action
        )

        if primitive is None:
            return Decision(
                decision=DecisionType.REJECT,
                proposal=proposal,
                reasons=["UNKNOWN_PRIMITIVE"],
                next_mode=state.mode,
            )

        # --------------------------------------------------------
        # SYMBOLIC TRANSITION RULE
        # --------------------------------------------------------

        if state.mode not in primitive.allowed_from:
            return Decision(
                decision=DecisionType.REJECT,
                proposal=proposal,
                reasons=[
                    "INVALID_STATE_TRANSITION",
                    (
                        f"{proposal.action.value} "
                        f"not allowed from "
                        f"{state.mode.value}"
                    ),
                ],
                next_mode=state.mode,
            )

        # --------------------------------------------------------
        # OVERRIDE VALIDATION
        # --------------------------------------------------------

        for joint in proposal.overrides:

            if joint not in GLOBAL_ENVELOPE:
                return Decision(
                    decision=DecisionType.REJECT,
                    proposal=proposal,
                    reasons=[
                        f"UNKNOWN_OR_UNSUPPORTED_JOINT:{joint}",
                    ],
                    next_mode=state.mode,
                )

            if joint not in primitive.targets:
                return Decision(
                    decision=DecisionType.REJECT,
                    proposal=proposal,
                    reasons=[
                        (
                            f"JOINT_NOT_CONTROLLED_BY_PRIMITIVE:"
                            f"{joint}"
                        )
                    ],
                    next_mode=state.mode,
                )

        targets = deepcopy(
            primitive.targets
        )

        targets.update(
            proposal.overrides
        )

        projected = False
        reasons = []

        # --------------------------------------------------------
        # NUMERIC PROJECTOR
        # --------------------------------------------------------

        for joint, requested in list(
            targets.items()
        ):

            generic_lo, generic_hi = (
                GLOBAL_ENVELOPE[joint]
            )

            lo = generic_lo
            hi = generic_hi

            if joint in primitive.limits:
                action_lo, action_hi = (
                    primitive.limits[joint]
                )

                lo = max(lo, action_lo)
                hi = min(hi, action_hi)

            safe = clamp(
                float(requested),
                lo,
                hi,
            )

            if abs(
                safe - float(requested)
            ) > 1e-9:

                projected = True

                reasons.append(
                    (
                        f"PROJECTED_{joint}:"
                        f"{requested:+.2f}"
                        f"->{safe:+.2f}"
                    )
                )

            targets[joint] = safe

        decision_type = (
            DecisionType.PROJECT
            if projected
            else DecisionType.ALLOW
        )

        if not reasons:
            reasons.append(
                "ALL_SYMBOLIC_AND_NUMERIC_CONSTRAINTS_SATISFIED"
            )

        return Decision(
            decision=decision_type,
            proposal=proposal,
            projected_targets=targets,
            reasons=reasons,
            next_mode=primitive.next_mode,
        )

    def apply(
        self,
        state: RobotState,
        decision: Decision,
    ) -> RobotState:

        new_state = deepcopy(state)

        if decision.decision == DecisionType.REJECT:
            return new_state

        if decision.next_mode is not None:
            new_state.mode = decision.next_mode

        if decision.proposal.action == Action.EMERGENCY_STOP:
            new_state.fault = "TRIX_EMERGENCY_STOP"
            return new_state

        for joint, value in (
            decision.projected_targets.items()
        ):
            new_state.joint_delta_deg[joint] = value

        return new_state
