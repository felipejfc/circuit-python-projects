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

def print_status(mpu, avg_acc_x, avg_acc_y, circle2, loop_durations):
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % mpu.acceleration)
    print("Average Acceleration X: %.2f" % avg_acc_x)
    print("Average Acceleration Y: %.2f" % avg_acc_y)
    if enable_vertical_movement:
        print("Circle2 Y:", circle2.y)
    avg_loop_duration = sum(loop_durations) / len(loop_durations)
    print("Average loop duration: %.4f seconds" % avg_loop_duration)

last_print_time = time.monotonic()

while True:
    start_time = time.monotonic()  # Start time measurement
    
    # Calculate the moving average of the last 10 acceleration values
    avg_acc_x = calculate_moving_average(mpu.acceleration[0], acc_x_values)
    avg_acc_y = calculate_moving_average(mpu.acceleration[1], acc_y_values)

    # Update circle position
    circle2.x = WIDTH // 2 - CIRCLE_RADIUS + math.floor(avg_acc_y * 20)
    if enable_vertical_movement:
        circle2.y = HEIGHT // 2 - CIRCLE_RADIUS + math.floor(avg_acc_x * 20)

    # Show or hide the "Level!" label based on avg_acc_x and avg_acc_y
    if enable_vertical_movement:
        level_label.hidden = not (0.00 <= abs(avg_acc_x) <= 0.05 and 0.00 <= abs(avg_acc_y) <= 0.05)
    else:
        level_label.hidden = not (0.00 <= abs(avg_acc_y) <= 0.05)

    end_time = time.monotonic()  # End time measurement
    loop_duration = end_time - start_time
    calculate_moving_average(loop_duration, loop_durations)

    current_time = end_time
    if current_time - last_print_time >= 1:
        # Print status every second
        print_status(mpu, avg_acc_x, avg_acc_y, circle2, loop_durations)
        last_print_time = current_time

    oled.refresh()
    time.sleep(1 / 60)