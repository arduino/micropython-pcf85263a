"""
Basic example showing how to read the current time from the PCF85263 RTC.

Initial author: Sebastian Romero (s.romero@arduino.cc)
Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

from machine import I2C
from time import sleep

try:
    from pcf85263 import PCF85263
except ImportError:
    print("Please install the pcf85263 module first.")
    import sys
    sys.exit(1)

# Initialize I2C. Change the bus number or pins as needed for your specific board.
i2c = I2C(0)

# Initialize the RTC
rtc = PCF85263(i2c)

print("Starting RTC Clock Reader...")

while True:
    # Read the datetime property
    # Returns: (year, month, mday, hour, minute, second, weekday, yearday)
    dt = rtc.datetime
    
    # Simple formatting: YYYY-MM-DD HH:MM:SS
    formatted_time = f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}"
    
    print(f"Current RTC Time: {formatted_time}")
    
    # Delay before reading again
    sleep(1)
