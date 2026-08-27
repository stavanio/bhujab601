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

START = np.array([
    -2.16,
    +0.03,
    +0.25,
    -2.00,
    -1.69,
    -3.47,
], dtype=float)

J1_DELTA = 110.0

model = pin.buildModelFromUrdf(str(URDF))
data = model.createData()

fid = model.getFrameId(EE_FRAME)

if fid >= len(model.frames):
    raise RuntimeError(f"Frame {EE_FRAME!r} not found")


def fk(deg6):
    q = np.zeros(model.nq)
    q[:6] = np.radians(deg6)

    if np.any(q < model.lowerPositionLimit) or \
       np.any(q > model.upperPositionLimit):
        return None

    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)

    xyz = np.array(data.oMf[fid].translation, dtype=float)

    radial = math.hypot(xyz[0], xyz[1])

    return xyz, radial


# ------------------------------------------------------------
# J1 workspace pose establishes the horizontal "forward" ray.
# ------------------------------------------------------------

j1_pose = START.copy()
j1_pose[0] += J1_DELTA

base = fk(j1_pose)

if base is None:
    raise RuntimeError("J1 workspace pose invalid")

base_xyz, base_radial = base

forward_xy = base_xyz[:2]
forward_xy /= np.linalg.norm(forward_xy)


def metrics(q):
    result = fk(q)

    if result is None:
        return None

    xyz, radial = result

    # Distance along the actual horizontal direction established by J1.
    forward = float(np.dot(xyz[:2], forward_xy))

    return xyz, radial, forward


print("=" * 110)
print("J1 WORKSPACE REFERENCE")
print("=" * 110)

print(
    f"J1 workspace XYZ = "
    f"[{base_xyz[0]:+.3f}, "
    f"{base_xyz[1]:+.3f}, "
    f"{base_xyz[2]:+.3f}] m"
)

print(f"radial = {base_radial:.3f} m")

print()
print("=" * 110)
print("URDF JOINT LIMITS")
print("=" * 110)

for i in range(6):
    lo = math.degrees(model.lowerPositionLimit[i])
    hi = math.degrees(model.upperPositionLimit[i])

    print(
        f"J{i+1}: "
        f"{lo:+8.1f}° .. {hi:+8.1f}°"
    )


# ------------------------------------------------------------
# Wide OFFLINE search.
#
# Important:
# We are deliberately allowing NEGATIVE J3 and NEGATIVE J4.
#
# No values below are robot commands.
# ------------------------------------------------------------

rows = []

for j2d in np.arange(+8.0, +42.1, 2.0):

    for j3d in np.arange(-40.0, +12.1, 2.0):

        for j4d in np.arange(-30.0, +30.1, 2.0):

            q = START.copy()

            q[0] += J1_DELTA
            q[1] += j2d
            q[2] += j3d
            q[3] += j4d

            result = metrics(q)

            if result is None:
                continue

            xyz, radial, forward = result

            rows.append({
                "j2": j2d,
                "j3": j3d,
                "j4": j4d,
                "xyz": xyz,
                "radial": radial,
                "forward": forward,
            })


print()
print("=" * 110)
print("MAXIMUM HORIZONTAL REACH — REGARDLESS OF HEIGHT")
print("=" * 110)

best_reach = sorted(
    rows,
    key=lambda r: r["forward"],
    reverse=True
)

for i, r in enumerate(best_reach[:20], 1):

    xyz = r["xyz"]

    print(
        f"{i:2d}. "
        f"J2Δ={r['j2']:+5.1f}° "
        f"J3Δ={r['j3']:+5.1f}° "
        f"J4Δ={r['j4']:+5.1f}° | "
        f"forward={r['forward']*100:6.1f} cm | "
        f"radial={r['radial']*100:6.1f} cm | "
        f"Z={xyz[2]*100:6.1f} cm | "
        f"XYZ=["
        f"{xyz[0]:+.3f}, "
        f"{xyz[1]:+.3f}, "
        f"{xyz[2]:+.3f}]"
    )


# ------------------------------------------------------------
# Now find maximum reach in useful LOW-Z bands.
# These are MODEL Z values, NOT assumed table clearances.
# ------------------------------------------------------------

bands = [
    (0.04, 0.08),
    (0.08, 0.12),
    (0.12, 0.16),
    (0.16, 0.20),
]

for zlo, zhi in bands:

    candidates = [
        r for r in rows
        if zlo <= r["xyz"][2] < zhi
    ]

    candidates.sort(
        key=lambda r: r["forward"],
        reverse=True
    )

    print()
    print("=" * 110)
    print(
        f"BEST HORIZONTAL REACH WITH "
        f"{zlo*100:.0f} cm <= MODEL Z < {zhi*100:.0f} cm"
    )
    print("=" * 110)

    if not candidates:
        print("No candidates")
        continue

    for i, r in enumerate(candidates[:12], 1):

        xyz = r["xyz"]

        print(
            f"{i:2d}. "
            f"J2Δ={r['j2']:+5.1f}° "
            f"J3Δ={r['j3']:+5.1f}° "
            f"J4Δ={r['j4']:+5.1f}° | "
            f"forward={r['forward']*100:6.1f} cm | "
            f"Z={xyz[2]*100:6.1f} cm"
        )


# ------------------------------------------------------------
# Pareto frontier:
# pose is useful if another pose is not BOTH farther and lower.
# ------------------------------------------------------------

pareto = []

for a in rows:

    dominated = False

    for b in rows:

        if (
            b["forward"] >= a["forward"]
            and b["xyz"][2] <= a["xyz"][2]
            and (
                b["forward"] > a["forward"]
                or b["xyz"][2] < a["xyz"][2]
            )
        ):
            dominated = True
            break

    if not dominated:
        pareto.append(a)

pareto.sort(key=lambda r: r["xyz"][2])

print()
print("=" * 110)
print("REACH-vs-HEIGHT PARETO FRONTIER")
print("=" * 110)

for r in pareto:

    xyz = r["xyz"]

    print(
        f"J2Δ={r['j2']:+5.1f}° "
        f"J3Δ={r['j3']:+5.1f}° "
        f"J4Δ={r['j4']:+5.1f}° | "
        f"forward={r['forward']*100:6.1f} cm | "
        f"Z={xyz[2]*100:6.1f} cm"
    )

print()
print("OFFLINE ONLY — ZERO CAN / ZERO MOTOR COMMANDS")
