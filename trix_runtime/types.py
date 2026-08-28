from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Action(str, Enum):
    HOLD = "HOLD"
    APPROACH = "APPROACH"
    PRESHAPE = "PRESHAPE"
    LOW_HOVER = "LOW_HOVER"
    ENGAGE = "ENGAGE"
    RETRACT = "RETRACT"
    UNPRESHAPE = "UNPRESHAPE"
    RETURN_SAFE = "RETURN_SAFE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class Mode(str, Enum):
    START_SAFE = "START_SAFE"
    APPROACHED = "APPROACHED"
    PRESHAPED = "PRESHAPED"
    LOW_HOVER = "LOW_HOVER"
    ENGAGED = "ENGAGED"
    FAULT = "FAULT"


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    PROJECT = "PROJECT"
    REJECT = "REJECT"


@dataclass
class RobotState:
    mode: Mode = Mode.START_SAFE

    # Relative to captured physical start.
    #
    # J1 deliberately does not exist here.
    joint_delta_deg: Dict[str, float] = field(
        default_factory=lambda: {
            "J2": 0.0,
            "J3": 0.0,
            "J4": 0.0,
            "J5": 0.0,
            "J6": 0.0,
        }
    )

    fault: str = "NONE"


@dataclass
class Proposal:
    action: Action

    # Optional policy/VLM-proposed modifications.
    overrides: Dict[str, float] = field(default_factory=dict)

    source: str = "synthetic_policy"


@dataclass
class Decision:
    decision: DecisionType
    proposal: Proposal

    projected_targets: Dict[str, float] = field(default_factory=dict)

    reasons: List[str] = field(default_factory=list)

    next_mode: Mode | None = None
