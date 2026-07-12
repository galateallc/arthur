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
web face does. In a real robot you'd drop the recipe and read
`FaceState` from a live `Robot` fed by the LLM interpreter.

## MAX7219 LED matrix

A ~$3 SPI display driver, usually pre-soldered to an 8x8 LED module.
The adapter condenses the 12 muscles onto the grid: rows 0–1 brows
(lifted when raised, shifted inward when knitted), rows 2–3 eyes (two
rows wide open, one row squinting), rows 5–7 mouth (smile, frown, open
jaw, pressed lips).

Wiring (enable SPI first: `sudo raspi-config` → Interface Options → SPI):

| MAX7219 pin | Raspberry Pi |
|-------------|--------------|
| VCC | 5V |
| GND | GND |
| DIN | MOSI (pin 19) |
| CS  | CE0 (pin 24) |
| CLK | SCLK (pin 23) |

## PCA9685 servo board

A 16-channel PWM driver on I2C (enable it: `sudo raspi-config` →
Interface Options → I2C). One servo per muscle on channels 0–11. The
entire mapping is the `SERVO_MAP` table in `servo_face.py` — each
channel is a `(muscle, rest_angle, full_contraction_angle)` triple, and
activation is linearly interpolated between the two angles. Angles may
run "backwards" (rest > full) for mirrored linkages, so tuning an
animatronic head is just editing that table.

**Power:** feed the servos from their own 5–6 V supply on the board's
V+ terminal, with ground common to the Pi. Twelve hobby servos can draw
several amps — far more than the Pi's 5 V rail can source.

## Bring your own actuators

The interesting part to copy into your own robot is small: get a
`FaceState`, map its 12 floats to whatever actuators you have.

```python
from kindalive.expression.face import FaceProjection

face = FaceProjection.compute(engine.state)   # 12 floats in [0, 1]
my_renderer.draw(face.lip_corner_pull, face.jaw_open, ...)
```
