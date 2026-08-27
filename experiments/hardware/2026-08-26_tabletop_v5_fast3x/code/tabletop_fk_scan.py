from pathlib import Path
import math
import numpy as np
import pinocchio as pin

URDF = Path.home() / (
    "reBotArm_control_py/urdf/"
    "00-arm-rs_asm-v3/urdf/"
    "00-arm-rs_asm-v3.urdf"
)

EE_FRAME = "gripper_end"

# Exact captured start from successful V4 run.
START = np.array([
    -2.16,   # J1
    +0.03,   # J2
    +0.25,   # J3
    -2.00,   # J4
    -1.69,   # J5
    -3.47,   # J6
])

model = pin.buildModelFromUrdf(str(URDF))
data = model.createData()

fid = model.getFrameId(EE_FRAME)

if fid >= len(model.frames):
    raise RuntimeError(f"Frame {EE_FRAME!r} not found")

def fk(deg6):
    q = np.zeros(model.nq)
    q[:6] = np.radians(deg6)

    # Gripper finger coordinates remain neutral.
    if np.any(q < model.lowerPositionLimit) or np.any(q > model.upperPositionLimit):
        return None

    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)

    T = data.oMf[fid]
    xyz = np.array(T.translation, dtype=float)

    x, y, z = xyz
    radial = math.hypot(x, y)

    return xyz, radial

def show(name, q):
    out = fk(q)
    if out is None:
        print(f"{name:<18} OUTSIDE MODEL LIMITS")
        return

    xyz, r = out
    print(
        f"{name:<18} "
        f"J=[{', '.join(f'{v:+7.2f}' for v in q)}]  "
        f"XYZ=[{xyz[0]:+.3f}, {xyz[1]:+.3f}, {xyz[2]:+.3f}] m  "
        f"radial={r:.3f} m"
    )

# ------------------------------------------------------------------
# Reconstruct successful V4 stages.
# ------------------------------------------------------------------

p0 = START.copy()

p1 = START.copy()
p1[0] += 110.0

p2 = p1.copy()
p2[1] += 10.0

p3a = p2.copy()
p3a[3] += 10.0

p3 = p3a.copy()
p3[2] += 9.0

print("=" * 100)
print("SUCCESSFUL V4 FK RECONSTRUCTION")
print("=" * 100)

show("START", p0)
show("J1 +110", p1)
show("J2 +10", p2)
show("J4 +10", p3a)
show("J3 +9", p3)

baseline = fk(p3)

if baseline is None:
    raise RuntimeError("Successful V4 pose is outside URDF model limits")

base_xyz, base_r = baseline

print()
print("=" * 100)
print("TABLETOP SEARCH")
print("Looking for poses FARTHER OUT and LOWER than successful V4")
print("=" * 100)

candidates = []

# J1 remains at successful +110 degree preposition.
#
# Search deliberately includes smaller/negative J3 values because
# positive J3 has physically behaved like a rise on this arm.
#
# OFFLINE ONLY -- these values are NOT robot commands.

for j2_delta in np.arange(10.0, 30.1, 2.0):
    for j3_delta in np.arange(-6.0, 12.1, 2.0):
        for j4_delta in np.arange(8.0, 30.1, 2.0):

            q = START.copy()

            q[0] += 110.0
            q[1] += j2_delta
            q[2] += j3_delta
            q[3] += j4_delta

            result = fk(q)

            if result is None:
                continue

            xyz, radial = result

            reach_gain = radial - base_r
            drop = base_xyz[2] - xyz[2]

            # We only care about candidates that improve BOTH.
            if reach_gain <= 0.0:
                continue

            if drop <= 0.0:
                continue

            # Equal physical weighting: one cm outward is worth
            # one cm downward for this exploratory ranking.
            score = reach_gain + drop

            candidates.append(
                (
                    score,
                    reach_gain,
                    drop,
                    radial,
                    xyz[2],
                    j2_delta,
                    j3_delta,
                    j4_delta,
                    xyz,
                )
            )

candidates.sort(reverse=True, key=lambda row: row[0])

print()
print(
    f"Successful V4 baseline:"
    f" radial={base_r:.3f} m,"
    f" Z={base_xyz[2]:.3f} m"
)

print()
print("TOP 20 FARTHER + LOWER CANDIDATES")
print()

print(
    " rank | J2Δ   J3Δ   J4Δ | "
    "reach gain | Z drop | radial | EE Z   | XYZ"
)

print("-" * 100)

for i, row in enumerate(candidates[:20], start=1):
    (
        score,
        reach_gain,
        drop,
        radial,
        z,
        j2,
        j3,
        j4,
        xyz,
    ) = row

    print(
        f"{i:5d} | "
        f"{j2:+5.1f} {j3:+5.1f} {j4:+5.1f} | "
        f"{reach_gain*100:+8.1f} cm | "
        f"{drop*100:+6.1f} cm | "
        f"{radial:.3f} m | "
        f"{z:.3f} m | "
        f"[{xyz[0]:+.3f}, {xyz[1]:+.3f}, {xyz[2]:+.3f}]"
    )

print()
print("OFFLINE FK ONLY — NO CAN / NO ROBOT COMMANDS")
