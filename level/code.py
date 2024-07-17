import time
import board
import busio
import math
import adafruit_mpu6050
import adafruit_ssd1306
from i2cdisplaybus import I2CDisplayBus
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import displayio
from terminalio import FONT
from adafruit_display_shapes.circle import Circle

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

# Create background
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw inner rectangle
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
splash.append(inner_sprite)

# Create circles
circle1 = Circle(WIDTH // 2, HEIGHT // 2, CIRCLE_RADIUS, fill=0x000000, outline=0xFFFFFF, stroke=2)
circle2 = Circle(WIDTH // 2, HEIGHT // 2, CIRCLE_RADIUS, fill=0xFFFFFF, outline=0xFFFFFF, stroke=2)
splash.append(circle1)
splash.append(circle2)

# Disable auto-refresh
oled.auto_refresh = False

# Global lists to store the last 10 acceleration values for X and Y
acc_x_values = []
acc_y_values = []
loop_durations = []

# Configuration variable to enable/disable vertical movement
enable_vertical_movement = False

def calculate_moving_average(new_value, values_list, max_length=10):
    values_list.append(new_value)
    if len(values_list) > max_length:
        values_list.pop(0)
    return sum(values_list) / len(values_list)

def print_status(mpu, circle2, loop_durations):
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % mpu.acceleration)
    print("Circle2 X:", circle2.x)
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

    end_time = time.monotonic()  # End time measurement
    loop_duration = end_time - start_time
    calculate_moving_average(loop_duration, loop_durations)

    current_time = time.monotonic()
    if current_time - last_print_time >= 1:
        # Print status every second
        print_status(mpu, circle2, loop_durations)
        last_print_time = current_time

    oled.refresh()
    time.sleep(1 / 60)