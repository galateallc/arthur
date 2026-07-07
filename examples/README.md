# Examples — Kindalive on Real Hardware

`FaceState` — the 12-muscle facial vector Kindalive computes from its
chemical state — is renderer-agnostic. The web UI draws it as a virtual
LED dot-matrix; these examples drive physical hardware from the exact
same vector. Both run **without any hardware**: if the driver library
isn't installed they render to the terminal, so you can develop the
mapping on a laptop and copy the file to a Raspberry Pi unchanged.

| Example | Hardware | Driver |
|---------|----------|--------|
| `led_matrix_face.py` | MAX7219 8x8 LED matrix (SPI) | `pip install luma.led_matrix` |
| `servo_face.py` | PCA9685 16-channel servo board (I2C) | `pip install adafruit-circuitpython-servokit` |

```bash
pip install kindalive            # zero-dependency core is enough
python3 examples/led_matrix_face.py --mood joy
python3 examples/servo_face.py --mood anger
```

Each demo injects a chemical impulse recipe (joy / fear / anger /
sadness), then lets the neurochemical engine decay in real time — you
watch the expression fade back to the robot's baseline, exactly like the
web face does.

The interesting part to copy into your own robot is small: get a
`FaceState`, map its 12 floats to whatever actuators you have.

```python
from kindalive.expression.face import FaceProjection

face = FaceProjection.compute(engine.state)   # 12 floats in [0, 1]
my_renderer.draw(face.lip_corner_pull, face.jaw_open, ...)
```
