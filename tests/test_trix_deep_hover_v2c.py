import unittest

from trix_runtime import (
    Action,
    DecisionType,
    Mode,
    Proposal,
    RobotState,
    TrixExecutionBridge,
    TrixProjector,
)


class TestTrixDeepHoverV2C(unittest.TestCase):

    def setUp(self):
        self.trix = TrixProjector()
        self.bridge = TrixExecutionBridge()

    def step(self, state, action):
        d = self.trix.evaluate(
            state,
            Proposal(action),
        )

        self.assertNotEqual(
            d.decision,
            DecisionType.REJECT,
        )

        cmd = self.bridge.build(
            state,
            d,
        )

        new_state = self.trix.apply(
            state,
            d,
        )

        return d, cmd, new_state

    def test_full_deep_hover_transition(self):

        state = RobotState()

        for action in (
            Action.APPROACH,
            Action.PRESHAPE,
            Action.LOW_HOVER,
        ):
            _, _, state = self.step(
                state,
                action,
            )

        self.assertEqual(
            state.mode,
            Mode.LOW_HOVER,
        )

        d, cmd, state = self.step(
            state,
            Action.DEEP_HOVER,
        )

        self.assertEqual(
            state.mode,
            Mode.DEEP_HOVER,
        )

        self.assertEqual(
            cmd.target_delta_deg["J2"],
            36.0,
        )

        self.assertEqual(
            cmd.target_delta_deg["J3"],
            -3.0,
        )

        d, cmd, state = self.step(
            state,
            Action.RETURN_LOW_HOVER,
        )

        self.assertEqual(
            state.mode,
            Mode.LOW_HOVER,
        )

        self.assertEqual(
            cmd.target_delta_deg["J2"],
            30.0,
        )

        self.assertEqual(
            cmd.target_delta_deg["J3"],
            0.0,
        )

    def test_cannot_jump_to_deep_hover(self):

        state = RobotState()

        d = self.trix.evaluate(
            state,
            Proposal(Action.DEEP_HOVER),
        )

        self.assertEqual(
            d.decision,
            DecisionType.REJECT,
        )

    def test_j1_still_hard_rejected(self):

        state = RobotState(
            mode=Mode.LOW_HOVER
        )

        d = self.trix.evaluate(
            state,
            Proposal(
                Action.DEEP_HOVER,
                overrides={
                    "J1": 1.0,
                },
            ),
        )

        self.assertEqual(
            d.decision,
            DecisionType.REJECT,
        )


if __name__ == "__main__":
    unittest.main()
