from machine import I2C
import time
from pcf85263 import PCF85263

# Initialize I2C - adjust depending on your board
i2c = I2C(0)

# Create RTC instance
rtc = PCF85263(i2c)

# Switch to stopwatch mode
rtc.stopwatch_mode = True

# Disable previous alarms, just in case
rtc.disable_alarm1()
rtc.disable_alarm2()

# Reset stopwatch to zero
print("Resetting stopwatch to zero...")
rtc.stopwatch_reset()

# Configure Alarm 1 to trigger at 5 seconds
print("Setting Alarm 1 for 0 hours, 0 minutes, and 5 seconds.")
rtc.set_stopwatch_alarm1(hours=0, minutes=0, seconds=5)

# Start counting
print("Starting stopwatch...")
rtc.start()

# Poll for the alarm flag
print("Waiting for Alarm 1 to trigger...")
while True:
    hours, minutes, seconds, hundredths = rtc.stopwatch_time
    # Print the current stopwatch time (only showing whole seconds to avoid spamming the console too much)
    print(f"Elapsed Time: {hours:02d}:{minutes:02d}:{seconds:02d}.{hundredths:02d}", end="\r")
    
    if rtc.alarm1_triggered:
        print(f"\n-> Alarm 1 Triggered! It has been roughly 5 seconds.")
        break
    time.sleep(0.1)

print("Test finished.")

# Switch back to RTC mode to restore default functionality
rtc.stopwatch_mode = False
print("Switched back to RTC mode.")
