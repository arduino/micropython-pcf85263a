from machine import I2C
import time
from pcf85263 import PCF85263

# Initialize I2C - adjust depending on your board
i2c = I2C(0)

# Create RTC instance
rtc = PCF85263(i2c)

# Switch to stopwatch mode
rtc.stopwatch_mode = True

# Reset stopwatch to zero
print("Resetting stopwatch to zero...")
rtc.stopwatch_reset()

# Start counting
print("Running stopwatch for 2.8 seconds...")
rtc.start()

# Simulate elapsed time
time.sleep(2.8)

# Read the elapsed time
hours, minutes, seconds, hundredths = rtc.stopwatch_time
print(f"Elapsed Time: {hours:02d}:{minutes:02d}:{seconds:02d}.{hundredths:02d}")
time.sleep(2)

# Run it for 3 seconds and continously print the stopwatch time every second
rtc.stopwatch_reset()
rtc.start()
print("Running stopwatch for 3 seconds...")
start_time = time.ticks_ms()

last_time = None # To track the last printed time and avoid duplicates
while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
    new_time = rtc.stopwatch_time
    if new_time != last_time:
         hours, minutes, seconds, hundredths = new_time
         print(f"Stopwatch Time: {hours:02d}:{minutes:02d}:{seconds:02d}.{hundredths:02d}")
         last_time = new_time

# Switch back to RTC mode
rtc.stopwatch_mode = False
print("Switched back to RTC mode.")
