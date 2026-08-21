# First controlled motion

A deliberately conservative first-motion test was used instead of immediately running the larger vendor example.

## Environment

```bash
git clone https://github.com/LAN-GER/rebot_control.git
cd rebot_control

uv venv
source .venv/bin/activate
uv pip install motorbridge pynput pyyaml
```

Verify:

```bash
python -c "import motorbridge, pynput, yaml; print('OK')"
```

## Controller isolation

Before running the Python motion test:

- disconnect MotorBridge Studio;
- stop `motorbridge-gateway`;
- leave arm power/CAN physically connected.

## Proven first motion

The sequence successfully executed:

```text
all motors registered
all motors switched to MIT mode
all motors enabled
J1 moved +3°
J1 returned to 0°
all motors disabled
safe stop complete
```

Speed limit: **1 degree/second**.

## Example

See [`examples/tiny_first_move.py`](../examples/tiny_first_move.py).

## Verify home after motion

Use the upstream example:

```bash
cd ~/rebot_control
source .venv/bin/activate
python examples/read_joint_angles.py
```

After commissioning, actual measured rest values were stable around:

```text
[0.54, 0.00, 0.00, 0.00, -0.02, -0.03, -0.06] deg
```

Do not repeatedly re-zero merely to chase tiny encoder residuals.
