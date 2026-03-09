from machine import I2C
import time
from pcf85263 import PCF85263

# Initialize I2C - adjust depending on your board
i2c = I2C(0)

# Create RTC instance
rtc = PCF85263(i2c)

# Set the current time to slightly before the alarm goes off
# (2024, 12, 31, 23, 59, 50, 2, 0) -> Year, Month, Day, Hour, Minute, Second, Weekday, Yearday
rtc.datetime = (2024, 12, 31, 23, 59, 50, 2, 0)
print("Current time set to 23:59:50")

# Set Alarm 1 to trigger at exactly 23:59:55
print("Setting Alarm 1 for 23:59:55 (matches exactly 55 seconds)...")
rtc.set_alarm1(seconds=55)

# Set Alarm 2 to trigger when minutes roll over to 0 (midnight)
print("Setting Alarm 2 for minute 0 (midnight rollover)...")
rtc.set_alarm2(minutes=0)

print("Waiting for alarms to trigger (polling)...")
try:
    while True:
        # Check alarm 1
        if rtc.alarm1_triggered:
            dt = rtc.datetime
            print(f"⏰ Alarm 1 triggered! Time is now {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
            # Note: Reading alarm1_triggered automatically clears the internal flag,
            # so the alarm remains active and would trigger again when the condition 
            # is met (e.g. next minute at 55 seconds).
            rtc.disable_alarm1() # Disable Alarm 1 to prevent it from triggering again until we set it again
            
        # Check alarm 2
        if rtc.alarm2_triggered:
            dt = rtc.datetime
            print(f"⏰ Alarm 2 triggered! Time is now {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}")
            rtc.disable_alarm2() # Completely disable Alarm 2
            break # Exit after alarm 2 triggers
            
        time.sleep(1) # Poll every 1 second
except KeyboardInterrupt:
    print("Exiting...")
