"""
Known-good conservative first-motion test for B601-RS.

Preconditions:
- B601-RS already zeroed and parameter-initialized.
- can0 UP at 1 Mbps.
- MotorBridge Studio/gateway not acting as a second controller.
- Workspace clear and arm securely mounted.

Motion:
- J1 only
- 0 -> +3 degrees
- max speed 1 degree/second
- return to zero
- disable
"""

import time
from rebot import ReBotRSMITController

arm = ReBotRSMITController()

try:
    print("Starting controller...")
    arm.start(enable_esc=False, install_signal_handlers=False)

    arm.set_max_speeds([1.0] * 7)

    print("Moving J1 from 0° to +3°...")
    arm.set_joint_angle(1, 3.0)

    while abs(arm.get_command_angles()[0] - 3.0) > 0.05:
        time.sleep(0.05)

    time.sleep(0.5)

    print("Returning J1 to 0°...")
    arm.set_joint_angle(1, 0.0)

    while abs(arm.get_command_angles()[0]) > 0.05:
        time.sleep(0.05)

    time.sleep(0.5)
    print("Motion complete.")

finally:
    arm.stop(return_to_zero=False, wait=True)
    print("Motors disabled.")
