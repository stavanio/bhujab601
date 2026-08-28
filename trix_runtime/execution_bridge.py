from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from .types import (
    Action,
    Decision,
    DecisionType,
    RobotState,
)


# The physical execution interface intentionally contains ONLY
# the joints that the current TRiX experiment is allowed to use.
SUPPORTED_JOINTS = (
    "J2",
    "J3",
    "J4",
    "J5",
    "J6",
)


class BridgeKind(str, Enum):
    MOVE = "MOVE"
    NO_MOTION = "NO_MOTION"
    STOP_REQUEST = "STOP_REQUEST"


class BridgeSafetyError(RuntimeError):
    pass


@dataclass
class BridgeCommand:
    kind: BridgeKind
    action: Action
    target_delta_deg: Dict[str, float]
    reason: str


class TrixExecutionBridge:
    """
    Convert an approved TRiX decision into an executor-facing command.

    This module:
      - does NOT import rebot
      - does NOT import socketcan
      - does NOT open CAN
      - does NOT know about motor IDs
      - only exposes J2-J6
    """

    def build(
        self,
        state_before: RobotState,
        decision: Decision,
    ) -> Optional[BridgeCommand]:

        # A rejected proposal must produce NO actuator command.
        if decision.decision == DecisionType.REJECT:
            return None

        # Defensive boundary:
        # even if an upstream software bug somehow creates an
        # invalid Decision object, unsupported joints may not
        # cross this bridge.
        unsupported = (
            set(decision.projected_targets)
            - set(SUPPORTED_JOINTS)
        )

        if unsupported:
            raise BridgeSafetyError(
                "UNSUPPORTED_JOINT_AT_EXECUTION_BOUNDARY:"
                + ",".join(sorted(unsupported))
            )

        if decision.proposal.action == Action.EMERGENCY_STOP:
            return BridgeCommand(
                kind=BridgeKind.STOP_REQUEST,
                action=decision.proposal.action,
                target_delta_deg={},
                reason="TRIX_EMERGENCY_STOP_REQUEST",
            )

        # Symbolic actions that intentionally cause no joint motion.
        if decision.proposal.action in (
            Action.HOLD,
            Action.ENGAGE,
        ):
            return BridgeCommand(
                kind=BridgeKind.NO_MOTION,
                action=decision.proposal.action,
                target_delta_deg={},
                reason="SYMBOLIC_ACTION_NO_JOINT_MOTION",
            )

        # Build a FULL J2-J6 target pose by starting with the
        # currently accepted symbolic state and applying only the
        # approved/projected changes from TRiX.
        target = {
            joint: float(
                state_before.joint_delta_deg[joint]
            )
            for joint in SUPPORTED_JOINTS
        }

        for joint, value in (
            decision.projected_targets.items()
        ):
            target[joint] = float(value)

        return BridgeCommand(
            kind=BridgeKind.MOVE,
            action=decision.proposal.action,
            target_delta_deg=target,
            reason="ADMISSIBLE_TRIX_TARGET",
        )
