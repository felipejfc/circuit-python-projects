import time
import board
import busio
import math
import adafruit_mpu6050
from i2cdisplaybus import I2CDisplayBus
import adafruit_displayio_ssd1306
import displayio
from terminalio import FONT
from adafruit_display_shapes.circle import Circle
from adafruit_display_text import label
from collections import deque
import digitalio
from adafruit_debouncer import Debouncer

# Constants
WIDTH = 128
HEIGHT = 64
BORDER = 3
CIRCLE_RADIUS = 15

# Initialize I2C and devices
displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
mpu = adafruit_mpu6050.MPU6050(i2c)
display_bus = I2CDisplayBus(i2c, device_address=0x3C, reset=None)
oled = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# Create display context
splash = displayio.Group()
oled.root_group = splash

def create_tilegrid(width, height, color, x=0, y=0):
    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    palette[0] = color
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=x, y=y)

# Create background
splash.append(create_tilegrid(WIDTH, HEIGHT, 0xFFFFFF))

# Draw inner rectangle
splash.append(create_tilegrid(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 0x000000, BORDER, BORDER))

# Create circles
circle1 = Circle(WIDTH // 2, HEIGHT // 2, CIRCLE_RADIUS, fill=0x000000, outline=0xFFFFFF, stroke=2)
circle2 = Circle(WIDTH // 2, HEIGHT // 2, CIRCLE_RADIUS, fill=0xFFFFFF, outline=0xFFFFFF, stroke=2)
splash.append(circle1)
splash.append(circle2)

# Create label for "Level!"
level_label = label.Label(FONT, text="Level!", color=0xFFFFFF, y=HEIGHT - 10, anchor_point=(0.5, 1))
label_width = level_label.bounding_box[2]
level_label.x = WIDTH // 2 - label_width // 2
splash.append(level_label)
level_label.hidden = True  # Initially hidden

# Disable auto-refresh
oled.auto_refresh = False

# Global lists to store the last 10 acceleration values for X and Y
acc_x_values = deque([0]*20, 20)
acc_y_values = deque([0]*20, 20)
loop_durations = deque([0]*20, 20)

# Configuration variable to enable/disable vertical movement
enable_vertical_movement = False

def calculate_moving_average(new_value, values_deque):
    values_deque.append(new_value)
    return sum(values_deque) / len(values_deque)

def print_status(mpu, circle2, loop_duration):
    print(f"Acceleration: X:{mpu.acceleration[0]:.2f}, Y: {mpu.acceleration[1]:.2f}, Z: {mpu.acceleration[2]:.2f} m/s^2")
    if enable_vertical_movement:
        print(f"Circle2 Y: {circle2.y}")
    print(f"Average loop duration: {loop_duration:.4f} seconds")

last_print_time = time.monotonic()

# Initialize button
button_pin = digitalio.DigitalInOut(board.D1)
button_pin.direction = digitalio.Direction.INPUT
button_pin.pull = digitalio.Pull.UP
button = Debouncer(button_pin)

# Initial positions
current_x = WIDTH // 2 - CIRCLE_RADIUS
current_y = HEIGHT // 2 - CIRCLE_RADIUS

while True:
    start_time = time.monotonic()  # Start time measurement

    # Update button state
    button.update()
    if button.fell:  # Button pressed
        enable_vertical_movement = not enable_vertical_movement

    # Get current acceleration values
    acc_x, acc_y, _ = mpu.acceleration

    # Calculate moving averages
    avg_acc_x = calculate_moving_average(acc_x, acc_x_values)
    avg_acc_y = calculate_moving_average(acc_y, acc_y_values)

    # Calculate target positions
    current_x = WIDTH // 2 - CIRCLE_RADIUS + math.floor(avg_acc_y * 20)
    current_y = HEIGHT // 2 - CIRCLE_RADIUS + math.floor(avg_acc_x * 20) if enable_vertical_movement else HEIGHT // 2 - CIRCLE_RADIUS

    # Update circle position
    circle2.x = int(current_x)
    circle2.y = int(current_y)

    # Show or hide the "Level!" label based on avg_acc_x and avg_acc_y
    level_label.hidden = not (0.00 <= abs(avg_acc_x) <= 0.05 and 0.00 <= abs(avg_acc_y) <= 0.05) if enable_vertical_movement else not (0.00 <= abs(avg_acc_y) <= 0.05)

    # Calculate loop duration
    loop_duration = time.monotonic() - start_time

    # Print status every second
    if time.monotonic() - last_print_time >= 1:
        print_status(mpu, circle2, loop_duration)
        last_print_time = time.monotonic()

    oled.refresh()
    time.sleep(1 / 60)